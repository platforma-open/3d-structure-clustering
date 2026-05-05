import type {
  AxisId,
  InferOutputsType,
  PFrameHandle,
  PlDataTableModel,
  PObjectId,
} from "@platforma-sdk/model";
import {
  BlockModelV3,
  createDiscoveredPColumnId,
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

// `easy-linclust` is intentionally absent — foldseek's linclust rejects PDB
// directories ("Input database has the wrong type (Generic)") and only accepts
// FASTA / stdin. Adding it would require chaining `foldseek createdb` →
// `foldseek linclust`, which means shuffling ~14 db files between two exec
// runs without an `addFileSet` API. Re-enable when the use case warrants it.
export const clusteringModeOptions = [
  { label: "Cascaded", value: "easy-cluster" satisfies ClusteringMode },
] as const;

export function defaultBlockLabelFor(args: Partial<BlockData>): string {
  const parts: string[] = ["FoldSeek 3Di+AA"];
  parts.push(`TM≥${(args.tmScoreThreshold ?? 0.5).toFixed(2)}`);
  parts.push(`cov≥${(args.coverageThreshold ?? 0.8).toFixed(2)}`);
  if (args.clusteringMode === "easy-linclust") parts.push("linclust");
  if (args.cdrh3LengthStratify) parts.push("stratified");
  return parts.join(", ");
}

export const platforma = BlockModelV3.create(blockDataModel)

  .args<BlockArgs>((data) => {
    if (data.dataset === undefined) throw new Error("Select a predicted PDB column");
    return {
      defaultBlockLabel: data.defaultBlockLabel,
      customBlockLabel: data.customBlockLabel,
      dataset: data.dataset,
      tmScoreThreshold: data.tmScoreThreshold,
      coverageThreshold: data.coverageThreshold,
      clusteringMode: data.clusteringMode,
      cdrh3LengthStratify: data.cdrh3LengthStratify,
      cpu: data.cpu,
      mem: data.mem,
    };
  })

  // PDB column options. The dropdown label combines the dataset's native
  // label with the clonotype axis's chain domain so options read e.g.
  // "My Dataset (IGHeavy)" / "My Dataset (IGLight)" — the column-level label
  // alone collides across upstream chain-split datasets because MiXCR puts
  // chain info on the axis, not the column.
  .output("datasetOptions", (ctx) =>
    ctx.resultPool.getOptions(
      [
        { axes: [{ name: "pl7.app/vdj/clonotypeKey" }], name: "pl7.app/structure/pdb" },
        { axes: [{ name: "pl7.app/vdj/scClonotypeKey" }], name: "pl7.app/structure/pdb" },
      ],
      (spec) => {
        const chain = isPColumnSpec(spec)
          ? spec.axesSpec?.[0]?.domain?.["pl7.app/vdj/chain"]
          : undefined;
        return chain ? `3D Structure (${chain})` : "3D Structure";
      },
    ),
  )

  .output("hasCdrh3LengthColumn", (): boolean => false)

  .outputWithStatus("clustersTable", (ctx): PlDataTableModel | undefined => {
    const acc = ctx.outputs?.resolve("clustersTable");
    if (acc === undefined) return undefined;
    const snapshots = new OutputColumnProvider(acc).getAllColumns();
    if (snapshots.length === 0) return undefined;
    return createPlDataTableV3(ctx, {
      columns: snapshots.map((s) => ({
        column: {
          ...s,
          id: createDiscoveredPColumnId({
            column: s.id as PObjectId,
            path: [],
            columnQualifications: [],
            queriesQualifications: {},
          }),
        },
        originalId: s.id as PObjectId,
        qualifications: { forQueries: {}, forHit: [] },
        path: [],
        isPrimary: true,
      })),
      tableState: ctx.data.tableState,
    });
  })

  // Single-column pFrames for the histogram + bubble plot pages. Splitting
  // into per-page frames mirrors the pattern in 3d-structure-prediction —
  // GraphMaker pre-fills extra slots from siblings if given a multi-column
  // source, producing overlapping plots.
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

  // Specs surfaced to the plot pages so they can build PredefinedGraphOption
  // defaults without re-resolving the result. The pages key off the spec
  // `name` to find the right source.
  .output("clusterSizeSpec", (ctx) => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    return pCols?.find((c) => c.spec.name === "pl7.app/structure/clustering/clusterSize")?.spec;
  })

  .output("clusterRadiusSpec", (ctx) => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    return pCols?.find((c) => c.spec.name === "pl7.app/structure/clustering/clusterRadius")?.spec;
  })

  // Centroid PDB ResourceMap: clusterId → File handle. Built by the
  // build-centroid-pdbs-map workdir processor template.
  .output("centroidPdbsMap", (ctx) => {
    const pCols = ctx.outputs?.resolve("centroidPdbsMap")?.getPColumns();
    if (pCols === undefined) return undefined;
    const pdbCol = pCols.find((c) => c.spec.name === "pl7.app/structure/centroidPdb");
    if (pdbCol === undefined) return undefined;
    const parsed = parseResourceMap(pdbCol.data, (acc) => acc.getRemoteFileHandle(), false);
    if (!parsed.isComplete) return undefined;
    return parsed.data;
  })

  // ClusterId axis identifier — used by the UI to wire `show-cell-button-for-axis-id`
  // for per-row centroid-PDB download / view.
  .output("clusterAxisId", (ctx): AxisId | undefined => {
    const pCols = ctx.outputs?.resolve("clustersTable")?.getPColumns();
    if (pCols === undefined || pCols.length === 0) return undefined;
    // Find any column on the [sampleId, clusterId] axes.
    for (const col of pCols) {
      const axis = col.spec.axesSpec.find((a) => a.name === "pl7.app/structure/clusterId");
      if (axis !== undefined) return { type: axis.type, name: axis.name, domain: axis.domain };
    }
    return undefined;
  })

  // Singleton-rate signal — the >25% alert (R51) compares this to a threshold.
  .output("singletonRate", (ctx): number | undefined => {
    const raw = ctx.outputs?.resolve("clusteringSummary")?.getDataAsJson();
    return (raw as { singletonRate?: number } | undefined)?.singletonRate;
  })

  // True when the resolved confident PDB set is empty — drives the empty-input
  // alert (R18, R43).
  .output("emptyInput", (ctx): boolean | undefined => {
    const raw = ctx.outputs?.resolve("clusteringSummary")?.getDataAsJson();
    return (raw as { emptyInput?: boolean } | undefined)?.emptyInput;
  })

  .output("clusteringLogHandle", (ctx) => ctx.outputs?.resolve("clusteringLog")?.getLogHandle())

  .title(() => "3D Structure Clustering")

  .subtitle((ctx) => ctx.data.customBlockLabel || ctx.data.defaultBlockLabel)

  .sections((_ctx) => [
    { type: "link", href: "/", label: "Clusters" },
    { type: "link", href: "/histogram", label: "Cluster size distribution" },
    { type: "link", href: "/bubble-plot", label: "Cluster abundance" },
  ])

  .done();

export type BlockOutputs = InferOutputsType<typeof platforma>;
