# @platforma-open/milaboratories.3d-structure-clustering.ui

## 1.1.3

### Patch Changes

- a7329d2: Migrate to the latest block template and add the mandatory kind package

  Refreshed onto block-tools 2.14.3 via `upgrade-sdk`, and added the `kind/`
  package every block must now declare. The kind carries the block's identity
  (`{name}@{version}`, read from its own `package.json`) and its init-params
  contract.

  `BlockParams` is the five settings that change what the clustering produces:
  `clusteringMode`, `alignmentType`, `tmScoreThreshold`, `coverageThreshold` and
  `cdrh3FlankResidues`. All are optional, so a project template can seed any
  subset and the model's `init` keeps a default behind each. `.templateParams`
  projects the same five back, so export and apply are inverses. `dataset` is
  excluded by construction — it is an anchor-bound selection that cannot travel
  between projects. `cpu` and `mem` are excluded because they describe the machine
  a run gets, not the analysis. The two setting vocabularies moved from
  `model/src/types.ts` into the kind, which owns them; the model re-exports them so
  every consumer keeps working.

  Author-code fixes the upgrade required:

  - `OutputColumnProvider` is gone from `@platforma-sdk/model`. The clusters table
    now uses `AccessorColumnsProvider` (a memoised factory, not a constructor) and
    `getColumns()` / `getSpec()`.
  - `ColumnVisibilityRule.match` is a declarative `ColumnSelector` now, not a
    predicate. The rule that hides the L centroid sequence on heavy-only datasets
    became `{ name, domain }`.
  - The test used the facade's old `blockSpec` export, which the slim facade
    replaced with a from-pack-v2 `BlockPointer`.
  - `@platforma-sdk/ui-vue` is on 1.83.3, which publishes the
    `dist/components/*.vue.d.ts` its own `lib.d.ts` re-exports again. 1.83.1 had
    dropped them, and the slim facade inlines the model's whole public type
    surface, so `BlockData`'s `GraphMakerState` reached those missing files
    through graph-maker and the facade build failed.
  - The model declares `@platforma-sdk/ui-vue` directly so graph-maker's peer
    resolves to the catalog version instead of floating to the newest published
    one.

  The software package moves from `pl-pkg` to `block-tools software build`.

- Updated dependencies [fbd79e3]
- Updated dependencies [a7329d2]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.2.1

## 1.1.2

### Patch Changes

- Updated dependencies [2c7c718]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.2.0

## 1.1.1

### Patch Changes

- c635aff: Migrate block onto the structurer (block-tools 2.11.0) — full SDK upgrade: model/ui-vue/test 1.79.14, workflow-tengo 6.6.3, tengo-builder 4.0.8, ts-builder 1.5.2. Adopts the canonical tool-managed layout (oxlint/oxfmt across model/ui/test, tsconfig, turbo, block index, scaffold-owned CI workflows, managed package.json + catalog).
- Updated dependencies [c635aff]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.1.1

## 1.1.0

### Minor Changes

- 94cb563: Select the 3D structures dataset directly. The upstream 3D Structure Prediction block now exports a confident-only PDB map, so there is no subset to choose: the settings panel uses the standard `PlDatasetSelector` to pick the PDB dataset directly (replacing the subset-only `PlDatasetSubsetSelector`), and the model no longer attaches subset filters (which had begun surfacing unrelated upstream subsets such as Lead Selection's). Removes the now-dead confident-subset filtering machinery (`filter-pdbs` / `build-filtered-pdbs-map` templates and the `filter_pdbs.py` software entrypoint).

### Patch Changes

- Updated dependencies [94cb563]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.1.0

## 1.0.5

### Patch Changes

- 7ce563e: Stage PDBs under synthetic FoldSeek-safe filenames instead of the raw clonotypeKey. FoldSeek does not echo arbitrary filename stems back verbatim, which broke the member→clonotypeKey round-trip in process_results.py for certain datasets ("FoldSeek output references unknown member files"). The clonotypeKey↔filename mapping is now carried solely through the manifest.
- Updated dependencies [7ce563e]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.0.5

## 1.0.4

### Patch Changes

- Updated dependencies [d04a8ac]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.0.4

## 1.0.3

### Patch Changes

- Updated dependencies [3bbd5eb]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.0.3

## 1.0.2

### Patch Changes

- a2dd3d6: Expose parameter-driven cluster label in trace. Linker columns now carry a `milaboratories.3d-structure-clustering.clustering` trace element whose label follows the block's customBlockLabel / defaultBlockLabel — so downstream consumers (lead-selection) can show a meaningful cluster choice instead of the generic "Cluster" fallback.
- Updated dependencies [a2dd3d6]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.0.2

## 1.0.1

### Patch Changes

- 0f9d457: Multiple improvements: add 3d viewer and msa, introduce different alignment modes, deduplication
- Updated dependencies [0f9d457]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.0.1
