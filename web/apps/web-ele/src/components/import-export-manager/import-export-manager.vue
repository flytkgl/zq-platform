<script setup lang="ts">
import type {
  ImportExportManagerEmits,
  ImportExportManagerProps,
  TaskRecord,
} from './types';

import type { ImportResult } from '#/api/online-dev/form-data-api';

import { computed, onMounted, onUnmounted, ref } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';

import {
  AlertCircle,
  ArrowDownToLine,
  ArrowUpFromLine,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  Loader,
  RefreshCw,
  Square,
  Trash2,
  Upload,
  XCircle,
} from '@vben/icons';

import { UploadFilled } from '@element-plus/icons-vue';
import { useLocalStorage } from '@vueuse/core';
import {
  ElButton,
  ElCheckbox,
  ElCollapse,
  ElCollapseItem,
  ElIcon,
  ElMessage,
  ElPopconfirm,
  ElPopover,
  ElScrollbar,
  ElTabPane,
  ElTabs,
  ElTag,
  ElUpload,
} from 'element-plus';

import {
  cancelExportTaskApi,
  createExportTaskApi,
  downloadFormDataExcel,
  downloadImportTemplate,
  importFormDataExcelApi,
  pollExportTask,
} from '#/api/online-dev/form-data-api';

defineOptions({ name: 'ImportExportManager' });

const props = withDefaults(defineProps<ImportExportManagerProps>(), {
  formName: '',
  showImport: true,
  showExport: true,
  showTemplate: true,
});

const emit = defineEmits<ImportExportManagerEmits>();

// 状态
const activeTab = ref('import');
const popoverVisible = ref(false);
const importLoading = ref(false);
const exportLoading = ref(false);
const updateExisting = ref(false);
const includeSubTables = ref(true);
const useAsyncExport = ref(true); // 默认使用异步导出
const exportProgress = ref(0);

// 任务历史
const taskHistory = useLocalStorage<TaskRecord[]>(
  `import-export-history-${props.formCode}`,
  [],
);

// 最近导入结果
const lastImportResult = ref<ImportResult | null>(null);
const showErrorDetails = ref<string[]>([]);

// 存储活跃的轮询停止函数
const activePollers = new Map<string, () => void>();

// 启动轮询任务
function startPolling(taskId: string, filename: string, isLatest: boolean) {
  const { promise, stop } = pollExportTask(props.formCode, taskId, {
    filename,
    onProgress: (progress, status, details) => {
      updateTaskRecord(taskId, {
        progress,
        totalCount: details?.total_count,
        processedCount: details?.processed_count,
        status:
          status === 'processing'
            ? 'running'
            : (status === 'completed'
              ? 'success'
              : 'failed'),
      });

      if (isLatest) {
        exportProgress.value = progress;
      }
    },
  });

  // 存储 stop 函数
  activePollers.set(taskId, stop);

  promise
    .then(() => {
      updateTaskRecord(taskId, { status: 'success' });
      ElMessage.success(`任务 ${filename} 导出成功`);
    })
    .catch((error) => {
      updateTaskRecord(taskId, {
        status: 'failed',
        error: error.message,
      });
      if (isLatest) {
        ElMessage.error(`任务 ${filename} 失败: ${error.message}`);
      }
    })
    .finally(() => {
      activePollers.delete(taskId);
      if (isLatest) {
        exportLoading.value = false;
        exportProgress.value = 0;
      }
    });
}

// 恢复未完成的任务
function recoverRunningTasks() {
  taskHistory.value.forEach((task) => {
    if (task.type === 'export' && task.status === 'running') {
      exportLoading.value = true;
      useAsyncExport.value = true;
      const isLatest = taskHistory.value[0]?.id === task.id;
      startPolling(task.id, task.filename, isLatest);
    }
  });
}

onMounted(() => {
  recoverRunningTasks();
});

// 停止所有轮询
function stopAllPollers() {
  activePollers.forEach((stop) => stop());
  activePollers.clear();
}

// 页面卸载时停止所有轮询
onUnmounted(() => {
  stopAllPollers();
});

// 路由离开时停止所有轮询
onBeforeRouteLeave(() => {
  stopAllPollers();
});

// 计算属性
const hasErrors = computed(
  () => lastImportResult.value && lastImportResult.value.failed > 0,
);

// 生成任务ID
function generateTaskId() {
  return `task_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

// 添加任务记录
function addTaskRecord(
  type: 'export' | 'import',
  filename: string,
  options?: any,
): TaskRecord {
  const record: TaskRecord = {
    id: generateTaskId(),
    type,
    filename,
    status: 'running',
    startTime: new Date(),
    options,
  };
  taskHistory.value.unshift(record);
  return record;
}

// 更新任务记录
function updateTaskRecord(id: string, updates: Partial<TaskRecord>) {
  const record = taskHistory.value.find((t) => t.id === id);
  if (record) {
    Object.assign(record, updates, {
      endTime: ['failed', 'success'].includes(updates.status || '')
        ? new Date()
        : undefined,
    });
  }
}

// 下载模板
async function handleDownloadTemplate() {
  try {
    await downloadImportTemplate(
      props.formCode,
      `${props.formName || props.formCode}_导入模板.xlsx`,
    );
    ElMessage.success('模板下载成功');
  } catch {
    ElMessage.error('模板下载失败');
  }
}

// 导出数据
async function handleExport() {
  exportLoading.value = true;
  exportProgress.value = 0;
  const filename = `${props.formName || props.formCode}_数据.xlsx`;
  const options = {
    includeSubTables: includeSubTables.value,
    filename,
  };
  const record = addTaskRecord('export', filename, options);

  try {
    if (useAsyncExport.value) {
      // 异步导出（适用于大数据量）
      // 1. 创建后端任务
      const { task_id } = await createExportTaskApi(props.formCode, {
        includeSubTables: includeSubTables.value,
      });

      // 2. 更新前端记录 ID 为后端 UUID
      const index = taskHistory.value.findIndex((t) => t.id === record.id);
      if (index !== -1 && taskHistory.value[index]) {
        taskHistory.value[index]!.id = task_id;
        record.id = task_id;
      }

      // 3. 跳转到进行中 Tab
      activeTab.value = 'running';

      // 4. 启动轮询（会自动处理成功/失败/停止）
      startPolling(task_id, filename, true);
      return; // 轮询会处理后续逻辑
    } else {
      // 同步导出（适用于小数据量）
      await downloadFormDataExcel(props.formCode, {
        includeSubTables: includeSubTables.value,
        filename,
      });
    }
    updateTaskRecord(record.id, {
      status: 'success',
      result: { count: 0 },
    });
    ElMessage.success('导出成功');
    emit('export-success');
  } catch (error: any) {
    updateTaskRecord(record.id, {
      status: 'failed',
      error: error?.message || '导出失败',
    });
    ElMessage.error(error?.message || '导出失败');
  } finally {
    exportLoading.value = false;
    exportProgress.value = 0;
  }
}

// 上传导入文件
async function handleUploadRequest(options: any) {
  const { file } = options;
  importLoading.value = true;
  lastImportResult.value = null;
  showErrorDetails.value = [];

  const record = addTaskRecord('import', file.name);

  try {
    const result = await importFormDataExcelApi(
      props.formCode,
      file,
      updateExisting.value,
    );
    lastImportResult.value = result;

    updateTaskRecord(record.id, {
      status: result.failed > 0 ? 'failed' : 'success',
      result,
    });

    if (result.failed > 0) {
      ElMessage.warning(
        `导入完成：成功 ${result.success} 条，失败 ${result.failed} 条`,
      );
      showErrorDetails.value = ['errors'];
    } else {
      ElMessage.success(`成功导入 ${result.success} 条数据`);
      emit('import-success', result);
    }
  } catch (error: any) {
    updateTaskRecord(record.id, {
      status: 'failed',
      error: error?.message || '导入失败',
    });
    ElMessage.error(error?.message || '导入失败');
  } finally {
    importLoading.value = false;
  }
}

// 重试任务
function handleRetry(task: TaskRecord) {
  if (task.type === 'export' && task.options) {
    activeTab.value = 'export';
    includeSubTables.value = task.options.includeSubTables ?? true;
    useAsyncExport.value = true;
    handleExport();
  }
}

// 取消任务
async function handleCancelTask(task: TaskRecord) {
  if (task.type !== 'export' || task.status !== 'running') {
    return;
  }

  try {
    // 1. 停止前端轮询
    const stopFn = activePollers.get(task.id);
    if (stopFn) {
      stopFn();
      activePollers.delete(task.id);
    }

    // 2. 调用后端取消 API
    await cancelExportTaskApi(props.formCode, task.id);

    // 3. 更新任务状态为已取消
    updateTaskRecord(task.id, { status: 'cancelled' });

    // 4. 重置导出状态
    exportLoading.value = false;
    exportProgress.value = 0;

    ElMessage.info('导出任务已取消');
  } catch (error: any) {
    ElMessage.error(error?.message || '取消失败');
  }
}

// 清除历史
function handleClearHistory() {
  taskHistory.value = runningTasks.value;
  ElMessage.success('历史记录已清除');
}

// 计算属性
const runningTasks = computed(() =>
  taskHistory.value.filter(
    (t) => t.status === 'running' || t.status === 'pending',
  ),
);

const completedTasks = computed(() =>
  taskHistory.value.filter(
    (t) => t.status !== 'running' && t.status !== 'pending',
  ),
);

// 判断是否过期
function isExpired(task: TaskRecord) {
  if (task.status === 'success' && task.expiresAt) {
    return new Date(task.expiresAt) < new Date();
  }
  return false;
}

// 格式化时间
function formatTime(date: Date | string) {
  const d = new Date(date);
  return d.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

// 获取状态标签类型
function getStatusType(
  status: string,
): 'danger' | 'info' | 'success' | 'warning' {
  const map: Record<string, 'danger' | 'info' | 'success' | 'warning'> = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    cancelled: 'info',
  };
  return map[status] || 'info';
}

// 获取状态文本
function getStatusText(status: string) {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '进行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消',
  };
  return map[status] || status;
}
</script>

<template>
  <ElPopover
    v-model:visible="popoverVisible"
    placement="bottom-end"
    :width="420"
    trigger="click"
  >
    <template #reference>
      <ElButton circle :icon="FileSpreadsheet" title="导入导出" />
    </template>

    <div class="import-export-manager">
      <ElTabs v-model="activeTab" class="!-mt-2">
        <!-- 导入 Tab -->
        <ElTabPane v-if="showImport" label="导入" name="import">
          <div class="flex flex-col gap-4">
            <!-- 下载模板 -->
            <div
              v-if="showTemplate"
              class="flex items-center justify-between rounded-lg bg-[var(--el-fill-color-lighter)] p-3"
            >
              <div class="flex items-center gap-2">
                <ArrowDownToLine
                  class="h-4 w-4 text-[var(--el-color-primary)]"
                />
                <span class="text-sm">下载导入模板</span>
              </div>
              <ElButton
                size="small"
                type="primary"
                link
                @click="handleDownloadTemplate"
              >
                下载
              </ElButton>
            </div>

            <!-- 上传区域 -->
            <ElUpload
              drag
              action=""
              :http-request="handleUploadRequest"
              :show-file-list="false"
              :disabled="importLoading"
              accept=".xlsx,.xls"
              class="!w-full"
            >
              <div
                v-loading="importLoading"
                element-loading-text="正在导入..."
                class="flex flex-col items-center py-4"
              >
                <ElIcon
                  class="mb-2 text-3xl text-[var(--el-text-color-secondary)]"
                >
                  <UploadFilled />
                </ElIcon>
                <div class="text-sm text-[var(--el-text-color-secondary)]">
                  拖拽文件到此处，或
                  <em class="not-italic text-[var(--el-color-primary)]">点击上传</em>
                </div>
                <div
                  class="mt-1 text-xs text-[var(--el-text-color-placeholder)]"
                >
                  支持 .xlsx, .xls 格式
                </div>
              </div>
            </ElUpload>

            <!-- 选项 -->
            <div class="flex items-center">
              <ElCheckbox v-model="updateExisting" size="small">
                更新已存在的数据（根据ID匹配）
              </ElCheckbox>
            </div>

            <!-- 导入结果 -->
            <div
              v-if="lastImportResult"
              class="rounded-lg border border-[var(--el-border-color-lighter)] p-3"
            >
              <div class="mb-2 flex items-center justify-between">
                <span class="text-sm font-medium">导入结果</span>
                <div class="flex items-center gap-3 text-sm">
                  <span
                    class="flex items-center gap-1 text-[var(--el-color-success)]"
                  >
                    <CheckCircle2 class="h-4 w-4" />
                    {{ lastImportResult.success }}
                  </span>
                  <span
                    v-if="lastImportResult.failed > 0"
                    class="flex items-center gap-1 text-[var(--el-color-danger)]"
                  >
                    <XCircle class="h-4 w-4" />
                    {{ lastImportResult.failed }}
                  </span>
                </div>
              </div>

              <!-- 错误详情 -->
              <ElCollapse v-if="hasErrors" v-model="showErrorDetails">
                <ElCollapseItem title="查看错误详情" name="errors">
                  <ElScrollbar max-height="150px">
                    <div class="space-y-1">
                      <div
                        v-for="(err, idx) in lastImportResult.errors"
                        :key="idx"
                        class="flex items-start gap-2 rounded bg-[var(--el-color-danger-light-9)] p-2 text-xs"
                      >
                        <AlertCircle
                          class="mt-0.5 h-3 w-3 flex-shrink-0 text-[var(--el-color-danger)]"
                        />
                        <div>
                          <span class="font-medium">第 {{ err.row }} 行</span>
                          <span v-if="err.field">，字段 {{ err.field }}</span>
                          <span>：{{ err.error }}</span>
                        </div>
                      </div>
                    </div>
                  </ElScrollbar>
                </ElCollapseItem>
              </ElCollapse>
            </div>
          </div>
        </ElTabPane>

        <!-- 导出 Tab -->
        <ElTabPane v-if="showExport" label="导出" name="export">
          <div class="flex flex-col gap-4">
            <div class="rounded-lg bg-[var(--el-fill-color-lighter)] p-4">
              <div class="mb-3 flex items-center gap-2">
                <Download class="h-4 w-4 text-[var(--el-color-primary)]" />
                <span class="text-sm font-medium">导出数据</span>
              </div>
              <div class="mb-3 space-y-2">
                <ElCheckbox v-model="includeSubTables" size="small">
                  包含子表数据（多Sheet）
                </ElCheckbox>
                <ElCheckbox v-model="useAsyncExport" size="small">
                  异步导出（推荐大数据量使用）
                </ElCheckbox>
              </div>
              <!-- 导出进度条 -->
              <div
                v-if="
                  exportLoading && useAsyncExport && runningTasks.length > 0
                "
                class="mb-3"
              >
                <div class="mb-1 flex justify-between text-xs">
                  <span>导出进度</span>
                  <span class="flex items-center gap-2">
                    <span>{{ runningTasks[0]?.progress || 0 }}%</span>
                    <span
                      v-if="runningTasks[0]?.totalCount"
                      class="text-[var(--el-text-color-secondary)]"
                    >
                      ({{ runningTasks[0]?.processedCount || 0 }}/{{
                        runningTasks[0]?.totalCount
                      }}
                      条)
                    </span>
                  </span>
                </div>
                <div
                  class="h-2 overflow-hidden rounded-full bg-[var(--el-fill-color)]"
                >
                  <div
                    class="h-full rounded-full bg-[var(--el-color-primary)] transition-all duration-300"
                    :style="{ width: `${runningTasks[0]?.progress || 0}%` }"
                  ></div>
                </div>
              </div>
              <ElButton
                type="primary"
                :loading="exportLoading"
                :disabled="runningTasks.length > 0"
                class="w-full"
                @click="handleExport"
              >
                <template #icon>
                  <ArrowUpFromLine class="h-4 w-4" />
                </template>
                {{
                  exportLoading || runningTasks.length > 0
                    ? '导出中...'
                    : '导出 Excel'
                }}
              </ElButton>
            </div>
          </div>
        </ElTabPane>

        <!-- 进行中 Tab -->
        <ElTabPane label="进行中" name="running">
          <template #label>
            <span class="flex items-center gap-1">
              进行中
              <ElTag
                v-if="runningTasks.length > 0"
                type="primary"
                size="small"
                round
              >
                {{ runningTasks.length }}
              </ElTag>
            </span>
          </template>
          <div
            v-if="runningTasks.length === 0"
            class="py-8 text-center text-sm text-[var(--el-text-color-placeholder)]"
          >
            暂无进行中的任务
          </div>
          <ElScrollbar v-else max-height="250px">
            <div class="space-y-2">
              <div
                v-for="task in runningTasks"
                :key="task.id"
                class="flex items-center justify-between rounded-lg border border-[var(--el-border-color-lighter)] p-3"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--el-color-primary-light-9)]"
                  >
                    <Loader
                      class="h-4 w-4 animate-spin text-[var(--el-color-primary)]"
                    />
                  </div>
                  <div>
                    <div class="text-sm font-medium">{{ task.filename }}</div>
                    <div
                      class="text-xs text-[var(--el-text-color-placeholder)]"
                    >
                      开始于 {{ formatTime(task.startTime) }}
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <div class="flex flex-col items-end gap-1">
                    <div class="flex items-center gap-2 text-xs">
                      <span class="text-[var(--el-color-primary)]">
                        {{ task.progress || 0 }}%
                      </span>
                      <span
                        v-if="task.totalCount"
                        class="text-[var(--el-text-color-secondary)]"
                      >
                        {{ task.processedCount || 0 }}/{{ task.totalCount }}
                      </span>
                    </div>
                    <div
                      class="h-1.5 w-24 overflow-hidden rounded-full bg-[var(--el-fill-color)]"
                    >
                      <div
                        class="h-full rounded-full bg-[var(--el-color-primary)] transition-all duration-300"
                        :style="{ width: `${task.progress || 0}%` }"
                      ></div>
                    </div>
                  </div>
                  <ElPopconfirm
                    title="确定要取消此导出任务吗？"
                    confirm-button-text="确定"
                    cancel-button-text="取消"
                    @confirm="handleCancelTask(task)"
                  >
                    <template #reference>
                      <ElButton
                        type="danger"
                        size="small"
                        circle
                        title="取消导出"
                      >
                        <Square class="h-3 w-3" />
                      </ElButton>
                    </template>
                  </ElPopconfirm>
                </div>
              </div>
            </div>
          </ElScrollbar>
        </ElTabPane>

        <!-- 历史记录 Tab -->
        <ElTabPane label="历史" name="history">
          <div class="mb-2 flex justify-end">
            <ElButton
              v-if="completedTasks.length > 0"
              type="danger"
              link
              size="small"
              @click="handleClearHistory"
            >
              <template #icon>
                <Trash2 class="h-3 w-3" />
              </template>
              清除历史
            </ElButton>
          </div>
          <div
            v-if="completedTasks.length === 0"
            class="py-8 text-center text-sm text-[var(--el-text-color-placeholder)]"
          >
            暂无历史记录
          </div>
          <ElScrollbar v-else max-height="250px">
            <div class="space-y-2">
              <div
                v-for="task in completedTasks"
                :key="task.id"
                class="flex items-center justify-between rounded-lg border border-[var(--el-border-color-lighter)] p-3"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="flex h-8 w-8 items-center justify-center rounded-full"
                    :class="
                      task.type === 'import'
                        ? 'bg-[var(--el-color-success-light-9)]'
                        : 'bg-[var(--el-color-primary-light-9)]'
                    "
                  >
                    <Upload
                      v-if="task.type === 'import'"
                      class="h-4 w-4 text-[var(--el-color-success)]"
                    />
                    <Download
                      v-else
                      class="h-4 w-4 text-[var(--el-color-primary)]"
                    />
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <div class="text-sm font-medium">{{ task.filename }}</div>
                      <ElTag
                        v-if="isExpired(task)"
                        type="info"
                        size="small"
                        effect="plain"
                      >
                        已过期
                      </ElTag>
                    </div>
                    <div
                      class="text-xs text-[var(--el-text-color-placeholder)]"
                    >
                      {{ formatTime(task.endTime || task.startTime) }}
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <ElButton
                    v-if="task.status === 'failed' && task.type === 'export'"
                    type="primary"
                    link
                    size="small"
                    @click="handleRetry(task)"
                  >
                    <template #icon>
                      <RefreshCw class="h-3 w-3" />
                    </template>
                    重试
                  </ElButton>
                  <ElTag :type="getStatusType(task.status)" size="small">
                    {{ getStatusText(task.status) }}
                  </ElTag>
                </div>
              </div>
            </div>
          </ElScrollbar>
        </ElTabPane>
      </ElTabs>
    </div>
  </ElPopover>
</template>

<style scoped>
.import-export-manager :deep(.el-tabs__header) {
  margin-bottom: 12px;
}

.import-export-manager :deep(.el-upload-dragger) {
  padding: 0;
  border-color: var(--el-border-color);
}

.import-export-manager :deep(.el-upload-dragger:hover) {
  border-color: var(--el-color-primary);
}

.import-export-manager :deep(.el-collapse-item__header) {
  height: 32px;
  font-size: 12px;
  line-height: 32px;
  color: var(--el-color-danger);
}

.import-export-manager :deep(.el-collapse-item__content) {
  padding-bottom: 0;
}
</style>
