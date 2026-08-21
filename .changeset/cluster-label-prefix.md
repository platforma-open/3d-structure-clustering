---
'@platforma-open/milaboratories.3d-structure-clustering.software': patch
'@platforma-open/milaboratories.3d-structure-clustering.workflow': patch
'@platforma-open/milaboratories.3d-structure-clustering': patch
---

Prefix cluster labels that carry no recognised record prefix

A cluster is labelled from its representative record's label, with a leading `C-` (MiXCR) or `P-`
(peptide) rewritten to `CL-`. An imported set's labels are the scientist's own identifiers —
`AB-001`, `trastuzumab` — so nothing was rewritten and the cluster appeared under a bare record
name, reading as a record rather than a cluster.

Such labels now get `CL-` prepended: `AB-001` becomes `CL-AB-001`. MiXCR and peptide labels are
unchanged. Labels already starting with `CL-` are left alone.

The same change clonotype-clustering made, applied here deliberately rather than incidentally:
both blocks label clusters from the same upstream `pl7.app/label` column, and a scientist can see
both in one project, so the two must agree.

`synthetic-repertoire-profiler` labels variants `V-XXXXX`, which the rewrite did not match either,
so amplicon clusters were also showing a bare record label and now read `CL-V-XXXXX`. Adding `V`
to the rewrite instead would give `CL-XXXXX` and match MiXCR and peptide, but that changes labels
for an existing modality and is left to whoever owns that call — as in clonotype-clustering.

A cluster whose representative has no upstream label at all still falls back to the bare centroid
key. That path is unchanged: the key is a hash, and prefixing it would present a degraded
fallback as a real label.
