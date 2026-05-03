<script setup lang="ts">
import type {
  RealtimeStats as RealtimeStatsType,
  ServerMonitorResponse,
} from '#/api/core/server-monitor';

import { Database } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElProgress,
  ElTag,
} from 'element-plus';

defineOptions({ name: 'MemoryPanel' });

defineProps<{
  realtimeData: null | RealtimeStatsType;
  serverData: null | ServerMonitorResponse;
}>();

// 格式化内存大小（后端返回的是GB）
function formatMemory(gb: number): string {
  if (gb === 0) return '0 GB';
  if (gb < 1) {
    return `${(gb * 1024).toFixed(2)} MB`;
  }
  return `${gb.toFixed(2)} GB`;
}

// 获取使用率颜色
function getPercentColor(
  percent: number,
): 'danger' | 'info' | 'primary' | 'success' | 'warning' {
  if (percent >= 90) return 'danger';
  if (percent >= 70) return 'warning';
  return 'success';
}
</script>

<template>
  <div class="space-y-4">
    <!-- 内存概览卡片 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <!-- 总内存 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
            <Database :size="20" class="text-blue-600 dark:text-blue-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.totalMemory')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatMemory(serverData?.memory_info?.virtual?.total || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.physicalMemoryTotal') }}
        </div>
      </ElCard>

      <!-- 已使用 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-orange-100 p-2 dark:bg-orange-900/30">
            <Database :size="20" class="text-orange-600 dark:text-orange-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.used')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatMemory(serverData?.memory_info?.virtual?.used || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ (serverData?.memory_info?.virtual?.percent || 0).toFixed(1) }}%
          {{ $t('server-monitor.memoryUsage') }}
        </div>
      </ElCard>

      <!-- 可用内存 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
            <Database :size="20" class="text-green-600 dark:text-green-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.availableMemory')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatMemory(serverData?.memory_info?.virtual?.available || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.immediatelyAvailable') }}
        </div>
      </ElCard>

      <!-- 使用率 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
            <Database :size="20" class="text-purple-600 dark:text-purple-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.memoryUsage')
          }}</span>
        </div>
        <div class="mb-2 text-4xl font-bold">
          {{ (realtimeData?.memory_percent || 0).toFixed(1) }}%
        </div>
        <ElProgress
          :percentage="Number((realtimeData?.memory_percent || 0).toFixed(1))"
          :color="getPercentColor(realtimeData?.memory_percent || 0)"
          :stroke-width="8"
        />
      </ElCard>
    </div>

    <!-- 虚拟内存详情 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Database :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.virtualMemoryRam')
          }}</span>
        </div>
      </template>

      <div class="mb-4">
        <div class="mb-2 flex items-center justify-between">
          <span class="text-sm text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.memoryUsageStatus')
          }}</span>
          <ElTag
            :type="
              getPercentColor(serverData?.memory_info?.virtual?.percent || 0)
            "
          >
            {{ (serverData?.memory_info?.virtual?.percent || 0).toFixed(2) }}%
          </ElTag>
        </div>
        <ElProgress
          :percentage="
            Number((serverData?.memory_info?.virtual?.percent || 0).toFixed(1))
          "
          :color="
            getPercentColor(serverData?.memory_info?.virtual?.percent || 0)
          "
          :stroke-width="8"
        >
          <template #default="{ percentage }">
            <span class="text-xs">{{ percentage }}%</span>
          </template>
        </ElProgress>
      </div>

      <ElDescriptions :column="2" border size="small">
        <ElDescriptionsItem :label="$t('server-monitor.totalMemory')">
          {{ formatMemory(serverData?.memory_info?.virtual?.total || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.availableMemory')">
          {{ formatMemory(serverData?.memory_info?.virtual?.available || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.used')">
          {{ formatMemory(serverData?.memory_info?.virtual?.used || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.freeMemory')">
          {{ formatMemory(serverData?.memory_info?.virtual?.free || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.activeMemory')">
          {{ formatMemory(serverData?.memory_info?.virtual?.active || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.inactiveMemory')">
          {{ formatMemory(serverData?.memory_info?.virtual?.inactive || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.buffer')">
          {{ formatMemory(serverData?.memory_info?.virtual?.buffers || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.cache')">
          {{ formatMemory(serverData?.memory_info?.virtual?.cached || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.sharedMemory')">
          {{ formatMemory(serverData?.memory_info?.virtual?.shared || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.memoryUsage')">
          <ElTag
            :type="
              getPercentColor(serverData?.memory_info?.virtual?.percent || 0)
            "
          >
            {{ (serverData?.memory_info?.virtual?.percent || 0).toFixed(2) }}%
          </ElTag>
        </ElDescriptionsItem>
      </ElDescriptions>
    </ElCard>

    <!-- 交换内存（Swap）详情 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Database :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.swapPartition')
          }}</span>
        </div>
      </template>

      <div class="mb-4">
        <div class="mb-2 flex items-center justify-between">
          <span class="text-sm text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.swapUsageStatus')
          }}</span>
          <ElTag
            :type="getPercentColor(serverData?.memory_info?.swap?.percent || 0)"
          >
            {{ (serverData?.memory_info?.swap?.percent || 0).toFixed(2) }}%
          </ElTag>
        </div>
        <ElProgress
          :percentage="
            Number((serverData?.memory_info?.swap?.percent || 0).toFixed(1))
          "
          :color="getPercentColor(serverData?.memory_info?.swap?.percent || 0)"
          :stroke-width="8"
        >
          <template #default="{ percentage }">
            <span class="text-xs">{{ percentage }}%</span>
          </template>
        </ElProgress>
      </div>

      <ElDescriptions :column="2" border size="small">
        <ElDescriptionsItem :label="$t('server-monitor.swapTotal')">
          {{ formatMemory(serverData?.memory_info?.swap?.total || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.used')">
          {{ formatMemory(serverData?.memory_info?.swap?.used || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.swapAvailable')">
          {{ formatMemory(serverData?.memory_info?.swap?.free || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.memoryUsage')">
          <ElTag
            :type="getPercentColor(serverData?.memory_info?.swap?.percent || 0)"
          >
            {{ (serverData?.memory_info?.swap?.percent || 0).toFixed(2) }}%
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.swapIn')">
          {{ formatMemory(serverData?.memory_info?.swap?.sin || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('server-monitor.swapOut')">
          {{ formatMemory(serverData?.memory_info?.swap?.sout || 0) }}
        </ElDescriptionsItem>
      </ElDescriptions>
    </ElCard>

    <!-- 内存使用分布 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Database :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.memoryDistribution')
          }}</span>
        </div>
      </template>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <!-- 已使用 -->
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('server-monitor.used')
            }}</span>
            <ElTag type="warning" size="small">
              {{
                (
                  ((serverData?.memory_info?.virtual?.used || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1)
              }}%
            </ElTag>
          </div>
          <div class="mb-2 text-2xl font-bold">
            {{ formatMemory(serverData?.memory_info?.virtual?.used || 0) }}
          </div>
          <ElProgress
            :percentage="
              Number(
                (
                  ((serverData?.memory_info?.virtual?.used || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1),
              )
            "
            color="#f59e0b"
            :show-text="false"
          />
        </div>

        <!-- 缓存 -->
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('server-monitor.cache')
            }}</span>
            <ElTag type="info" size="small">
              {{
                (
                  ((serverData?.memory_info?.virtual?.cached || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1)
              }}%
            </ElTag>
          </div>
          <div class="mb-2 text-2xl font-bold">
            {{ formatMemory(serverData?.memory_info?.virtual?.cached || 0) }}
          </div>
          <ElProgress
            :percentage="
              Number(
                (
                  ((serverData?.memory_info?.virtual?.cached || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1),
              )
            "
            color="#3b82f6"
            :show-text="false"
          />
        </div>

        <!-- 缓冲区 -->
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('server-monitor.buffer')
            }}</span>
            <ElTag type="info" size="small">
              {{
                (
                  ((serverData?.memory_info?.virtual?.buffers || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1)
              }}%
            </ElTag>
          </div>
          <div class="mb-2 text-2xl font-bold">
            {{ formatMemory(serverData?.memory_info?.virtual?.buffers || 0) }}
          </div>
          <ElProgress
            :percentage="
              Number(
                (
                  ((serverData?.memory_info?.virtual?.buffers || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1),
              )
            "
            color="#8b5cf6"
            :show-text="false"
          />
        </div>

        <!-- 活跃内存 -->
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('server-monitor.activeMemory')
            }}</span>
            <ElTag type="success" size="small">
              {{
                (
                  ((serverData?.memory_info?.virtual?.active || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1)
              }}%
            </ElTag>
          </div>
          <div class="mb-2 text-2xl font-bold">
            {{ formatMemory(serverData?.memory_info?.virtual?.active || 0) }}
          </div>
          <ElProgress
            :percentage="
              Number(
                (
                  ((serverData?.memory_info?.virtual?.active || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1),
              )
            "
            color="#10b981"
            :show-text="false"
          />
        </div>

        <!-- 非活跃内存 -->
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('server-monitor.inactiveMemory')
            }}</span>
            <ElTag type="info" size="small">
              {{
                (
                  ((serverData?.memory_info?.virtual?.inactive || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1)
              }}%
            </ElTag>
          </div>
          <div class="mb-2 text-2xl font-bold">
            {{ formatMemory(serverData?.memory_info?.virtual?.inactive || 0) }}
          </div>
          <ElProgress
            :percentage="
              Number(
                (
                  ((serverData?.memory_info?.virtual?.inactive || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1),
              )
            "
            color="#6b7280"
            :show-text="false"
          />
        </div>

        <!-- 空闲内存 -->
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('server-monitor.freeMemory')
            }}</span>
            <ElTag type="success" size="small">
              {{
                (
                  ((serverData?.memory_info?.virtual?.free || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1)
              }}%
            </ElTag>
          </div>
          <div class="mb-2 text-2xl font-bold">
            {{ formatMemory(serverData?.memory_info?.virtual?.free || 0) }}
          </div>
          <ElProgress
            :percentage="
              Number(
                (
                  ((serverData?.memory_info?.virtual?.free || 0) /
                    (serverData?.memory_info?.virtual?.total || 1)) *
                  100
                ).toFixed(1),
              )
            "
            color="#22c55e"
            :show-text="false"
          />
        </div>
      </div>
    </ElCard>

    <!-- 实时内存详情 -->
    <ElCard v-if="realtimeData?.memory_details" shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Database :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.realtimeMemoryDetails')
          }}</span>
        </div>
      </template>
      <div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
        <div
          v-for="(value, key) in realtimeData.memory_details"
          :key="key"
          class="rounded-lg border border-gray-200 p-3 dark:border-gray-700"
        >
          <div class="mb-1 text-xs text-gray-500 dark:text-gray-400">
            {{ key }}
          </div>
          <div class="text-lg font-semibold">
            {{ typeof value === 'number' ? formatMemory(value) : value || '-' }}
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>
