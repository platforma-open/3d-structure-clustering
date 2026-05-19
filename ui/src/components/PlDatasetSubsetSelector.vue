<script lang="ts">
// Wrapper around PlDropdown that mirrors PlDatasetSelector's wire format but
// only surfaces the per-dataset filter rows — the bare primary is hidden
// because in this block every cluster-input dataset is a clonotype set that
// only carries meaning once narrowed to "predicted" / "confident" subsets.
export default {
  name: "PlDatasetSubsetSelector",
};
</script>

<script lang="ts" setup>
import type { DatasetOption, DatasetSelection, PlRef } from "@platforma-sdk/model";
import { createDatasetSelection, createPrimaryRef, plRefsEqual } from "@platforma-sdk/model";
import type { ListOption } from "@platforma-sdk/ui-vue";
import { PlDropdown } from "@platforma-sdk/ui-vue";
import { computed } from "vue";

const slots = defineSlots<{
  tooltip?: () => unknown;
}>();

const model = defineModel<DatasetSelection | undefined>();

const props = withDefaults(
  defineProps<{
    options?: Readonly<DatasetOption[]>;
    label?: string;
    helper?: string;
    loadingOptionsHelper?: string;
    error?: unknown;
    placeholder?: string;
    clearable?: boolean;
    required?: boolean;
    disabled?: boolean;
  }>(),
  {
    options: undefined,
    label: undefined,
    helper: undefined,
    loadingOptionsHelper: undefined,
    error: undefined,
    placeholder: "...",
    clearable: false,
    required: false,
    disabled: false,
  },
);

type Selection = { primary: PlRef; filter: PlRef };

const selectionValue = computed<Selection | undefined>(() => {
  const primary = model.value?.primary;
  if (primary === undefined || primary.filter === undefined) return undefined;
  return { primary: primary.column, filter: primary.filter };
});

const dropdownOptions = computed<ListOption<Selection>[] | undefined>(() => {
  if (props.options === undefined) return undefined;
  const out: ListOption<Selection>[] = [];
  for (const o of props.options) {
    for (const filter of o.filters ?? []) {
      out.push({
        label: filter.label,
        description: o.primary.label,
        value: { primary: o.primary.ref, filter: filter.ref },
      });
    }
  }
  return out;
});

function findOption(primary: PlRef): DatasetOption | undefined {
  return props.options?.find((o) => plRefsEqual(o.primary.ref, primary, true));
}

function onChange(selection: Selection | undefined) {
  if (selection === undefined) {
    model.value = undefined;
    return;
  }
  model.value = createDatasetSelection(
    createPrimaryRef(selection.primary, selection.filter),
    findOption(selection.primary)?.enrichments,
  );
}
</script>

<template>
  <PlDropdown
    :model-value="selectionValue"
    :options="dropdownOptions"
    :label="label"
    :helper="helper"
    :loading-options-helper="loadingOptionsHelper"
    :error="error"
    :placeholder="placeholder"
    :clearable="clearable"
    :required="required"
    :disabled="disabled"
    @update:model-value="onChange"
  >
    <template v-if="slots.tooltip" #tooltip>
      <slot name="tooltip" />
    </template>
  </PlDropdown>
</template>
