<script setup lang="ts">
import { PlMultiSequenceAlignment } from "@milaboratories/multi-sequence-alignment";
import { PlStructureViewer } from "@milaboratories/structure-viewer";
import type { PlStructureViewerProps } from "@milaboratories/structure-viewer";
import type { PColumnIdAndSpec, PlSelectionModel, PTableKey } from "@platforma-sdk/model";
import {
  PlAccordionSection,
  PlAgDataTableV2,
  PlAlert,
  PlBlockPage,
  PlBtnGhost,
  PlDropdown,
  PlLogView,
  PlNumberField,
  PlSlideModal,
  PlTabs,
  usePlDataTableSettingsV2,
} from "@platforma-sdk/ui-vue";
import { computed, ref, watch } from "vue";
import { useApp } from "../app";
import {
  ALIGNMENT_DEFAULTS,
  alignmentTypeOptions,
} from "@platforma-open/milaboratories.3d-structure-clustering.model";
import PlDatasetSubsetSelector from "../components/PlDatasetSubsetSelector.vue";

const app = useApp();

const settingsOpen = ref(app.model.data.dataset === undefined);
const logOpen = ref(false);

const tableSettings = usePlDataTableSettingsV2({
  model: () => app.model.outputs.clustersTable,
});

// Replace characters that are unsafe in cross-platform file names. Built via
// fromCharCode so the C0 control range stays out of the regex literal (which
// trips lint rules forbidding control characters in source).
function buildUnsafeFileNameRe(): RegExp {
  const punct = '\\\\/:*?"<>|';
  let controls = "";
  for (let i = 0; i < 32; i++) controls += String.fromCharCode(i);
  return new RegExp(`[${punct}${controls}]+`, "g");
}
const UNSAFE_FILENAME_RE = buildUnsafeFileNameRe();
function sanitizeFileName(label: string): string {
  return label
    .replace(UNSAFE_FILENAME_RE, "_")
    .replace(/\s+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 200);
}

// Combined viewer modal — one button per cluster row opens a single modal
// with MSA and 3D-structure tabs.
type ViewerTab = "msa" | "structure";
const viewerTabOptions: { label: string; value: ViewerTab }[] = [
  { label: "MSA", value: "msa" },
  { label: "3D Structure", value: "structure" },
];
const viewerOpen = ref(false);
const activeViewerTab = ref<ViewerTab>("msa");
const structureViewerProps = ref<PlStructureViewerProps>();
const msaSelection = ref<PlSelectionModel>({ axesSpec: [], selectedKeys: [] });

function onClusterButtonClicked(key?: PTableKey) {
  if (!key) return;
  const clusterId = key.at(0);
  if (clusterId === undefined || clusterId === null) return;
  const axisSpec = app.model.outputs.clusterAxisSpec;
  if (!axisSpec) return;

  msaSelection.value = { axesSpec: [axisSpec], selectedKeys: [key] };

  const entry = app.model.outputs.centroidPdbsMap?.find((e) => e.key.at(0) === clusterId);
  const handle = entry?.value?.handle;
  structureViewerProps.value = handle
    ? { handle, fileName: `${sanitizeFileName(String(clusterId)) || "cluster"}.pdb` }
    : undefined;

  viewerOpen.value = true;
}

function handleViewerVisibility(open: boolean) {
  viewerOpen.value = open;
  if (!open) structureViewerProps.value = undefined;
}

// The MSA viewer asks which p-columns in `msaPf` carry the sequences to align.
// For heavy-only inputs the L sequence column is present but all-empty, which
// trips kalign ("0 sequences found"). Gate the L track out when the workflow
// reports no light chain.
const isSequenceColumn = (column: PColumnIdAndSpec) => {
  if (column.spec?.name !== "pl7.app/structure/memberSequence") return false;
  if (
    app.model.outputs.hasLightChain === false &&
    column.spec.domain?.["pl7.app/structure/chain"] === "L"
  ) {
    return false;
  }
  return true;
};

const emptyInput = computed(() => app.model.outputs.emptyInput === true);
const singletonRate = computed(() => app.model.outputs.singletonRate);
const singletonAlertVisible = computed(
  () => singletonRate.value !== undefined && singletonRate.value > 0.25,
);

function setTmScoreThreshold(value: number | undefined) {
  if (value === undefined) return;
  app.model.data.tmScoreThreshold = Math.min(1.0, Math.max(0.3, value));
}

function setCoverageThreshold(value: number | undefined) {
  if (value === undefined) return;
  app.model.data.coverageThreshold = Math.min(1.0, Math.max(0.5, value));
}

function setCdrh3Flank(value: number | undefined) {
  if (value === undefined) return;
  app.model.data.cdrh3FlankResidues = Math.min(30, Math.max(0, Math.round(value)));
}

const isCdrh3Mode = computed(() => app.model.data.alignmentType === "cdrh3");

watch(
  () => app.model.data.alignmentType,
  (mode) => {
    const defaults = ALIGNMENT_DEFAULTS[mode];
    if (defaults === undefined) return;
    app.model.data.tmScoreThreshold = defaults.tmScoreThreshold;
    app.model.data.coverageThreshold = defaults.coverageThreshold;
  },
);
</script>

<template>
  <PlBlockPage
    v-model:subtitle="app.model.data.customBlockLabel"
    :subtitle-placeholder="app.model.data.defaultBlockLabel"
    title="3D Structure Clustering"
  >
    <template #append>
      <PlBtnGhost @click.stop="logOpen = true" icon="file-logs"> Logs </PlBtnGhost>
      <PlBtnGhost @click.stop="settingsOpen = true" icon="settings"> Settings </PlBtnGhost>
    </template>

    <PlAlert v-if="emptyInput" type="warn">
      No confident PDB structures available. Verify the upstream block ran successfully and the
      confidence subset is populated.
    </PlAlert>

    <PlAlert v-if="singletonAlertVisible" type="info" closable>
      {{ Math.round((singletonRate ?? 0) * 100) }}% of structures clustered as singletons.
      <template v-if="isCdrh3Mode">
        In CDR-H3 mode a high singleton rate is often expected — each unique paratope shape becomes
        its own cluster. For broader, canonical-class-level groupings lower the TM-score threshold
        (~0.45–0.55) or increase the CDR-H3 flank.
      </template>
      <template v-else>
        Lower the TM-score threshold to pull in more distant structural relatives.
      </template>
    </PlAlert>

    <PlAgDataTableV2
      v-model="app.model.data.tableState"
      :settings="tableSettings"
      :show-cell-button-for-axis-id="app.model.outputs.clusterAxisId"
      not-ready-text="Configure the dataset and run."
      no-rows-text="No clusters yet."
      @cell-button-clicked="onClusterButtonClicked"
    />

    <PlSlideModal v-model="settingsOpen" close-on-outside-click shadow>
      <template #title>Settings</template>

      <PlDatasetSubsetSelector
        v-model="app.model.data.dataset"
        :options="app.model.outputs.datasetOptions"
        label="3D Structure"
        clearable
        required
      />

      <PlDropdown
        v-model="app.model.data.alignmentType"
        :options="alignmentTypeOptions"
        label="Alignment mode"
        required
      >
        <template #tooltip>
          <b>CDR-H3 Structure</b> pre-slices each PDB to the CDR-H3 loop so clustering reflects
          paratope shape rather than the conserved framework. <b>Full Structure + AA</b> aligns the
          whole Fv with FoldSeek's 3Di + AA combined score — framework AA conservation inflates
          similarity. <b>Full Structure</b> aligns the whole Fv with pure TM-align, no AA bias.
        </template>
      </PlDropdown>

      <PlNumberField
        v-if="isCdrh3Mode"
        :model-value="app.model.data.cdrh3FlankResidues"
        label="CDR-H3 flank (residues)"
        :min-value="0"
        :max-value="30"
        :step="1"
        @update:model-value="setCdrh3Flank"
      >
        <template #tooltip>
          Extra residues kept on each side of CDR-H3. Trade-off: larger flank gives a longer
          fragment so TM-score's length-dependent d0 is more forgiving, but conserved FR3/FR4
          framework leaks into the cluster signal and collapses everything into one giant cluster.
          Smaller flank keeps the signal CDR-focused but TM-score becomes very strict (d0 ≈ 0.7 Å at
          flank=5, fragments ~23 aa). Default <b>5</b> is the balance point.
        </template>
      </PlNumberField>

      <PlNumberField
        :model-value="app.model.data.tmScoreThreshold"
        label="TM-score threshold"
        :min-value="0.3"
        :max-value="1.0"
        :step="0.05"
        @update:model-value="setTmScoreThreshold"
      >
        <template #tooltip>
          Minimum TM-score for two structures to land in the same cluster. The useful range depends
          on alignment scope: <b>~0.85–1.00 for full-Fv modes</b> (the immunoglobulin framework
          alone scores ≥0.85), <b>~0.4–0.8 for CDR-H3 mode</b> (short fragments have a small d0 and
          score much lower at the same physical RMSD). Defaults switch automatically with alignment
          scope — 0.95 for full-Fv, 0.70 for CDR-H3.
        </template>
      </PlNumberField>

      <PlNumberField
        :model-value="app.model.data.coverageThreshold"
        label="Coverage threshold"
        :min-value="0.5"
        :max-value="1.0"
        :step="0.05"
        @update:model-value="setCoverageThreshold"
      >
        <template #tooltip>
          Minimum alignment coverage for two structures to be considered for clustering.
          <template v-if="isCdrh3Mode">
            In CDR-H3 mode this effectively filters by CDR-H3 length similarity — pairs whose length
            ratio falls below the threshold are rejected before scoring. Raise it (~0.9+) to enforce
            same-length clustering, lower (~0.6) to allow cross-length matches. Default 0.80.
          </template>
          <template v-else>
            In full-Fv modes it filters partial alignments. Default 0.90.
          </template>
        </template>
      </PlNumberField>

      <PlAccordionSection label="Advanced">
        <PlNumberField
          v-model="app.model.data.cpu"
          label="CPU cores"
          :min-value="1"
          :max-value="64"
          :step="1"
        />

        <PlNumberField
          v-model="app.model.data.mem"
          label="Memory (GiB)"
          :min-value="4"
          :max-value="256"
          :step="4"
        />
      </PlAccordionSection>
    </PlSlideModal>

    <PlSlideModal v-model="logOpen" width="80%">
      <template #title>FoldSeek log</template>
      <PlLogView :log-handle="app.model.outputs.clusteringLogHandle" />
    </PlSlideModal>

    <PlSlideModal
      :model-value="viewerOpen"
      width="100%"
      :close-on-outside-click="false"
      @update:model-value="handleViewerVisibility"
    >
      <template #title>
        {{
          activeViewerTab === "msa"
            ? "Cluster Members — Multiple Sequence Alignment"
            : "Centroid 3D Structure"
        }}
      </template>
      <PlTabs v-model="activeViewerTab" :options="viewerTabOptions" />
      <template v-if="activeViewerTab === 'msa'">
        <PlMultiSequenceAlignment
          v-if="app.model.outputs.msaPf"
          v-model="app.model.data.alignmentModel"
          :sequence-column-predicate="isSequenceColumn"
          :p-frame="app.model.outputs.msaPf"
          :selection="msaSelection"
        />
      </template>
      <template v-else-if="activeViewerTab === 'structure'">
        <PlStructureViewer v-if="structureViewerProps" v-bind="structureViewerProps" />
        <PlAlert v-else type="warn">
          No centroid 3D structure available for the selected cluster.
        </PlAlert>
      </template>
    </PlSlideModal>
  </PlBlockPage>
</template>
