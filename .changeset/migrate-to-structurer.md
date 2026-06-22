---
'@platforma-open/milaboratories.3d-structure-clustering.model': patch
'@platforma-open/milaboratories.3d-structure-clustering.ui': patch
'@platforma-open/milaboratories.3d-structure-clustering.workflow': patch
'@platforma-open/milaboratories.3d-structure-clustering.software': patch
'@platforma-open/milaboratories.3d-structure-clustering': patch
---

Migrate block onto the structurer (block-tools 2.11.0) — full SDK upgrade: model/ui-vue/test 1.79.14, workflow-tengo 6.6.3, tengo-builder 4.0.8, ts-builder 1.5.2. Adopts the canonical tool-managed layout (oxlint/oxfmt across model/ui/test, tsconfig, turbo, block index, scaffold-owned CI workflows, managed package.json + catalog).