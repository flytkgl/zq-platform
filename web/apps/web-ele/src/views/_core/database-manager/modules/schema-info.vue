<script setup lang="ts">
import type { TreeNode } from '../index.vue';

import { ref, watch } from 'vue';

import { Copy, Database, Eye, Table } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElDescriptions,
  ElDescriptionsItem,
  ElDivider,
  ElMessage,
  ElTabPane,
  ElTabs,
  ElTag,
} from 'element-plus';

import { getTablesApi, getViewsApi } from '#/api/core/database-manager';

interface Props {
  node: TreeNode;
}

const props = defineProps<Props>();

const loading = ref(false);
const tableCount = ref(0);
const viewCount = ref(0);
const tableList = ref<any[]>([]);
const viewList = ref<any[]>([]);

// 加载Schema信息
async function loadSchemaInfo() {
  if (!props.node.meta?.dbName || !props.node.meta?.schema) {
    return;
  }

  loading.value = true;
  try {
    // 同时获取该Schema下的所有表和视图
    const [tables, views] = await Promise.all([
      getTablesApi(
        props.node.meta.dbName,
        props.node.meta.database,
        props.node.meta.schema,
      ),
      getViewsApi(
        props.node.meta.dbName,
        props.node.meta.database,
        props.node.meta.schema,
      ),
    ]);
    tableList.value = tables;
    tableCount.value = tables.length;
    viewList.value = views;
    viewCount.value = views.length;
  } catch (error) {
    console.error('Failed to load schema info:', error);
    ElMessage.error($t('database-manager.loadSchemaInfoFailed'));
  } finally {
    loading.value = false;
  }
}

// 复制Schema名称
function copySchemaName() {
  if (props.node.meta?.schema) {
    navigator.clipboard.writeText(props.node.meta.schema);
    ElMessage.success($t('database-manager.copiedToClipboard'));
  }
}

// 监听节点变化
watch(
  () => props.node,
  () => {
    loadSchemaInfo();
  },
  { immediate: true },
);
</script>

<template>
  <div class="h-full space-y-6" v-loading="loading">
    <!-- Schema基本信息 -->
    <div>
      <div class="mb-4 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Database :size="20" class="text-blue-500" />
          <h3 class="text-base font-semibold">
            {{ $t('database-manager.schemaInfo') }}
          </h3>
        </div>
        <ElButton size="small" @click="copySchemaName">
          <Copy :size="14" />
          <span class="ml-1">{{ $t('database-manager.copyName') }}</span>
        </ElButton>
      </div>

      <ElDescriptions :column="2" border>
        <ElDescriptionsItem :label="$t('database-manager.schemaName')">
          <span class="font-medium">{{ node.meta?.schema }}</span>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.database')">
          {{ node.meta?.database }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.databaseType')">
          <ElTag
            :type="node.meta?.dbType === 'postgresql' ? 'primary' : 'warning'"
          >
            {{ node.meta?.dbType?.toUpperCase() }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.objectStatistics')">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-1">
              <Table :size="16" />
              <span class="font-semibold text-blue-600">{{ tableCount }}</span>
              <span class="text-xs text-gray-500">{{
                $t('database-manager.tables')
              }}</span>
            </div>
            <div class="flex items-center gap-1">
              <Eye :size="16" />
              <span class="font-semibold text-green-600">{{ viewCount }}</span>
              <span class="text-xs text-gray-500">{{
                $t('database-manager.views')
              }}</span>
            </div>
          </div>
        </ElDescriptionsItem>
      </ElDescriptions>
    </div>

    <ElDivider />

    <!-- 表和视图列表 -->
    <div class="flex-1">
      <div class="mb-4 flex items-center gap-2">
        <Database :size="18" class="text-green-500" />
        <h3 class="text-base font-semibold">
          {{ $t('database-manager.databaseObjects') }}
        </h3>
      </div>

      <ElTabs>
        <!-- 表列表 -->
        <ElTabPane>
          <template #label>
            <div class="flex items-center gap-2">
              <Table :size="16" />
              <span
                >{{ $t('database-manager.tables') }} ({{ tableCount }})</span
              >
            </div>
          </template>

          <div
            v-if="tableList.length === 0"
            class="py-8 text-center text-gray-400"
          >
            {{ $t('database-manager.noTablesInSchema') }}
          </div>

          <div
            v-else
            class="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3"
          >
            <div
              v-for="table in tableList"
              :key="table.table_name"
              class="cursor-pointer rounded-lg border p-3 transition-all hover:border-blue-400 hover:shadow-sm"
            >
              <div class="flex items-start gap-2">
                <Table :size="16" class="mt-1 text-gray-500" />
                <div class="min-w-0 flex-1">
                  <div
                    class="truncate text-sm font-medium"
                    :title="table.table_name"
                  >
                    {{ table.table_name }}
                  </div>
                  <div
                    v-if="table.description"
                    class="mt-1 truncate text-xs text-gray-500"
                  >
                    {{ table.description }}
                  </div>
                  <div class="mt-2 flex gap-2 text-xs text-gray-400">
                    <span v-if="table.row_count !== undefined">
                      {{ table.row_count?.toLocaleString() }} 行
                    </span>
                    <span v-if="table.total_size">
                      {{ table.total_size }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </ElTabPane>

        <!-- 视图列表 -->
        <ElTabPane>
          <template #label>
            <div class="flex items-center gap-2">
              <Eye :size="16" />
              <span>{{ $t('database-manager.views') }} ({{ viewCount }})</span>
            </div>
          </template>

          <div
            v-if="viewList.length === 0"
            class="py-8 text-center text-gray-400"
          >
            {{ $t('database-manager.noViewsInSchema') }}
          </div>

          <div
            v-else
            class="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3"
          >
            <div
              v-for="view in viewList"
              :key="view.view_name"
              class="cursor-pointer rounded-lg border p-3 transition-all hover:border-green-400 hover:shadow-sm"
            >
              <div class="flex items-start gap-2">
                <Eye :size="16" class="mt-1 text-green-500" />
                <div class="min-w-0 flex-1">
                  <div
                    class="truncate text-sm font-medium"
                    :title="view.view_name"
                  >
                    {{ view.view_name }}
                  </div>
                  <div
                    v-if="view.description"
                    class="mt-1 truncate text-xs text-gray-500"
                  >
                    {{ view.description }}
                  </div>
                  <div class="mt-2 flex gap-2 text-xs">
                    <ElTag
                      v-if="view.view_type === 'MATERIALIZED VIEW'"
                      type="warning"
                      size="small"
                    >
                      {{ $t('database-manager.materializedView') }}
                    </ElTag>
                    <ElTag
                      v-else-if="view.is_updatable"
                      type="success"
                      size="small"
                    >
                      {{ $t('database-manager.updatable') }}
                    </ElTag>
                    <ElTag v-else type="info" size="small">
                      {{ $t('database-manager.readOnly') }}
                    </ElTag>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </ElTabPane>
      </ElTabs>
    </div>

    <ElDivider />

    <!-- Schema说明 -->
    <div>
      <h3 class="mb-4 text-base font-semibold">
        {{ $t('database-manager.description') }}
      </h3>
      <div class="space-y-2 text-sm text-gray-600">
        <p>
          <strong>Schema</strong>
          是数据库对象的逻辑容器，用于组织和管理表、视图、函数等对象。
        </p>
        <ul class="ml-2 list-inside list-disc space-y-1">
          <li>
            PostgreSQL: 每个数据库可以包含多个Schema，默认Schema为
            <code class="rounded bg-gray-100 px-1">public</code>
          </li>
          <li>
            SQL Server: 使用Schema来组织数据库对象，默认Schema为
            <code class="rounded bg-gray-100 px-1">dbo</code>
          </li>
          <li>MySQL: 不支持Schema概念，数据库即为最高层级容器</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
code {
  font-family: Monaco, Menlo, 'Ubuntu Mono', Consolas, monospace;
  font-size: 0.9em;
}
</style>
