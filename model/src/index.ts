import type {
  AxisId,
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
import type { BlockArgs, BlockData, ClusteringMode } from "./types";

export * from "./types";
export { blockDataModel } from "./dataModel";

// `easy-linclust` is not exposed: foldseek's linclust rejects PDB directories
// and requires a separate `foldseek createdb` chain.
export const clusteringModeOptions = [
  { label: "Cascaded", value: "easy-cluster" satisfies ClusteringMode },
] as const;

export function defaultBlockLabelFor(args: Partial<BlockData>): string {
  const parts: string[] = ["FoldSeek 3Di+AA"];
  parts.push(`TM≥${(args.tmScoreThreshold ?? 0.5).toFixed(2)}`);
  parts.push(`cov≥${(args.coverageThreshold ?? 0.8).toFixed(2)}`);
  if (args.clusteringMode === "easy-linclust") parts.push("linclust");
  return parts.join(", ");
}

export const platforma = BlockModelV3.create(blockDataModel)

  .args<BlockArgs>((data) => {
    if (data.dataset === undefined) throw new Error("Select a predicted PDB column");
    return {
      customBlockLabel: data.customBlockLabel,
      dataset: data.dataset.primary,
      tmScoreThreshold: data.tmScoreThreshold,
      coverageThreshold: data.coverageThreshold,
      clusteringMode: data.clusteringMode,
      cpu: data.cpu,
      mem: data.mem,
    };
  })

  // Labels are decorated with the chain pulled from the clonotypeKey axis
  // domain so chain-split PDB columns don't collide on the same "3D Structure"
  // label in the dropdown.
  .output("datasetOptions", (ctx): DatasetOption[] | undefined => {
    const options = buildDatasetOptions(ctx, {
      primary: (spec: PObjectSpec): boolean => {
        if (!isPColumnSpec(spec)) return false;
        if (spec.name !== "pl7.app/structure/pdb") return false;
        const rowAxis = spec.axesSpec?.[0]?.name;
        return rowAxis === "pl7.app/vdj/clonotypeKey" || rowAxis === "pl7.app/vdj/scClonotypeKey";
      },
    });
    if (options === undefined) return undefined;
    return options.map((opt) => {
      const spec = ctx.resultPool.getPColumnSpecByRef(opt.primary.ref);
      const chain =
        spec !== undefined && isPColumnSpec(spec)
          ? spec.axesSpec?.[0]?.domain?.["pl7.app/vdj/chain"]
          : undefined;
      const label = chain ? `3D Structure (${chain})` : "3D Structure";
      return { ...opt, primary: { ...opt.primary, label } };
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

  // ClusterId axis identifier — used by the UI to wire per-row centroid-PDB
  // download / view via `show-cell-button-for-axis-id`.
  .output("clusterAxisId", (ctx): AxisId | undefined => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    if (pCols === undefined || pCols.length === 0) return undefined;
    for (const col of pCols) {
      const axis = col.spec.axesSpec.find((a) => a.name === "pl7.app/clusterId");
      if (axis !== undefined) return { type: axis.type, name: axis.name, domain: axis.domain };
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
