# @platforma-open/milaboratories.3d-structure-clustering.workflow

## 1.1.2

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

- Updated dependencies [652701b]
  - @platforma-open/milaboratories.3d-structure-clustering.software@1.1.2

## 1.1.1

### Patch Changes

- c635aff: Migrate block onto the structurer (block-tools 2.11.0) — full SDK upgrade: model/ui-vue/test 1.79.14, workflow-tengo 6.6.3, tengo-builder 4.0.8, ts-builder 1.5.2. Adopts the canonical tool-managed layout (oxlint/oxfmt across model/ui/test, tsconfig, turbo, block index, scaffold-owned CI workflows, managed package.json + catalog).
- Updated dependencies [c635aff]
  - @platforma-open/milaboratories.3d-structure-clustering.software@1.1.1

## 1.1.0

### Minor Changes

- 94cb563: Select the 3D structures dataset directly. The upstream 3D Structure Prediction block now exports a confident-only PDB map, so there is no subset to choose: the settings panel uses the standard `PlDatasetSelector` to pick the PDB dataset directly (replacing the subset-only `PlDatasetSubsetSelector`), and the model no longer attaches subset filters (which had begun surfacing unrelated upstream subsets such as Lead Selection's). Removes the now-dead confident-subset filtering machinery (`filter-pdbs` / `build-filtered-pdbs-map` templates and the `filter_pdbs.py` software entrypoint).

### Patch Changes

- Updated dependencies [94cb563]
  - @platforma-open/milaboratories.3d-structure-clustering.software@1.1.0

## 1.0.5

### Patch Changes

- 7ce563e: Stage PDBs under synthetic FoldSeek-safe filenames instead of the raw clonotypeKey. FoldSeek does not echo arbitrary filename stems back verbatim, which broke the member→clonotypeKey round-trip in process_results.py for certain datasets ("FoldSeek output references unknown member files"). The clonotypeKey↔filename mapping is now carried solely through the manifest.
- Updated dependencies [7ce563e]
  - @platforma-open/milaboratories.3d-structure-clustering.software@1.0.3

## 1.0.4

### Patch Changes

- Updated dependencies [2ce6662]
  - @platforma-open/milaboratories.3d-structure-clustering.software@1.0.2

## 1.0.3

### Patch Changes

- 3bbd5eb: Add centroid heavy/light chain sequence columns to the per-cluster result table. Sequences are extracted from the centroid PDB by `process_results.py` and projected onto the cluster axis as a separate `centroid_sequences.tsv` (mirrors clonotype-clustering's `clusterToSeq` pattern). The light-chain column is hidden on heavy-only datasets via `hasLightChain`.

## 1.0.2

### Patch Changes

- a2dd3d6: Expose parameter-driven cluster label in trace. Linker columns now carry a `milaboratories.3d-structure-clustering.clustering` trace element whose label follows the block's customBlockLabel / defaultBlockLabel — so downstream consumers (lead-selection) can show a meaningful cluster choice instead of the generic "Cluster" fallback.

## 1.0.1

### Patch Changes

- 0f9d457: Multiple improvements: add 3d viewer and msa, introduce different alignment modes, deduplication
- Updated dependencies [0f9d457]
  - @platforma-open/milaboratories.3d-structure-clustering.software@1.0.1
