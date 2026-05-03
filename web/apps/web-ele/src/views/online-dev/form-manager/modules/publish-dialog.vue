<script lang="ts" setup>
import type { FormPublishInput } from '#/api/online-dev/form-manager';

import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { ElButton, ElDialog, ElMessage, ElScrollbar } from 'element-plus';

import { publishFormApi } from '#/api/online-dev/form-manager';
import PublishInfoEditor from '#/components/form-editor/PublishInfoEditor.vue';

interface Props {
  modelValue: boolean;
  formId: string;
  formName: string;
  formCode: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  published: [];
  'update:modelValue': [value: boolean];
}>();

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const loading = ref(false);

// 表单数据
const formData = ref<FormPublishInput>({
  menu_name: '',
  menu_parent_id: undefined,
  menu_icon: 'lucide:file-text',
  menu_order: 0,
});

// 监听弹窗打开
watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      // 重置表单，菜单名称默认为表单名称
      formData.value = {
        menu_name: props.formName,
        menu_parent_id: undefined,
        menu_icon: 'lucide:file-text',
        menu_order: 0,
      };
    }
  },
);

// 提交发布
async function handlePublish() {
  if (!formData.value.menu_name) {
    ElMessage.warning($t('form-manager.placeholder.name'));
    return;
  }

  loading.value = true;
  try {
    await publishFormApi(props.formId, formData.value);
    ElMessage.success($t('form-manager.publishDialog.success'));
    emit('published');
    dialogVisible.value = false;
  } catch (error: any) {
    ElMessage.error(error?.message || $t('form-manager.publishDialog.failed'));
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <ElDialog
    v-model="dialogVisible"
    :title="$t('form-manager.publishDialog.title')"
    width="500px"
    destroy-on-close
    align-center
    append-to-body
  >
    <ElScrollbar max-height="60vh">
      <div class="pr-4">
        <PublishInfoEditor
          v-model="formData"
          :form-code="formCode"
          :show-route-info="true"
        />
      </div>
    </ElScrollbar>

    <template #footer>
      <ElButton @click="dialogVisible = false">
        {{ $t('common.cancel') }}
      </ElButton>
      <ElButton type="primary" :loading="loading" @click="handlePublish">
        {{ $t('form-manager.publishDialog.confirmPublish') }}
      </ElButton>
    </template>
  </ElDialog>
</template>

<style>
/* 确保 IconPicker 的弹出层在 Dialog 之上 */
.z-popup {
  z-index: 2100 !important;
}
</style>
