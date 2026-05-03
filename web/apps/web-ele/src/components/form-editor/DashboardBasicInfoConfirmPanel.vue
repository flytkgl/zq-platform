<script setup lang="ts">
/**
 * 仪表盘基础信息确认面板
 * 复用 PageBasicInfoEditor 公共组件
 */
import type { PageBasicInfo } from './PageBasicInfoEditor.vue';

import { computed, ref, watch } from 'vue';

import { Maximize, Minimize } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import PageBasicInfoEditor from './PageBasicInfoEditor.vue';

export interface DashboardBasicInfoData {
  type: string;
  title: string;
  data: {
    category: string;
    code: string;
    description: string;
    name: string;
    sort: number;
  };
  nodeId: string;
}

const props = defineProps<{
  basicInfo?: DashboardBasicInfoData;
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

const form = ref<PageBasicInfo>({
  name: '',
  code: '',
  category: 'dashboard',
  description: '',
  sort: 0,
});

watch(
  () => props.basicInfo,
  (info) => {
    if (info?.data) {
      form.value = {
        name: info.data.name || '',
        code: info.data.code || '',
        category: info.data.category || 'dashboard',
        description: info.data.description || '',
        sort: info.data.sort || 0,
      };
    }
  },
  { immediate: true },
);

const handleConfirm = () => {
  emit('confirm', { ...form.value });
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
        {{ basicInfo?.title || $t('ai-platform.dashboard.basicInfo.title') }}
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
      <PageBasicInfoEditor v-model="form" />
    </div>
  </div>
</template>
