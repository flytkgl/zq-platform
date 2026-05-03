<script setup lang="ts">
import type { TreeNode } from '../index.vue';

import type { ExecuteSQLResponse } from '#/api/core/database-manager';

import { ref } from 'vue';

import { Zap } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElAlert,
  ElButton,
  ElCard,
  ElMessage,
  ElTable,
  ElTableColumn,
} from 'element-plus';

import { executeSQLApi } from '#/api/core/database-manager';

interface Props {
  node: TreeNode;
}

const props = defineProps<Props>();

const sqlText = ref('');
const executing = ref(false);
const result = ref<ExecuteSQLResponse | null>(null);

// 执行SQL
async function executeSQL() {
  if (!sqlText.value.trim()) {
    ElMessage.warning($t('database-manager.pleaseEnterSQL'));
    return;
  }

  if (!props.node.meta?.dbName) {
    ElMessage.error($t('database-manager.invalidDatabaseConnection'));
    return;
  }

  executing.value = true;
  result.value = null;

  try {
    const sql = sqlText.value.trim();
    const isQuery = /^\s*(SELECT|SHOW|DESCRIBE|DESC|EXPLAIN)\s+/i.test(sql);

    const data = await executeSQLApi(props.node.meta.dbName, {
      sql,
      is_query: isQuery,
    });

    result.value = data;

    if (data.success) {
      ElMessage.success(data.message || $t('database-manager.executeSuccess'));
    } else {
      ElMessage.error(data.message || $t('database-manager.executeFailed'));
    }
  } catch (error: any) {
    console.error('Failed to execute SQL:', error);
    ElMessage.error(error.message || $t('database-manager.executeSQLFailed'));
  } finally {
    executing.value = false;
  }
}

// 清空
function clearSQL() {
  sqlText.value = '';
  result.value = null;
}

// 示例SQL
function loadExample() {
  sqlText.value = props.node.meta?.table
    ? `SELECT * FROM ${props.node.meta.schema ? `${props.node.meta.schema}.` : ''}${props.node.meta.table} LIMIT 10;`
    : 'SELECT 1;';
}
</script>

<template>
  <div class="flex h-full flex-col gap-3">
    <!-- SQL编辑器 -->
    <ElCard shadow="never">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-semibold">{{
            $t('database-manager.sqlEditor')
          }}</span>
          <div class="flex gap-2">
            <ElButton size="small" @click="loadExample">
              {{ $t('database-manager.loadExample') }}
            </ElButton>
            <ElButton size="small" @click="clearSQL">
              {{ $t('database-manager.clearSQL') }}
            </ElButton>
            <ElButton
              type="primary"
              size="small"
              @click="executeSQL"
              :loading="executing"
            >
              <Zap :size="14" />
              <span class="ml-1">{{ $t('database-manager.execute') }}</span>
            </ElButton>
          </div>
        </div>
      </template>

      <textarea
        v-model="sqlText"
        class="focus:ring-primary h-48 w-full resize-none rounded border p-3 font-mono text-sm focus:outline-none focus:ring-2"
        :placeholder="$t('database-manager.sqlPlaceholder')"
        spellcheck="false"
      ></textarea>
    </ElCard>

    <!-- 执行结果 -->
    <ElCard v-if="result" shadow="never" class="flex-1">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-semibold">{{
            $t('database-manager.executionResult')
          }}</span>
          <span class="text-sm text-gray-500">
            {{ $t('database-manager.executionTime') }}:
            {{ result.execution_time?.toFixed(2) }}ms
          </span>
        </div>
      </template>

      <!-- 成功提示 -->
      <ElAlert
        v-if="result.success && !result.rows"
        type="success"
        :closable="false"
        class="mb-3"
      >
        <template #title>
          <div>{{ result.message }}</div>
          <div v-if="result.affected_rows !== undefined" class="mt-1 text-sm">
            {{ $t('database-manager.affectedRows') }}:
            {{ result.affected_rows }}
          </div>
        </template>
      </ElAlert>

      <!-- 错误提示 -->
      <ElAlert
        v-if="!result.success"
        type="error"
        :closable="false"
        class="mb-3"
      >
        <template #title>
          <div class="font-mono text-sm">{{ result.message }}</div>
        </template>
      </ElAlert>

      <!-- 查询结果表格 -->
      <div v-if="result.success && result.rows && result.rows.length > 0">
        <div class="mb-2 text-sm text-gray-500">
          {{ $t('database-manager.returned') }} {{ result.rows.length }}
          {{ $t('database-manager.records') }}
        </div>
        <ElTable
          :data="result.rows"
          stripe
          border
          max-height="400"
          style="width: 100%"
        >
          <ElTableColumn
            v-for="column in result.columns || []"
            :key="column"
            :prop="column"
            :label="column"
            min-width="120"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <span v-if="row[column] === null" class="italic text-gray-400"
                >NULL</span
              >
              <span v-else>{{ row[column] }}</span>
            </template>
          </ElTableColumn>
        </ElTable>
      </div>

      <!-- 无结果 -->
      <div
        v-if="result.success && result.rows && result.rows.length === 0"
        class="py-8 text-center text-gray-400"
      >
        {{ $t('database-manager.querySuccessNoData') }}
      </div>
    </ElCard>

    <!-- 提示信息 -->
    <ElCard v-else shadow="never" class="flex-1">
      <div
        class="flex h-full flex-col items-center justify-center text-gray-400"
      >
        <Zap :size="48" class="mb-4 opacity-50" />
        <div class="text-sm">{{ $t('database-manager.enterSQL') }}</div>
        <div class="mt-2 text-xs">
          {{ $t('database-manager.sqlWarning') }}
        </div>
      </div>
    </ElCard>
  </div>
</template>

<style scoped>
textarea {
  font-family:
    Monaco, Menlo, 'Ubuntu Mono', Consolas, source-code-pro, monospace;
}
</style>
