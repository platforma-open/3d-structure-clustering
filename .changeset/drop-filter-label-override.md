---
'@platforma-open/milaboratories.3d-structure-clustering.model': patch
'@platforma-open/milaboratories.3d-structure-clustering': patch
---

Drop the filter native-label override in the dataset selector. 3d-structure-prediction now emits per-kind trace labels (e.g. `"Confident structures - <instance>"`), so `deriveDistinctLabels` already returns unique, instance-aware labels — the override was clipping them back to just `"Confident structures"` and losing the instance discriminator when multiple prediction blocks were present. Chain-aware primary-label naming is unchanged.