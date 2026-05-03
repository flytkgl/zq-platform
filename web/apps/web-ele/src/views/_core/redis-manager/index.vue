<script setup lang="ts">
import type { RedisDatabase } from '#/api/core/redis-manager';

import { computed, onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';
import { Database, Plus, RotateCw, Search } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElInput,
  ElMessage,
  ElOption,
  ElScrollbar,
  ElSelect,
  ElTag,
} from 'element-plus';

import { getRedisDatabasesApi } from '#/api/core/redis-manager';

import KeyDetailPanel from './modules/key-detail-panel.vue';
import KeyFormModal from './modules/key-form-modal.vue';
import KeyListPanel from './modules/key-list-panel.vue';

defineOptions({ name: 'RedisManager' });

// 数据库列表
const databases = ref<RedisDatabase[]>([]);
const selectedDbIndex = ref<number>(0);
const loading = ref(false);
const refreshingDatabases = ref(false);

// 选中的键
const selectedKey = ref<string>('');

// 键详情面板引用
const keyDetailPanelRef = ref();
const keyListPanelRef = ref();

// 刷新键详情
function handleRefreshKeyDetail() {
  keyDetailPanelRef.value?.handleRefresh();
}

// 刷新键列表
function handleRefreshKeyList() {
  keyListPanelRef.value?.handleRefresh();
}

// 搜索和过滤
const searchPattern = ref('*');
const keyType = ref<string>('');

// 键类型选项
const keyTypeOptions = [
  { label: $t('redis-manager.allTypes'), value: '' },
  { label: 'String', value: 'string' },
  { label: 'List', value: 'list' },
  { label: 'Set', value: 'set' },
  { label: 'ZSet', value: 'zset' },
  { label: 'Hash', value: 'hash' },
];

// 表单模态框
const formModalVisible = ref(false);
const formMode = ref<'create' | 'edit'>('create');
const editingKey = ref<string>('');

// 获取数据库列表
async function loadDatabases() {
  try {
    loading.value = true;
    const response = await getRedisDatabasesApi();
    databases.value = response.databases;
  } catch (error) {
    console.error('Failed to load databases:', error);
    ElMessage.error($t('redis-manager.loadDatabasesFailed'));
  } finally {
    loading.value = false;
  }
}

// 选择数据库
function handleSelectDatabase(dbIndex: number) {
  selectedDbIndex.value = dbIndex;
  selectedKey.value = ''; // 清空选中的键
}

// 选择键
function handleSelectKey(key: string) {
  selectedKey.value = key;
}

// 打开新增键表单
function handleCreateKey() {
  formMode.value = 'create';
  editingKey.value = '';
  formModalVisible.value = true;
}

// 打开编辑键表单
function handleEditKey(key: string) {
  formMode.value = 'edit';
  editingKey.value = key;
  formModalVisible.value = true;
}

// 刷新数据库列表
async function handleRefresh() {
  refreshingDatabases.value = true;
  try {
    await loadDatabases();
  } finally {
    // 延迟一点时间，让动画更明显
    setTimeout(() => {
      refreshingDatabases.value = false;
    }, 500);
  }
}

// 表单提交成功
function handleFormSuccess() {
  formModalVisible.value = false;
  // 刷新键列表（通过事件通知子组件）
}

// 计算当前数据库信息
const currentDatabase = computed(() => {
  return databases.value.find((db) => db.db_index === selectedDbIndex.value);
});

onMounted(() => {
  loadDatabases();
});
</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full gap-3">
      <!-- 左侧：数据库列表 -->
      <div class="w-1/6 flex-shrink-0">
        <ElCard
          class="h-full"
          style="border: none"
          :body-style="{ padding: '12px', height: '100%' }"
        >
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Database :size="18" class="text-primary" />
                <span class="text-sm font-semibold">{{
                  $t('redis-manager.database')
                }}</span>
              </div>
              <ElButton
                :title="$t('redis-manager.refresh')"
                @click="handleRefresh"
                circle
              >
                <RotateCw
                  :size="16"
                  :class="{ 'animate-spin': refreshingDatabases }"
                />
              </ElButton>
            </div>
          </template>

          <ElScrollbar class="h-[calc(100%-48px)]">
            <div class="space-y-2">
              <div
                v-for="db in databases"
                :key="db.db_index"
                class="cursor-pointer rounded-lg border p-3 transition-all"
                :class="
                  selectedDbIndex === db.db_index
                    ? 'border-primary bg-primary/10'
                    : 'hover:border-primary/50 border-gray-200 dark:border-gray-700'
                "
                @click="handleSelectDatabase(db.db_index)"
              >
                <div class="flex items-center justify-between">
                  <span class="font-mono text-sm font-semibold">
                    DB{{ db.db_index }}
                  </span>
                  <ElTag
                    v-if="db.keys_count > 0"
                    size="small"
                    :type="selectedDbIndex === db.db_index ? 'primary' : 'info'"
                  >
                    {{ db.keys_count }}
                  </ElTag>
                </div>
                <div
                  v-if="db.keys_count > 0"
                  class="mt-1 text-xs text-gray-500"
                >
                  <div>
                    {{ $t('redis-manager.expires') }}: {{ db.expires_count }}
                  </div>
                  <div v-if="db.avg_ttl > 0">
                    {{ $t('redis-manager.avgTTL') }}:
                    {{ Math.round(db.avg_ttl / 1000) }}s
                  </div>
                </div>
              </div>
            </div>
          </ElScrollbar>
        </ElCard>
      </div>

      <!-- 右侧：键管理区域 -->
      <div class="flex flex-1 gap-3">
        <!-- 键列表 -->
        <div class="w-1/2">
          <ElCard
            class="flex h-full flex-col"
            style="border: none"
            :body-style="{
              display: 'flex',
              flexDirection: 'column',
              flex: 1,
              minHeight: 0,
              padding: 0,
              overflow: 'hidden',
            }"
          >
            <template #header>
              <div class="flex items-center justify-between gap-3">
                <!-- 左侧：标题 -->
                <div class="flex items-center gap-2">
                  <span class="font-semibold">{{
                    $t('redis-manager.keyList')
                  }}</span>
                  <ElTag v-if="currentDatabase" size="small" type="info">
                    DB{{ selectedDbIndex }} -
                    {{
                      $t('redis-manager.keysCount', {
                        count: currentDatabase.keys_count,
                      })
                    }}
                  </ElTag>
                </div>

                <!-- 右侧：搜索、过滤、刷新、按钮 -->
                <div class="flex items-center gap-2">
                  <ElInput
                    v-model="searchPattern"
                    :placeholder="$t('redis-manager.searchKeyPlaceholder')"
                    style="width: 140px"
                    clearable
                  >
                    <template #prefix>
                      <Search :size="16" />
                    </template>
                  </ElInput>
                  <ElSelect
                    v-model="keyType"
                    :placeholder="$t('redis-manager.type')"
                    style="width: 100px"
                    clearable
                  >
                    <ElOption
                      v-for="option in keyTypeOptions"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </ElSelect>
                  <ElButton
                    :title="$t('redis-manager.refresh')"
                    @click="handleRefreshKeyList"
                  >
                    <RotateCw
                      :size="16"
                      :class="{ 'animate-spin': keyListPanelRef?.refreshing }"
                    />
                  </ElButton>
                  <ElButton type="primary" @click="handleCreateKey">
                    <Plus :size="16" class="mr-1" />
                    {{ $t('redis-manager.addKey') }}
                  </ElButton>
                </div>
              </div>
            </template>

            <KeyListPanel
              ref="keyListPanelRef"
              :db-index="selectedDbIndex"
              :selected-key="selectedKey"
              :search-pattern="searchPattern"
              :key-type="keyType"
              @select-key="handleSelectKey"
              @edit-key="handleEditKey"
            />
          </ElCard>
        </div>

        <!-- 键详情 -->
        <div class="w-1/2">
          <ElCard
            class="flex h-full flex-col"
            style="border: none"
            :body-style="{
              display: 'flex',
              flexDirection: 'column',
              flex: 1,
              minHeight: 0,
              padding: 0,
              overflow: 'hidden',
            }"
          >
            <template #header>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="font-semibold">{{
                    $t('redis-manager.keyDetail')
                  }}</span>
                  <span
                    v-if="selectedKey"
                    class="font-mono text-sm text-gray-500"
                  >
                    {{ selectedKey }}
                  </span>
                </div>
                <ElButton
                  v-if="selectedKey"
                  :title="$t('redis-manager.refresh')"
                  @click="handleRefreshKeyDetail"
                >
                  <RotateCw
                    :size="16"
                    :class="{ 'animate-spin': keyDetailPanelRef?.refreshing }"
                  />
                </ElButton>
              </div>
            </template>

            <KeyDetailPanel
              ref="keyDetailPanelRef"
              :db-index="selectedDbIndex"
              :selected-key="selectedKey"
              @edit-key="handleEditKey"
              @key-deleted="selectedKey = ''"
            />
          </ElCard>
        </div>
      </div>
    </div>

    <!-- 键表单模态框 -->
    <KeyFormModal
      v-model:visible="formModalVisible"
      :db-index="selectedDbIndex"
      :mode="formMode"
      :editing-key="editingKey"
      @success="handleFormSuccess"
    />
  </Page>
</template>

<style scoped>
/* 自定义样式 */
</style>
