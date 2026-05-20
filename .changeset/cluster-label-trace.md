---
'@platforma-open/milaboratories.3d-structure-clustering.workflow': patch
'@platforma-open/milaboratories.3d-structure-clustering.model': patch
'@platforma-open/milaboratories.3d-structure-clustering.ui': patch
'@platforma-open/milaboratories.3d-structure-clustering': patch
---

Expose parameter-driven cluster label in trace. Linker columns now carry a `milaboratories.3d-structure-clustering.clustering` trace element whose label follows the block's customBlockLabel / defaultBlockLabel — so downstream consumers (lead-selection) can show a meaningful cluster choice instead of the generic "Cluster" fallback.