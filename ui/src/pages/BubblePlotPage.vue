<script setup lang="ts">
import type { PredefinedGraphOption } from "@milaboratories/graph-maker";
import { GraphMaker } from "@milaboratories/graph-maker";
import { PlBlockPage } from "@platforma-sdk/ui-vue";
import { computed } from "vue";
import { useApp } from "../app";

const app = useApp();

// One bubble per [sampleId, clusterId]; size = per-sample abundance, color =
// per-cluster size. `clusterSize >= 3` filter hides singletons.
const defaultOptions = computed((): PredefinedGraphOption<"bubble">[] | undefined => {
  const abundanceSpec = app.model.outputs.perSampleClusterAbundanceSpec;
  const sizeSpec = app.model.outputs.clusterSizeSpec;
  if (!abundanceSpec || !sizeSpec) return undefined;
  const sampleAxis = abundanceSpec.axesSpec.find((a) => a.name === "pl7.app/sampleId");
  const clusterAxis = abundanceSpec.axesSpec.find((a) => a.name === "pl7.app/clusterId");
  if (!sampleAxis || !clusterAxis) return undefined;
  return [
    { inputName: "x", selectedSource: clusterAxis },
    { inputName: "y", selectedSource: sampleAxis },
    { inputName: "valueColor", selectedSource: sizeSpec },
    { inputName: "valueSize", selectedSource: abundanceSpec },
    { inputName: "filters", selectedSource: sizeSpec, selectedFilterRange: { min: 3 } },
  ];
});
</script>

<template>
  <PlBlockPage>
    <GraphMaker
      v-model="app.model.data.graphStateBubble"
      chart-type="bubble"
      :data-state-key="app.model.outputs.bubblePlotPf"
      :p-frame="app.model.outputs.bubblePlotPf"
      :default-options="defaultOptions"
      :status-text="{ noPframe: { title: 'Run the workflow to see cluster abundance' } }"
    />
  </PlBlockPage>
</template>
