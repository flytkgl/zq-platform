<script setup lang="ts">
import { ref } from 'vue';

import { RotateCw, Search } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElInput } from 'element-plus';

import { FuPage } from '#/components/fu-page';

import DatabaseTree from './modules/database-tree.vue';
import DetailPanel from './modules/detail-panel.vue';

defineOptions({ name: 'DatabaseManager' });

// 树节点类型
export interface TreeNode {
  id: string;
  label: string;
  type:
    | 'connection'
    | 'database'
    | 'schema'
    | 'table'
    | 'tables-folder'
    | 'view'
    | 'views-folder';
  children?: TreeNode[];
  isLeaf?: boolean;
  meta?: {
    database?: string;
    dbName?: string;
    dbType?: string;
    schema?: string;
    table?: string;
    view?: string;
  };
}

// 选中的节点
const selectedNode = ref<null | TreeNode>(null);
// 当前激活的Tab
const activeTab = ref('structure');
// 搜索关键词
const searchKeyword = ref('');
// 刷新状态
const refreshing = ref(false);
// 树组件引用
const treeRef = ref();

// 处理节点选择
function handleNodeSelect(node: TreeNode) {
  selectedNode.value = node;
}

// 处理Tab切换
function handleSwitchTab(tabName: string) {
  activeTab.value = tabName;
}

// 处理搜索
function handleSearch() {
  if (treeRef.value?.handleSearch) {
    treeRef.value.handleSearch(searchKeyword.value);
  }
}

// 处理刷新
async function handleRefresh() {
  if (treeRef.value?.handleRefresh) {
    refreshing.value = true;
    await treeRef.value.handleRefresh();
    refreshing.value = false;
  }
}
</script>

<template>
  <FuPage
    left-width="300px"
    :left-min-width="250"
    :left-max-width="500"
    :left-padding="false"
    left-content-class="flex flex-col"
  >
    <!-- 左侧卡片头部 -->
    <template #left-header>
      <div class="flex gap-3">
        <!-- 搜索框 -->
        <ElInput
          v-model="searchKeyword"
          :placeholder="$t('database-manager.searchPlaceholder')"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <Search :size="16" />
          </template>
        </ElInput>
        <div class="flex items-center justify-between">
          <ElButton circle @click="handleRefresh">
            <RotateCw :size="16" :class="{ 'animate-spin': refreshing }" />
          </ElButton>
        </div>
      </div>
    </template>

    <!-- 左侧内容 -->
    <template #left>
      <!-- 树形结构 -->
      <div class="flex-1 overflow-auto px-5 py-4">
        <DatabaseTree
          ref="treeRef"
          :selected-node="selectedNode"
          :search-keyword="searchKeyword"
          @select="handleNodeSelect"
          @switch-tab="handleSwitchTab"
        />
      </div>
    </template>

    <!-- 右侧内容 -->
    <template #right>
      <DetailPanel :selected-node="selectedNode" :active-tab="activeTab" />
    </template>
  </FuPage>
</template>
