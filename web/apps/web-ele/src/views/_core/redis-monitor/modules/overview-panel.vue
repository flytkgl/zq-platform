<script setup lang="ts">
import type {
  RedisMonitorOverview,
  RedisRealtimeStats,
} from '#/api/core/redis-monitor';

import { computed } from 'vue';

import {
  Activity,
  Cpu,
  Database,
  HardDrive,
  Network,
  Settings,
  Users,
} from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElProgress,
  ElTag,
} from 'element-plus';

defineOptions({ name: 'OverviewPanel' });

const props = defineProps<{
  monitorData: null | RedisMonitorOverview;
  realtimeData: null | RedisRealtimeStats;
}>();

// 客户端数量（使用实际客户端列表长度）
const clientsCount = computed(() => props.monitorData?.clients?.length || 0);

// 格式化运行时间
function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86_400);
  const hours = Math.floor((seconds % 86_400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${days}${$t('redis-monitor.days')} ${hours}${$t('redis-monitor.hours')} ${minutes}${$t('redis-monitor.minutes')}`;
}

// 格式化字节大小
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(2)} ${sizes[i]}`;
}

// 获取百分比颜色
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
    <!-- 关键指标卡片 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <!-- 内存使用率 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
            <Database :size="20" class="text-blue-600 dark:text-blue-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('redis-monitor.memoryUsage')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ realtimeData?.memory_usage_percent?.toFixed(1) || '0.0' }}%
        </div>
        <ElProgress
          :percentage="
            Number(realtimeData?.memory_usage_percent?.toFixed(1) || 0)
          "
          :color="getPercentColor(realtimeData?.memory_usage_percent || 0)"
          :stroke-width="8"
        />
      </ElCard>

      <!-- 连接客户端数 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-green-100 p-2 dark:bg-green-900/30">
            <Users :size="20" class="text-green-600 dark:text-green-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('redis-monitor.connectedClients')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ clientsCount }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('redis-monitor.currentConnections') }}
        </div>
      </ElCard>

      <!-- 每秒操作数 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
            <Activity :size="20" class="text-purple-600 dark:text-purple-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('redis-monitor.opsPerSec')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ realtimeData?.ops_per_sec?.toLocaleString() || 0 }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">OPS</div>
      </ElCard>

      <!-- 命中率 -->
      <ElCard shadow="hover">
        <div class="mb-3 flex items-center gap-2">
          <div class="rounded-lg bg-orange-100 p-2 dark:bg-orange-900/30">
            <Activity :size="20" class="text-orange-600 dark:text-orange-400" />
          </div>
          <span class="text-sm font-medium text-gray-600 dark:text-gray-400">{{
            $t('redis-monitor.hitRate')
          }}</span>
        </div>
        <div class="mb-2 text-3xl font-bold">
          {{ realtimeData?.hit_rate?.toFixed(2) || '0.00' }}%
        </div>
        <ElProgress
          :percentage="Number(realtimeData?.hit_rate?.toFixed(1) || 0)"
          :color="getPercentColor(realtimeData?.hit_rate || 0)"
          :stroke-width="8"
        />
      </ElCard>
    </div>

    <!-- Redis基础信息 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Settings :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('redis-monitor.redisBasicInfo')
          }}</span>
        </div>
      </template>

      <ElDescriptions :column="3" border size="default">
        <ElDescriptionsItem :label="$t('redis-monitor.redisVersion')">
          <ElTag type="primary">
            {{ monitorData?.info?.redis_version || '-' }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('redis-monitor.redisMode')">
          <ElTag type="success">
            {{ monitorData?.info?.redis_mode || '-' }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('redis-monitor.role')">
          <ElTag
            :type="monitorData?.info?.role === 'master' ? 'danger' : 'info'"
          >
            {{ monitorData?.info?.role || '-' }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('redis-monitor.os')">
          {{ monitorData?.info?.os || '-' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('redis-monitor.architecture')">
          {{ monitorData?.info?.arch_bits || 0 }} {{ $t('redis-monitor.bits') }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('redis-monitor.tcpPort')">
          {{ monitorData?.info?.tcp_port || 0 }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('redis-monitor.uptime')">
          {{ formatUptime(monitorData?.info?.uptime_in_seconds || 0) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('redis-monitor.uptimeInDays')">
          {{ monitorData?.info?.uptime_in_days || 0 }}
          {{ $t('redis-monitor.days') }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('redis-monitor.connectionStatus')">
          <ElTag
            :type="monitorData?.status === 'connected' ? 'success' : 'danger'"
          >
            {{
              monitorData?.status === 'connected'
                ? $t('redis-monitor.connected')
                : $t('redis-monitor.disconnected')
            }}
          </ElTag>
        </ElDescriptionsItem>
      </ElDescriptions>
    </ElCard>

    <!-- 内存信息概览 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center gap-2">
          <Database :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('redis-monitor.memoryInfo')
          }}</span>
        </div>
      </template>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <ElDescriptions :column="1" border size="default">
            <ElDescriptionsItem :label="$t('redis-monitor.usedMemory')">
              {{ monitorData?.memory?.used_memory_human || '-' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="$t('redis-monitor.rssMemory')">
              {{ formatBytes(monitorData?.memory?.used_memory_rss || 0) }}
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="$t('redis-monitor.memoryPeak')">
              {{ monitorData?.memory?.used_memory_peak_human || '-' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="$t('redis-monitor.totalSystemMemory')">
              {{ monitorData?.memory?.total_system_memory_human || '-' }}
            </ElDescriptionsItem>
          </ElDescriptions>
        </div>
        <div>
          <ElDescriptions :column="1" border size="default">
            <ElDescriptionsItem :label="$t('redis-monitor.datasetMemory')">
              {{ formatBytes(monitorData?.memory?.used_memory_dataset || 0) }}
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="$t('redis-monitor.maxMemoryLimit')">
              {{
                monitorData?.memory?.maxmemory_human ||
                $t('redis-monitor.noLimit')
              }}
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="$t('redis-monitor.memoryPolicy')">
              <ElTag type="info">
                {{ monitorData?.memory?.maxmemory_policy || '-' }}
              </ElTag>
            </ElDescriptionsItem>
            <ElDescriptionsItem :label="$t('redis-monitor.fragmentationRatio')">
              <ElTag
                :type="
                  (monitorData?.memory?.mem_fragmentation_ratio || 0) > 1.5
                    ? 'warning'
                    : 'success'
                "
              >
                {{
                  monitorData?.memory?.mem_fragmentation_ratio?.toFixed(2) ||
                  '0.00'
                }}
              </ElTag>
            </ElDescriptionsItem>
          </ElDescriptions>
        </div>
      </div>
    </ElCard>

    <!-- 统计信息 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <!-- 连接统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Activity :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.connectionStats')
            }}</span>
          </div>
        </template>

        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.totalConnections')
            }}</span>
            <span class="font-semibold">{{
              monitorData?.stats?.total_connections_received?.toLocaleString() ||
              0
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.connectedClients')
            }}</span>
            <span class="font-semibold">{{ clientsCount }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.blockedClients')
            }}</span>
            <span class="font-semibold">{{
              monitorData?.info?.blocked_clients || 0
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.rejectedConnections')
            }}</span>
            <span class="font-semibold text-red-600">{{
              monitorData?.stats?.rejected_connections?.toLocaleString() || 0
            }}</span>
          </div>
        </div>
      </ElCard>

      <!-- 命令统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Cpu :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.commandStats')
            }}</span>
          </div>
        </template>

        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.totalCommands')
            }}</span>
            <span class="font-semibold">{{
              monitorData?.stats?.total_commands_processed?.toLocaleString() ||
              0
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.opsPerSec')
            }}</span>
            <span class="font-semibold text-green-600">{{
              monitorData?.stats?.instantaneous_ops_per_sec?.toLocaleString() ||
              0
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.keyspaceHits')
            }}</span>
            <span class="font-semibold text-green-600">{{
              monitorData?.stats?.keyspace_hits?.toLocaleString() || 0
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.keyspaceMisses')
            }}</span>
            <span class="font-semibold text-red-600">{{
              monitorData?.stats?.keyspace_misses?.toLocaleString() || 0
            }}</span>
          </div>
        </div>
      </ElCard>
    </div>

    <!-- 键空间信息 -->
    <ElCard
      v-if="monitorData?.keyspace && monitorData.keyspace.length > 0"
      shadow="hover"
    >
      <template #header>
        <div class="flex items-center gap-2">
          <HardDrive :size="18" class="text-primary" />
          <span class="font-semibold">{{
            $t('redis-monitor.keyspaceInfo')
          }}</span>
        </div>
      </template>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <ElCard
          v-for="db in monitorData.keyspace"
          :key="db.db_id"
          shadow="hover"
          class="border border-gray-200 dark:border-gray-700"
        >
          <div class="mb-2 flex items-center justify-between">
            <span class="font-semibold">DB{{ db.db_id }}</span>
            <ElTag type="primary" size="small">
              {{ db.keys }} {{ $t('redis-monitor.keys') }}
            </ElTag>
          </div>
          <div class="space-y-1 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-gray-600 dark:text-gray-400"
                >{{ $t('redis-monitor.expires') }}:</span
              >
              <span>{{ db.expires }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-600 dark:text-gray-400"
                >{{ $t('redis-monitor.avgTTL') }}:</span
              >
              <span>{{ db.avg_ttl }}ms</span>
            </div>
          </div>
        </ElCard>
      </div>
    </ElCard>

    <!-- 网络IO统计 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <!-- 输入统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Network :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.networkInput')
            }}</span>
          </div>
        </template>

        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.totalNetInput')
            }}</span>
            <span class="font-semibold">{{
              formatBytes(monitorData?.stats?.total_net_input_bytes || 0)
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.inputKbps')
            }}</span>
            <span class="font-semibold text-blue-600">{{
                monitorData?.stats?.instantaneous_input_kbps?.toFixed(2) ||
                '0.00'
              }}
              KB/s</span>
          </div>
        </div>
      </ElCard>

      <!-- 输出统计 -->
      <ElCard shadow="hover">
        <template #header>
          <div class="flex items-center gap-2">
            <Network :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.networkOutput')
            }}</span>
          </div>
        </template>

        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.totalNetOutput')
            }}</span>
            <span class="font-semibold">{{
              formatBytes(monitorData?.stats?.total_net_output_bytes || 0)
            }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">{{
              $t('redis-monitor.outputKbps')
            }}</span>
            <span class="font-semibold text-green-600">{{
                monitorData?.stats?.instantaneous_output_kbps?.toFixed(2) ||
                '0.00'
              }}
              KB/s</span>
          </div>
        </div>
      </ElCard>
    </div>
  </div>
</template>
