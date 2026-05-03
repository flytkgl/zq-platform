<script lang="ts" setup>
import type { TaskLogEntry } from '#/api/core/scheduler';

import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElEmpty,
  ElProgress,
  ElScrollbar,
  ElTag,
} from 'element-plus';

import { subscribeTaskLogStream } from '#/api/core/scheduler';

interface Props {
  logId?: string;
  visible?: boolean;
}

defineOptions({ name: 'TaskLogStream' });

const props = withDefaults(defineProps<Props>(), {
  logId: undefined,
  visible: false,
});

const emit = defineEmits<{
  complete: [];
}>();

const logs = ref<TaskLogEntry[]>([]);
const isConnected = ref(false);
const isComplete = ref(false);
const progress = ref(0);
const currentStep = ref('');

let unsubscribe: (() => void) | null = null;

/**
 * 获取日志级别对应的标签类型
 */
function getLevelType(
  level: string,
): 'danger' | 'info' | 'primary' | 'success' | 'warning' {
  const typeMap: Record<
    string,
    'danger' | 'info' | 'primary' | 'success' | 'warning'
  > = {
    debug: 'info',
    error: 'danger',
    info: 'primary',
    success: 'success',
    warning: 'warning',
  };
  return typeMap[level] || 'info';
}

/**
 * 获取日志级别对应的图标
 */
function getLevelIcon(level: string): string {
  const iconMap: Record<string, string> = {
    debug: 'lucide:bug',
    error: 'lucide:x-circle',
    info: 'lucide:info',
    success: 'lucide:check-circle',
    warning: 'lucide:alert-triangle',
  };
  return iconMap[level] || 'lucide:info';
}

/**
 * 格式化时间戳
 */
function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      hour12: false,
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return timestamp;
  }
}

/**
 * 开始订阅日志
 */
function startSubscription() {
  if (!props.logId || unsubscribe) {
    return;
  }

  logs.value = [];
  isConnected.value = true;
  isComplete.value = false;
  progress.value = 0;
  currentStep.value = '';

  unsubscribe = subscribeTaskLogStream(
    props.logId,
    (entry) => {
      logs.value.push(entry);

      // 更新进度
      if (entry.progress !== undefined) {
        progress.value = entry.progress;
      }

      // 更新当前步骤
      if (entry.step) {
        currentStep.value = entry.step;
      }
    },
    (error) => {
      console.error('Task log stream error:', error);
      isConnected.value = false;
    },
    () => {
      isConnected.value = false;
      isComplete.value = true;
      emit('complete');
    },
  );
}

/**
 * 停止订阅
 */
function stopSubscription() {
  if (unsubscribe) {
    unsubscribe();
    unsubscribe = null;
  }
  isConnected.value = false;
}

/**
 * 清空日志
 */
function clearLogs() {
  logs.value = [];
  progress.value = 0;
  currentStep.value = '';
  isComplete.value = false;
}

// 监听 logId 变化
watch(
  () => props.logId,
  (newLogId) => {
    stopSubscription();
    if (newLogId && props.visible) {
      startSubscription();
    }
  },
);

// 监听 visible 变化
watch(
  () => props.visible,
  (newVisible) => {
    if (newVisible && props.logId) {
      startSubscription();
    } else {
      stopSubscription();
    }
  },
  { immediate: true },
);

// 组件挂载时启动订阅
onMounted(() => {
  if (props.visible && props.logId) {
    startSubscription();
  }
});

// 组件卸载时停止订阅
onBeforeUnmount(() => {
  stopSubscription();
});

// 暴露方法
defineExpose({
  clearLogs,
  startSubscription,
  stopSubscription,
});
</script>

<template>
  <div class="task-log-stream">
    <!-- 头部：进度和状态 -->
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium">{{
          $t('scheduler.executionProgress')
        }}</span>
        <ElTag v-if="isConnected" type="success" size="small">
          <IconifyIcon icon="lucide:radio" class="mr-1 size-3 animate-pulse" />
          {{ $t('scheduler.streaming') }}
        </ElTag>
        <ElTag v-else-if="isComplete" type="info" size="small">
          {{ $t('scheduler.streamComplete') }}
        </ElTag>
      </div>
      <ElButton
        v-if="logs.length > 0"
        type="info"
        text
        size="small"
        @click="clearLogs"
      >
        <IconifyIcon icon="lucide:trash-2" class="mr-1 size-4" />
        {{ $t('common.clear') }}
      </ElButton>
    </div>

    <!-- 进度条 -->
    <ElProgress
      v-if="progress > 0 || isConnected"
      :percentage="progress"
      :status="isComplete ? 'success' : undefined"
      :stroke-width="8"
      class="mb-4"
    />

    <!-- 当前步骤 -->
    <div
      v-if="currentStep && !isComplete"
      class="mb-4 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400"
    >
      <IconifyIcon icon="lucide:loader-2" class="size-4 animate-spin" />
      <span>{{ currentStep }}</span>
    </div>

    <!-- 日志列表 -->
    <ElScrollbar v-if="logs.length > 0" max-height="400px">
      <div class="space-y-2">
        <div
          v-for="(log, index) in logs"
          :key="index"
          class="flex items-start gap-2 rounded-lg border border-gray-100 p-3 dark:border-gray-800"
          :class="{
            'bg-red-50 dark:bg-red-900/10': log.level === 'error',
            'bg-yellow-50 dark:bg-yellow-900/10': log.level === 'warning',
            'bg-green-50 dark:bg-green-900/10': log.level === 'success',
          }"
        >
          <!-- 图标 -->
          <IconifyIcon
            :icon="getLevelIcon(log.level)"
            class="mt-0.5 size-4 flex-shrink-0"
            :class="{
              'text-red-500': log.level === 'error',
              'text-yellow-500': log.level === 'warning',
              'text-green-500': log.level === 'success',
              'text-blue-500': log.level === 'info',
              'text-gray-500': log.level === 'debug',
            }"
          />

          <!-- 内容 -->
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <ElTag :type="getLevelType(log.level)" size="small">
                {{ log.level.toUpperCase() }}
              </ElTag>
              <span class="text-xs text-gray-500">
                {{ formatTimestamp(log.timestamp) }}
              </span>
              <span v-if="log.step" class="text-xs text-gray-400">
                [{{ log.step }}]
              </span>
            </div>
            <div class="mt-1 text-sm">{{ log.message }}</div>
            <div
              v-if="log.data"
              class="mt-2 overflow-x-auto rounded bg-gray-100 p-2 font-mono text-xs dark:bg-gray-800"
            >
              <pre>{{ JSON.stringify(log.data, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </ElScrollbar>

    <!-- 空状态 -->
    <ElEmpty
      v-else-if="!isConnected"
      :description="$t('scheduler.noStreamLogs')"
      :image-size="80"
    />

    <!-- 等待连接 -->
    <div
      v-else
      class="flex flex-col items-center justify-center py-8 text-gray-500"
    >
      <IconifyIcon icon="lucide:loader-2" class="size-8 animate-spin" />
      <span class="mt-2 text-sm">{{ $t('scheduler.waitingForLogs') }}</span>
    </div>
  </div>
</template>

<style scoped>
.task-log-stream {
  padding: 16px;
}
</style>
