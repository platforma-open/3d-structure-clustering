import type {
  AxisId,
  AxisSpec,
  DatasetOption,
  InferOutputsType,
  PFrameHandle,
  PlDataTableModel,
  PObjectSpec,
} from "@platforma-sdk/model";
import {
  BlockModelV3,
  buildDatasetOptions,
  createPFrameForGraphs,
  createPlDataTableV3,
  isPColumnSpec,
  OutputColumnProvider,
  parseResourceMap,
} from "@platforma-sdk/model";
import { blockDataModel } from "./dataModel";
import type { AlignmentType, BlockArgs, BlockData, ClusteringMode } from "./types";

export * from "./types";
export { blockDataModel } from "./dataModel";

// Restrict the filter slot in `PlDatasetSelector` to subsets coming from the
// 3d-structure-prediction block (typically the `confident` subset). Mirrors
// 3d-structure-prediction's `hasLeadSelectionTrace` pattern.
const PREDICTION_TRACE_TYPE = "milaboratories.3d-structure-prediction";

function hasPredictionTrace(annotations: Record<string, string> | undefined): boolean {
  const raw = annotations?.["pl7.app/trace"];
  if (!raw) return false;
  try {
    const parsed: unknown = JSON.parse(raw);
    return (
      Array.isArray(parsed) &&
      parsed.some(
        (e) =>
          typeof e === "object" &&
          e !== null &&
          (e as { type?: unknown }).type === PREDICTION_TRACE_TYPE,
      )
    );
  } catch {
    return false;
  }
}

// `easy-linclust` is not exposed: foldseek's linclust rejects PDB directories
// and requires a separate `foldseek createdb` chain.
export const clusteringModeOptions = [
  { label: "Cascaded", value: "easy-cluster" satisfies ClusteringMode },
] as const;

export const alignmentTypeOptions = [
  { label: "CDR-H3 only", value: "cdrh3" satisfies AlignmentType },
  { label: "Full PDB + AA (3Di + AA)", value: "full_pdb_aa" satisfies AlignmentType },
  { label: "Full PDB (TM-align)", value: "full_pdb" satisfies AlignmentType },
] as const;

const ALIGNMENT_LABEL: Record<AlignmentType, string> = {
  cdrh3: "CDR-H3",
  full_pdb_aa: "Full PDB+AA",
  full_pdb: "Full PDB",
};

// Mode-appropriate defaults applied by the UI on alignment-scope change.
// cdrh3 mode (with flank=5 → ~23-aa fragments, d0 ≈ 0.7 Å) lives in a
// completely different TM-score regime than full-Fv: the framework-conserved
// baseline of ≥0.85 disappears, and the meaningful working range drops to
// ~0.4–0.8. Coverage in cdrh3 mode also acts as a CDR-H3 length filter —
// pairs whose length ratio falls below the threshold are filtered out
// before scoring. 0.70/0.80 was empirically validated against a 65-PDB
// repertoire (37 clusters vs ~12 in full-PDB modes).
export const ALIGNMENT_DEFAULTS: Record<
  AlignmentType,
  {
    tmScoreThreshold: number;
    coverageThreshold: number;
  }
> = {
  cdrh3: { tmScoreThreshold: 0.7, coverageThreshold: 0.8 },
  full_pdb_aa: { tmScoreThreshold: 0.95, coverageThreshold: 0.9 },
  full_pdb: { tmScoreThreshold: 0.95, coverageThreshold: 0.9 },
};

export function defaultBlockLabelFor(args: Partial<BlockData>): string {
  const parts: string[] = [`${ALIGNMENT_LABEL[args.alignmentType ?? "full_pdb_aa"]}`];
  parts.push(`TM≥${(args.tmScoreThreshold ?? 0.95).toFixed(2)}`);
  parts.push(`cov≥${(args.coverageThreshold ?? 0.9).toFixed(2)}`);
  if (args.clusteringMode === "easy-linclust") parts.push("linclust");
  return parts.join(", ");
}

export const platforma = BlockModelV3.create(blockDataModel)

  .args<BlockArgs>((data) => {
    if (data.dataset === undefined) throw new Error("Select a dataset");
    return {
      customBlockLabel: data.customBlockLabel,
      dataset: data.dataset.primary,
      tmScoreThreshold: data.tmScoreThreshold,
      coverageThreshold: data.coverageThreshold,
      clusteringMode: data.clusteringMode,
      alignmentType: data.alignmentType,
      cdrh3FlankResidues: data.cdrh3FlankResidues,
      cpu: data.cpu,
      mem: data.mem,
    };
  })

  .output("datasetOptions", (ctx): DatasetOption[] | undefined => {
    const options = buildDatasetOptions(ctx, {
      primary: (spec: PObjectSpec): boolean => {
        if (!isPColumnSpec(spec)) return false;
        if (spec.name !== "pl7.app/structure/pdb") return false;
        const rowAxis = spec.axesSpec?.[0]?.name;
        return rowAxis === "pl7.app/vdj/clonotypeKey" || rowAxis === "pl7.app/vdj/scClonotypeKey";
      },
      filter: (spec: PObjectSpec): boolean => hasPredictionTrace(spec.annotations),
    });
    if (options === undefined) return undefined;
    return options.map((opt) => {
      const primarySpec = ctx.resultPool.getPColumnSpecByRef(opt.primary.ref);
      const chain =
        primarySpec !== undefined && isPColumnSpec(primarySpec)
          ? primarySpec.axesSpec?.[0]?.domain?.["pl7.app/vdj/chain"]
          : undefined;
      const primaryLabel = chain ? `3D Structure (${chain})` : "3D Structure";

      // SDK 1.76.5 suppresses filters' `pl7.app/label` in `filterMatchesToOptions`
      // (filter_discovery.ts:74-77 — `formatters.native` is hardcoded to return
      // undefined). Filter columns with identical traces collapse to the same
      // trace-derived label. Override post-hoc with each filter's own
      // `pl7.app/label`.
      const filters = opt.filters?.map((f) => {
        const filterSpec = ctx.resultPool.getPColumnSpecByRef(f.ref);
        const native =
          filterSpec !== undefined && isPColumnSpec(filterSpec)
            ? filterSpec.annotations?.["pl7.app/label"]
            : undefined;
        return native ? { ...f, label: native } : f;
      });

      return {
        ...opt,
        primary: { ...opt.primary, label: primaryLabel },
        ...(filters !== undefined && filters.length > 0 ? { filters } : {}),
      };
    });
  })

  .outputWithStatus("clustersTable", (ctx): PlDataTableModel | undefined => {
    const acc = ctx.outputs?.resolve("clustersTable");
    if (acc === undefined) return undefined;
    const snapshots = new OutputColumnProvider(acc).getAllColumns();
    if (snapshots.length === 0) return undefined;

    // Anchor on a per-cluster PColumn so the table is keyed by [clusterId]
    // and V3's discovery surfaces the `pl7.app/label` column as the
    // axis-value substitution. maxHops:0 keeps per-clonotype columns out of
    // the per-cluster table.
    const anchorSpec = snapshots.find(
      (s) => s.spec.name === "pl7.app/structure/clustering/clusterSize",
    )?.spec;
    if (anchorSpec === undefined) return undefined;

    return createPlDataTableV3(ctx, {
      columns: {
        sources: [new OutputColumnProvider(acc)],
        anchors: { main: anchorSpec },
        selector: { mode: "enrichment", maxHops: 0 },
      },
      tableState: ctx.data.tableState,
    });
  })

  // Single-column histogram pframe — GraphMaker pre-fills extra slots from
  // siblings when given a multi-column source, producing overlapping plots.
  .outputWithStatus("histogramPf", (ctx): PFrameHandle | undefined => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    if (pCols === undefined) return undefined;
    const col = pCols.find((c) => c.spec.name === "pl7.app/structure/clustering/clusterSize");
    if (!col) return undefined;
    return createPFrameForGraphs(ctx, [col]);
  })

  .outputWithStatus("bubblePlotPf", (ctx): PFrameHandle | undefined => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    if (pCols === undefined) return undefined;
    return createPFrameForGraphs(ctx, pCols);
  })

  // Specs surfaced to the plot pages for PredefinedGraphOption defaults.
  .output("clusterSizeSpec", (ctx) => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    return pCols?.find((c) => c.spec.name === "pl7.app/structure/clustering/clusterSize")?.spec;
  })

  .output("clusterRadiusSpec", (ctx) => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    return pCols?.find((c) => c.spec.name === "pl7.app/structure/clustering/clusterRadius")?.spec;
  })

  // Per-[sampleId, clusterId] abundance count for the bubble plot. Matched
  // by axes + abundance annotations (the count column inherits the upstream
  // name, which varies by modality).
  .output("perSampleClusterAbundanceSpec", (ctx) => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    return pCols?.find(
      (c) =>
        c.spec.axesSpec.length === 2 &&
        c.spec.axesSpec.some((a) => a.name === "pl7.app/sampleId") &&
        c.spec.axesSpec.some((a) => a.name === "pl7.app/clusterId") &&
        c.spec.annotations?.["pl7.app/isAbundance"] === "true" &&
        c.spec.annotations?.["pl7.app/abundance/normalized"] !== "true",
    )?.spec;
  })

  // Centroid PDB ResourceMap: clusterId → File handle.
  .output("centroidPdbsMap", (ctx) => {
    const pCols = ctx.outputs?.resolve("centroidPdbsMap")?.getPColumns();
    if (pCols === undefined) return undefined;
    const pdbCol = pCols.find((c) => c.spec.name === "pl7.app/structure/centroidPdb");
    if (pdbCol === undefined) return undefined;
    const parsed = parseResourceMap(pdbCol.data, (acc) => acc.getRemoteFileHandle(), false);
    if (!parsed.isComplete) return undefined;
    return parsed.data;
  })

  // MSA pframe — feeds `PlMultiSequenceAlignment` on the main page. Carries
  // the per-clonotype member sequence (extracted from PDB ATOM records),
  // the cluster↔clonotype linker, and TM-distance to the centroid for
  // ordering. We attach the upstream clonotype-label column so the viewer
  // can label rows, then build the pframe with `ctx.createPFrame` directly
  // (mirrors `paratope-clustering`) — `createPFrameForGraphs` would enrich
  // with unrelated result-pool columns and break the join. Selection by
  // clusterId is applied UI-side.
  .output("msaPf", (ctx): PFrameHandle | undefined => {
    const msaCols = ctx.outputs?.resolve("msaPf")?.getPColumns();
    if (msaCols === undefined) return undefined;
    const datasetRef = ctx.data.dataset?.primary.column;
    if (datasetRef === undefined) return undefined;
    const labelCols =
      ctx.resultPool.getAnchoredPColumns({ main: datasetRef }, [
        {
          axes: [{ anchor: "main", idx: 0 }],
          name: "pl7.app/label",
        },
      ]) ?? [];
    return ctx.createPFrame([...msaCols, ...labelCols]);
  })

  // ClusterId axis identifier — used by the UI to match the cluster cell in
  // `cellRendererSelector` (AxisId is sufficient for that comparison).
  .output("clusterAxisId", (ctx): AxisId | undefined => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    if (pCols === undefined || pCols.length === 0) return undefined;
    for (const col of pCols) {
      const axis = col.spec.axesSpec.find((a) => a.name === "pl7.app/clusterId");
      if (axis !== undefined) return { type: axis.type, name: axis.name, domain: axis.domain };
    }
    return undefined;
  })

  // Full cluster axis spec (with annotations) — the MSA viewer's
  // `PlSelectionModel.axesSpec` needs the same AxisSpec the pframe joins use,
  // so we forward the raw spec from one of the cluster-keyed columns.
  .output("clusterAxisSpec", (ctx): AxisSpec | undefined => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    if (pCols === undefined || pCols.length === 0) return undefined;
    for (const col of pCols) {
      const axis = col.spec.axesSpec.find((a) => a.name === "pl7.app/clusterId");
      if (axis !== undefined) return axis;
    }
    return undefined;
  })

  .output("singletonRate", (ctx): number | undefined => {
    const raw = ctx.outputs?.resolve("clusteringSummary")?.getDataAsJson();
    return (raw as { singletonRate?: number } | undefined)?.singletonRate;
  })

  .output("emptyInput", (ctx): boolean | undefined => {
    const raw = ctx.outputs?.resolve("clusteringSummary")?.getDataAsJson();
    return (raw as { emptyInput?: boolean } | undefined)?.emptyInput;
  })

  .output("clusteringLogHandle", (ctx) => ctx.outputs?.resolve("clusteringLog")?.getLogHandle())

  .title(() => "3D Structure Clustering")

  .subtitle((ctx) => ctx.data.customBlockLabel || defaultBlockLabelFor(ctx.data))

  .sections((_ctx) => [
    { type: "link", href: "/", label: "Main" },
    { type: "link", href: "/bubble", label: "Most Abundant Clusters" },
    { type: "link", href: "/histogram", label: "Cluster Size Histogram" },
  ])

  .done();

export type BlockOutputs = InferOutputsType<typeof platforma>;
