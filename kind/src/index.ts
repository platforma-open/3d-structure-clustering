import { assertParamsObject, defineBlockKind } from "@platforma-sdk/block-kind";
import { name, version } from "../package.json" with { type: "json" };

/**
 * How FoldSeek groups the structures. `easy-linclust` is declared but not
 * exposed in the UI — FoldSeek's linclust rejects PDB directories and needs a
 * separate `foldseek createdb` chain.
 */
export type ClusteringMode = "easy-cluster" | "easy-linclust";

/**
 * What FoldSeek scores against.
 *  - cdrh3:       pre-slice each PDB to CDR-H3 (REMARK 99 PLATFORMA CDRH3),
 *                 then cluster on those fragments — paratope-focused.
 *  - full_pdb_aa: full Fv, FoldSeek `--alignment-type 2` (3Di + AA combined) —
 *                 inflates similarity when framework AA is conserved.
 *  - full_pdb:    full Fv, FoldSeek `--alignment-type 1` (TM-align, backbone
 *                 only) — pure structural score.
 */
export type AlignmentType = "cdrh3" | "full_pdb_aa" | "full_pdb";

const CLUSTERING_MODES = ["easy-cluster", "easy-linclust"] as const;
const ALIGNMENT_TYPES = ["cdrh3", "full_pdb_aa", "full_pdb"] as const;

/**
 * This block's init-params contract — what a project template supplies to seed a
 * new instance.
 *
 * These are the five settings that change what the clustering produces. The
 * block's input selection is deliberately absent: `dataset` is an anchor-bound
 * reference (`DatasetSelection`) whose meaning depends on the anchor map of the
 * project that made it, so it cannot travel in a template. `cpu` and `mem` are
 * absent because they describe the machine a run gets, not the analysis. View
 * state — table state, the two graph states, the alignment model — and
 * `customBlockLabel` are not configuration and are absent for that reason.
 *
 * Every field is optional so a template can seed any subset; the model's `init`
 * keeps a default behind each one.
 */
export type BlockParams = {
  clusteringMode?: ClusteringMode;
  alignmentType?: AlignmentType;
  tmScoreThreshold?: number;
  coverageThreshold?: number;
  cdrh3FlankResidues?: number;
};

/**
 * Reject a value that is not one of a closed set.
 *
 * Both unions above are the block's own vocabulary, so there is no SDK guard to
 * reach for and the closed sets live here beside the types they check.
 */
function oneOf<T extends string>(key: string, value: unknown, allowed: readonly T[]): T {
  if (typeof value !== "string" || !(allowed as readonly string[]).includes(value)) {
    throw new Error(
      `'${key}' must be one of: ${allowed.join(", ")}. Got: ${JSON.stringify(value)}`,
    );
  }
  return value as T;
}

/** Reject a value that is not a finite number. */
function finiteNumber(key: string, value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`'${key}' must be a finite number. Got: ${JSON.stringify(value)}`);
  }
  return value;
}

/**
 * The same contract at runtime, for params arriving from a template file rather
 * than from typed code — the only point that can catch a hand-written entry
 * being wrong.
 *
 * Each field is checked only when present, because all five are optional. Keys
 * the contract does not name are dropped by not being read; refusing them would
 * mean holding a list of field names as strings that nothing keeps in step with
 * the type.
 *
 * The three numbers are checked as finite numbers and no further. The UI clamps
 * the two thresholds to 0–1 and the flank to a small residue count, and
 * `ALIGNMENT_DEFAULTS` in the model moves the threshold ranges when the
 * alignment scope changes. Encoding any of that here would make the kind refuse
 * a file this block itself exported the day a clamp changes. Range is meaning;
 * the kind checks the envelope.
 */
function parseInitializationParams(value: unknown): BlockParams {
  assertParamsObject(value);

  const params: BlockParams = {};

  if (value.clusteringMode !== undefined) {
    params.clusteringMode = oneOf("clusteringMode", value.clusteringMode, CLUSTERING_MODES);
  }

  if (value.alignmentType !== undefined) {
    params.alignmentType = oneOf("alignmentType", value.alignmentType, ALIGNMENT_TYPES);
  }

  if (value.tmScoreThreshold !== undefined) {
    params.tmScoreThreshold = finiteNumber("tmScoreThreshold", value.tmScoreThreshold);
  }

  if (value.coverageThreshold !== undefined) {
    params.coverageThreshold = finiteNumber("coverageThreshold", value.coverageThreshold);
  }

  if (value.cdrh3FlankResidues !== undefined) {
    params.cdrh3FlankResidues = finiteNumber("cdrh3FlankResidues", value.cdrh3FlankResidues);
  }

  return params;
}

// Identity (`name`/`version`) comes from this package's own `package.json`, so
// the on-wire `{name}@{version}` reference can never drift from what npm
// publishes; the bundler inlines the JSON import.
export const kind = defineBlockKind<BlockParams>({
  name,
  version,
  parseInitializationParams,
});
