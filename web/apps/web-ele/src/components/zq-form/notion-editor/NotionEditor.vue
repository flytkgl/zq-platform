<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';

import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Bold,
  ChevronDown,
  Code,
  Highlighter,
  Italic,
  Link as LinkIcon,
  Strikethrough,
  Type,
  Underline as UnderlineIcon,
} from '@vben/icons';

import CharacterCount from '@tiptap/extension-character-count';
import Color from '@tiptap/extension-color';
import Highlight from '@tiptap/extension-highlight';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import { Table } from '@tiptap/extension-table';
import { TableCell } from '@tiptap/extension-table-cell';
import { TableHeader } from '@tiptap/extension-table-header';
import { TableRow } from '@tiptap/extension-table-row';
import TextAlign from '@tiptap/extension-text-align';
import { TextStyle } from '@tiptap/extension-text-style';
import Underline from '@tiptap/extension-underline';
import StarterKit from '@tiptap/starter-kit';
import { EditorContent, useEditor } from '@tiptap/vue-3';
import { BubbleMenu } from '@tiptap/vue-3/menus';
import GlobalDragHandle from 'tiptap-extension-global-drag-handle';
import { Markdown } from 'tiptap-markdown';

import TableHandles from './components/TableHandles.vue';
import TableMenu from './components/TableMenu.vue';
import {
  createSlashCommandSuggestion,
  SlashCommand,
} from './extensions/slash-command';

interface Props {
  modelValue?: string;
  placeholder?: string;
  disabled?: boolean;
  readonly?: boolean;
  minHeight?: number | string;
  maxHeight?: number | string;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: '输入 / 打开命令菜单...',
  disabled: false,
  readonly: false,
  minHeight: 300,
  maxHeight: 600,
});

const emit = defineEmits<{
  change: [value: string];
  'update:modelValue': [value: string];
}>();

// 链接弹窗状态
const showLinkPopover = ref(false);
const linkUrl = ref('');

// Turn Into 菜单状态
const showTurnIntoMenu = ref(false);

// 颜色选择器状态
const showColorPicker = ref(false);

// 表格右键菜单状态
const showTableMenu = ref(false);
const tableMenuType = ref<'column' | 'row'>('row');
const tableMenuPosition = ref({ x: 0, y: 0 });

// 文本颜色列表
const textColors = [
  { color: 'inherit', label: '默认' },
  { color: '#6b7280', label: '灰色' },
  { color: '#92400e', label: '棕色' },
  { color: '#c2410c', label: '橙色' },
  { color: '#ca8a04', label: '黄色' },
  { color: '#16a34a', label: '绿色' },
  { color: '#0284c7', label: '蓝色' },
  { color: '#7c3aed', label: '紫色' },
  { color: '#db2777', label: '粉色' },
  { color: '#dc2626', label: '红色' },
];

// 高亮颜色列表
const highlightColors = [
  { color: '', label: '无' },
  { color: '#f3f4f6', label: '灰色' },
  { color: '#fef3c7', label: '黄色' },
  { color: '#d1fae5', label: '绿色' },
  { color: '#dbeafe', label: '蓝色' },
  { color: '#ede9fe', label: '紫色' },
  { color: '#fce7f3', label: '粉色' },
  { color: '#fee2e2', label: '红色' },
  { color: '#ffedd5', label: '橙色' },
  { color: '#e0f2fe', label: '青色' },
];

// Turn Into 选项
const turnIntoItems = [
  { icon: 'Type', label: 'Text', key: 'paragraph' },
  { icon: 'Heading1', label: 'Heading 1', key: 'h1' },
  { icon: 'Heading2', label: 'Heading 2', key: 'h2' },
  { icon: 'Heading3', label: 'Heading 3', key: 'h3' },
  { icon: 'List', label: 'Bulleted list', key: 'bulletList' },
  { icon: 'ListOrdered', label: 'Numbered list', key: 'orderedList' },
  { icon: 'Quote', label: 'Blockquote', key: 'blockquote' },
  { icon: 'Code', label: 'Code block', key: 'codeBlock' },
];

// 编辑器实例
const editor = useEditor({
  content: props.modelValue,
  editable: !props.disabled && !props.readonly,
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3],
      },
    }),
    Underline,
    TextAlign.configure({
      types: ['heading', 'paragraph'],
    }),
    Highlight.configure({
      multicolor: true,
    }),
    Link.configure({
      openOnClick: false,
      HTMLAttributes: {
        class: 'text-[var(--el-color-primary)] underline cursor-pointer',
      },
    }),
    Placeholder.configure({
      placeholder: props.placeholder,
    }),
    Markdown.configure({
      html: true,
      tightLists: true,
      bulletListMarker: '-',
      linkify: true,
      breaks: true,
      transformPastedText: true,
      transformCopiedText: true,
    }),
    CharacterCount,
    TextStyle,
    Color,
    GlobalDragHandle.configure({
      dragHandleWidth: 20,
      scrollTreshold: 100,
    }),
    Table.configure({
      resizable: true,
    }),
    TableRow,
    TableHeader,
    TableCell.extend({
      addAttributes() {
        return {
          ...this.parent?.(),
          backgroundColor: {
            default: null,
            parseHTML: (element) => element.style.backgroundColor || null,
            renderHTML: (attributes) => {
              if (!attributes.backgroundColor) {
                return {};
              }
              return {
                style: `background-color: ${attributes.backgroundColor}`,
              };
            },
          },
        };
      },
    }),
    SlashCommand.configure({
      suggestion: createSlashCommandSuggestion(),
    }),
  ],
  onUpdate: ({ editor: editorInstance }) => {
    const markdown =
      (editorInstance.storage as any)?.markdown?.getMarkdown() || '';
    emit('update:modelValue', markdown);
    emit('change', markdown);
  },
  editorProps: {
    attributes: {
      class: 'notion-editor-content',
    },
  },
});

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  (value) => {
    if (
      editor.value &&
      (editor.value.storage as any)?.markdown?.getMarkdown() !== value
    ) {
      editor.value.commands.setContent(value || '', { emitUpdate: false });
    }
  },
);

// 监听 disabled/readonly 变化
watch(
  () => [props.disabled, props.readonly],
  ([disabled, readonly]) => {
    editor.value?.setEditable(!disabled && !readonly);
  },
);

// 销毁编辑器
onBeforeUnmount(() => {
  editor.value?.destroy();
});

// 样式计算
const editorStyle = computed(() => ({
  minHeight:
    typeof props.minHeight === 'number'
      ? `${props.minHeight}px`
      : props.minHeight,
  maxHeight:
    typeof props.maxHeight === 'number'
      ? `${props.maxHeight}px`
      : props.maxHeight,
}));

// 设置链接
function setLink() {
  if (linkUrl.value) {
    editor.value?.chain().focus().setLink({ href: linkUrl.value }).run();
  } else {
    editor.value?.chain().focus().unsetLink().run();
  }
  showLinkPopover.value = false;
  linkUrl.value = '';
}

// 打开链接弹窗
function openLinkPopover() {
  const previousUrl = editor.value?.getAttributes('link').href;
  linkUrl.value = previousUrl || '';
  showLinkPopover.value = true;
}

// 设置高亮
function toggleHighlight() {
  editor.value?.chain().focus().toggleHighlight({ color: '#fef08a' }).run();
}

// 设置对齐
function setTextAlign(align: 'center' | 'left' | 'right') {
  editor.value?.chain().focus().setTextAlign(align).run();
}

// 获取当前文本类型
function getCurrentType() {
  if (editor.value?.isActive('heading', { level: 1 })) return 'Heading 1';
  if (editor.value?.isActive('heading', { level: 2 })) return 'Heading 2';
  if (editor.value?.isActive('heading', { level: 3 })) return 'Heading 3';
  if (editor.value?.isActive('bulletList')) return 'Bulleted list';
  if (editor.value?.isActive('orderedList')) return 'Numbered list';
  if (editor.value?.isActive('blockquote')) return 'Blockquote';
  if (editor.value?.isActive('codeBlock')) return 'Code block';
  return 'Text';
}

// Turn Into 操作
function turnInto(key: string) {
  if (!editor.value) return;

  switch (key) {
    case 'blockquote': {
      editor.value.chain().focus().toggleBlockquote().run();
      break;
    }
    case 'bulletList': {
      editor.value.chain().focus().toggleBulletList().run();
      break;
    }
    case 'codeBlock': {
      editor.value.chain().focus().toggleCodeBlock().run();
      break;
    }
    case 'h1': {
      editor.value.chain().focus().toggleHeading({ level: 1 }).run();
      break;
    }
    case 'h2': {
      editor.value.chain().focus().toggleHeading({ level: 2 }).run();
      break;
    }
    case 'h3': {
      editor.value.chain().focus().toggleHeading({ level: 3 }).run();
      break;
    }
    case 'orderedList': {
      editor.value.chain().focus().toggleOrderedList().run();
      break;
    }
    case 'paragraph': {
      editor.value.chain().focus().setParagraph().run();
      break;
    }
  }
  showTurnIntoMenu.value = false;
}

// 设置文字颜色
function setTextColor(color: string) {
  if (!editor.value) return;
  if (color === 'inherit') {
    editor.value.chain().focus().unsetColor().run();
  } else {
    editor.value.chain().focus().setColor(color).run();
  }
}

// 设置高亮颜色
function setHighlightColor(color: string) {
  if (!editor.value) return;
  if (color) {
    editor.value.chain().focus().setHighlight({ color }).run();
  } else {
    editor.value.chain().focus().unsetHighlight().run();
  }
}

// 获取当前文字颜色
function getCurrentTextColor() {
  return editor.value?.getAttributes('textStyle').color || 'inherit';
}

// 表格右键菜单处理
function handleContextMenu(e: MouseEvent) {
  const target = e.target as HTMLElement;
  const cell = target.closest('td, th');

  if (cell && editor.value?.isActive('table')) {
    e.preventDefault();

    // 判断是行操作还是列操作（简化处理，默认为行操作）
    tableMenuType.value = 'row';
    tableMenuPosition.value = { x: e.clientX, y: e.clientY };
    showTableMenu.value = true;

    // 点击其他地方关闭菜单
    const closeMenu = () => {
      showTableMenu.value = false;
      document.removeEventListener('click', closeMenu);
    };
    setTimeout(() => {
      document.addEventListener('click', closeMenu);
    }, 0);
  }
}

// 暴露方法
defineExpose({
  getEditor: () => editor.value,
  getMarkdown: () =>
    (editor.value?.storage as any)?.markdown?.getMarkdown() || '',
  getHTML: () => editor.value?.getHTML() || '',
  getText: () => editor.value?.getText() || '',
  setContent: (content: string) => editor.value?.commands.setContent(content),
  clear: () => editor.value?.commands.clearContent(),
  focus: () => editor.value?.commands.focus(),
});
</script>

<template>
  <div class="notion-editor">
    <!-- 气泡菜单 - 选中文本时显示 -->
    <BubbleMenu
      v-if="editor"
      :editor="editor"
      :tippy-options="{ duration: 100 }"
      class="bubble-menu"
    >
      <div
        class="flex items-center gap-1 rounded-lg border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-1 shadow-lg"
      >
        <!-- Turn Into 下拉菜单 -->
        <div class="turn-into-wrapper">
          <button
            class="turn-into-trigger"
            @click="showTurnIntoMenu = !showTurnIntoMenu"
          >
            <span class="trigger-text">{{ getCurrentType() }}</span>
            <ChevronDown class="h-3 w-3" />
          </button>
          <div v-if="showTurnIntoMenu" class="turn-into-dropdown">
            <div class="dropdown-header">Turn Into</div>
            <button
              v-for="item in turnIntoItems"
              :key="item.key"
              class="dropdown-item"
              :class="{ 'is-active': getCurrentType() === item.label }"
              @click="turnInto(item.key)"
            >
              <Type v-if="item.icon === 'Type'" class="h-4 w-4" />
              <span>{{ item.label }}</span>
            </button>
          </div>
        </div>

        <div class="mx-1 h-4 w-px bg-[var(--el-border-color)]"></div>

        <!-- 格式化按钮 -->
        <button
          class="menu-button"
          :class="{ 'is-active': editor.isActive('bold') }"
          title="加粗 (Ctrl+B)"
          @click="editor.chain().focus().toggleBold().run()"
        >
          <Bold class="h-4 w-4" />
        </button>
        <button
          class="menu-button"
          :class="{ 'is-active': editor.isActive('italic') }"
          title="斜体 (Ctrl+I)"
          @click="editor.chain().focus().toggleItalic().run()"
        >
          <Italic class="h-4 w-4" />
        </button>
        <button
          class="menu-button"
          :class="{ 'is-active': editor.isActive('underline') }"
          title="下划线 (Ctrl+U)"
          @click="editor.chain().focus().toggleUnderline().run()"
        >
          <UnderlineIcon class="h-4 w-4" />
        </button>
        <button
          class="menu-button"
          :class="{ 'is-active': editor.isActive('strike') }"
          title="删除线"
          @click="editor.chain().focus().toggleStrike().run()"
        >
          <Strikethrough class="h-4 w-4" />
        </button>
        <button
          class="menu-button"
          :class="{ 'is-active': editor.isActive('code') }"
          title="代码"
          @click="editor.chain().focus().toggleCode().run()"
        >
          <Code class="h-4 w-4" />
        </button>

        <div class="mx-1 h-4 w-px bg-[var(--el-border-color)]"></div>

        <!-- 高亮 -->
        <button
          class="menu-button"
          :class="{ 'is-active': editor.isActive('highlight') }"
          title="高亮"
          @click="toggleHighlight"
        >
          <Highlighter class="h-4 w-4" />
        </button>

        <!-- 链接 -->
        <button
          class="menu-button"
          :class="{ 'is-active': editor.isActive('link') }"
          title="链接 (Ctrl+K)"
          @click="openLinkPopover"
        >
          <LinkIcon class="h-4 w-4" />
        </button>

        <!-- 颜色选择器 -->
        <div class="color-picker-wrapper">
          <button
            class="color-trigger"
            @click="showColorPicker = !showColorPicker"
          >
            <Type class="h-4 w-4" :style="{ color: getCurrentTextColor() }" />
            <ChevronDown class="h-3 w-3" />
          </button>
          <div v-if="showColorPicker" class="color-dropdown">
            <div class="color-section">
              <div class="section-title">Text Color</div>
              <div class="color-grid">
                <button
                  v-for="item in textColors"
                  :key="item.color"
                  class="color-item"
                  :class="{ 'is-active': getCurrentTextColor() === item.color }"
                  :title="item.label"
                  @click="
                    setTextColor(item.color);
                    showColorPicker = false;
                  "
                >
                  <span
                    class="color-letter"
                    :style="{
                      color:
                        item.color === 'inherit'
                          ? 'var(--el-text-color-primary)'
                          : item.color,
                    }"
                    >A</span
                  >
                </button>
              </div>
            </div>
            <div class="color-section">
              <div class="section-title">Highlight Color</div>
              <div class="color-grid">
                <button
                  v-for="item in highlightColors"
                  :key="item.color || 'none'"
                  class="color-item highlight-item"
                  :class="{
                    'is-active': editor.isActive('highlight', {
                      color: item.color,
                    }),
                  }"
                  :title="item.label"
                  @click="
                    setHighlightColor(item.color);
                    showColorPicker = false;
                  "
                >
                  <span
                    class="highlight-circle"
                    :style="{
                      backgroundColor: item.color || 'transparent',
                      border: !item.color
                        ? '1px dashed var(--el-border-color)'
                        : 'none',
                    }"
                  ></span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="mx-1 h-4 w-px bg-[var(--el-border-color)]"></div>

        <!-- 对齐 -->
        <button
          class="menu-button"
          :class="{ 'is-active': editor.isActive({ textAlign: 'left' }) }"
          title="左对齐"
          @click="setTextAlign('left')"
        >
          <AlignLeft class="h-4 w-4" />
        </button>
        <button
          class="menu-button"
          :class="{ 'is-active': editor.isActive({ textAlign: 'center' }) }"
          title="居中"
          @click="setTextAlign('center')"
        >
          <AlignCenter class="h-4 w-4" />
        </button>
        <button
          class="menu-button"
          :class="{ 'is-active': editor.isActive({ textAlign: 'right' }) }"
          title="右对齐"
          @click="setTextAlign('right')"
        >
          <AlignRight class="h-4 w-4" />
        </button>
      </div>
    </BubbleMenu>

    <!-- 链接输入弹窗 -->
    <Teleport to="body">
      <div
        v-if="showLinkPopover"
        class="link-popover"
        @keydown.enter="setLink"
        @keydown.escape="showLinkPopover = false"
      >
        <input
          v-model="linkUrl"
          type="text"
          class="link-input"
          placeholder="输入链接地址..."
          autofocus
        />
        <button class="link-button" @click="setLink">确定</button>
        <button class="link-button cancel" @click="showLinkPopover = false">
          取消
        </button>
      </div>
    </Teleport>

    <!-- 编辑器内容 -->
    <div class="editor-container" @contextmenu="handleContextMenu">
      <EditorContent
        :editor="editor"
        :style="editorStyle"
        class="notion-editor-wrapper"
      />
    </div>

    <!-- 表格右键菜单 -->
    <Teleport to="body">
      <TableMenu
        v-if="showTableMenu && editor"
        :editor="editor"
        :type="tableMenuType"
        :position="tableMenuPosition"
        @close="showTableMenu = false"
      />
    </Teleport>

    <!-- 表格行/列手柄 -->
    <TableHandles v-if="editor" :editor="editor" />
  </div>
</template>

<style scoped>
.notion-editor {
  position: relative;
  width: 100%;
}

.notion-editor-wrapper {
  width: 100%;
  overflow-y: auto;
  padding: 1rem;
}

.notion-editor-wrapper :deep(.ProseMirror) {
  outline: none;
  min-height: inherit;
  max-height: inherit;
}

.notion-editor-wrapper
  :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: var(--el-text-color-placeholder);
  pointer-events: none;
  height: 0;
}

.notion-editor-wrapper :deep(.ProseMirror h1) {
  font-size: 2rem;
  font-weight: 700;
  margin: 1.5rem 0 0.5rem;
  line-height: 1.2;
}

.notion-editor-wrapper :deep(.ProseMirror h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 1.25rem 0 0.5rem;
  line-height: 1.3;
}

.notion-editor-wrapper :deep(.ProseMirror h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 1rem 0 0.5rem;
  line-height: 1.4;
}

.notion-editor-wrapper :deep(.ProseMirror p) {
  margin: 0.5rem 0;
  line-height: 1.6;
}

.notion-editor-wrapper :deep(.ProseMirror ul),
.notion-editor-wrapper :deep(.ProseMirror ol) {
  padding-left: 1.5rem;
  margin: 0.5rem 0;
}

.notion-editor-wrapper :deep(.ProseMirror li) {
  margin: 0.25rem 0;
}

.notion-editor-wrapper :deep(.ProseMirror blockquote) {
  border-left: 3px solid var(--el-color-primary);
  padding-left: 1rem;
  margin: 1rem 0;
  color: var(--el-text-color-secondary);
}

.notion-editor-wrapper :deep(.ProseMirror code) {
  background-color: var(--el-fill-color-light);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
}

.notion-editor-wrapper :deep(.ProseMirror pre) {
  background-color: var(--el-fill-color-dark);
  color: var(--el-text-color-primary);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
}

.notion-editor-wrapper :deep(.ProseMirror pre code) {
  background-color: transparent;
  padding: 0;
  color: inherit;
}

.floating-menu {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bubble-menu {
  z-index: 1000;
}

.menu-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.25rem;
  border: none;
  background: transparent;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all 0.2s;
}

.menu-button:hover {
  background-color: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.menu-button.is-active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.slash-menu {
  position: fixed;
  z-index: 1000;
  min-width: 200px;
  background: var(--el-bg-color);
  /* border: 1px solid var(--el-border-color); */
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 0.25rem;
}

.slash-menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.slash-menu-item:hover {
  background-color: var(--el-fill-color-light);
}

/* 链接弹窗样式 */
.link-popover {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2000;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 0.5rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.link-input {
  width: 300px;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--el-border-color);
  border-radius: 0.375rem;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s;
}

.link-input:focus {
  border-color: var(--el-color-primary);
}

.link-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  background: var(--el-color-primary);
  color: white;
  font-size: 0.875rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

.link-button:hover {
  opacity: 0.9;
}

.link-button.cancel {
  background: var(--el-fill-color);
  color: var(--el-text-color-regular);
}

/* 高亮样式 */
.notion-editor-wrapper :deep(.ProseMirror mark) {
  background-color: #fef08a;
  padding: 0.125rem 0;
}

/* 链接样式 */
.notion-editor-wrapper :deep(.ProseMirror a) {
  color: var(--el-color-primary);
  text-decoration: underline;
  cursor: pointer;
}

/* Turn Into 菜单样式 */
.turn-into-wrapper {
  position: relative;
}

.turn-into-trigger {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 0.25rem;
  background: transparent;
  color: var(--el-text-color-regular);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.turn-into-trigger:hover {
  background-color: var(--el-fill-color-light);
}

.trigger-text {
  white-space: nowrap;
}

.turn-into-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 2001;
  white-space: nowrap;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 0.5rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  padding: 0.5rem;
  margin-top: 0.25rem;
}

.dropdown-header {
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 0.25rem;
  background: transparent;
  color: var(--el-text-color-regular);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  width: 100%;
}

.dropdown-item:hover {
  background-color: var(--el-fill-color-light);
}

.dropdown-item.is-active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

/* 颜色选择器样式 */
.color-picker-wrapper {
  position: relative;
}

.color-trigger {
  display: flex;
  align-items: center;
  gap: 0.125rem;
  padding: 0.25rem 0.375rem;
  border: none;
  border-radius: 0.25rem;
  background: transparent;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: all 0.2s;
}

.color-trigger:hover {
  background-color: var(--el-fill-color-light);
}

.color-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 2001;
  min-width: 220px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 0.5rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  padding: 0.75rem;
  margin-top: 0.25rem;
}

.color-section {
  margin-bottom: 0.75rem;
}

.color-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  margin-bottom: 0.5rem;
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.375rem;
}

.color-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.color-item:hover {
  border-color: var(--el-color-primary);
  transform: scale(1.1);
}

.color-item.is-active {
  border-color: var(--el-color-primary);
  border-width: 2px;
}

.color-letter {
  font-size: 0.875rem;
  font-weight: 600;
}

.highlight-circle {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
}

/* 编辑器容器样式 */
.editor-container {
  position: relative;
}

/* 拖拽手柄样式 */
.notion-editor-wrapper :deep(.drag-handle) {
  position: fixed;
  opacity: 1;
  transition: opacity ease-in 0.2s;
  border-radius: 0.25rem;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10' style='fill: rgba(55, 53, 47, 0.35)'%3E%3Cpath d='M3,2 C2.44771525,2 2,1.55228475 2,1 C2,0.44771525 2.44771525,0 3,0 C3.55228475,0 4,0.44771525 4,1 C4,1.55228475 3.55228475,2 3,2 Z M3,6 C2.44771525,6 2,5.55228475 2,5 C2,4.44771525 2.44771525,4 3,4 C3.55228475,4 4,4.44771525 4,5 C4,5.55228475 3.55228475,6 3,6 Z M3,10 C2.44771525,10 2,9.55228475 2,9 C2,8.44771525 2.44771525,8 3,8 C3.55228475,8 4,8.44771525 4,9 C4,9.55228475 3.55228475,10 3,10 Z M7,2 C6.44771525,2 6,1.55228475 6,1 C6,0.44771525 6.44771525,0 7,0 C7.55228475,0 8,0.44771525 8,1 C8,1.55228475 7.55228475,2 7,2 Z M7,6 C6.44771525,6 6,5.55228475 6,5 C6,4.44771525 6.44771525,4 7,4 C7.55228475,4 8,4.44771525 8,5 C8,5.55228475 7.55228475,6 7,6 Z M7,10 C6.44771525,10 6,9.55228475 6,9 C6,8.44771525 6.44771525,8 7,8 C7.55228475,8 8,8.44771525 8,9 C8,9.55228475 7.55228475,10 7,10 Z'%3E%3C/path%3E%3C/svg%3E");
  background-size: calc(0.5em + 0.375rem) calc(0.5em + 0.375rem);
  background-repeat: no-repeat;
  background-position: center;
  width: 1.2rem;
  height: 1.5rem;
  z-index: 50;
  cursor: grab;
}

.notion-editor-wrapper :deep(.drag-handle:hover) {
  background-color: var(--el-fill-color-light);
  transition: background-color 0.2s;
}

.notion-editor-wrapper :deep(.drag-handle:active) {
  background-color: var(--el-fill-color);
  cursor: grabbing;
}

.notion-editor-wrapper :deep(.drag-handle.hide) {
  opacity: 0;
  pointer-events: none;
}

/* dark mode 拖拽手柄 */
:root.dark .notion-editor-wrapper :deep(.drag-handle) {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10' style='fill: rgba(255, 255, 255, 0.5)'%3E%3Cpath d='M3,2 C2.44771525,2 2,1.55228475 2,1 C2,0.44771525 2.44771525,0 3,0 C3.55228475,0 4,0.44771525 4,1 C4,1.55228475 3.55228475,2 3,2 Z M3,6 C2.44771525,6 2,5.55228475 2,5 C2,4.44771525 2.44771525,4 3,4 C3.55228475,4 4,4.44771525 4,5 C4,5.55228475 3.55228475,6 3,6 Z M3,10 C2.44771525,10 2,9.55228475 2,9 C2,8.44771525 2.44771525,8 3,8 C3.55228475,8 4,8.44771525 4,9 C4,9.55228475 3.55228475,10 3,10 Z M7,2 C6.44771525,2 6,1.55228475 6,1 C6,0.44771525 6.44771525,0 7,0 C7.55228475,0 8,0.44771525 8,1 C8,1.55228475 7.55228475,2 7,2 Z M7,6 C6.44771525,6 6,5.55228475 6,5 C6,4.44771525 6.44771525,4 7,4 C7.55228475,4 8,4.44771525 8,5 C8,5.55228475 7.55228475,6 7,6 Z M7,10 C6.44771525,10 6,9.55228475 6,9 C6,8.44771525 6.44771525,8 7,8 C7.55228475,8 8,8.44771525 8,9 C8,9.55228475 7.55228475,10 7,10 Z'%3E%3C/path%3E%3C/svg%3E");
}

/* 表格样式 */
.notion-editor-wrapper :deep(table) {
  border-collapse: collapse;
  margin: 1rem 0;
  overflow: hidden;
  table-layout: fixed;
  width: 100%;
}

.notion-editor-wrapper :deep(table td),
.notion-editor-wrapper :deep(table th) {
  border: 1px solid var(--el-border-color);
  box-sizing: border-box;
  min-width: 1em;
  padding: 0 0.75rem;
  position: relative;
  vertical-align: middle;
}

.notion-editor-wrapper :deep(table th) {
  background-color: var(--el-fill-color-light);
  font-weight: 600;
  text-align: left;
}

.notion-editor-wrapper :deep(table .selectedCell:after) {
  background: var(--el-color-primary-light-8);
  content: '';
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  pointer-events: none;
  position: absolute;
  z-index: 2;
}

.notion-editor-wrapper :deep(table .column-resize-handle) {
  background-color: var(--el-color-primary);
  bottom: -2px;
  pointer-events: none;
  position: absolute;
  right: -1px;
  top: 0;
  width: 2px;
}

.notion-editor-wrapper :deep(.tableWrapper) {
  margin: 1.5rem 0;
  overflow-x: auto;
}

.notion-editor-wrapper :deep(.resize-cursor) {
  cursor: col-resize;
}
</style>
