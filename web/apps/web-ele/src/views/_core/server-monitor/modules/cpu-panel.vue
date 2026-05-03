<script setup lang="ts">
import type {
  RealtimeStats as RealtimeStatsType,
  ServerMonitorResponse,
} from '#/api/core/server-monitor';

import { Cpu } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElProgress,
  ElTag,
} from 'element-plus';

defineOptions({ name: 'CpuPanel' });

defineProps<{
  realtimeData: null | RealtimeStatsType;
  serverData: null | ServerMonitorResponse;
}>();

// 获取使用率颜色
function getPercentColor(
  percent: number,
): 'danger' | 'info' | 'primary' | 'success' | 'warning' {
  if (percent >= 90) return 'danger';
  if (percent >= 70) return 'warning';
  return 'success';
}

// 格式化频率（MHz）
function formatFrequency(mhz: number): string {
  if (mhz >= 1000) {
    return `${(mhz / 1000).toFixed(2)} GHz`;
  }
  return `${mhz.toFixed(0)} MHz`;
}
</script>

<template>
  <div class="space-y-4">
    <!-- CPU 概览卡片 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <!-- 总体使用率 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
            <Cpu :size="20" class="text-blue-600 dark:text-blue-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.overallUsage')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ realtimeData?.cpu_percent?.toFixed(1) || '0.0' }}%
        </div>
        <ElProgress
          :percentage="Number(realtimeData?.cpu_percent?.toFixed(1) || 0)"
          :color="getPercentColor(realtimeData?.cpu_percent || 0)"
          :stroke-width="8"
        />
      </ElCard>

      <!-- 物理核心 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
            <Cpu :size="20" class="text-green-600 dark:text-green-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.physicalCores')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ serverData?.cpu_info?.physical_cores || 0 }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.coreCount') }}
        </div>
      </ElCard>

      <!-- 逻辑处理器 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
            <Cpu :size="20" class="text-purple-600 dark:text-purple-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.logicalProcessors')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ serverData?.cpu_info?.total_cores || 0 }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.threadCount') }}
        </div>
      </ElCard>
    </div>

    <!-- CPU 详细信息 -->
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <!-- 基本信息 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Cpu :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('server-monitor.basicInfo')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('server-monitor.processorModel')">
            {{ serverData?.basic_info?.processor || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.architecture')">
            {{ serverData?.basic_info?.architecture || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.physicalCoreCount')">
            {{ serverData?.cpu_info?.physical_cores || 0 }}
          </ElDescriptionsItem>
          <ElDescriptionsItem
            :label="$t('server-monitor.logicalProcessorCount')"
          >
            {{ serverData?.cpu_info?.total_cores || 0 }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.currentUsage')">
            <ElTag :type="getPercentColor(realtimeData?.cpu_percent || 0)">
              {{ realtimeData?.cpu_percent?.toFixed(2) || '0.00' }}%
            </ElTag>
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 频率信息 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Cpu :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('server-monitor.frequencyInfo')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('server-monitor.currentFrequency')">
            <ElTag type="primary">
              {{
                formatFrequency(serverData?.cpu_info?.current_frequency || 0)
              }}
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.maxFrequency')">
            {{ formatFrequency(serverData?.cpu_info?.max_frequency || 0) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.minFrequency')">
            {{ formatFrequency(serverData?.cpu_info?.min_frequency || 0) }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </div>

    <!-- 每个核心的使用率 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Cpu :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.coreUsage')
          }}</span>
        </div>
      </template>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="(percent, index) in serverData?.cpu_info
            ?.cpu_percent_per_core || []"
          :key="index"
          class="rounded-lg border border-gray-200 p-4 dark:border-gray-700"
        >
          <div class="mb-2 flex items-center justify-between">
            <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{ $t('server-monitor.core') }} {{ index }}</span>
            <ElTag :type="getPercentColor(percent)" size="small">
              {{ percent.toFixed(1) }}%
            </ElTag>
          </div>
          <ElProgress
            :percentage="Number(percent.toFixed(1))"
            :color="getPercentColor(percent)"
            :show-text="false"
          />
        </div>
      </div>
    </ElCard>

    <!-- CPU 时间统计 -->
    <ElCard v-if="serverData?.cpu_info?.cpu_times" shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Cpu :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.cpuTimeStats')
          }}</span>
        </div>
      </template>
      <div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
        <div
          v-for="(value, key) in serverData.cpu_info.cpu_times"
          :key="key"
          class="rounded-lg border border-gray-200 p-3 dark:border-gray-700"
        >
          <div class="mb-1 text-xs text-gray-500 dark:text-gray-400">
            {{ key }}
          </div>
          <div class="text-lg font-semibold">
            {{ typeof value === 'number' ? value.toFixed(2) : value }}
          </div>
        </div>
      </div>
    </ElCard>

    <!-- CPU 统计信息 -->
    <ElCard v-if="serverData?.cpu_info?.cpu_stats" shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Cpu :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.cpuStatsInfo')
          }}</span>
        </div>
      </template>
      <div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
        <div
          v-for="(value, key) in serverData.cpu_info.cpu_stats"
          :key="key"
          class="rounded-lg border border-gray-200 p-3 dark:border-gray-700"
        >
          <div class="mb-1 text-xs text-gray-500 dark:text-gray-400">
            {{ key }}
          </div>
          <div class="text-lg font-semibold">
            {{ typeof value === 'number' ? value.toLocaleString() : value }}
          </div>
        </div>
      </div>
    </ElCard>

    <!-- 系统负载 -->
    <ElCard v-if="realtimeData?.system_load" shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Cpu :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.systemLoad')
          }}</span>
        </div>
      </template>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
            {{ $t('server-monitor.load1min') }}
          </div>
          <div class="mb-2 text-3xl font-bold">
            {{ realtimeData.system_load.load_1min?.toFixed(2) || '0.00' }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            {{ $t('server-monitor.cpuCoreCount') }}:
            {{ realtimeData.system_load.cpu_count || 0 }}
          </div>
        </div>
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
            {{ $t('server-monitor.load5min') }}
          </div>
          <div class="mb-2 text-3xl font-bold">
            {{ realtimeData.system_load.load_5min?.toFixed(2) || '0.00' }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            {{ $t('server-monitor.cpuCoreCount') }}:
            {{ realtimeData.system_load.cpu_count || 0 }}
          </div>
        </div>
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
            {{ $t('server-monitor.load15min') }}
          </div>
          <div class="mb-2 text-3xl font-bold">
            {{ realtimeData.system_load.load_15min?.toFixed(2) || '0.00' }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            {{ $t('server-monitor.cpuCoreCount') }}:
            {{ realtimeData.system_load.cpu_count || 0 }}
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>
