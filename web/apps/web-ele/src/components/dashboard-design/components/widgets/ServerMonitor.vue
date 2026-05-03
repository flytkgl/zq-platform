<script setup lang="ts">
import type {
  RealtimeStats,
  ServerMonitorResponse,
} from '#/api/core/server-monitor';
import type { DashboardWidget } from '#/components/dashboard-design';

import { computed, onMounted, onUnmounted, ref } from 'vue';

import { Cpu, Database, HardDrive, Network } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElProgress } from 'element-plus';

import {
  getRealtimeStatsApi,
  getServerOverviewApi,
} from '#/api/core/server-monitor';

const props = defineProps<{
  widget: DashboardWidget;
}>();

const loading = ref(false);
const serverData = ref<null | ServerMonitorResponse>(null);
const realtimeData = ref<null | RealtimeStats>(null);
let timer: null | ReturnType<typeof setInterval> = null;

// 刷新间隔
const refreshInterval = computed(
  () => props.widget.props.refreshInterval || 5000,
);

// 区域背景色
function getAreaStyle(colorProp: string) {
  const color = props.widget.props[colorProp];
  if (!color) return {};
  if (color.includes('gradient')) return { background: color };
  return { backgroundColor: color };
}

// 格式化字节
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(1)} ${sizes[i]}`;
}

// 格式化内存（后端返回 GB）
function formatMemory(gb: number): string {
  if (gb === 0) return '0 GB';
  if (gb < 1) return `${(gb * 1024).toFixed(0)} MB`;
  return `${gb.toFixed(1)} GB`;
}

// 格式化速度
function formatSpeed(bytesPerSecond: number): string {
  return `${formatBytes(bytesPerSecond)}/s`;
}

// 使用率颜色
function getProgressColor(percent: number): string {
  if (percent >= 90) return 'var(--el-color-danger)';
  if (percent >= 70) return 'var(--el-color-warning)';
  return 'var(--el-color-success)';
}

// 格式化运行时间
function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86_400);
  const hours = Math.floor((seconds % 86_400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const parts = [];
  if (days > 0)
    parts.push(`${days}${$t('dashboard-design.widgets.serverMonitor.days')}`);
  if (hours > 0)
    parts.push(`${hours}${$t('dashboard-design.widgets.serverMonitor.hours')}`);
  if (minutes > 0)
    parts.push(
      `${minutes}${$t('dashboard-design.widgets.serverMonitor.minutes')}`,
    );
  return parts.join(' ') || '-';
}

// 加载数据
async function loadData(showLoading = false) {
  if (showLoading) loading.value = true;
  try {
    const [overview, realtime] = await Promise.all([
      getServerOverviewApi(),
      getRealtimeStatsApi(),
    ]);
    serverData.value = overview;
    realtimeData.value = realtime;
  } catch (error) {
    console.error('Failed to load server monitor data:', error);
  } finally {
    if (showLoading) loading.value = false;
  }
}

// 自动刷新
function startAutoRefresh() {
  if (timer) return;
  timer = setInterval(() => {
    getRealtimeStatsApi()
      .then((data) => {
        realtimeData.value = data;
      })
      .catch(() => {});
  }, refreshInterval.value);
}

function stopAutoRefresh() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}

onMounted(async () => {
  await loadData(true);
  startAutoRefresh();
});

onUnmounted(() => {
  stopAutoRefresh();
});
</script>

<template>
  <div class="server-monitor flex h-full flex-col p-4" v-loading="loading">
    <!-- 头部 -->
    <div class="mb-6 flex items-center justify-between">
      <span class="text-sm font-medium">{{ widget.props.title }}</span>
      <span class="text-muted-foreground text-xs">
        {{ serverData?.basic_info?.hostname || '-' }}
        ({{ serverData?.basic_info?.ip_address || '-' }})
      </span>
    </div>

    <!-- 指标网格 -->
    <div class="grid max-h-[150px] flex-1 grid-cols-2 gap-3 lg:grid-cols-4">
      <!-- CPU -->
      <div
        class="flex flex-col justify-between rounded-lg p-4"
        :class="{ 'bg-secondary/50': !widget.props.cpuBgColor }"
        :style="getAreaStyle('cpuBgColor')"
      >
        <div class="mb-2 flex items-center gap-2">
          <div
            class="flex h-7 w-7 items-center justify-center rounded-md"
            style="background: rgba(59, 130, 246, 0.15)"
          >
            <Cpu class="h-4 w-4" style="color: var(--el-color-primary)" />
          </div>
          <span class="text-muted-foreground text-xs">CPU</span>
        </div>
        <div class="mb-1 text-xl font-bold">
          {{ realtimeData?.cpu_percent?.toFixed(1) || '0.0' }}%
        </div>
        <ElProgress
          :percentage="Number(realtimeData?.cpu_percent?.toFixed(1) || 0)"
          :color="getProgressColor(realtimeData?.cpu_percent || 0)"
          :show-text="false"
          :stroke-width="4"
        />
        <div class="text-muted-foreground mt-1 text-xs">
          {{ serverData?.cpu_info?.physical_cores || 0
          }}{{ $t('dashboard-design.widgets.serverMonitor.core') }}
          {{ serverData?.cpu_info?.total_cores || 0
          }}{{ $t('dashboard-design.widgets.serverMonitor.thread') }}
        </div>
      </div>

      <!-- 内存 -->
      <div
        class="flex flex-col justify-between rounded-lg p-4"
        :class="{ 'bg-secondary/50': !widget.props.memoryBgColor }"
        :style="getAreaStyle('memoryBgColor')"
      >
        <div class="mb-2 flex items-center gap-2">
          <div
            class="flex h-7 w-7 items-center justify-center rounded-md"
            style="background: rgba(34, 197, 94, 0.15)"
          >
            <Database class="h-4 w-4" style="color: var(--el-color-success)" />
          </div>
          <span class="text-muted-foreground text-xs">{{
            $t('dashboard-design.widgets.serverMonitor.memory')
          }}</span>
        </div>
        <div class="mb-1 text-xl font-bold">
          {{ realtimeData?.memory_percent?.toFixed(1) || '0.0' }}%
        </div>
        <ElProgress
          :percentage="Number(realtimeData?.memory_percent?.toFixed(1) || 0)"
          :color="getProgressColor(realtimeData?.memory_percent || 0)"
          :show-text="false"
          :stroke-width="4"
        />
        <div class="text-muted-foreground mt-1 text-xs">
          {{ formatMemory(realtimeData?.memory_details?.used || 0) }}
          / {{ formatMemory(realtimeData?.memory_details?.total || 0) }}
        </div>
      </div>

      <!-- 磁盘 -->
      <div
        class="flex flex-col justify-between rounded-lg p-4"
        :class="{ 'bg-secondary/50': !widget.props.diskBgColor }"
        :style="getAreaStyle('diskBgColor')"
      >
        <div class="mb-2 flex items-center gap-2">
          <div
            class="flex h-7 w-7 items-center justify-center rounded-md"
            style="background: rgba(139, 92, 246, 0.15)"
          >
            <HardDrive class="h-4 w-4" style="color: var(--el-color-warning)" />
          </div>
          <span class="text-muted-foreground text-xs">{{
            $t('dashboard-design.widgets.serverMonitor.disk')
          }}</span>
        </div>
        <div class="space-y-0.5 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground text-xs">{{
              $t('dashboard-design.widgets.serverMonitor.read')
            }}</span>
            <span class="text-xs font-medium">{{
              formatSpeed(realtimeData?.disk_io?.read_speed || 0)
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground text-xs">{{
              $t('dashboard-design.widgets.serverMonitor.write')
            }}</span>
            <span class="text-xs font-medium">{{
              formatSpeed(realtimeData?.disk_io?.write_speed || 0)
            }}</span>
          </div>
        </div>
        <div class="text-muted-foreground mt-1 text-xs">
          {{ $t('dashboard-design.widgets.serverMonitor.totalRW') }}:
          {{ formatBytes(realtimeData?.disk_total?.read_bytes || 0) }} /
          {{ formatBytes(realtimeData?.disk_total?.write_bytes || 0) }}
        </div>
      </div>

      <!-- 网络 -->
      <div
        class="flex flex-col justify-between rounded-lg p-4"
        :class="{ 'bg-secondary/50': !widget.props.networkBgColor }"
        :style="getAreaStyle('networkBgColor')"
      >
        <div class="mb-2 flex items-center gap-2">
          <div
            class="flex h-7 w-7 items-center justify-center rounded-md"
            style="background: rgba(249, 115, 22, 0.15)"
          >
            <Network class="h-4 w-4" style="color: var(--el-color-danger)" />
          </div>
          <span class="text-muted-foreground text-xs">{{
            $t('dashboard-design.widgets.serverMonitor.network')
          }}</span>
        </div>
        <div class="space-y-0.5 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground text-xs">{{
              $t('dashboard-design.widgets.serverMonitor.upload')
            }}</span>
            <span class="text-xs font-medium">{{
              formatSpeed(realtimeData?.network_io?.upload_speed || 0)
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground text-xs">{{
              $t('dashboard-design.widgets.serverMonitor.download')
            }}</span>
            <span class="text-xs font-medium">{{
              formatSpeed(realtimeData?.network_io?.download_speed || 0)
            }}</span>
          </div>
        </div>
        <div class="text-muted-foreground mt-1 text-xs">
          {{ $t('dashboard-design.widgets.serverMonitor.uptime') }}:
          {{ formatUptime(serverData?.boot_time?.uptime_seconds || 0) }}
        </div>
      </div>
    </div>
  </div>
</template>
