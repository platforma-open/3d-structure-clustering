---
'@platforma-open/milaboratories.3d-structure-clustering.workflow': minor
'@platforma-open/milaboratories.3d-structure-clustering.model': minor
'@platforma-open/milaboratories.3d-structure-clustering.ui': minor
'@platforma-open/milaboratories.3d-structure-clustering.software': minor
'@platforma-open/milaboratories.3d-structure-clustering': minor
---

Select the 3D structures dataset directly. The upstream 3D Structure Prediction block now exports a confident-only PDB map, so there is no subset to choose: the settings panel uses the standard `PlDatasetSelector` to pick the PDB dataset directly (replacing the subset-only `PlDatasetSubsetSelector`), and the model no longer attaches subset filters (which had begun surfacing unrelated upstream subsets such as Lead Selection's). Removes the now-dead confident-subset filtering machinery (`filter-pdbs` / `build-filtered-pdbs-map` templates and the `filter_pdbs.py` software entrypoint).
