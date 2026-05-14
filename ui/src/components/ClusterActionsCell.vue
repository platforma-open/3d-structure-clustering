<script lang="ts" setup>
import type { PTableKey } from "@platforma-sdk/model";
import type { ICellRendererParams } from "ag-grid-enterprise";
import { PlMaskIcon16 } from "@platforma-sdk/ui-vue";
import type { PlAgDataTableV2Row } from "@platforma-sdk/ui-vue";
import "./cluster-actions-cell.css";

type ActionPayload = { key: PTableKey; label: string };

type Params = ICellRendererParams<PlAgDataTableV2Row> & {
  onOpenStructure?: (payload: ActionPayload) => void;
  onOpenMsa?: (payload: ActionPayload) => void;
};

const props = defineProps<{ params: Params }>();

function trigger(handler?: (payload: ActionPayload) => void) {
  const key = props.params.data?.axesKey;
  if (!key || !handler) return;
  handler({ key, label: String(props.params.value ?? "") });
}
</script>

<template>
  <div class="cluster-actions-cell">
    <span class="cluster-actions-cell__label">{{ params.value }}</span>
    <button
      type="button"
      class="cluster-actions-cell__btn"
      title="View 3D structure of cluster centroid"
      @click.stop="trigger(params.onOpenStructure)"
    >
      <PlMaskIcon16 name="arrow-link" />
    </button>
    <button
      type="button"
      class="cluster-actions-cell__btn"
      title="View multiple sequence alignment of cluster members"
      @click.stop="trigger(params.onOpenMsa)"
    >
      <PlMaskIcon16 name="maximize" />
    </button>
  </div>
</template>
