<script setup lang="ts">
import type { DashboardWidget } from '#/components/dashboard-design';
import type { ApplicationListItem } from '#/api/core/application';

import { computed, onMounted, ref } from 'vue';

import { AppWindow, ChevronRight, IconifyIcon } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElEmpty, ElScrollbar } from 'element-plus';

import { getApplicationListApi } from '#/api/core/application';

const props = defineProps<{
  widget: DashboardWidget;
}>();

// 应用列表
const appList = ref<ApplicationListItem[]>([]);
const loading = ref(false);

// 最大显示数量
const maxCount = computed(() => props.widget.props.maxCount || 8);

// 显示的应用列表
const displayApps = computed(() => appList.value.slice(0, maxCount.value));

// 加载已发布的应用列表
const loadApps = async () => {
  loading.value = true;
  try {
    const res = await getApplicationListApi({
      page: 1,
      pageSize: 100,
      status: 'published',
    });
    appList.value = res.items || [];
  } catch (error) {
    console.error('Failed to load applications:', error);
  } finally {
    loading.value = false;
  }
};

// 点击应用
const handleClick = (app: ApplicationListItem) => {
  window.open(`${window.location.origin}/app/${app.code}`, '_blank');
};

// 点击更多
const handleMore = () => {
  window.open(`${window.location.origin}/application`, '_blank');
};

onMounted(() => {
  loadApps();
});
</script>

<template>
  <div class="my-apps flex h-full flex-col p-4" v-loading="loading">
    <!-- 头部 -->
    <div class="mb-4 flex items-center justify-between">
      <span class="text-sm font-medium">{{ widget.props.title }}</span>
      <button
        v-if="widget.props.showMore"
        type="button"
        class="text-muted-foreground hover:text-primary flex items-center gap-0.5 text-xs transition-colors"
        @click="handleMore"
      >
        {{ $t('dashboard-design.widgets.myApps.more') }}
        <ChevronRight class="h-3.5 w-3.5" />
      </button>
    </div>
    <!-- 应用网格 -->
    <ElScrollbar class="flex-1">
      <div
        v-if="displayApps.length > 0"
        class="flex flex-wrap gap-4"
      >
        <div
          v-for="app in displayApps"
          :key="app.id"
          class="flex cursor-pointer flex-col items-center gap-2 transition-transform hover:scale-105 m-4"
          style="width: 72px"
          @click="handleClick(app)"
        >
          <div
            class="flex h-12 w-12 items-center justify-center rounded-xl"
            style="background: linear-gradient(135deg, var(--el-color-primary-light-3), var(--el-color-primary))"
          >
            <IconifyIcon
              v-if="app.icon"
              :icon="app.icon"
              class="h-6 w-6 text-white"
            />
            <AppWindow v-else class="h-6 w-6 text-white" />
          </div>
          <span class="text-muted-foreground w-full truncate text-center text-xs">{{ app.name }}</span>
        </div>
      </div>
      <ElEmpty
        v-else-if="!loading"
        :description="$t('dashboard-design.widgets.myApps.noData')"
        :image-size="60"
      />
    </ElScrollbar>
  </div>
</template>
