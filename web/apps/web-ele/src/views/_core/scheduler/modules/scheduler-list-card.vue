<script lang="ts" setup>
import type { SchedulerJob } from '#/api/core/scheduler';
import type { CardListOptions } from '#/components/card-list';

import { onMounted, ref } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElMessage,
  ElMessageBox,
  ElPopover,
  ElTooltip,
} from 'element-plus';

import {
  deleteSchedulerJobApi,
  executeSchedulerJobApi,
  getSchedulerJobListApi,
} from '#/api/core/scheduler';
import { CardList } from '#/components/card-list';
import { useAppContextStore } from '#/store/app-context';

import { getStatusName } from '../data';
import SchedulerFormModal from './scheduler-form-modal.vue';

const emit = defineEmits<{
  refresh: [];
  select: [jobId: string | undefined];
}>();

const appContextStore = useAppContextStore();

const jobList = ref<SchedulerJob[]>([]);
const loading = ref(false);
const selectedJobId = ref<string>();
const searchKeyword = ref<string>('');
const hoveredJobId = ref<string>();
const schedulerFormModalRef = ref<InstanceType<typeof SchedulerFormModal>>();
const dropdownOpenJobId = ref<string>(); // 追踪哪个任务的下拉菜单是打开的

// 卡片列表配置
const cardListOptions: CardListOptions<SchedulerJob> = {
  searchFields: [{ field: 'name' }, { field: 'code' }],
  titleField: 'name',
};

async function fetchJobList() {
  try {
    loading.value = true;
    const response = await getSchedulerJobListApi({
      page: 1,
      pageSize: 100,
      applicationId: appContextStore.currentApp?.id,
    });
    jobList.value = response.items || [];
  } finally {
    loading.value = false;
  }
}

/**
 * 处理任务选择
 */
function onJobSelect(jobId: string | undefined) {
  selectedJobId.value = jobId;
  emit('select', jobId);
}

/**
 * 打开添加任务对话框
 */
function onAddJob() {
  schedulerFormModalRef.value?.open();
}

/**
 * 打开编辑任务对话框
 */
function onEditJob(job: SchedulerJob, e?: Event) {
  e?.stopPropagation();
  schedulerFormModalRef.value?.open(job);
}

/**
 * 删除任务
 */
async function onDeleteJob(job: SchedulerJob, e?: Event) {
  e?.stopPropagation();

  ElMessageBox.confirm(
    $t('scheduler.deleteJobConfirm', { name: job.name }),
    $t('common.delete'),
    {
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
      type: 'warning',
      showClose: false,
    },
  )
    .then(async () => {
      try {
        await deleteSchedulerJobApi(job.id);
        ElMessage.success($t('ui.actionMessage.deleteSuccess', [job.name]));

        // 如果删除的是当前选中的任务，清除选中状态
        if (selectedJobId.value === job.id) {
          selectedJobId.value = undefined;
          emit('select', undefined);
        }

        await fetchJobList();
      } catch {
        ElMessage.error($t('ui.actionMessage.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

/**
 * 立即执行任务
 */
async function onExecuteJob(job: SchedulerJob, e?: Event) {
  e?.stopPropagation();

  try {
    await executeSchedulerJobApi({ job_id: job.id });
    ElMessage.success($t('scheduler.executeSuccess', { name: job.name }));
    await fetchJobList();
    emit('refresh');
  } catch {
    ElMessage.error($t('scheduler.executeFailed'));
  }
}

/**
 * 处理下拉菜单命令
 */
function handleDropdownCommand(command: string, job: SchedulerJob) {
  switch (command) {
    case 'delete': {
      onDeleteJob(job);
      break;
    }
    case 'execute': {
      onExecuteJob(job);
      break;
    }
  }
}

/**
 * 添加/编辑任务成功后的回调
 */
async function onFormSuccess() {
  ElMessage.success($t('scheduler.operationSuccess'));
  await fetchJobList();
  emit('refresh');
}

/**
 * 处理 hoveredId 更新
 * 如果下拉菜单打开，不清除 hoveredId
 */
function handleHoveredIdUpdate(id: string | undefined) {
  // 如果要清除 hoveredId，但有下拉菜单打开，则保持当前的 hoveredId
  if (id === undefined && dropdownOpenJobId.value) {
    return;
  }
  hoveredJobId.value = id;
}

/**
 * 处理下拉菜单可见性变化
 */
function handleDropdownVisibleChange(visible: boolean, jobId: string) {
  dropdownOpenJobId.value = visible ? jobId : undefined;
}

onMounted(() => {
  fetchJobList();
});
</script>

<template>
  <CardList
    :items="jobList"
    :loading="loading"
    :selected-id="selectedJobId"
    :hovered-id="hoveredJobId"
    :search-keyword="searchKeyword"
    :options="cardListOptions"
    @select="onJobSelect"
    @update:search-keyword="(v) => (searchKeyword = v)"
    @update:hovered-id="handleHoveredIdUpdate"
    @add="onAddJob"
    @edit="onEditJob"
    @delete="onDeleteJob"
  >
    <!-- 自定义项目渲染（标题行） -->
    <template #item="{ item }">
      <div class="truncate text-sm font-medium" :title="item.name">
        {{ item.name }}
      </div>
    </template>

    <!-- 详细信息（第二行） -->
    <template #details="{ item }">
      <div class="flex items-center gap-2 text-xs opacity-70">
        <!-- 任务编码 -->
        <span class="truncate" :title="item.code">
          {{ item.code }}
        </span>

        <!-- 应用名称 -->
        <template v-if="appContextStore.currentApp?.name">
          <span class="text-gray-400">|</span>
          <span class="truncate" :title="appContextStore.currentApp?.name">
            {{ appContextStore.currentApp?.name }}
          </span>
        </template>

        <!-- 分隔符 -->
        <span class="text-gray-400">|</span>

        <!-- 触发器类型 -->
        <span class="flex-shrink-0">
          {{
            item.trigger_type === 'cron'
              ? $t('scheduler.triggerCron')
              : item.trigger_type === 'interval'
                ? $t('scheduler.triggerInterval')
                : $t('scheduler.triggerDate')
          }}
        </span>

        <!-- 分隔符 -->
        <span class="text-gray-400">|</span>

        <!-- 任务状态 -->
        <span class="flex-shrink-0">
          {{ getStatusName(item.status) }}
        </span>

        <!-- 执行次数 -->
        <span v-if="item.total_run_count" class="flex-shrink-0">
          {{ $t('scheduler.executionCount') }}: {{ item.total_run_count }}
        </span>
      </div>
    </template>

    <!-- 操作按钮（第一行最右侧） -->
    <template #actions="{ item }">
      <div
        class="flex flex-shrink-0"
        @click.stop
        @mouseenter.stop
        @mouseleave.stop
      >
        <!-- 编辑按钮 -->
        <ElTooltip :content="$t('scheduler.editJob')" placement="top">
          <ElButton
            type="primary"
            text
            size="small"
            circle
            @click="onEditJob(item, $event)"
          >
            <IconifyIcon icon="ep:edit" class="size-4" />
          </ElButton>
        </ElTooltip>

        <!-- 详情按钮 -->
        <ElPopover placement="right" :width="400">
          <template #reference>
            <ElButton
              type="info"
              text
              size="small"
              style="margin-left: 0"
              circle
            >
              <IconifyIcon icon="ep:info-filled" class="size-4" />
            </ElButton>
          </template>

          <!-- Popover 内容：详细信息 -->
          <div class="space-y-2 p-3 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.jobName') }}:</span>
              <span class="font-medium">{{ item.name || '-' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.jobCode') }}:</span>
              <span class="font-medium">{{ item.code || '-' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.jobGroup') }}:</span>
              <span class="font-medium">{{ item.group || '-' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.triggerType') }}:</span>
              <span class="font-medium">
                {{
                  item.trigger_type === 'cron'
                    ? $t('scheduler.triggerCron')
                    : item.trigger_type === 'interval'
                      ? $t('scheduler.triggerInterval')
                      : $t('scheduler.triggerDate')
                }}
              </span>
            </div>
            <div v-if="item.cron_expression" class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.cronExpression') }}:</span>
              <span class="font-mono text-xs">{{ item.cron_expression }}</span>
            </div>
            <div v-if="item.interval_seconds" class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.intervalTime') }}:</span>
              <span class="font-medium">{{ item.interval_seconds
                }}{{ $t('scheduler.unit.seconds') }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.jobStatus') }}:</span>
              <span class="font-medium">{{ getStatusName(item.status) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.priority') }}:</span>
              <span class="font-medium">{{ item.priority }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.maxInstances') }}:</span>
              <span class="font-medium">{{ item.max_instances }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.maxRetries') }}:</span>
              <span class="font-medium">{{ item.max_retries }}</span>
            </div>
            <div v-if="item.timeout" class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.timeout') }}:</span>
              <span class="font-medium">{{ item.timeout }}{{ $t('scheduler.unit.seconds') }}</span>
            </div>
            <div class="border-t border-gray-200 pt-2 dark:border-gray-700">
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.totalRunCount') }}:</span>
                <span class="font-medium">{{ item.total_run_count }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.successCount') }}:</span>
                <span class="font-medium text-green-600">{{
                  item.success_count
                }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.failureCount') }}:</span>
                <span class="font-medium text-red-600">{{
                  item.failure_count
                }}</span>
              </div>
            </div>
            <div
              v-if="item.last_run_time"
              class="border-t border-gray-200 pt-2 dark:border-gray-700"
            >
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.lastRunTime') }}:</span>
                <span class="text-xs">{{ item.last_run_time }}</span>
              </div>
              <div v-if="item.next_run_time" class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.nextRunTime') }}:</span>
                <span class="text-xs">{{ item.next_run_time }}</span>
              </div>
            </div>
            <div
              v-if="item.description"
              class="border-t border-gray-200 pt-2 dark:border-gray-700"
            >
              <span class="text-gray-600 dark:text-gray-400">{{ $t('scheduler.description') }}:</span>
              <div
                class="mt-1 max-h-32 overflow-y-auto break-words rounded bg-gray-100 p-2 text-xs dark:bg-gray-800"
              >
                {{ item.description }}
              </div>
            </div>
          </div>
        </ElPopover>

        <!-- 更多操作下拉菜单 -->
        <ElDropdown
          trigger="click"
          :hide-on-click="true"
          :popper-options="{
            modifiers: [
              {
                name: 'offset',
                options: {
                  offset: [0, 8],
                },
              },
            ],
          }"
          @visible-change="
            (visible: boolean) => handleDropdownVisibleChange(visible, item.id)
          "
          @command="(cmd: string) => handleDropdownCommand(cmd, item)"
        >
          <ElButton type="info" text size="small" circle style="margin-left: 0">
            <IconifyIcon icon="ep:more-filled" class="size-4" />
          </ElButton>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem command="execute">
                <IconifyIcon icon="ep:video-play" class="mr-2 size-4" />
                {{ $t('scheduler.executeNow') }}
              </ElDropdownItem>
              <ElDropdownItem command="delete" divided>
                <IconifyIcon
                  icon="ep:delete"
                  class="mr-2 size-4 text-red-500"
                />
                <span class="text-red-500">{{
                  $t('scheduler.deleteJob')
                }}</span>
              </ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
      </div>
    </template>

    <!-- Modal 组件 -->
    <template #modal>
      <SchedulerFormModal
        ref="schedulerFormModalRef"
        @success="onFormSuccess"
      />
    </template>
  </CardList>
</template>

<style scoped>
/* 输入框前置图标样式 */
:deep(.el-input__icon) {
  cursor: pointer;
}

/* 文本按钮样式 */
:deep(.el-button--text) {
  padding: 0 4px;
}

/* Popover reference 样式 */
:deep(.el-popover__reference) {
  padding: 0;
}
</style>
