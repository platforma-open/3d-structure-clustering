<script setup lang="ts">
import {
  PlAccordionSection,
  PlAgDataTableV2,
  PlAlert,
  PlBlockPage,
  PlBtnGhost,
  PlDatasetSelector,
  PlLogView,
  PlNumberField,
  PlSlideModal,
  usePlDataTableSettingsV2,
} from "@platforma-sdk/ui-vue";
import { computed, ref } from "vue";
import { useApp } from "../app";
import { defaultBlockLabelFor } from "@platforma-open/milaboratories.3d-structure-clustering.model";

const app = useApp();

const settingsOpen = ref(app.model.data.dataset === undefined);
const logOpen = ref(false);

const tableSettings = usePlDataTableSettingsV2({
  model: () => app.model.outputs.clustersTable,
});

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
</script>

<template>
  <PlBlockPage
    v-model:subtitle="app.model.data.customBlockLabel"
    :subtitle-placeholder="defaultBlockLabelFor(app.model.data)"
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
      {{ Math.round((singletonRate ?? 0) * 100) }}% of structures clustered as singletons. Lower the
      TM-score threshold to pull in more distant relatives.
    </PlAlert>

    <PlAgDataTableV2
      v-model="app.model.data.tableState"
      :settings="tableSettings"
      not-ready-text="Configure the dataset and run."
      no-rows-text="No clusters yet."
    />

    <PlSlideModal v-model="settingsOpen" close-on-outside-click shadow>
      <template #title>Settings</template>

      <PlDatasetSelector
        v-model="app.model.data.dataset"
        :options="app.model.outputs.datasetOptions"
        label="3D Structure"
        clearable
        required
      />

      <PlNumberField
        :model-value="app.model.data.tmScoreThreshold"
        label="TM-score threshold"
        :min-value="0.3"
        :max-value="1.0"
        :step="0.05"
        @update:model-value="setTmScoreThreshold"
      >
        <template #tooltip>
          Minimum TM-score for two structures to land in the same cluster. Default 0.9 favours
          tight, fold-identical clusters; lower it to pull in more distant structural relatives.
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
          Minimum alignment coverage for two structures to land in the same cluster.
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
  </PlBlockPage>
</template>
