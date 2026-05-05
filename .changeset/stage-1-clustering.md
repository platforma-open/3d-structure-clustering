---
"@platforma-open/milaboratories.3d-structure-clustering": minor
"@platforma-open/milaboratories.3d-structure-clustering.workflow": minor
"@platforma-open/milaboratories.3d-structure-clustering.model": minor
"@platforma-open/milaboratories.3d-structure-clustering.ui": minor
"@platforma-open/milaboratories.3d-structure-clustering.software": minor
---

Stage 1 — core FoldSeek clustering of antibody 3D structures.

- Consumes a PDB ResourceMap from `3d-structure-prediction` (or any block exporting `pl7.app/structure/pdb`) via the new Filter Column API: `PlDatasetSelector` picks the dataset and the upstream `confident` subset filter. Enrichment columns are auto-discovered.
- Workflow chains: `prepare-inputs` (Python — stages confident PDBs into a workdir) → `foldseek easy-cluster` (3Di+AA, configurable TM-score and coverage thresholds) → `foldseek easy-search` (per-member→centroid TM-scores) → `process-results` (Python — emits cluster_assignments / cluster_summary / centroids_manifest TSVs and copies centroid PDBs).
- Outputs: `pl7.app/structure/clusterId` axis (linker PColumn from clonotype to cluster), per-clonotype `tmDistanceToCentroid` and `tmScoreToCentroid`, per-cluster `clusterSize` and `clusterRadius`, centroid PDB ResourceMap on `[clusterId]`, plus a `clusteringSummary` JSON with totalRows / clusterCount / singletonRate / emptyInput.
- UI: three pages — Clusters table (PlAgDataTableV2), Cluster size histogram, Cluster abundance bubble plot. Settings panel exposes TM-score threshold (0.3–1.0), coverage threshold (0.5–1.0), clustering mode (`easy-cluster` / `easy-linclust`), CDRH3-length stratification toggle, advanced CPU/memory inputs. Block subtitle reflects active parameters.
- FoldSeek binary delivered via the new bioconda package `@platforma-open/steineggerlab.software-foldseek` (1.1.0).

Stage 2 (clonotype-clustering comparison view, AIRR export, PDB viewer modal) follows in a separate release.
