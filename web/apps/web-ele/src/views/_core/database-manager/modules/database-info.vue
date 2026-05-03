<script setup lang="ts">
import type { TreeNode } from '../index.vue';

import type { DatabaseInfo } from '#/api/core/database-manager';

import { ref, watch } from 'vue';

import { $t } from '@vben/locales';

import {
  ElDescriptions,
  ElDescriptionsItem,
  ElDivider,
  ElMessage,
  ElSkeleton,
} from 'element-plus';

import { getDatabasesApi } from '#/api/core/database-manager';

interface Props {
  node: TreeNode;
}

const props = defineProps<Props>();

const loading = ref(false);
const databaseInfo = ref<DatabaseInfo | null>(null);

// 加载数据库信息
async function loadDatabaseInfo() {
  if (!props.node.meta?.dbName) {
    return;
  }

  loading.value = true;
  try {
    const databases = await getDatabasesApi(props.node.meta.dbName);
    databaseInfo.value =
      databases.find((db) => db.name === props.node.meta?.database) || null;
  } catch (error) {
    console.error('Failed to load database info:', error);
    ElMessage.error($t('database-manager.loadDatabaseInfoFailed'));
  } finally {
    loading.value = false;
  }
}

// 格式化大小
function formatSize(bytes?: number) {
  if (!bytes) return '-';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`;
}

// 监听节点变化
watch(
  () => props.node,
  () => {
    loadDatabaseInfo();
  },
  { immediate: true },
);
</script>

<template>
  <div class="h-full space-y-6">
    <!-- 数据库基本信息 -->
    <div>
      <h3 class="mb-4 text-base font-semibold">
        {{ $t('database-manager.databaseInfo') }}
      </h3>

      <ElSkeleton v-if="loading" :rows="5" animated />

      <ElDescriptions v-else-if="databaseInfo" :column="2" border>
        <ElDescriptionsItem
          :label="$t('database-manager.databaseName')"
          :span="2"
        >
          <span class="text-lg font-medium">{{ databaseInfo.name }}</span>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.owner')">
          {{ databaseInfo.owner || '-' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.encoding')">
          {{ databaseInfo.encoding || '-' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.collation')">
          {{ databaseInfo.collation || '-' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.tableCount')">
          <span class="text-primary font-medium">
            {{ databaseInfo.tables_count?.toLocaleString() || 0 }}
            {{ $t('database-manager.tables') }}
          </span>
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('database-manager.databaseSize')"
          :span="2"
        >
          <div class="flex items-center gap-2">
            <span class="font-medium">{{ databaseInfo.size || '-' }}</span>
            <span v-if="databaseInfo.size_bytes" class="text-sm text-gray-500">
              ({{ formatSize(databaseInfo.size_bytes) }})
            </span>
          </div>
        </ElDescriptionsItem>
        <ElDescriptionsItem
          v-if="databaseInfo.description"
          :label="$t('database-manager.description')"
          :span="2"
        >
          {{ databaseInfo.description }}
        </ElDescriptionsItem>
      </ElDescriptions>

      <div v-else class="py-8 text-center text-gray-400">
        {{ $t('database-manager.noDatabaseInfo') }}
      </div>
    </div>

    <ElDivider />

    <!-- 快速操作 -->
    <div>
      <h3 class="mb-4 text-base font-semibold">
        {{ $t('database-manager.quickOperations') }}
      </h3>
      <div class="space-y-3 text-sm">
        <div class="flex items-start gap-2">
          <span class="text-primary">📂</span>
          <div>
            <div class="font-medium">
              {{ $t('database-manager.viewTableList') }}
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ $t('database-manager.expandLeftTreeNode') }}
            </div>
          </div>
        </div>
        <div class="flex items-start gap-2">
          <span class="text-primary">🔍</span>
          <div>
            <div class="font-medium">
              {{ $t('database-manager.searchTable') }}
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ $t('database-manager.useSearchBox') }}
            </div>
          </div>
        </div>
        <div class="flex items-start gap-2">
          <span class="text-primary">⚡</span>
          <div>
            <div class="font-medium">
              {{ $t('database-manager.executeSql') }}
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ $t('database-manager.switchToSqlTab') }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <ElDivider />

    <!-- 统计信息 -->
    <div v-if="databaseInfo">
      <h3 class="mb-4 text-base font-semibold">
        {{ $t('database-manager.statistics') }}
      </h3>
      <div class="grid grid-cols-2 gap-4">
        <div class="rounded-lg bg-blue-50 p-4 text-center">
          <div class="text-2xl font-bold text-blue-600">
            {{ databaseInfo.tables_count?.toLocaleString() || 0 }}
          </div>
          <div class="mt-1 text-sm text-gray-600">
            {{ $t('database-manager.tableCount') }}
          </div>
        </div>
        <div class="rounded-lg bg-green-50 p-4 text-center">
          <div class="text-2xl font-bold text-green-600">
            {{ databaseInfo.size || '-' }}
          </div>
          <div class="mt-1 text-sm text-gray-600">
            {{ $t('database-manager.databaseSize') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
