# @platforma-open/milaboratories.3d-structure-clustering

## 1.1.1

### Patch Changes

- c635aff: Migrate block onto the structurer (block-tools 2.11.0) — full SDK upgrade: model/ui-vue/test 1.79.14, workflow-tengo 6.6.3, tengo-builder 4.0.8, ts-builder 1.5.2. Adopts the canonical tool-managed layout (oxlint/oxfmt across model/ui/test, tsconfig, turbo, block index, scaffold-owned CI workflows, managed package.json + catalog).
- Updated dependencies [c635aff]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.1.1
  - @platforma-open/milaboratories.3d-structure-clustering.ui@1.1.1
  - @platforma-open/milaboratories.3d-structure-clustering.workflow@1.1.1

## 1.1.0

### Minor Changes

- 94cb563: Select the 3D structures dataset directly. The upstream 3D Structure Prediction block now exports a confident-only PDB map, so there is no subset to choose: the settings panel uses the standard `PlDatasetSelector` to pick the PDB dataset directly (replacing the subset-only `PlDatasetSubsetSelector`), and the model no longer attaches subset filters (which had begun surfacing unrelated upstream subsets such as Lead Selection's). Removes the now-dead confident-subset filtering machinery (`filter-pdbs` / `build-filtered-pdbs-map` templates and the `filter_pdbs.py` software entrypoint).

### Patch Changes

- Updated dependencies [94cb563]
  - @platforma-open/milaboratories.3d-structure-clustering.workflow@1.1.0
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.1.0
  - @platforma-open/milaboratories.3d-structure-clustering.ui@1.1.0

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
