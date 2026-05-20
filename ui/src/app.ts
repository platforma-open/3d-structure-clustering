import { platforma } from "@platforma-open/milaboratories.3d-structure-clustering.model";
import { defineAppV3 } from "@platforma-sdk/ui-vue";
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
