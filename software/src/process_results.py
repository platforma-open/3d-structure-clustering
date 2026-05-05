"""Parse FoldSeek cluster output and emit the final cluster TSVs.

Reads:
- cluster_tsv      — FoldSeek easy-cluster output: <centroid_filename>\t<member_filename>
- manifest.tsv     — clonotypeKey, staged_filename, bin (built inline by the workflow)
- pdbs/            — directory of staged PDB files

TM-distance per (member, centroid) pair is computed in Python via the tmtools
TM-align bindings (no second foldseek call) — same architectural pattern as
clonotype-clustering, where the distance metric is computed in post-processing
rather than by re-running the clustering tool.

Writes (under --output-dir):
- cluster_assignments.tsv — clonotypeKey, clusterId, isCentroid, tmScoreToCentroid, tmDistanceToCentroid
- cluster_summary.tsv     — clusterId, size, radius, centroidClonotypeKey
- centroids_manifest.tsv  — clusterId, pdb_filename
- centroids/              — copies of the centroid PDBs

Cluster IDs are assigned within a bin: when manifest has multiple bins (CDRH3
length stratification), cluster IDs are prefixed L<n>_C<idx>; otherwise C<idx>.
"""

import argparse
import json
import os
import shutil

import pandas as pd
from tmtools import tm_align
from tmtools.io import get_residue_data, get_structure


def load_pdb_coords(path: str) -> tuple:
    """Return (coords, sequence) for the first chain in the PDB file."""
    structure = get_structure(path)
    chain = next(structure.get_chains())
    coords, seq = get_residue_data(chain)
    return coords, seq


def main():
    parser = argparse.ArgumentParser(description="Parse FoldSeek cluster output, compute TM-distance, emit final TSVs.")
    parser.add_argument("--cluster-tsv", required=True, help="FoldSeek result_cluster.tsv")
    parser.add_argument("--manifest", required=True, help="manifest.tsv (clonotypeKey, staged_filename, bin)")
    parser.add_argument("--pdbs-dir", required=True, help="Staged PDBs directory")
    parser.add_argument("--output-dir", default="results", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    centroids_dir = os.path.join(args.output_dir, "centroids")
    os.makedirs(centroids_dir, exist_ok=True)

    # Manifest: staged_filename -> clonotypeKey, bin.
    manifest = pd.read_csv(args.manifest, sep="\t", dtype=str)
    file_to_ck = dict(zip(manifest["staged_filename"], manifest["clonotypeKey"]))
    file_to_bin = dict(zip(manifest["staged_filename"], manifest["bin"]))

    def normalize_filename(name: str) -> str:
        # FoldSeek strips ".pdb" in cluster TSV; keys are stems.
        # For multi-chain PDBs foldseek appends "_<chain_id>" to the stem,
        # producing e.g. `<clonotypeKey>_L`.
        if name in file_to_ck:
            return name
        if f"{name}.pdb" in file_to_ck:
            return f"{name}.pdb"
        if "_" in name:
            stem = name.rsplit("_", 1)[0]
            if f"{stem}.pdb" in file_to_ck:
                return f"{stem}.pdb"
            if stem in file_to_ck:
                return stem
        return name

    # Cluster TSV: <centroid_stem>\t<member_stem>, no header.
    cluster_df = pd.read_csv(
        args.cluster_tsv, sep="\t", header=None, names=["centroid_raw", "member_raw"], dtype=str
    )
    cluster_df["centroid_filename"] = cluster_df["centroid_raw"].apply(normalize_filename)
    cluster_df["member_filename"] = cluster_df["member_raw"].apply(normalize_filename)
    cluster_df["clonotypeKey"] = cluster_df["member_filename"].map(file_to_ck)
    cluster_df["bin"] = cluster_df["member_filename"].map(file_to_bin)
    cluster_df["centroidClonotypeKey"] = cluster_df["centroid_filename"].map(file_to_ck)

    if cluster_df["clonotypeKey"].isna().any():
        missing = cluster_df[cluster_df["clonotypeKey"].isna()]["member_raw"].tolist()
        raise SystemExit(
            f"FoldSeek output references unknown member files: {missing[:5]} (manifest mismatch)"
        )

    # FoldSeek can emit several rows for the same input file (chain/domain/lookup
    # variants), which after `normalize_filename` collapse to the same
    # clonotypeKey. Keep one row per (member_filename) — prefer the row where
    # member==centroid so each clonotype's "self" assignment wins when present.
    is_self = cluster_df["member_filename"] == cluster_df["centroid_filename"]
    cluster_df = (
        cluster_df.assign(_self_first=(~is_self).astype(int))
        .sort_values(["member_filename", "_self_first"])
        .drop_duplicates("member_filename", keep="first")
        .drop(columns=["_self_first"])
        .reset_index(drop=True)
    )

    # Cluster identity follows the clonotype-clustering pattern: the cluster
    # axis value IS the centroid's clonotypeKey (a hash from the upstream
    # data), namespaced by the cluster axis spec's domain. A separate
    # clusterLabel column carries the user-facing display string. Until a
    # clonotypeKeyLabel enrichment is wired through the workflow, the label
    # mirrors the centroid clonotypeKey verbatim.
    cluster_df["clusterId"] = cluster_df["centroidClonotypeKey"]
    cluster_df["clusterLabel"] = cluster_df["centroidClonotypeKey"]
    cluster_df["isCentroid"] = (
        cluster_df["clonotypeKey"] == cluster_df["centroidClonotypeKey"]
    ).astype("Int64")

    # Load each PDB once — clusters often share the same centroid across many
    # members, so caching by filename avoids re-parsing.
    pdb_cache: dict[str, tuple] = {}

    def load_cached(filename: str, bin_label: str):
        if filename in pdb_cache:
            return pdb_cache[filename]
        candidates = [
            os.path.join(args.pdbs_dir, filename),
            os.path.join(args.pdbs_dir, bin_label, filename),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)
        if path is None:
            raise SystemExit(f"PDB file not found for {filename} (bin {bin_label})")
        pdb_cache[filename] = load_pdb_coords(path)
        return pdb_cache[filename]

    # Compute TM-score per (member, centroid) pair via tmtools.
    # Normalize by chain1 (member) length — the conventional TM-align reading.
    tm_scores: list[float] = []
    for _, row in cluster_df.iterrows():
        if row["isCentroid"] == 1:
            tm_scores.append(1.0)
            continue
        m_coords, m_seq = load_cached(row["member_filename"], row["bin"])
        c_coords, c_seq = load_cached(row["centroid_filename"], row["bin"])
        result = tm_align(m_coords, c_coords, m_seq, c_seq)
        tm_scores.append(max(0.0, min(1.0, float(result.tm_norm_chain1))))

    cluster_df["tmScoreToCentroid"] = tm_scores
    cluster_df["tmDistanceToCentroid"] = 1.0 - cluster_df["tmScoreToCentroid"]

    assignments = cluster_df[
        [
            "clonotypeKey",
            "clusterId",
            "clusterLabel",
            "isCentroid",
            "tmScoreToCentroid",
            "tmDistanceToCentroid",
        ]
    ].sort_values(["clusterId", "isCentroid"], ascending=[True, False])
    assignments.to_csv(
        os.path.join(args.output_dir, "cluster_assignments.tsv"), sep="\t", index=False
    )

    # Cluster summary: size, radius (= max tmDistanceToCentroid in cluster),
    # plus clusterLabel for UI display.
    summary = (
        cluster_df.groupby("clusterId")
        .agg(
            clusterLabel=("clusterLabel", "first"),
            size=("clonotypeKey", "count"),
            radius=("tmDistanceToCentroid", "max"),
            centroidClonotypeKey=("centroidClonotypeKey", "first"),
        )
        .reset_index()
    )
    summary.to_csv(os.path.join(args.output_dir, "cluster_summary.tsv"), sep="\t", index=False)

    # Copy centroid PDBs and emit manifest.
    centroids_manifest_rows: list[dict[str, str]] = []
    seen_centroids: set[str] = set()
    for _, row in cluster_df.drop_duplicates("clusterId").iterrows():
        cid = row["clusterId"]
        cfile = row["centroid_filename"]
        if cfile in seen_centroids:
            continue
        seen_centroids.add(cfile)
        bin_label = row["bin"]
        candidates = [
            os.path.join(args.pdbs_dir, cfile),
            os.path.join(args.pdbs_dir, bin_label, cfile),
        ]
        src = next((p for p in candidates if os.path.exists(p)), None)
        if src is None:
            print(f"warning: centroid PDB not found for cluster {cid} ({cfile}); cluster excluded from centroidPdbs")
            continue
        shutil.copy(src, os.path.join(centroids_dir, cfile))
        centroids_manifest_rows.append({"clusterId": cid, "pdb_filename": cfile})

    centroids_manifest = pd.DataFrame(
        centroids_manifest_rows, columns=["clusterId", "pdb_filename"]
    )
    centroids_manifest.to_csv(
        os.path.join(args.output_dir, "centroids_manifest.tsv"), sep="\t", index=False
    )

    total = len(assignments)
    singletons = int((summary["size"] == 1).sum())
    summary_json = {
        "totalRows": total,
        "clusterCount": int(len(summary)),
        "singletonCount": singletons,
        "singletonRate": (singletons / total) if total > 0 else 0.0,
        "emptyInput": total == 0,
    }
    with open(os.path.join(args.output_dir, "summary.json"), "w") as fh:
        json.dump(summary_json, fh)

    print(
        f"Wrote {len(summary)} clusters covering {total} clonotypes "
        f"({singletons} singletons; {len(centroids_manifest_rows)} centroid PDBs copied)"
    )


if __name__ == "__main__":
    main()
