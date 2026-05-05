<script setup lang="ts">
import type { PredefinedGraphOption } from "@milaboratories/graph-maker";
import { GraphMaker } from "@milaboratories/graph-maker";
import { PlBlockPage } from "@platforma-sdk/ui-vue";
import { computed } from "vue";
import { useApp } from "../app";

const app = useApp();

const defaultOptions = computed((): PredefinedGraphOption<"histogram">[] | undefined => {
  const spec = app.model.outputs.clusterSizeSpec;
  if (!spec) return undefined;
  return [{ inputName: "value", selectedSource: spec }];
});
</script>

<template>
  <PlBlockPage>
    <GraphMaker
      v-model="app.model.data.graphStateHistogram"
      chart-type="histogram"
      :data-state-key="app.model.outputs.histogramPf"
      :p-frame="app.model.outputs.histogramPf"
      :default-options="defaultOptions"
      :status-text="{ noPframe: { title: 'Run the workflow to see cluster size distribution' } }"
    />
  </PlBlockPage>
</template>
