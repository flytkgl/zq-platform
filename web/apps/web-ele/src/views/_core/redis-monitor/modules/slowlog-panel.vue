<script setup lang="ts">
import type {
  RedisMonitorOverview,
  RedisRealtimeStats,
} from '#/api/core/redis-monitor';

import { computed } from 'vue';

import { Activity, Clock, Database, Network, Timer } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElCard, ElEmpty, ElTag } from 'element-plus';

defineOptions({ name: 'SlowlogPanel' });

const props = defineProps<{
  monitorData: null | RedisMonitorOverview;
  realtimeData: null | RedisRealtimeStats;
}>();

// 慢日志列表
const slowLogs = computed(() => props.monitorData?.slow_log || []);

// 统计信息
const totalSlowLogs = computed(() => slowLogs.value.length);
const avgDuration = computed(() => {
  if (slowLogs.value.length === 0) return 0;
  const total = slowLogs.value.reduce((sum, log) => sum + log.duration, 0);
  return total / slowLogs.value.length;
});
const maxDuration = computed(() => {
  if (slowLogs.value.length === 0) return 0;
  return Math.max(...slowLogs.value.map((log) => log.duration));
});

// 格式化时间戳
function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString();
}

// 格式化持续时间（微秒）
function formatDuration(microseconds: number): string {
  if (microseconds < 1000) return `${microseconds}μs`;
  if (microseconds < 1_000_000) return `${(microseconds / 1000).toFixed(2)}ms`;
  return `${(microseconds / 1_000_000).toFixed(2)}s`;
}

// 获取持续时间颜色
function getDurationColor(
  microseconds: number,
): 'danger' | 'info' | 'success' | 'warning' {
  if (microseconds >= 1_000_000) return 'danger'; // >= 1s
  if (microseconds >= 100_000) return 'warning'; // >= 100ms
  if (microseconds >= 10_000) return 'info'; // >= 10ms
  return 'success';
}

// 获取持续时间进度条百分比
function getDurationPercent(duration: number): number {
  if (maxDuration.value === 0) return 0;
  return (duration / maxDuration.value) * 100;
}

// 截取命令显示
function truncateCommand(command: string, maxLength: number = 100): string {
  if (command.length <= maxLength) return command;
  return `${command.slice(0, Math.max(0, maxLength))}...`;
}
</script>

<template>
  <div class="space-y-4">
    <!-- 慢日志统计卡片 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <!-- 慢日志总数 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.totalSlowLogs') }}
            </div>
            <div class="text-3xl font-bold">
              {{ totalSlowLogs }}
            </div>
          </div>
          <div class="rounded-lg bg-blue-100 p-3 dark:bg-blue-900/30">
            <Timer :size="32" class="text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </ElCard>

      <!-- 平均耗时 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.avgDuration') }}
            </div>
            <div class="text-3xl font-bold">
              {{ formatDuration(avgDuration) }}
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ avgDuration.toFixed(0) }} μs
            </div>
          </div>
          <div class="rounded-lg bg-orange-100 p-3 dark:bg-orange-900/30">
            <Clock :size="32" class="text-orange-600 dark:text-orange-400" />
          </div>
        </div>
      </ElCard>

      <!-- 最大耗时 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.maxDuration') }}
            </div>
            <div class="text-3xl font-bold text-red-600">
              {{ formatDuration(maxDuration) }}
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ maxDuration.toFixed(0) }} μs
            </div>
          </div>
          <div class="rounded-lg bg-red-100 p-3 dark:bg-red-900/30">
            <Activity :size="32" class="text-red-600 dark:text-red-400" />
          </div>
        </div>
      </ElCard>
    </div>

    <!-- 慢日志列表 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Timer :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.slowLogList')
            }}</span>
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {{
              $t('redis-monitor.recentLogsCount', { count: slowLogs.length })
            }}
          </div>
        </div>
      </template>

      <div v-if="slowLogs.length === 0">
        <ElEmpty :description="$t('redis-monitor.noSlowLogs')">
          <template #image>
            <Database :size="64" class="text-gray-300" />
          </template>
        </ElEmpty>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="(log, index) in slowLogs"
          :key="log.id"
          class="hover:border-primary rounded-lg border border-gray-200 p-4 transition-all hover:shadow-md dark:border-gray-700"
        >
          <!-- 日志头部 -->
          <div class="mb-3 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div
                class="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-800"
              >
                <span
                  class="font-mono text-sm font-semibold text-gray-600 dark:text-gray-400"
                >
                  #{{ index + 1 }}
                </span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-sm text-gray-500 dark:text-gray-400"
                    >ID:</span
                  >
                  <span class="font-mono text-sm font-semibold">{{
                    log.id
                  }}</span>
                </div>
                <div
                  class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400"
                >
                  <Clock :size="12" />
                  <span>{{ formatTimestamp(log.timestamp) }}</span>
                </div>
              </div>
            </div>
            <ElTag :type="getDurationColor(log.duration)" size="large">
              {{ formatDuration(log.duration) }}
            </ElTag>
          </div>

          <!-- 命令内容 -->
          <div class="mb-3 rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="mb-1 text-xs text-gray-500 dark:text-gray-400">
              {{ $t('redis-monitor.command') }}:
            </div>
            <div class="break-all font-mono text-sm">
              {{ truncateCommand(log.command) }}
            </div>
          </div>

          <!-- 客户端信息和耗时进度 -->
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <!-- 客户端信息 -->
            <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
              <div class="mb-2 flex items-center gap-2">
                <Network :size="14" class="text-gray-400" />
                <span class="text-xs text-gray-500 dark:text-gray-400">{{
                  $t('redis-monitor.clientInfo')
                }}</span>
              </div>
              <div class="space-y-1">
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600 dark:text-gray-400">IP:</span>
                  <span class="font-mono">{{ log.client_ip || '-' }}</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600 dark:text-gray-400"
                    >{{ $t('redis-monitor.name') }}:</span
                  >
                  <span class="font-mono">{{
                    log.client_name || $t('redis-monitor.unnamed')
                  }}</span>
                </div>
              </div>
            </div>

            <!-- 耗时进度 -->
            <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
              <div class="mb-2 flex items-center gap-2">
                <Activity :size="14" class="text-gray-400" />
                <span class="text-xs text-gray-500 dark:text-gray-400">{{
                  $t('redis-monitor.durationProportion')
                }}</span>
              </div>
              <div class="space-y-2">
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600 dark:text-gray-400"
                    >{{ $t('redis-monitor.relativeToMax') }}:</span
                  >
                  <span class="font-semibold"
                    >{{ getDurationPercent(log.duration).toFixed(1) }}%</span
                  >
                </div>
                <div
                  class="h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700"
                >
                  <div
                    class="h-full transition-all"
                    :class="{
                      'bg-red-500': getDurationColor(log.duration) === 'danger',
                      'bg-yellow-500':
                        getDurationColor(log.duration) === 'warning',
                      'bg-blue-500': getDurationColor(log.duration) === 'info',
                      'bg-green-500':
                        getDurationColor(log.duration) === 'success',
                    }"
                    :style="{ width: `${getDurationPercent(log.duration)}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ElCard>

    <!-- 慢日志说明 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Activity :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('redis-monitor.slowLogDesc')
          }}</span>
        </div>
      </template>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.slowLogThreshold') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.slowLogThresholdDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.executionTime') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.executionTimeDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.clientInfo') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.clientInfoDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.performanceOptimization') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.performanceOptimizationDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.timeUnit') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{
              $t('redis-monitor.timeUnitDesc') ||
              'μs(微秒) = 0.001ms，ms(毫秒) = 0.001s'
            }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.colorIndicator') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{
              $t('redis-monitor.colorIndicatorDesc') ||
              '红色(≥1s) > 黄色(≥100ms) > 蓝色(≥10ms) > 绿色'
            }}
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>
