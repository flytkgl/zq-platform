<script setup lang="ts">
import type {
  DatabaseMonitorOverview,
  DatabaseRealtimeStats,
} from '#/api/core/database-monitor';

import { computed } from 'vue';

import { Activity, HardDrive, Network, Server } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElProgress,
  ElTag,
} from 'element-plus';

defineOptions({ name: 'OverviewPanel' });

const props = defineProps<{
  monitorData: DatabaseMonitorOverview | null;
  realtimeData: DatabaseRealtimeStats | null;
}>();

// 基本信息
const basicInfo = computed(() => props.monitorData?.basic_info);

// 连接信息
const connectionInfo = computed(() => props.monitorData?.connection_info);

// 数据库大小
const databaseSize = computed(() => props.monitorData?.database_size);

// 性能统计
const performanceStats = computed(() => props.monitorData?.performance_stats);

// 连接使用率
const connectionUsagePercent = computed(() => {
  return props.realtimeData?.connection_usage_percent || 0;
});

// 缓存命中率
const cacheHitRatio = computed(() => {
  return props.realtimeData?.cache_hit_ratio || 0;
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

// 获取百分比颜色
function getPercentColor(percent: number): string {
  if (percent >= 90) return '#f56c6c';
  if (percent >= 70) return '#e6a23c';
  return '#67c23a';
}

// 获取数据库类型标签颜色
function getDbTypeColor(
  dbType: string,
): 'danger' | 'info' | 'success' | 'warning' {
  const type = dbType.toUpperCase();
  if (type === 'POSTGRESQL') return 'success';
  if (type === 'MYSQL') return 'info';
  if (type === 'SQLSERVER') return 'warning';
  return 'info';
}
</script>

<template>
  <div class="space-y-4">
    <!-- 关键指标卡片 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <!-- 连接使用率 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
              <Network :size="20" class="text-blue-600 dark:text-blue-400" />
            </div>
            <span
              class="text-sm font-medium text-gray-600 dark:text-gray-400"
              >{{ $t('database-monitor.connectionUsageRate') }}</span
            >
          </div>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ connectionUsagePercent.toFixed(1) }}%
        </div>
        <ElProgress
          :percentage="Number(connectionUsagePercent.toFixed(1))"
          :color="getPercentColor(connectionUsagePercent)"
          :stroke-width="8"
        />
      </ElCard>

      <!-- 数据库大小 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
            <HardDrive
              :size="20"
              class="text-purple-600 dark:text-purple-400"
            />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('database-monitor.databaseSize')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ databaseSize?.database_size_gb.toFixed(2) || 0 }} GB
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ databaseSize?.database_size_mb.toFixed(2) || 0 }} MB
        </div>
      </ElCard>

      <!-- 缓存命中率 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
            <Activity :size="20" class="text-green-600 dark:text-green-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('database-monitor.cacheHitRatio')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ cacheHitRatio.toFixed(2) }}%
        </div>
        <ElProgress
          :percentage="Number(cacheHitRatio.toFixed(1))"
          :color="getPercentColor(100 - cacheHitRatio)"
          :stroke-width="8"
        />
      </ElCard>

      <!-- 活动连接数 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-orange-100 p-2 dark:bg-orange-900/30">
            <Network :size="20" class="text-orange-600 dark:text-orange-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('database-monitor.activeConnections')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ realtimeData?.active_connections || 0 }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('database-monitor.currentActiveConnections') }}
        </div>
      </ElCard>
    </div>

    <!-- 详细信息 -->
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <!-- 基本信息 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Server :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('database-monitor.basicInfo')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('database-monitor.databaseType')">
            <ElTag :type="getDbTypeColor(basicInfo?.db_type || '')">
              {{ basicInfo?.db_type || '-' }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.hostAddress')">
            {{ basicInfo?.host || '-' }}:{{ basicInfo?.port || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.databaseName')">
            {{ basicInfo?.database || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.version')">
            {{ basicInfo?.version || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.uptime')">
            {{ basicInfo?.uptime || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.timezone')">
            {{ basicInfo?.timezone || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.charset')">
            {{ basicInfo?.charset || '-' }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 连接信息 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Network :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('database-monitor.connectionInfo')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('database-monitor.totalConnections')">
            {{ connectionInfo?.total_connections || 0 }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.maxConnections')">
            {{ connectionInfo?.max_connections || 0 }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.activeConnections')">
            <span class="font-semibold text-green-600">
              {{ connectionInfo?.active_connections || 0 }}
            </span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.idleConnections')">
            <span class="text-gray-600">
              {{ connectionInfo?.idle_connections || 0 }}
            </span>
          </ElDescriptionsItem>
          <ElDescriptionsItem
            :label="$t('database-monitor.connectionUsageRate')"
          >
            <div class="flex items-center gap-2">
              <ElProgress
                :percentage="
                  Number(
                    connectionInfo?.connection_usage_percent?.toFixed(1) || 0,
                  )
                "
                :color="
                  getPercentColor(connectionInfo?.connection_usage_percent || 0)
                "
                class="flex-1"
              />
              <span class="font-semibold">
                {{ connectionInfo?.connection_usage_percent?.toFixed(1) || 0 }}%
              </span>
            </div>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 数据库大小 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <HardDrive :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('database-monitor.storageInfo')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('database-monitor.databaseSizeGb')">
            <span class="font-mono font-semibold">
              {{ databaseSize?.database_size_gb.toFixed(2) || 0 }} GB
            </span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.databaseSizeMb')">
            <span class="font-mono">
              {{ databaseSize?.database_size_mb.toFixed(2) || 0 }} MB
            </span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.databaseSizeBytes')">
            <span class="font-mono text-sm">
              {{ formatBytes(databaseSize?.database_size_bytes || 0) }}
            </span>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 性能统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Activity :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('database-monitor.performanceStats')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('database-monitor.cacheHitRatio')">
            <div class="flex items-center gap-2">
              <ElProgress
                :percentage="
                  Number(performanceStats?.cache_hit_ratio?.toFixed(1) || 0)
                "
                :color="
                  getPercentColor(
                    100 - (performanceStats?.cache_hit_ratio || 0),
                  )
                "
                class="flex-1"
              />
              <span class="font-semibold">
                {{ performanceStats?.cache_hit_ratio?.toFixed(2) || 0 }}%
              </span>
            </div>
          </ElDescriptionsItem>

          <!-- PostgreSQL 特有指标 -->
          <template v-if="basicInfo?.db_type === 'POSTGRESQL'">
            <ElDescriptionsItem
              :label="$t('database-monitor.transactionsCommit')"
            >
              {{ formatNumber(performanceStats?.transactions_commit || 0) }}
            </ElDescriptionsItem>
            <ElDescriptionsItem
              :label="$t('database-monitor.transactionsRollback')"
            >
              {{ formatNumber(performanceStats?.transactions_rollback || 0) }}
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="$t('database-monitor.tuplesReturned')">
              {{ formatNumber(performanceStats?.tuples_returned || 0) }}
            </ElDescriptionsItem>
          </template>

          <!-- MySQL 特有指标 -->
          <template v-if="basicInfo?.db_type === 'MYSQL'">
            <ElDescriptionsItem :label="$t('database-monitor.totalQueries')">
              {{ formatNumber(performanceStats?.total_queries || 0) }}
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="$t('database-monitor.slowQueries')">
              <span
                :class="
                  (performanceStats?.slow_queries || 0) > 0
                    ? 'text-red-600'
                    : ''
                "
              >
                {{ formatNumber(performanceStats?.slow_queries || 0) }}
              </span>
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="$t('database-monitor.bytesReceived')">
              {{ formatBytes(performanceStats?.bytes_received || 0) }}
            </ElDescriptionsItem>
          </template>

          <!-- SQL Server 特有指标 -->
          <template v-if="basicInfo?.db_type === 'SQLSERVER'">
            <ElDescriptionsItem
              :label="$t('database-monitor.batchRequestsPerSec')"
            >
              {{ performanceStats?.batch_requests_per_sec || 0 }}
            </ElDescriptionsItem>
            <ElDescriptionsItem
              :label="$t('database-monitor.pageLifeExpectancy')"
            >
              {{ performanceStats?.page_life_expectancy || 0 }}
            </ElDescriptionsItem>
            <ElDescriptionsItem
              :label="$t('database-monitor.bufferCacheHitRatio')"
            >
              {{ performanceStats?.buffer_cache_hit_ratio?.toFixed(2) || 0 }}%
            </ElDescriptionsItem>
          </template>
        </ElDescriptions>
      </ElCard>
    </div>
  </div>
</template>
