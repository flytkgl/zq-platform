<script lang="ts" setup>
/**
 * 表单基础信息编辑组件
 * 可用于：表单管理器、工作流设计预览编辑
 */
import { computed } from 'vue';

import { $t } from '@vben/locales';

import {
  ElForm,
  ElFormItem,
  ElInput,
  ElOption,
  ElSelect,
} from 'element-plus';

export interface BasicFormData {
  name: string;
  code: string;
  form_type: 'normal' | 'workflow';
  sort: number;
  description: string;
}

interface Props {
  modelValue: BasicFormData;
  disabled?: boolean;
  showTitle?: boolean;
  labelWidth?: string;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  showTitle: true,
  labelWidth: '100px',
});

const emit = defineEmits<{
  'update:modelValue': [value: BasicFormData];
}>();

const formData = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

// 更新单个字段
function updateField<K extends keyof BasicFormData>(key: K, value: BasicFormData[K]) {
  emit('update:modelValue', { ...props.modelValue, [key]: value });
}
</script>

<template>
  <div class="basic-info-editor">
    <h3 v-if="showTitle" class="mb-6 text-center text-lg font-medium">
      {{ $t('form-manager.editor.steps.basic') }}
    </h3>
    <ElForm
      :model="formData"
      :label-width="labelWidth"
      label-position="right"
      :disabled="disabled"
    >
      <ElFormItem :label="$t('form-manager.name')" required>
        <ElInput
          :model-value="formData.name"
          :placeholder="$t('form-manager.placeholder.name')"
          clearable
          @update:model-value="updateField('name', $event)"
        />
      </ElFormItem>
      <ElFormItem :label="$t('form-manager.code')" required>
        <ElInput
          :model-value="formData.code"
          :placeholder="$t('form-manager.placeholder.code')"
          clearable
          @update:model-value="updateField('code', $event)"
        />
      </ElFormItem>
      <ElFormItem :label="$t('form-manager.type')" required>
        <ElSelect
          :model-value="formData.form_type"
          :placeholder="$t('form-manager.placeholder.type')"
          class="w-full"
          @update:model-value="updateField('form_type', $event)"
        >
          <ElOption :label="$t('form-manager.typeMap.normal')" value="normal" />
          <ElOption :label="$t('form-manager.typeMap.workflow')" value="workflow" />
        </ElSelect>
      </ElFormItem>
      <ElFormItem :label="$t('common.sort')">
        <ElInput
          :model-value="formData.sort"
          type="number"
          placeholder="0"
          @update:model-value="updateField('sort', Number($event))"
        />
      </ElFormItem>
      <ElFormItem :label="$t('form-manager.description')">
        <ElInput
          :model-value="formData.description"
          type="textarea"
          :rows="4"
          :placeholder="$t('form-manager.editor.placeholder.remark')"
          @update:model-value="updateField('description', $event)"
        />
      </ElFormItem>
    </ElForm>
  </div>
</template>

<style scoped>
.basic-info-editor {
  width: 100%;
}
</style>
