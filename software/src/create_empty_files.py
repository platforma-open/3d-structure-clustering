"""Emit empty-but-headed TSVs for the empty-input short-circuit.

When the confident PDB set is empty (no rows), the workflow skips the FoldSeek
pipeline and calls this entrypoint to materialize placeholder TSVs with the
expected headers, so downstream xsv.importFile calls don't fail on missing
files. Mirrors the pattern in clonotype-clustering's create-empty-files.py.
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
