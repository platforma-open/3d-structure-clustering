# Overview

Clusters predicted antibody 3D structures by 3Di+AA similarity using [FoldSeek](https://github.com/steineggerlab/foldseek), surfacing structurally similar candidates whose CDR loops adopt the same conformation but differ in sequence — common after framework swaps and across species. Structure-based clusters complement sequence-based clustering and feed into Lead Selection as an additional diversification axis.

The block consumes per-clonotype PDB files produced by the [3D Structure Prediction](https://github.com/platforma-open/milaboratories.3d-structure-prediction) block. When a confidence filter is selected on the dataset, only confident predictions are clustered. FoldSeek's 3Di structural alphabet combined with the amino acid alphabet is four to five orders of magnitude faster than DALI / TM-align while preserving cluster quality on antibody-scale datasets, making single-shot clustering of 10K–100K structures tractable on a single node.

For each cluster the block reports cluster size, cluster radius (max TM-distance to centroid), per-clonotype TM-distance to centroid, the centroid PDB itself, and per-cluster abundance totals carried through from the upstream dataset.

The UI has three pages: a per-cluster table (size, radius, abundance totals, centroid label), a "Most Abundant Clusters" bubble plot (sample × cluster, sized by per-sample abundance, coloured by cluster size), and a cluster-size histogram.

## Multi-chain assumption

The block accepts both single-chain (heavy-only) and paired H+L PDB inputs. **Cluster assignment is heavy-chain driven**: FoldSeek's `easy-cluster` mode clusters each PDB chain independently, and the block keeps only the row corresponding to each member's heavy chain (chain id `H` in the PDB; for non-standard chain naming the first chain by alphabetical order is used and a warning is logged). The L-chain FoldSeek decisions are discarded for the cluster assignment.

TM-distance to centroid is computed on the heavy chain only and reflects the alignment scope (CDR-H3 loop in `cdrh3` alignment mode, full chain otherwise). The per-cluster MSA viewer surfaces both heavy and light chain sequences (`sequence_H` and `sequence_L`) so paired antibodies can be inspected; for heavy-only inputs the light-chain column is empty.

FoldSeek is developed by the [Steinegger Lab](https://steineggerlab.com/). Please cite:

> van Kempen M, Kim SS, Tumescheit C, Mirdita M, Lee J, Gilchrist CLM, Söding J, Steinegger M. *Fast and accurate protein structure search with Foldseek.* Nature Biotechnology, 42, 243–246 (2024). [https://doi.org/10.1038/s41587-023-01773-0](https://doi.org/10.1038/s41587-023-01773-0)
