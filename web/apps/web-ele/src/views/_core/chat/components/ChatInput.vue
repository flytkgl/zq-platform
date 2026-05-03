<script setup lang="ts">
import type { ChatMessage } from '#/api/core/chat';

import { computed, nextTick, onMounted, ref, watch } from 'vue';

import {
  CornerUpLeft,
  Loader2,
  Mic,
  Paperclip,
  Send,
  Smile,
  Square,
  X,
} from '@vben/icons';
import { $t } from '@vben/locales';

import { ElMessage, ElPopover, ElTooltip } from 'element-plus';

import { uploadFile } from '#/api/core/file';
import { getFileTypeIcon } from '#/assets/file-icons';

import {
  formatVoiceDuration,
  useVoiceRecorder,
} from '../composables/useVoiceRecorder';
import EmojiPicker from './EmojiPicker.vue';

const props = defineProps<{
  disabled?: boolean;
  replyTo?: ChatMessage | null;
  sending?: boolean;
}>();

const emit = defineEmits<{
  cancelReply: [];
  send: [
    content: string,
    msgType: string,
    fileId?: string,
    fileName?: string,
    localUrl?: string,
    extra?: Record<string, any>,
  ];
  typing: [];
}>();

const inputText = ref('');
const uploading = ref(false);
const inputRef = ref<HTMLTextAreaElement>();
const emojiVisible = ref(false);

// ---- 语音录音 ----
const {
  isRecording,
  duration: recordingDuration,
  startRecording,
  stopRecording,
  cancelRecording,
} = useVoiceRecorder();
const voiceUploading = ref(false);

async function handleStartRecording() {
  const ok = await startRecording();
  if (!ok) {
    ElMessage.warning($t('chat.micPermissionDenied'));
  }
}

async function handleStopRecording() {
  const result = await stopRecording();
  if (!result) return;

  if (result.duration < 1) {
    ElMessage.warning($t('chat.voiceTooShort'));
    return;
  }

  voiceUploading.value = true;
  try {
    const file = new File([result.blob], `voice_${Date.now()}.webm`, {
      type: result.blob.type,
    });
    const res = await uploadFile(file, { source: 'chat' });
    if (res?.id) {
      emit('send', '', 'voice', res.id, file.name, undefined, {
        duration: result.duration,
      });
    }
  } catch (error) {
    console.error('\u8BED\u97F3\u4E0A\u4F20\u5931\u8D25:', error);
  } finally {
    voiceUploading.value = false;
  }
}

function handleCancelRecording() {
  cancelRecording();
}

function handleEmojiSelect(emoji: string) {
  const el = inputRef.value;
  if (el) {
    const start = el.selectionStart ?? inputText.value.length;
    const end = el.selectionEnd ?? start;
    inputText.value =
      inputText.value.slice(0, start) + emoji + inputText.value.slice(end);
    nextTick(() => {
      const pos = start + emoji.length;
      el.setSelectionRange(pos, pos);
      el.focus();
      autoResize();
    });
  } else {
    inputText.value += emoji;
  }
  emojiVisible.value = false;
}

// ---- 暂存附件 ----
interface PendingFile {
  fileId: string;
  fileName: string;
  fileType: 'file' | 'image';
  localUrl?: string;
  ext: string;
}
const pendingFiles = ref<PendingFile[]>([]);

const IMAGE_EXTS = new Set([
  'bmp',
  'gif',
  'ico',
  'jpeg',
  'jpg',
  'png',
  'svg',
  'tiff',
  'webp',
]);

function isImageExt(ext: string): boolean {
  return IMAGE_EXTS.has(ext.toLowerCase().replace('.', ''));
}

function getExt(name: string): string {
  const idx = name.lastIndexOf('.');
  return idx === -1 ? '' : name.slice(idx + 1).toLowerCase();
}

function removePendingFile(index: number) {
  const pf = pendingFiles.value[index];
  if (pf?.localUrl) URL.revokeObjectURL(pf.localUrl);
  pendingFiles.value.splice(index, 1);
}

const canSend = computed(() => {
  return (
    (inputText.value.trim() || pendingFiles.value.length > 0) &&
    !props.sending &&
    !uploading.value
  );
});

function autoResize() {
  const el = inputRef.value;
  if (!el) return;
  el.style.height = 'auto';
  const maxH = 200; // ~6 rows
  el.style.height = `${Math.min(el.scrollHeight, maxH)}px`;
  el.style.overflowY = el.scrollHeight > maxH ? 'auto' : 'hidden';
}

watch(
  () => props.replyTo,
  (val) => {
    if (val) {
      nextTick(() => {
        inputRef.value?.focus();
      });
    }
  },
);

onMounted(() => {
  nextTick(autoResize);
});

let typingTimer: null | ReturnType<typeof setTimeout> = null;

function handleInput() {
  autoResize();
  if (!typingTimer) {
    emit('typing');
    typingTimer = setTimeout(() => {
      typingTimer = null;
    }, 2000);
  }
}

function handleSend() {
  if (!canSend.value) return;

  // 发送所有暂存附件
  if (pendingFiles.value.length > 0) {
    for (const pf of pendingFiles.value) {
      emit(
        'send',
        pf.fileName,
        pf.fileType,
        pf.fileId,
        pf.fileName,
        pf.localUrl,
      );
    }
    pendingFiles.value = []; // 不 revoke localUrl，交给消息列表使用
  }

  // 发送文本
  const text = inputText.value.trim();
  if (text) {
    emit('send', text, 'text');
    inputText.value = '';
    nextTick(autoResize);
  }

  if (props.replyTo) {
    emit('cancelReply');
  }
}

function handleKeydown(e: Event) {
  const ke = e as KeyboardEvent;
  if (ke.key === 'Enter' && !ke.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}

async function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items;
  if (!items) return;

  const files: File[] = [];
  for (const item of items) {
    if (item.kind === 'file') {
      const file = item.getAsFile();
      if (file) {
        // 截图粘贴时文件名通常为 image.png，加上时间戳区分
        const name =
          file.name === 'image.png'
            ? `screenshot_${Date.now()}.png`
            : file.name;
        files.push(new File([file], name, { type: file.type }));
      }
    }
  }

  if (files.length > 0) {
    e.preventDefault();
    await processFiles(files);
  }
}

async function handleUploadFile() {
  await handleFileUpload('file');
}

async function processFiles(files: File[]) {
  if (files.length === 0) return;
  uploading.value = true;
  try {
    for (const file of files) {
      const ext = getExt(file.name);
      const actualType: 'file' | 'image' = isImageExt(ext) ? 'image' : 'file';
      const localUrl = isImageExt(ext) ? URL.createObjectURL(file) : undefined;

      try {
        const res = await uploadFile(file, { source: 'chat' });
        if (res?.id) {
          pendingFiles.value.push({
            fileId: res.id,
            fileName: file.name,
            fileType: actualType,
            localUrl,
            ext,
          });
        } else if (localUrl) {
          URL.revokeObjectURL(localUrl);
        }
      } catch (error) {
        console.error('上传失败:', file.name, error);
        if (localUrl) URL.revokeObjectURL(localUrl);
      }
    }
  } finally {
    uploading.value = false;
  }
}

async function handleFileUpload(type: 'file' | 'image') {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  if (type === 'image') {
    input.accept = 'image/*';
  }
  input.addEventListener('change', async () => {
    const files = input.files;
    if (!files || files.length === 0) return;
    await processFiles([...files]);
  });
  input.click();
}

// ---- 拖拽上传 ----
const isDragOver = ref(false);
let dragCounter = 0;

function handleDragEnter(e: DragEvent) {
  e.preventDefault();
  dragCounter++;
  if (e.dataTransfer?.types.includes('Files')) {
    isDragOver.value = true;
  }
}

function handleDragOver(e: DragEvent) {
  e.preventDefault();
}

function handleDragLeave(e: DragEvent) {
  e.preventDefault();
  dragCounter--;
  if (dragCounter <= 0) {
    dragCounter = 0;
    isDragOver.value = false;
  }
}

async function handleDrop(e: DragEvent) {
  e.preventDefault();
  dragCounter = 0;
  isDragOver.value = false;
  const files = e.dataTransfer?.files;
  if (!files || files.length === 0) return;
  await processFiles([...files]);
}
</script>

<template>
  <div
    class="relative mb-4"
    @dragenter="handleDragEnter"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <!-- 拖拽上传遮罩 -->
    <div v-if="isDragOver" class="drag-overlay mx-3">
      <div class="drag-overlay-content">
        <Paperclip class="h-6 w-6" />
        <span class="text-sm font-medium">{{ $t('chat.dropToUpload') }}</span>
      </div>
    </div>
    <!-- 回复预览条 -->
    <div
      v-if="replyTo"
      class="flex items-center gap-2 bg-[var(--el-fill-color-light)] px-4 py-2"
    >
      <CornerUpLeft
        class="h-3.5 w-3.5 shrink-0 text-[var(--el-color-primary)]"
      />
      <div class="min-w-0 flex-1">
        <div class="text-xs font-medium text-[var(--el-color-primary)]">
          {{ $t('chat.replyingTo', { name: replyTo.sender_name }) }}
        </div>
        <div class="truncate text-xs text-[var(--el-text-color-secondary)]">
          {{ replyTo.content || `[${replyTo.msg_type}]` }}
        </div>
      </div>
      <X
        class="h-4 w-4 shrink-0 cursor-pointer text-[var(--el-text-color-placeholder)] transition-colors hover:text-[var(--el-text-color-primary)]"
        @click="emit('cancelReply')"
      />
    </div>

    <!-- 附件预览列表 -->
    <div v-if="pendingFiles.length > 0" class="pending-files-area">
      <div
        v-for="(pf, idx) in pendingFiles"
        :key="pf.fileId"
        class="pending-file-item"
      >
        <div class="pending-file-preview">
          <img
            v-if="pf.localUrl"
            :src="pf.localUrl"
            class="pending-file-thumb"
          />
          <img
            v-else
            :src="getFileTypeIcon(pf.ext)"
            class="pending-file-icon"
          />
        </div>
        <div class="min-w-0 flex-1">
          <div
            class="truncate text-xs font-medium text-[var(--el-text-color-primary)]"
          >
            {{ pf.fileName }}
          </div>
        </div>
        <X
          class="h-3.5 w-3.5 shrink-0 cursor-pointer text-[var(--el-text-color-placeholder)] transition-colors hover:text-[var(--el-text-color-primary)]"
          @click="removePendingFile(idx)"
        />
      </div>
    </div>

    <div class="chat-input-container">
      <!-- 录音中 UI -->
      <div v-if="isRecording" class="voice-recording-bar">
        <div class="voice-recording-indicator">
          <span class="voice-recording-dot"></span>
          <span class="text-xs font-medium text-[var(--el-color-danger)]">
            {{ formatVoiceDuration(recordingDuration) }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button class="voice-cancel-btn" @click="handleCancelRecording">
            <X class="h-4 w-4" />
          </button>
          <button class="voice-stop-btn" @click="handleStopRecording">
            <Square class="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <!-- 语音上传中 -->
      <div v-else-if="voiceUploading" class="voice-recording-bar">
        <div
          class="flex items-center gap-2 text-xs text-[var(--el-text-color-placeholder)]"
        >
          <Loader2 class="h-3.5 w-3.5 animate-spin" />
          {{ $t('chat.voiceUploading') }}
        </div>
      </div>

      <!-- 正常输入 UI -->
      <template v-else>
        <!-- 上传中提示 -->
        <div
          v-if="uploading"
          class="flex items-center gap-2 px-3 pt-2 text-xs text-[var(--el-text-color-placeholder)]"
        >
          <Loader2 class="h-3.5 w-3.5 animate-spin" />
          {{ $t('chat.uploading') || '上传中...' }}
        </div>
        <!-- 输入框 -->
        <textarea
          ref="inputRef"
          v-model="inputText"
          class="chat-textarea"
          :placeholder="$t('chat.inputPlaceholder')"
          :disabled="disabled"
          rows="2"
          @input="handleInput"
          @keydown="handleKeydown"
          @paste="handlePaste"
        ></textarea>
        <!-- 底部操作栏 -->
        <div class="chat-input-actions">
          <div class="flex items-center gap-1.5">
            <ElTooltip :content="$t('chat.sendFile')" placement="top">
              <Paperclip
                class="chat-action-icon"
                :class="{ 'pointer-events-none opacity-50': uploading }"
                @click="handleUploadFile"
              />
            </ElTooltip>
            <ElPopover
              v-model:visible="emojiVisible"
              placement="top-start"
              :width="336"
              trigger="click"
              :show-arrow="false"
              :offset="8"
              popper-class="emoji-popover"
            >
              <template #reference>
                <span
                  class="chat-action-icon inline-flex"
                  :title="$t('chat.emoji')"
                >
                  <Smile class="h-[18px] w-[18px]" />
                </span>
              </template>
              <EmojiPicker @select="handleEmojiSelect" />
            </ElPopover>
          </div>
          <div class="flex items-center gap-1.5">
            <ElTooltip :content="$t('chat.voiceMessage')" placement="top">
              <button class="chat-send-btn" @click="handleStartRecording">
                <Mic class="h-4 w-4" />
              </button>
            </ElTooltip>
            <button
              class="chat-send-btn"
              :class="{ 'chat-send-btn--active': canSend }"
              :disabled="!canSend"
              @click="handleSend"
            >
              <Send class="h-4 w-4" />
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.chat-input-container {
  display: flex;
  flex-direction: column;
  margin: 8px 12px;
  background: var(--el-fill-color-light);
  border: 1px solid transparent;
  border-radius: 12px;
  transition: all 0.2s;
}

.chat-input-container:focus-within {
  background: var(--el-bg-color);
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
}

.chat-textarea {
  display: block;
  width: 100%;
  max-height: 200px;
  padding: 10px 12px 0;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  color: var(--el-text-color-primary);
  resize: none;
  background: transparent;
  border: none;
  outline: none;
}

.chat-textarea::placeholder {
  color: var(--el-text-color-placeholder);
}

.chat-textarea:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.chat-input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px 6px;
}

.chat-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  padding: 0;
  color: var(--el-text-color-placeholder);
  cursor: not-allowed;
  background: transparent;
  border: none;
  border-radius: 8px;
  transition: all 0.2s;
}

.chat-send-btn--active {
  color: #fff;
  cursor: pointer;
  background: var(--el-color-primary);
}

.chat-send-btn--active:hover {
  background: var(--el-color-primary-light-3);
}

.chat-send-btn--active:active {
  background: var(--el-color-primary-dark-2);
}

.pending-files-area {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: 120px;
  margin: 0 12px;
  padding: 6px 0;
  overflow-y: auto;
}

.pending-file-item {
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 200px;
  padding: 4px 8px;
  background: var(--el-fill-color-lighter);
  border-radius: 6px;
}

.pending-file-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 4px;
}

.pending-file-thumb {
  width: 32px;
  height: 32px;
  object-fit: cover;
  border-radius: 4px;
}

.pending-file-icon {
  width: 24px;
  height: 24px;
}

.chat-action-icon {
  width: 18px;
  height: 18px;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  outline: none;
  transition: color 0.2s;
}

.chat-action-icon:hover {
  color: var(--el-color-primary);
}

.chat-action-icon:focus,
.chat-action-icon:focus-visible {
  outline: none;
  box-shadow: none;
}

/* ---- 语音录音 ---- */
.voice-recording-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
}

.voice-recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.voice-recording-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: var(--el-color-danger);
  border-radius: 50%;
  animation: voice-pulse 1s ease-in-out infinite;
}

@keyframes voice-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

.voice-cancel-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
}

.voice-cancel-btn:hover {
  color: var(--el-text-color-primary);
  background: var(--el-fill-color-dark);
}

.voice-stop-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  color: #fff;
  background: var(--el-color-danger);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
}

.voice-stop-btn:hover {
  background: var(--el-color-danger-light-3);
}

/* ---- 拖拽上传遮罩 ---- */
.drag-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-color-primary-light-9);
  border: 2px dashed var(--el-color-primary);
  border-radius: 12px;
}

.drag-overlay-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: var(--el-color-primary);
  pointer-events: none;
}
</style>

<style>
.emoji-popover.el-popover.el-popper {
  padding: 0 !important;
}
</style>
