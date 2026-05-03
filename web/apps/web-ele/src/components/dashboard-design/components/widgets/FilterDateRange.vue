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
const dateRange = ref<[string, string] | []>(
  props.widget.props.defaultValue || [],
);

const label = computed(() => props.widget.props.label || '');
const startPlaceholder = computed(
  () =>
    props.widget.props.startPlaceholder ||
    $t('dashboard-design.material.defaultProps.filterStartDate'),
);
const endPlaceholder = computed(
  () =>
    props.widget.props.endPlaceholder ||
    $t('dashboard-design.material.defaultProps.filterEndDate'),
);
const startParamKey = computed(
  () => props.widget.props.startParamKey || '',
);
const endParamKey = computed(
  () => props.widget.props.endParamKey || '',
);
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

function handleChange(val: [string, string] | null) {
  if (props.isDesignMode) return;
  if (val && val.length === 2) {
    if (startParamKey.value) {
      store.updateGlobalParam(startParamKey.value, val[0]);
    }
    if (endParamKey.value) {
      store.updateGlobalParam(endParamKey.value, val[1]);
    }
  } else {
    if (startParamKey.value) {
      store.updateGlobalParam(startParamKey.value, '');
    }
    if (endParamKey.value) {
      store.updateGlobalParam(endParamKey.value, '');
    }
  }
}

watch(
  () => props.widget.props.defaultValue,
  (val) => {
    if (!props.isDesignMode && Array.isArray(val) && val.length === 2) {
      dateRange.value = val as [string, string];
      if (startParamKey.value) {
        store.updateGlobalParam(startParamKey.value, val[0]);
      }
      if (endParamKey.value) {
        store.updateGlobalParam(endParamKey.value, val[1]);
      }
    }
  },
  { immediate: true },
);

const hasParamKey = computed(
  () => startParamKey.value || endParamKey.value,
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
      v-model="dateRange"
      type="daterange"
      :start-placeholder="startPlaceholder"
      :end-placeholder="endPlaceholder"
      :disabled="isDesignMode"
      :format="dateFormat"
      :value-format="dateFormat"
      :size="componentSize"
      clearable
      class="!flex-1"
      @change="handleChange"
    />
    <span
      v-if="isDesignMode && !hasParamKey"
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
