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

import { renameItem } from '#/api/core/file';

import { useFileManager } from '../composables/useFileManager';

const props = defineProps<{
  item: null | { id: string; name: string; type: string };
  visible: boolean;
}>();

const emit = defineEmits(['update:visible', 'success']);

const { fetchFiles } = useFileManager();
const loading = ref(false);
const form = ref({
  name: '',
});
const formRef = ref<any>(null);

watch(
  () => props.visible,
  (val) => {
    if (val && props.item) {
      form.value.name = props.item.name;
    }
  },
);

const handleClose = () => {
  emit('update:visible', false);
};

const handleSubmit = async () => {
  if (!props.item) return;
  if (!form.value.name) {
    ElMessage.warning($t('file-manager.pleaseEnterName'));
    return;
  }

  loading.value = true;
  try {
    await renameItem(props.item.id, {
      name: form.value.name,
    });
    ElMessage.success($t('file-manager.renameSuccess'));
    emit('update:visible', false);
    emit('success');
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
    :model-value="visible"
    :title="$t('file-manager.rename')"
    width="400px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <ElForm ref="formRef" :model="form" @submit.prevent="handleSubmit">
      <ElFormItem :label="$t('file-manager.name')">
        <ElInput
          v-model="form.name"
          :placeholder="$t('file-manager.pleaseEnterName')"
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
