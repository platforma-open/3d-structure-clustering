# 3D Structure Clustering

Group antibody candidates by the shape of their binding site rather than the letters of their sequence. This Platforma block clusters predicted 3D structures with Foldseek, surfacing candidates whose CDR loops adopt the same conformation even when their sequences diverge — and reports a centroid structure, cluster radius, and per-member structural distance for every cluster.

Open-source analysis block for Platforma, the biologics discovery platform by MiLaboratories. For the full no-code workflow, see [platforma.bio](https://platforma.bio/).

## What it does

Two antibodies can bind the same epitope through the same loop conformation while sharing little sequence identity. Sequence clustering misses that relationship entirely — after a framework swap, or across species, related binders scatter into separate families. Structural clustering finds them.

The block clusters the predicted structures from [3D Structure Prediction](https://github.com/platforma-open/3d-structure-prediction) using Foldseek, which encodes tertiary contacts as a structural alphabet (3Di) and so runs four to five orders of magnitude faster than DALI or TM-align. That speed is what makes the operation practical: clustering 10,000 to 100,000 structures in one pass on a single node, rather than as an overnight job. When the upstream dataset carries a confidence filter, only confident predictions are clustered.

You choose what similarity is measured over:

* **CDR-H3 Structure** — each structure is sliced down to its CDR-H3 loop, with a configurable flank, and clustering runs on those fragments. Paratope-focused, and the mode to use when the question is whether two candidates present the same binding surface.
* **Full Structure** — the whole Fv, backbone geometry only. A pure structural score.
* **Full Structure + aa Sequence** — the whole Fv with 3Di and amino acid alphabets combined. Note that this inflates similarity when the framework sequence is conserved, which it usually is, so shared framework can dominate the signal.

A TM-score threshold and a coverage threshold control how tight clusters are.

For each cluster you get its size, its radius as the maximum TM-distance from centroid, the centroid's own PDB structure, per-member TM-distance and TM-score to that centroid, and abundance totals carried through from upstream. Results are explored as a per-cluster table, a bubble plot of the most abundant clusters across samples, and a cluster size histogram, with a multiple sequence alignment view over each cluster's members.

### Chain handling

Both heavy-only and paired H+L structures are accepted, but **cluster assignment is driven by the heavy chain**. Foldseek clusters each PDB chain independently, and the block keeps the heavy-chain row for each member — chain `H`, or the first chain alphabetically for non-standard naming, with a warning logged. Light-chain clustering decisions are discarded, and TM-distance to centroid is computed on the heavy chain only. The alignment viewer shows both heavy and light chain sequences, so paired antibodies can still be inspected side by side.

## Inputs & outputs

* **Input:** per-clonotype PDB structures from [3D Structure Prediction](https://github.com/platforma-open/3d-structure-prediction) — heavy-only or paired H+L. CDR-H3 mode reads the CDR boundaries that block writes into each model.
* **Output:** a structural cluster ID per clonotype, cluster size, cluster radius (maximum TM-distance to centroid), per-member TM-distance and TM-score to centroid, a centroid flag, the centroid PDB structure, and per-cluster abundance totals — plus a cluster table, an abundance bubble plot, a size histogram, and a per-cluster alignment view.

## Specifications

| | |
|---|---|
| Block title in app | 3D Structure Clustering |
| Engine | [Foldseek](https://github.com/steineggerlab/foldseek) cascaded clustering, 3Di structural alphabet |
| Input | Predicted per-clonotype PDB models from 3D Structure Prediction |
| Alignment modes | CDR-H3 Structure (with configurable flank), Full Structure, Full Structure + aa Sequence |
| Thresholds | TM-score threshold, coverage threshold |
| Chain scope | Cluster assignment and TM-distance from the heavy chain; both chains shown in the alignment view |
| Per-cluster metrics | Size, radius (max TM-distance to centroid), centroid PDB, per-member TM-distance and TM-score |
| Scale | Practical for 10K–100K structures in a single pass on one node |
| Views | Cluster table, most abundant clusters bubble plot, cluster size histogram, multiple sequence alignment |

## Use cases

* **Find structurally related binders across sequence families:** group candidates whose CDR loops share a conformation despite low sequence identity.
* **Framework-swap campaigns:** recognize that a humanized or reformatted variant is the same binder as its parent, which sequence clustering would separate.
* **Cross-species comparison:** relate murine, llama, and human candidates by binding-site shape rather than germline sequence.
* **Paratope grouping:** use CDR-H3 mode to group candidates by the surface they actually present to the antigen.
* **Structural diversification in lead selection:** supply structural cluster assignments to [Lead Selection](https://github.com/platforma-open/antibody-tcr-lead-selection) as a diversification axis independent of sequence.
* **Representative selection:** advance each cluster's centroid to reduce a panel to structurally distinct candidates.
* **Cluster tightness:** use cluster radius to tell a converged conformational family from a loose grouping.

## How it compares to other Platforma blocks

* **3D Structure Clustering** groups by predicted structure, so candidates with the same loop conformation cluster together regardless of sequence. It requires a structure prediction run upstream.
* **[Sequence Clustering](https://github.com/platforma-open/clonotype-clustering)** groups by sequence identity or BLOSUM similarity — cheap, runs on any dataset, and the right first pass.
* **[Embedding Clustering](https://github.com/platforma-open/embedding-clustering)** groups in protein language model embedding space, which captures learned similarity without needing a structure.

The three are complementary axes, and Lead Selection can diversify on whichever one the campaign calls for.

## FAQ

### Why cluster on structure instead of sequence?

Because binding is a property of shape. Two antibodies can present the same paratope through the same CDR conformation while differing substantially in sequence — a framework swap, a humanization, or a homolog from another species. Sequence clustering splits those apart; structural clustering keeps them together.

### Which alignment mode should I use?

CDR-H3 Structure when the question is about the binding surface, which is the usual case in discovery. Full Structure for a pure whole-Fv geometric comparison. Full Structure + aa Sequence combines structure and sequence, but framework amino acids are conserved across most antibodies and will inflate similarity — use it deliberately, not as a default.

### What is cluster radius?

The largest TM-distance from any member to the cluster centroid. A small radius means every member is structurally close to the centroid — a tight conformational family. A large one means the cluster spans more varied geometry, and the centroid represents it less well.

### Why is clustering driven by the heavy chain?

Foldseek clusters each PDB chain independently, so a paired structure produces separate heavy and light decisions. The heavy chain carries CDR-H3 and dominates the binding interface in most antibodies, so its assignment is the one kept. Light-chain sequences are still shown in the alignment view for inspection.

### How large a dataset can it handle?

Foldseek's structural alphabet makes single-pass clustering of 10,000 to 100,000 structures tractable on one node. That is the range this block is built for.

### Do I need to run structure prediction first?

Yes. The block consumes predicted PDB models from 3D Structure Prediction, which also writes the CDR boundary records that CDR-H3 mode slices on.

### What happens to low-confidence predictions?

If a confidence filter is applied on the upstream dataset, only confident predictions reach clustering — so structural clusters are not built on models the predictor was unsure about.

## Citation

Foldseek is developed by the [Steinegger Lab](https://steineggerlab.com/). If you use this block in your research, please cite:

> van Kempen, M., Kim, S. S., Tumescheit, C., Mirdita, M., Lee, J., Gilchrist, C. L. M., Söding, J., & Steinegger, M. (2024). Fast and accurate protein structure search with Foldseek. *Nature Biotechnology* **42**(2), 243–246. [https://doi.org/10.1038/s41587-023-01773-0](https://doi.org/10.1038/s41587-023-01773-0)

## Part of the Platforma ecosystem

This block is part of [Platforma](https://platforma.bio/) by [MiLaboratories](https://github.com/milaboratory), built on [Foldseek](https://github.com/steineggerlab/foldseek). Explore the other open-source blocks at [github.com/platforma-open](https://github.com/platforma-open) and the docs for antibody discovery at [docs.platforma.bio/biology-guides/antibody-discovery](https://docs.platforma.bio/biology-guides/antibody-discovery/).
