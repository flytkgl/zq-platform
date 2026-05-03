<script setup lang="ts">
import type { DashboardWidget } from '../../store/dashboardDesignStore';

import { computed, onMounted, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { ElOption, ElSelect } from 'element-plus';

import { requestClient } from '#/api/request';

import { useDashboardDesignStore } from '../../store/dashboardDesignStore';

const props = defineProps<{
  isDesignMode?: boolean;
  widget: DashboardWidget;
}>();

const store = useDashboardDesignStore();
const selectValue = ref<any>(props.widget.props.defaultValue || '');
const dynamicOptions = ref<{ label: string; value: any }[]>([]);
const loadingOptions = ref(false);

const label = computed(() => props.widget.props.label || '');
const placeholder = computed(
  () =>
    props.widget.props.placeholder ||
    $t('dashboard-design.material.defaultProps.filterSelectPlaceholder'),
);
const paramKey = computed(() => props.widget.props.paramKey || '');
const multiple = computed(() => props.widget.props.multiple || false);
const clearable = computed(() => props.widget.props.clearable !== false);

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

const options = computed(() => {
  if (props.widget.props.optionSource === 'dataSource') {
    return dynamicOptions.value;
  }
  return props.widget.props.options || [];
});

async function loadDynamicOptions() {
  const code = props.widget.props.optionDataSourceCode;
  if (!code) return;
  try {
    loadingOptions.value = true;
    const response = await requestClient.get(
      `/api/core/data-source/execute/${code}`,
    );
    const rawData = response?.data ?? response;
    const data = Array.isArray(rawData) ? rawData : [];
    const labelField = props.widget.props.optionLabelField || 'label';
    const valueField = props.widget.props.optionValueField || 'value';
    dynamicOptions.value = data.map((item: any) => ({
      label: String(item[labelField] ?? ''),
      value: item[valueField],
    }));
  } catch (error) {
    console.error('Failed to load filter options:', error);
  } finally {
    loadingOptions.value = false;
  }
}

function handleChange(val: any) {
  if (props.isDesignMode) return;
  if (paramKey.value) {
    store.updateGlobalParam(paramKey.value, val);
  }
}

function handleClear() {
  if (props.isDesignMode) return;
  if (paramKey.value) {
    store.updateGlobalParam(paramKey.value, multiple.value ? [] : '');
  }
}

watch(
  () => props.widget.props.defaultValue,
  (val) => {
    if (!props.isDesignMode && val !== undefined) {
      selectValue.value = val;
      if (paramKey.value) {
        store.updateGlobalParam(paramKey.value, val);
      }
    }
  },
  { immediate: true },
);

onMounted(() => {
  if (props.widget.props.optionSource === 'dataSource') {
    loadDynamicOptions();
  }
});
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
    <ElSelect
      v-model="selectValue"
      :placeholder="placeholder"
      :disabled="isDesignMode"
      :multiple="multiple"
      :clearable="clearable"
      :loading="loadingOptions"
      :size="componentSize"
      class="flex-1"
      @change="handleChange"
      @clear="handleClear"
    >
      <ElOption
        v-for="opt in options"
        :key="opt.value"
        :label="opt.label"
        :value="opt.value"
      />
    </ElSelect>
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
