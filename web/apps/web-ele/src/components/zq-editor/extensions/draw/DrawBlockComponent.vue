<script setup lang="ts">
import type { DrawData } from '#/components/zq-draw';

import { computed, onBeforeUnmount, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { NodeViewWrapper } from '@tiptap/vue-3';
import { ElButton } from 'element-plus';

import { ZqDraw } from '#/components/zq-draw';
import DrawPreview from '#/components/zq-draw/DrawPreview.vue';

const props = defineProps<{
  deleteNode: () => void;
  editor: any;
  node: any;
  selected: boolean;
  updateAttributes: (attrs: Record<string, any>) => void;
}>();

const showEditor = ref(false);
const drawRef = ref<InstanceType<typeof ZqDraw>>();
const containerRef = ref<HTMLDivElement>();

const isResizing = ref(false);
const resizeDirection = ref('');
const startX = ref(0);
const startY = ref(0);
const startWidth = ref(0);
const startHeight = ref(0);

const MIN_WIDTH = 200;
const MIN_HEIGHT = 120;

const blockWidth = computed(() => props.node.attrs.width || 800);
const blockHeight = computed(() => props.node.attrs.height || 450);
const hasData = computed(() => !!props.node.attrs.data);

const drawData = computed<DrawData | undefined>(() => {
  const raw = props.node.attrs.data;
  if (!raw) return undefined;
  try {
    return typeof raw === 'string' ? JSON.parse(raw) : raw;
  } catch {
    return undefined;
  }
});

const containerStyle = computed(() => ({
  width: `${blockWidth.value}px`,
  height: `${blockHeight.value}px`,
}));

function openEditor() {
  if (!props.editor.isEditable) return;
  showEditor.value = true;
}

function closeEditor() {
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = null;
  }
  const data = drawRef.value?.getDrawData();
  if (data) {
    props.updateAttributes({ data: JSON.stringify(data) });
  }
  showEditor.value = false;
}

async function handleSave(data: DrawData) {
  props.updateAttributes({
    data: JSON.stringify(data),
  });
  closeEditor();
}

async function handleSaveAndClose() {
  const data = drawRef.value?.getDrawData();
  if (data) {
    await handleSave(data);
  } else {
    closeEditor();
  }
}

let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;
const AUTO_SAVE_DELAY = 1500;

function handleDrawChange() {
  if (!showEditor.value) return;
  if (autoSaveTimer) clearTimeout(autoSaveTimer);
  autoSaveTimer = setTimeout(() => {
    const data = drawRef.value?.getDrawData();
    if (data) {
      props.updateAttributes({ data: JSON.stringify(data) });
    }
  }, AUTO_SAVE_DELAY);
}

watch(showEditor, (val) => {
  if (!val && autoSaveTimer) {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = null;
  }
});

function handleDelete() {
  props.deleteNode();
}

function startResize(e: MouseEvent, direction: string) {
  e.preventDefault();
  e.stopPropagation();
  isResizing.value = true;
  resizeDirection.value = direction;
  startX.value = e.clientX;
  startY.value = e.clientY;
  startWidth.value = blockWidth.value;
  startHeight.value = blockHeight.value;
  document.addEventListener('mousemove', handleResize);
  document.addEventListener('mouseup', stopResize);
}

function handleResize(e: MouseEvent) {
  if (!isResizing.value) return;
  const deltaX = e.clientX - startX.value;
  const deltaY = e.clientY - startY.value;
  const dir = resizeDirection.value;

  let newWidth = startWidth.value;
  let newHeight = startHeight.value;

  if (dir.includes('e')) newWidth = startWidth.value + deltaX;
  if (dir.includes('w')) newWidth = startWidth.value - deltaX;
  if (dir.includes('s')) newHeight = startHeight.value + deltaY;
  if (dir.includes('n')) newHeight = startHeight.value - deltaY;

  newWidth = Math.max(MIN_WIDTH, Math.round(newWidth));
  newHeight = Math.max(MIN_HEIGHT, Math.round(newHeight));

  props.updateAttributes({ width: newWidth, height: newHeight });
}

function stopResize() {
  isResizing.value = false;
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
}

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = null;
  }
});
</script>

<template>
  <NodeViewWrapper
    class="draw-block"
    :class="{ 'draw-block--selected': selected }"
    data-type="draw"
  >
    <div
      ref="containerRef"
      class="draw-block__container"
      :class="{ 'is-resizing': isResizing }"
      :style="containerStyle"
    >
      <div
        v-if="hasData && drawData"
        class="draw-block__preview"
        @dblclick="openEditor"
      >
        <DrawPreview
          :data="drawData"
          :width="blockWidth"
          :height="blockHeight"
        />
        <div v-if="editor.isEditable" class="draw-block__hover-hint">
          <span class="draw-block__hover-hint-text">
            {{ $t('zq-editor.draw.dblclickToEdit') }}
          </span>
        </div>
      </div>
      <div v-else class="draw-block__empty" @click="openEditor">
        <div class="draw-block__empty-icon">
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M12 19l7-7 3 3-7 7-3-3z" />
            <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z" />
            <path d="M2 2l7.586 7.586" />
            <circle cx="11" cy="11" r="2" />
          </svg>
        </div>
        <span class="draw-block__empty-text">
          {{ $t('zq-editor.draw.clickToCreate') }}
        </span>
      </div>

      <div v-if="!editor.isEditable" class="draw-block__readonly"></div>

      <!-- Resize handles -->
      <template v-if="selected && editor.isEditable">
        <div
          class="draw-block__resize-handle draw-block__resize-e"
          @mousedown="(e) => startResize(e, 'e')"
        ></div>
        <div
          class="draw-block__resize-handle draw-block__resize-s"
          @mousedown="(e) => startResize(e, 's')"
        ></div>
        <div
          class="draw-block__resize-handle draw-block__resize-se"
          @mousedown="(e) => startResize(e, 'se')"
        ></div>
      </template>
    </div>

    <Teleport to="body">
      <div v-if="showEditor" class="draw-block__dialog-overlay">
        <div class="draw-block__dialog">
          <div class="draw-block__dialog-header">
            <span class="draw-block__dialog-title">
              {{ $t('zq-editor.draw.title') }}
            </span>
            <div class="draw-block__dialog-actions">
              <ElButton size="small" @click="handleDelete">
                {{ $t('zq-editor.draw.delete') }}
              </ElButton>
              <ElButton size="small" type="primary" @click="handleSaveAndClose">
                {{ $t('zq-editor.draw.saveAndClose') }}
              </ElButton>
              <ElButton size="small" @click="closeEditor">
                {{ $t('zq-editor.draw.close') }}
              </ElButton>
            </div>
          </div>
          <div class="draw-block__dialog-body">
            <ZqDraw
              ref="drawRef"
              :model-value="drawData"
              width="100%"
              height="100%"
              @save="handleSave"
              @change="handleDrawChange"
            />
          </div>
        </div>
      </div>
    </Teleport>
  </NodeViewWrapper>
</template>

<style scoped>
.draw-block {
  margin: 12px 0;
}

.draw-block--selected .draw-block__container {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 2px;
}

.draw-block__container {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  transition: outline 0.15s;
  max-width: 100%;
}

.draw-block__container.is-resizing {
  user-select: none;
}

.draw-block__preview {
  position: relative;
  width: 100%;
  height: 100%;
  cursor: default;
}

.draw-block__hover-hint {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  pointer-events: none;
  transition: background 0.2s;
}

.draw-block__hover-hint-text {
  padding: 6px 14px;
  font-size: 12px;
  color: var(--el-color-white);
  background: var(--el-color-primary);
  border-radius: 6px;
  opacity: 0;
  transition: opacity 0.2s;
}

.draw-block__preview:hover .draw-block__hover-hint {
  background: rgba(0, 0, 0, 0.04);
}

.draw-block__preview:hover .draw-block__hover-hint-text {
  opacity: 0.85;
}

.draw-block__empty {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  cursor: pointer;
  background: var(--el-fill-color-lighter);
  transition: background 0.15s;
}

.draw-block__empty:hover {
  background: var(--el-fill-color-light);
}

.draw-block__empty-icon {
  color: var(--el-text-color-placeholder);
}

.draw-block__empty-text {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.draw-block__readonly {
  position: absolute;
  inset: 0;
  cursor: default;
}

/* Resize handles */
.draw-block__resize-handle {
  position: absolute;
  z-index: 10;
}

.draw-block__resize-e {
  top: 0;
  right: -3px;
  bottom: 0;
  width: 6px;
  cursor: e-resize;
}

.draw-block__resize-e::after {
  content: '';
  position: absolute;
  top: 50%;
  right: 0;
  width: 4px;
  height: 32px;
  transform: translateY(-50%);
  background: var(--el-color-primary);
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.15s;
}

.draw-block--selected .draw-block__resize-e::after {
  opacity: 1;
}

.draw-block__resize-s {
  bottom: -3px;
  left: 0;
  right: 0;
  height: 6px;
  cursor: s-resize;
}

.draw-block__resize-s::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 32px;
  height: 4px;
  transform: translateX(-50%);
  background: var(--el-color-primary);
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.15s;
}

.draw-block--selected .draw-block__resize-s::after {
  opacity: 1;
}

.draw-block__resize-se {
  right: -4px;
  bottom: -4px;
  width: 12px;
  height: 12px;
  cursor: se-resize;
}

.draw-block__resize-se::after {
  content: '';
  position: absolute;
  right: 2px;
  bottom: 2px;
  width: 8px;
  height: 8px;
  background: var(--el-color-primary);
  border: 2px solid var(--el-bg-color);
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.15s;
}

.draw-block--selected .draw-block__resize-se::after {
  opacity: 1;
}

/* Dialog */
.draw-block__dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
}

.draw-block__dialog {
  display: flex;
  flex-direction: column;
  width: calc(100vw - 0px);
  height: calc(100vh - 0px);
  overflow: hidden;
  background: var(--el-bg-color);
  //border-radius: 12px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}

.draw-block__dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  //border-bottom: 1px solid var(--el-border-color-lighter);
}

.draw-block__dialog-title {
  font-size: 15px;
  font-weight: 600;
}

.draw-block__dialog-actions {
  display: flex;
  gap: 8px;
}

.draw-block__dialog-body {
  flex: 1;
  overflow: hidden;
}
</style>
