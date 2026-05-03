<script setup lang="ts">
import type {
  RealtimeStats as RealtimeStatsType,
  ServerMonitorResponse,
} from '#/api/core/server-monitor';

import { ListTree } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElCard, ElTag } from 'element-plus';

defineOptions({ name: 'ProcessPanel' });

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

// 获取进程状态颜色
function getStatusColor(
  status: string,
): 'danger' | 'info' | 'primary' | 'success' | 'warning' {
  const statusMap: Record<
    string,
    'danger' | 'info' | 'primary' | 'success' | 'warning'
  > = {
    running: 'success',
    sleeping: 'info',
    stopped: 'warning',
    zombie: 'danger',
  };
  return statusMap[status.toLowerCase()] || 'info';
}
</script>

<template>
  <div class="space-y-4">
    <!-- 进程统计概览 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <!-- 总进程数 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
            <ListTree :size="20" class="text-blue-600 dark:text-blue-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.totalProcesses')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ realtimeData?.process_info?.total_processes || 0 }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.totalSystemProcesses') }}
        </div>
      </ElCard>

      <!-- 运行中 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
            <ListTree :size="20" class="text-green-600 dark:text-green-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.running')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ realtimeData?.process_info?.running_processes || 0 }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.runningProcesses') }}
        </div>
      </ElCard>

      <!-- 休眠中 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
            <ListTree :size="20" class="text-purple-600 dark:text-purple-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.sleeping')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ realtimeData?.process_info?.sleeping_processes || 0 }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.sleepingProcesses') }}
        </div>
      </ElCard>

      <!-- 其他状态 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-orange-100 p-2 dark:bg-orange-900/30">
            <ListTree :size="20" class="text-orange-600 dark:text-orange-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.otherStatus')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{
            (realtimeData?.process_info?.total_processes || 0) -
            (realtimeData?.process_info?.running_processes || 0) -
            (realtimeData?.process_info?.sleeping_processes || 0)
          }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.stoppedZombieStatus') }}
        </div>
      </ElCard>
    </div>

    <!-- Top 进程列表 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <ListTree :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.topProcessesCpu')
          }}</span>
        </div>
      </template>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                PID
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('server-monitor.processName') }}
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                CPU %
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                内存 %
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('server-monitor.status') }}
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('server-monitor.createTime') }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="process in realtimeData?.process_info?.top_processes || []"
              :key="process.pid"
              class="transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <td class="px-4 py-3 font-mono text-xs">{{ process.pid }}</td>
              <td class="px-4 py-3 font-medium">
                <div class="max-w-xs truncate" :title="process.name">
                  {{ process.name }}
                </div>
              </td>
              <td class="px-4 py-3">
                <ElTag
                  :type="getPercentColor(process.cpu_percent)"
                  size="small"
                >
                  {{ process.cpu_percent.toFixed(1) }}%
                </ElTag>
              </td>
              <td class="px-4 py-3">
                <ElTag
                  :type="getPercentColor(process.memory_percent)"
                  size="small"
                >
                  {{ process.memory_percent.toFixed(1) }}%
                </ElTag>
              </td>
              <td class="px-4 py-3">
                <ElTag :type="getStatusColor(process.status)" size="small">
                  {{ process.status }}
                </ElTag>
              </td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">
                {{ process.create_time }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 空状态 -->
      <div
        v-if="
          !realtimeData?.process_info?.top_processes ||
          realtimeData.process_info.top_processes.length === 0
        "
        class="py-12 text-center text-gray-400"
      >
        <ListTree :size="48" class="mx-auto mb-4 opacity-50" />
        <p>{{ $t('server-monitor.noProcessData') }}</p>
      </div>
    </ElCard>

    <!-- 进程统计详情 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <!-- 进程状态分布 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <ListTree :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('server-monitor.processDistribution')
            }}</span>
          </div>
        </template>

        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="h-3 w-3 rounded-full bg-green-500"></div>
              <span class="text-sm text-gray-600 dark:text-gray-400">{{
                $t('server-monitor.running')
              }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-semibold">{{
                realtimeData?.process_info?.running_processes || 0
              }}</span>
              <ElTag type="success" size="small">
                {{
                  (
                    ((realtimeData?.process_info?.running_processes || 0) /
                      (realtimeData?.process_info?.total_processes || 1)) *
                    100
                  ).toFixed(1)
                }}%
              </ElTag>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="h-3 w-3 rounded-full bg-blue-500"></div>
              <span class="text-sm text-gray-600 dark:text-gray-400">{{
                $t('server-monitor.sleeping')
              }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-semibold">{{
                realtimeData?.process_info?.sleeping_processes || 0
              }}</span>
              <ElTag type="info" size="small">
                {{
                  (
                    ((realtimeData?.process_info?.sleeping_processes || 0) /
                      (realtimeData?.process_info?.total_processes || 1)) *
                    100
                  ).toFixed(1)
                }}%
              </ElTag>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="h-3 w-3 rounded-full bg-gray-500"></div>
              <span class="text-sm text-gray-600 dark:text-gray-400">{{
                $t('server-monitor.otherStatus')
              }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-semibold">{{
                (realtimeData?.process_info?.total_processes || 0) -
                (realtimeData?.process_info?.running_processes || 0) -
                (realtimeData?.process_info?.sleeping_processes || 0)
              }}</span>
              <ElTag type="info" size="small">
                {{
                  (
                    (((realtimeData?.process_info?.total_processes || 0) -
                      (realtimeData?.process_info?.running_processes || 0) -
                      (realtimeData?.process_info?.sleeping_processes || 0)) /
                      (realtimeData?.process_info?.total_processes || 1)) *
                    100
                  ).toFixed(1)
                }}%
              </ElTag>
            </div>
          </div>

          <div class="mt-4 border-t border-gray-200 pt-3 dark:border-gray-700">
            <div class="flex items-center justify-between">
              <span class="font-medium text-gray-700 dark:text-gray-300">{{
                $t('server-monitor.total')
              }}</span>
              <span class="text-lg font-bold">{{
                realtimeData?.process_info?.total_processes || 0
              }}</span>
            </div>
          </div>
        </div>
      </ElCard>

      <!-- 资源使用Top进程 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <ListTree :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('server-monitor.resourceUsageRanking')
            }}</span>
          </div>
        </template>

        <div class="space-y-3">
          <div
            v-for="(process, index) in (
              realtimeData?.process_info?.top_processes || []
            ).slice(0, 5)"
            :key="process.pid"
            class="rounded-lg border border-gray-200 p-3 dark:border-gray-700"
          >
            <div class="mb-2 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div
                  class="flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold"
                  :class="{
                    'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400':
                      index === 0,
                    'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400':
                      index === 1,
                    'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400':
                      index === 2,
                    'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400':
                      index > 2,
                  }"
                >
                  {{ index + 1 }}
                </div>
                <span class="font-medium">{{ process.name }}</span>
              </div>
              <span class="text-xs text-gray-500">PID: {{ process.pid }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-600 dark:text-gray-400">CPU:</span>
              <ElTag :type="getPercentColor(process.cpu_percent)" size="small">
                {{ process.cpu_percent.toFixed(1) }}%
              </ElTag>
            </div>
            <div class="mt-1 flex items-center justify-between text-sm">
              <span class="text-gray-600 dark:text-gray-400">内存:</span>
              <ElTag
                :type="getPercentColor(process.memory_percent)"
                size="small"
              >
                {{ process.memory_percent.toFixed(1) }}%
              </ElTag>
            </div>
          </div>

          <!-- 空状态 -->
          <div
            v-if="
              !realtimeData?.process_info?.top_processes ||
              realtimeData.process_info.top_processes.length === 0
            "
            class="py-8 text-center text-gray-400"
          >
            <p class="text-sm">{{ $t('server-monitor.noProcessData') }}</p>
          </div>
        </div>
      </ElCard>
    </div>
  </div>
</template>
