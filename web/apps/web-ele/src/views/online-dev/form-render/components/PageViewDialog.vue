<script lang="ts" setup>
/**
 * 页面查看弹窗组件
 * 用于在自定义按钮点击后显示页面内容
 */
import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { ElEmpty, ElMessage } from 'element-plus';

import { getPageByCodeApi } from '#/api/online-dev/page-manager';
import DashboardRenderer from '#/components/dashboard-design/DashboardRenderer.vue';
import { ZqDialog } from '#/components/zq-dialog';

interface Props {
  modelValue: boolean;
  pageCode: string;
  title?: string;
  width?: string;
  fullscreen?: boolean;
  rowData?: Record<string, any>;
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  width: '80%',
  fullscreen: false,
  rowData: () => ({}),
});

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const loading = ref(false);
const pageConfig = ref<string>('');
const pageName = ref('');

async function loadPageData() {
  if (!props.pageCode) {
    ElMessage.error($t('form-manager.listDesign.pageCodeRequired'));
    return;
  }

  loading.value = true;
  try {
    const page = await getPageByCodeApi(props.pageCode);
    pageName.value = page.name;

    pageConfig.value =
      page.page_config && Object.keys(page.page_config).length > 0
        ? JSON.stringify(page.page_config)
        : '';
  } catch (error: any) {
    ElMessage.error(
      error?.message || $t('form-manager.listDesign.pageLoadFailed'),
    );
    visible.value = false;
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      loadPageData();
    } else {
      pageConfig.value = '';
      pageName.value = '';
    }
  },
);

const dialogTitle = computed(() => {
  return (
    props.title || pageName.value || $t('form-manager.listDesign.pageView')
  );
});
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="dialogTitle"
    :width="width"
    :fullscreen="fullscreen"
    :close-on-click-modal="false"
    destroy-on-close
    :show-footer="false"
  >
    <div v-loading="loading" class="page-view-content">
      <DashboardRenderer v-if="pageConfig" :config="pageConfig" />
      <ElEmpty
        v-else-if="!loading"
        :description="$t('form-manager.listDesign.pageNoConfig')"
      />
    </div>
  </ZqDialog>
</template>

<style scoped>
.page-view-content {
  /* min-height: 400px; */
  height: calc(100vh - 200px);
  overflow: auto;
}
</style>
