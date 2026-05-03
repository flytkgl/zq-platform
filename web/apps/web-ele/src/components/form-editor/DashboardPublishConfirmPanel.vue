<script setup lang="ts">
/**
 * 仪表盘发布确认面板
 * 复用 PagePublishInfoEditor 公共组件
 */
import type { PagePublishInfo } from './PagePublishInfoEditor.vue';

import { computed, ref, watch } from 'vue';

import { Maximize, Minimize } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import PagePublishInfoEditor from './PagePublishInfoEditor.vue';

export interface DashboardPublishData {
  type: string;
  title: string;
  data: {
    application_id?: string;
    dashboard_code: string;
    dashboard_id: string;
    menu_icon: string;
    menu_name: string;
    menu_order: number;
    menu_parent_id?: string;
  };
  nodeId: string;
}

const props = defineProps<{
  publishData?: DashboardPublishData;
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

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
});

const form = ref<PagePublishInfo>({
  menu_name: '',
  menu_parent_id: undefined,
  menu_icon: 'lucide:layout-dashboard',
  menu_order: 0,
});

watch(
  () => props.publishData,
  (data) => {
    if (data?.data) {
      form.value = {
        menu_name: data.data.menu_name || '',
        menu_parent_id: data.data.menu_parent_id || undefined,
        menu_icon: data.data.menu_icon || 'lucide:layout-dashboard',
        menu_order: data.data.menu_order || 0,
      };
    }
  },
  { immediate: true },
);

const handleConfirm = () => {
  const confirmData = {
    dashboard_id: props.publishData?.data.dashboard_id,
    dashboard_code: props.publishData?.data.dashboard_code,
    menu_name: form.value.menu_name,
    menu_parent_id: form.value.menu_parent_id || '',
    menu_icon: form.value.menu_icon,
    menu_order: form.value.menu_order,
    application_id: props.publishData?.data.application_id || '',
  };
  console.log('[DashboardPublishConfirmPanel] 确认数据:', confirmData);
  emit('confirm', confirmData);
};

const handleClose = () => {
  dialogVisible.value = false;
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
      class="border-border bg-muted/50 flex items-center justify-between border-b px-4 py-3"
    >
      <div class="text-foreground font-medium">
        {{ publishData?.title || $t('ai-platform.dashboard.publish.title') }}
      </div>
      <div class="flex items-center gap-2">
        <ElButton size="small" @click="handleClose">
          {{ $t('common.cancel') }}
        </ElButton>
        <ElButton size="small" type="primary" @click="handleConfirm">
          {{ $t('common.confirmAndContinue') }}
        </ElButton>
        <ElButton
          link
          :icon="isFullscreen ? Minimize : Maximize"
          :title="isFullscreen ? '退出全屏' : '全屏'"
          @click="toggleFullscreen"
        />
      </div>
    </div>

    <!-- 内容 -->
    <div class="flex-1 overflow-y-auto p-6">
      <PagePublishInfoEditor
        v-model="form"
        :page-code="publishData?.data.dashboard_code || ''"
        :show-route-info="true"
        route-prefix="/page-render/"
      />
    </div>
  </div>
</template>
