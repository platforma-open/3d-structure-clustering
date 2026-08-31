# @platforma-open/milaboratories.3d-structure-clustering

## 1.2.1

### Patch Changes

- fbd79e3: Accept structures predicted from synthetic-repertoire-profiler VDJ datasets

  The dataset picker now admits a `pl7.app/variantKey` row axis that declares
  `pl7.app/modality: vdj`, alongside the existing import-vdj-data sets. This
  mirrors the gate 3D Structure Prediction opened in the same round — the PDB
  column inherits its row axis from whatever that block was pointed at, so the two
  tests stay identical by design.

  Nothing else in the block needed changing, and that is worth recording. The gate
  was its only `pl7.app/vdj/*` dependency:

  - The primary abundance is discovered by annotation, not by name. A profiler run
    emits `pl7.app/readCount` on `[sampleId, variantKey]` with
    `pl7.app/abundance/isPrimary` set and `normalized` false, which is exactly what
    the workflow's selector asks for. The abundance unit already reads "reads"
    unless the column name says molecules.
  - Row labels come from `pl7.app/label` on the record axis. The profiler emits one
    ("Variant Id"), and the existing label rule prepends `CL-` to a label carrying
    no `C-` / `P-` prefix.
  - CDR-H3 slicing keeps working. The `REMARK 99 PLATFORMA CDRH3` record is written
    by 3D Structure Prediction from ANARCI numbering of the sequence itself, not
    from any upstream VDJ feature column.
  - A profiler run frames variants against one parent and carries no chain key, so
    it folds in NanoBodyBuilder2 mode and yields heavy-only structures. The
    workflow already derives `hasLightChain` from the PDB contents, so the MSA
    viewer drops the empty L track on its own.

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

## 1.2.0

### Minor Changes

- 2c7c718: Accept PDB datasets keyed on `pl7.app/variantKey`

  The dataset selector required the PDB map's row axis to be `pl7.app/vdj/clonotypeKey` or
  `pl7.app/vdj/scClonotypeKey`. That axis is inherited from whatever 3D Structure Prediction was
  pointed at, and prediction now accepts `import-vdj-data`'s bare antibody sets on
  `pl7.app/variantKey` — so their structures existed but could not be selected here.

  `pl7.app/variantKey` is shared with peptide-extraction and synthetic-repertoire-profiler, so
  the admission test reads `pl7.app/vdj/clonotypingRunId` from the axis domain rather than
  trusting the axis name. It is deliberately identical to `isFoldableRowAxis` in
  3d-structure-prediction.

  No workflow change: `clonotypeAxisSpec` is already read off the input PDB spec, and the
  required primary abundance resolves through an anchored selector.

  Note for imported sets: their abundance is the synthetic per-record constant that
  `import-vdj-data` emits, so per-cluster abundance counts records rather than molecules.

### Patch Changes

- 652701b: Prefix cluster labels that carry no recognised record prefix

  A cluster is labelled from its representative record's label, with a leading `C-` (MiXCR) or `P-`
  (peptide) rewritten to `CL-`. An imported set's labels are the scientist's own identifiers —
  `AB-001`, `trastuzumab` — so nothing was rewritten and the cluster appeared under a bare record
  name, reading as a record rather than a cluster.

  Such labels now get `CL-` prepended: `AB-001` becomes `CL-AB-001`. MiXCR and peptide labels are
  unchanged.

  A label already shaped like `CL-01` is prepended too, giving `CL-CL-01`. An imported set's labels
  are arbitrary, so `CL-01` is a record the scientist named that way; leaving it alone would show a
  cluster and a record under one identical string — the confusion this change exists to remove.

  The same change clonotype-clustering made, applied here deliberately rather than incidentally:
  both blocks label clusters from the same upstream `pl7.app/label` column, and a scientist can see
  both in one project, so the two must agree.

  `synthetic-repertoire-profiler` labels variants `V-XXXXX`, which the rewrite did not match either,
  so amplicon clusters were also showing a bare record label and now read `CL-V-XXXXX`. Adding `V`
  to the rewrite instead would give `CL-XXXXX` and match MiXCR and peptide, but that changes labels
  for an existing modality and is left to whoever owns that call — as in clonotype-clustering.

  A cluster whose representative has no upstream label at all still falls back to the bare centroid
  key. That path is unchanged: the key is a hash, and prefixing it would present a degraded
  fallback as a real label.

- c1f3988: Pass `--registry-serve-url` when publishing the block

  `block-tools` made `--registry-serve-url` a required option for `publish`, and the facade's
  `prepublishOnly` predates that. With block-tools moving from 2.11.0 to 2.14.3 on this branch, the
  release would have failed the way 3d-structure-prediction's already did:

  ```
  error: required option '--registry-serve-url <url>' not specified
  ```

  The component packages publish to npm before the facade runs, so the failure leaves the block
  itself unpublished at a version whose parts are already out. Fixed before that happens rather
  than after.

  The redundant `block-tools pack &&` prefix goes with it: `build` already runs
  `shx rm -rf ./block-pack && block-tools pack`, and CI publishes with `build-script-name: 'build'`.

- Updated dependencies [2c7c718]
- Updated dependencies [652701b]
  - @platforma-open/milaboratories.3d-structure-clustering.model@1.2.0
  - @platforma-open/milaboratories.3d-structure-clustering.workflow@1.1.2
  - @platforma-open/milaboratories.3d-structure-clustering.ui@1.1.2

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
