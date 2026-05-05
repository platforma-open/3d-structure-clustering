import { createPlDataTableStateV2, DataModelBuilder } from "@platforma-sdk/model";
import type { BlockData } from "./types";

const initialGraphState = (title: string, fillColor: string) =>
  ({
    title,
    template: "bins",
    currentTab: null,
    layersSettings: { bins: { fillColor } },
    axesSettings: {
      axisY: { axisLabelsAngle: 0 as const, scale: "linear" },
      other: { binsCount: 30 },
    },
  }) satisfies import("@milaboratories/graph-maker").GraphMakerState;

const initialBubbleState = () =>
  ({
    title: "Cluster abundance",
    template: "dots",
    currentTab: null,
    layersSettings: {},
    axesSettings: {},
  }) satisfies import("@milaboratories/graph-maker").GraphMakerState;

export const blockDataModel = new DataModelBuilder().from<BlockData>("v1").init(() => ({
  defaultBlockLabel: "",
  customBlockLabel: "",

  tmScoreThreshold: 0.9,
  coverageThreshold: 0.9,
  clusteringMode: "easy-cluster" as const,
  cdrh3LengthStratify: false,

  tableState: createPlDataTableStateV2(),
  graphStateBubble: initialBubbleState(),
  graphStateHistogram: initialGraphState("Cluster size distribution", "#7da3d1"),
}));
