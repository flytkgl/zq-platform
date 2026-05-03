<script setup lang="ts">
import type {
  RedisMonitorOverview,
  RedisRealtimeStats,
} from '#/api/core/redis-monitor';
import type { CardListItem, CardListOptions } from '#/components/card-list';

import { computed, onMounted, onUnmounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';

import { Page } from '@vben/common-ui';
import {
  BarChart,
  Database,
  Key,
  LayoutDashboard,
  Timer,
  Users,
} from '@vben/icons';
import { $t } from '@vben/locales';

import { ElCard, ElMessage, ElScrollbar, ElTag } from 'element-plus';

import {
  getRedisMonitorOverviewApi,
  getRedisRealtimeStatsApi,
} from '#/api/core/redis-monitor';
import { CardList } from '#/components/card-list';

import ClientsPanel from './modules/clients-panel.vue';
import KeyspacePanel from './modules/keyspace-panel.vue';
import MemoryPanel from './modules/memory-panel.vue';
import OverviewPanel from './modules/overview-panel.vue';
import SlowlogPanel from './modules/slowlog-panel.vue';
import StatsPanel from './modules/stats-panel.vue';

defineOptions({ name: 'RedisMonitor' });

// 菜单项类型
interface MonitorMenuItem extends CardListItem {
  id: string;
  name: string;
  key: 'clients' | 'keyspace' | 'memory' | 'overview' | 'slowlog' | 'stats';
  icon?: string;
}

// 菜单项数据
const menuItems = ref<MonitorMenuItem[]>([
  { id: 'overview', name: $t('redis-monitor.overview'), key: 'overview' },
  { id: 'memory', name: $t('redis-monitor.memory'), key: 'memory' },
  { id: 'clients', name: $t('redis-monitor.clients'), key: 'clients' },
  { id: 'keyspace', name: $t('redis-monitor.keyspace'), key: 'keyspace' },
  { id: 'stats', name: $t('redis-monitor.stats'), key: 'stats' },
  { id: 'slowlog', name: $t('redis-monitor.slowlog'), key: 'slowlog' },
]);

// 图标映射
const iconMap: Record<string, any> = {
  overview: LayoutDashboard,
  memory: Database,
  clients: Users,
  keyspace: Key,
  stats: BarChart,
  slowlog: Timer,
};

const selectedMenuId = ref<string>('overview');

// CardList 配置
const cardListOptions: CardListOptions<MonitorMenuItem> = {
  searchFields: [{ field: 'name' }],
  displayMode: 'center',
  titleField: 'name',
};

// 当前标题和图标
const currentTitle = computed(() => {
  const item = menuItems.value.find((m) => m.id === selectedMenuId.value);
  return item?.name || '';
});

const currentIcon = computed(() => {
  return iconMap[selectedMenuId.value];
});

// 菜单选择处理
function handleMenuSelect(id: string | undefined) {
  if (id) {
    selectedMenuId.value = id;
  }
}

// 监控数据
const monitorData = ref<null | RedisMonitorOverview>(null);
const realtimeData = ref<null | RedisRealtimeStats>(null);

// 自动刷新
const autoRefresh = ref(true);
const refreshInterval = ref<null | number>(null);
const REFRESH_INTERVAL = 3000; // 5秒

// 加载监控数据
async function loadMonitorData() {
  try {
    const response = await getRedisMonitorOverviewApi();
    monitorData.value = response;
  } catch (error) {
    ElMessage.error($t('redis-monitor.loadFailed'));
    console.error(error);
  }
}

// 加载实时统计
async function loadRealtimeStats() {
  try {
    const response = await getRedisRealtimeStatsApi();
    realtimeData.value = response;
  } catch (error) {
    console.error($t('redis-monitor.loadRealtimeStatsFailed'), error);
  }
}

// 手动刷新
async function handleRefresh() {
  await loadMonitorData();
  await loadRealtimeStats();
  ElMessage.success($t('redis-monitor.refreshSuccess'));
}

// 切换自动刷新
function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value;
  if (autoRefresh.value) {
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
}

// 开始自动刷新
function startAutoRefresh() {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value);
  }
  refreshInterval.value = window.setInterval(async () => {
    await loadRealtimeStats();
  }, REFRESH_INTERVAL);
}

// 停止自动刷新
function stopAutoRefresh() {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value);
    refreshInterval.value = null;
  }
}

onMounted(async () => {
  await loadMonitorData();
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
    <!-- 主内容区域 -->
    <div class="flex h-full">
      <!-- 左侧菜单 -->
      <div class="w-1/6 flex-shrink-0">
        <CardList
          :items="menuItems"
          :selected-id="selectedMenuId"
          :options="cardListOptions"
          :loading="false"
          class="redis-monitor-menu"
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
        <!-- 概览信息 -->
        <ElCard
          v-if="selectedMenuId === 'overview'"
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
                <ElTag :type="autoRefresh ? 'success' : 'info'">
                  {{
                    autoRefresh
                      ? $t('redis-monitor.autoRefreshing')
                      : $t('redis-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar class="monitor-scrollbar">
            <div class="p-4">
              <OverviewPanel
                :monitor-data="monitorData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- 内存信息 -->
        <ElCard
          v-else-if="selectedMenuId === 'memory'"
          class="flex h-full flex-col"
          shadow="never"
          style="border: none"
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
                <ElTag :type="autoRefresh ? 'success' : 'info'">
                  {{
                    autoRefresh
                      ? $t('redis-monitor.autoRefreshing')
                      : $t('redis-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar class="monitor-scrollbar">
            <div class="p-4">
              <MemoryPanel
                :monitor-data="monitorData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- 客户端信息 -->
        <ElCard
          v-else-if="selectedMenuId === 'clients'"
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
                <ElTag :type="autoRefresh ? 'success' : 'info'">
                  {{
                    autoRefresh
                      ? $t('redis-monitor.autoRefreshing')
                      : $t('redis-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar class="monitor-scrollbar">
            <div class="p-4">
              <ClientsPanel
                :monitor-data="monitorData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- 键空间信息 -->
        <ElCard
          v-else-if="selectedMenuId === 'keyspace'"
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
                <ElTag :type="autoRefresh ? 'success' : 'info'">
                  {{
                    autoRefresh
                      ? $t('redis-monitor.autoRefreshing')
                      : $t('redis-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar class="monitor-scrollbar">
            <div class="p-4">
              <KeyspacePanel
                :monitor-data="monitorData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- 统计信息 -->
        <ElCard
          v-else-if="selectedMenuId === 'stats'"
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
                <ElTag :type="autoRefresh ? 'success' : 'info'">
                  {{
                    autoRefresh
                      ? $t('redis-monitor.autoRefreshing')
                      : $t('redis-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar class="monitor-scrollbar">
            <div class="p-4">
              <StatsPanel
                :monitor-data="monitorData"
                :realtime-data="realtimeData"
              />
            </div>
          </ElScrollbar>
        </ElCard>

        <!-- 慢日志 -->
        <ElCard
          v-else-if="selectedMenuId === 'slowlog'"
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
                <ElTag :type="autoRefresh ? 'success' : 'info'">
                  {{
                    autoRefresh
                      ? $t('redis-monitor.autoRefreshing')
                      : $t('redis-monitor.paused')
                  }}
                </ElTag>
              </div>
            </div>
          </template>

          <ElScrollbar class="monitor-scrollbar">
            <div class="p-4">
              <SlowlogPanel
                :monitor-data="monitorData"
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
                {{ $t('redis-monitor.featureDeveloping') }}
              </p>
            </div>
          </div>
        </ElCard>
      </div>
    </div>
  </Page>
</template>

<style scoped>
.monitor-scrollbar {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
