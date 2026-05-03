<script setup lang="ts">
import type {
  RedisMonitorOverview,
  RedisRealtimeStats,
} from '#/api/core/redis-monitor';

import { computed } from 'vue';

import { Activity, Database, Key } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElCard, ElEmpty, ElProgress, ElTag } from 'element-plus';

defineOptions({ name: 'KeyspacePanel' });

const props = defineProps<{
  monitorData: null | RedisMonitorOverview;
  realtimeData: null | RedisRealtimeStats;
}>();

// 键空间列表
const keyspaces = computed(() => props.monitorData?.keyspace || []);

// 总键数
const totalKeys = computed(() => {
  return keyspaces.value.reduce((sum, db) => sum + db.keys, 0);
});

// 总过期键数
const totalExpires = computed(() => {
  return keyspaces.value.reduce((sum, db) => sum + db.expires, 0);
});

// 平均TTL
const avgTTL = computed(() => {
  if (keyspaces.value.length === 0) return 0;
  const totalTTL = keyspaces.value.reduce((sum, db) => sum + db.avg_ttl, 0);
  return Math.round(totalTTL / keyspaces.value.length);
});

// 格式化时间（毫秒转为可读格式）
function formatTTL(ms: number): string {
  if (ms === 0) return $t('redis-monitor.permanent');
  if (ms < 1000) return `${ms}${$t('redis-monitor.milliseconds')}`;
  if (ms < 60_000)
    return `${Math.floor(ms / 1000)}${$t('redis-monitor.seconds')}`;
  if (ms < 3_600_000)
    return `${Math.floor(ms / 60_000)}${$t('redis-monitor.minutes')}`;
  if (ms < 86_400_000)
    return `${Math.floor(ms / 3_600_000)}${$t('redis-monitor.hours')}`;
  return `${Math.floor(ms / 86_400_000)}${$t('redis-monitor.days')}`;
}

// 获取过期率颜色
function getExpireRateColor(
  expires: number,
  total: number,
): 'danger' | 'info' | 'success' | 'warning' {
  if (total === 0) return 'info';
  const rate = (expires / total) * 100;
  if (rate >= 80) return 'success';
  if (rate >= 50) return 'warning';
  if (rate >= 20) return 'info';
  return 'danger';
}

// 获取数据库使用率
function getDbUsagePercent(keys: number): number {
  // 假设每个数据库最大容量为1000万个键
  const maxKeys = 10_000_000;
  return Math.min((keys / maxKeys) * 100, 100);
}

// 获取使用率颜色
function getUsageColor(percent: number): 'danger' | 'success' | 'warning' {
  if (percent >= 80) return 'danger';
  if (percent >= 50) return 'warning';
  return 'success';
}
</script>

<template>
  <div class="space-y-4">
    <!-- 键空间统计卡片 -->
    <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
      <!-- 总键数 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.totalKeys') }}
            </div>
            <div class="text-3xl font-bold">
              {{ totalKeys.toLocaleString() }}
            </div>
          </div>
          <div class="rounded-lg bg-blue-100 p-3 dark:bg-blue-900/30">
            <Key :size="32" class="text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </ElCard>

      <!-- 过期键数 -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.expiresKeys') }}
            </div>
            <div class="text-3xl font-bold">
              {{ totalExpires.toLocaleString() }}
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ $t('redis-monitor.proportion') }}:
              {{
                totalKeys > 0
                  ? ((totalExpires / totalKeys) * 100).toFixed(1)
                  : 0
              }}%
            </div>
          </div>
          <div class="rounded-lg bg-orange-100 p-3 dark:bg-orange-900/30">
            <Activity :size="32" class="text-orange-600 dark:text-orange-400" />
          </div>
        </div>
      </ElCard>

      <!-- 平均TTL -->
      <ElCard shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <div class="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {{ $t('redis-monitor.avgTTL') }}
            </div>
            <div class="text-3xl font-bold">
              {{ formatTTL(avgTTL) }}
            </div>
          </div>
          <div class="rounded-lg bg-green-100 p-3 dark:bg-green-900/30">
            <Database :size="32" class="text-green-600 dark:text-green-400" />
          </div>
        </div>
      </ElCard>
    </div>

    <!-- 数据库列表 -->
    <ElCard shadow="hover">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Database :size="18" class="text-primary" />
            <span class="font-semibold">{{
              $t('redis-monitor.databaseList')
            }}</span>
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {{
              $t('redis-monitor.totalDatabasesCount', {
                count: keyspaces.length,
              })
            }}
          </div>
        </div>
      </template>

      <div v-if="keyspaces.length === 0">
        <ElEmpty :description="$t('redis-monitor.noDatabaseInfo')" />
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="db in keyspaces"
          :key="db.db_id"
          class="rounded-lg border border-gray-200 p-4 dark:border-gray-700"
        >
          <!-- 数据库头部 -->
          <div class="mb-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div
                class="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30"
              >
                <Database :size="24" class="text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div class="text-lg font-semibold">DB{{ db.db_id }}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  {{ $t('redis-monitor.database') }} {{ db.db_id }}
                </div>
              </div>
            </div>
            <ElTag :type="db.keys > 0 ? 'success' : 'info'" size="large">
              {{
                db.keys > 0
                  ? $t('redis-monitor.active')
                  : $t('redis-monitor.paused')
              }}
            </ElTag>
          </div>

          <!-- 数据库统计 -->
          <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
            <!-- 键数量 -->
            <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
              <div class="mb-2 flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">{{
                  $t('redis-monitor.keyCount')
                }}</span>
                <Key :size="16" class="text-gray-400" />
              </div>
              <div class="text-2xl font-bold">
                {{ db.keys.toLocaleString() }}
              </div>
              <div class="mt-2">
                <ElProgress
                  :percentage="getDbUsagePercent(db.keys)"
                  :color="getUsageColor(getDbUsagePercent(db.keys))"
                  :show-text="false"
                />
              </div>
            </div>

            <!-- 过期键 -->
            <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
              <div class="mb-2 flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">{{
                  $t('redis-monitor.expires')
                }}</span>
                <Activity :size="16" class="text-gray-400" />
              </div>
              <div class="text-2xl font-bold">
                {{ db.expires.toLocaleString() }}
              </div>
              <div class="mt-2 flex items-center gap-2">
                <ElTag
                  :type="getExpireRateColor(db.expires, db.keys)"
                  size="small"
                >
                  {{
                    db.keys > 0 ? ((db.expires / db.keys) * 100).toFixed(1) : 0
                  }}%
                </ElTag>
                <span class="text-xs text-gray-500">{{
                  $t('redis-monitor.expireRate')
                }}</span>
              </div>
            </div>

            <!-- 平均TTL -->
            <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
              <div class="mb-2 flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">{{
                  $t('redis-monitor.avgTTL')
                }}</span>
                <Database :size="16" class="text-gray-400" />
              </div>
              <div class="text-2xl font-bold">
                {{ formatTTL(db.avg_ttl) }}
              </div>
              <div class="mt-2 text-xs text-gray-500">
                {{
                  db.avg_ttl > 0
                    ? `${db.avg_ttl.toLocaleString()}${$t('redis-monitor.milliseconds')}`
                    : $t('redis-monitor.noExpireTime')
                }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </ElCard>

    <!-- 键空间说明 -->
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
            {{ $t('redis-monitor.keyCount') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.keyCountDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.expires') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.expiresDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.avgTTL') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.avgTTLDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.expireRate') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.expireRateDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.dbId') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.dbIdDesc') }}
          </div>
        </div>
        <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <div class="mb-1 font-medium text-gray-700 dark:text-gray-300">
            {{ $t('redis-monitor.usageRate') }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            {{ $t('redis-monitor.usageRateDesc') }}
          </div>
        </div>
      </div>
    </ElCard>
  </div>
</template>
