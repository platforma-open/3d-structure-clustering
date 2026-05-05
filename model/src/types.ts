import type { GraphMakerState } from "@milaboratories/graph-maker";
import type { PlDataTableStateV2, PlRef } from "@platforma-sdk/model";

export type ClusteringMode = "easy-cluster" | "easy-linclust";

/**
 * Args sent to the workflow — validated output of `.args(...)`. The workflow
 * uses `dataset` (a `PlRef` to the predicted PDB column) as the main anchor
 * and the input ResourceMap to cluster.
 */
export type BlockArgs = {
  defaultBlockLabel: string;
  customBlockLabel: string;

  dataset: PlRef;

  tmScoreThreshold: number;
  coverageThreshold: number;
  clusteringMode: ClusteringMode;
  cdrh3LengthStratify: boolean;
  cpu?: number;
  mem?: number;
};

/**
 * Unified V3 data model — what the user manipulates in the UI and what
 * `.args()` derives the workflow args from. The user picks the predicted
 * PDB column directly; the dropdown labels include chain (e.g. "IGH").
 */
export type BlockData = {
  defaultBlockLabel: string;
  customBlockLabel: string;

  dataset?: PlRef;

  tmScoreThreshold: number;
  coverageThreshold: number;
  clusteringMode: ClusteringMode;
  cdrh3LengthStratify: boolean;
  cpu?: number;
  mem?: number;

  tableState: PlDataTableStateV2;
  graphStateBubble: GraphMakerState;
  graphStateHistogram: GraphMakerState;
};
