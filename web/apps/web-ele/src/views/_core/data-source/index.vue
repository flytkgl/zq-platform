<script lang="ts" setup>
import type { DataSource } from '#/api/core/data-source';

import { onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';
import { Copy, Database, Edit, Play, Plus, Trash2 } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElEmpty,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElPagination,
  ElTag,
  ElTooltip,
} from 'element-plus';

import {
  copyDataSourceApi,
  deleteDataSourceApi,
  getDataSourceListApi,
} from '#/api/core/data-source';
import { useAppContextStore } from '#/store/app-context';

import DataSourceEditorModal from './modules/data-source-editor-modal.vue';
import TestDialog from './modules/test-dialog.vue';

defineOptions({ name: 'DataSourceManagement' });

const appContextStore = useAppContextStore();

// 搜索关键词
const searchKeyword = ref('');

// 列表数据
const loading = ref(false);
const dataSourceList = ref<DataSource[]>([]);

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 12,
  total: 0,
});

// 弹窗状态
const showFormModal = ref(false);
const editingId = ref<null | string>(null);
const showTestDialog = ref(false);
const testingDataSource = ref<DataSource | null>(null);

// 获取列表
async function fetchList() {
  loading.value = true;
  try {
    const res = await getDataSourceListApi({
      page: pagination.current,
      pageSize: pagination.pageSize,
      applicationId: appContextStore.currentApp?.id,
      name: searchKeyword.value || undefined,
    });
    dataSourceList.value = res.items;
    pagination.total = res.total;
  } catch (error) {
    console.error('获取数据源列表失败:', error);
  } finally {
    loading.value = false;
  }
}

// 搜索
function handleSearch() {
  pagination.current = 1;
  fetchList();
}

// 分页变化
function handlePageChange(page: number) {
  pagination.current = page;
  fetchList();
}

// 每页条数变化
function handleSizeChange(size: number) {
  pagination.pageSize = size;
  pagination.current = 1;
  fetchList();
}

// 创建
function handleCreate() {
  editingId.value = null;
  showFormModal.value = true;
}

// 编辑
function handleEdit(item: DataSource) {
  editingId.value = item.id;
  showFormModal.value = true;
}

// 测试
function handleTest(item: DataSource) {
  testingDataSource.value = item;
  showTestDialog.value = true;
}

// 删除
async function handleDelete(item: DataSource) {
  try {
    await ElMessageBox.confirm(
      $t('data-source.deleteConfirmMessage', { name: item.name }),
      $t('data-source.deleteConfirmTitle'),
      {
        confirmButtonText: $t('data-source.confirm'),
        cancelButtonText: $t('data-source.cancel'),
        type: 'warning',
      },
    );
    await deleteDataSourceApi(item.id);
    ElMessage.success($t('data-source.deleteSuccess', { name: item.name }));
    fetchList();
  } catch {
    // 用户取消
  }
}

// 复制
async function handleCopy(item: DataSource) {
  try {
    const { value: newCode } = await ElMessageBox.prompt(
      $t('data-source.inputNewCode'),
      $t('data-source.copyDataSource'),
      {
        confirmButtonText: $t('data-source.confirm'),
        cancelButtonText: $t('data-source.cancel'),
        inputPattern: /^[\w-]+$/,
        inputErrorMessage: $t('data-source.codeFormatError'),
        inputValue: `${item.code}_copy`,
      },
    );
    await copyDataSourceApi(item.id, {
      new_code: newCode,
      new_name: `${item.name} ${$t('data-source.copy')}`,
    });
    ElMessage.success($t('data-source.copySuccess'));
    fetchList();
  } catch {
    // 用户取消
  }
}

// 保存成功回调
function handleFormSave() {
  ElMessage.success($t('data-source.saveSuccess'));
  fetchList();
}

// 获取类型标签
function getTypeTag(type: string) {
  const map: Record<
    string,
    { label: string; type: 'primary' | 'success' | 'warning' }
  > = {
    sql: { label: 'SQL', type: 'primary' },
    api: { label: 'API', type: 'success' },
    static: { label: $t('data-source.staticLabel'), type: 'warning' },
  };
  return map[type] || { label: type, type: 'primary' };
}

onMounted(() => {
  fetchList();
});
</script>

<template>
  <div class="data-source-list-page">
    <Page auto-content-height v-loading="loading">
      <template #title>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <ElInput
              v-model="searchKeyword"
              :placeholder="$t('data-source.inputDataSourceName')"
              clearable
              class="w-64"
              @keyup.enter="handleSearch"
            />
            <ElButton @click="handleSearch">{{ $t('common.search') }}</ElButton>
          </div>
          <ElButton type="primary" @click="handleCreate">
            <Plus class="mr-1 h-4 w-4" />
            {{ $t('data-source.createDataSource') }}
          </ElButton>
        </div>
      </template>

      <!-- 数据源卡片列表 -->
      <div
        v-if="dataSourceList.length > 0"
        class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
      >
        <ElCard
          v-for="item in dataSourceList"
          :key="item.id"
          class="group data-source-card cursor-pointer transition-shadow"
          shadow="hover"
          :body-style="{ padding: '0' }"
          style="border: none"
          @click="handleEdit(item)"
        >
          <div class="p-4">
            <!-- 头部：图标 + 右侧信息区 -->
            <div class="mb-3 flex gap-3">
              <div
                class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg"
                :class="
                  item.source_type === 'api'
                    ? 'bg-success/10'
                    : item.source_type === 'sql'
                      ? 'bg-primary/10'
                      : 'bg-warning/10'
                "
              >
                <Database
                  class="h-5 w-5"
                  :class="
                    item.source_type === 'api'
                      ? 'text-success'
                      : item.source_type === 'sql'
                        ? 'text-primary'
                        : 'text-warning'
                  "
                />
              </div>
              <div class="min-w-0 flex-1">
                <!-- name + 操作 -->
                <div class="flex items-center justify-between">
                  <div class="min-w-0 flex-1 whitespace-nowrap text-sm font-medium group-hover:truncate">
                    {{ item.name }}
                  </div>
                  <div
                    class="flex flex-shrink-0 items-center -space-x-1 opacity-0 transition-opacity group-hover:opacity-100"
                    @click.stop
                  >
                    <ElTooltip
                      :content="$t('data-source.edit')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleEdit(item)">
                        <Edit class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip
                      :content="$t('data-source.testConnection')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleTest(item)">
                        <Play class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip
                      :content="$t('data-source.copy')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleCopy(item)">
                        <Copy class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip
                      :content="$t('data-source.delete')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleDelete(item)">
                        <Trash2 class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                  </div>
                </div>
                <!-- code -->
                <div class="text-muted-foreground font-mono text-xs">
                  {{ item.code }}
                </div>
              </div>
            </div>
            <!-- 描述 -->
            <div
              class="text-muted-foreground mb-3 line-clamp-1 min-h-[18px] text-xs"
            >
              {{ item.description }}
            </div>
            <!-- 标签 -->
            <div class="mb-3 flex items-center justify-between">
              <div class="flex gap-1">
                <ElTag size="small" :type="getTypeTag(item.source_type).type">
                  {{ getTypeTag(item.source_type).label }}
                </ElTag>
                <ElTag size="small" :type="item.status ? 'success' : 'info'">
                  {{
                    item.status
                      ? $t('data-source.enable')
                      : $t('data-source.disable')
                  }}
                </ElTag>
              </div>
            </div>
            <!-- 应用名称 + 创建时间 -->
            <div class="flex items-center justify-between">
              <div class="text-muted-foreground flex gap-1 text-xs">
                <div v-if="item.application_name">
                  {{ item.application_name }}
                </div>
                <div v-else>
                  {{ $t('common.mainApp') }}
                </div>
              </div>
              <span class="text-muted-foreground text-xs">
                {{ item.sys_create_datetime }}
              </span>
            </div>
          </div>
        </ElCard>
      </div>

      <!-- 空状态 -->
      <ElEmpty v-else :description="$t('common.noData')" />

      <!-- 分页 -->
      <template #footer>
        <div class="flex w-full items-center justify-end">
          <ElPagination
            v-model:current-page="pagination.current"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[12, 24, 36, 48]"
            :pager-count="7"
            layout="total, sizes, prev, pager, next, jumper"
            background
            size="small"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </div>
      </template>
    </Page>

    <!-- 数据源编辑器弹窗 -->
    <DataSourceEditorModal
      v-model="showFormModal"
      :data-source-id="editingId"
      @save="handleFormSave"
    />

    <!-- 测试弹窗 -->
    <TestDialog
      v-if="testingDataSource"
      v-model="showTestDialog"
      :data-source="testingDataSource"
    />
  </div>
</template>
