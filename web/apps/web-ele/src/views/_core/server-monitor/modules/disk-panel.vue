<script setup lang="ts">
import type {
  RealtimeStats as RealtimeStatsType,
  ServerMonitorResponse,
} from '#/api/core/server-monitor';

import { HardDrive } from '@vben/icons';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElProgress,
  ElTag,
} from 'element-plus';

defineOptions({ name: 'DiskPanel' });

defineProps<{
  realtimeData: null | RealtimeStatsType;
  serverData: null | ServerMonitorResponse;
}>();

// 格式化字节大小（用于速度等真实字节数据）
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(2)} ${sizes[i]}`;
}

// 格式化磁盘大小（后端返回的是GB）
function formatDiskSize(gb: number): string {
  if (gb === 0) return '0 GB';
  if (gb < 1) {
    return `${(gb * 1024).toFixed(2)} MB`;
  }
  if (gb >= 1024) {
    return `${(gb / 1024).toFixed(2)} TB`;
  }
  return `${gb.toFixed(2)} GB`;
}

// 格式化速度
function formatSpeed(bytesPerSecond: number): string {
  return `${formatBytes(bytesPerSecond)}/s`;
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
    <!-- 磁盘IO概览 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <!-- 读取速度 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
            <HardDrive :size="20" class="text-blue-600 dark:text-blue-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.readSpeed')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatSpeed(realtimeData?.disk_io?.read_speed || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.currentReadRate') }}
        </div>
      </ElCard>

      <!-- 写入速度 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
            <HardDrive :size="20" class="text-green-600 dark:text-green-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.writeSpeed')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatSpeed(realtimeData?.disk_io?.write_speed || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.currentWriteRate') }}
        </div>
      </ElCard>

      <!-- 总读取 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
            <HardDrive
              :size="20"
              class="text-purple-600 dark:text-purple-400"
            />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.totalRead')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatBytes(realtimeData?.disk_total?.read_bytes || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.accumulatedReadData') }}
        </div>
      </ElCard>

      <!-- 总写入 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-orange-100 p-2 dark:bg-orange-900/30">
            <HardDrive
              :size="20"
              class="text-orange-600 dark:text-orange-400"
            />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('server-monitor.totalWrite')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ formatBytes(realtimeData?.disk_total?.write_bytes || 0) }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.accumulatedWriteData') }}
        </div>
      </ElCard>
    </div>

    <!-- 磁盘分区列表 -->
    <div class="grid grid-cols-1 gap-4">
      <ElCard
        v-for="(partition, index) in serverData?.disk_info?.partitions || []"
        :key="index"
        shadow="hover"
      >
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <HardDrive :size="18" class="text-primary" />
              <span class="font-semibold">{{ partition.mountpoint }}</span>
              <ElTag size="small" type="info">
                {{ partition.file_system }}
              </ElTag>
            </div>
            <ElTag :type="getPercentColor(partition.percent)" size="small">
              {{ partition.percent.toFixed(1) }}%
              {{ $t('server-monitor.used') }}
            </ElTag>
          </div>
        </template>

        <div class="mb-4">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('server-monitor.diskUsage')
            }}</span>
            <span class="text-sm font-medium">
              {{ formatDiskSize(partition.used) }} /
              {{ formatDiskSize(partition.total_size) }}
            </span>
          </div>
          <ElProgress
            :percentage="Number(partition.percent.toFixed(1))"
            :color="getPercentColor(partition.percent)"
            :stroke-width="8"
          >
            <template #default="{ percentage }">
              <span class="text-xs">{{ percentage }}%</span>
            </template>
          </ElProgress>
        </div>

        <ElDescriptions :column="2" border size="small">
          <ElDescriptionsItem :label="$t('server-monitor.device')">
            {{ partition.device }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.mountPoint')">
            {{ partition.mountpoint }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.fileSystem')">
            {{ partition.file_system }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.usageRate')">
            <ElTag :type="getPercentColor(partition.percent)">
              {{ partition.percent.toFixed(2) }}%
            </ElTag>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.totalCapacity')">
            {{ formatDiskSize(partition.total_size) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.used')">
            {{ formatDiskSize(partition.used) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.availableSpace')">
            {{ formatDiskSize(partition.free) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.remainingSpace')">
            {{ formatDiskSize(partition.free) }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </div>

    <!-- 磁盘IO统计 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <HardDrive :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.diskIoStats')
          }}</span>
        </div>
      </template>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <!-- 读取统计 -->
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-3 flex items-center gap-2">
            <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
              <HardDrive :size="16" class="text-blue-600 dark:text-blue-400" />
            </div>
            <span class="font-medium">{{
              $t('server-monitor.readStats')
            }}</span>
          </div>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.currentSpeed') }}:</span
              >
              <span class="font-semibold">{{
                formatSpeed(realtimeData?.disk_io?.read_speed || 0)
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.totalReadAmount') }}:</span
              >
              <span class="font-semibold">{{
                formatDiskSize(serverData?.disk_info?.total_read_bytes || 0)
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.readCount') }}:</span
              >
              <span class="font-semibold">{{
                (serverData?.disk_info?.total_read_count || 0).toLocaleString()
              }}</span>
            </div>
            <div
              v-if="serverData?.disk_info?.total_read_time !== undefined"
              class="flex items-center justify-between"
            >
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.readTime') }}:</span
              >
              <span class="font-semibold"
                >{{ (serverData.disk_info.total_read_time / 1000).toFixed(2) }}
                {{ $t('server-monitor.seconds') }}</span
              >
            </div>
          </div>
        </div>

        <!-- 写入统计 -->
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-3 flex items-center gap-2">
            <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
              <HardDrive
                :size="16"
                class="text-green-600 dark:text-green-400"
              />
            </div>
            <span class="font-medium">{{
              $t('server-monitor.writeStats')
            }}</span>
          </div>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.currentSpeed') }}:</span
              >
              <span class="font-semibold">{{
                formatSpeed(realtimeData?.disk_io?.write_speed || 0)
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.totalWriteAmount') }}:</span
              >
              <span class="font-semibold">{{
                formatDiskSize(serverData?.disk_info?.total_write_bytes || 0)
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.writeCount') }}:</span
              >
              <span class="font-semibold">{{
                (serverData?.disk_info?.total_write_count || 0).toLocaleString()
              }}</span>
            </div>
            <div
              v-if="serverData?.disk_info?.total_write_time !== undefined"
              class="flex items-center justify-between"
            >
              <span class="text-sm text-gray-600 dark:text-gray-400"
                >{{ $t('server-monitor.writeTime') }}:</span
              >
              <span class="font-semibold"
                >{{ (serverData.disk_info.total_write_time / 1000).toFixed(2) }}
                {{ $t('server-monitor.seconds') }}</span
              >
            </div>
          </div>
        </div>
      </div>
    </ElCard>

    <!-- 实时磁盘IO -->
    <ElCard v-if="realtimeData?.disk_io" shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <HardDrive :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.realtimeDiskIo')
          }}</span>
        </div>
      </template>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
            {{ $t('server-monitor.readSpeed') }}
          </div>
          <div class="mb-2 text-2xl font-bold text-blue-600 dark:text-blue-400">
            {{ formatSpeed(realtimeData.disk_io.read_speed || 0) }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            {{ $t('server-monitor.currentReadRate') }}
          </div>
        </div>

        <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
            {{ $t('server-monitor.writeSpeed') }}
          </div>
          <div
            class="mb-2 text-2xl font-bold text-green-600 dark:text-green-400"
          >
            {{ formatSpeed(realtimeData.disk_io.write_speed || 0) }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            {{ $t('server-monitor.currentWriteRate') }}
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>
