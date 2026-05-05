import {
  defaultBlockLabelFor,
  platforma,
} from "@platforma-open/milaboratories.3d-structure-clustering.model";
import { defineAppV3 } from "@platforma-sdk/ui-vue";
import { watch, watchEffect } from "vue";
import BubblePlotPage from "./pages/BubblePlotPage.vue";
import HistogramPage from "./pages/HistogramPage.vue";
import MainPage from "./pages/MainPage.vue";

export const sdkPlugin = defineAppV3(platforma, () => ({
  showErrorsNotification: true,
  routes: {
    "/": () => MainPage,
    "/histogram": () => HistogramPage,
    "/bubble-plot": () => BubblePlotPage,
  },
}));

export const useApp = sdkPlugin.useApp;

// Plugin-load gate: data is only available once the plugin finishes loading,
// so reactive sync effects are wired here. Mirrors the pattern in
// 3d-structure-prediction/ui/src/app.ts.
const unwatch = watch(sdkPlugin, ({ loaded }) => {
  if (!loaded) return;
  unwatch();
  const app = useApp();

  // Keep defaultBlockLabel in sync with current data so the subtitle
  // placeholder reflects the active parameters (R42).
  watchEffect(() => {
    app.model.data.defaultBlockLabel = defaultBlockLabelFor({
      tmScoreThreshold: app.model.data.tmScoreThreshold,
      coverageThreshold: app.model.data.coverageThreshold,
      clusteringMode: app.model.data.clusteringMode,
      cdrh3LengthStratify: app.model.data.cdrh3LengthStratify,
    });
  });
});
