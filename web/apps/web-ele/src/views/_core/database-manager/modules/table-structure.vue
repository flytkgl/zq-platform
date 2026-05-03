<script setup lang="ts">
import type { TreeNode } from '../index.vue';

import type { TableStructure } from '#/api/core/database-manager';

import { ref, watch } from 'vue';

import { Copy } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElDivider,
  ElMessage,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import {
  getTableDDLApi,
  getTableStructureApi,
} from '#/api/core/database-manager';

interface Props {
  node: TreeNode;
}

const props = defineProps<Props>();

const loading = ref(false);
const loadingDDL = ref(false);
const tableStructure = ref<null | TableStructure>(null);
const ddlStatement = ref('');

// 加载DDL语句
async function loadTableDDL() {
  if (!props.node.meta?.dbName || !props.node.meta?.table) {
    return;
  }

  loadingDDL.value = true;
  try {
    const data = await getTableDDLApi(
      props.node.meta.dbName,
      props.node.meta.table,
      props.node.meta.database,
      props.node.meta.schema,
    );
    ddlStatement.value = data.ddl;
  } catch (error) {
    console.error('Failed to load table DDL:', error);
    ElMessage.error($t('database-manager.loadDDLFailed'));
    ddlStatement.value = $t('database-manager.loadDDLFailedMsg');
  } finally {
    loadingDDL.value = false;
  }
}

// 复制DDL
function copyDDL() {
  if (ddlStatement.value) {
    navigator.clipboard.writeText(ddlStatement.value);
    ElMessage.success($t('database-manager.copiedToClipboard'));
  }
}

// 加载表结构
async function loadTableStructure() {
  if (!props.node.meta?.dbName || !props.node.meta?.table) {
    return;
  }

  loading.value = true;
  try {
    const data = await getTableStructureApi(
      props.node.meta.dbName,
      props.node.meta.table,
      props.node.meta.database,
      props.node.meta.schema,
    );
    tableStructure.value = data;
  } catch (error) {
    console.error('Failed to load table structure:', error);
    ElMessage.error($t('database-manager.loadTableStructureFailed'));
  } finally {
    loading.value = false;
  }
}

// 监听节点变化
watch(
  () => props.node,
  () => {
    loadTableStructure();
    loadTableDDL();
  },
  { immediate: true },
);
</script>

<template>
  <div class="h-full space-y-6">
    <!-- 表信息 -->
    <div v-if="tableStructure">
      <h3 class="mb-4 text-base font-semibold">
        {{ $t('database-manager.tableInfo') }}
      </h3>
      <div class="grid grid-cols-2 gap-4 rounded-lg border p-4 text-sm">
        <div class="flex justify-between">
          <span class="text-gray-500">{{ $t('database-manager.tableName') }}:</span>
          <span class="font-medium">{{
            tableStructure.table_info.table_name
          }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">{{ $t('database-manager.tableType') }}:</span>
          <span>{{ tableStructure.table_info.table_type || 'TABLE' }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">{{ $t('database-manager.rowCount') }}:</span>
          <span>{{
            tableStructure.table_info.row_count?.toLocaleString() || '-'
          }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">{{ $t('database-manager.tableSize') }}:</span>
          <span>{{ tableStructure.table_info.total_size || '-' }}</span>
        </div>
      </div>
    </div>

    <ElDivider />

    <!-- 字段列表 -->
    <div class="flex-1">
      <h3 class="mb-4 text-base font-semibold">
        {{ $t('database-manager.fields') }} ({{
          tableStructure?.columns.length || 0
        }})
      </h3>
      <ElTable
        :data="tableStructure?.columns || []"
        v-loading="loading"
        stripe
        border
        height="300"
      >
        <ElTableColumn
          prop="column_name"
          :label="$t('database-manager.fieldName')"
          width="150"
        />
        <ElTableColumn
          prop="data_type"
          :label="$t('database-manager.dataType')"
          width="120"
        />
        <ElTableColumn
          :label="$t('database-manager.nullable')"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <ElTag :type="row.is_nullable ? 'info' : 'success'" size="small">
              {{ row.is_nullable ? 'YES' : 'NO' }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn
          prop="column_default"
          :label="$t('database-manager.defaultValue')"
          width="120"
        />
        <ElTableColumn
          :label="$t('database-manager.primaryKey')"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <ElTag v-if="row.is_primary_key" type="danger" size="small">
              PK
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn
          :label="$t('database-manager.unique')"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <ElTag v-if="row.is_unique" type="warning" size="small">UQ</ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn
          prop="description"
          :label="$t('database-manager.description')"
          min-width="150"
          show-overflow-tooltip
        />
      </ElTable>
    </div>

    <ElDivider />

    <!-- DDL语句 -->
    <div v-loading="loadingDDL">
      <div class="mb-4 flex items-center justify-between">
        <h3 class="text-base font-semibold">
          {{ $t('database-manager.ddlStatement') }}
        </h3>
        <ElButton size="small" @click="copyDDL" :disabled="!ddlStatement">
          <Copy :size="14" />
          <span class="ml-1">{{ $t('database-manager.copy') }}</span>
        </ElButton>
      </div>
      <pre
        class="max-h-96 overflow-auto rounded-lg border bg-gray-50 p-4 font-mono text-sm leading-relaxed"
        >{{ ddlStatement || $t('database-manager.loading') }}</pre
      >
    </div>

    <ElDivider />

    <!-- 索引列表 -->
    <div>
      <h3 class="mb-4 text-base font-semibold">
        {{ $t('database-manager.indexes') }} ({{
          tableStructure?.indexes.length || 0
        }})
      </h3>
      <ElTable
        :data="tableStructure?.indexes || []"
        v-loading="loading"
        stripe
        border
        max-height="200"
      >
        <ElTableColumn
          prop="index_name"
          :label="$t('database-manager.indexName')"
          width="180"
        />
        <ElTableColumn
          prop="index_type"
          :label="$t('database-manager.indexType')"
          width="100"
        />
        <ElTableColumn
          prop="columns"
          :label="$t('database-manager.columns')"
          min-width="150"
        />
        <ElTableColumn
          :label="$t('database-manager.unique')"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <ElTag v-if="row.is_unique" type="warning" size="small">UQ</ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn
          :label="$t('database-manager.primaryKey')"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <ElTag v-if="row.is_primary" type="danger" size="small">PK</ElTag>
          </template>
        </ElTableColumn>
      </ElTable>
    </div>

    <ElDivider />

    <!-- 约束列表 -->
    <div>
      <h3 class="mb-4 text-base font-semibold">
        {{ $t('database-manager.constraints') }} ({{
          tableStructure?.constraints.length || 0
        }})
      </h3>
      <ElTable
        :data="tableStructure?.constraints || []"
        v-loading="loading"
        stripe
        border
        max-height="200"
      >
        <ElTableColumn
          prop="constraint_name"
          :label="$t('database-manager.constraintName')"
          width="180"
        />
        <ElTableColumn
          prop="constraint_type"
          :label="$t('database-manager.constraintType')"
          width="120"
        />
        <ElTableColumn
          prop="columns"
          :label="$t('database-manager.columns')"
          width="150"
        />
        <ElTableColumn
          prop="definition"
          :label="$t('database-manager.definition')"
          min-width="200"
          show-overflow-tooltip
        />
      </ElTable>
    </div>
  </div>
</template>
