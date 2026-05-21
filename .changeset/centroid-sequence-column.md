---
'@platforma-open/milaboratories.3d-structure-clustering.workflow': patch
'@platforma-open/milaboratories.3d-structure-clustering.model': patch
---

Add centroid heavy/light chain sequence columns to the per-cluster result table. Sequences are extracted from the centroid PDB by `process_results.py` and projected onto the cluster axis as a separate `centroid_sequences.tsv` (mirrors clonotype-clustering's `clusterToSeq` pattern). The light-chain column is hidden on heavy-only datasets via `hasLightChain`.
