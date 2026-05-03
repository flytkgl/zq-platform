<script lang="ts" setup>
/**
 * 页面基础信息编辑器
 * 供 page-manager 和工作流节点共用
 */
import { watch } from 'vue';

import { $t } from '@vben/locales';

import {
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElOption,
  ElSelect,
} from 'element-plus';

export interface PageBasicInfo {
  name: string;
  code: string;
  category: string;
  description: string;
  sort: number;
}

interface Props {
  modelValue: PageBasicInfo;
  isEditMode?: boolean;
  showTitle?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isEditMode: false,
  showTitle: false,
});

const emit = defineEmits<{
  'update:modelValue': [value: PageBasicInfo];
}>();

// 更新表单数据
function updateFormData(key: keyof PageBasicInfo, value: any) {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: value,
  });
}

// 分类选项
const categoryOptions = [
  { label: $t('page-manager.categoryMap.dashboard'), value: 'dashboard' },
  { label: $t('page-manager.categoryMap.portal'), value: 'portal' },
  { label: $t('page-manager.categoryMap.databoard'), value: 'databoard' },
  { label: $t('page-manager.categoryMap.other'), value: 'other' },
];

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  () => {},
  { deep: true },
);
</script>

<template>
  <div>
    <h3 v-if="showTitle" class="mb-6 text-center text-lg font-medium">
      {{ $t('page-manager.editor.steps.basic') }}
    </h3>
    <ElForm :model="modelValue" label-width="100px" label-position="right">
      <ElFormItem :label="$t('page-manager.name')" required>
        <ElInput
          :model-value="modelValue.name"
          :placeholder="$t('page-manager.placeholder.name')"
          clearable
          @update:model-value="updateFormData('name', $event)"
        />
      </ElFormItem>

      <ElFormItem :label="$t('page-manager.code')" required>
        <ElInput
          :model-value="modelValue.code"
          :placeholder="$t('page-manager.placeholder.code')"
          clearable
          :disabled="isEditMode"
          @update:model-value="updateFormData('code', $event)"
        />
        <template #error>
          <div
            v-if="
              modelValue.code &&
              !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(modelValue.code)
            "
            class="el-form-item__error"
          >
            {{ $t('page-manager.codeFormatError') }}
          </div>
        </template>
      </ElFormItem>

      <ElFormItem :label="$t('page-manager.category')">
        <ElSelect
          :model-value="modelValue.category"
          :placeholder="$t('page-manager.placeholder.category')"
          class="w-full"
          clearable
          @update:model-value="updateFormData('category', $event)"
        >
          <ElOption
            v-for="opt in categoryOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </ElSelect>
      </ElFormItem>

      <ElFormItem :label="$t('common.sort')">
        <ElInputNumber
          :model-value="modelValue.sort"
          :min="0"
          :max="9999"
          class="w-full"
          @update:model-value="updateFormData('sort', $event ?? 0)"
        />
      </ElFormItem>

      <ElFormItem :label="$t('page-manager.description')">
        <ElInput
          :model-value="modelValue.description"
          type="textarea"
          :rows="4"
          :placeholder="$t('page-manager.placeholder.description')"
          @update:model-value="updateFormData('description', $event)"
        />
      </ElFormItem>
    </ElForm>
  </div>
</template>
