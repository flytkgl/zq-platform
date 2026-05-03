<script setup lang="ts">
import type {
  DatabaseMonitorOverview,
  DatabaseRealtimeStats,
} from '#/api/core/database-monitor';

import { computed } from 'vue';

import { Activity, BarChart, TrendingUp, Zap } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElProgress,
  ElTag,
} from 'element-plus';

defineOptions({ name: 'PerformancePanel' });

const props = defineProps<{
  monitorData: DatabaseMonitorOverview | null;
  realtimeData: DatabaseRealtimeStats | null;
}>();

// 基本信息
const basicInfo = computed(() => props.monitorData?.basic_info);

// 性能统计
const performanceStats = computed(() => props.monitorData?.performance_stats);

// 缓存命中率
const cacheHitRatio = computed(() => {
  return props.realtimeData?.cache_hit_ratio || 0;
});

// 格式化大数字
function formatNumber(num: number): string {
  if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(2)}B`;
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(2)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
  return num.toString();
}

// 格式化字节
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(2)} ${sizes[i]}`;
}

// 获取百分比颜色
function getPercentColor(percent: number): string {
  if (percent >= 90) return '#67c23a';
  if (percent >= 70) return '#e6a23c';
  return '#f56c6c';
}

// 获取数据库类型
const dbType = computed(() => basicInfo.value?.db_type || '');
</script>

<template>
  <div class="space-y-4">
    <!-- 核心性能指标 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <!-- 缓存命中率 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
              <Zap :size="20" class="text-green-600 dark:text-green-400" />
            </div>
            <span
              class="text-sm font-medium text-gray-600 dark:text-gray-400"
              >{{ $t('database-monitor.cacheHitRatio') }}</span
            >
          </div>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ cacheHitRatio.toFixed(2) }}%
        </div>
        <ElProgress
          :percentage="Number(cacheHitRatio.toFixed(1))"
          :color="getPercentColor(cacheHitRatio)"
          :stroke-width="8"
        />
        <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {{ $t('database-monitor.cacheHitRatio') }}
        </div>
      </ElCard>

      <!-- PostgreSQL: 事务提交 -->
      <ElCard v-if="dbType === 'POSTGRESQL'" shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
            <TrendingUp :size="20" class="text-blue-600 dark:text-blue-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('database-monitor.transactionsCommit')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatNumber(performanceStats?.transactions_commit || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('database-monitor.totalCommittedTransactions') }}
        </div>
      </ElCard>

      <!-- PostgreSQL: 事务回滚 -->
      <ElCard v-if="dbType === 'POSTGRESQL'" shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-orange-100 p-2 dark:bg-orange-900/30">
            <Activity :size="20" class="text-orange-600 dark:text-orange-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('database-monitor.transactionsRollback')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatNumber(performanceStats?.transactions_rollback || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('database-monitor.totalRollbackTransactions') }}
        </div>
      </ElCard>

      <!-- MySQL: 总查询数 -->
      <ElCard v-if="dbType === 'MYSQL'" shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
            <BarChart :size="20" class="text-blue-600 dark:text-blue-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('database-monitor.totalQueries')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatNumber(performanceStats?.total_queries || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('database-monitor.totalQueriesCount') }}
        </div>
      </ElCard>

      <!-- MySQL: 慢查询 -->
      <ElCard v-if="dbType === 'MYSQL'" shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-red-100 p-2 dark:bg-red-900/30">
            <Activity :size="20" class="text-red-600 dark:text-red-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('database-monitor.slowQueries')
          }}</span>
        </div>
        <div
          class="mb-2 text-3xl font-bold"
          :class="
            (performanceStats?.slow_queries || 0) > 0 ? 'text-red-600' : ''
          "
        >
          {{ formatNumber(performanceStats?.slow_queries || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('database-monitor.queriesNeedOptimization') }}
        </div>
      </ElCard>

      <!-- SQL Server: 批处理请求 -->
      <ElCard v-if="dbType === 'SQLSERVER'" shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
            <Zap :size="20" class="text-purple-600 dark:text-purple-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('database-monitor.batchRequestsPerSec')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ performanceStats?.batch_requests_per_sec || 0 }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('database-monitor.batchRequestsPerSecDesc') }}
        </div>
      </ElCard>
    </div>

    <!-- PostgreSQL 性能详情 -->
    <div
      v-if="dbType === 'POSTGRESQL'"
      class="grid grid-cols-1 gap-4 lg:grid-cols-2"
    >
      <!-- 事务统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <TrendingUp :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('database-monitor.transactionStats')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem
            :label="$t('database-monitor.transactionsCommit')"
          >
            <span class="font-mono">{{
              formatNumber(performanceStats?.transactions_commit || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem
            :label="$t('database-monitor.transactionsRollback')"
          >
            <span class="font-mono">{{
              formatNumber(performanceStats?.transactions_rollback || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.commitRate')">
            <div class="flex items-center gap-2">
              <ElProgress
                :percentage="
                  Number(
                    (
                      ((performanceStats?.transactions_commit || 0) /
                        ((performanceStats?.transactions_commit || 0) +
                          (performanceStats?.transactions_rollback || 1))) *
                      100
                    ).toFixed(1),
                  )
                "
                :color="
                  getPercentColor(
                    ((performanceStats?.transactions_commit || 0) /
                      ((performanceStats?.transactions_commit || 0) +
                        (performanceStats?.transactions_rollback || 1))) *
                      100,
                  )
                "
                class="flex-1"
              />
              <span class="font-semibold">
                {{
                  (
                    ((performanceStats?.transactions_commit || 0) /
                      ((performanceStats?.transactions_commit || 0) +
                        (performanceStats?.transactions_rollback || 1))) *
                    100
                  ).toFixed(1)
                }}%
              </span>
            </div>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.cacheHitRatio')">
            <div class="flex items-center gap-2">
              <ElProgress
                :percentage="
                  Number(performanceStats?.cache_hit_ratio?.toFixed(1) || 0)
                "
                :color="getPercentColor(performanceStats?.cache_hit_ratio || 0)"
                class="flex-1"
              />
              <span class="font-semibold">
                {{ performanceStats?.cache_hit_ratio?.toFixed(2) || 0 }}%
              </span>
            </div>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 元组操作统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <BarChart :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('database-monitor.tupleOperations')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('database-monitor.tuplesReturned')">
            <span class="font-mono">{{
              formatNumber(performanceStats?.tuples_returned || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.tuplesFetched')">
            <span class="font-mono">{{
              formatNumber(performanceStats?.tuples_fetched || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.tuplesInserted')">
            <span class="font-mono text-green-600">{{
              formatNumber(performanceStats?.tuples_inserted || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.tuplesUpdated')">
            <span class="font-mono text-blue-600">{{
              formatNumber(performanceStats?.tuples_updated || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.tuplesDeleted')">
            <span class="font-mono text-red-600">{{
              formatNumber(performanceStats?.tuples_deleted || 0)
            }}</span>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </div>

    <!-- MySQL 性能详情 -->
    <div
      v-if="dbType === 'MYSQL'"
      class="grid grid-cols-1 gap-4 lg:grid-cols-2"
    >
      <!-- 查询统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <BarChart :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('database-monitor.queryStats')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('database-monitor.totalQueries')">
            <span class="font-mono">{{
              formatNumber(performanceStats?.total_queries || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.totalConnections')">
            <span class="font-mono">{{
              formatNumber(performanceStats?.total_connections || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.slowQueries')">
            <div class="flex items-center gap-2">
              <span
                class="font-mono"
                :class="
                  (performanceStats?.slow_queries || 0) > 0
                    ? 'text-red-600'
                    : ''
                "
              >
                {{ formatNumber(performanceStats?.slow_queries || 0) }}
              </span>
              <ElTag
                v-if="(performanceStats?.slow_queries || 0) > 0"
                type="danger"
                size="small"
              >
                {{ $t('database-monitor.needOptimization') }}
              </ElTag>
            </div>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.cacheHitRatio')">
            <div class="flex items-center gap-2">
              <ElProgress
                :percentage="
                  Number(performanceStats?.cache_hit_ratio?.toFixed(1) || 0)
                "
                :color="getPercentColor(performanceStats?.cache_hit_ratio || 0)"
                class="flex-1"
              />
              <span class="font-semibold">
                {{ performanceStats?.cache_hit_ratio?.toFixed(2) || 0 }}%
              </span>
            </div>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 网络流量 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Activity :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('database-monitor.networkTraffic')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('database-monitor.bytesReceived')">
            <span class="font-mono">{{
              formatBytes(performanceStats?.bytes_received || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.bytesSent')">
            <span class="font-mono">{{
              formatBytes(performanceStats?.bytes_sent || 0)
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('database-monitor.totalTraffic')">
            <span class="font-mono font-semibold">
              {{
                formatBytes(
                  (performanceStats?.bytes_received || 0) +
                    (performanceStats?.bytes_sent || 0),
                )
              }}
            </span>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </div>

    <!-- SQL Server 性能详情 -->
    <div
      v-if="dbType === 'SQLSERVER'"
      class="grid grid-cols-1 gap-4 lg:grid-cols-2"
    >
      <!-- 批处理统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Zap :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('database-monitor.batchStats')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem
            :label="$t('database-monitor.batchRequestsPerSec')"
          >
            <span class="font-mono">{{
              performanceStats?.batch_requests_per_sec || 0
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem
            :label="$t('database-monitor.pageLifeExpectancy')"
          >
            <span class="font-mono">{{
              performanceStats?.page_life_expectancy || 0
            }}</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem
            :label="$t('database-monitor.bufferCacheHitRatio')"
          >
            <div class="flex items-center gap-2">
              <ElProgress
                :percentage="
                  Number(
                    performanceStats?.buffer_cache_hit_ratio?.toFixed(1) || 0,
                  )
                "
                :color="
                  getPercentColor(performanceStats?.buffer_cache_hit_ratio || 0)
                "
                class="flex-1"
              />
              <span class="font-semibold">
                {{ performanceStats?.buffer_cache_hit_ratio?.toFixed(2) || 0 }}%
              </span>
            </div>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 缓存统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Activity :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('database-monitor.cacheStats')
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
                :color="getPercentColor(performanceStats?.cache_hit_ratio || 0)"
                class="flex-1"
              />
              <span class="font-semibold">
                {{ performanceStats?.cache_hit_ratio?.toFixed(2) || 0 }}%
              </span>
            </div>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </div>

    <!-- 性能说明 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Activity :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('database-monitor.performanceMetricExplanation')
          }}</span>
        </div>
      </template>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('database-monitor.cacheHitRatio') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('database-monitor.cacheHitRatioDesc') }}
          </div>
        </div>

        <!-- PostgreSQL -->
        <template v-if="dbType === 'POSTGRESQL'">
          <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
              {{ $t('database-monitor.transactionsCommit') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              {{ $t('database-monitor.transactionsCommitDesc') }}
            </div>
          </div>
          <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
              {{ $t('database-monitor.transactionsRollback') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              {{ $t('database-monitor.transactionsRollbackDesc') }}
            </div>
          </div>
          <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
              {{ $t('database-monitor.tupleOperations') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              {{ $t('database-monitor.tupleOperationsDesc') }}
            </div>
          </div>
        </template>

        <!-- MySQL -->
        <template v-if="dbType === 'MYSQL'">
          <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
              {{ $t('database-monitor.totalQueries') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              {{ $t('database-monitor.totalQueriesDesc') }}
            </div>
          </div>
          <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
              {{ $t('database-monitor.slowQueries') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              {{ $t('database-monitor.slowQueriesDesc') }}
            </div>
          </div>
          <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
              {{ $t('database-monitor.networkTraffic') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              {{ $t('database-monitor.networkTrafficDesc') }}
            </div>
          </div>
        </template>

        <!-- SQL Server -->
        <template v-if="dbType === 'SQLSERVER'">
          <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
              {{ $t('database-monitor.batchRequests') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              {{ $t('database-monitor.batchRequestsDesc') }}
            </div>
          </div>
          <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
              {{ $t('database-monitor.pageLifeExpectancy') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              {{ $t('database-monitor.pageLifeExpectancyDesc') }}
            </div>
          </div>
          <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
              {{ $t('database-monitor.bufferCacheHitRatio') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              {{ $t('database-monitor.bufferCacheHitRatioDesc') }}
            </div>
          </div>
        </template>
      </div>
    </ElCard>
  </div>
</template>
