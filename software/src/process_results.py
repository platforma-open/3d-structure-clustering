"""Parse FoldSeek's cluster.tsv, compute per-pair TM-distances via tmtools,
and emit the per-cluster + per-sample-cluster outputs consumed by the workflow.

Multi-chain PDB handling
------------------------
FoldSeek's ``easy-cluster`` treats every chain as an independent entity, so for
H+L (paired) PDBs ``result_cluster.tsv`` emits per-chain rows (``<key>_H``,
``<key>_L``) which may land under different centroids. We resolve this by
declaring H the cluster-defining chain:

- ``cluster.tsv`` rows are filtered to the *primary* chain of each member
  (``"H"`` if present in the PDB, otherwise the first chain by alphabetical
  order — flagged with a warning). Single-chain PDBs surface in cluster.tsv
  without a ``_<chain>`` suffix and are kept as-is.
- ``tmDistanceToCentroid`` is computed on the primary chain only.
- ``member_sequences.tsv`` carries ``sequence_H`` + ``sequence_L`` columns so
  the per-cluster MSA viewer can show both tracks for paired antibodies.
  Single-chain inputs leave ``sequence_L`` empty.

Outputs (under --output-dir):
- cluster_assignments.tsv      clonotypeKey, clusterId, clusterLabel, isCentroid,
                               tmScoreToCentroid, tmDistanceToCentroid
- cluster_summary.tsv          clusterId, clusterLabel, size, radius
- centroids_manifest.tsv       clusterId, pdb_filename
- centroids/                   copies of centroid PDBs
- abundances.tsv               sampleId, clusterId, abundance, abundance_fraction
- abundances-per-cluster.tsv   clusterId, abundance_per_cluster, abundance_fraction_per_cluster
- member_sequences.tsv         clonotypeKey, sequence_H, sequence_L — per-chain
                               amino-acid sequences extracted from each member's
                               PDB chains, in the same scope (full Fv vs CDR-H3
                               fragment) FoldSeek clustered on. sequence_L is
                               empty for single-chain (heavy-only) inputs.
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


def list_pdb_chain_ids(path: str) -> list[str]:
    """Returns the chain IDs present in a PDB file, in file order."""
    structure = get_structure(path)
    return [chain.id for chain in structure.get_chains()]


def load_pdb_chain(path: str, chain_id: str | None) -> tuple | None:
    """Load (coords, sequence) for a specific chain. If chain_id is None, use
    the first chain — appropriate for single-chain PDBs. Returns None if the
    requested chain isn't present."""
    structure = get_structure(path)
    chains = list(structure.get_chains())
    if not chains:
        return None
    if chain_id is None:
        return get_residue_data(chains[0])
    for chain in chains:
        if chain.id == chain_id:
            return get_residue_data(chain)
    return None


def main():
    parser = argparse.ArgumentParser(description="Parse FoldSeek cluster output, compute TM-distance, emit final TSVs.")
    parser.add_argument("--cluster-tsv", required=True, help="FoldSeek result_cluster.tsv")
    parser.add_argument("--manifest", required=True, help="manifest.tsv (clonotypeKey, staged_filename, bin)")
    parser.add_argument("--pdbs-dir", required=True, help="Staged PDBs directory (used for centroid copy)")
    parser.add_argument(
        "--align-pdbs-dir",
        default=None,
        help="Optional separate PDBs directory used for TM-distance alignment "
             "(defaults to --pdbs-dir). In cdrh3 alignment mode this points to "
             "the CDR-H3-sliced PDBs so TM-distance reflects loop similarity, "
             "while --pdbs-dir still points to the full PDBs so centroids "
             "exported to the user remain full antibodies.",
    )
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

    align_pdbs_dir = args.align_pdbs_dir or args.pdbs_dir

    def _resolve_in(base: str, filename: str, bin_label: str) -> str:
        for p in (
            os.path.join(base, filename),
            os.path.join(base, bin_label, filename),
        ):
            if os.path.exists(p):
                return p
        raise SystemExit(f"PDB file not found for {filename} (bin {bin_label}) under {base}")

    def resolve_align_pdb_path(filename: str, bin_label: str) -> str:
        return _resolve_in(align_pdbs_dir, filename, bin_label)

    # Per-PDB chain inventory drives the "primary chain" decision for both
    # cluster-row filtering and sequence extraction. Build it once up front so
    # downstream code can ask `primary_chain(filename)` without re-parsing PDBs.
    pdb_chains_by_filename: dict[str, list[str]] = {}
    for staged_filename, bin_label in file_to_bin.items():
        pdb_path = resolve_align_pdb_path(staged_filename, bin_label)
        pdb_chains_by_filename[staged_filename] = list_pdb_chain_ids(pdb_path)

    # Per-clonotype primary/secondary chain selection. Convention: heavy chain
    # is labelled `H`, light chain `L`. For non-standard chain naming we fall
    # back to alphabetical order and warn so the output is still usable but
    # downstream interpretation is the caller's responsibility.
    primary_chain_by_filename: dict[str, str | None] = {}
    secondary_chain_by_filename: dict[str, str | None] = {}
    warned_non_standard: set[str] = set()
    for staged_filename, chains in pdb_chains_by_filename.items():
        if len(chains) <= 1:
            # Single-chain PDB: FoldSeek emits unsuffixed rows; we pass
            # chain_id=None to load the only chain regardless of its label.
            primary_chain_by_filename[staged_filename] = None
            secondary_chain_by_filename[staged_filename] = None
            continue
        if "H" in chains:
            primary = "H"
        else:
            primary = sorted(chains)[0]
            warned_non_standard.add(staged_filename)
        if "L" in chains and "L" != primary:
            secondary = "L"
        else:
            others = sorted([c for c in chains if c != primary])
            secondary = others[0] if others else None
        primary_chain_by_filename[staged_filename] = primary
        secondary_chain_by_filename[staged_filename] = secondary

    if warned_non_standard:
        sample = sorted(warned_non_standard)[:3]
        print(
            f"warning: {len(warned_non_standard)} multi-chain PDB(s) lack a chain labelled 'H'; "
            f"falling back to alphabetical first-chain as primary "
            f"(examples: {sample})"
        )

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

    def normalize_filename(name: str) -> tuple[str, str | None]:
        """Map a FoldSeek-emitted filename back to the manifest entry plus
        chain id. For multi-chain PDBs FoldSeek strips `.pdb` and appends
        `_<chain_id>` to the stem (e.g. `<key>_L`); single-chain PDBs come
        through unsuffixed. Returns (manifest_filename, chain_id)."""
        if name in file_to_ck:
            return name, None
        if f"{name}.pdb" in file_to_ck:
            return f"{name}.pdb", None
        if "_" in name:
            stem, chain_id = name.rsplit("_", 1)
            if f"{stem}.pdb" in file_to_ck:
                return f"{stem}.pdb", chain_id
            if stem in file_to_ck:
                return stem, chain_id
        return name, None

    cluster_df = pd.read_csv(
        args.cluster_tsv, sep="\t", header=None, names=["centroid_raw", "member_raw"], dtype=str
    )
    centroid_pairs = cluster_df["centroid_raw"].apply(normalize_filename)
    member_pairs = cluster_df["member_raw"].apply(normalize_filename)
    cluster_df["centroid_filename"] = [p[0] for p in centroid_pairs]
    cluster_df["centroid_chain"] = [p[1] for p in centroid_pairs]
    cluster_df["member_filename"] = [p[0] for p in member_pairs]
    cluster_df["member_chain"] = [p[1] for p in member_pairs]
    cluster_df["clonotypeKey"] = cluster_df["member_filename"].map(file_to_ck)
    cluster_df["bin"] = cluster_df["member_filename"].map(file_to_bin)
    cluster_df["centroidClonotypeKey"] = cluster_df["centroid_filename"].map(file_to_ck)

    if cluster_df["clonotypeKey"].isna().any():
        missing = cluster_df[cluster_df["clonotypeKey"].isna()]["member_raw"].tolist()
        raise SystemExit(
            f"FoldSeek output references unknown member files: {missing[:5]} (manifest mismatch)"
        )

    # H-driven cluster assignment: keep only rows whose member chain matches
    # the member PDB's primary chain (None for single-chain, "H" for paired
    # antibody Fvs). L-chain FoldSeek decisions are discarded for the cluster
    # assignment; the L-chain sequence is still surfaced in member_sequences.
    # NaN==NaN is False in pandas, so single-chain rows (both sides None) need
    # an explicit both-null branch — otherwise every heavy-only row drops out.
    cluster_df["member_primary_chain"] = cluster_df["member_filename"].map(
        primary_chain_by_filename
    )
    mc = cluster_df["member_chain"]
    mpc = cluster_df["member_primary_chain"]
    cluster_df = cluster_df[(mc == mpc) | (mc.isna() & mpc.isna())]
    cluster_df = cluster_df.drop(columns=["member_primary_chain"]).reset_index(drop=True)

    # FoldSeek can still emit multiple primary-chain rows per input file (chain
    # duplications, domain variants) that collapse to the same clonotypeKey.
    # Keep the row where member==centroid when present (self-assignment wins).
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

    # Cache only centroids: each centroid is reused across every member of its
    # cluster, so re-parsing it N times is wasteful. Members are each used
    # exactly once — caching them would balloon memory on large datasets
    # without speeding anything up.
    centroid_cache: dict[str, tuple] = {}

    def load_primary_centroid(filename: str, bin_label: str):
        cached = centroid_cache.get(filename)
        if cached is not None:
            return cached
        chain_id = primary_chain_by_filename.get(filename)
        data = load_pdb_chain(resolve_align_pdb_path(filename, bin_label), chain_id)
        if data is None:
            raise SystemExit(
                f"Primary chain {chain_id!r} not found in PDB {filename} "
                f"(available chains: {pdb_chains_by_filename.get(filename, [])})"
            )
        centroid_cache[filename] = data
        return data

    # TM-score is computed on the primary chain only (heavy chain for paired
    # Fvs). Normalised by chain1 (member) length — the conventional reading.
    # Sequences are extracted from the same PDBs used for alignment, so the
    # MSA viewer sees CDR-H3 fragments in cdrh3 mode and full chains otherwise.
    tm_scores: list[float] = []
    member_sequences_h: list[str] = []
    member_sequences_l: list[str] = []
    for _, row in cluster_df.iterrows():
        primary = primary_chain_by_filename.get(row["member_filename"])
        secondary = secondary_chain_by_filename.get(row["member_filename"])
        member_path = resolve_align_pdb_path(row["member_filename"], row["bin"])

        primary_data = load_pdb_chain(member_path, primary)
        if primary_data is None:
            raise SystemExit(
                f"Primary chain {primary!r} not found in PDB {row['member_filename']}"
            )
        m_coords, m_seq = primary_data

        if row["isCentroid"] == 1:
            tm_scores.append(1.0)
        else:
            c_coords, c_seq = load_primary_centroid(row["centroid_filename"], row["bin"])
            result = tm_align(m_coords, c_coords, m_seq, c_seq)
            tm_scores.append(max(0.0, min(1.0, float(result.tm_norm_chain1))))

        member_sequences_h.append(m_seq)
        if secondary is None:
            member_sequences_l.append("")
        else:
            secondary_data = load_pdb_chain(member_path, secondary)
            member_sequences_l.append(secondary_data[1] if secondary_data is not None else "")

    cluster_df["tmScoreToCentroid"] = tm_scores
    cluster_df["tmDistanceToCentroid"] = 1.0 - cluster_df["tmScoreToCentroid"]
    cluster_df["sequence_H"] = member_sequences_h
    cluster_df["sequence_L"] = member_sequences_l

    member_seq_df = (
        cluster_df[["clonotypeKey", "sequence_H", "sequence_L"]]
        .drop_duplicates("clonotypeKey")
        .sort_values("clonotypeKey")
    )
    member_seq_df.to_csv(
        os.path.join(args.output_dir, "member_sequences.tsv"), sep="\t", index=False
    )

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
    # hasLightChain drives the MSA viewer's sequence-column filter on the UI
    # side. Heavy-only inputs (single-chain PDBs) write all-empty sequence_L
    # values; without this flag the viewer would still try to align the empty
    # L track and kalign would error with "0 sequences found".
    has_light_chain = any(seq for seq in member_sequences_l)
    summary_json = {
        "totalRows": total,
        "clusterCount": int(len(summary)),
        "singletonCount": singletons,
        "singletonRate": (singletons / total) if total > 0 else 0.0,
        "emptyInput": total == 0,
        "hasLightChain": has_light_chain,
    }
    with open(os.path.join(args.output_dir, "summary.json"), "w") as fh:
        json.dump(summary_json, fh)

    print(
        f"Wrote {len(summary)} clusters covering {total} clonotypes "
        f"({singletons} singletons; {len(centroids_manifest_rows)} centroid PDBs copied)"
    )


if __name__ == "__main__":
    main()
