<script setup lang="ts">
import type { Editor } from '@tiptap/vue-3';

import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue';

import { GripVertical } from '@vben/icons';

import TableMenu from './TableMenu.vue';

interface Props {
  editor: Editor;
}

const props = defineProps<Props>();

const showRowHandle = ref(false);
const showColumnHandle = ref(false);
const rowHandlePosition = ref({ top: 0, left: 0, height: 0 });
const columnHandlePosition = ref({ top: 0, left: 0, width: 0 });
const currentRowIndex = ref(-1);
const currentColumnIndex = ref(-1);

// 保存当前悬停的单元格，用于点击手柄时聚焦
let currentCell: HTMLElement | null = null;

const showMenu = ref(false);
const menuType = ref<'column' | 'row'>('row');
const menuPosition = ref({ x: 0, y: 0 });

// 用于追踪鼠标是否在手柄区域
const isMouseOverHandle = ref(false);
let hideTimeout: null | ReturnType<typeof setTimeout> = null;

let editorElement: HTMLElement | null = null;

function handleMouseMove(e: MouseEvent) {
  if (!props.editor || !editorElement) return;

  const target = e.target as HTMLElement;
  const cell = target.closest('td, th') as HTMLElement;
  const table = target.closest('table') as HTMLElement;

  if (!cell || !table) {
    // 不立即隐藏，给用户时间移动到手柄
    scheduleHide();
    return;
  }

  // 取消隐藏计时器
  cancelHide();
  const row = cell.closest('tr') as HTMLElement;
  if (!row) return;

  const tableRect = table.getBoundingClientRect();
  const rowRect = row.getBoundingClientRect();
  const cellRect = cell.getBoundingClientRect();

  // 计算行索引
  const rows = [...table.querySelectorAll('tr')] as HTMLElement[];
  currentRowIndex.value = rows.indexOf(row);

  // 计算列索引
  const cells = [...row.querySelectorAll('td, th')];
  currentColumnIndex.value = cells.indexOf(cell);

  // 保存当前单元格引用
  currentCell = cell;

  // 行手柄位置（左侧）- 高度与行高一致
  rowHandlePosition.value = {
    top: rowRect.top,
    left: tableRect.left - 20,
    height: rowRect.height,
  };

  // 列手柄位置（顶部）- 宽度与列宽一致
  columnHandlePosition.value = {
    top: tableRect.top - 20,
    left: cellRect.left,
    width: cellRect.width,
  };

  showRowHandle.value = true;
  showColumnHandle.value = true;
}

function scheduleHide() {
  if (hideTimeout) return;
  hideTimeout = setTimeout(() => {
    if (!isMouseOverHandle.value && !showMenu.value) {
      showRowHandle.value = false;
      showColumnHandle.value = false;
    }
    hideTimeout = null;
  }, 300);
}

function cancelHide() {
  if (hideTimeout) {
    clearTimeout(hideTimeout);
    hideTimeout = null;
  }
}

function handleMouseLeave() {
  scheduleHide();
}

function handleHandleMouseEnter() {
  isMouseOverHandle.value = true;
  cancelHide();
}

function handleHandleMouseLeave() {
  isMouseOverHandle.value = false;
  scheduleHide();
}

function handleRowClick(e: MouseEvent) {
  e.stopPropagation();

  // 选中当前行
  if (currentRowIndex.value >= 0) {
    selectRow(currentRowIndex.value);
  }

  menuType.value = 'row';
  menuPosition.value = { x: e.clientX, y: e.clientY };
  showMenu.value = true;

  // 点击其他地方关闭菜单
  const closeMenu = (event: MouseEvent) => {
    const target = event.target as HTMLElement;
    // 如果点击的是菜单内部，不关闭
    if (target.closest('.table-menu')) return;

    showMenu.value = false;
    showRowHandle.value = false;
    showColumnHandle.value = false;
    document.removeEventListener('click', closeMenu);
  };
  setTimeout(() => {
    document.addEventListener('click', closeMenu);
  }, 0);
}

function handleColumnClick(e: MouseEvent) {
  e.stopPropagation();

  // 选中当前列
  if (currentColumnIndex.value >= 0) {
    selectColumn(currentColumnIndex.value);
  }

  menuType.value = 'column';
  menuPosition.value = { x: e.clientX, y: e.clientY };
  showMenu.value = true;

  // 点击其他地方关闭菜单
  const closeMenu = (event: MouseEvent) => {
    const target = event.target as HTMLElement;
    // 如果点击的是菜单内部，不关闭
    if (target.closest('.table-menu')) return;

    showMenu.value = false;
    showRowHandle.value = false;
    showColumnHandle.value = false;
    document.removeEventListener('click', closeMenu);
  };
  setTimeout(() => {
    document.addEventListener('click', closeMenu);
  }, 0);
}

function focusCurrentCell() {
  if (!currentCell || !props.editor) return;

  // 获取单元格在编辑器中的位置并聚焦
  const view = props.editor.view;
  const pos = view.posAtDOM(currentCell, 0);
  if (pos >= 0) {
    props.editor.chain().focus().setTextSelection(pos).run();
  }
}

function selectRow(_rowIndex: number) {
  focusCurrentCell();
}

function selectColumn(_colIndex: number) {
  focusCurrentCell();
}

function closeMenu() {
  showMenu.value = false;
}

onMounted(() => {
  nextTick(() => {
    editorElement = document.querySelector(
      '.notion-editor-wrapper .ProseMirror',
    );
    if (editorElement) {
      editorElement.addEventListener('mousemove', handleMouseMove);
      editorElement.addEventListener('mouseleave', handleMouseLeave);
    }
  });
});

onBeforeUnmount(() => {
  if (editorElement) {
    editorElement.removeEventListener('mousemove', handleMouseMove);
    editorElement.removeEventListener('mouseleave', handleMouseLeave);
  }
  cancelHide();
});
</script>

<template>
  <!-- 行手柄 -->
  <Teleport to="body">
    <div
      v-if="showRowHandle"
      class="table-handle row-handle"
      :style="{
        top: `${rowHandlePosition.top}px`,
        left: `${rowHandlePosition.left}px`,
        height: `${rowHandlePosition.height}px`,
      }"
      @click="handleRowClick"
      @mouseenter="handleHandleMouseEnter"
      @mouseleave="handleHandleMouseLeave"
    >
      <GripVertical class="handle-icon" />
    </div>
  </Teleport>

  <!-- 列手柄 -->
  <Teleport to="body">
    <div
      v-if="showColumnHandle"
      class="table-handle column-handle"
      :style="{
        top: `${columnHandlePosition.top}px`,
        left: `${columnHandlePosition.left}px`,
        width: `${columnHandlePosition.width}px`,
      }"
      @click="handleColumnClick"
      @mouseenter="handleHandleMouseEnter"
      @mouseleave="handleHandleMouseLeave"
    >
      <GripVertical class="handle-icon rotated" />
    </div>
  </Teleport>

  <!-- 菜单 -->
  <Teleport to="body">
    <TableMenu
      v-if="showMenu"
      :editor="editor"
      :type="menuType"
      :position="menuPosition"
      @close="closeMenu"
    />
  </Teleport>
</template>

<style scoped>
.table-handle {
  position: fixed;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.table-handle:hover {
  background: var(--el-fill-color);
}

.row-handle {
  width: 16px;
}

.column-handle {
  height: 16px;
}

.handle-icon {
  width: 12px;
  height: 12px;
  color: var(--el-text-color-secondary);
}

.handle-icon.rotated {
  transform: rotate(90deg);
}
</style>
