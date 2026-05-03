<script setup lang="ts">
import { computed, ref } from 'vue';

import { NodeViewWrapper } from '@tiptap/vue-3';
import { $t } from '@vben/locales';
import { ElButton } from 'element-plus';

import { ZqWhiteboard } from '#/components/zq-whiteboard';
import type { WhiteboardData } from '#/components/zq-whiteboard/types';

const props = defineProps<{
  node: any;
  updateAttributes: (attrs: Record<string, any>) => void;
  deleteNode: () => void;
  editor: any;
  selected: boolean;
}>();

const showEditor = ref(false);
const whiteboardRef = ref<InstanceType<typeof ZqWhiteboard>>();

const thumbnail = computed(() => props.node.attrs.thumbnail);
const hasData = computed(() => !!props.node.attrs.data);

const whiteboardData = computed<WhiteboardData | undefined>(() => {
  const raw = props.node.attrs.data;
  if (!raw) return undefined;
  try {
    return typeof raw === 'string' ? JSON.parse(raw) : raw;
  } catch {
    return undefined;
  }
});

function openEditor() {
  showEditor.value = true;
}

function closeEditor() {
  showEditor.value = false;
}

function handleSave(data: WhiteboardData) {
  const thumb = whiteboardRef.value?.getThumbnail() || data.thumbnail || '';
  props.updateAttributes({
    data: JSON.stringify(data),
    thumbnail: thumb,
  });
  closeEditor();
}

function handleDelete() {
  props.deleteNode();
}
</script>

<template>
  <NodeViewWrapper
    class="wb-block"
    :class="{ 'wb-block--selected': selected }"
    data-type="whiteboard"
  >
    <div class="wb-block__container">
      <div v-if="thumbnail" class="wb-block__preview" @dblclick="openEditor">
        <img :src="thumbnail" :alt="$t('zq-editor.whiteboard.title')" class="wb-block__thumbnail" />
        <div class="wb-block__overlay">
          <ElButton size="small" type="primary" @click.stop="openEditor">
            {{ $t('zq-editor.whiteboard.edit') }}
          </ElButton>
        </div>
      </div>
      <div v-else class="wb-block__empty" @click="openEditor">
        <div class="wb-block__empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="20" rx="2" />
            <path d="M7 7h.01M7 12h.01M12 7h.01M17 7h.01M12 12h.01M7 17h.01M12 17h.01M17 12h.01M17 17h.01" />
          </svg>
        </div>
        <span class="wb-block__empty-text">
          {{ $t('zq-editor.whiteboard.clickToCreate') }}
        </span>
      </div>

      <div v-if="!editor.isEditable" class="wb-block__readonly" />
    </div>

    <!-- Full-screen whiteboard editor dialog -->
    <Teleport to="body">
      <div v-if="showEditor" class="wb-block__dialog-overlay">
        <div class="wb-block__dialog">
          <!-- <div class="wb-block__dialog-header">
            <span class="wb-block__dialog-title">
              {{ $t('zq-editor.whiteboard.title') }}
            </span>
            <div class="wb-block__dialog-actions">
              <ElButton size="small" @click="handleDelete">
                {{ $t('zq-editor.whiteboard.delete') }}
              </ElButton>
              <ElButton
                size="small"
                type="primary"
                @click="whiteboardRef?.save()"
              >
                {{ $t('zq-editor.whiteboard.saveAndClose') }}
              </ElButton>
              <ElButton size="small" @click="closeEditor">
                {{ $t('zq-editor.whiteboard.close') }}
              </ElButton>
            </div>
          </div> -->
          <div class="wb-block__dialog-body">
            <ZqWhiteboard
              ref="whiteboardRef"
              :model-value="whiteboardData"
              width="100%"
              height="100%"
              @save="handleSave"
            />
          </div>
        </div>
      </div>
    </Teleport>
  </NodeViewWrapper>
</template>

<style scoped>
.wb-block {
  margin: 12px 0;
}

.wb-block--selected .wb-block__container {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 2px;
}

.wb-block__container {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  transition: outline 0.15s;
}

.wb-block__preview {
  position: relative;
  cursor: pointer;
}

.wb-block__thumbnail {
  display: block;
  width: 100%;
  height: auto;
  max-height: 400px;
  object-fit: contain;
  background: var(--el-fill-color-lighter);
}

.wb-block__overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0);
  transition: background 0.2s;
}

.wb-block__overlay .el-button {
  opacity: 0;
  transition: opacity 0.2s;
}

.wb-block__preview:hover .wb-block__overlay {
  background: rgba(0, 0, 0, 0.08);
}

.wb-block__preview:hover .wb-block__overlay .el-button {
  opacity: 1;
}

.wb-block__empty {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;
  padding: 40px;
  cursor: pointer;
  background: var(--el-fill-color-lighter);
  transition: background 0.15s;
}

.wb-block__empty:hover {
  background: var(--el-fill-color-light);
}

.wb-block__empty-icon {
  color: var(--el-text-color-placeholder);
}

.wb-block__empty-text {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.wb-block__readonly {
  position: absolute;
  inset: 0;
  cursor: default;
}

.wb-block__dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
}

.wb-block__dialog {
  display: flex;
  flex-direction: column;
  width: calc(100vw - 40px);
  height: calc(100vh - 40px);
  overflow: hidden;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}

.wb-block__dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.wb-block__dialog-title {
  font-size: 15px;
  font-weight: 600;
}

.wb-block__dialog-actions {
  display: flex;
  gap: 8px;
}

.wb-block__dialog-body {
  flex: 1;
  overflow: hidden;
}
</style>
