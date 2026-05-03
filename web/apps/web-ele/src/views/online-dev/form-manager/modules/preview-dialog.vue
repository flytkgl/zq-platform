<script setup lang="ts">
import { reactive, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import {
  ElButton,
  ElDialog,
  ElForm,
  ElMessage,
  ElScrollbar,
} from 'element-plus';

import { getFormDetailApi } from '#/api/online-dev/form-manager';
import PreviewItem from '#/components/form-design/components/PreviewItem.vue';

import { useFormData } from '../composables/useFormData';

const props = defineProps<{
  formId: null | string;
}>();

const visible = defineModel<boolean>({ default: false });

const loading = ref(false);
const formConfig = ref<any>(null);
const formData = reactive<any>({});
const formRef = ref();

const { initFormData, resetFormData } = useFormData(formData);

// 加载表单配置
async function loadFormConfig() {
  if (!props.formId) return;

  loading.value = true;
  try {
    const res = await getFormDetailApi(props.formId);
    formConfig.value = res.form_config;

    // 重置表单数据
    resetFormData();

    // 初始化表单数据
    if (formConfig.value?.items) {
      initFormData(formConfig.value.items);
    }
  } catch (error) {
    ElMessage.error($t('form-manager.previewDialog.loadFailed'));
    console.error(error);
  } finally {
    loading.value = false;
  }
}

// 监听弹窗打开
watch(visible, (val) => {
  if (val && props.formId) {
    loadFormConfig();
  }
});

// 验证提交
const handleSubmit = async () => {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
    ElMessage.success($t('form-manager.previewDialog.verifySuccess'));
    console.log('表单数据:', formData);
  } catch {
    ElMessage.error($t('form-manager.previewDialog.verifyFailed'));
  }
};
</script>

<template>
  <ElDialog
    v-model="visible"
    :title="$t('form-manager.previewDialog.title')"
    width="800px"
    destroy-on-close
    append-to-body
    align-center
  >
    <ElScrollbar v-loading="loading" max-height="60vh">
      <div
        v-if="formConfig"
        :style="{
          padding: `${formConfig.formPadding || 20}px`,
          margin: `${formConfig.formMargin || 0}px`,
          width: formConfig.formWidth || '100%',
          maxWidth: formConfig.formMaxWidth || 'none',
          backgroundColor: formConfig.formBackground || 'transparent',
          border: formConfig.formBorder
            ? '1px solid var(--el-border-color)'
            : 'none',
          borderRadius: formConfig.formBorder
            ? `${formConfig.formBorderRadius || 4}px`
            : '0',
          boxShadow: formConfig.formShadow
            ? '0 2px 12px 0 rgba(0, 0, 0, 0.1)'
            : 'none',
        }"
      >
        <ElForm
          ref="formRef"
          :model="formData"
          :label-width="`${formConfig.labelWidth || 100}px`"
          :label-position="formConfig.labelPosition || 'right'"
          :size="formConfig.size || 'default'"
          :disabled="formConfig.disabled || false"
          :style="{
            '--el-form-item-margin-bottom': `${formConfig.itemSpacing || 18}px`,
          }"
        >
          <PreviewItem
            v-for="item in formConfig.items"
            :key="item.id"
            :item="item"
            :model-value="formData"
          />
        </ElForm>
      </div>

      <div v-if="formConfig" class="bg-accent mt-4 rounded p-4">
        <div class="text-muted-foreground mb-2 text-sm font-bold">
          {{ $t('form-manager.previewDialog.realtimeData') }}
        </div>
        <pre class="text-muted-foreground overflow-auto text-xs">{{
          formData
        }}</pre>
      </div>

      <div
        v-if="!formConfig && !loading"
        class="text-muted-foreground py-8 text-center"
      >
        {{ $t('form-manager.previewDialog.noConfig') }}
      </div>
    </ElScrollbar>

    <template #footer>
      <ElButton @click="visible = false">
        {{ $t('form-manager.previewDialog.close') }}
      </ElButton>
      <ElButton type="primary" @click="handleSubmit">
        {{ $t('form-manager.previewDialog.verifySubmit') }}
      </ElButton>
    </template>
  </ElDialog>
</template>
