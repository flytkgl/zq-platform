<script setup lang="ts">
import type { DashboardWidget } from '#/components/dashboard-design';

import { computed } from 'vue';

import {
  ChevronRight,
  ClipboardCheck,
  ClipboardList,
  FilePen,
  Play,
  Send,
  UserCheck,
} from '@vben/icons';
import { $t } from '@vben/locales';

const props = defineProps<{
  widget: DashboardWidget;
}>();

// 审批中心菜单项
const menuItems = computed(() => [
  {
    key: 'initiated',
    title: $t('dashboard-design.widgets.approvalCenter.initiated'),
    icon: Send,
    color: 'rgba(59, 130, 246, 0.85)',
    path: '/workflow/initiated',
  },
  {
    key: 'pending',
    title: $t('dashboard-design.widgets.approvalCenter.pending'),
    icon: ClipboardList,
    color: 'rgba(245, 158, 11, 0.85)',
    path: '/workflow/pending',
  },
  {
    key: 'handling',
    title: $t('dashboard-design.widgets.approvalCenter.handling'),
    icon: FilePen,
    color: 'rgba(139, 92, 246, 0.85)',
    path: '/workflow/pending',
  },
  {
    key: 'handled',
    title: $t('dashboard-design.widgets.approvalCenter.handled'),
    icon: ClipboardCheck,
    color: 'rgba(14, 165, 233, 0.85)',
    path: '/workflow/handled',
  },
  {
    key: 'copy',
    title: $t('dashboard-design.widgets.approvalCenter.copy'),
    icon: UserCheck,
    color: 'rgba(249, 115, 22, 0.85)',
    path: '/workflow/copy',
  },
  {
    key: 'start',
    title: $t('dashboard-design.widgets.approvalCenter.start'),
    icon: Play,
    color: 'rgba(20, 184, 166, 0.85)',
    path: '/workflow/start',
  },
]);

// 路由前缀
const routePrefix = computed(
  () => props.widget.props.routePrefix || '/app/workflow_center',
);

// 点击菜单项
const handleClick = (item: { path: string }) => {
  window.open(`${routePrefix.value}${item.path}`, '_blank');
};

// 点击更多
const handleMore = () => {
  window.open(`${routePrefix.value}/workflow/pending`, '_blank');
};
</script>

<template>
  <div class="approval-center flex h-full flex-col p-4">
    <!-- 头部 -->
    <div class="mb-4 flex items-center justify-between">
      <span class="text-sm font-medium">{{ widget.props.title }}</span>
      <button
        v-if="widget.props.showMore"
        type="button"
        class="text-muted-foreground hover:text-primary flex items-center gap-0.5 text-xs transition-colors"
        @click="handleMore"
      >
        {{ $t('dashboard-design.widgets.approvalCenter.more') }}
        <ChevronRight class="h-3.5 w-3.5" />
      </button>
    </div>
    <!-- 菜单网格 -->
    <div class="flex flex-1 items-center justify-around gap-2">
      <div
        v-for="item in menuItems"
        :key="item.key"
        class="flex cursor-pointer flex-col items-center gap-2 transition-transform hover:scale-105"
        @click="handleClick(item)"
      >
        <div
          class="flex h-11 w-11 items-center justify-center rounded-full"
          :style="{ backgroundColor: item.color }"
        >
          <component :is="item.icon" class="h-5 w-5 text-white" />
        </div>
        <span class="text-muted-foreground whitespace-nowrap text-xs">{{
          item.title
        }}</span>
      </div>
    </div>
  </div>
</template>
