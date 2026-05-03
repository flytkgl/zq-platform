<script setup lang="ts">
import type { JSONContent } from '@tiptap/vue-3';

import type { FileUploadOptions } from './types';

import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue';

import { isTextSelection } from '@tiptap/core';
import { CellSelection } from '@tiptap/pm/tables';
import { EditorContent } from '@tiptap/vue-3';
import { BubbleMenu } from '@tiptap/vue-3/menus';
import { $t } from '@vben/locales';
import { ElMessage } from 'element-plus';

import { getFileInfo } from '#/api/core/file';
import { getFileUrl } from '#/composables/useFileUrl';
import FileSelector from '#/components/zq-form/file-selector/file-selector.vue';
import { ImageSelector } from '#/components/zq-form/image-selector';

import { useZqEditor } from './composables/use-editor';
import { useFileUpload } from './composables/use-file-upload';
import BubbleToolbar from './menus/BubbleToolbar.vue';
import DragHandleMenu from './menus/DragHandleMenu.vue';
import EmojiPicker from './menus/EmojiPicker.vue';
import SearchReplacePanel from './menus/SearchReplacePanel.vue';
import TableContextMenu from './menus/TableContextMenu.vue';
import TableFloatingToolbar from './menus/TableFloatingToolbar.vue';
import TableHandles from './menus/TableHandles.vue';

import './styles/editor.scss';

interface Props {
  modelValue?: JSONContent | string;
  mode?: 'compact' | 'full';
  placeholder?: string;
  disabled?: boolean;
  readonly?: boolean;
  minHeight?: number | string;
  maxHeight?: number | string;
  uploadOptions?: FileUploadOptions;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: undefined,
  mode: 'compact',
  placeholder: '',
  disabled: false,
  readonly: false,
  minHeight: 200,
  maxHeight: 600,
  uploadOptions: undefined,
});

const emit = defineEmits<{
  change: [value: JSONContent];
  'update:modelValue': [value: JSONContent];
  ready: [editor: any];
  focus: [event: FocusEvent];
  blur: [event: FocusEvent];
}>();

const editorContainerRef = ref<HTMLElement>();

const {
  editor,
  editorStyle,
  getJSON,
  getHTML,
  getText,
  getMarkdown,
  setContent,
  clear,
  focus,
  isEmpty,
} = useZqEditor({ props, emit });

const { handleFile, handleDrop, handlePaste } = useFileUpload(
  () => editor.value,
  props.uploadOptions,
);

function shouldShowBubble({ state, from, to }: { state: any; from: number; to: number }) {
  const { selection } = state;
  if (selection.empty || !isTextSelection(selection)) return false;
  const text = state.doc.textBetween(from, to, ' ');
  return text.trim().length > 0;
}

function onCustomUpload(e: Event) {
  const detail = (e as CustomEvent).detail;
  if (detail?.file) {
    handleFile(detail.file);
  }
}

// --- Image Selector ---
const imageSelectorRef = ref<InstanceType<typeof ImageSelector>>();
const imageSelectorValue = ref<string>();

function onOpenImageSelector() {
  imageSelectorValue.value = undefined;
  nextTick(() => {
    imageSelectorRef.value?.openModal();
  });
}

async function onImageSelected(fileId: string | string[] | undefined) {
  if (!fileId || !editor.value) return;
  const ids = Array.isArray(fileId) ? fileId : [fileId];
  for (const id of ids) {
    const url = await getFileUrl(id);
    editor.value
      .chain()
      .focus()
      .setImageBlock({ src: url, fileId: id })
      .run();
  }
  imageSelectorValue.value = undefined;
}

// --- File Selector (video / attachment) ---
const fileSelectorRef = ref<InstanceType<typeof FileSelector>>();
const fileSelectorValue = ref<string>();
const fileSelectorMode = ref<'file' | 'video'>('file');
const fileSelectorAccept = ref<string[]>([]);

function onOpenFileSelector(e: Event) {
  const detail = (e as CustomEvent).detail;
  const mode: 'file' | 'video' = detail?.mode || 'file';
  fileSelectorMode.value = mode;
  fileSelectorAccept.value =
    mode === 'video'
      ? ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime']
      : [];
  fileSelectorValue.value = undefined;
  nextTick(() => {
    fileSelectorRef.value?.openModal();
  });
}

async function onFileSelected(fileId: string | string[] | undefined) {
  if (!fileId || !editor.value) return;
  const ids = Array.isArray(fileId) ? fileId : [fileId];
  for (const id of ids) {
    try {
      const [info, url] = await Promise.all([
        getFileInfo(id) as Promise<any>,
        getFileUrl(id),
      ]);
      if (fileSelectorMode.value === 'video') {
        editor.value
          .chain()
          .focus()
          .setVideoBlock({ src: url, id })
          .run();
      } else {
        editor.value
          .chain()
          .focus()
          .setAttachmentBlock({
            id,
            name: info.name || 'file',
            size: info.file_size ?? info.size ?? 0,
            type: info.mime_type || '',
            url,
          })
          .run();
      }
    } catch {
      ElMessage.warning($t('zq-editor.upload.uploadFailed'));
      try {
        const url = await getFileUrl(id);
        if (fileSelectorMode.value === 'video') {
          editor.value.chain().focus().setVideoBlock({ src: url, id }).run();
        } else {
          editor.value
            .chain()
            .focus()
            .setAttachmentBlock({ id, name: id, size: 0, type: '', url })
            .run();
        }
      } catch {
        ElMessage.error($t('zq-editor.upload.uploadFailed'));
      }
    }
  }
  fileSelectorValue.value = undefined;
}

// --- Search & Replace ---
const showSearchPanel = ref(false);
const searchPanelRef = ref<InstanceType<typeof SearchReplacePanel>>();

function onOpenSearch(e: Event) {
  const detail = (e as CustomEvent).detail;
  showSearchPanel.value = true;
  nextTick(() => {
    searchPanelRef.value?.open({
      showReplace: detail?.showReplace ?? false,
    });
  });
}

function onCloseSearch() {
  showSearchPanel.value = false;
}

// --- Emoji Picker (from slash command) ---
const showSlashEmojiPicker = ref(false);

function onOpenEmojiPicker() {
  showSlashEmojiPicker.value = true;
}

function onCloseEmojiPicker() {
  showSlashEmojiPicker.value = false;
}

// --- Table Context Menu ---
const showTableContextMenu = ref(false);
const tableContextMenuPosition = ref({ x: 0, y: 0 });
const tableContextMenuCell = ref<HTMLElement | null>(null);

function onTableRightMouseDown(e: MouseEvent) {
  if (e.button !== 2 || !editor.value) return;

  const target = e.target as HTMLElement;
  if (!target.closest('td, th')) return;

  const { state } = editor.value.view;
  if (state.selection instanceof CellSelection) {
    e.preventDefault();
    e.stopImmediatePropagation();
  }
}

function onTableContextMenu(e: MouseEvent) {
  if (!editor.value || props.disabled || props.readonly) return;

  const target = e.target as HTMLElement;
  const cell = target.closest('td, th') as HTMLElement | null;
  const table = target.closest('table') as HTMLElement | null;

  if (!cell || !table) return;

  e.preventDefault();
  e.stopPropagation();

  const { state } = editor.value.view;
  if (!(state.selection instanceof CellSelection)) {
    const pos = editor.value.view.posAtDOM(cell, 0);
    if (pos >= 0) {
      editor.value.chain().focus().setTextSelection(pos).run();
    }
  }

  tableContextMenuPosition.value = { x: e.clientX, y: e.clientY };
  tableContextMenuCell.value = cell;
  showTableContextMenu.value = true;
}

function closeTableContextMenu() {
  showTableContextMenu.value = false;
  tableContextMenuCell.value = null;
}

onMounted(() => {
  const el = editorContainerRef.value;
  if (el) {
    el.addEventListener('zq-editor:upload-file', onCustomUpload);
    el.addEventListener('zq-editor:open-image-selector', onOpenImageSelector);
    el.addEventListener('zq-editor:open-file-selector', onOpenFileSelector);
    el.addEventListener('zq-editor:open-emoji-picker', onOpenEmojiPicker);
    el.addEventListener('zq-editor:open-search', onOpenSearch);
    el.addEventListener('mousedown', onTableRightMouseDown as EventListener, true);
    el.addEventListener('contextmenu', onTableContextMenu as EventListener);
  }
});

onBeforeUnmount(() => {
  const el = editorContainerRef.value;
  if (el) {
    el.removeEventListener('zq-editor:upload-file', onCustomUpload);
    el.removeEventListener(
      'zq-editor:open-image-selector',
      onOpenImageSelector,
    );
    el.removeEventListener('zq-editor:open-file-selector', onOpenFileSelector);
    el.removeEventListener('zq-editor:open-emoji-picker', onOpenEmojiPicker);
    el.removeEventListener('zq-editor:open-search', onOpenSearch);
    el.removeEventListener('mousedown', onTableRightMouseDown as EventListener, true);
    el.removeEventListener('contextmenu', onTableContextMenu as EventListener);
  }
});

defineExpose({
  getEditor: () => editor.value,
  getJSON,
  getHTML,
  getText,
  getMarkdown,
  setContent,
  clear,
  focus,
  isEmpty,
});
</script>

<template>
  <div
    ref="editorContainerRef"
    class="zq-editor"
    :class="{
      'zq-editor--full': mode === 'full',
      'zq-editor--compact': mode === 'compact',
    }"
    @drop.prevent="handleDrop"
    @dragover.prevent
    @paste="handlePaste"
  >
    <!-- Bubble menu -->
    <BubbleMenu
      v-if="editor && !disabled && !readonly"
      :editor="editor"
      :tippy-options="{ duration: 100, maxWidth: 'none' }"
      :should-show="shouldShowBubble"
      class="zq-editor__bubble"
    >
      <BubbleToolbar :editor="editor" />
    </BubbleMenu>

    <!-- Search & Replace panel (Teleport to body for fixed positioning) -->
    <Teleport to="body">
      <SearchReplacePanel
        v-if="showSearchPanel && editor"
        ref="searchPanelRef"
        :editor="editor"
        @close="onCloseSearch"
      />
    </Teleport>

    <!-- Editor content -->
    <div class="zq-editor__content">
      <EditorContent
        :editor="editor"
        :style="editorStyle"
        class="zq-editor__wrapper"
      />
    </div>

    <!-- Drag handle menu -->
    <DragHandleMenu v-if="editor" :editor="editor" />

    <!-- Table handles -->
    <TableHandles v-if="editor" :editor="editor" />

    <!-- Table floating toolbar -->
    <TableFloatingToolbar
      v-if="editor && !disabled && !readonly"
      :editor="editor"
    />

    <!-- Table context menu (right-click) -->
    <Teleport to="body">
      <TableContextMenu
        v-if="showTableContextMenu && editor && tableContextMenuCell"
        :editor="editor"
        :position="tableContextMenuPosition"
        :cell-element="tableContextMenuCell"
        @close="closeTableContextMenu"
      />
    </Teleport>

    <!-- Emoji picker (from slash command) -->
    <Teleport to="body">
      <div
        v-if="showSlashEmojiPicker && editor"
        class="zq-editor__emoji-overlay"
        @click.self="onCloseEmojiPicker"
      >
        <div class="zq-editor__emoji-panel">
          <EmojiPicker :editor="editor" @close="onCloseEmojiPicker" />
        </div>
      </div>
    </Teleport>

    <!-- Hidden selectors for slash commands -->
    <div style="display: none">
      <ImageSelector
        ref="imageSelectorRef"
        :model-value="imageSelectorValue"
        source="editor"
        @change="onImageSelected"
      />
    </div>
    <FileSelector
      ref="fileSelectorRef"
      :model-value="fileSelectorValue"
      :accept="fileSelectorAccept"
      trigger="button"
      source="editor"
      @change="onFileSelected"
    />
  </div>
</template>

<style scoped>
.zq-editor__bubble {
  z-index: 1000;
}
</style>

<style>
.zq-editor__emoji-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.1);
}

.zq-editor__emoji-panel {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}
</style>
