---
'@platforma-open/milaboratories.3d-structure-clustering.model': minor
'@platforma-open/milaboratories.3d-structure-clustering': minor
---

Accept structures predicted from synthetic-repertoire-profiler VDJ datasets

The dataset picker now admits a `pl7.app/variantKey` row axis that declares
`pl7.app/modality: vdj`, alongside the existing import-vdj-data sets. This
mirrors the gate 3D Structure Prediction opened in the same round — the PDB
column inherits its row axis from whatever that block was pointed at, so the two
tests stay identical by design.

Nothing else in the block needed changing, and that is worth recording. The gate
was its only `pl7.app/vdj/*` dependency:

- The primary abundance is discovered by annotation, not by name. A profiler run
  emits `pl7.app/readCount` on `[sampleId, variantKey]` with
  `pl7.app/abundance/isPrimary` set and `normalized` false, which is exactly what
  the workflow's selector asks for. The abundance unit already reads "reads"
  unless the column name says molecules.
- Row labels come from `pl7.app/label` on the record axis. The profiler emits one
  ("Variant Id"), and the existing label rule prepends `CL-` to a label carrying
  no `C-` / `P-` prefix.
- CDR-H3 slicing keeps working. The `REMARK 99 PLATFORMA CDRH3` record is written
  by 3D Structure Prediction from ANARCI numbering of the sequence itself, not
  from any upstream VDJ feature column.
- A profiler run frames variants against one parent and carries no chain key, so
  it folds in NanoBodyBuilder2 mode and yields heavy-only structures. The
  workflow already derives `hasLightChain` from the PDB contents, so the MSA
  viewer drops the empty L track on its own.
