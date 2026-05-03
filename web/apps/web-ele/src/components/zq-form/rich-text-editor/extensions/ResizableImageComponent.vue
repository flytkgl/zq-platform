<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue';

import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Maximize2,
  RotateCw,
  Trash2,
} from '@vben/icons';

import { NodeViewWrapper } from '@tiptap/vue-3';
import { ElInputNumber } from 'element-plus';

const props = defineProps<{
  deleteNode: () => void;
  editor: any;
  node: any;
  selected: boolean;
  updateAttributes: (attrs: Record<string, any>) => void;
}>();

// 图片属性
const imgRef = ref<HTMLImageElement | null>(null);
const isResizing = ref(false);
const startX = ref(0);
const startY = ref(0);
const startWidth = ref(0);
const startHeight = ref(0);
const resizeDirection = ref<string>('');

// 右键菜单
const contextMenuVisible = ref(false);
const contextMenuPosition = ref({ x: 0, y: 0 });
const showSizePanel = ref(false);

// 尺寸输入
const widthInput = ref<number>(0);
const heightInput = ref<number>(0);
const keepRatio = ref(true);
const originalRatio = ref(1);

// 预设尺寸
const presetSizes = [
  { label: '25%', value: 25 },
  { label: '50%', value: 50 },
  { label: '75%', value: 75 },
  { label: '100%', value: 100 },
];

// 计算图片样式
const imageStyle = computed(() => {
  const style: Record<string, string> = {};
  if (props.node.attrs.width) {
    style.width =
      typeof props.node.attrs.width === 'number'
        ? `${props.node.attrs.width}px`
        : props.node.attrs.width;
  }
  if (props.node.attrs.height) {
    style.height =
      typeof props.node.attrs.height === 'number'
        ? `${props.node.attrs.height}px`
        : props.node.attrs.height;
  }
  return style;
});

// 计算容器样式（对齐）
const wrapperStyle = computed(() => {
  const alignment = props.node.attrs.alignment || 'center';
  const justifyMap: Record<string, string> = {
    left: 'flex-start',
    center: 'center',
    right: 'flex-end',
  };
  return {
    justifyContent: justifyMap[alignment] || 'center',
  };
});

// 图片加载完成后获取原始尺寸
const handleImageLoad = () => {
  if (imgRef.value) {
    const img = imgRef.value;
    originalRatio.value = img.naturalWidth / img.naturalHeight;

    if (props.node.attrs.width) {
      widthInput.value =
        typeof props.node.attrs.width === 'number'
          ? props.node.attrs.width
          : Number.parseInt(props.node.attrs.width) || img.naturalWidth;
      heightInput.value =
        typeof props.node.attrs.height === 'number'
          ? props.node.attrs.height
          : Number.parseInt(props.node.attrs.height) || img.naturalHeight;
    } else {
      widthInput.value = img.naturalWidth;
      heightInput.value = img.naturalHeight;
    }
  }
};

// 右键菜单
const handleContextMenu = (e: MouseEvent) => {
  e.preventDefault();
  e.stopPropagation();

  contextMenuPosition.value = { x: e.clientX, y: e.clientY };
  contextMenuVisible.value = true;
  showSizePanel.value = false;

  // 点击其他地方关闭菜单
  nextTick(() => {
    document.addEventListener('click', closeContextMenu);
    document.addEventListener('contextmenu', closeContextMenu);
  });
};

const closeContextMenu = () => {
  contextMenuVisible.value = false;
  showSizePanel.value = false;
  document.removeEventListener('click', closeContextMenu);
  document.removeEventListener('contextmenu', closeContextMenu);
};

// 开始调整大小
const startResize = (e: MouseEvent, direction: string) => {
  e.preventDefault();
  e.stopPropagation();

  isResizing.value = true;
  resizeDirection.value = direction;
  startX.value = e.clientX;
  startY.value = e.clientY;

  if (imgRef.value) {
    startWidth.value = imgRef.value.offsetWidth;
    startHeight.value = imgRef.value.offsetHeight;
  }

  document.addEventListener('mousemove', handleResize);
  document.addEventListener('mouseup', stopResize);
};

// 处理调整大小
const handleResize = (e: MouseEvent) => {
  if (!isResizing.value) return;

  const deltaX = e.clientX - startX.value;
  const deltaY = e.clientY - startY.value;

  let newWidth = startWidth.value;
  let newHeight = startHeight.value;

  if (resizeDirection.value.includes('e')) {
    newWidth = Math.max(50, startWidth.value + deltaX);
  }
  if (resizeDirection.value.includes('w')) {
    newWidth = Math.max(50, startWidth.value - deltaX);
  }
  if (resizeDirection.value.includes('s')) {
    newHeight = Math.max(50, startHeight.value + deltaY);
  }
  if (resizeDirection.value.includes('n')) {
    newHeight = Math.max(50, startHeight.value - deltaY);
  }

  // 保持比例
  if (keepRatio.value && originalRatio.value) {
    if (
      resizeDirection.value.includes('e') ||
      resizeDirection.value.includes('w')
    ) {
      newHeight = Math.round(newWidth / originalRatio.value);
    } else {
      newWidth = Math.round(newHeight * originalRatio.value);
    }
  }

  props.updateAttributes({
    width: newWidth,
    height: newHeight,
  });

  widthInput.value = newWidth;
  heightInput.value = newHeight;
};

// 停止调整大小
const stopResize = () => {
  isResizing.value = false;
  resizeDirection.value = '';
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
};

// 设置对齐方式
const setAlignment = (alignment: 'center' | 'left' | 'right') => {
  props.updateAttributes({ alignment });
  closeContextMenu();
};

// 设置预设尺寸（百分比）
const setPresetSize = (percent: number) => {
  if (imgRef.value) {
    const editorEl = props.editor?.view?.dom?.parentElement;
    const containerWidth = editorEl?.clientWidth || 800;
    const maxWidth = containerWidth - 32;

    const newWidth = Math.round((maxWidth * percent) / 100);
    const newHeight = Math.round(newWidth / originalRatio.value);

    props.updateAttributes({
      width: newWidth,
      height: newHeight,
    });

    widthInput.value = newWidth;
    heightInput.value = newHeight;
  }
  closeContextMenu();
};

// 切换自定义尺寸面板
const toggleSizePanel = () => {
  showSizePanel.value = !showSizePanel.value;
};

// 手动输入宽度
const handleWidthChange = (value: number | undefined) => {
  if (!value) return;
  const newWidth = value;
  let newHeight = heightInput.value;

  if (keepRatio.value && originalRatio.value) {
    newHeight = Math.round(newWidth / originalRatio.value);
    heightInput.value = newHeight;
  }

  props.updateAttributes({
    width: newWidth,
    height: newHeight,
  });
};

// 手动输入高度
const handleHeightChange = (value: number | undefined) => {
  if (!value) return;
  const newHeight = value;
  let newWidth = widthInput.value;

  if (keepRatio.value && originalRatio.value) {
    newWidth = Math.round(newHeight * originalRatio.value);
    widthInput.value = newWidth;
  }

  props.updateAttributes({
    width: newWidth,
    height: newHeight,
  });
};

// 重置为原始尺寸
const resetSize = () => {
  if (imgRef.value) {
    const img = imgRef.value;
    props.updateAttributes({
      width: img.naturalWidth,
      height: img.naturalHeight,
    });
    widthInput.value = img.naturalWidth;
    heightInput.value = img.naturalHeight;
  }
  closeContextMenu();
};

// 删除图片
const handleDelete = () => {
  props.deleteNode();
  closeContextMenu();
};

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
  document.removeEventListener('click', closeContextMenu);
  document.removeEventListener('contextmenu', closeContextMenu);
});
</script>

<template>
  <NodeViewWrapper class="resizable-image-wrapper flex" :style="wrapperStyle">
    <div
      class="resizable-image-container relative inline-block"
      :class="{ 'is-selected': selected, 'is-resizing': isResizing }"
    >
      <!-- 图片 -->
      <img
        ref="imgRef"
        :src="node.attrs.src"
        :alt="node.attrs.alt"
        :title="node.attrs.title"
        :style="imageStyle"
        class="block max-w-full rounded"
        draggable="false"
        @load="handleImageLoad"
        @contextmenu="handleContextMenu"
      />

      <!-- 选中时显示调整手柄 -->
      <template v-if="selected">
        <div
          class="resize-handle resize-handle-nw"
          @mousedown="(e) => startResize(e, 'nw')"
        ></div>
        <div
          class="resize-handle resize-handle-ne"
          @mousedown="(e) => startResize(e, 'ne')"
        ></div>
        <div
          class="resize-handle resize-handle-sw"
          @mousedown="(e) => startResize(e, 'sw')"
        ></div>
        <div
          class="resize-handle resize-handle-se"
          @mousedown="(e) => startResize(e, 'se')"
        ></div>
      </template>
    </div>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <div
        v-if="contextMenuVisible"
        class="image-context-menu"
        :style="{
          left: `${contextMenuPosition.x}px`,
          top: `${contextMenuPosition.y}px`,
        }"
        @click.stop
      >
        <!-- 对齐方式 -->
        <div class="menu-group">
          <div class="menu-group-title">对齐方式</div>
          <div class="menu-row">
            <button
              class="menu-icon-btn"
              :class="{ active: node.attrs.alignment === 'left' }"
              title="左对齐"
              @click="setAlignment('left')"
            >
              <AlignLeft class="h-4 w-4" />
            </button>
            <button
              class="menu-icon-btn"
              :class="{ active: node.attrs.alignment === 'center' }"
              title="居中"
              @click="setAlignment('center')"
            >
              <AlignCenter class="h-4 w-4" />
            </button>
            <button
              class="menu-icon-btn"
              :class="{ active: node.attrs.alignment === 'right' }"
              title="右对齐"
              @click="setAlignment('right')"
            >
              <AlignRight class="h-4 w-4" />
            </button>
          </div>
        </div>

        <div class="menu-divider"></div>

        <!-- 快速缩放 -->
        <div class="menu-group">
          <div class="menu-group-title">快速缩放</div>
          <div class="menu-row">
            <button
              v-for="size in presetSizes"
              :key="size.value"
              class="menu-size-btn"
              @click="setPresetSize(size.value)"
            >
              {{ size.label }}
            </button>
          </div>
        </div>

        <div class="menu-divider"></div>

        <!-- 自定义尺寸 -->
        <button class="menu-item" @click="toggleSizePanel">
          <Maximize2 class="menu-item-icon" />
          <span>自定义尺寸</span>
        </button>

        <!-- 尺寸面板 -->
        <div v-if="showSizePanel" class="size-panel">
          <div class="size-row">
            <span class="size-label">宽</span>
            <ElInputNumber
              v-model="widthInput"
              :min="50"
              :max="2000"
              size="small"
              controls-position="right"
              @change="handleWidthChange"
            />
          </div>
          <div class="size-row">
            <span class="size-label">高</span>
            <ElInputNumber
              v-model="heightInput"
              :min="50"
              :max="2000"
              size="small"
              controls-position="right"
              @change="handleHeightChange"
            />
          </div>
          <label class="size-checkbox">
            <input v-model="keepRatio" type="checkbox" />
            <span>保持比例</span>
          </label>
        </div>

        <div class="menu-divider"></div>

        <!-- 重置尺寸 -->
        <button class="menu-item" @click="resetSize">
          <RotateCw class="menu-item-icon" />
          <span>重置尺寸</span>
        </button>

        <!-- 删除 -->
        <button class="menu-item menu-item-danger" @click="handleDelete">
          <Trash2 class="menu-item-icon" />
          <span>删除图片</span>
        </button>
      </div>
    </Teleport>
  </NodeViewWrapper>
</template>

<style scoped>
.resizable-image-wrapper {
  margin: 0.5em 0;
}

.resizable-image-container {
  position: relative;
  display: inline-block;
  line-height: 0;

  &.is-selected {
    img {
      outline: 2px solid var(--el-color-primary);
      outline-offset: 2px;
    }
  }

  &.is-resizing {
    user-select: none;
  }
}

/* 调整手柄样式 - 只保留四个角 */
.resize-handle {
  position: absolute;
  z-index: 10;
  width: 10px;
  height: 10px;
  background-color: var(--el-color-primary);
  border: 2px solid var(--el-bg-color);
  border-radius: 2px;

  &:hover {
    background-color: var(--el-color-primary-dark-2);
  }
}

.resize-handle-nw {
  top: -5px;
  left: -5px;
  cursor: nw-resize;
}

.resize-handle-ne {
  top: -5px;
  right: -5px;
  cursor: ne-resize;
}

.resize-handle-sw {
  bottom: -5px;
  left: -5px;
  cursor: sw-resize;
}

.resize-handle-se {
  right: -5px;
  bottom: -5px;
  cursor: se-resize;
}

/* 右键菜单样式 */
.image-context-menu {
  position: fixed;
  z-index: 9999;
  min-width: 180px;
  padding: 6px 0;
  background-color: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgb(0 0 0 / 15%);
}

.menu-group {
  padding: 6px 12px;
}

.menu-group-title {
  margin-bottom: 6px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.menu-row {
  display: flex;
  gap: 4px;
}

.menu-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 28px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  background-color: transparent;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  transition: all 0.2s;

  &:hover {
    color: var(--el-color-primary);
    border-color: var(--el-color-primary);
  }

  &.active {
    color: #fff;
    background-color: var(--el-color-primary);
    border-color: var(--el-color-primary);
  }
}

.menu-size-btn {
  flex: 1;
  height: 28px;
  font-size: 12px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  background-color: transparent;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  transition: all 0.2s;

  &:hover {
    color: var(--el-color-primary);
    background-color: var(--el-color-primary-light-9);
    border-color: var(--el-color-primary);
  }
}

.menu-divider {
  height: 1px;
  margin: 6px 0;
  background-color: var(--el-border-color-lighter);
}

.menu-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  background-color: transparent;
  border: none;
  transition: background-color 0.2s;

  &:hover {
    background-color: var(--el-fill-color-light);
  }

  &.menu-item-danger {
    color: var(--el-color-danger);

    &:hover {
      background-color: var(--el-color-danger-light-9);
    }
  }
}

.menu-item-icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
}

/* 尺寸面板 */
.size-panel {
  padding: 8px 12px;
  background-color: var(--el-fill-color-lighter);
  border-top: 1px solid var(--el-border-color-lighter);
}

.size-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.size-label {
  width: 20px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.size-checkbox {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  cursor: pointer;

  input {
    width: 14px;
    height: 14px;
    cursor: pointer;
  }
}

:deep(.el-input-number--small) {
  width: 100px;
}
</style>
