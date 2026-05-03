<script lang="ts" setup>
import type { LinkedFieldEmits, LinkedFieldProps } from './types';

import { computed, watch } from 'vue';

import { $t } from '@vben/locales';

import { ElInput } from 'element-plus';

defineOptions({
  name: 'LinkedField',
});

const props = withDefaults(defineProps<LinkedFieldProps>(), {
  placeholder: '',
  disabled: true,
});

const emit = defineEmits<LinkedFieldEmits>();

// 计算显示值
const displayValue = computed(() => {
  if (!props.sourceField || !props.displayField || !props.formData) {
    return '';
  }

  // 获取源字段的值（可能是选中项的完整对象或者ID）
  const sourceValue = props.formData[props.sourceField];

  if (!sourceValue) {
    return '';
  }

  // 如果源字段值是对象，直接从中取 displayField
  if (typeof sourceValue === 'object' && sourceValue !== null) {
    return sourceValue[props.displayField] ?? '';
  }

  // 如果源字段值是数组（多选），取第一个的 displayField
  if (Array.isArray(sourceValue) && sourceValue.length > 0) {
    const firstItem = sourceValue[0];
    if (typeof firstItem === 'object' && firstItem !== null) {
      return firstItem[props.displayField] ?? '';
    }
  }

  // 如果有 _selectedItem 存储的完整对象
  const selectedItemKey = `${props.sourceField}_selectedItem`;
  const selectedItem = props.formData[selectedItemKey];
  if (selectedItem && typeof selectedItem === 'object') {
    return selectedItem[props.displayField] ?? '';
  }

  // 如果有 _selectedItems 存储的完整对象数组
  const selectedItemsKey = `${props.sourceField}_selectedItems`;
  const selectedItems = props.formData[selectedItemsKey];
  if (Array.isArray(selectedItems) && selectedItems.length > 0) {
    const firstItem = selectedItems[0];
    if (typeof firstItem === 'object' && firstItem !== null) {
      return firstItem[props.displayField] ?? '';
    }
  }

  return '';
});

// 监听显示值变化，更新 modelValue
// 注意：当 displayValue 为空但已有保存的 modelValue 时（如编辑回显场景），不覆盖
watch(
  displayValue,
  (newVal) => {
    if (newVal !== props.modelValue) {
      if (newVal) {
        emit('update:modelValue', newVal);
        emit('change', newVal);
      } else if (!props.modelValue) {
        emit('update:modelValue', undefined);
        emit('change', undefined);
      }
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="linked-field-wrapper">
    <ElInput
      :model-value="displayValue || props.modelValue"
      :placeholder="
        placeholder || $t('form-design.attribute.linkedFieldPlaceholder')
      "
      :disabled="true"
      readonly
      class="linked-field"
    />
  </div>
</template>

<style scoped>
.linked-field :deep(.el-input__inner) {
  cursor: default;
}
</style>
