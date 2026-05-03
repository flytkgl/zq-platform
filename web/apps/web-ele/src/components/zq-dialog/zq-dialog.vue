<script setup lang="ts">
import type { ZqDialogEmits, ZqDialogExpose, ZqDialogProps } from './types';

import { computed, ref, useAttrs, watch } from 'vue';

import { Maximize, Minimize, X } from '@vben/icons';

import { ElButton, ElDialog, ElScrollbar } from 'element-plus';

import './style.css';

defineOptions({
  name: 'ZqDialog',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<ZqDialogProps>(), {
  modelValue: false,
  title: '',
  width: '50%',
  contentHeight: undefined,
  maxHeight: undefined,
  loading: false,
  confirmLoading: false,
  showFooter: true,
  showConfirmButton: true,
  showCancelButton: true,
  confirmText: '确定',
  cancelText: '取消',
  confirmButtonType: 'primary',
  showFullscreenButton: true,
  defaultFullscreen: false,
  showCloseButton: true,
  draggable: true,
  destroyOnClose: true,
  closeOnClickModal: false,
  appendToBody: true,
  beforeClose: undefined,
});

const emit = defineEmits<ZqDialogEmits>();

const attrs = useAttrs();

// 内部状态
const visible = ref(props.modelValue);
const isFullscreen = ref(props.defaultFullscreen);
const innerLoading = ref(props.loading);
const innerConfirmLoading = ref(props.confirmLoading);

// 监听 props 变化
watch(
  () => props.modelValue,
  (val) => {
    visible.value = val;
  },
);

watch(
  () => props.loading,
  (val) => {
    innerLoading.value = val;
  },
);

watch(
  () => props.confirmLoading,
  (val) => {
    innerConfirmLoading.value = val;
  },
);

// 监听内部状态变化，同步到外部
watch(visible, (val) => {
  emit('update:modelValue', val);
  // 关闭时重置全屏状态为默认值
  if (!val) {
    isFullscreen.value = props.defaultFullscreen;
  }
});

// 计算 dialog class
const dialogClass = computed(() => {
  const classes = ['zq-dialog'];
  if (isFullscreen.value) {
    classes.push('is-fullscreen');
  }
  return classes.join(' ');
});

// 计算滚动区域样式
const scrollbarStyle = computed(() => {
  const style: Record<string, string> = {};
  if (props.contentHeight) {
    style.height =
      typeof props.contentHeight === 'number'
        ? `${props.contentHeight}px`
        : props.contentHeight;
  }
  return style;
});

// 计算滚动区域最大高度
const scrollbarMaxHeight = computed(() => {
  if (isFullscreen.value) {
    return undefined; // 全屏时由 CSS 控制
  }
  if (props.maxHeight) {
    return typeof props.maxHeight === 'number'
      ? `${props.maxHeight}px`
      : props.maxHeight;
  }
  // 默认最大高度为视口高度减去 header、footer 和边距的空间
  // 预留约 200px 给 header、footer 和边距
  return 'calc(100vh - 200px)';
});

// 切换全屏
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value;
}

// 关闭对话框
function handleClose() {
  if (props.beforeClose) {
    props.beforeClose(() => {
      visible.value = false;
    });
  } else {
    visible.value = false;
  }
}

// 取消
function handleCancel() {
  emit('cancel');
  handleClose();
}

// 确认
function handleConfirm() {
  emit('confirm');
}

// 事件处理
function handleOpen() {
  emit('open');
}

function handleOpened() {
  emit('opened');
}

function handleCloseEvent() {
  emit('close');
}

function handleClosed() {
  emit('closed');
}

// 暴露方法
const expose: ZqDialogExpose = {
  open: () => {
    visible.value = true;
  },
  close: () => {
    visible.value = false;
  },
  setLoading: (val: boolean) => {
    innerLoading.value = val;
  },
  setConfirmLoading: (val: boolean) => {
    innerConfirmLoading.value = val;
  },
};

defineExpose(expose);
</script>

<template>
  <ElDialog
    v-model="visible"
    :class="dialogClass"
    :title="undefined"
    :width="typeof props.width === 'number' ? `${props.width}px` : props.width"
    :show-close="false"
    :draggable="draggable"
    :destroy-on-close="destroyOnClose"
    :close-on-click-modal="closeOnClickModal"
    :append-to-body="appendToBody"
    :fullscreen="isFullscreen"
    align-center
    v-bind="attrs"
    @open="handleOpen"
    @opened="handleOpened"
    @close="handleCloseEvent"
    @closed="handleClosed"
    header-class="!px-1"
  >
    <!-- 自定义 Header -->
    <template #header>
      <div class="flex w-full items-center justify-between">
        <span
          class="flex-1 truncate text-base font-medium text-[var(--el-text-color-primary)]"
        >
          <slot name="title">{{ title }}</slot>
        </span>
        <slot name="header-extra"></slot>
        <div class="ml-4 flex items-center gap-2">
          <!-- 全屏按钮 -->
          <span
            v-if="showFullscreenButton"
            class="flex h-7 w-7 cursor-pointer items-center justify-center rounded text-[var(--el-text-color-regular)] transition-all duration-200 hover:bg-[var(--el-fill-color-light)] hover:text-[var(--el-text-color-primary)]"
            title="全屏"
            @click="toggleFullscreen"
          >
            <Minimize v-if="isFullscreen" class="h-4 w-4" />
            <Maximize v-else class="h-4 w-4" />
          </span>
          <!-- 关闭按钮 -->
          <span
            v-if="showCloseButton"
            class="flex h-7 w-7 cursor-pointer items-center justify-center rounded text-[var(--el-text-color-regular)] transition-all duration-200 hover:bg-[var(--el-color-danger-light-9)] hover:text-[var(--el-color-danger)]"
            title="关闭"
            @click="handleClose"
          >
            <X class="h-4 w-4" />
          </span>
        </div>
      </div>
    </template>

    <!-- 内容区：ElScrollbar + Loading -->
    <div v-loading="innerLoading" class="zq-dialog-body relative">
      <ElScrollbar :style="scrollbarStyle" :max-height="scrollbarMaxHeight">
        <div class="px-1">
          <slot></slot>
        </div>
      </ElScrollbar>
    </div>

    <!-- Footer -->
    <template v-if="showFooter" #footer>
      <slot name="footer">
        <ElButton v-if="showCancelButton" @click="handleCancel">
          {{ cancelText }}
        </ElButton>
        <ElButton
          v-if="showConfirmButton"
          :type="confirmButtonType"
          :loading="innerConfirmLoading"
          @click="handleConfirm"
        >
          {{ confirmText }}
        </ElButton>
      </slot>
    </template>
  </ElDialog>
</template>
