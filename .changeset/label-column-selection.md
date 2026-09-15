---
'@platforma-open/milaboratories.3d-structure-clustering.workflow': patch
'@platforma-open/milaboratories.3d-structure-clustering': patch
---

Pick the upstream `pl7.app/label` column, not the first one the pool returns

The clonotype axis can carry more than one `pl7.app/label` column. MiXCR or the import block writes
the source column. Each 3D Structure Prediction run re-exports a copy over the records it predicted.
The workflow took the first column in the list. The pool orders that list by block id, which says
nothing about where a column came from. When a copy from a prediction run over a different subset
came first, every centroid outside that subset had no label. The Cluster Id column then showed the
raw clonotype key.

The workflow now takes the label column with the fewest `pl7.app/trace` steps. That column is the
source column. Ties resolve on the bundle key, so the choice is the same on every run.
