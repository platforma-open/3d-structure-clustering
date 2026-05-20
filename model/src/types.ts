import type { GraphMakerState } from "@milaboratories/graph-maker";
import type {
  DatasetSelection,
  PlDataTableStateV2,
  PlMultiSequenceAlignmentModel,
  PrimaryRef,
} from "@platforma-sdk/model";

export type ClusteringMode = "easy-cluster" | "easy-linclust";

// What FoldSeek scores against:
//  - cdrh3:       pre-slice each PDB to CDR-H3 (REMARK 99 PLATFORMA CDRH3),
//                 then cluster on those fragments — paratope-focused.
//  - full_pdb_aa: full Fv, FoldSeek `--alignment-type 2` (3Di + AA combined) —
//                 inflates similarity when framework AA is conserved.
//  - full_pdb:    full Fv, FoldSeek `--alignment-type 1` (TM-align, backbone
//                 only) — pure structural score.
export type AlignmentType = "cdrh3" | "full_pdb_aa" | "full_pdb";

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
