<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { ArrowLeft, Save } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElMessage } from 'element-plus';

import {
  getPageDetailApi,
  updatePageApi,
} from '#/api/online-dev/page-manager';
import DashboardDesign from '#/components/dashboard-design/index.vue';
import { useDashboardDesignStore } from '#/components/dashboard-design/store/dashboardDesignStore';

const route = useRoute();
const router = useRouter();
const dashboardDesignStore = useDashboardDesignStore();

const pageId = route.params.id as string;
const loading = ref(false);
const pageName = ref('');
const pageCode = ref('');

// 自动保存状态
const autoSaveStatus = ref<'saved' | 'saving' | 'unsaved'>('saved');

// 加载页面数据
async function loadPageData() {
  if (!pageId) return;
  loading.value = true;
  try {
    const page = await getPageDetailApi(pageId);

    pageName.value = page.name;
    pageCode.value = page.code;

    // 恢复页面设计配置
    if (page.page_config && Object.keys(page.page_config).length > 0) {
      dashboardDesignStore.importConfig(JSON.stringify(page.page_config));
    }
  } catch (error: any) {
    ElMessage.error(error?.message || $t('page-manager.editor.loadFailed'));
  } finally {
    loading.value = false;
  }
}

// 保存
async function handleSave(showMessage = true) {
  loading.value = true;
  autoSaveStatus.value = 'saving';
  try {
    const pageConfig = JSON.parse(dashboardDesignStore.exportConfig());

    await updatePageApi(pageId, {
      page_config: pageConfig,
    });

    autoSaveStatus.value = 'saved';
    if (showMessage) {
      ElMessage.success($t('page-manager.saveSuccess'));
    }
  } catch (error: any) {
    autoSaveStatus.value = 'unsaved';
    if (showMessage) {
      ElMessage.error(error?.message || $t('common.saveFailed'));
    }
  } finally {
    loading.value = false;
  }
}

// 返回上一页
function handleBack() {
  dashboardDesignStore.clearCanvas();
  dashboardDesignStore.setActive(null);
  router.back();
}

// 处理设计器保存事件
function handleDesignSave(_config: string) {
  // 配置已经在 store 中，保存时会自动获取
}

onMounted(() => {
  loadPageData();
});
</script>

<template>
  <div class="flex h-screen w-full flex-col">
    <!-- Header -->
    <header
      class="bg-background-deep z-10 m-3 flex h-14 shrink-0 items-center justify-between rounded-[8px] px-4 shadow-sm"
    >
      <div class="flex items-center gap-4">
        <ElButton link :icon="ArrowLeft" @click="handleBack" />
        <div v-if="pageName" class="flex flex-col">
          <span class="text-foreground text-sm font-bold">{{ pageName }}</span>
          <span class="text-muted-foreground font-mono text-xs">{{
            pageCode
          }}</span>
        </div>
      </div>

      <!-- 右侧：操作按钮 -->
      <div class="flex items-center gap-3">
        <span class="text-muted-foreground text-xs">
          <template v-if="autoSaveStatus === 'saving'">{{
            $t('page-manager.editor.autoSave.saving')
          }}</template>
          <template v-else-if="autoSaveStatus === 'saved'">{{
            $t('page-manager.editor.autoSave.saved')
          }}</template>
          <template v-else>{{
            $t('page-manager.editor.autoSave.unsaved')
          }}</template>
        </span>
        <ElButton
          type="primary"
          :loading="loading"
          :icon="Save"
          @click="handleSave(true)"
        >
          {{ $t('common.save') }}
        </ElButton>
      </div>
    </header>

    <!-- 页面设计 -->
    <div
      class="bg-background-deep relative mx-3 mb-3 flex-1 overflow-hidden rounded-[8px]"
      v-loading="loading"
    >
      <DashboardDesign @save="handleDesignSave" />
    </div>
  </div>
</template>
