"""Slice each PDB in --input-dir to its CDR-H3 region.

Reads `REMARK 99 PLATFORMA CDRH3 <chain><lo>-<chain><hi>` from each PDB to
identify the chain + residue range, then writes ATOM/HETATM records whose
residue sequence number is within `[lo, hi]` (inclusive) on that chain into
`--output-dir`, preserving the source filename. Optional `--flank` extends
the kept range on both sides — useful when raw CDR-H3 is too short for
FoldSeek's TM-align to score reliably.

PDBs without a recognized CDR-H3 REMARK are reported as warnings and copied
through unchanged so downstream pipeline doesn't drop them silently. PDBs
whose CDR-H3 range produces zero ATOM lines are reported and copied through
unchanged as well — this indicates a numbering-scheme mismatch between the
REMARK and the ATOM records, which is a prediction-side bug.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path

# Tolerant of the leading whitespace variation FoldSeek/biopython sometimes
# emit ("REMARK  99" vs "REMARK 99"); matches an optional insertion code on
# both endpoints in case a future REMARK encodes one.
REMARK_RE = re.compile(
    r"^REMARK\s+99\s+PLATFORMA\s+CDRH3\s+([A-Za-z])(\d+)[A-Za-z]?-[A-Za-z](\d+)[A-Za-z]?",
)


def _parse_cdrh3_remark(src: Path) -> tuple[str, int, int] | None:
    with open(src) as fh:
        for line in fh:
            if not line.startswith("REMARK"):
                # CDR REMARKs are injected ahead of ATOM/HETATM/MODEL; once we
                # leave the header section there's nothing left to find.
                if line.startswith(("ATOM", "HETATM", "MODEL")):
                    break
                continue
            m = REMARK_RE.match(line.rstrip())
            if m:
                return m.group(1), int(m.group(2)), int(m.group(3))
    return None


def _slice_pdb(src: Path, dst: Path, chain: str, lo: int, hi: int, flank: int) -> int:
    """Write a CDR-H3 slice of `src` to `dst`. Returns kept ATOM/HETATM count."""
    kept = 0
    kept_end = False
    lo_eff = lo - flank
    hi_eff = hi + flank
    with open(src) as fh_in, open(dst, "w") as fh_out:
        for line in fh_in:
            record = line[:6]
            if record.startswith(("ATOM", "HETATM")):
                # PDB columns: chain id at 22 (1-based 22), resSeq at 23-26.
                line_chain = line[21:22]
                try:
                    resseq = int(line[22:26].strip())
                except ValueError:
                    continue
                if line_chain == chain and lo_eff <= resseq <= hi_eff:
                    fh_out.write(line)
                    kept += 1
            elif line.startswith(("HEADER", "TITLE", "CRYST", "ORIG", "SCALE", "REMARK")):
                fh_out.write(line)
            elif line.startswith("TER"):
                # Keep TER for the kept chain only; if nothing was kept yet
                # the TER will be from a chain we skipped.
                if kept > 0:
                    fh_out.write(line)
            elif line.startswith("END"):
                fh_out.write(line)
                kept_end = True
        if kept > 0 and not kept_end:
            fh_out.write("END\n")
    return kept


def main() -> None:
    parser = argparse.ArgumentParser(description="Slice PDBs to CDR-H3 region.")
    parser.add_argument("--input-dir", required=True, help="Directory of input PDBs")
    parser.add_argument("--output-dir", required=True, help="Directory to write sliced PDBs")
    parser.add_argument(
        "--flank",
        type=int,
        default=0,
        help="Extra residues to keep on each side of CDR-H3 (default 0)",
    )
    args = parser.parse_args()

    src_dir = Path(args.input_dir)
    dst_dir = Path(args.output_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    sliced = 0
    no_remark = 0
    empty = 0
    for src in sorted(src_dir.iterdir()):
        if not src.name.endswith(".pdb"):
            continue
        dst = dst_dir / src.name
        parsed = _parse_cdrh3_remark(src)
        if parsed is None:
            no_remark += 1
            print(f"warning: no CDRH3 REMARK in {src.name}; copying through unchanged")
            shutil.copy(src, dst)
            continue
        chain, lo, hi = parsed
        kept = _slice_pdb(src, dst, chain, lo, hi, args.flank)
        if kept == 0:
            empty += 1
            print(
                f"warning: CDRH3 range {chain}{lo}-{chain}{hi} matched no ATOM "
                f"records in {src.name} (numbering-scheme mismatch?); "
                f"copying through unchanged"
            )
            shutil.copy(src, dst)
            continue
        sliced += 1

    print(
        f"sliced {sliced} PDBs to CDR-H3 "
        f"(flank={args.flank}); {no_remark} without REMARK; "
        f"{empty} with empty slice — both passed through unchanged"
    )


if __name__ == "__main__":
    main()
