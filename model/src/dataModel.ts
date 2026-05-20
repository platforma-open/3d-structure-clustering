import { createPlDataTableStateV2, DataModelBuilder } from "@platforma-sdk/model";
import type { BlockData } from "./types";

const initialGraphState = (title: string, fillColor: string) =>
  ({
    title,
    template: "bins",
    currentTab: null,
    layersSettings: { bins: { fillColor } },
    axesSettings: {
      axisY: { axisLabelsAngle: 0 as const, scale: "linear" },
      other: { binsCount: 30 },
    },
  }) satisfies import("@milaboratories/graph-maker").GraphMakerState;

const initialBubbleState = () =>
  ({
    title: "Cluster abundance",
    template: "dots",
    currentTab: null,
    layersSettings: {},
    axesSettings: {},
  }) satisfies import("@milaboratories/graph-maker").GraphMakerState;

export const blockDataModel = new DataModelBuilder().from<BlockData>("v1").init(() => ({
  customBlockLabel: "",
  defaultBlockLabel: "",

  tmScoreThreshold: 0.95,
  coverageThreshold: 0.9,
  clusteringMode: "easy-cluster" as const,
  alignmentType: "full_pdb_aa" as const,
  // Only consulted in cdrh3 mode. Trade-off: small flank keeps the cluster
  // signal CDR-focused but starves TM-score's length-dependent d0; large
  // flank pulls in highly-conserved FR3-end + FR4 residues and re-introduces
  // the framework-dominated "one huge cluster" symptom. flank=5 puts
  // fragments at ~23 aa (d0 ≈ 0.7 Å) — still loop-dominated but long enough
  // for TM-scoring to discriminate, with FoldSeek's k-mer prefilter able to
  // find candidate pairs.
  cdrh3FlankResidues: 5,

  tableState: createPlDataTableStateV2(),
  graphStateBubble: initialBubbleState(),
  graphStateHistogram: initialGraphState("Cluster size distribution", "#7da3d1"),
  alignmentModel: {},
}));
