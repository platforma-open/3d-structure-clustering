# @platforma-open/milaboratories.3d-structure-clustering.model

## 1.1.0

### Minor Changes

- 94cb563: Select the 3D structures dataset directly. The upstream 3D Structure Prediction block now exports a confident-only PDB map, so there is no subset to choose: the settings panel uses the standard `PlDatasetSelector` to pick the PDB dataset directly (replacing the subset-only `PlDatasetSubsetSelector`), and the model no longer attaches subset filters (which had begun surfacing unrelated upstream subsets such as Lead Selection's). Removes the now-dead confident-subset filtering machinery (`filter-pdbs` / `build-filtered-pdbs-map` templates and the `filter_pdbs.py` software entrypoint).

## 1.0.5

### Patch Changes

- 7ce563e: Stage PDBs under synthetic FoldSeek-safe filenames instead of the raw clonotypeKey. FoldSeek does not echo arbitrary filename stems back verbatim, which broke the member→clonotypeKey round-trip in process_results.py for certain datasets ("FoldSeek output references unknown member files"). The clonotypeKey↔filename mapping is now carried solely through the manifest.

## 1.0.4

### Patch Changes

- d04a8ac: Drop the filter native-label override in the dataset selector. 3d-structure-prediction now emits per-kind trace labels (e.g. `"Confident structures - <instance>"`), so `deriveDistinctLabels` already returns unique, instance-aware labels — the override was clipping them back to just `"Confident structures"` and losing the instance discriminator when multiple prediction blocks were present. Chain-aware primary-label naming is unchanged.

## 1.0.3

### Patch Changes

- 3bbd5eb: Add centroid heavy/light chain sequence columns to the per-cluster result table. Sequences are extracted from the centroid PDB by `process_results.py` and projected onto the cluster axis as a separate `centroid_sequences.tsv` (mirrors clonotype-clustering's `clusterToSeq` pattern). The light-chain column is hidden on heavy-only datasets via `hasLightChain`.

## 1.0.2

### Patch Changes

- a2dd3d6: Expose parameter-driven cluster label in trace. Linker columns now carry a `milaboratories.3d-structure-clustering.clustering` trace element whose label follows the block's customBlockLabel / defaultBlockLabel — so downstream consumers (lead-selection) can show a meaningful cluster choice instead of the generic "Cluster" fallback.

## 1.0.1

### Patch Changes

- 0f9d457: Multiple improvements: add 3d viewer and msa, introduce different alignment modes, deduplication
