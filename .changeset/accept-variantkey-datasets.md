---
'@platforma-open/milaboratories.3d-structure-clustering.model': minor
'@platforma-open/milaboratories.3d-structure-clustering': minor
---

Accept PDB datasets keyed on `pl7.app/variantKey`

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
