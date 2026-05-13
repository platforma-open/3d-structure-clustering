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
    "/bubble": () => BubblePlotPage,
    "/histogram": () => HistogramPage,
  },
}));

export const useApp = sdkPlugin.useApp;

// `app.model.data` is only available after the plugin loads.
const unwatch = watch(sdkPlugin, ({ loaded }) => {
  if (!loaded) return;
  unwatch();
  const app = useApp();

  watchEffect(() => {
    app.model.data.defaultBlockLabel = defaultBlockLabelFor({
      tmScoreThreshold: app.model.data.tmScoreThreshold,
      coverageThreshold: app.model.data.coverageThreshold,
      clusteringMode: app.model.data.clusteringMode,
    });
  });
});
