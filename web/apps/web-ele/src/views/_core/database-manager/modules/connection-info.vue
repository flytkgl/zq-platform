<script setup lang="ts">
import type { TreeNode } from '../index.vue';

import { ref, watch } from 'vue';

import { RotateCw } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElDescriptions,
  ElDescriptionsItem,
  ElDivider,
  ElMessage,
  ElTag,
} from 'element-plus';

import { testDatabaseConnectionApi } from '#/api/core/database-manager';

interface Props {
  node: TreeNode;
}

const props = defineProps<Props>();

const testing = ref(false);
const connectionStatus = ref<{
  message: string;
  success: boolean;
  tested: boolean;
}>({
  success: false,
  message: '',
  tested: false,
});

// 测试连接
async function testConnection() {
  if (!props.node.meta?.dbName) {
    return;
  }

  testing.value = true;
  try {
    const result = await testDatabaseConnectionApi(props.node.meta.dbName);
    connectionStatus.value = {
      success: result.success,
      message: result.message,
      tested: true,
    };

    if (result.success) {
      ElMessage.success($t('database-manager.testConnectionSuccess'));
    } else {
      ElMessage.error($t('database-manager.testConnectionFailed'));
    }
  } catch (error: any) {
    connectionStatus.value = {
      success: false,
      message: error.message || $t('database-manager.connectionError'),
      tested: true,
    };
    ElMessage.error($t('database-manager.testConnectionFailed'));
  } finally {
    testing.value = false;
  }
}

// 监听节点变化，重置状态
watch(
  () => props.node,
  () => {
    connectionStatus.value.tested = false;
  },
);
</script>

<script lang="ts">
// 获取数据库类型颜色
function getDbTypeColor(dbType?: string) {
  const type = dbType?.toLowerCase();
  switch (type) {
    case 'mysql': {
      return 'warning';
    }
    case 'postgresql': {
      return 'primary';
    }
    case 'sqlserver': {
      return 'danger';
    }
    default: {
      return 'info';
    }
  }
}
</script>

<template>
  <div class="h-full space-y-6">
    <!-- 连接信息 -->
    <div>
      <div class="mb-4 flex items-center justify-between">
        <h3 class="text-base font-semibold">
          {{ $t('database-manager.connectionInfo') }}
        </h3>
        <ElButton size="small" :loading="testing" @click="testConnection">
          <RotateCw :size="14" :class="{ 'animate-spin': testing }" />
          <span class="ml-1">{{ $t('database-manager.testConnection') }}</span>
        </ElButton>
      </div>

      <ElDescriptions :column="2" border>
        <ElDescriptionsItem :label="$t('database-manager.connectionName')">
          {{ node.label }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.databaseType')">
          <ElTag :type="getDbTypeColor(node.meta?.dbType)">
            {{ node.meta?.dbType?.toUpperCase() }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('database-manager.connectionIdentifier')"
        >
          {{ node.meta?.dbName }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.connectionStatus')">
          <ElTag
            v-if="connectionStatus.tested"
            :type="connectionStatus.success ? 'success' : 'danger'"
          >
            {{
              connectionStatus.success
                ? $t('database-manager.connectionSuccessful')
                : $t('database-manager.connectionFailed')
            }}
          </ElTag>
          <span v-else class="text-gray-400">{{
            $t('database-manager.notTested')
          }}</span>
        </ElDescriptionsItem>
      </ElDescriptions>

      <!-- 连接测试结果 -->
      <div v-if="connectionStatus.tested" class="mt-4">
        <div class="mb-2 text-sm font-medium">
          {{ $t('database-manager.testResult') }}
        </div>
        <div
          class="rounded-lg border p-3 text-sm"
          :class="
            connectionStatus.success
              ? 'border-green-200 bg-green-50 text-green-700'
              : 'border-red-200 bg-red-50 text-red-700'
          "
        >
          {{ connectionStatus.message }}
        </div>
      </div>
    </div>

    <ElDivider />

    <!-- 使用说明 -->
    <div>
      <h3 class="mb-4 text-base font-semibold">
        {{ $t('database-manager.usageInstructions') }}
      </h3>
      <div class="space-y-2 text-sm text-gray-600">
        <div>{{ $t('database-manager.expandConnection') }}</div>
        <div>{{ $t('database-manager.selectDatabase') }}</div>
        <div>{{ $t('database-manager.selectTable') }}</div>
        <div>{{ $t('database-manager.searchFunction') }}</div>
      </div>
    </div>

    <ElDivider />

    <!-- 快捷操作 -->
    <div>
      <h3 class="mb-4 text-base font-semibold">
        {{ $t('database-manager.quickActions') }}
      </h3>
      <div class="space-y-2">
        <ElButton
          type="primary"
          size="small"
          class="w-full"
          @click="testConnection"
        >
          {{ $t('database-manager.testDatabaseConnection') }}
        </ElButton>
        <div class="mt-2 text-xs text-gray-500">
          {{ $t('database-manager.tip') }}
        </div>
      </div>
    </div>
  </div>
</template>
