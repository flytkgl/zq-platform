<script setup lang="ts">
import type { Editor } from '@tiptap/vue-3';

import { computed, ref } from 'vue';

import {
  ArrowLeft,
  ArrowRight,
  ChevronRight,
  Copy,
  MoveDown,
  MoveUp,
  Paintbrush,
  Plus,
  Trash2,
  X,
} from '@vben/icons';

interface Props {
  editor: Editor;
  type: 'column' | 'row';
  position: { x: number; y: number };
}

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
}>();

const showColorSubmenu = ref(false);

const isRow = computed(() => props.type === 'row');

const cellColors = [
  { name: '默认', value: '' },
  { name: '浅灰', value: '#f1f5f9' },
  { name: '浅红', value: '#fee2e2' },
  { name: '浅橙', value: '#ffedd5' },
  { name: '浅黄', value: '#fef9c3' },
  { name: '浅绿', value: '#dcfce7' },
  { name: '浅蓝', value: '#dbeafe' },
  { name: '浅紫', value: '#f3e8ff' },
  { name: '浅粉', value: '#fce7f3' },
];

function moveUp() {
  // Tiptap 没有直接的移动行/列命令
  // 暂不实现
  emit('close');
}

function moveDown() {
  emit('close');
}

function insertBefore() {
  if (isRow.value) {
    (props.editor.chain().focus() as any).addRowBefore().run();
  } else {
    (props.editor.chain().focus() as any).addColumnBefore().run();
  }
  emit('close');
}

function insertAfter() {
  if (isRow.value) {
    (props.editor.chain().focus() as any).addRowAfter().run();
  } else {
    (props.editor.chain().focus() as any).addColumnAfter().run();
  }
  emit('close');
}

function deleteRowOrColumn() {
  if (isRow.value) {
    (props.editor.chain().focus() as any).deleteRow().run();
  } else {
    (props.editor.chain().focus() as any).deleteColumn().run();
  }
  emit('close');
}

function duplicateRowOrColumn() {
  // 复制行/列：先插入，然后复制内容（简化实现）
  if (isRow.value) {
    (props.editor.chain().focus() as any).addRowAfter().run();
  } else {
    (props.editor.chain().focus() as any).addColumnAfter().run();
  }
  emit('close');
}

function clearContents() {
  // 清空内容：选中单元格后删除内容
  // 简化实现
  emit('close');
}

function setCellBackground(color: string) {
  if (color) {
    (props.editor.chain().focus() as any)
      .setCellAttribute('backgroundColor', color)
      .run();
  } else {
    (props.editor.chain().focus() as any)
      .setCellAttribute('backgroundColor', null)
      .run();
  }
  showColorSubmenu.value = false;
  emit('close');
}
</script>

<template>
  <div
    class="table-menu"
    :style="{ left: `${position.x}px`, top: `${position.y}px` }"
    @click.stop
  >
    <div class="menu-content">
      <!-- 移动操作 -->
      <button class="menu-item" @click="moveUp" :disabled="true">
        <component :is="isRow ? MoveUp : ArrowLeft" class="menu-icon" />
        <span>{{ isRow ? '上移行' : '左移列' }}</span>
      </button>
      <button class="menu-item" @click="moveDown" :disabled="true">
        <component :is="isRow ? MoveDown : ArrowRight" class="menu-icon" />
        <span>{{ isRow ? '下移行' : '右移列' }}</span>
      </button>

      <div class="menu-divider"></div>

      <!-- 插入操作 -->
      <button class="menu-item" @click="insertBefore">
        <Plus class="menu-icon" />
        <span>{{ isRow ? '在上方插入行' : '在左侧插入列' }}</span>
      </button>
      <button class="menu-item" @click="insertAfter">
        <Plus class="menu-icon" />
        <span>{{ isRow ? '在下方插入行' : '在右侧插入列' }}</span>
      </button>

      <div class="menu-divider"></div>

      <!-- 颜色 -->
      <div
        class="menu-item-with-submenu"
        @mouseenter="showColorSubmenu = true"
        @mouseleave="showColorSubmenu = false"
      >
        <button class="menu-item">
          <Paintbrush class="menu-icon" />
          <span>颜色</span>
          <ChevronRight class="submenu-arrow" />
        </button>
        <div v-if="showColorSubmenu" class="submenu color-submenu">
          <button
            v-for="color in cellColors"
            :key="color.value"
            class="color-item"
            @click="setCellBackground(color.value)"
          >
            <span
              class="color-preview"
              :style="{
                backgroundColor: color.value || '#ffffff',
                border: color.value
                  ? 'none'
                  : '1px solid var(--el-border-color)',
              }"
            ></span>
            <span>{{ color.name }}</span>
          </button>
        </div>
      </div>

      <!-- 清空内容（仅列） -->
      <button
        v-if="!isRow"
        class="menu-item"
        @click="clearContents"
        :disabled="true"
      >
        <X class="menu-icon" />
        <span>清空列内容</span>
      </button>

      <div class="menu-divider"></div>

      <!-- 复制 -->
      <button class="menu-item" @click="duplicateRowOrColumn">
        <Copy class="menu-icon" />
        <span>{{ isRow ? '复制行' : '复制列' }}</span>
      </button>

      <!-- 删除 -->
      <button class="menu-item menu-item-danger" @click="deleteRowOrColumn">
        <Trash2 class="menu-icon" />
        <span>{{ isRow ? '删除行' : '删除列' }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.table-menu {
  position: fixed;
  z-index: 9999;
  min-width: 180px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  padding: 4px;
}

.menu-content {
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: var(--el-text-color-primary);
  border-radius: 4px;
  transition: background-color 0.15s;
  text-align: left;
}

.menu-item:hover:not(:disabled) {
  background-color: var(--el-fill-color-light);
}

.menu-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.menu-item-danger {
  color: var(--el-color-danger);
}

.menu-item-danger:hover:not(:disabled) {
  background-color: var(--el-color-danger-light-9);
}

.menu-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.menu-divider {
  height: 1px;
  background-color: var(--el-border-color-lighter);
  margin: 4px 8px;
}

.menu-item-with-submenu {
  position: relative;
}

.submenu-arrow {
  width: 14px;
  height: 14px;
  margin-left: auto;
  opacity: 0.5;
}

.submenu {
  position: absolute;
  left: calc(100% - 4px);
  top: -4px;
  min-width: 140px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  padding: 4px;
  padding-left: 8px;
}

.color-submenu {
  min-width: 120px;
}

.color-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: var(--el-text-color-primary);
  border-radius: 4px;
  transition: background-color 0.15s;
}

.color-item:hover {
  background-color: var(--el-fill-color-light);
}

.color-preview {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  flex-shrink: 0;
}
</style>
