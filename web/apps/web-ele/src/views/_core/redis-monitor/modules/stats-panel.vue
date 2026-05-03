<script setup lang="ts">
import type {
  RedisMonitorOverview,
  RedisRealtimeStats,
} from '#/api/core/redis-monitor';

import { computed } from 'vue';

import { Activity, BarChart, Network, TrendingUp, Zap } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElProgress,
  ElTag,
} from 'element-plus';

defineOptions({ name: 'StatsPanel' });

const props = defineProps<{
  monitorData: null | RedisMonitorOverview;
  realtimeData: null | RedisRealtimeStats;
}>();

// 统计信息
const stats = computed(() => props.monitorData?.stats);

// 命中率
const hitRate = computed(() => {
  if (!stats.value) return 0;
  const hits = stats.value.keyspace_hits || 0;
  const misses = stats.value.keyspace_misses || 0;
  const total = hits + misses;
  return total > 0 ? (hits / total) * 100 : 0;
});

// 格式化字节大小
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(2)} ${sizes[i]}`;
}

// 格式化大数字
function formatNumber(num: number): string {
  if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(2)}B`;
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(2)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
  return num.toString();
}

// 获取命中率颜色
function getHitRateColor(rate: number): 'danger' | 'success' | 'warning' {
  if (rate >= 90) return 'success';
  if (rate >= 70) return 'warning';
  return 'danger';
}

// 获取性能状态
function getPerformanceStatus(opsPerSec: number): {
  text: string;
  type: 'danger' | 'info' | 'success' | 'warning';
} {
  if (opsPerSec >= 10_000)
    return { text: $t('redis-monitor.excellent'), type: 'success' };
  if (opsPerSec >= 5000)
    return { text: $t('redis-monitor.good'), type: 'success' };
  if (opsPerSec >= 1000)
    return { text: $t('redis-monitor.normal'), type: 'info' };
  if (opsPerSec >= 100)
    return { text: $t('redis-monitor.lower'), type: 'warning' };
  return { text: $t('redis-monitor.veryLow'), type: 'danger' };
}
</script>

<template>
  <div class="space-y-4">
    <!-- 关键性能指标 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <!-- 每秒操作数 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.opsPerSec') }}
            </div>
            <div class="text-3xl font-bold">
              {{ formatNumber(stats?.instantaneous_ops_per_sec || 0) }}
            </div>
            <div class="mt-2">
              <ElTag
                :type="
                  getPerformanceStatus(stats?.instantaneous_ops_per_sec || 0)
                    .type
                "
                size="small"
              >
                {{
                  getPerformanceStatus(stats?.instantaneous_ops_per_sec || 0)
                    .text
                }}
              </ElTag>
            </div>
          </div>
          <div class="rounded-lg bg-blue-100 p-3 dark:bg-blue-900/30">
            <Zap :size="32" class="text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </ElCard>

      <!-- 命中率 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.cacheHitRate') }}
            </div>
            <div class="text-3xl font-bold">{{ hitRate.toFixed(2) }}%</div>
            <div class="mt-2">
              <ElProgress
                :percentage="hitRate"
                :color="getHitRateColor(hitRate)"
                :show-text="false"
              />
            </div>
          </div>
          <div class="rounded-lg bg-green-100 p-3 dark:bg-green-900/30">
            <TrendingUp :size="32" class="text-green-600 dark:text-green-400" />
          </div>
        </div>
      </ElCard>

      <!-- 总命令数 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.totalCommands') }}
            </div>
            <div class="text-3xl font-bold">
              {{ formatNumber(stats?.total_commands_processed || 0) }}
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ (stats?.total_commands_processed || 0).toLocaleString() }}
            </div>
          </div>
          <div class="rounded-lg bg-purple-100 p-3 dark:bg-purple-900/30">
            <Activity :size="32" class="text-purple-600 dark:text-purple-400" />
          </div>
        </div>
      </ElCard>

      <!-- 总连接数 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.totalConnections') }}
            </div>
            <div class="text-3xl font-bold">
              {{ formatNumber(stats?.total_connections_received || 0) }}
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ (stats?.total_connections_received || 0).toLocaleString() }}
            </div>
          </div>
          <div class="rounded-lg bg-orange-100 p-3 dark:bg-orange-900/30">
            <Network :size="32" class="text-orange-600 dark:text-orange-400" />
          </div>
        </div>
      </ElCard>
    </div>

    <!-- 详细统计信息 -->
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <!-- 命令统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Activity :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.commandStats')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('redis-monitor.totalCommands')">
            <span class="font-mono">{{
              (stats?.total_commands_processed || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.opsPerSec')">
            <div class="flex items-center gap-2">
              <span class="font-mono font-semibold">{{
                stats?.instantaneous_ops_per_sec || 0
              }}</span>
              <ElTag
                :type="
                  getPerformanceStatus(stats?.instantaneous_ops_per_sec || 0)
                    .type
                "
                size="small"
              >
                {{
                  getPerformanceStatus(stats?.instantaneous_ops_per_sec || 0)
                    .text
                }}
              </ElTag>
            </div>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.keyspaceHits')">
            <span class="font-mono text-green-600">{{
              (stats?.keyspace_hits || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.keyspaceMisses')">
            <span class="font-mono text-red-600">{{
              (stats?.keyspace_misses || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.hitRate')">
            <div class="flex items-center gap-2">
              <ElProgress
                :percentage="hitRate"
                :color="getHitRateColor(hitRate)"
                class="flex-1"
              />
              <span class="font-semibold">{{ hitRate.toFixed(2) }}%</span>
            </div>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 连接统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Network :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.connectionStats')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('redis-monitor.totalConnections')">
            <span class="font-mono">{{
              (stats?.total_connections_received || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.rejectedConnections')">
            <span
              class="font-mono"
              :class="
                (stats?.rejected_connections || 0) > 0 ? 'text-red-600' : ''
              "
            >
              {{ (stats?.rejected_connections || 0).toLocaleString() }}
            </span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.totalInputTraffic')">
            <span class="font-mono">{{
              formatBytes(stats?.total_net_input_bytes || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.totalOutputTraffic')">
            <span class="font-mono">{{
              formatBytes(stats?.total_net_output_bytes || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem
            :label="$t('redis-monitor.instantaneousInputRate')"
          >
            <span class="font-mono"
              >{{
                (stats?.instantaneous_input_kbps || 0).toFixed(2)
              }}
              KB/s</span
            >
          </ElDescriptionsItem>
          <ElDescriptionsItem
            :label="$t('redis-monitor.instantaneousOutputRate')"
          >
            <span class="font-mono"
              >{{
                (stats?.instantaneous_output_kbps || 0).toFixed(2)
              }}
              KB/s</span
            >
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 键操作统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <BarChart :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.keyOperationStats')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('redis-monitor.expiresKeys')">
            <span class="font-mono">{{
              (stats?.expired_keys || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.evictedKeys')">
            <span
              class="font-mono"
              :class="(stats?.evicted_keys || 0) > 0 ? 'text-orange-600' : ''"
            >
              {{ (stats?.evicted_keys || 0).toLocaleString() }}
            </span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.keyspaceHits')">
            <span class="font-mono text-green-600">{{
              (stats?.keyspace_hits || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.keyspaceMisses')">
            <span class="font-mono text-red-600">{{
              (stats?.keyspace_misses || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 同步统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Activity :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.syncStats')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('redis-monitor.syncFull')">
            <span class="font-mono">{{
              (stats?.sync_full || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.syncPartialOk')">
            <span class="font-mono text-green-600">{{
              (stats?.sync_partial_ok || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.syncPartialErr')">
            <span
              class="font-mono"
              :class="(stats?.sync_partial_err || 0) > 0 ? 'text-red-600' : ''"
            >
              {{ (stats?.sync_partial_err || 0).toLocaleString() }}
            </span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.pubsubChannels')">
            <span class="font-mono">{{
              (stats?.pubsub_channels || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.pubsubPatterns')">
            <span class="font-mono">{{
              (stats?.pubsub_patterns || 0).toLocaleString()
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('redis-monitor.latestForkUsec')">
            <span class="font-mono"
              >{{ (stats?.latest_fork_usec || 0).toLocaleString() }} μs</span
            >
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </div>

    <!-- 统计说明 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Activity :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('redis-monitor.indicatorDesc')
          }}</span>
        </div>
      </template>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.opsPerSec') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.opsPerSecDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.hitRate') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.hitRateDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.evictedKeys') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.evictedKeysDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.rejectedConnections') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.rejectedConnectionsDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.syncFull') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.syncFullDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.latestForkUsec') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.latestForkUsecDesc') }}
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>
