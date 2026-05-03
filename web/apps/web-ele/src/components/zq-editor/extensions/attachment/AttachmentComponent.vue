<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import {
  Download,
  FileArchive,
  FileAudio,
  FileCode,
  FileImage,
  FileSpreadsheet,
  FileText,
  FileVideo,
  File as GenericFile,
  Trash2,
} from '@vben/icons';
import { $t } from '@vben/locales';

import { NodeViewWrapper } from '@tiptap/vue-3';

import { getFileUrl } from '#/composables/useFileUrl';

import { formatFileSize } from './index';

const props = defineProps<{
  deleteNode: () => void;
  node: any;
  selected: boolean;
}>();

const name = computed(() => props.node.attrs.name || $t('zq-editor.attachment.untitled'));
const size = computed(() => formatFileSize(props.node.attrs.size || 0));
const fileType = computed(() => props.node.attrs.type || '');

const resolvedUrl = ref('');

async function resolveUrl() {
  const id = props.node.attrs.id;
  const url = props.node.attrs.url;
  if (id) {
    resolvedUrl.value = await getFileUrl(id);
  } else if (url) {
    resolvedUrl.value = url;
  }
}

watch(
  () => [props.node.attrs.id, props.node.attrs.url],
  () => resolveUrl(),
  { immediate: true },
);

const fileIconMap: Record<string, any> = {
  image: FileImage,
  video: FileVideo,
  audio: FileAudio,
  pdf: FileText,
  doc: FileText,
  xls: FileSpreadsheet,
  zip: FileArchive,
  code: FileCode,
};

const fileIcon = computed(() => {
  const t = fileType.value.toLowerCase();
  if (t.startsWith('image')) return fileIconMap.image;
  if (t.startsWith('video')) return fileIconMap.video;
  if (t.startsWith('audio')) return fileIconMap.audio;
  if (t.includes('pdf')) return fileIconMap.pdf;
  if (t.includes('doc') || t.includes('word')) return fileIconMap.doc;
  if (t.includes('xls') || t.includes('sheet')) return fileIconMap.xls;
  if (t.includes('zip') || t.includes('rar') || t.includes('7z')) return fileIconMap.zip;
  return GenericFile;
});

async function handleDownload() {
  const id = props.node.attrs.id;
  if (id) {
    const url = await getFileUrl(id);
    window.open(url, '_blank');
  } else if (resolvedUrl.value) {
    window.open(resolvedUrl.value, '_blank');
  }
}
</script>

<template>
  <NodeViewWrapper
    class="zq-attachment"
    :class="{ 'is-selected': selected }"
    data-type="attachment"
  >
    <div class="zq-attachment__body" contenteditable="false">
      <div class="zq-attachment__icon">
        <component :is="fileIcon" class="h-5 w-5" />
      </div>
      <div class="zq-attachment__info">
        <span class="zq-attachment__name">{{ name }}</span>
        <span class="zq-attachment__size">{{ size }}</span>
      </div>
      <div class="zq-attachment__actions">
        <button class="zq-attachment__btn" :title="$t('zq-editor.attachment.download')" @click="handleDownload">
          <Download class="h-4 w-4" />
        </button>
        <button class="zq-attachment__btn zq-attachment__btn--danger" :title="$t('zq-editor.attachment.delete')" @click="deleteNode">
          <Trash2 class="h-4 w-4" />
        </button>
      </div>
    </div>
  </NodeViewWrapper>
</template>

<style scoped>
.zq-attachment {
  margin: 0.5rem 0;
}

.zq-attachment__body {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
  transition: all 0.15s;
}

.zq-attachment.is-selected .zq-attachment__body {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 1px var(--el-color-primary-light-5);
}

.zq-attachment__body:hover {
  background: var(--el-fill-color-light);
}

.zq-attachment__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.zq-attachment__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.zq-attachment__name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.zq-attachment__size {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
}

.zq-attachment__actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.zq-attachment__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 5px;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.zq-attachment__btn:hover {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

.zq-attachment__btn--danger:hover {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}
</style>
