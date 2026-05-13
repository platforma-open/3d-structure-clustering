"""Filter the staged PDB directory to the upstream-confident subset.

Reads manifest.tsv + confident_keys.tsv + pdbs/, writes filtered/<filename>
copies + filtered/filtered_manifest.tsv (clonotypeKey, filename). The first
column of confident_keys.tsv is the pt-encoded axis key (header opaque, read
positionally).
"""

import argparse
import os
import shutil

import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Filter staged PDBs to the confident subset.")
    parser.add_argument("--manifest", required=True, help="manifest.tsv (clonotypeKey, staged_filename, bin)")
    parser.add_argument("--confident-keys-tsv", required=True, help="Confident-keys TSV (axis-key first column)")
    parser.add_argument("--pdbs-dir", required=True, help="Source PDB directory (per manifest.staged_filename)")
    parser.add_argument("--output-dir", default="filtered", help="Filtered PDB directory + filtered_manifest.tsv parent")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    manifest = pd.read_csv(args.manifest, sep="\t", dtype=str)
    keys_df = pd.read_csv(args.confident_keys_tsv, sep="\t", dtype=str)
    confident = set(keys_df.iloc[:, 0].dropna().tolist())

    rows = []
    for _, row in manifest.iterrows():
        key = row["clonotypeKey"]
        if key not in confident:
            continue
        filename = row["staged_filename"]
        src = os.path.join(args.pdbs_dir, filename)
        if not os.path.exists(src):
            print(f"warning: staged PDB missing for {key} ({filename}); skipped")
            continue
        shutil.copy(src, os.path.join(args.output_dir, filename))
        rows.append({"clonotypeKey": key, "filename": filename})

    filtered_manifest = pd.DataFrame(rows, columns=["clonotypeKey", "filename"])
    filtered_manifest.to_csv(
        os.path.join(args.output_dir, "filtered_manifest.tsv"), sep="\t", index=False
    )
    print(
        f"Filtered {len(rows)} confident PDBs out of {len(manifest)} "
        f"(confident keys: {len(confident)})"
    )


if __name__ == "__main__":
    main()
