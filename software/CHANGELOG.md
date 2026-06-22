# @platforma-open/milaboratories.3d-structure-clustering.software

## 1.1.1

### Patch Changes

- c635aff: Migrate block onto the structurer (block-tools 2.11.0) — full SDK upgrade: model/ui-vue/test 1.79.14, workflow-tengo 6.6.3, tengo-builder 4.0.8, ts-builder 1.5.2. Adopts the canonical tool-managed layout (oxlint/oxfmt across model/ui/test, tsconfig, turbo, block index, scaffold-owned CI workflows, managed package.json + catalog).

## 1.1.0

### Minor Changes

- 94cb563: Select the 3D structures dataset directly. The upstream 3D Structure Prediction block now exports a confident-only PDB map, so there is no subset to choose: the settings panel uses the standard `PlDatasetSelector` to pick the PDB dataset directly (replacing the subset-only `PlDatasetSubsetSelector`), and the model no longer attaches subset filters (which had begun surfacing unrelated upstream subsets such as Lead Selection's). Removes the now-dead confident-subset filtering machinery (`filter-pdbs` / `build-filtered-pdbs-map` templates and the `filter_pdbs.py` software entrypoint).

## 1.0.3

### Patch Changes

- 7ce563e: Stage PDBs under synthetic FoldSeek-safe filenames instead of the raw clonotypeKey. FoldSeek does not echo arbitrary filename stems back verbatim, which broke the member→clonotypeKey round-trip in process_results.py for certain datasets ("FoldSeek output references unknown member files"). The clonotypeKey↔filename mapping is now carried solely through the manifest.

## 1.0.2

### Patch Changes

- 2ce6662: Fix release error

## 1.0.1

### Patch Changes

- 0f9d457: Multiple improvements: add 3d viewer and msa, introduce different alignment modes, deduplication
