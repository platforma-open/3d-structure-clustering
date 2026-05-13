import type { GraphMakerState } from "@milaboratories/graph-maker";
import type { DatasetSelection, PlDataTableStateV2, PrimaryRef } from "@platforma-sdk/model";

export type ClusteringMode = "easy-cluster" | "easy-linclust";

export type BlockArgs = {
  defaultBlockLabel: string;
  customBlockLabel: string;

  dataset: PrimaryRef;

  tmScoreThreshold: number;
  coverageThreshold: number;
  clusteringMode: ClusteringMode;
  cpu?: number;
  mem?: number;
};

export type BlockData = {
  defaultBlockLabel: string;
  customBlockLabel: string;

  dataset?: DatasetSelection;

  tmScoreThreshold: number;
  coverageThreshold: number;
  clusteringMode: ClusteringMode;
  cpu?: number;
  mem?: number;

  tableState: PlDataTableStateV2;
  graphStateBubble: GraphMakerState;
  graphStateHistogram: GraphMakerState;
};
