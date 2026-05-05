<script setup lang="ts">
import type { PredefinedGraphOption } from "@milaboratories/graph-maker";
import { GraphMaker } from "@milaboratories/graph-maker";
import { PlBlockPage } from "@platforma-sdk/ui-vue";
import { computed } from "vue";
import { useApp } from "../app";

const app = useApp();

// One point per cluster: x = cluster size, y = cluster radius (TM-distance),
// dot size = cluster size. The bubble template needs two axes — we only have
// [clusterId], so a scatterplot of (size, radius) is the natural fit and
// gives a quick visual of "tight, populous clusters" (top-left) vs "loose,
// rare clusters" (bottom-right).
const defaultOptions = computed((): PredefinedGraphOption<"scatterplot">[] | undefined => {
  const sizeSpec = app.model.outputs.clusterSizeSpec;
  const radiusSpec = app.model.outputs.clusterRadiusSpec;
  if (!sizeSpec || !radiusSpec) return undefined;
  return [
    { inputName: "x", selectedSource: sizeSpec },
    { inputName: "y", selectedSource: radiusSpec },
    { inputName: "size", selectedSource: sizeSpec },
  ];
});
</script>

<template>
  <PlBlockPage>
    <GraphMaker
      v-model="app.model.data.graphStateBubble"
      chart-type="scatterplot"
      :data-state-key="app.model.outputs.bubblePlotPf"
      :p-frame="app.model.outputs.bubblePlotPf"
      :default-options="defaultOptions"
      :status-text="{ noPframe: { title: 'Run the workflow to see cluster overview' } }"
    />
  </PlBlockPage>
</template>
