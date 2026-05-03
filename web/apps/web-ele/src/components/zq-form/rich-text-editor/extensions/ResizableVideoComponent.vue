<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  RotateCcw,
  Trash2,
} from '@vben/icons';

import { NodeViewWrapper } from '@tiptap/vue-3';
import { ElButton, ElCheckbox, ElInputNumber } from 'element-plus';

import { getFileUrl } from '#/composables/useFileUrl';

const props = defineProps<{
  deleteNode: () => void;
  node: any;
  selected: boolean;
  updateAttributes: (attrs: Record<string, any>) => void;
}>();

// 状态
const isSelected = ref(false);
const showContextMenu = ref(false);
const contextMenuPosition = ref({ x: 0, y: 0 });
const showCustomSize = ref(false);
const keepRatio = ref(true);
const videoRef = ref<HTMLVideoElement | null>(null);
const originalSize = ref({ width: 0, height: 0 });

// 视频URL（响应式，支持token刷新）
const resolvedVideoSrc = ref('');

// 异步解析视频URL
async function resolveVideoUrl() {
  const id = props.node.attrs.id;
  const src = props.node.attrs.src;

  // 如果有文件ID，优先使用ID获取带token的URL
  if (id) {
    resolvedVideoSrc.value = await getFileUrl(id);
  } else if (src) {
    resolvedVideoSrc.value = src;
  } else {
    resolvedVideoSrc.value = '';
  }
}

// 监听属性变化
watch(
  () => [props.node.attrs.id, props.node.attrs.src],
  () => {
    resolveVideoUrl();
  },
  { immediate: true },
);

// 计算属性
const videoSrc = computed(() => resolvedVideoSrc.value);
const currentWidth = computed(() => {
  const w = props.node.attrs.width;
  if (typeof w === 'string' && w.endsWith('%')) {
    return Number.parseInt(w);
  }
  return w || 100;
});
const currentHeight = computed(() => props.node.attrs.height || 'auto');
const alignment = computed(() => props.node.attrs.alignment || 'center');

const nodeStyle = computed(() => {
  const styles: Record<string, string> = {
    display: 'flex',
  };

  if (alignment.value === 'left') {
    styles.justifyContent = 'flex-start';
  } else if (alignment.value === 'right') {
    styles.justifyContent = 'flex-end';
  } else {
    styles.justifyContent = 'center';
  }

  return styles;
});

const containerStyle = computed(() => {
  const styles: Record<string, string> = {};

  const w = props.node.attrs.width;
  if (typeof w === 'number') {
    styles.width = `${w}px`;
  } else if (typeof w === 'string') {
    styles.width = w;
  } else {
    styles.width = '100%';
  }

  return styles;
});

// 方法
const handleClick = () => {
  isSelected.value = true;
};

const handleContextMenu = (e: MouseEvent) => {
  e.preventDefault();
  e.stopPropagation();
  isSelected.value = true;
  showContextMenu.value = true;
  contextMenuPosition.value = { x: e.clientX, y: e.clientY };
};

const hideContextMenu = () => {
  showContextMenu.value = false;
  showCustomSize.value = false;
};

const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  if (
    !target.closest('.resizable-video-wrapper') &&
    !target.closest('.video-context-menu')
  ) {
    isSelected.value = false;
    hideContextMenu();
  }
};

const setAlignment = (align: 'center' | 'left' | 'right') => {
  props.updateAttributes({ alignment: align });
};

const setPresetSize = (percent: number) => {
  props.updateAttributes({ width: `${percent}%`, height: 'auto' });
  hideContextMenu();
};

const updateWidth = (value: number | undefined) => {
  if (!value) return;
  if (
    keepRatio.value &&
    originalSize.value.width &&
    originalSize.value.height
  ) {
    const ratio = originalSize.value.height / originalSize.value.width;
    props.updateAttributes({ width: value, height: Math.round(value * ratio) });
  } else {
    props.updateAttributes({ width: value });
  }
};

const updateHeight = (value: number | undefined) => {
  if (!value) return;
  if (
    keepRatio.value &&
    originalSize.value.width &&
    originalSize.value.height
  ) {
    const ratio = originalSize.value.width / originalSize.value.height;
    props.updateAttributes({ height: value, width: Math.round(value * ratio) });
  } else {
    props.updateAttributes({ height: value });
  }
};

const resetSize = () => {
  props.updateAttributes({ width: '100%', height: 'auto' });
  hideContextMenu();
};

const handleDelete = () => {
  props.deleteNode();
};

// 拖拽调整大小
const isResizing = ref(false);
const resizeStartPos = ref({ x: 0, y: 0 });
const resizeStartSize = ref({ width: 0, height: 0 });
const resizeCorner = ref('');

const startResize = (e: MouseEvent, corner: string) => {
  e.preventDefault();
  e.stopPropagation();
  isResizing.value = true;
  resizeCorner.value = corner;
  resizeStartPos.value = { x: e.clientX, y: e.clientY };

  const wrapper = (e.target as HTMLElement).closest(
    '.resizable-video-wrapper',
  ) as HTMLElement;
  if (wrapper) {
    resizeStartSize.value = {
      width: wrapper.offsetWidth,
      height: wrapper.offsetHeight,
    };
  }

  document.addEventListener('mousemove', handleResize);
  document.addEventListener('mouseup', stopResize);
};

const handleResize = (e: MouseEvent) => {
  if (!isResizing.value) return;

  const deltaX = e.clientX - resizeStartPos.value.x;

  // 左侧控制点需要反向计算
  const isLeftCorner =
    resizeCorner.value === 'nw' || resizeCorner.value === 'sw';
  const adjustedDeltaX = isLeftCorner ? -deltaX : deltaX;

  let newWidth = resizeStartSize.value.width + adjustedDeltaX;
  let newHeight = resizeStartSize.value.height;

  // 保持比例
  if (originalSize.value.width && originalSize.value.height) {
    const ratio = originalSize.value.height / originalSize.value.width;
    newHeight = Math.round(newWidth * ratio);
  }

  // 限制最小尺寸
  newWidth = Math.max(100, newWidth);
  newHeight = Math.max(60, newHeight);

  props.updateAttributes({ width: newWidth, height: newHeight });
};

const stopResize = () => {
  isResizing.value = false;
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
};

// 获取视频原始尺寸
const handleVideoLoaded = () => {
  if (videoRef.value) {
    originalSize.value = {
      width: videoRef.value.videoWidth,
      height: videoRef.value.videoHeight,
    };
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
});
</script>

<template>
  <NodeViewWrapper class="resizable-video-node" :style="nodeStyle">
    <div
      class="resizable-video-wrapper"
      :class="{ 'is-selected': isSelected || selected }"
      :style="containerStyle"
      @click="handleClick"
      @contextmenu="handleContextMenu"
    >
      <video
        ref="videoRef"
        :src="videoSrc"
        controls
        class="resizable-video"
        @loadedmetadata="handleVideoLoaded"
      >
        您的浏览器不支持视频播放
      </video>

      <!-- 调整大小的控制点 -->
      <template v-if="isSelected || selected">
        <div
          class="resize-handle resize-handle-se"
          @mousedown="startResize($event, 'se')"
        ></div>
        <div
          class="resize-handle resize-handle-sw"
          @mousedown="startResize($event, 'sw')"
        ></div>
        <div
          class="resize-handle resize-handle-ne"
          @mousedown="startResize($event, 'ne')"
        ></div>
        <div
          class="resize-handle resize-handle-nw"
          @mousedown="startResize($event, 'nw')"
        ></div>
      </template>
    </div>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <div
        v-if="showContextMenu"
        class="video-context-menu"
        :style="{
          left: `${contextMenuPosition.x}px`,
          top: `${contextMenuPosition.y}px`,
        }"
        @click.stop
      >
        <!-- 对齐方式 -->
        <div class="menu-section">
          <div class="menu-label">对齐方式</div>
          <div class="menu-buttons">
            <ElButton
              :type="alignment === 'left' ? 'primary' : 'default'"
              size="small"
              @click="setAlignment('left')"
            >
              <AlignLeft class="h-4 w-4" />
            </ElButton>
            <ElButton
              :type="alignment === 'center' ? 'primary' : 'default'"
              size="small"
              @click="setAlignment('center')"
            >
              <AlignCenter class="h-4 w-4" />
            </ElButton>
            <ElButton
              :type="alignment === 'right' ? 'primary' : 'default'"
              size="small"
              @click="setAlignment('right')"
            >
              <AlignRight class="h-4 w-4" />
            </ElButton>
          </div>
        </div>

        <!-- 快速缩放 -->
        <div class="menu-section">
          <div class="menu-label">快速缩放</div>
          <div class="menu-buttons">
            <ElButton size="small" @click="setPresetSize(25)">25%</ElButton>
            <ElButton size="small" @click="setPresetSize(50)">50%</ElButton>
            <ElButton size="small" @click="setPresetSize(75)">75%</ElButton>
            <ElButton size="small" @click="setPresetSize(100)">100%</ElButton>
          </div>
        </div>

        <!-- 自定义尺寸 -->
        <div class="menu-section">
          <ElButton
            size="small"
            class="w-full"
            @click="showCustomSize = !showCustomSize"
          >
            自定义尺寸
          </ElButton>
          <div v-if="showCustomSize" class="custom-size-panel">
            <div class="size-inputs">
              <div class="size-input-group">
                <span class="size-label">宽:</span>
                <ElInputNumber
                  :model-value="
                    typeof currentWidth === 'number' ? currentWidth : undefined
                  "
                  :min="100"
                  :max="1920"
                  size="small"
                  controls-position="right"
                  @update:model-value="updateWidth"
                />
              </div>
              <div class="size-input-group">
                <span class="size-label">高:</span>
                <ElInputNumber
                  :model-value="
                    typeof currentHeight === 'number'
                      ? currentHeight
                      : undefined
                  "
                  :min="60"
                  :max="1080"
                  size="small"
                  controls-position="right"
                  @update:model-value="updateHeight"
                />
              </div>
            </div>
            <ElCheckbox v-model="keepRatio" size="small">保持比例</ElCheckbox>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="menu-section menu-actions">
          <ElButton size="small" @click="resetSize">
            <RotateCcw class="mr-1 h-3 w-3" />
            重置尺寸
          </ElButton>
          <ElButton size="small" type="danger" @click="handleDelete">
            <Trash2 class="mr-1 h-3 w-3" />
            删除视频
          </ElButton>
        </div>
      </div>
    </Teleport>
  </NodeViewWrapper>
</template>

<style scoped>
.resizable-video-node {
  display: block;
  margin: 12px 0;
}

.resizable-video-wrapper {
  position: relative;
  display: inline-block;
  max-width: 100%;
  border-radius: 8px;
  transition: box-shadow 0.2s;
}

.resizable-video-wrapper:hover {
  box-shadow: 0 0 0 2px var(--el-color-primary-light-5);
}

.resizable-video-wrapper.is-selected {
  box-shadow: 0 0 0 2px var(--el-color-primary);
}

.resizable-video {
  display: block;
  width: 100%;
  height: auto;
  background-color: var(--el-fill-color-darker);
  border-radius: 8px;
}

/* 调整大小控制点 */
.resize-handle {
  position: absolute;
  z-index: 10;
  width: 12px;
  height: 12px;
  background-color: var(--el-color-primary);
  border: 2px solid var(--el-bg-color);
  border-radius: 50%;
}

.resize-handle-se {
  right: -6px;
  bottom: -6px;
  cursor: se-resize;
}

.resize-handle-sw {
  bottom: -6px;
  left: -6px;
  cursor: sw-resize;
}

.resize-handle-ne {
  top: -6px;
  right: -6px;
  cursor: ne-resize;
}

.resize-handle-nw {
  top: -6px;
  left: -6px;
  cursor: nw-resize;
}

/* 右键菜单 */
.video-context-menu {
  position: fixed;
  z-index: 9999;
  min-width: 200px;
  padding: 12px;
  background-color: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgb(0 0 0 / 15%);
}

.menu-section {
  margin-bottom: 12px;
}

.menu-section:last-child {
  margin-bottom: 0;
}

.menu-label {
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.menu-buttons {
  display: flex;
  gap: 4px;
}

.custom-size-panel {
  padding: 8px;
  margin-top: 8px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
}

.size-inputs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
}

.size-input-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.size-label {
  min-width: 24px;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.menu-actions {
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
