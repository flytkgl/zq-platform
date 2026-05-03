<script lang="ts" setup>
/**
 * 页面发布弹窗
 * 复用 PagePublishInfoEditor 公共组件
 */
import type { PagePublishInfo } from '#/components/form-editor';

import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { ElButton, ElDialog, ElMessage, ElScrollbar } from 'element-plus';

import { publishPageApi } from '#/api/online-dev/page-manager';
import { PagePublishInfoEditor } from '#/components/form-editor';

interface Props {
  modelValue: boolean;
  pageId: string;
  pageName: string;
  pageCode: string;
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

// 发布表单
const publishForm = ref<PagePublishInfo>({
  menu_name: '',
  menu_parent_id: undefined,
  menu_icon: 'lucide:layout-dashboard',
  menu_order: 0,
});

// 监听弹窗打开
watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      // 初始化表单
      publishForm.value = {
        menu_name: props.pageName,
        menu_parent_id: undefined,
        menu_icon: 'lucide:layout-dashboard',
        menu_order: 0,
      };
    }
  },
);

async function handlePublish() {
  if (!publishForm.value.menu_name) {
    ElMessage.warning($t('page-manager.placeholder.name'));
    return;
  }

  loading.value = true;
  try {
    await publishPageApi(props.pageId, {
      menu_name: publishForm.value.menu_name,
      menu_parent_id: publishForm.value.menu_parent_id || undefined,
      menu_icon: publishForm.value.menu_icon,
      menu_order: publishForm.value.menu_order,
    });
    ElMessage.success($t('page-manager.publishDialog.success'));
    emit('published');
    dialogVisible.value = false;
  } catch (error: any) {
    ElMessage.error(error?.message || $t('page-manager.publishDialog.failed'));
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <ElDialog
    v-model="dialogVisible"
    :title="$t('page-manager.publishDialog.title')"
    width="500px"
    :close-on-click-modal="false"
    destroy-on-close
    align-center
    append-to-body
  >
    <ElScrollbar max-height="60vh">
      <div class="pr-4">
        <PagePublishInfoEditor
          v-model="publishForm"
          :page-code="pageCode"
          :show-route-info="true"
        />
      </div>
    </ElScrollbar>

    <template #footer>
      <ElButton @click="dialogVisible = false">
        {{ $t('common.cancel') }}
      </ElButton>
      <ElButton type="primary" :loading="loading" @click="handlePublish">
        {{ $t('page-manager.publish') }}
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
