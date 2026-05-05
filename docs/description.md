# Overview

Clusters predicted antibody 3D structures by 3Di+AA similarity using [FoldSeek](https://github.com/steineggerlab/foldseek), surfacing structurally similar candidates whose CDR loops adopt the same conformation but differ in sequence — common after framework swaps and across species. Structure-based clusters complement sequence-based clustering and feed into Lead Selection as an additional diversification axis.

The block consumes per-clonotype PDB files produced by the [3D Structure Prediction](https://github.com/platforma-open/milaboratories.3d-structure-prediction) block (or any block exporting `pl7.app/structure/pdb`). The upstream `confident` subset is honored automatically — only predictions above the user's confidence threshold are clustered, so structural neighbors of low-quality predictions don't pollute the result. FoldSeek's 3Di structural alphabet combined with the amino acid alphabet (`--alignment-type 2`) is four to five orders of magnitude faster than DALI / TM-align while preserving cluster quality on antibody-scale datasets, making single-shot clustering of 10K–100K structures tractable on a single node.

For each cluster the block emits cluster size, cluster radius (max TM-distance to centroid), per-clonotype TM-distance to centroid, and the centroid PDB itself. A linker PColumn bridges the upstream clonotype axis to the new `pl7.app/structure/clusterId` axis, so cluster IDs flow through downstream blocks without manual joins. The `clusterRepresentative` subset column lets Lead Selection pick one row per structural cluster.

CDRH3 dominates antibody binding geometry and varies by length, so the block exposes a "stratify by CDRH3 length" toggle that runs FoldSeek once per length bin and namespaces cluster IDs by bin — two clusters with different CDRH3 lengths never share an ID.

The block also exports an [AIRR Community Rearrangement](https://docs.airr-community.org/en/stable/datarep/rearrangements.html) TSV augmented with a `structure_cluster_id` column, downloadable from the main page.

FoldSeek is developed by the [Steinegger Lab](https://steineggerlab.com/). Please cite:

> van Kempen M, Kim SS, Tumescheit C, Mirdita M, Lee J, Gilchrist CLM, Söding J, Steinegger M. *Fast and accurate protein structure search with Foldseek.* Nature Biotechnology, 42, 243–246 (2024). [https://doi.org/10.1038/s41587-023-01773-0](https://doi.org/10.1038/s41587-023-01773-0)
