"""Parse FoldSeek's cluster.tsv, compute per-pair TM-distances via tmtools,
and emit the per-cluster + per-sample-cluster outputs consumed by the workflow.

Outputs (under --output-dir):
- cluster_assignments.tsv      clonotypeKey, clusterId, clusterLabel, isCentroid,
                               tmScoreToCentroid, tmDistanceToCentroid
- cluster_summary.tsv          clusterId, clusterLabel, size, radius
- centroids_manifest.tsv       clusterId, pdb_filename
- centroids/                   copies of centroid PDBs
- abundances.tsv               sampleId, clusterId, abundance, abundance_fraction
- abundances-per-cluster.tsv   clusterId, abundance_per_cluster, abundance_fraction_per_cluster
- summary.json                 totalRows, clusterCount, singletonCount, singletonRate, emptyInput
"""

import argparse
import json
import os
import re
import shutil

import pandas as pd
from tmtools import tm_align
from tmtools.io import get_residue_data, get_structure

# Upstream `pl7.app/label` values carry `C-` (MiXCR) or `P-` (peptide) prefix;
# rewrite to `CL-` so cluster labels mirror clonotype-clustering.
_CLUSTER_LABEL_PREFIX_RE = re.compile(r"^[CP]-")


def cluster_label_from(centroid_clonotype_key: str, key_to_label: dict[str, str]) -> str:
    raw = key_to_label.get(centroid_clonotype_key) or ""
    if not raw:
        return centroid_clonotype_key
    return _CLUSTER_LABEL_PREFIX_RE.sub("CL-", raw)


def load_pdb_coords(path: str) -> tuple:
    structure = get_structure(path)
    chain = next(structure.get_chains())
    return get_residue_data(chain)


def main():
    parser = argparse.ArgumentParser(description="Parse FoldSeek cluster output, compute TM-distance, emit final TSVs.")
    parser.add_argument("--cluster-tsv", required=True, help="FoldSeek result_cluster.tsv")
    parser.add_argument("--manifest", required=True, help="manifest.tsv (clonotypeKey, staged_filename, bin)")
    parser.add_argument("--pdbs-dir", required=True, help="Staged PDBs directory")
    parser.add_argument("--output-dir", default="results", help="Output directory")
    parser.add_argument("--labels-tsv", default=None,
                        help="Optional clonotype-labels TSV (axis-key first column + clonotypeLabel). "
                             "Without it, clusterLabel falls back to the centroid clonotypeKey hash.")
    parser.add_argument("--abundance-tsv", required=True,
                        help="Upstream abundance TSV (sampleId, clonotypeKey, abundance).")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    centroids_dir = os.path.join(args.output_dir, "centroids")
    os.makedirs(centroids_dir, exist_ok=True)

    manifest = pd.read_csv(args.manifest, sep="\t", dtype=str)
    file_to_ck = dict(zip(manifest["staged_filename"], manifest["clonotypeKey"]))
    file_to_bin = dict(zip(manifest["staged_filename"], manifest["bin"]))

    # Labels TSV is written by `pt`; first column header is the JSON-encoded
    # axis spec, so read by position.
    key_to_label: dict[str, str] = {}
    if args.labels_tsv:
        labels_df = pd.read_csv(args.labels_tsv, sep="\t", dtype=str)
        if labels_df.shape[1] >= 2 and "clonotypeLabel" in labels_df.columns:
            key_col = labels_df.columns[0]
            key_to_label = dict(
                zip(labels_df[key_col], labels_df["clonotypeLabel"].fillna(""))
            )

    def normalize_filename(name: str) -> str:
        # FoldSeek strips `.pdb`; for multi-chain PDBs it appends `_<chain_id>`
        # to the stem (e.g. `<key>_L`). Resolve back to the manifest filename.
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

    # FoldSeek can emit multiple rows per input file (chain/domain variants)
    # that collapse to the same clonotypeKey after normalize_filename. Keep
    # the row where member==centroid when present (so self-assignment wins).
    is_self = cluster_df["member_filename"] == cluster_df["centroid_filename"]
    cluster_df = (
        cluster_df.assign(_self_first=(~is_self).astype(int))
        .sort_values(["member_filename", "_self_first"])
        .drop_duplicates("member_filename", keep="first")
        .drop(columns=["_self_first"])
        .reset_index(drop=True)
    )

    cluster_df["clusterId"] = cluster_df["centroidClonotypeKey"]
    cluster_df["clusterLabel"] = cluster_df["centroidClonotypeKey"].map(
        lambda k: cluster_label_from(k, key_to_label)
    )
    cluster_df["isCentroid"] = (
        cluster_df["clonotypeKey"] == cluster_df["centroidClonotypeKey"]
    ).astype("Int64")

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

    # TM-score normalised by chain1 (member) length — the conventional reading.
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

    # Abundance aggregates. Inner-join with the cluster set drops abundance
    # rows for clonotypes without a PDB. Per-sample fraction sums to 1 within
    # each sample; per-cluster fraction sums to 1 globally.
    abundance_df = pd.read_csv(
        args.abundance_tsv,
        sep="\t",
        dtype={"sampleId": str, "clonotypeKey": str},
    )
    abundance_df["abundance"] = pd.to_numeric(abundance_df["abundance"], errors="coerce").fillna(0.0)

    clusters_for_join = cluster_df[["clonotypeKey", "clusterId"]].drop_duplicates("clonotypeKey")
    abundance_joined = abundance_df.merge(clusters_for_join, on="clonotypeKey", how="inner")

    per_sample_cluster = (
        abundance_joined.groupby(["sampleId", "clusterId"], as_index=False)["abundance"].sum()
    )
    sample_totals = per_sample_cluster.groupby("sampleId")["abundance"].transform("sum")
    per_sample_cluster["abundance_fraction"] = (
        per_sample_cluster["abundance"] / sample_totals
    ).fillna(0.0)
    per_sample_cluster.to_csv(
        os.path.join(args.output_dir, "abundances.tsv"), sep="\t", index=False
    )

    per_cluster = (
        per_sample_cluster.groupby("clusterId", as_index=False)["abundance"]
        .sum()
        .rename(columns={"abundance": "abundance_per_cluster"})
    )
    grand_total = float(per_cluster["abundance_per_cluster"].sum())
    per_cluster["abundance_fraction_per_cluster"] = (
        per_cluster["abundance_per_cluster"] / grand_total if grand_total > 0 else 0.0
    )
    per_cluster.to_csv(
        os.path.join(args.output_dir, "abundances-per-cluster.tsv"), sep="\t", index=False
    )

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
