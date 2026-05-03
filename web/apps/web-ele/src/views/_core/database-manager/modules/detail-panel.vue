<script setup lang="ts">
import type { TreeNode } from '../index.vue';

import { $t } from '@vben/locales';

import { ElEmpty, ElTabPane, ElTabs } from 'element-plus';

import ConnectionInfo from './connection-info.vue';
import DatabaseInfo from './database-info.vue';
import SchemaInfo from './schema-info.vue';
import SqlExecutor from './sql-executor.vue';
import TableData from './table-data.vue';
import TableEditor from './table-editor.vue';
import TableStructure from './table-structure.vue';
import ViewStructure from './view-structure.vue';

interface Props {
  selectedNode: null | TreeNode;
  activeTab?: string;
}

withDefaults(defineProps<Props>(), {
  activeTab: 'structure',
});
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 未选择任何节点 -->
    <ElEmpty
      v-if="!selectedNode"
      :description="$t('database-manager.selectItemFromLeft')"
      :image-size="120"
      class="mt-20"
    />

    <!-- 选中连接 -->
    <ConnectionInfo
      v-else-if="selectedNode && selectedNode.type === 'connection'"
      :node="selectedNode"
    />

    <!-- 选中数据库 -->
    <DatabaseInfo
      v-else-if="selectedNode && selectedNode.type === 'database'"
      :node="selectedNode"
    />

    <!-- 选中Schema -->
    <SchemaInfo
      v-else-if="selectedNode && selectedNode.type === 'schema'"
      :node="selectedNode"
    />

    <!-- 选中表 -->
    <div v-else-if="selectedNode.type === 'table'" class="flex flex-1 flex-col">
      <ElTabs :model-value="activeTab" class="flex-1">
        <ElTabPane
          :label="$t('database-manager.tableStructure')"
          name="structure"
        >
          <TableStructure :node="selectedNode" />
        </ElTabPane>
        <ElTabPane :label="$t('database-manager.dataQuery')" name="data">
          <TableData :node="selectedNode" />
        </ElTabPane>
        <ElTabPane :label="$t('database-manager.sqlExecution')" name="sql">
          <SqlExecutor :node="selectedNode" />
        </ElTabPane>
        <ElTabPane :label="$t('database-manager.objectEditor')" name="editor">
          <TableEditor :node="selectedNode" />
        </ElTabPane>
      </ElTabs>
    </div>

    <!-- 选中视图 -->
    <div v-else-if="selectedNode.type === 'view'" class="flex flex-1 flex-col">
      <div class="mb-3">
        <h3 class="text-lg font-semibold">{{ selectedNode.label }}</h3>
        <div class="mt-1 text-sm text-gray-500">
          {{ selectedNode.meta?.database
          }}<span v-if="selectedNode.meta?.schema"
            >.{{ selectedNode.meta?.schema }}</span
          >
        </div>
      </div>

      <ElTabs :model-value="activeTab" class="flex-1">
        <ElTabPane
          :label="$t('database-manager.viewStructure')"
          name="structure"
        >
          <ViewStructure :node="selectedNode" />
        </ElTabPane>
        <ElTabPane :label="$t('database-manager.dataQuery')" name="data">
          <TableData :node="selectedNode" />
        </ElTabPane>
        <ElTabPane :label="$t('database-manager.sqlExecution')" name="sql">
          <SqlExecutor :node="selectedNode" />
        </ElTabPane>
      </ElTabs>
    </div>
  </div>
</template>
