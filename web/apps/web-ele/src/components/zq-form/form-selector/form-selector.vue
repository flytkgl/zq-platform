<script lang="ts" setup>
import type { FormSelectorEmits, FormSelectorProps } from './types';

import { computed, ref, watch } from 'vue';

import { Table2 } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElOption, ElSelect } from 'element-plus';

import { requestClient } from '#/api/request';
import { ZqDialog } from '#/components/zq-dialog';
import FormDataList from '#/views/online-dev/form-render/components/FormDataList.vue';

defineOptions({
  name: 'FormSelector',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<FormSelectorProps>(), {
  multiple: false,
  collapseTags: false,
  maxCollapseTags: 1,
  placeholder: () => $t('form-design.attribute.clickToSelect'),
  disabled: false,
  clearable: true,
  dialogTitle: () => $t('form-design.attribute.selectData'),
  dialogWidth: '1200px',
  valueField: 'id',
  labelField: 'name',
  expandMultipleToRows: false,
  externalSelectedValues: () => [],
});

const emit = defineEmits<FormSelectorEmits>();

const dialogVisible = ref(false);

// 选中的值
const selectedValues = ref<Set<string>>(new Set());
// 选中项的信息映射
const selectedItemsMap = ref<Map<string, any>>(new Map());
// 标签加载状态
const labelsLoading = ref(false);

// 触发 select-item 事件
const emitSelectItem = () => {
  const items = [...selectedValues.value]
    .map((v) => selectedItemsMap.value.get(v))
    .filter(Boolean);
  if (props.multiple) {
    emit('select-item', items.length > 0 ? items : undefined);
  } else {
    emit('select-item', items[0] || undefined);
  }
};

// 加载初始值对应的标签信息
const loadInitialLabels = async (values: any[]) => {
  if (!props.formCode) return;

  try {
    const stringValues = values.map(String);
    const ids = stringValues.join(',');
    // 使用 filter_ 前缀格式，后端会自动将逗号分隔的字符串转换为 IN 查询
    const response = await requestClient.get(
      `/api/online_dev/form-data/${props.formCode}/list`,
      {
        params: {
          [`filter_${props.valueField}`]: ids,
          pageSize: stringValues.length,
        },
      },
    );
    const data = response?.items || [];
    for (const item of data) {
      const value = String(item[props.valueField]);
      selectedItemsMap.value.set(value, item);
    }
  } catch (error) {
    console.error('加载初始标签失败:', error);
  }
};

// 初始化选中值
watch(
  () => props.modelValue,
  async (val) => {
    if (val) {
      const values = Array.isArray(val) ? val : [val];
      selectedValues.value = new Set(values.map(String));

      const missingValues = values.filter(
        (v) => !selectedItemsMap.value.has(String(v)),
      );
      if (missingValues.length > 0) {
        labelsLoading.value = true;
        await loadInitialLabels(missingValues);
        labelsLoading.value = false;

        // expandMultipleToRows 模式下不触发，避免标签加载完后误触发行展开
        if (!props.expandMultipleToRows) {
          emitSelectItem();
        }
      }
    } else {
      selectedValues.value = new Set();
      selectedItemsMap.value.clear();
    }
  },
  { immediate: true },
);

// 监听 formCode 变化，当 formCode 有值且有 modelValue 时加载标签
watch(
  () => props.formCode,
  async (formCode) => {
    if (formCode && props.modelValue) {
      const values = Array.isArray(props.modelValue)
        ? props.modelValue
        : [props.modelValue];
      const missingValues = values.filter(
        (v) => !selectedItemsMap.value.has(String(v)),
      );
      if (missingValues.length > 0) {
        labelsLoading.value = true;
        await loadInitialLabels(missingValues);
        labelsLoading.value = false;
        if (!props.expandMultipleToRows) {
          emitSelectItem();
        }
      }
    }
  },
);

// el-select 的值
const selectValue = computed(() => {
  if (labelsLoading.value) {
    return props.multiple ? [] : '';
  }

  // expandMultipleToRows 模式：输入框只显示外部 modelValue，不跟随弹窗内实时选择
  if (props.expandMultipleToRows) {
    if (!props.modelValue) return props.multiple ? [] : '';
    return props.multiple
      ? (Array.isArray(props.modelValue) ? props.modelValue : [props.modelValue])
      : (Array.isArray(props.modelValue) ? props.modelValue[0] || '' : props.modelValue);
  }

  const values = [...selectedValues.value];
  return props.multiple ? values : values[0] || '';
});

// 获取显示标签的辅助函数
const getItemLabel = (item: any, value: string): string => {
  if (!item) return value;
  // 如果指定了 labelField，优先使用
  if (props.labelField && item[props.labelField]) {
    return item[props.labelField];
  }
  // 尝试常见的标签字段名
  const fallbackFields = ['name', 'label', 'title', 'text'];
  for (const field of fallbackFields) {
    if (item[field]) {
      return item[field];
    }
  }
  return value;
};

// el-select 的选项（用于显示已选中的标签）
const selectOptions = computed(() => {
  if (labelsLoading.value) {
    return [];
  }

  // expandMultipleToRows 模式：只基于外部 modelValue 生成选项
  if (props.expandMultipleToRows) {
    if (!props.modelValue) return [];
    const vals = Array.isArray(props.modelValue) ? props.modelValue : [props.modelValue];
    return vals.filter(Boolean).map((v) => {
      const item = selectedItemsMap.value.get(String(v));
      return {
        value: String(v),
        label: getItemLabel(item, String(v)),
      };
    });
  }

  return [...selectedValues.value].map((v) => {
    const item = selectedItemsMap.value.get(v);
    return {
      value: v,
      label: getItemLabel(item, v),
    };
  });
});

// 打开弹窗
const openDialog = () => {
  if (props.disabled) return;

  // expandMultipleToRows 模式：合并子表已有行的值到选中集合
  if (props.expandMultipleToRows && props.externalSelectedValues && props.externalSelectedValues.length > 0) {
    for (const v of props.externalSelectedValues) {
      selectedValues.value.add(String(v));
    }
    selectedValues.value = new Set(selectedValues.value);
  }

  dialogVisible.value = true;
};

// 确认选择
const handleConfirm = () => {
  const values = [...selectedValues.value];
  const result = props.multiple ? values : values[0] || null;

  emit('update:modelValue', result);
  emit('change', result);
  emitSelectItem();

  dialogVisible.value = false;
};

// 清空选择
const handleClear = () => {
  selectedValues.value = new Set();
  selectedItemsMap.value.clear();
  emit('update:modelValue', props.multiple ? [] : null);
  emit('change', props.multiple ? [] : null);
  emit('select-item', undefined);
};

// 移除单个标签
const handleRemoveTag = (value: string) => {
  selectedValues.value.delete(value);
  selectedItemsMap.value.delete(value);
  selectedValues.value = new Set(selectedValues.value);

  const values = [...selectedValues.value];
  const result = props.multiple ? values : values[0] || null;
  emit('update:modelValue', result);
  emit('change', result);
  emitSelectItem();
};

// FormDataList 行选择处理
const handleRowSelect = (row: any) => {
  const value = String(row[props.valueField]);

  if (props.multiple) {
    if (selectedValues.value.has(value)) {
      selectedValues.value.delete(value);
      selectedItemsMap.value.delete(value);
    } else {
      selectedValues.value.add(value);
      selectedItemsMap.value.set(value, row);
    }
    selectedValues.value = new Set(selectedValues.value);
  } else {
    if (selectedValues.value.has(value)) {
      selectedValues.value.clear();
      selectedItemsMap.value.clear();
    } else {
      selectedValues.value = new Set([value]);
      selectedItemsMap.value.clear();
      selectedItemsMap.value.set(value, row);
    }
  }
};

// FormDataList 全选处理
const handleSelectAll = (rows: any[]) => {
  const valueField = props.valueField;
  const allValues = rows.map((row) => String(row[valueField]));

  const allSelected = allValues.every((v) => selectedValues.value.has(v));

  if (allSelected) {
    for (const row of rows) {
      const value = String(row[valueField]);
      selectedValues.value.delete(value);
      selectedItemsMap.value.delete(value);
    }
  } else {
    for (const row of rows) {
      const value = String(row[valueField]);
      selectedValues.value.add(value);
      selectedItemsMap.value.set(value, row);
    }
  }
  selectedValues.value = new Set(selectedValues.value);
};
</script>

<template>
  <div class="form-selector">
    <!-- 使用 el-select 样式 -->
    <ElSelect
      :model-value="selectValue"
      :multiple="multiple"
      :placeholder="labelsLoading ? $t('common.loading') : placeholder"
      :disabled="disabled"
      :clearable="clearable"
      :loading="labelsLoading"
      :collapse-tags="collapseTags"
      :collapse-tags-tooltip="collapseTags"
      :max-collapse-tags="maxCollapseTags"
      :suffix-icon="Table2"
      class="w-full"
      popper-class="form-selector-popper-hidden"
      @click="openDialog"
      @clear="handleClear"
      @remove-tag="handleRemoveTag"
    >
      <ElOption
        v-for="item in selectOptions"
        :key="item.value"
        :label="item.label"
        :value="item.value"
      />
    </ElSelect>

    <!-- 选择弹窗 - 使用 FormDataList 组件 -->
    <ZqDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :width="dialogWidth"
      append-to-body
      destroy-on-close
      :show-fullscreen-button="false"
      class="form-selector-dialog h-[90%]"
    >
      <div
        v-if="formCode"
        class="form-data-list-wrapper bg-background-deep rounded-[8px]"
      >
        <FormDataList
          :form-code="formCode"
          :show-toolbar="false"
          :selection-mode="true"
          :selection-multiple="multiple"
          :selected-values="selectedValues"
          :selection-value-field="valueField"
          :height-offset="160"
          @row-select="handleRowSelect"
          @select-all="handleSelectAll"
        />
      </div>
      <div v-else class="no-form-code">
        {{ $t('form-design.attribute.selectFormFirst') }}
      </div>

      <template #footer>
        <div class="flex w-full items-center justify-between">
          <div class="text-sm text-[var(--el-text-color-secondary)]">
            {{
              $t('form-design.attribute.selectedCount', {
                count: selectedValues.size,
              })
            }}
          </div>
          <div class="flex gap-2">
            <ElButton @click="dialogVisible = false">
              {{ $t('common.cancel') }}
            </ElButton>
            <ElButton type="primary" @click="handleConfirm">
              {{ $t('common.ok') }}
            </ElButton>
          </div>
        </div>
      </template>
    </ZqDialog>
  </div>
</template>

<style scoped>
.form-selector {
  width: 100%;
}

.form-data-list-wrapper {
  /* height: 74vh; */
  min-height: 100%;
}

.no-form-code {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--el-text-color-secondary);
}
</style>

<style>
/* 隐藏 el-select 的下拉菜单 */
.form-selector-popper-hidden {
  display: none !important;
}

.form-selector-dialog .el-dialog__body {
  padding: 0;
}
</style>
