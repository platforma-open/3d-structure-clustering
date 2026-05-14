"""Empty-input short-circuit: writes header-only TSVs so downstream
xsv.importFile calls don't fail when the (filtered) PDB set is empty.
"""

import argparse
import json
import os

import pandas as pd


CLUSTER_ASSIGNMENTS_COLS = [
    "clonotypeKey",
    "clusterId",
    "clusterLabel",
    "isCentroid",
    "tmScoreToCentroid",
    "tmDistanceToCentroid",
]
CLUSTER_SUMMARY_COLS = ["clusterId", "clusterLabel", "size", "radius", "centroidClonotypeKey"]
CENTROIDS_MANIFEST_COLS = ["clusterId", "pdb_filename"]
ABUNDANCES_COLS = ["sampleId", "clusterId", "abundance", "abundance_fraction"]
ABUNDANCES_PER_CLUSTER_COLS = [
    "clusterId",
    "abundance_per_cluster",
    "abundance_fraction_per_cluster",
]
MEMBER_SEQUENCES_COLS = ["clonotypeKey", "sequence_H", "sequence_L"]


def main():
    parser = argparse.ArgumentParser(description="Emit empty placeholder TSVs.")
    parser.add_argument("--output-dir", default="results", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(os.path.join(args.output_dir, "centroids"), exist_ok=True)

    pd.DataFrame(columns=CLUSTER_ASSIGNMENTS_COLS).to_csv(
        os.path.join(args.output_dir, "cluster_assignments.tsv"), sep="\t", index=False
    )
    pd.DataFrame(columns=CLUSTER_SUMMARY_COLS).to_csv(
        os.path.join(args.output_dir, "cluster_summary.tsv"), sep="\t", index=False
    )
    pd.DataFrame(columns=CENTROIDS_MANIFEST_COLS).to_csv(
        os.path.join(args.output_dir, "centroids_manifest.tsv"), sep="\t", index=False
    )
    pd.DataFrame(columns=ABUNDANCES_COLS).to_csv(
        os.path.join(args.output_dir, "abundances.tsv"), sep="\t", index=False
    )
    pd.DataFrame(columns=ABUNDANCES_PER_CLUSTER_COLS).to_csv(
        os.path.join(args.output_dir, "abundances-per-cluster.tsv"), sep="\t", index=False
    )
    pd.DataFrame(columns=MEMBER_SEQUENCES_COLS).to_csv(
        os.path.join(args.output_dir, "member_sequences.tsv"), sep="\t", index=False
    )

    # Empty FoldSeek cluster.tsv (no header — FoldSeek emits headerless 2-col TSV)
    # so the workflow's `foldseekClusters` output is always populated.
    with open(os.path.join(args.output_dir, "cluster.tsv"), "w"):
        pass

    summary_json = {
        "totalRows": 0,
        "clusterCount": 0,
        "singletonCount": 0,
        "singletonRate": 0.0,
        "emptyInput": True,
    }
    with open(os.path.join(args.output_dir, "summary.json"), "w") as fh:
        json.dump(summary_json, fh)

    print("Created empty placeholder TSVs")


if __name__ == "__main__":
    main()
