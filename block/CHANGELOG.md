# @platforma-open/milaboratories.3d-structure-clustering

## 1.0.6

### Patch Changes

- 7ce563e: Stage PDBs under synthetic FoldSeek-safe filenames instead of the raw clonotypeKey. FoldSeek does not echo arbitrary filename stems back verbatim, which broke the member→clonotypeKey round-trip in process_results.py for certain datasets ("FoldSeek output references unknown member files"). The clonotypeKey↔filename mapping is now carried solely through the manifest.
- Updated dependencies [7ce563e]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.0.5
  - @platforma-open/milaboratories.3d-structure-clustering.ui@1.0.5
  - @platforma-open/milaboratories.3d-structure-clustering.workflow@1.0.5

## 1.0.5

### Patch Changes

- d04a8ac: Drop the filter native-label override in the dataset selector. 3d-structure-prediction now emits per-kind trace labels (e.g. `"Confident structures - <instance>"`), so `deriveDistinctLabels` already returns unique, instance-aware labels — the override was clipping them back to just `"Confident structures"` and losing the instance discriminator when multiple prediction blocks were present. Chain-aware primary-label naming is unchanged.
- Updated dependencies [d04a8ac]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.0.4
  - @platforma-open/milaboratories.3d-structure-clustering.ui@1.0.4

## 1.0.4

### Patch Changes

- @platforma-open/milaboratories.3d-structure-clustering.workflow@1.0.4

## 1.0.3

### Patch Changes

- Updated dependencies [3bbd5eb]
  - @platforma-open/milaboratories.3d-structure-clustering.workflow@1.0.3
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.0.3
  - @platforma-open/milaboratories.3d-structure-clustering.ui@1.0.3

## 1.0.2

### Patch Changes

- a2dd3d6: Expose parameter-driven cluster label in trace. Linker columns now carry a `milaboratories.3d-structure-clustering.clustering` trace element whose label follows the block's customBlockLabel / defaultBlockLabel — so downstream consumers (lead-selection) can show a meaningful cluster choice instead of the generic "Cluster" fallback.
- Updated dependencies [a2dd3d6]
  - @platforma-open/milaboratories.3d-structure-clustering.workflow@1.0.2
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.0.2
  - @platforma-open/milaboratories.3d-structure-clustering.ui@1.0.2

## 1.0.1

### Patch Changes

- Updated dependencies [0f9d457]
  - @platforma-open/milaboratories.3d-structure-clustering.workflow@1.0.1
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.0.1
  - @platforma-open/milaboratories.3d-structure-clustering.ui@1.0.1
