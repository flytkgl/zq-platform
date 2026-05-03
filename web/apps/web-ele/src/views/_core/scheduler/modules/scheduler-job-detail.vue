<script lang="ts" setup>
import type { SchedulerLog } from '#/api/core/scheduler';

import { computed, onMounted, ref, watch } from 'vue';

import { ElRefreshRight, IconifyIcon } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElButtonGroup,
  ElCard,
  ElDialog,
  ElEmpty,
  ElPopover,
  ElScrollbar,
  ElSkeleton,
  ElSkeletonItem,
  ElTag,
  ElTooltip,
} from 'element-plus';

import {
  getSchedulerLogByJobApi,
  getSchedulerLogListApi,
} from '#/api/core/scheduler';

import TaskLogStream from './task-log-stream.vue';

interface Props {
  jobId?: string;
}

defineOptions({ name: 'SchedulerJobDetail' });

const props = defineProps<Props>();

const logs = ref<SchedulerLog[]>([]);
const loading = ref(false);
const isLoadingMore = ref(false);
const currentPage = ref(1);
const pageSize = ref(20);
const totalItems = ref(0);
const hasLoadedMore = ref(false);
const viewMode = ref<'card' | 'list'>('card'); // 视图模式：list-列表，card-卡片

// 实时日志弹窗
const liveLogDialogVisible = ref(false);
const currentLiveLogId = ref<string | undefined>(undefined);
const currentLiveLogName = ref('');

// 是否还有更多数据
const hasMoreData = computed(() => {
  const totalLoaded = currentPage.value * pageSize.value;
  return totalLoaded < totalItems.value;
});

/**
 * 获取状态显示文本
 */
function getStatusText(status: string) {
  const textMap: Record<string, string> = {
    success: $t('scheduler.status.success'),
    failed: $t('scheduler.status.failed'),
    running: $t('scheduler.status.running'),
    pending: $t('scheduler.status.pending'),
    timeout: $t('scheduler.status.timeout'),
    skipped: $t('scheduler.status.skipped'),
  };
  return textMap[status] || status;
}

/**
 * 获取任务日志
 * 如果 jobId 不存在，则加载所有任务的日志
 */
async function loadJobLogs(isLoadMore = false) {
  if (isLoadMore) {
    isLoadingMore.value = true;
  } else {
    loading.value = true;
    currentPage.value = 1;
    hasLoadedMore.value = false;
  }

  try {
    let response;

    // 如果有 jobId，加载特定任务的日志；否则加载所有任务的日志
    response = await (props.jobId
      ? getSchedulerLogByJobApi(props.jobId, {
          page: currentPage.value,
          pageSize: pageSize.value,
        })
      : getSchedulerLogListApi({
          page: currentPage.value,
          pageSize: pageSize.value,
        }));

    logs.value =
      currentPage.value === 1
        ? response.items || []
        : [...logs.value, ...(response.items || [])];
    totalItems.value = response.total || 0;
  } finally {
    if (isLoadMore) {
      isLoadingMore.value = false;
    } else {
      loading.value = false;
    }
  }
}

/**
 * 处理滚动到底部
 */
async function handleScrollToBottom() {
  if (isLoadingMore.value || !hasMoreData.value || loading.value) {
    return;
  }

  hasLoadedMore.value = true;
  currentPage.value += 1;
  await loadJobLogs(true);
}

/**
 * 重新加载
 */
async function reload() {
  await loadJobLogs(false);
}

/**
 * 打开实时日志弹窗
 */
function openLiveLogDialog(logId: string, jobName: string) {
  currentLiveLogId.value = logId;
  currentLiveLogName.value = jobName;
  liveLogDialogVisible.value = true;
}

/**
 * 实时日志完成回调
 */
function onLiveLogComplete() {
  // 刷新日志列表
  reload();
}

// 监听 jobId 变化
watch(
  () => props.jobId,
  () => {
    reload();
  },
);

// 组件挂载时加载日志
onMounted(() => {
  reload();
});
</script>

<template>
  <ElCard
    shadow="never"
    style="border: none"
    class="flex h-full flex-col"
    :body-style="{
      display: 'flex',
      flexDirection: 'column',
      flex: 1,
      padding: '0',
      overflow: 'hidden',
      minHeight: 0,
    }"
  >
    <template #header>
      <div class="flex w-full items-center justify-between">
        <span>{{ $t('scheduler.executionLogs') }}</span>

        <!-- 视图模式切换按钮和刷新按钮 -->
        <div class="flex items-center gap-2">
          <ElButtonGroup class="view-mode-toggle">
            <ElTooltip :content="$t('scheduler.cardView')" placement="bottom">
              <ElButton
                :type="viewMode === 'card' ? 'primary' : 'default'"
                @click="viewMode = 'card'"
              >
                <IconifyIcon icon="lucide:layout-grid" class="icon" />
              </ElButton>
            </ElTooltip>
            <ElTooltip :content="$t('scheduler.listView')" placement="bottom">
              <ElButton
                :type="viewMode === 'list' ? 'primary' : 'default'"
                @click="viewMode = 'list'"
              >
                <IconifyIcon icon="lucide:list" class="icon" />
              </ElButton>
            </ElTooltip>
          </ElButtonGroup>

          <!-- 刷新按钮 -->
          <ElTooltip :content="$t('scheduler.refresh')" placement="bottom">
            <ElButton circle @click="reload">
              <ElRefreshRight
                class="h-4 w-4"
                :class="{ 'animate-spin': loading }"
              />
            </ElButton>
          </ElTooltip>
        </div>
      </div>
    </template>

    <!-- 日志列表 -->
    <ElScrollbar
      class="log-scrollbar"
      :distance="40"
      @end-reached="handleScrollToBottom"
    >
      <div class="p-4">
        <!-- 加载中的骨架屏 -->
        <ElSkeleton :loading="loading" animated>
          <template #template>
            <!-- 列表视图骨架屏 -->
            <div v-if="viewMode === 'list'" class="space-y-2">
              <template v-for="_ in 20" :key="_">
                <div
                  class="rounded-lg border border-gray-200 p-3 dark:border-gray-700"
                >
                  <!-- 第一行：状态标签 + 任务名称 + 详情按钮 -->
                  <div class="mb-2 flex items-center justify-between">
                    <div class="flex min-w-0 flex-1 items-center gap-2">
                      <!-- 状态标签骨架 -->
                      <ElSkeletonItem
                        variant="text"
                        style="width: 50px; height: 22px; border-radius: 4px"
                      />
                      <!-- 任务名称骨架 -->
                      <ElSkeletonItem
                        variant="text"
                        style="width: 120px; height: 16px"
                      />
                      <!-- 任务编码骨架 -->
                      <ElSkeletonItem
                        variant="text"
                        style="width: 80px; height: 12px"
                      />
                    </div>
                    <!-- 详情按钮骨架 -->
                    <ElSkeletonItem
                      variant="circle"
                      style="width: 20px; height: 20px"
                    />
                  </div>
                  <!-- 第二行：开始时间 + 持续时间 -->
                  <div class="flex items-center justify-between">
                    <ElSkeletonItem
                      variant="text"
                      style="width: 140px; height: 14px"
                    />
                    <div class="flex items-center gap-2">
                      <ElSkeletonItem
                        variant="text"
                        style="width: 60px; height: 14px"
                      />
                    </div>
                  </div>
                </div>
              </template>
            </div>

            <!-- 卡片视图骨架屏 -->
            <div
              v-else
              class="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4"
            >
              <template v-for="_ in 20" :key="_">
                <div
                  class="flex flex-col gap-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700"
                >
                  <!-- 顶部：状态标签 + 详情按钮 -->
                  <div class="flex items-center justify-between">
                    <ElSkeletonItem
                      variant="text"
                      style="width: 50px; height: 20px; border-radius: 4px"
                    />
                    <ElSkeletonItem
                      variant="circle"
                      style="width: 20px; height: 20px"
                    />
                  </div>

                  <!-- 任务信息 -->
                  <div class="flex flex-col gap-1">
                    <ElSkeletonItem
                      variant="text"
                      style="width: 100%; height: 18px"
                    />
                    <ElSkeletonItem
                      variant="text"
                      style="width: 70%; height: 12px"
                    />
                  </div>

                  <!-- 时间信息 -->
                  <div
                    class="flex flex-col gap-1 border-t border-gray-100 pt-3 dark:border-gray-800"
                  >
                    <div class="flex items-center justify-between">
                      <ElSkeletonItem
                        variant="text"
                        style="width: 60px; height: 12px"
                      />
                      <ElSkeletonItem
                        variant="text"
                        style="width: 100px; height: 12px"
                      />
                    </div>
                    <div class="flex items-center justify-between">
                      <ElSkeletonItem
                        variant="text"
                        style="width: 60px; height: 12px"
                      />
                      <ElSkeletonItem
                        variant="text"
                        style="width: 40px; height: 12px"
                      />
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </template>
          <template #default>
            <!-- 列表视图 -->
            <div
              v-if="logs.length > 0 && viewMode === 'list'"
              class="space-y-2"
            >
              <template v-for="log in logs" :key="log.id">
                <!-- 日志项 -->
                <div
                  class="hover:border-primary rounded-lg border border-gray-200 p-3 transition-all hover:shadow-md dark:border-gray-700"
                >
                  <!-- 第一行：左侧状态标签 + 任务名称 + 最右侧详情按钮 -->
                  <div class="mb-2 flex items-center justify-between">
                    <div class="flex min-w-0 flex-1 items-center gap-2">
                      <!-- 状态标签 -->
                      <ElTag
                        :type="
                          log.status === 'success'
                            ? 'success'
                            : log.status === 'failed'
                              ? 'danger'
                              : log.status === 'running'
                                ? 'warning'
                                : 'info'
                        "
                        class="flex-shrink-0"
                      >
                        {{ getStatusText(log.status) }}
                      </ElTag>
                      <span
                        v-if="log.job_name"
                        class="truncate text-sm font-medium"
                        >{{ log.job_name }}</span
                      >
                      <span v-if="log.job_code" class="text-xs text-gray-500">{{
                        log.job_code
                      }}</span>
                    </div>
                    <!-- 操作按钮 -->
                    <div class="flex flex-shrink-0 items-center gap-1">
                      <!-- 查看实时日志按钮（仅 running 状态显示） -->
                      <ElTooltip
                        v-if="log.status === 'running'"
                        :content="$t('scheduler.viewLiveLogs')"
                        placement="top"
                      >
                        <ElButton
                          type="warning"
                          text
                          size="small"
                          @click="openLiveLogDialog(log.id, log.job_name || '')"
                        >
                          <IconifyIcon
                            icon="lucide:radio"
                            class="size-4 animate-pulse"
                          />
                        </ElButton>
                      </ElTooltip>
                      <!-- 详情按钮 -->
                      <ElPopover placement="left" :width="400">
                        <template #reference>
                          <ElButton type="primary" text size="small">
                            <IconifyIcon icon="ep:info-filled" class="size-4" />
                          </ElButton>
                        </template>

                        <!-- Popover 内容：详细日志信息 -->
                        <div class="space-y-2 text-sm">
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.jobName') }}:</span
                            >
                            <span class="font-medium">{{
                              log.job_name || '-'
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.jobCode') }}:</span
                            >
                            <span class="font-medium">{{
                              log.job_code || '-'
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.executionLogs') }}:</span
                            >
                            <span class="font-medium">{{
                              getStatusText(log.status)
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.startTime') }}:</span
                            >
                            <span class="font-medium">{{
                              log.start_time || '-'
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.endTime') }}:</span
                            >
                            <span class="font-medium">{{
                              log.end_time || '-'
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.duration') }}:</span
                            >
                            <span class="font-medium">{{
                              log.duration ? `${log.duration}s` : '-'
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.retryCount') }}:</span
                            >
                            <span class="font-medium">{{
                              log.retry_count || 0
                            }}</span>
                          </div>
                          <div
                            v-if="log.result"
                            class="border-t border-gray-200 pt-2 dark:border-gray-700"
                          >
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.executionResult') }}:</span
                            >
                            <div
                              class="mt-1 max-h-32 overflow-y-auto break-words rounded bg-gray-100 p-2 text-xs dark:bg-gray-800"
                            >
                              {{ log.result }}
                            </div>
                          </div>
                          <div v-if="log.exception" class="pt-2">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.exceptionInfo') }}:</span
                            >
                            <div
                              class="mt-1 max-h-32 overflow-y-auto break-words rounded bg-red-50 p-2 text-xs text-red-700 dark:bg-red-900/20 dark:text-red-400"
                            >
                              {{ log.exception }}
                            </div>
                          </div>
                          <div v-if="log.traceback" class="pt-2">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.stackTrace') }}:</span
                            >
                            <div
                              class="mt-1 max-h-32 overflow-y-auto break-words rounded bg-gray-100 p-2 font-mono text-xs dark:bg-gray-800"
                            >
                              {{ log.traceback }}
                            </div>
                          </div>
                        </div>
                      </ElPopover>
                    </div>
                  </div>

                  <!-- 第二行：左侧开始时间 + 最右侧持续时间 -->
                  <div
                    class="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400"
                  >
                    <span>{{ log.start_time || '-' }}</span>
                    <div class="flex flex-shrink-0 items-center gap-2">
                      <span
                        v-if="log.retry_count"
                        class="text-orange-600 dark:text-orange-400"
                      >
                        {{
                          $t('scheduler.retryTimes', { count: log.retry_count })
                        }}
                      </span>
                      <span v-if="log.duration" class="font-medium">
                        {{ log.duration }}s
                      </span>
                    </div>
                  </div>
                </div>
              </template>
            </div>

            <!-- 卡片视图 -->
            <div
              v-else-if="logs.length > 0 && viewMode === 'card'"
              class="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4"
            >
              <template v-for="log in logs" :key="log.id">
                <!-- 日志卡片 -->
                <div
                  class="hover:border-primary flex flex-col gap-3 rounded-lg border border-gray-200 p-4 transition-all hover:shadow-lg dark:border-gray-700"
                >
                  <!-- 顶部：状态标签 -->
                  <div class="flex items-center justify-between">
                    <ElTag
                      :type="
                        log.status === 'success'
                          ? 'success'
                          : log.status === 'failed'
                            ? 'danger'
                            : log.status === 'running'
                              ? 'warning'
                              : 'info'
                      "
                      size="small"
                    >
                      {{ getStatusText(log.status) }}
                    </ElTag>
                    <div class="flex items-center gap-1">
                      <!-- 查看实时日志按钮（仅 running 状态显示） -->
                      <ElTooltip
                        v-if="log.status === 'running'"
                        :content="$t('scheduler.viewLiveLogs')"
                        placement="top"
                      >
                        <ElButton
                          type="warning"
                          text
                          size="small"
                          @click="openLiveLogDialog(log.id, log.job_name || '')"
                        >
                          <IconifyIcon
                            icon="lucide:radio"
                            class="size-4 animate-pulse"
                          />
                        </ElButton>
                      </ElTooltip>
                      <ElPopover placement="left" :width="400">
                        <template #reference>
                          <ElButton type="primary" text size="small">
                            <IconifyIcon icon="ep:info-filled" class="size-4" />
                          </ElButton>
                        </template>

                        <!-- Popover 内容 -->
                        <div class="space-y-2 text-sm">
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.jobName') }}:</span
                            >
                            <span class="font-medium">{{
                              log.job_name || '-'
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.jobCode') }}:</span
                            >
                            <span class="font-medium">{{
                              log.job_code || '-'
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.executionLogs') }}:</span
                            >
                            <span class="font-medium">{{
                              getStatusText(log.status)
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.startTime') }}:</span
                            >
                            <span class="font-medium">{{
                              log.start_time || '-'
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.endTime') }}:</span
                            >
                            <span class="font-medium">{{
                              log.end_time || '-'
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.duration') }}:</span
                            >
                            <span class="font-medium">{{
                              log.duration ? `${log.duration}s` : '-'
                            }}</span>
                          </div>
                          <div class="flex justify-between">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.retryCount') }}:</span
                            >
                            <span class="font-medium">{{
                              log.retry_count || 0
                            }}</span>
                          </div>
                          <div
                            v-if="log.result"
                            class="border-t border-gray-200 pt-2 dark:border-gray-700"
                          >
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.executionResult') }}:</span
                            >
                            <div
                              class="mt-1 max-h-32 overflow-y-auto break-words rounded bg-gray-100 p-2 text-xs dark:bg-gray-800"
                            >
                              {{ log.result }}
                            </div>
                          </div>
                          <div v-if="log.exception" class="pt-2">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.exceptionInfo') }}:</span
                            >
                            <div
                              class="mt-1 max-h-32 overflow-y-auto break-words rounded bg-red-50 p-2 text-xs text-red-700 dark:bg-red-900/20 dark:text-red-400"
                            >
                              {{ log.exception }}
                            </div>
                          </div>
                          <div v-if="log.traceback" class="pt-2">
                            <span class="text-gray-600 dark:text-gray-400"
                              >{{ $t('scheduler.stackTrace') }}:</span
                            >
                            <div
                              class="mt-1 max-h-32 overflow-y-auto break-words rounded bg-gray-100 p-2 font-mono text-xs dark:bg-gray-800"
                            >
                              {{ log.traceback }}
                            </div>
                          </div>
                        </div>
                      </ElPopover>
                    </div>
                  </div>

                  <!-- 任务信息 -->
                  <div class="flex flex-col gap-1">
                    <div
                      v-if="log.job_name"
                      class="truncate text-base font-medium"
                      :title="log.job_name"
                    >
                      {{ log.job_name }}
                    </div>
                    <div
                      v-if="log.job_code"
                      class="truncate text-xs text-gray-500"
                      :title="log.job_code"
                    >
                      {{ log.job_code }}
                    </div>
                  </div>

                  <!-- 时间信息 -->
                  <div
                    class="flex flex-col gap-1 border-t border-gray-100 pt-3 text-xs text-gray-600 dark:border-gray-800 dark:text-gray-400"
                  >
                    <div class="flex items-center justify-between">
                      <span class="text-gray-500">{{
                        $t('scheduler.startTime')
                      }}</span>
                      <span class="font-mono">{{ log.start_time || '-' }}</span>
                    </div>
                    <div class="flex items-center justify-between">
                      <span class="text-gray-500">{{
                        $t('scheduler.duration')
                      }}</span>
                      <span
                        class="font-mono"
                        :class="
                          log.duration && log.duration > 60
                            ? 'text-orange-600'
                            : ''
                        "
                      >
                        {{ log.duration ? `${log.duration}s` : '-' }}
                      </span>
                    </div>
                    <div
                      v-if="log.retry_count"
                      class="flex items-center justify-between"
                    >
                      <span class="text-gray-500">{{
                        $t('scheduler.retryCount')
                      }}</span>
                      <span class="font-medium text-orange-600">{{
                        log.retry_count
                      }}</span>
                    </div>
                  </div>

                  <!-- 结果预览（如果有异常）-->
                  <div
                    v-if="log.exception"
                    class="truncate rounded bg-red-50 p-2 text-xs text-red-700 dark:bg-red-900/20 dark:text-red-400"
                  >
                    {{ log.exception }}
                  </div>
                </div>
              </template>
            </div>

            <!-- 加载更多提示 -->
            <div
              v-if="isLoadingMore"
              class="flex items-center justify-center py-4"
            >
              <div class="loading-spinner"></div>
              <span class="ml-2 text-sm text-gray-500">{{
                $t('scheduler.loading')
              }}</span>
            </div>

            <!-- 无更多数据提示 -->
            <div
              v-else-if="logs.length > 0 && !hasMoreData && hasLoadedMore"
              class="py-4 text-center text-sm text-gray-500"
            >
              {{ $t('scheduler.allLogsLoaded') }}
            </div>

            <!-- 空状态 -->
            <div
              v-else-if="logs.length === 0"
              class="flex items-center justify-center py-8"
            >
              <ElEmpty :description="$t('scheduler.noLogs')" />
            </div>
          </template>
        </ElSkeleton>
      </div>
    </ElScrollbar>
  </ElCard>

  <!-- 实时日志弹窗 -->
  <ElDialog
    v-model="liveLogDialogVisible"
    :title="`${$t('scheduler.viewLiveLogs')} - ${currentLiveLogName}`"
    width="700px"
    destroy-on-close
  >
    <TaskLogStream
      :log-id="currentLiveLogId"
      :visible="liveLogDialogVisible"
      @complete="onLiveLogComplete"
    />
  </ElDialog>
</template>

<style scoped>
:deep(.el-card) {
  border: none;
  box-shadow: 0 1px 3px rgb(0 0 0 / 10%);
}

.log-scrollbar {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.view-mode-toggle .icon {
  width: 16px;
  height: 16px;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--el-color-primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
