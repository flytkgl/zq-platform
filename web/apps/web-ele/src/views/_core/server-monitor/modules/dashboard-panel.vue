<script setup lang="ts">
import type {
  RealtimeStats as RealtimeStatsType,
  ServerMonitorResponse,
} from '#/api/core/server-monitor';

import { computed, ref, watch } from 'vue';

import {
  Activity,
  Cpu,
  Database,
  HardDrive,
  Info,
  ListTree,
  Network,
} from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElProgress,
  ElTag,
} from 'element-plus';

defineOptions({ name: 'DashboardPanel' });

const props = defineProps<{
  realtimeData: null | RealtimeStatsType;
  serverData: null | ServerMonitorResponse;
}>();

// 网络使用历史数据（最多保存60个点，约3分钟数据）
interface NetworkDataPoint {
  timestamp: string;
  uploadSpeed: number; // bytes/s
  downloadSpeed: number; // bytes/s
}

const networkHistory = ref<NetworkDataPoint[]>([]);
const MAX_HISTORY_POINTS = 60;

// 鼠标悬停状态
const hoveredIndex = ref<null | number>(null);
const tooltipVisible = ref(false);
const tooltipX = ref(0);
const tooltipY = ref(0);

// 监听实时数据变化，添加到历史记录
watch(
  () => props.realtimeData,
  (newData) => {
    if (newData && newData.network_io) {
      const now = new Date();
      const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

      networkHistory.value.push({
        timestamp: timeStr,
        uploadSpeed: newData.network_io.upload_speed || 0,
        downloadSpeed: newData.network_io.download_speed || 0,
      });

      // 保持最多60个数据点
      if (networkHistory.value.length > MAX_HISTORY_POINTS) {
        networkHistory.value.shift();
      }
    }
  },
  { immediate: true },
);

// 计算图表数据
const networkChartData = computed(() => {
  if (networkHistory.value.length === 0) {
    return {
      labels: [],
      uploadValues: [],
      downloadValues: [],
      hasData: false,
    };
  }

  return {
    labels: networkHistory.value.map((d) => d.timestamp),
    uploadValues: networkHistory.value.map((d) => d.uploadSpeed),
    downloadValues: networkHistory.value.map((d) => d.downloadSpeed),
    hasData: true,
  };
});

// 格式化字节大小
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(2)} ${sizes[i]}`;
}

// 格式化内存大小（后端返回的是GB）
function formatMemory(gb: number): string {
  if (gb === 0) return '0 GB';
  if (gb < 1) {
    return `${(gb * 1024).toFixed(2)} MB`;
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

// 格式化运行时间
function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86_400);
  const hours = Math.floor((seconds % 86_400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  const parts = [];
  if (days > 0) parts.push(`${days}${$t('server-monitor.days')}`);
  if (hours > 0) parts.push(`${hours}${$t('server-monitor.hours')}`);
  if (minutes > 0) parts.push(`${minutes}${$t('server-monitor.minutes')}`);

  return parts.join(' ') || $t('server-monitor.justStarted');
}

// 处理鼠标移动事件
function handleMouseMove(event: MouseEvent) {
  const svg = event.currentTarget as SVGElement;
  const rect = svg.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const xPercent = x / rect.width;

  const dataLength = networkChartData.value.uploadValues.length;
  const index = Math.round(xPercent * (dataLength - 1));

  if (index >= 0 && index < dataLength) {
    hoveredIndex.value = index;
    tooltipVisible.value = true;
    tooltipX.value = event.clientX;
    tooltipY.value = event.clientY;
  }
}

// 处理鼠标离开事件
function handleMouseLeave() {
  tooltipVisible.value = false;
  hoveredIndex.value = null;
}
</script>

<template>
  <div class="space-y-4">
    <!-- 关键指标卡片 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <!-- CPU使用率 -->
      <ElCard shadow="hover" class="metric-card">
        <div class="mb-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
              <Cpu :size="20" class="text-blue-600 dark:text-blue-400" />
            </div>
            <span
              class="text-sm font-medium text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.cpuUsage') }}</span
            >
          </div>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ realtimeData?.cpu_percent?.toFixed(1) || '0.0' }}%
        </div>
        <ElProgress
          :percentage="Number(realtimeData?.cpu_percent?.toFixed(1) || 0)"
          :color="getPercentColor(realtimeData?.cpu_percent || 0)"
          :show-text="false"
        />
        <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {{ serverData?.cpu_info?.physical_cores || 0
          }}{{ $t('server-monitor.core') }} /
          {{ serverData?.cpu_info?.total_cores || 0
          }}{{ $t('server-monitor.threadCount') }}
        </div>
      </ElCard>

      <!-- 内存使用率 -->
      <ElCard shadow="hover" class="metric-card">
        <div class="mb-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
              <Database :size="20" class="text-green-600 dark:text-green-400" />
            </div>
            <span
              class="text-sm font-medium text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.memoryUsage') }}</span
            >
          </div>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ realtimeData?.memory_percent?.toFixed(1) || '0.0' }}%
        </div>
        <ElProgress
          :percentage="Number(realtimeData?.memory_percent?.toFixed(1) || 0)"
          :color="getPercentColor(realtimeData?.memory_percent || 0)"
          :show-text="false"
        />
        <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.used') }}:
          {{ formatMemory(realtimeData?.memory_details?.used || 0) }} /
          {{ $t('server-monitor.total') }}:
          {{ formatMemory(realtimeData?.memory_details?.total || 0) }}
        </div>
      </ElCard>

      <!-- 磁盘IO -->
      <ElCard shadow="hover" class="metric-card">
        <div class="mb-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
              <HardDrive
                :size="20"
                class="text-purple-600 dark:text-purple-400"
              />
            </div>
            <span
              class="text-sm font-medium text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.diskIo') }}</span
            >
          </div>
        </div>
        <div class="space-y-1">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.read') }}:</span
            >
            <span class="font-semibold">{{
              formatSpeed(realtimeData?.disk_io?.read_speed || 0)
            }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.write') }}:</span
            >
            <span class="font-semibold">{{
              formatSpeed(realtimeData?.disk_io?.write_speed || 0)
            }}</span>
          </div>
        </div>
        <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.totalRead') }}:
          {{ formatBytes(realtimeData?.disk_total?.read_bytes || 0) }} /
          {{ $t('server-monitor.totalWrite') }}:
          {{ formatBytes(realtimeData?.disk_total?.write_bytes || 0) }}
        </div>
      </ElCard>

      <!-- 网络IO -->
      <ElCard shadow="hover" class="metric-card">
        <div class="mb-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="rounded-lg bg-orange-100 p-2 dark:bg-orange-900/30">
              <Network
                :size="20"
                class="text-orange-600 dark:text-orange-400"
              />
            </div>
            <span
              class="text-sm font-medium text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.networkIo') }}</span
            >
          </div>
        </div>
        <div class="space-y-1">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.upload') }}:</span
            >
            <span class="font-semibold">{{
              formatSpeed(realtimeData?.network_io?.upload_speed || 0)
            }}</span>
          </div>
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.download') }}:</span
            >
            <span class="font-semibold">{{
              formatSpeed(realtimeData?.network_io?.download_speed || 0)
            }}</span>
          </div>
        </div>
        <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {{ $t('server-monitor.totalSent') }}:
          {{ formatBytes(realtimeData?.network_total?.bytes_sent || 0) }} /
          {{ $t('server-monitor.totalReceived') }}:
          {{ formatBytes(realtimeData?.network_total?.bytes_recv || 0) }}
        </div>
      </ElCard>
    </div>

    <!-- 系统信息 -->
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <!-- 基础信息 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Info :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('server-monitor.basicInfo')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('server-monitor.hostname')">
            {{ serverData?.basic_info?.hostname || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.ipAddress')">
            {{ serverData?.basic_info?.ip_address || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.os')">
            {{ serverData?.basic_info?.system || '-' }}
            {{ serverData?.basic_info?.release || '' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.architecture')">
            {{ serverData?.basic_info?.architecture || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.processor')">
            {{ serverData?.basic_info?.processor || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.pythonVersion')">
            {{ serverData?.basic_info?.python_version || '-' }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>

      <!-- 系统状态 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Activity :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('server-monitor.systemStatus')
            }}</span>
          </div>
        </template>
        <ElDescriptions :column="1" border size="small">
          <ElDescriptionsItem :label="$t('server-monitor.systemLoad')">
            <div class="flex items-center gap-2">
              <ElTag size="small" type="info">
                {{ $t('server-monitor.load1min') }}:
                {{ realtimeData?.system_load?.load_1min?.toFixed(2) || '0.00' }}
              </ElTag>
              <ElTag size="small" type="info">
                {{ $t('server-monitor.load5min') }}:
                {{ realtimeData?.system_load?.load_5min?.toFixed(2) || '0.00' }}
              </ElTag>
              <ElTag size="small" type="info">
                {{ $t('server-monitor.load15min') }}:
                {{
                  realtimeData?.system_load?.load_15min?.toFixed(2) || '0.00'
                }}
              </ElTag>
            </div>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.uptime')">
            {{ formatUptime(serverData?.boot_time?.uptime_seconds || 0) }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.startTime')">
            {{ serverData?.boot_time?.boot_time || '-' }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.processCount')">
            <div class="flex items-center gap-2">
              <ElTag size="small" type="success">
                {{ $t('server-monitor.total') }}:
                {{ realtimeData?.process_info?.total_processes || 0 }}
              </ElTag>
              <ElTag size="small" type="primary">
                {{ $t('server-monitor.running') }}:
                {{ realtimeData?.process_info?.running_processes || 0 }}
              </ElTag>
              <ElTag size="small" type="info">
                {{ $t('server-monitor.sleeping') }}:
                {{ realtimeData?.process_info?.sleeping_processes || 0 }}
              </ElTag>
            </div>
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.onlineUsers')">
            {{ serverData?.users_info?.length || 0 }}
            {{ $t('server-monitor.unitUser') }}
          </ElDescriptionsItem>
          <ElDescriptionsItem :label="$t('server-monitor.updateTime')">
            {{ realtimeData?.timestamp || '-' }}
          </ElDescriptionsItem>
        </ElDescriptions>
      </ElCard>
    </div>

    <!-- 网络使用趋势 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Network :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('server-monitor.networkUsageTrend')
            }}</span>
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {{
              $t('server-monitor.recentDataPoints', {
                count: networkHistory.length,
              })
            }}
          </div>
        </div>
      </template>

      <div
        v-if="!networkChartData.hasData"
        class="flex h-64 items-center justify-center text-gray-400"
      >
        <div class="text-center">
          <Network :size="48" class="mx-auto mb-4" />
          <p class="text-lg">{{ $t('server-monitor.waitingForData') }}</p>
          <p class="mt-2 text-sm">
            {{ $t('server-monitor.collectingNetworkData') }}
          </p>
        </div>
      </div>

      <div v-else class="relative h-64 p-4">
        <!-- Y轴标签 -->
        <div
          class="absolute left-0 top-0 flex h-full flex-col justify-between py-4 text-xs text-gray-500"
        >
          <span>{{
            formatBytes(
              Math.max(
                ...networkChartData.uploadValues,
                ...networkChartData.downloadValues,
              ),
            )
          }}</span>
          <span>{{
            formatBytes(
              Math.max(
                ...networkChartData.uploadValues,
                ...networkChartData.downloadValues,
              ) * 0.75,
            )
          }}</span>
          <span>{{
            formatBytes(
              Math.max(
                ...networkChartData.uploadValues,
                ...networkChartData.downloadValues,
              ) * 0.5,
            )
          }}</span>
          <span>{{
            formatBytes(
              Math.max(
                ...networkChartData.uploadValues,
                ...networkChartData.downloadValues,
              ) * 0.25,
            )
          }}</span>
          <span>0</span>
        </div>

        <!-- 图表区域 -->
        <div class="relative ml-20 h-full">
          <svg
            class="h-full w-full cursor-crosshair"
            viewBox="0 0 800 200"
            preserveAspectRatio="none"
            @mousemove="handleMouseMove"
            @mouseleave="handleMouseLeave"
          >
            <!-- 网格线 -->
            <line
              v-for="i in 5"
              :key="`grid-${i}`"
              :x1="0"
              :y1="(i - 1) * 50"
              :x2="800"
              :y2="(i - 1) * 50"
              stroke="currentColor"
              stroke-width="0.5"
              class="text-gray-200 dark:text-gray-700"
              stroke-dasharray="5,5"
            />

            <!-- 上传速度折线 -->
            <polyline
              :points="
                networkChartData.uploadValues
                  .map((val, idx) => {
                    const maxVal =
                      Math.max(
                        ...networkChartData.uploadValues,
                        ...networkChartData.downloadValues,
                      ) || 1;
                    const x =
                      (idx / (networkChartData.uploadValues.length - 1 || 1)) *
                      800;
                    const y = 200 - (val / maxVal) * 200;
                    return `${x},${y}`;
                  })
                  .join(' ')
              "
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="text-green-500"
            />

            <!-- 上传速度填充 -->
            <polygon
              :points="
                [
                  '0,200',
                  ...networkChartData.uploadValues.map((val, idx) => {
                    const maxVal =
                      Math.max(
                        ...networkChartData.uploadValues,
                        ...networkChartData.downloadValues,
                      ) || 1;
                    const x =
                      (idx / (networkChartData.uploadValues.length - 1 || 1)) *
                      800;
                    const y = 200 - (val / maxVal) * 200;
                    return `${x},${y}`;
                  }),
                  '800,200',
                ].join(' ')
              "
              fill="currentColor"
              class="text-green-500 opacity-10"
            />

            <!-- 下载速度折线 -->
            <polyline
              :points="
                networkChartData.downloadValues
                  .map((val, idx) => {
                    const maxVal =
                      Math.max(
                        ...networkChartData.uploadValues,
                        ...networkChartData.downloadValues,
                      ) || 1;
                    const x =
                      (idx /
                        (networkChartData.downloadValues.length - 1 || 1)) *
                      800;
                    const y = 200 - (val / maxVal) * 200;
                    return `${x},${y}`;
                  })
                  .join(' ')
              "
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="text-blue-500"
            />

            <!-- 下载速度填充 -->
            <polygon
              :points="
                [
                  '0,200',
                  ...networkChartData.downloadValues.map((val, idx) => {
                    const maxVal =
                      Math.max(
                        ...networkChartData.uploadValues,
                        ...networkChartData.downloadValues,
                      ) || 1;
                    const x =
                      (idx /
                        (networkChartData.downloadValues.length - 1 || 1)) *
                      800;
                    const y = 200 - (val / maxVal) * 200;
                    return `${x},${y}`;
                  }),
                  '800,200',
                ].join(' ')
              "
              fill="currentColor"
              class="text-blue-500 opacity-10"
            />

            <!-- 悬停指示线和数据点 -->
            <g v-if="hoveredIndex !== null">
              <!-- 垂直指示线 -->
              <line
                :x1="
                  (hoveredIndex /
                    (networkChartData.uploadValues.length - 1 || 1)) *
                  800
                "
                :y1="0"
                :x2="
                  (hoveredIndex /
                    (networkChartData.uploadValues.length - 1 || 1)) *
                  800
                "
                :y2="200"
                stroke="currentColor"
                stroke-width="1"
                stroke-dasharray="4,4"
                class="text-gray-400"
              />

              <!-- 上传数据点高亮 -->
              <circle
                :cx="
                  (hoveredIndex /
                    (networkChartData.uploadValues.length - 1 || 1)) *
                  800
                "
                :cy="
                  200 -
                  ((networkChartData.uploadValues[hoveredIndex] || 0) /
                    (Math.max(
                      ...networkChartData.uploadValues,
                      ...networkChartData.downloadValues,
                    ) || 1)) *
                    200
                "
                r="5"
                fill="currentColor"
                class="text-green-500"
                stroke="white"
                stroke-width="2"
              />

              <!-- 下载数据点高亮 -->
              <circle
                :cx="
                  (hoveredIndex /
                    (networkChartData.downloadValues.length - 1 || 1)) *
                  800
                "
                :cy="
                  200 -
                  ((networkChartData.downloadValues[hoveredIndex] || 0) /
                    (Math.max(
                      ...networkChartData.uploadValues,
                      ...networkChartData.downloadValues,
                    ) || 1)) *
                    200
                "
                r="5"
                fill="currentColor"
                class="text-blue-500"
                stroke="white"
                stroke-width="2"
              />
            </g>
          </svg>

          <!-- 悬停提示框 -->
          <Teleport to="body">
            <div
              v-if="tooltipVisible && hoveredIndex !== null"
              class="fixed z-50 rounded-lg border border-gray-200 bg-white px-3 py-2 shadow-lg dark:border-gray-700 dark:bg-gray-800"
              :style="{
                left: `${tooltipX + 10}px`,
                top: `${tooltipY + 10}px`,
              }"
            >
              <div
                class="mb-1 text-xs font-semibold text-gray-600 dark:text-gray-400"
              >
                {{ networkChartData.labels[hoveredIndex] }}
              </div>
              <div class="flex items-center gap-2 text-sm">
                <div class="h-2 w-2 rounded-full bg-green-500"></div>
                <span class="text-gray-700 dark:text-gray-300"
                  >{{ $t('server-monitor.upload') }}:</span
                >
                <span class="font-semibold text-green-600">{{
                  formatSpeed(networkChartData.uploadValues[hoveredIndex] || 0)
                }}</span>
              </div>
              <div class="mt-1 flex items-center gap-2 text-sm">
                <div class="h-2 w-2 rounded-full bg-blue-500"></div>
                <span class="text-gray-700 dark:text-gray-300"
                  >{{ $t('server-monitor.download') }}:</span
                >
                <span class="font-semibold text-blue-600">{{
                  formatSpeed(
                    networkChartData.downloadValues[hoveredIndex] || 0,
                  )
                }}</span>
              </div>
            </div>
          </Teleport>
        </div>

        <!-- X轴时间标签 -->
        <div class="ml-20 mt-2 flex justify-between text-xs text-gray-500">
          <span>{{ networkChartData.labels[0] || '-' }}</span>
          <span>{{
            networkChartData.labels[
              Math.floor(networkChartData.labels.length / 2)
            ] || '-'
          }}</span>
          <span>{{
            networkChartData.labels[networkChartData.labels.length - 1] || '-'
          }}</span>
        </div>

        <!-- 图例和统计 -->
        <div class="mt-4 flex items-center justify-center gap-6 text-sm">
          <div class="flex items-center gap-2">
            <div class="h-3 w-3 rounded-full bg-green-500"></div>
            <span class="text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.upload') }}:</span
            >
            <span class="font-semibold">{{
              formatSpeed(
                networkChartData.uploadValues[
                  networkChartData.uploadValues.length - 1
                ] || 0,
              )
            }}</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="h-3 w-3 rounded-full bg-blue-500"></div>
            <span class="text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.download') }}:</span
            >
            <span class="font-semibold">{{
              formatSpeed(
                networkChartData.downloadValues[
                  networkChartData.downloadValues.length - 1
                ] || 0,
              )
            }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.peakUpload') }}:</span
            >
            <span class="font-semibold text-green-600">{{
              formatSpeed(Math.max(...networkChartData.uploadValues))
            }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-gray-600 dark:text-gray-400"
              >{{ $t('server-monitor.peakDownload') }}:</span
            >
            <span class="font-semibold text-blue-600">{{
              formatSpeed(Math.max(...networkChartData.downloadValues))
            }}</span>
          </div>
        </div>
      </div>
    </ElCard>

    <!-- 进程信息 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <ListTree :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('server-monitor.top10Processes')
          }}</span>
        </div>
      </template>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th
                class="px-4 py-2 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                PID
              </th>
              <th
                class="px-4 py-2 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('server-monitor.processName') }}
              </th>
              <th
                class="px-4 py-2 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                CPU %
              </th>
              <th
                class="px-4 py-2 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                内存 %
              </th>
              <th
                class="px-4 py-2 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('server-monitor.status') }}
              </th>
              <th
                class="px-4 py-2 text-left font-medium text-gray-600 dark:text-gray-400"
              >
                {{ $t('server-monitor.createTime') }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="process in realtimeData?.process_info?.top_processes || []"
              :key="process.pid"
              class="hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <td class="px-4 py-2">{{ process.pid }}</td>
              <td class="px-4 py-2 font-medium">{{ process.name }}</td>
              <td class="px-4 py-2">
                <ElTag
                  :type="getPercentColor(process.cpu_percent)"
                  size="small"
                >
                  {{ process.cpu_percent.toFixed(1) }}%
                </ElTag>
              </td>
              <td class="px-4 py-2">
                <ElTag
                  :type="getPercentColor(process.memory_percent)"
                  size="small"
                >
                  {{ process.memory_percent.toFixed(1) }}%
                </ElTag>
              </td>
              <td class="px-4 py-2">
                <ElTag size="small" type="info">{{ process.status }}</ElTag>
              </td>
              <td class="px-4 py-2 text-gray-600 dark:text-gray-400">
                {{ process.create_time }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </ElCard>
  </div>
</template>
