<script lang="ts" setup>
import type { CodeGeneratorEmits, CodeGeneratorProps } from './types';

import { onMounted, ref, watch } from 'vue';

import { ElButton, ElInput, ElMessage } from 'element-plus';

import { requestClient } from '#/api/request';

defineOptions({
  name: 'CodeGenerator',
});

const props = withDefaults(defineProps<CodeGeneratorProps>(), {
  prefix: '',
  separator: '',
  generateMode: 'date_seq',
  dateFormat: 'YYYYMMDD',
  seqLength: 4,
  seqResetRule: 'daily',
  randomLength: 6,
  customTemplate: '',
  businessType: 'default',
  disabled: true,
  readonly: true,
  placeholder: '自动生成编码',
  generateOnMount: true,
  isEdit: false,
});

const emit = defineEmits<CodeGeneratorEmits>();

const codeValue = ref('');
const loading = ref(false);
// 标记是否已经生成过编码，防止重复生成
const hasGenerated = ref(false);

const generateCode = async () => {
  if (loading.value) return;

  loading.value = true;

  try {
    const response = await requestClient.post<{ code: string }>(
      '/api/core/code-generator/generate',
      {
        prefix: props.prefix,
        separator: props.separator,
        generate_mode: props.generateMode,
        date_format: props.dateFormat,
        seq_length: props.seqLength,
        seq_reset_rule: props.seqResetRule,
        random_length: props.randomLength,
        custom_template: props.customTemplate,
        business_type: props.businessType,
      },
    );

    if (response && response.code) {
      codeValue.value = response.code;
      hasGenerated.value = true;
      emit('update:modelValue', response.code);
      emit('change', response.code);
    }
  } catch (error) {
    console.error('生成编码失败:', error);
    ElMessage.error('生成编码失败，请重试');
  } finally {
    loading.value = false;
  }
};

// 监听外部值变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal !== undefined && newVal !== codeValue.value) {
      codeValue.value = newVal;
      // 如果接收到非空的外部值，标记为已生成，阻止后续自动生成
      if (newVal) {
        hasGenerated.value = true;
      }
    }
  },
  { immediate: true },
);

onMounted(() => {
  // 如果初始就有值，确保显示
  if (props.modelValue) {
    codeValue.value = props.modelValue;
    hasGenerated.value = true;
  }

  // 只有在非编辑模式下，且需要自动生成，且当前没有值时才生成
  if (
    !props.isEdit &&
    props.generateOnMount &&
    !props.modelValue &&
    !hasGenerated.value
  ) {
    generateCode();
  }
});

defineExpose({
  generateCode,
});
</script>

<template>
  <div class="code-generator-wrapper flex items-center gap-2">
    <ElInput
      v-model="codeValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      class="flex-1"
    />
    <ElButton
      v-if="!readonly"
      type="primary"
      :loading="loading"
      :disabled="disabled"
      @click="generateCode"
    >
      生成
    </ElButton>
  </div>
</template>

<style scoped>
.code-generator-wrapper {
  width: 100%;
}
</style>
