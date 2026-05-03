<script setup lang="ts">
import { ref, watch } from 'vue';

import { $t } from '@vben/locales';

import {
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
} from 'element-plus';

import { createFolder } from '#/api/core/file';

import { useFileManager } from '../composables/useFileManager';

const { createFolderDialogVisible, currentFolderId, fetchFiles } =
  useFileManager();

const form = ref({
  name: '',
});

const formRef = ref<any>(null);
const loading = ref(false);

// 监听对话框打开，重置表单
watch(createFolderDialogVisible, (val) => {
  if (val) {
    form.value.name = '';
  }
});

const handleClose = () => {
  createFolderDialogVisible.value = false;
};

const handleSubmit = async () => {
  if (!form.value.name) {
    ElMessage.warning($t('file-manager.pleaseEnterFolderName'));
    return;
  }

  loading.value = true;
  try {
    await createFolder({
      name: form.value.name,
      parent_id: currentFolderId.value || undefined,
    });
    ElMessage.success($t('file-manager.createSuccess'));
    createFolderDialogVisible.value = false;
    // 刷新列表
    fetchFiles();
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <ElDialog
    v-model="createFolderDialogVisible"
    :title="$t('file-manager.newFolder')"
    width="400px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <ElForm ref="formRef" :model="form" @submit.prevent="handleSubmit">
      <ElFormItem :label="$t('file-manager.folderName')">
        <ElInput
          v-model="form.name"
          :placeholder="$t('file-manager.pleaseEnterFolderName')"
          autofocus
          @keyup.enter="handleSubmit"
        />
      </ElFormItem>
    </ElForm>
    <template #footer>
      <div class="dialog-footer">
        <ElButton @click="handleClose">
          {{ $t('file-manager.cancel') }}
        </ElButton>
        <ElButton type="primary" :loading="loading" @click="handleSubmit">
          {{ $t('file-manager.confirm') }}
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>
