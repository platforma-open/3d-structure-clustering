import type { GraphMakerState } from "@milaboratories/graph-maker";
import type {
  AlignmentType,
  ClusteringMode,
} from "@platforma-open/milaboratories.3d-structure-clustering.kind";
import type {
  DatasetSelection,
  PlDataTableStateV2,
  PlMultiSequenceAlignmentModel,
  PrimaryRef,
} from "@platforma-sdk/model";

/**
 * The two setting vocabularies live in the kind, not here. They are part of the
 * block's init-params contract, and the kind cannot import the model — the
 * dependency runs model → kind. Re-exported so every existing consumer keeps
 * working.
 */
export type { AlignmentType, ClusteringMode };

export type BlockArgs = {
  customBlockLabel: string;
  defaultBlockLabel: string;

  dataset: PrimaryRef;

  tmScoreThreshold: number;
  coverageThreshold: number;
  clusteringMode: ClusteringMode;
  alignmentType: AlignmentType;
  cdrh3FlankResidues: number;
  cpu?: number;
  mem?: number;
};

export type BlockData = {
  customBlockLabel: string;

  dataset?: DatasetSelection;

  tmScoreThreshold: number;
  coverageThreshold: number;
  clusteringMode: ClusteringMode;
  alignmentType: AlignmentType;
  cdrh3FlankResidues: number;
  cpu?: number;
  mem?: number;

  tableState: PlDataTableStateV2;
  graphStateBubble: GraphMakerState;
  graphStateHistogram: GraphMakerState;
  alignmentModel: PlMultiSequenceAlignmentModel;
};
