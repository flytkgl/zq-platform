<script setup lang="ts">
import type {
  RedisMonitorOverview,
  RedisRealtimeStats,
} from '#/api/core/redis-monitor';

import { computed } from 'vue';

import { Activity, Network, Users } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElCard, ElEmpty, ElTag } from 'element-plus';

defineOptions({ name: 'ClientsPanel' });

const props = defineProps<{
  monitorData: null | RedisMonitorOverview;
  realtimeData: null | RedisRealtimeStats;
}>();

// 客户端列表
const clients = computed(() => props.monitorData?.clients || []);

// 格式化时间（秒转为可读格式）
function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds}${$t('redis-monitor.seconds')}`;
  if (seconds < 3600)
    return `${Math.floor(seconds / 60)}${$t('redis-monitor.minutes')}`;
  if (seconds < 86_400)
    return `${Math.floor(seconds / 3600)}${$t('redis-monitor.hours')}`;
  return `${Math.floor(seconds / 86_400)}${$t('redis-monitor.days')}`;
}

// 格式化字节大小
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(2)} ${sizes[i]}`;
}

// 获取客户端状态颜色
function getClientStatusColor(
  flags: string,
): 'danger' | 'info' | 'success' | 'warning' {
  if (flags.includes('M')) return 'danger'; // Master
  if (flags.includes('S')) return 'warning'; // Slave
  if (flags.includes('b')) return 'info'; // Blocked
  return 'success'; // Normal
}

// 获取客户端状态文本
function getClientStatusText(flags: string): string {
  if (flags.includes('M')) return $t('redis-monitor.master');
  if (flags.includes('S')) return $t('redis-monitor.slave');
  if (flags.includes('b')) return $t('redis-monitor.blocked');
  if (flags.includes('N')) return $t('redis-monitor.normal');
  return $t('redis-monitor.active');
}
</script>

<template>
  <div class="space-y-4">
    <!-- 客户端统计卡片 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <!-- 连接客户端数 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.connectedClients') }}
            </div>
            <div class="text-3xl font-bold">
              {{ clients.length }}
            </div>
          </div>
          <div class="rounded-lg bg-blue-100 p-3 dark:bg-blue-900/30">
            <Users :size="32" class="text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </ElCard>

      <!-- 阻塞客户端数 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.blockedClients') }}
            </div>
            <div class="text-3xl font-bold">
              {{ monitorData?.info?.blocked_clients || 0 }}
            </div>
          </div>
          <div class="rounded-lg bg-orange-100 p-3 dark:bg-orange-900/30">
            <Activity :size="32" class="text-orange-600 dark:text-orange-400" />
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
              {{ monitorData?.stats?.total_connections_received || 0 }}
            </div>
          </div>
          <div class="rounded-lg bg-green-100 p-3 dark:bg-green-900/30">
            <Network :size="32" class="text-green-600 dark:text-green-400" />
          </div>
        </div>
      </ElCard>
    </div>

    <!-- 客户端列表 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Users :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.clientList')
            }}</span>
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {{
              $t('redis-monitor.totalClientsCount', { count: clients.length })
            }}
          </div>
        </div>
      </template>

      <div v-if="clients.length === 0">
        <ElEmpty :description="$t('redis-monitor.noClientConnections')" />
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('redis-monitor.clientId') }}
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('redis-monitor.address') }}
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('redis-monitor.name') }}
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('redis-monitor.database') }}
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('redis-monitor.status') }}
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('redis-monitor.age') }}
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('redis-monitor.idle') }}
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('redis-monitor.outputBuffer') }}
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('redis-monitor.lastCommand') }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="client in clients"
              :key="client.id"
              class="hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <td class="px-4 py-3 font-mono text-xs">
                {{ client.id }}
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-1">
                  <Network :size="14" class="text-gray-400" />
                  <span class="font-mono text-xs">{{ client.addr }}</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <span v-if="client.name" class="font-medium">{{
                  client.name
                }}</span>
                <span v-else class="text-gray-400">-</span>
              </td>
              <td class="px-4 py-3">
                <ElTag size="small" type="info"> DB{{ client.db }} </ElTag>
              </td>
              <td class="px-4 py-3">
                <ElTag size="small" :type="getClientStatusColor(client.flags)">
                  {{ getClientStatusText(client.flags) }}
                </ElTag>
              </td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">
                {{ formatTime(client.age) }}
              </td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">
                {{ formatTime(client.idle) }}
              </td>
              <td class="px-4 py-3">
                <div class="text-xs">
                  <div>
                    {{ $t('redis-monitor.used') }}:
                    {{ formatBytes(client.omem) }}
                  </div>
                  <div class="text-gray-500">
                    {{ $t('redis-monitor.queue') }}:
                    {{ client.obl + client.oll }}
                  </div>
                </div>
              </td>
              <td class="px-4 py-3">
                <span
                  v-if="client.cmd"
                  class="rounded bg-gray-100 px-2 py-1 font-mono text-xs dark:bg-gray-700"
                >
                  {{ client.cmd }}
                </span>
                <span v-else class="text-gray-400">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </ElCard>

    <!-- 客户端详细信息说明 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Activity :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('redis-monitor.fieldDescription')
          }}</span>
        </div>
      </template>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.clientId') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.clientIdDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.address') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.addressDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.name') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.nameDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.age') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.ageDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.idle') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.idleDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.outputBuffer') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.outputBufferDesc') }}
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>
