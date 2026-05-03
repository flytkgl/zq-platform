<script setup lang="ts">
import type {
  RealtimeStats as RealtimeStatsType,
  ServerMonitorResponse,
} from '#/api/core/server-monitor';

import { Network } from '@vben/icons';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElTag,
} from 'element-plus';

defineOptions({ name: 'NetworkPanel' });

defineProps<{
  realtimeData: null | RealtimeStatsType;
  serverData: null | ServerMonitorResponse;
}>();

// 格式化字节大小
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(2)} ${sizes[i]}`;
}

// 格式化速度
function formatSpeed(bytesPerSecond: number): string {
  return `${formatBytes(bytesPerSecond)}/s`;
}
</script>

<template>
  <div class="space-y-4">
    <!-- 网络IO概览 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <!-- 上传速度 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
            <Network :size="20" class="text-blue-600 dark:text-blue-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.uploadSpeed')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatSpeed(realtimeData?.network_io?.upload_speed || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.currentUploadRate') }}
        </div>
      </ElCard>

      <!-- 下载速度 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
            <Network :size="20" class="text-green-600 dark:text-green-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.downloadSpeed')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatSpeed(realtimeData?.network_io?.download_speed || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.currentDownloadRate') }}
        </div>
      </ElCard>

      <!-- 总发送 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
            <Network :size="20" class="text-purple-600 dark:text-purple-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.totalSent')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatBytes(realtimeData?.network_total?.bytes_sent || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.accumulatedSentData') }}
        </div>
      </ElCard>

      <!-- 总接收 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-orange-100 p-2 dark:bg-orange-900/30">
            <Network :size="20" class="text-orange-600 dark:text-orange-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.totalReceived')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatBytes(realtimeData?.network_total?.bytes_recv || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.accumulatedReceivedData') }}
        </div>
      </ElCard>
    </div>

    <!-- 网络接口列表 -->
    <div class="grid grid-cols-1 gap-4">
      <ElCard
        v-for="(interfaceData, interfaceName) in serverData?.network_info
          ?.interfaces || {}"
        :key="interfaceName"
        shadow="hover"
      >
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Network :size="18" class="text-primary" />
              <span class="font-semibold">{{ interfaceName }}</span>
              <ElTag
                v-if="interfaceData.stats?.is_up"
                type="success"
                size="small"
              >
                {{ $t('server-monitor.online') }}
              </ElTag>
              <ElTag v-else type="info" size="small">
                {{ $t('server-monitor.offline') }}
              </ElTag>
            </div>
            <div class="flex items-center gap-2">
              <ElTag type="info" size="small">
                {{ interfaceData.stats?.speed || 0 }} Mbps
              </ElTag>
            </div>
          </div>
        </template>

        <ElDescriptions :column="2" border size="small">
          <ElDescriptionsItem :label="$t('server-monitor.interfaceName')">
            {{ interfaceName }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.status')">
            <ElTag v-if="interfaceData.stats?.is_up" type="success">
              {{ $t('server-monitor.online') }}
            </ElTag>
            <ElTag v-else type="info">{{ $t('server-monitor.offline') }}</ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.speed')">
            {{ interfaceData.stats?.speed || 0 }} Mbps
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.mtu')">
            {{ interfaceData.stats?.mtu || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.sentBytes')">
            {{
              formatBytes(
                serverData?.network_info?.per_interface?.[interfaceName]
                  ?.bytes_sent || 0,
              )
            }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.receivedBytes')">
            {{
              formatBytes(
                serverData?.network_info?.per_interface?.[interfaceName]
                  ?.bytes_recv || 0,
              )
            }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.sentPackets')">
            {{
              (
                serverData?.network_info?.per_interface?.[interfaceName]
                  ?.packets_sent || 0
              ).toLocaleString()
            }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.receivedPackets')">
            {{
              (
                serverData?.network_info?.per_interface?.[interfaceName]
                  ?.packets_recv || 0
              ).toLocaleString()
            }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.sentErrors')">
            {{
              (
                serverData?.network_info?.per_interface?.[interfaceName]
                  ?.errout || 0
              ).toLocaleString()
            }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.receivedErrors')">
            {{
              (
                serverData?.network_info?.per_interface?.[interfaceName]
                  ?.errin || 0
              ).toLocaleString()
            }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.sentDropped')">
            {{
              (
                serverData?.network_info?.per_interface?.[interfaceName]
                  ?.dropout || 0
              ).toLocaleString()
            }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.receivedDropped')">
            {{
              (
                serverData?.network_info?.per_interface?.[interfaceName]
                  ?.dropin || 0
              ).toLocaleString()
            }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </div>

    <!-- 网络总计统计 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Network :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.networkTrafficStats')
          }}</span>
        </div>
      </template>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <!-- 发送统计 -->
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-3 flex items-center gap-2">
            <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
              <Network :size="16" class="text-blue-600 dark:text-blue-400" />
            </div>
            <span class="font-medium">{{
              $t('server-monitor.sentStats')
            }}</span>
          </div>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.currentSpeed') }}:</span
              >
              <span class="font-semibold">{{
                formatSpeed(realtimeData?.network_io?.upload_speed || 0)
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.totalSentAmount') }}:</span
              >
              <span class="font-semibold">{{
                formatBytes(serverData?.network_info?.total?.bytes_sent || 0)
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.sentPackets') }}:</span
              >
              <span class="font-semibold">{{
                (
                  serverData?.network_info?.total?.packets_sent || 0
                ).toLocaleString()
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.sentErrors') }}:</span
              >
              <span class="font-semibold">{{
                (serverData?.network_info?.total?.errout || 0).toLocaleString()
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.sentDropped') }}:</span
              >
              <span class="font-semibold">{{
                (serverData?.network_info?.total?.dropout || 0).toLocaleString()
              }}</span>
            </div>
          </div>
        </div>

        <!-- 接收统计 -->
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-3 flex items-center gap-2">
            <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
              <Network :size="16" class="text-green-600 dark:text-green-400" />
            </div>
            <span class="font-medium">{{
              $t('server-monitor.receivedStats')
            }}</span>
          </div>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.currentSpeed') }}:</span
              >
              <span class="font-semibold">{{
                formatSpeed(realtimeData?.network_io?.download_speed || 0)
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.totalReceivedAmount') }}:</span
              >
              <span class="font-semibold">{{
                formatBytes(serverData?.network_info?.total?.bytes_recv || 0)
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.receivedPackets') }}:</span
              >
              <span class="font-semibold">{{
                (
                  serverData?.network_info?.total?.packets_recv || 0
                ).toLocaleString()
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.receivedErrors') }}:</span
              >
              <span class="font-semibold">{{
                (serverData?.network_info?.total?.errin || 0).toLocaleString()
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.receivedDropped') }}:</span
              >
              <span class="font-semibold">{{
                (serverData?.network_info?.total?.dropin || 0).toLocaleString()
              }}</span>
            </div>
          </div>
        </div>
      </div>
    </ElCard>

    <!-- 实时网络IO -->
    <ElCard v-if="realtimeData?.network_io" shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Network :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.realtimeNetworkIo')
          }}</span>
        </div>
      </template>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
            {{ $t('server-monitor.uploadSpeed') }}
          </div>
          <div class="mb-2 text-2xl font-bold text-blue-600 dark:text-blue-400">
            {{ formatSpeed(realtimeData.network_io.upload_speed || 0) }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            {{ $t('server-monitor.currentUploadRate') }}
          </div>
        </div>

        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
            {{ $t('server-monitor.downloadSpeed') }}
          </div>
          <div
            class="mb-2 text-2xl font-bold text-green-600 dark:text-green-400"
          >
            {{ formatSpeed(realtimeData.network_io.download_speed || 0) }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            {{ $t('server-monitor.currentDownloadRate') }}
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>
