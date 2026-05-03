<script setup lang="ts">
import type { TreeNode } from '../index.vue';

import { ref, watch } from 'vue';

import { Copy, Database, Eye, FileText, Table } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElMessage,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { getViewStructureApi } from '#/api/core/database-manager';

interface Props {
  node: TreeNode;
}

const props = defineProps<Props>();

const loading = ref(false);
const viewStructure = ref<any>(null);

// 加载视图结构
async function loadViewStructure() {
  const viewName = (props.node.meta as any)?.view;
  if (!props.node.meta?.dbName || !viewName) {
    return;
  }

  loading.value = true;
  try {
    const data = await getViewStructureApi(
      props.node.meta.dbName,
      viewName,
      props.node.meta.schema,
    );
    viewStructure.value = data;
  } catch (error) {
    console.error('Failed to load view structure:', error);
    ElMessage.error($t('database-manager.loadViewStructureFailed'));
  } finally {
    loading.value = false;
  }
}

// 复制定义SQL
function copyDefinition() {
  if (viewStructure.value?.definition_sql) {
    navigator.clipboard.writeText(viewStructure.value.definition_sql);
    ElMessage.success($t('database-manager.copiedToClipboard'));
  }
}

// 监听节点变化
watch(
  () => props.node,
  () => {
    loadViewStructure();
  },
  { immediate: true },
);
</script>

<template>
  <div class="flex h-full flex-col gap-4 overflow-auto p-4">
    <!-- 视图基本信息 -->
    <ElCard shadow="never" v-loading="loading">
      <template #header>
        <div class="flex items-center gap-2">
          <Eye :size="20" class="text-blue-500" />
          <span class="font-semibold">{{
            $t('database-manager.viewInfo')
          }}</span>
        </div>
      </template>

      <ElDescriptions v-if="viewStructure" :column="2" border>
        <ElDescriptionsItem :label="$t('database-manager.viewName')">
          <span class="font-medium">{{
            viewStructure.view_info.view_name
          }}</span>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="Schema">
          {{ viewStructure.view_info.schema_name || 'N/A' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.viewType')">
          <ElTag
            :type="
              viewStructure.view_info.view_type === 'MATERIALIZED VIEW'
                ? 'warning'
                : 'primary'
            "
            size="small"
          >
            {{
              viewStructure.view_info.view_type === 'MATERIALIZED VIEW'
                ? $t('database-manager.materializedView')
                : $t('database-manager.normalView')
            }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('database-manager.isUpdatable')">
          <ElTag
            :type="viewStructure.view_info.is_updatable ? 'success' : 'info'"
            size="small"
          >
            {{
              viewStructure.view_info.is_updatable
                ? $t('database-manager.yes')
                : $t('database-manager.no')
            }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('database-manager.checkOption')"
          v-if="viewStructure.view_info.view_type !== 'MATERIALIZED VIEW'"
        >
          {{ viewStructure.view_info.check_option || 'NONE' }}
        </ElDescriptionsItem>
      </ElDescriptions>

      <ElEmpty v-else :description="$t('database-manager.noData')" />
    </ElCard>

    <!-- 列信息 -->
    <ElCard shadow="never">
      <template #header>
        <div class="flex items-center gap-2">
          <Database :size="18" class="text-green-500" />
          <span class="font-semibold">{{ $t('database-manager.columnInfo') }} ({{
              viewStructure?.columns?.length || 0
            }})</span>
        </div>
      </template>

      <ElTable
        v-if="viewStructure?.columns"
        :data="viewStructure.columns"
        border
        stripe
        max-height="300"
      >
        <ElTableColumn
          prop="column_name"
          :label="$t('database-manager.columnName')"
          width="200"
        />
        <ElTableColumn
          prop="data_type"
          :label="$t('database-manager.dataType')"
          width="150"
        />
        <ElTableColumn
          prop="is_nullable"
          :label="$t('database-manager.nullable')"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <ElTag :type="row.is_nullable ? 'info' : 'warning'" size="small">
              {{
                row.is_nullable
                  ? $t('database-manager.yes')
                  : $t('database-manager.no')
              }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn
          prop="ordinal_position"
          :label="$t('database-manager.position')"
          width="80"
          align="center"
        />
        <ElTableColumn
          prop="description"
          :label="$t('database-manager.description')"
          min-width="200"
          show-overflow-tooltip
        />
      </ElTable>

      <ElEmpty v-else :description="$t('database-manager.noColumnInfo')" />
    </ElCard>

    <!-- 依赖的表 -->
    <ElCard shadow="never">
      <template #header>
        <div class="flex items-center gap-2">
          <Table :size="18" class="text-orange-500" />
          <span class="font-semibold">{{ $t('database-manager.dependentTables') }} ({{
              viewStructure?.dependencies?.length || 0
            }})</span>
        </div>
      </template>

      <div
        v-if="
          viewStructure?.dependencies && viewStructure.dependencies.length > 0
        "
        class="flex flex-wrap gap-2"
      >
        <ElTag
          v-for="table in viewStructure.dependencies"
          :key="table"
          type="info"
          size="large"
        >
          <Table :size="14" class="mr-1" />
          {{ table }}
        </ElTag>
      </div>

      <ElEmpty
        v-else
        :description="$t('database-manager.noDependentTables')"
        :image-size="60"
      />
    </ElCard>

    <!-- 视图定义SQL -->
    <ElCard shadow="never" class="flex-1">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <FileText :size="18" class="text-purple-500" />
            <span class="font-semibold">{{
              $t('database-manager.viewDefinition')
            }}</span>
          </div>
          <ElButton
            size="small"
            @click="copyDefinition"
            :disabled="!viewStructure?.definition_sql"
          >
            <Copy :size="14" />
            <span class="ml-1">{{ $t('database-manager.copy') }}</span>
          </ElButton>
        </div>
      </template>

      <pre
        v-if="viewStructure?.definition_sql"
        class="max-h-96 overflow-auto rounded bg-gray-50 p-4 font-mono text-sm leading-relaxed"
        >{{ viewStructure.definition_sql }}</pre>

      <ElEmpty v-else :description="$t('database-manager.noDefinition')" />
    </ElCard>

    <!-- 说明 -->
    <ElCard shadow="never">
      <template #header>
        <span class="font-semibold">{{
          $t('database-manager.description')
        }}</span>
      </template>
      <div class="space-y-2 text-sm text-gray-600">
        <p>
          <strong>{{ $t('database-manager.viewExplanation') }}</strong>
        </p>
        <ul class="ml-2 list-inside list-disc space-y-1">
          <li>{{ $t('database-manager.viewBenefit1') }}</li>
          <li>{{ $t('database-manager.viewBenefit2') }}</li>
          <li>{{ $t('database-manager.viewBenefit3') }}</li>
          <li>{{ $t('database-manager.viewBenefit4') }}</li>
        </ul>
      </div>
    </ElCard>
  </div>
</template>

<style scoped>
pre {
  font-family: Monaco, Menlo, 'Ubuntu Mono', Consolas, monospace;
  word-wrap: break-word;
  white-space: pre-wrap;
}
</style>
