<script setup lang="ts">
import type { DashboardWidget } from '../../store/dashboardDesignStore';

import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { ElDatePicker } from 'element-plus';

import { useDashboardDesignStore } from '../../store/dashboardDesignStore';

const props = defineProps<{
  isDesignMode?: boolean;
  widget: DashboardWidget;
}>();

const store = useDashboardDesignStore();
const dateValue = ref<string>(props.widget.props.defaultValue || '');

const label = computed(() => props.widget.props.label || '');
const placeholder = computed(
  () =>
    props.widget.props.placeholder ||
    $t('dashboard-design.material.defaultProps.filterDatePlaceholder'),
);
const paramKey = computed(() => props.widget.props.paramKey || '');
const dateFormat = computed(
  () => props.widget.props.dateFormat || 'YYYY-MM-DD',
);

const labelPosition = computed(
  () => props.widget.props.labelPosition || 'left',
);
const labelWidth = computed(() => props.widget.props.labelWidth ?? 80);
const labelAlign = computed(() => props.widget.props.labelAlign || 'right');
const componentSize = computed(
  () => props.widget.props.componentSize || 'default',
);
const showBorder = computed(() => props.widget.props.showBorder ?? false);
const borderRadius = computed(() => props.widget.props.borderRadius ?? 4);

const isTopLabel = computed(() => labelPosition.value === 'top');
const isHiddenLabel = computed(() => labelPosition.value === 'hidden');

const containerClass = computed(() => [
  'filter-widget h-full w-full',
  isTopLabel.value ? 'flex flex-col' : 'flex items-center',
  showBorder.value ? 'filter-widget--bordered' : '',
]);

const containerStyle = computed(() => ({
  padding: isTopLabel.value ? '8px 12px' : '0 12px',
  borderRadius: showBorder.value ? `${borderRadius.value}px` : undefined,
}));

const labelStyle = computed(() => ({
  width: isTopLabel.value ? 'auto' : `${labelWidth.value}px`,
  textAlign: labelAlign.value as 'center' | 'left' | 'right',
  flexShrink: 0,
  marginBottom: isTopLabel.value ? '4px' : undefined,
  marginRight: isTopLabel.value ? undefined : '8px',
}));

function handleChange(val: any) {
  if (props.isDesignMode) return;
  if (paramKey.value) {
    store.updateGlobalParam(paramKey.value, val || '');
  }
}

watch(
  () => props.widget.props.defaultValue,
  (val) => {
    if (!props.isDesignMode && val !== undefined) {
      dateValue.value = val;
      if (paramKey.value) {
        store.updateGlobalParam(paramKey.value, val);
      }
    }
  },
  { immediate: true },
);
</script>

<template>
  <div :class="containerClass" :style="containerStyle">
    <span
      v-if="label && !isHiddenLabel"
      class="text-foreground text-sm font-medium"
      :style="labelStyle"
    >
      {{ label }}
    </span>
    <ElDatePicker
      v-model="dateValue"
      type="date"
      :placeholder="placeholder"
      :disabled="isDesignMode"
      :format="dateFormat"
      :value-format="dateFormat"
      :size="componentSize"
      clearable
      class="!flex-1"
      @change="handleChange"
    />
    <span
      v-if="isDesignMode && !paramKey"
      class="ml-2 flex-shrink-0 text-xs text-orange-500"
    >
      {{ $t('dashboard-design.filter.noParamKey') }}
    </span>
  </div>
</template>

<style scoped>
.filter-widget--bordered {
  border: 1px solid var(--el-border-color);
  background-color: var(--el-bg-color);
}

.filter-widget.flex-col :deep(.el-input),
.filter-widget.flex-col :deep(.el-select),
.filter-widget.flex-col :deep(.el-date-editor) {
  flex: none;
  width: 100%;
}
</style>
