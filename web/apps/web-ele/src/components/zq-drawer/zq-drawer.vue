<script setup lang="ts">
import type { ZqDrawerEmits, ZqDrawerExpose, ZqDrawerProps } from './types';

import { computed, ref, useAttrs, watch } from 'vue';

import { Maximize, Minimize, X } from '@vben/icons';

import { ElButton, ElDrawer, ElScrollbar } from 'element-plus';

import './style.css';

defineOptions({
  name: 'ZqDrawer',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<ZqDrawerProps>(), {
  modelValue: false,
  title: '',
  size: '30%',
  direction: 'rtl',
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
  destroyOnClose: true,
  closeOnClickModal: false,
  appendToBody: true,
});

const emit = defineEmits<ZqDrawerEmits>();

const attrs = useAttrs();

const visible = ref(props.modelValue);
const isFullscreen = ref(props.defaultFullscreen);
const innerLoading = ref(props.loading);
const innerConfirmLoading = ref(props.confirmLoading);

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

watch(visible, (val) => {
  emit('update:modelValue', val);
  if (!val) {
    isFullscreen.value = props.defaultFullscreen;
  }
});

const drawerClass = computed(() => {
  const classes = ['zq-drawer'];
  if (isFullscreen.value) {
    classes.push('is-fullscreen');
  }
  return classes.join(' ');
});

const drawerSize = computed(() => {
  if (isFullscreen.value) {
    return '100%';
  }
  return props.size;
});

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

const scrollbarMaxHeight = computed(() => {
  if (isFullscreen.value) {
    return undefined;
  }
  if (props.maxHeight) {
    return typeof props.maxHeight === 'number'
      ? `${props.maxHeight}px`
      : props.maxHeight;
  }
  return undefined;
});

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value;
}

function handleClose() {
  visible.value = false;
}

function handleCancel() {
  emit('cancel');
  handleClose();
}

function handleConfirm() {
  emit('confirm');
}

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

const expose: ZqDrawerExpose = {
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
  <ElDrawer
    v-model="visible"
    :class="drawerClass"
    :title="undefined"
    :size="drawerSize"
    :direction="direction"
    :show-close="false"
    :destroy-on-close="destroyOnClose"
    :close-on-click-modal="closeOnClickModal"
    :append-to-body="appendToBody"
    v-bind="attrs"
    @open="handleOpen"
    @opened="handleOpened"
    @close="handleCloseEvent"
    @closed="handleClosed"
  >
    <template #header>
      <div class="flex w-full items-center justify-between">
        <span
          class="flex-1 truncate text-base font-medium text-[var(--el-text-color-primary)]"
        >
          <slot name="title">{{ title }}</slot>
        </span>
        <slot name="header-extra"></slot>
        <div class="ml-4 flex items-center gap-2">
          <span
            v-if="showFullscreenButton"
            class="flex h-7 w-7 cursor-pointer items-center justify-center rounded text-[var(--el-text-color-regular)] transition-all duration-200 hover:bg-[var(--el-fill-color-light)] hover:text-[var(--el-text-color-primary)]"
            title="全屏"
            @click="toggleFullscreen"
          >
            <Minimize v-if="isFullscreen" class="h-4 w-4" />
            <Maximize v-else class="h-4 w-4" />
          </span>
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

    <div v-loading="innerLoading" class="zq-drawer-body relative">
      <ElScrollbar :style="scrollbarStyle" :max-height="scrollbarMaxHeight">
        <div class="px-1">
          <slot></slot>
        </div>
      </ElScrollbar>
    </div>

    <template v-if="showFooter" #footer>
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <slot name="footer-left"></slot>
        </div>
        <div class="flex items-center gap-2">
          <slot name="footer-prepend"></slot>
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
          <slot name="footer-append"></slot>
        </div>
      </div>
    </template>
  </ElDrawer>
</template>
