<script setup lang="ts">
import type {
  RealtimeStats as RealtimeStatsType,
  ServerMonitorResponse,
} from '#/api/core/server-monitor';
import type { CardListItem, CardListOptions } from '#/components/card-list';

import { computed, onMounted, onUnmounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';

import { Page } from '@vben/common-ui';
import {
  Cpu,
  Database,
  HardDrive,
  LayoutDashboard,
  ListTree,
  Network,
} from '@vben/icons';
import { $t } from '@vben/locales';

import { ElCard, ElMessage, ElScrollbar, ElTag } from 'element-plus';

import {
  getRealtimeStatsApi,
  getServerOverviewApi,
} from '#/api/core/server-monitor';
import { CardList } from '#/components/card-list';

import CpuPanel from './modules/cpu-panel.vue';
import DashboardPanel from './modules/dashboard-panel.vue';
import DiskPanel from './modules/disk-panel.vue';
import MemoryPanel from './modules/memory-panel.vue';
import NetworkPanel from './modules/network-panel.vue';
import ProcessPanel from './modules/process-panel.vue';

defineOptions({ name: 'ServerMonitor' });

// 菜单项类型
interface MonitorMenuItem extends CardListItem {
  id: string;
  name: string;
  key: 'cpu' | 'dashboard' | 'disk' | 'memory' | 'network' | 'process';
  icon?: string;
}

// 菜单项数据
const menuItems = ref<MonitorMenuItem[]>([
  { id: 'dashboard', name: $t('server-monitor.systemInfo'), key: 'dashboard' },
  { id: 'cpu', name: $t('server-monitor.cpuInfo'), key: 'cpu' },
  { id: 'memory', name: $t('server-monitor.memoryInfo'), key: 'memory' },
  { id: 'disk', name: $t('server-monitor.diskInfo'), key: 'disk' },
  { id: 'network', name: $t('server-monitor.networkInfo'), key: 'network' },
  { id: 'process', name: $t('server-monitor.processInfo'), key: 'process' },
]);

// 图标映射
const iconMap: Record<string, any> = {
  dashboard: LayoutDashboard,
  cpu: Cpu,
  memory: Database,
  disk: HardDrive,
  network: Network,
  process: ListTree,
};

const selectedMenuId = ref<string>('dashboard');

// CardList 配置
const cardListOptions: CardListOptions<MonitorMenuItem> = {
  searchFields: [{ field: 'name' }],
  titleField: 'name',
  displayMode: 'center',
};

const loading = ref(false);
const autoRefresh = ref(true);
const refreshInterval = ref(3000); // 3秒刷新一次
let timer: NodeJS.Timeout | null = null;

// 服务器监控数据
const serverData = ref<null | ServerMonitorResponse>(null);
const realtimeData = ref<null | RealtimeStatsType>(null);

// 加载服务器概览数据
async function loadOverview(showLoading = false) {
  try {
    if (showLoading) {
      loading.value = true;
    }
    const data = await getServerOverviewApi();
    serverData.value = data;
  } catch (error: any) {
    ElMessage.error(error.message || $t('server-monitor.loadFailed'));
  } finally {
    if (showLoading) {
      loading.value = false;
    }
  }
}

// 加载实时统计数据
async function loadRealtimeStats(showLoading = false) {
  try {
    const data = await getRealtimeStatsApi();
    realtimeData.value = data;
  } catch (error: any) {
    console.error('加载实时统计数据失败:', error);
  }
}

// 手动刷新
async function handleRefresh() {
  await Promise.all([loadOverview(), loadRealtimeStats()]);
  ElMessage.success($t('server-monitor.refreshSuccess'));
}

// 自动刷新切换
function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value;
  if (autoRefresh.value) {
    startAutoRefresh();
    ElMessage.success($t('server-monitor.autoRefreshOn'));
  } else {
    stopAutoRefresh();
    ElMessage.info($t('server-monitor.autoRefreshOff'));
  }
}

// 处理菜单选择
function handleMenuSelect(id: string | undefined) {
  selectedMenuId.value = id || 'overview';
}

// 开始自动刷新
function startAutoRefresh() {
  if (timer) return;
  timer = setInterval(async () => {
    if (autoRefresh.value) {
      await loadRealtimeStats();
    }
  }, refreshInterval.value);
}

// 停止自动刷新
function stopAutoRefresh() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}

// 获取当前选中菜单的标题
const currentTitle = computed(() => {
  const item = menuItems.value.find((m) => m.id === selectedMenuId.value);
  return item ? item.name : $t('server-monitor.serverMonitor');
});

// 获取当前图标组件
const currentIcon = computed(() => {
  return iconMap[selectedMenuId.value] || LayoutDashboard;
});

onMounted(async () => {
  // 第一次加载显示loading
  await loadOverview(true);
  await loadRealtimeStats();
  startAutoRefresh();
});

onUnmounted(() => {
  stopAutoRefresh();
});

// 路由离开时停止轮询
onBeforeRouteLeave(() => {
  stopAutoRefresh();
  return true;
});
</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full">
      <!-- 左侧菜单 -->
      <div class="w-1/6 flex-shrink-0">
        <CardList
          :items="menuItems"
          :selected-id="selectedMenuId"
          :options="cardListOptions"
          :loading="false"
          class="server-monitor-menu"
          @select="handleMenuSelect"
        >
          <template #item="{ item }">
            <div class="flex items-center gap-2">
              <component :is="iconMap[item.id]" :size="16" />
              <span class="text-sm font-medium">{{ item.name }}</span>
            </div>
          </template>
        </CardList>
      </div>

      <!-- 右侧内容 -->
      <div class="flex-1">
        <ElCard
          v-if="selectedMenuId === 'dashboard'"
          class="flex h-full flex-col"
          style="border: none"
          shadow="never"
          :body-style="{
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            minHeight: 0,
            padding: 0,
            overflow: 'hidden',
          }"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <component :is="currentIcon" :size="20" class="text-primary" />
                <span class="font-semibold">{{ currentTitle }}</span>
              </div>
              <div class="flex items-center gap-2">
                <ElTag :type="autoRefresh ? 'success' : 'info'" size="small">
                  {{
                    autoRefresh
                      ? $t('server-monitor.autoRefreshing')
                      : $t('server-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar v-loading="loading" class="dashboard-scrollbar">
            <div class="p-4">
              <DashboardPanel
                :server-data="serverData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- CPU信息 -->
        <ElCard
          v-else-if="selectedMenuId === 'cpu'"
          class="flex h-full flex-col"
          style="border: none"
          shadow="never"
          :body-style="{
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            minHeight: 0,
            padding: 0,
            overflow: 'hidden',
          }"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <component :is="currentIcon" :size="20" class="text-primary" />
                <span class="font-semibold">{{ currentTitle }}</span>
              </div>
              <div class="flex items-center gap-2">
                <ElTag :type="autoRefresh ? 'success' : 'info'" size="small">
                  {{
                    autoRefresh
                      ? $t('server-monitor.autoRefreshing')
                      : $t('server-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar v-loading="loading" class="dashboard-scrollbar">
            <div class="p-4">
              <CpuPanel
                :server-data="serverData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- 内存信息 -->
        <ElCard
          v-else-if="selectedMenuId === 'memory'"
          class="flex h-full flex-col"
          style="border: none"
          shadow="never"
          :body-style="{
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            minHeight: 0,
            padding: 0,
            overflow: 'hidden',
          }"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <component :is="currentIcon" :size="20" class="text-primary" />
                <span class="font-semibold">{{ currentTitle }}</span>
              </div>
              <div class="flex items-center gap-2">
                <ElTag :type="autoRefresh ? 'success' : 'info'" size="small">
                  {{
                    autoRefresh
                      ? $t('server-monitor.autoRefreshing')
                      : $t('server-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar v-loading="loading" class="dashboard-scrollbar">
            <div class="p-4">
              <MemoryPanel
                :server-data="serverData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- 磁盘信息 -->
        <ElCard
          v-else-if="selectedMenuId === 'disk'"
          class="flex h-full flex-col"
          style="border: none"
          shadow="never"
          :body-style="{
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            minHeight: 0,
            padding: 0,
            overflow: 'hidden',
          }"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <component :is="currentIcon" :size="20" class="text-primary" />
                <span class="font-semibold">{{ currentTitle }}</span>
              </div>
              <div class="flex items-center gap-2">
                <ElTag :type="autoRefresh ? 'success' : 'info'" size="small">
                  {{
                    autoRefresh
                      ? $t('server-monitor.autoRefreshing')
                      : $t('server-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar v-loading="loading" class="dashboard-scrollbar">
            <div class="p-4">
              <DiskPanel
                :server-data="serverData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- 网络信息 -->
        <ElCard
          v-else-if="selectedMenuId === 'network'"
          class="flex h-full flex-col"
          style="border: none"
          shadow="never"
          :body-style="{
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            minHeight: 0,
            padding: 0,
            overflow: 'hidden',
          }"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <component :is="currentIcon" :size="20" class="text-primary" />
                <span class="font-semibold">{{ currentTitle }}</span>
              </div>
              <div class="flex items-center gap-2">
                <ElTag :type="autoRefresh ? 'success' : 'info'" size="small">
                  {{
                    autoRefresh
                      ? $t('server-monitor.autoRefreshing')
                      : $t('server-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar v-loading="loading" class="dashboard-scrollbar">
            <div class="p-4">
              <NetworkPanel
                :server-data="serverData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- 进程信息 -->
        <ElCard
          v-else-if="selectedMenuId === 'process'"
          class="flex h-full flex-col"
          style="border: none"
          shadow="never"
          :body-style="{
            display: 'flex',
            flexDirection: 'column',
            flex: 1,
            minHeight: 0,
            padding: 0,
            overflow: 'hidden',
          }"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <component :is="currentIcon" :size="20" class="text-primary" />
                <span class="font-semibold">{{ currentTitle }}</span>
              </div>
              <div class="flex items-center gap-2">
                <ElTag :type="autoRefresh ? 'success' : 'info'" size="small">
                  {{
                    autoRefresh
                      ? $t('server-monitor.autoRefreshing')
                      : $t('server-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar v-loading="loading" class="dashboard-scrollbar">
            <div class="p-4">
              <ProcessPanel
                :server-data="serverData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- 其他菜单内容占位 -->
        <ElCard v-else class="h-full">
          <div class="flex h-full items-center justify-center text-gray-400">
            <div class="text-center">
              <component :is="currentIcon" :size="48" class="mx-auto mb-4" />
              <p class="text-lg">{{ currentTitle }}</p>
              <p class="mt-2 text-sm">
                {{ $t('server-monitor.featureDeveloping') }}
              </p>
            </div>
          </div>
        </ElCard>
      </div>
    </div>
  </Page>
</template>
