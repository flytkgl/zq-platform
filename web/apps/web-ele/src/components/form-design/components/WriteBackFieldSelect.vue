<script setup lang="ts">
import { computed } from 'vue';

import { ElOption, ElSelect, ElTag } from 'element-plus';

export interface WriteBackField {
  name: string;
  comment?: string;
  label?: string;
  type?: string;
}

const props = withDefaults(
  defineProps<{
    modelValue?: string;
    fields?: WriteBackField[];
    placeholder?: string;
    disabled?: boolean;
    clearable?: boolean;
  }>(),
  {
    modelValue: '',
    fields: () => [],
    placeholder: '请选择字段',
    disabled: false,
    clearable: false,
  },
);

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void;
}>();

const selectedField = computed(() =>
  props.fields.find((field) => field.name === props.modelValue),
);

function getFieldLabel(field: WriteBackField) {
  return field.comment?.trim() || field.label?.trim() || field.name;
}

function getFieldType(field: WriteBackField) {
  return field.type?.trim().toUpperCase() || '未知类型';
}

function getOptionLabel(field: WriteBackField) {
  return `${getFieldLabel(field)} · ${field.name} · ${getFieldType(field)}`;
}
</script>

<template>
  <ElSelect
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :clearable="clearable"
    filterable
    class="w-full"
    popper-class="writeback-field-select-popper"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <ElOption
      v-for="field in fields"
      :key="field.name"
      :label="getOptionLabel(field)"
      :value="field.name"
    >
      <div class="min-w-0 py-0.5">
        <div class="truncate text-sm text-[var(--el-text-color-primary)]">
          {{ getFieldLabel(field) }}
        </div>
        <div
          class="flex min-w-0 items-center gap-2 text-xs text-[var(--el-text-color-secondary)]"
        >
          <span class="truncate font-mono">{{ field.name }}</span>
          <ElTag size="small" effect="plain" class="shrink-0">
            {{ getFieldType(field) }}
          </ElTag>
        </div>
      </div>
    </ElOption>
    <template #label>
      <span v-if="selectedField" class="flex min-w-0 items-center gap-1">
        <span class="truncate">{{ getFieldLabel(selectedField) }}</span>
        <span
          class="truncate font-mono text-xs text-[var(--el-text-color-secondary)]"
        >
          · {{ selectedField.name }}
        </span>
      </span>
    </template>
  </ElSelect>
</template>

<style>
.writeback-field-select-popper .el-select-dropdown__item {
  height: auto;
  min-height: 46px;
  padding: 6px 12px;
  line-height: 1.25;
  white-space: normal;
}

.writeback-field-select-popper .el-select-dropdown__item > div {
  width: 100%;
}
</style>
