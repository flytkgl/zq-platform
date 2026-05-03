<script setup lang="ts">
/**
 * 仪表盘设计确认面板
 * 复用 DashboardDesign 组件
 */
import { computed, ref, watch } from 'vue';

import { Maximize, Minimize } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import DashboardDesign from '#/components/dashboard-design/index.vue';
import { useDashboardDesignStore } from '#/components/dashboard-design/store/dashboardDesignStore';

export interface DashboardDesignData {
  type: string;
  title: string;
  data: {
    dashboard_code?: string;
    design_suggestion?: string;
    design_title?: string;
    page_config?: Record<string, any>;
  };
  nodeId: string;
}

const props = defineProps<{
  design?: DashboardDesignData;
  visible: boolean;
}>();

const emit = defineEmits<{
  close: [];
  confirm: [data: Record<string, any>];
  'update:visible': [value: boolean];
}>();

// 全屏状态
const isFullscreen = ref(false);

// 切换全屏
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

const dashboardDesignStore = useDashboardDesignStore();

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
});

// 监听设计数据变化，导入初始配置
watch(
  () => props.design,
  (design) => {
    if (
      design?.data?.page_config &&
      Object.keys(design.data.page_config).length > 0
    ) {
      dashboardDesignStore.importConfig(
        JSON.stringify(design.data.page_config),
      );
    } else {
      dashboardDesignStore.clearCanvas();
    }
  },
  { immediate: true },
);

const handleConfirm = () => {
  // 获取设计器配置
  const pageConfig = JSON.parse(dashboardDesignStore.exportConfig());

  emit('confirm', {
    page_config: pageConfig,
    design_title:
      props.design?.data?.design_title ||
      $t('ai-platform.dashboard.design.title'),
  });
};

const handleClose = () => {
  dialogVisible.value = false;
  dashboardDesignStore.clearCanvas();
  dashboardDesignStore.setActive(null);
  emit('close');
};
</script>

<template>
  <div
    v-if="visible"
    class="border-border bg-card flex flex-col rounded-lg"
    :class="[isFullscreen ? 'fixed inset-0 z-50 ml-0' : 'ml-3 h-full w-full']"
  >
    <!-- 头部 -->
    <div
      class="border-border bg-muted/50 flex shrink-0 items-center justify-between border-b px-4 py-3"
    >
      <div class="text-foreground flex items-center gap-3 font-medium">
        <div
          class="bg-primary flex h-8 w-8 items-center justify-center rounded"
        >
          <span class="text-sm font-bold text-white">D</span>
        </div>
        <span>{{
          design?.title || $t('ai-platform.dashboard.design.title')
        }}</span>
      </div>
      <div class="flex items-center gap-2">
        <ElButton size="small" @click="handleClose">
          {{ $t('common.cancel') }}
        </ElButton>
        <ElButton size="small" type="primary" @click="handleConfirm">
          {{ $t('common.confirmAndContinue') }}
        </ElButton>
        <div class="bg-border mx-1 h-5 w-px"></div>
        <ElButton
          link
          :icon="isFullscreen ? Minimize : Maximize"
          :title="isFullscreen ? '退出全屏' : '全屏'"
          @click="toggleFullscreen"
        />
      </div>
    </div>

    <!-- 设计器内容 -->
    <div class="flex-1 overflow-hidden">
      <DashboardDesign />
    </div>
  </div>
</template>
