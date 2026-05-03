<script setup lang="ts">
import type { ChatMessage } from '#/api/core/chat';

import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue';
import { useRouter } from 'vue-router';

import {
  BellRing,
  ChevronRight,
  Copy,
  CornerUpLeft,
  Loader2,
  Pause,
  Play,
  Undo2,
} from '@vben/icons';
import { $t } from '@vben/locales';
import { useUserStore } from '@vben/stores';

import { useVirtualizer } from '@tanstack/vue-virtual';
import dayjs from 'dayjs';
import { ElButton, ElImageViewer, ElMessage, ElMessageBox } from 'element-plus';

import { getFileTypeIcon } from '#/assets/file-icons';
import UserAvatar from '#/components/user-avatar/index.vue';
import { getFileUrl } from '#/composables/useFileUrl';

const props = defineProps<{
  hasMore?: boolean;
  loading?: boolean;
  messages: ChatMessage[];
  typingText?: string;
}>();

const emit = defineEmits<{
  loadMore: [];
  recall: [messageId: string];
  reply: [message: ChatMessage];
}>();

const userStore = useUserStore();
const currentUserId = userStore.userInfo?.userId || '';
const router = useRouter();

function isNotifyCard(msg: ChatMessage): boolean {
  return !!(msg.extra && (msg.extra as any).notify);
}

function handleNotifyClick(msg: ChatMessage) {
  const extra = msg.extra as any;
  if (!extra?.link_type || !extra?.link_id) return;
  let path = '';
  switch (extra.link_type) {
    case 'announcement': {
      path = '/message/announcement-list';
      break;
    }
    case 'workflow_instance': {
      path = `/app/workflow_center/workflow/initiated?id=${extra.link_id}`;
      break;
    }
    case 'workflow_task': {
      path = `/app/workflow_center/workflow/pending?id=${extra.link_id}`;
      break;
    }
  }
  if (path) {
    const url = router.resolve(path).href;
    window.open(url, '_blank');
  }
}

const scrollContainerRef = ref<HTMLDivElement>();
const isAutoScroll = ref(true);
const highlightedMessageId = ref<null | string>(null);
let pendingLoadMore = false;

// ---- 虚拟滚动 ----
const virtualizer = useVirtualizer(
  computed(() => ({
    count: props.messages.length,
    getScrollElement: () => scrollContainerRef.value ?? null,
    estimateSize: () => 72,
    overscan: 10,
    getItemKey: (index: number) => props.messages[index]?.id ?? index,
  })),
);

function isMyMessage(msg: ChatMessage): boolean {
  return msg.sender_id === currentUserId;
}

function formatTime(time?: string): string {
  if (!time) return '';
  return dayjs(time).format('HH:mm');
}

function shouldShowTime(index: number): boolean {
  if (index === 0) return true;
  const prev = props.messages[index - 1];
  const curr = props.messages[index];
  if (!prev?.sys_create_datetime || !curr?.sys_create_datetime) return false;
  return (
    dayjs(curr.sys_create_datetime).diff(
      dayjs(prev.sys_create_datetime),
      'minute',
    ) > 5
  );
}

function formatDateDivider(time?: string): string {
  if (!time) return '';
  const d = dayjs(time);
  const now = dayjs();
  if (d.isSame(now, 'day')) return d.format('HH:mm');
  if (d.isSame(now.subtract(1, 'day'), 'day'))
    return `${$t('chat.yesterday')} ${d.format('HH:mm')}`;
  if (d.isSame(now, 'year')) return d.format('MM/DD HH:mm');
  return d.format('YYYY/MM/DD HH:mm');
}

function scrollToBottom(smooth = true) {
  nextTick(() => {
    if (props.messages.length === 0) return;
    virtualizer.value.scrollToIndex(props.messages.length - 1, {
      align: 'end',
      behavior: smooth ? 'smooth' : 'auto',
    });
    // 虚拟列表需要二次滚动确保到底（首次 scrollToIndex 后 DOM 高度可能变化）
    nextTick(() => {
      virtualizer.value.scrollToIndex(props.messages.length - 1, {
        align: 'end',
        behavior: 'auto',
      });
    });
  });
}

function handleScroll() {
  const el = scrollContainerRef.value;
  if (!el) return;
  // 如果滚动到顶部附近，加载更多
  if (el.scrollTop < 50 && props.hasMore && !props.loading) {
    pendingLoadMore = true;
    emit('loadMore');
  }
  // 判断是否在底部附近
  isAutoScroll.value = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
}

// 消息数量变化时自动滚动（捕获 push/splice 等原地修改）
let prevMessageCount = 0;
watch(
  () => props.messages.length,
  (newLen) => {
    const insertedCount = newLen - prevMessageCount;
    // 加载历史消息（顶部插入）：保持当前可视区域不动
    if (pendingLoadMore && insertedCount > 0) {
      pendingLoadMore = false;
      nextTick(() => {
        // 滚动到插入前的第一条消息（现在偏移了 insertedCount）
        virtualizer.value.scrollToIndex(insertedCount, {
          align: 'start',
          behavior: 'auto',
        });
      });
      prevMessageCount = newLen;
      return;
    }
    if (insertedCount > 0 && isAutoScroll.value) {
      scrollToBottom();
    }
    prevMessageCount = newLen;
  },
);

// 消息列表被整体替换时滚到底部（捕获 messages.value = newArray）
watch(
  () => props.messages,
  (newMsgs, oldMsgs) => {
    if (!newMsgs || newMsgs.length === 0) return;
    // 引用不同说明是整体替换（缓存→服务端、切换会话等）
    if (newMsgs !== oldMsgs) {
      isAutoScroll.value = true;
      scrollToBottom(false);
      prevMessageCount = newMsgs.length;
    }
  },
);

// ---- 右键菜单 ----
const contextMenu = ref<{
  message: ChatMessage | null;
  visible: boolean;
  x: number;
  y: number;
}>({
  visible: false,
  x: 0,
  y: 0,
  message: null,
});

function handleContextMenu(e: MouseEvent, msg: ChatMessage) {
  e.preventDefault();
  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    message: msg,
  };
}

function closeContextMenu() {
  contextMenu.value.visible = false;
  contextMenu.value.message = null;
}

async function handleCopy(msg: ChatMessage) {
  closeContextMenu();
  if (msg.content) {
    await navigator.clipboard.writeText(msg.content);
    ElMessage.success($t('chat.copySuccess'));
  }
}

function handleReply(msg: ChatMessage) {
  closeContextMenu();
  emit('reply', msg);
}

async function handleRecallFromMenu(msg: ChatMessage) {
  closeContextMenu();
  try {
    await ElMessageBox.confirm(`${$t('chat.recall')}?`, {
      type: 'warning',
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
    });
    emit('recall', msg.id);
  } catch {
    // cancelled
  }
}

// 点击其他区域关闭菜单
function onDocumentClick() {
  if (contextMenu.value.visible) {
    closeContextMenu();
  }
}

// 初始滚动到底部
onMounted(() => {
  scrollToBottom(false);
  document.addEventListener('click', onDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick);
  if (loadImageUrlsTimer) clearTimeout(loadImageUrlsTimer);
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
});

function scrollToMessage(messageId: string) {
  const idx = props.messages.findIndex((m) => m.id === messageId);
  if (idx !== -1) {
    virtualizer.value.scrollToIndex(idx, {
      align: 'center',
      behavior: 'smooth',
    });
    highlightedMessageId.value = messageId;
    setTimeout(() => {
      highlightedMessageId.value = null;
    }, 1500);
  }
}

// ---- 文件类型判断 ----
function getExtFromName(name?: string): string {
  if (!name) return '';
  const idx = name.lastIndexOf('.');
  return idx === -1 ? '' : name.slice(idx + 1);
}

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

function isImageFile(msg: ChatMessage): boolean {
  const ext = (msg.file_ext || getExtFromName(msg.file_name))
    .toLowerCase()
    .replace('.', '');
  return IMAGE_EXTS.has(ext);
}

function isDisplayableImage(m: ChatMessage): boolean {
  return (
    (m.msg_type === 'image' || (m.msg_type === 'file' && isImageFile(m))) &&
    !!m.file_id
  );
}

// ---- 图片URL缓存 ----
const imageUrlMap = ref<Record<string, string>>({});
let loadImageUrlsTimer: null | ReturnType<typeof setTimeout> = null;
let loadingImageUrls = false;

function getImageUrl(fileId: string): string {
  return imageUrlMap.value[fileId] || '';
}

async function loadImageUrls() {
  if (loadingImageUrls) return;
  const imageMessages = props.messages.filter(
    (m) => isDisplayableImage(m) && !imageUrlMap.value[m.file_id!],
  );
  if (imageMessages.length === 0) return;

  loadingImageUrls = true;
  try {
    // 并发控制：每批最多5个
    const BATCH_SIZE = 5;
    const newMap = { ...imageUrlMap.value };
    let changed = false;

    for (let i = 0; i < imageMessages.length; i += BATCH_SIZE) {
      const batch = imageMessages.slice(i, i + BATCH_SIZE);
      const results = await Promise.allSettled(
        batch.map(async (m) => {
          const url = await getFileUrl(m.file_id!);
          return { fileId: m.file_id!, url };
        }),
      );

      for (const result of results) {
        if (result.status === 'fulfilled' && result.value.url) {
          newMap[result.value.fileId] = result.value.url;
          changed = true;
        }
      }
    }

    if (changed) {
      imageUrlMap.value = newMap;
    }
  } finally {
    loadingImageUrls = false;
  }
}

function debouncedLoadImageUrls() {
  if (loadImageUrlsTimer) clearTimeout(loadImageUrlsTimer);
  loadImageUrlsTimer = setTimeout(() => {
    loadImageUrls();
  }, 100);
}

// 精确监听：消息数量变化 或 消息ID变化（临时消息被替换）
const messageKey = computed(() => {
  const msgs = props.messages;
  const len = msgs.length;
  if (len === 0) return '';
  // 首尾ID + 长度 + 发送中数量（临时消息被替换时_sending数量会变）
  const sendingCount = msgs.reduce((n, m) => n + (m._sending ? 1 : 0), 0);
  return `${len}_${msgs[0]?.id}_${msgs[len - 1]?.id}_${sendingCount}`;
});

watch(
  messageKey,
  () => {
    debouncedLoadImageUrls();
  },
  { immediate: true },
);

// ---- 图片预览 ----
const previewVisible = ref(false);
const previewUrls = ref<string[]>([]);
const previewIndex = ref(0);

function formatFileSize(size?: number): string {
  if (size === undefined || size === null) return '';
  if (size === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let s = size;
  while (s >= 1024 && i < units.length - 1) {
    s /= 1024;
    i++;
  }
  return `${s.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function handleFilePreview(msg: ChatMessage) {
  if (!msg.file_id) return;
  const query = new URLSearchParams({
    name: msg.file_name || '',
    ext: msg.file_ext || '',
  });
  window.open(`/file-preview/${msg.file_id}?${query.toString()}`, '_blank');
}

async function handleImagePreview(msg: ChatMessage) {
  const imageMessages = props.messages.filter((m) => isDisplayableImage(m));
  // 复用已缓存的URL，只请求缺失的
  const urls: string[] = [];
  const missing: { fileId: string; idx: number }[] = [];
  for (const [i, imageMessage] of imageMessages.entries()) {
    const fid = imageMessage!.file_id!;
    const cached = imageUrlMap.value[fid];
    if (cached) {
      urls.push(cached);
    } else {
      urls.push('');
      missing.push({ idx: i, fileId: fid });
    }
  }
  // 批量加载缺失的
  if (missing.length > 0) {
    const results = await Promise.allSettled(
      missing.map((m) => getFileUrl(m.fileId)),
    );
    const newMap = { ...imageUrlMap.value };
    for (const [j, r] of results.entries()) {
      if (r?.status === 'fulfilled' && r.value) {
        urls[missing[j]!.idx] = r.value;
        newMap[missing[j]!.fileId] = r.value;
      }
    }
    imageUrlMap.value = newMap;
  }
  previewUrls.value = urls.filter(Boolean);
  previewIndex.value = imageMessages.findIndex((m) => m.id === msg.id);
  if (previewIndex.value < 0) previewIndex.value = 0;
  previewVisible.value = true;
}

// ---- 语音播放 ----
const playingVoiceId = ref<null | string>(null);
let currentAudio: HTMLAudioElement | null = null;

function formatVoiceDuration(seconds?: number): string {
  if (!seconds || seconds <= 0) return '0:01';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0
    ? `${m}:${String(s).padStart(2, '0')}`
    : `0:${String(s).padStart(2, '0')}`;
}

function getVoiceDuration(msg: ChatMessage): number {
  return msg.extra?.duration || 0;
}

function getVoiceBubbleWidth(msg: ChatMessage): string {
  const dur = getVoiceDuration(msg);
  const minW = 100;
  const maxW = 220;
  const w = Math.min(maxW, minW + dur * 4);
  return `${w}px`;
}

async function toggleVoicePlay(msg: ChatMessage) {
  if (playingVoiceId.value === msg.id) {
    currentAudio?.pause();
    currentAudio = null;
    playingVoiceId.value = null;
    return;
  }

  // 停止当前播放
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }

  if (!msg.file_id) return;

  try {
    const url = await getFileUrl(msg.file_id);
    if (!url) return;
    const audio = new Audio(url);
    currentAudio = audio;
    playingVoiceId.value = msg.id;

    audio.addEventListener('ended', () => {
      if (playingVoiceId.value === msg.id) {
        playingVoiceId.value = null;
      }
      currentAudio = null;
    });
    audio.onerror = () => {
      if (playingVoiceId.value === msg.id) {
        playingVoiceId.value = null;
      }
      currentAudio = null;
    };
    await audio.play();
  } catch {
    playingVoiceId.value = null;
    currentAudio = null;
  }
}

defineExpose({ scrollToBottom, scrollToMessage });
</script>

<template>
  <div
    ref="scrollContainerRef"
    class="virtual-scroll-container flex-1"
    @scroll="handleScroll"
  >
    <!-- 加载更多 -->
    <div v-if="hasMore" class="flex justify-center py-3">
      <ElButton v-if="!loading" text size="small" @click="emit('loadMore')">
        {{ $t('chat.loadMore') }}
      </ElButton>
      <div
        v-else
        class="flex items-center gap-1 text-xs text-[var(--el-text-color-placeholder)]"
      >
        <Loader2 class="h-3 w-3 animate-spin" />
        {{ $t('chat.loading') }}
      </div>
    </div>

    <!-- 虚拟滚动容器 -->
    <div
      class="virtual-list-inner"
      :style="{ height: `${virtualizer.getTotalSize()}px` }"
    >
      <div
        v-for="vRow in virtualizer.getVirtualItems()"
        :key="String(vRow.key)"
        :ref="
          (el) => {
            if (el) virtualizer.measureElement(el as HTMLElement);
          }
        "
        :data-index="vRow.index"
        class="virtual-item"
        :style="{
          transform: `translateY(${vRow.start}px)`,
        }"
      >
        <template v-if="messages[vRow.index]">
          <!-- 时间分割线 -->
          <div
            v-if="shouldShowTime(vRow.index)"
            class="my-3 flex justify-center"
          >
            <span
              class="rounded-full bg-[var(--el-fill-color)] px-3 py-0.5 text-xs text-[var(--el-text-color-placeholder)]"
            >
              {{ formatDateDivider(messages[vRow.index]!.sys_create_datetime) }}
            </span>
          </div>

          <!-- 撤回消息 -->
          <div
            v-if="messages[vRow.index]!.is_recalled"
            class="my-2 flex justify-center"
          >
            <span class="text-xs text-[var(--el-text-color-placeholder)]">
              {{ messages[vRow.index]!.sender_name || '' }}
              {{ $t('chat.messageRecalled') }}
            </span>
          </div>

          <!-- 系统消息 -->
          <div
            v-else-if="messages[vRow.index]!.msg_type === 'system'"
            class="my-2 flex justify-center"
          >
            <span
              class="rounded-full bg-[var(--el-fill-color)] px-3 py-0.5 text-xs text-[var(--el-text-color-placeholder)]"
            >
              {{ messages[vRow.index]!.content }}
            </span>
          </div>

          <!-- 普通消息 -->
          <div
            v-else
            :data-message-id="messages[vRow.index]!.id"
            class="my-2.5 flex items-start gap-2"
            :class="[
              { 'flex-row-reverse': isMyMessage(messages[vRow.index]!) },
              highlightedMessageId === messages[vRow.index]!.id
                ? 'message-highlight'
                : '',
            ]"
          >
            <!-- 头像 -->
            <UserAvatar
              :user-id="messages[vRow.index]!.sender_id"
              :name="messages[vRow.index]!.sender_name"
              :avatar="messages[vRow.index]!.sender_avatar"
              :size="36"
              :font-size="14"
              :shadow="true"
              class="shrink-0"
            />

            <!-- 消息体 -->
            <div
              class="flex max-w-[70%] flex-col"
              :class="{ 'items-end': isMyMessage(messages[vRow.index]!) }"
            >
              <!-- 发送者名称 -->
              <span
                v-if="!isMyMessage(messages[vRow.index]!)"
                class="mb-0.5 text-xs text-[var(--el-text-color-placeholder)]"
              >
                {{ messages[vRow.index]!.sender_name }}
              </span>

              <!-- 回复引用 -->
              <div
                v-if="
                  messages[vRow.index]!.reply_to_id &&
                  messages[vRow.index]!.reply_to_preview
                "
                class="reply-quote mb-1 max-w-full cursor-pointer truncate rounded bg-[var(--el-fill-color)] px-2 py-1 text-xs text-[var(--el-text-color-secondary)] transition-colors hover:bg-[var(--el-fill-color-dark)]"
                @click="scrollToMessage(messages[vRow.index]!.reply_to_id!)"
              >
                <span class="font-medium">{{
                  messages[vRow.index]!.reply_to_sender_name
                }}</span>: {{ messages[vRow.index]!.reply_to_preview }}
              </div>

              <!-- 通知卡片 -->
              <div
                v-if="
                  messages[vRow.index]!.msg_type === 'text' &&
                  isNotifyCard(messages[vRow.index]!)
                "
                class="notify-card p-1.5"
                :class="{
                  'notify-card--clickable': !!(
                    messages[vRow.index]!.extra as any
                  )?.link_type,
                }"
                @click="handleNotifyClick(messages[vRow.index]!)"
              >
                <div class="notify-card__header">
                  <BellRing class="h-4 w-4 text-[var(--el-color-primary)]" />
                  <span class="notify-card__title">
                    {{
                      (messages[vRow.index]!.extra as any)?.title ||
                      $t('chat.systemNotification')
                    }}
                  </span>
                </div>
                <div class="notify-card__body">
                  {{ messages[vRow.index]!.content }}
                </div>
                <div
                  v-if="(messages[vRow.index]!.extra as any)?.link_type"
                  class="notify-card__footer"
                >
                  <span>{{ $t('chat.viewDetail') }}</span>
                  <ChevronRight class="h-3.5 w-3.5" />
                </div>
              </div>

              <!-- 消息气泡 -->
              <div
                v-else-if="messages[vRow.index]!.msg_type === 'text'"
                class="relative rounded-lg px-3 py-2 text-sm leading-relaxed"
                :class="
                  isMyMessage(messages[vRow.index]!)
                    ? 'bg-[var(--el-color-primary)] text-white'
                    : 'bg-[var(--el-fill-color-light)] text-[var(--el-text-color-primary)]'
                "
                @contextmenu="handleContextMenu($event, messages[vRow.index]!)"
              >
                <span class="whitespace-pre-wrap break-words">{{
                  messages[vRow.index]!.content
                }}</span>
              </div>

              <!-- 图片消息 -->
              <div
                v-else-if="messages[vRow.index]!.msg_type === 'image'"
                class="relative overflow-hidden rounded-lg"
                @contextmenu="handleContextMenu($event, messages[vRow.index]!)"
              >
                <template
                  v-if="
                    messages[vRow.index]!._localUrl ||
                    (messages[vRow.index]!.file_id &&
                      getImageUrl(messages[vRow.index]!.file_id!))
                  "
                >
                  <img
                    :src="
                      messages[vRow.index]!._localUrl ||
                      getImageUrl(messages[vRow.index]!.file_id!)
                    "
                    :alt="messages[vRow.index]!.file_name || $t('chat.image')"
                    class="chat-image"
                    :class="{ 'opacity-60': messages[vRow.index]!._sending }"
                    loading="lazy"
                    @click="
                      !messages[vRow.index]!._sending &&
                      handleImagePreview(messages[vRow.index]!)
                    "
                  />
                </template>
                <template v-else-if="messages[vRow.index]!.file_id">
                  <div class="chat-image-placeholder">
                    <Loader2
                      class="h-5 w-5 animate-spin text-[var(--el-text-color-placeholder)]"
                    />
                  </div>
                </template>
                <div v-else class="px-3 py-2 text-xs opacity-80">
                  [{{ $t('chat.image') }}]
                </div>
              </div>

              <!-- 文件消息：图片类型直接显示 -->
              <div
                v-else-if="
                  messages[vRow.index]!.msg_type === 'file' &&
                  isImageFile(messages[vRow.index]!)
                "
                class="relative overflow-hidden rounded-lg"
                @contextmenu="handleContextMenu($event, messages[vRow.index]!)"
              >
                <template
                  v-if="
                    messages[vRow.index]!._localUrl ||
                    (messages[vRow.index]!.file_id &&
                      getImageUrl(messages[vRow.index]!.file_id!))
                  "
                >
                  <img
                    :src="
                      messages[vRow.index]!._localUrl ||
                      getImageUrl(messages[vRow.index]!.file_id!)
                    "
                    :alt="messages[vRow.index]!.file_name || $t('chat.image')"
                    class="chat-image"
                    :class="{ 'opacity-60': messages[vRow.index]!._sending }"
                    loading="lazy"
                    @click="
                      !messages[vRow.index]!._sending &&
                      handleImagePreview(messages[vRow.index]!)
                    "
                  />
                </template>
                <template v-else-if="messages[vRow.index]!.file_id">
                  <div class="chat-image-placeholder">
                    <Loader2
                      class="h-5 w-5 animate-spin text-[var(--el-text-color-placeholder)]"
                    />
                  </div>
                </template>
              </div>

              <!-- 文件消息卡片：非图片文件 -->
              <div
                v-else-if="messages[vRow.index]!.msg_type === 'file'"
                class="chat-file-card"
                :class="{
                  'chat-file-card--sending': messages[vRow.index]!._sending,
                }"
                @contextmenu="handleContextMenu($event, messages[vRow.index]!)"
                @click="handleFilePreview(messages[vRow.index]!)"
              >
                <div class="chat-file-card__icon">
                  <img
                    :src="
                      getFileTypeIcon(
                        messages[vRow.index]!.file_ext ||
                          getExtFromName(messages[vRow.index]!.file_name),
                      )
                    "
                    class="h-9 w-9"
                  />
                </div>
                <div class="chat-file-card__info">
                  <div
                    class="chat-file-card__name"
                    :title="messages[vRow.index]!.file_name"
                  >
                    {{ messages[vRow.index]!.file_name || $t('chat.file') }}
                  </div>
                  <div class="chat-file-card__meta">
                    {{ formatFileSize(messages[vRow.index]!.file_size) }}
                  </div>
                </div>
              </div>

              <!-- 语音消息 -->
              <div
                v-else-if="messages[vRow.index]!.msg_type === 'voice'"
                class="voice-bubble cursor-pointer"
                :class="
                  isMyMessage(messages[vRow.index]!)
                    ? 'voice-bubble--mine'
                    : 'voice-bubble--other'
                "
                :style="{ width: getVoiceBubbleWidth(messages[vRow.index]!) }"
                @click="toggleVoicePlay(messages[vRow.index]!)"
                @contextmenu="handleContextMenu($event, messages[vRow.index]!)"
              >
                <div class="voice-bubble__play">
                  <Loader2
                    v-if="messages[vRow.index]!._sending"
                    class="h-4 w-4 animate-spin"
                  />
                  <Pause
                    v-else-if="playingVoiceId === messages[vRow.index]!.id"
                    class="h-4 w-4"
                  />
                  <Play v-else class="h-4 w-4" />
                </div>
                <div class="voice-bubble__waves">
                  <span
                    v-for="n in 4"
                    :key="n"
                    class="voice-wave-bar"
                    :class="{
                      'voice-wave-bar--active':
                        playingVoiceId === messages[vRow.index]!.id,
                    }"
                  ></span>
                </div>
                <span class="voice-bubble__duration">
                  {{
                    formatVoiceDuration(getVoiceDuration(messages[vRow.index]!))
                  }}
                </span>
              </div>

              <!-- 时间 / 发送中状态 -->
              <span
                v-if="messages[vRow.index]!._sending"
                class="mt-0.5 flex items-center gap-1 text-[10px] text-[var(--el-text-color-placeholder)]"
              >
                <Loader2 class="h-2.5 w-2.5 animate-spin" />
                {{ $t('chat.sending') }}
              </span>
              <span
                v-else
                class="mt-0.5 text-[10px] text-[var(--el-text-color-placeholder)]"
              >
                {{ formatTime(messages[vRow.index]!.sys_create_datetime) }}
              </span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 正在输入提示 -->
    <div
      v-if="typingText"
      class="flex items-center gap-1 px-4 py-2 text-xs text-[var(--el-text-color-placeholder)]"
    >
      <Loader2 class="h-3 w-3 animate-spin" />
      {{ typingText }}
    </div>
  </div>

  <!-- 右键菜单 -->
  <Teleport to="body">
    <Transition name="context-menu">
      <div
        v-if="contextMenu.visible && contextMenu.message"
        class="context-menu"
        :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }"
        @contextmenu.prevent
      >
        <div
          v-if="contextMenu.message.msg_type === 'text'"
          class="context-menu-item"
          @click="handleCopy(contextMenu.message!)"
        >
          <Copy class="h-4 w-4" />
          <span>{{ $t('chat.copy') }}</span>
        </div>
        <div
          class="context-menu-item"
          @click="handleReply(contextMenu.message!)"
        >
          <CornerUpLeft class="h-4 w-4" />
          <span>{{ $t('chat.replyTo') }}</span>
        </div>
        <div
          v-if="isMyMessage(contextMenu.message)"
          class="context-menu-item context-menu-item--danger"
          @click="handleRecallFromMenu(contextMenu.message!)"
        >
          <Undo2 class="h-4 w-4" />
          <span>{{ $t('chat.recall') }}</span>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 图片预览 -->
  <ElImageViewer
    v-if="previewVisible"
    :url-list="previewUrls"
    :initial-index="previewIndex"
    @close="previewVisible = false"
  />
</template>

<style scoped>
.virtual-scroll-container {
  overflow-y: auto;
  contain: strict;
}

/* Element Plus 风格滚动条：鼠标悬停时才显示 */
.virtual-scroll-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.virtual-scroll-container::-webkit-scrollbar-thumb {
  background-color: transparent;
  border-radius: 3px;
  transition: background-color 0.3s;
}

.virtual-scroll-container:hover::-webkit-scrollbar-thumb {
  background-color: var(--el-scrollbar-bg-color, rgba(144, 147, 153, 0.3));
}

.virtual-scroll-container:hover::-webkit-scrollbar-thumb:hover {
  background-color: var(
    --el-scrollbar-hover-bg-color,
    rgba(144, 147, 153, 0.5)
  );
}

.virtual-scroll-container::-webkit-scrollbar-track {
  background: transparent;
}

.virtual-list-inner {
  position: relative;
  width: 100%;
}

.virtual-item {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 0 16px;
}

.context-menu {
  position: fixed;
  z-index: 9999;
  min-width: 120px;
  padding: 4px 0;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  box-shadow: var(--el-box-shadow-light);
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: background-color 0.15s;
}

.context-menu-item:hover {
  background: var(--el-fill-color-light);
}

.context-menu-item--danger:hover {
  color: var(--el-color-danger);
  background: var(--el-color-danger-light-9);
}

.context-menu-enter-active {
  transition: all 0.15s ease-out;
}

.context-menu-leave-active {
  transition: all 0.1s ease-in;
}

.context-menu-enter-from,
.context-menu-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.reply-quote {
  border-left: 2px solid var(--el-color-primary);
}

.message-highlight {
  animation: msg-highlight 1.5s ease-out;
}

@keyframes msg-highlight {
  0%,
  30% {
    background-color: var(--el-color-primary-light-9);
    border-radius: 8px;
  }
  100% {
    background-color: transparent;
  }
}

.chat-image {
  display: block;
  min-width: 80px;
  min-height: 80px;
  max-width: 200px;
  max-height: 200px;
  border-radius: 6px;
  cursor: pointer;
  object-fit: cover;
}

.chat-image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  border-radius: 6px;
  background: var(--el-fill-color-light);
}

.chat-file-card {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 240px;
  padding: 10px 12px;
  cursor: pointer;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.06);
  transition: all 0.2s;
}

.chat-file-card:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 2px 8px rgb(0 0 0 / 0.1);
}

.chat-file-card--sending {
  opacity: 0.6;
  pointer-events: none;
}

.chat-file-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.chat-file-card__info {
  flex: 1;
  min-width: 0;
}

.chat-file-card__name {
  overflow: hidden;
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-file-card__meta {
  margin-top: 2px;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

/* ---- 语音消息气泡 ---- */
.voice-bubble {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 80px;
  padding: 8px 18px 8px 12px;
  border-radius: 12px;
  transition: opacity 0.2s;
  user-select: none;
}

.voice-bubble:active {
  opacity: 0.8;
}

.voice-bubble--mine {
  background: var(--el-color-primary);
  color: #fff;
}

.voice-bubble--other {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.voice-bubble__play {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
}

.voice-bubble--mine .voice-bubble__play {
  background: rgba(255, 255, 255, 0.2);
}

.voice-bubble--other .voice-bubble__play {
  background: var(--el-fill-color);
}

.voice-bubble__waves {
  display: flex;
  align-items: center;
  gap: 3px;
  flex: 1;
  height: 20px;
}

.voice-wave-bar {
  display: inline-block;
  width: 3px;
  border-radius: 2px;
  background: currentColor;
  opacity: 0.4;
}

.voice-wave-bar:nth-child(1) {
  height: 8px;
}
.voice-wave-bar:nth-child(2) {
  height: 14px;
}
.voice-wave-bar:nth-child(3) {
  height: 10px;
}
.voice-wave-bar:nth-child(4) {
  height: 16px;
}

.voice-wave-bar--active {
  opacity: 0.9;
  animation: voice-wave 0.8s ease-in-out infinite alternate;
}

.voice-wave-bar--active:nth-child(1) {
  animation-delay: 0s;
}
.voice-wave-bar--active:nth-child(2) {
  animation-delay: 0.15s;
}
.voice-wave-bar--active:nth-child(3) {
  animation-delay: 0.3s;
}
.voice-wave-bar--active:nth-child(4) {
  animation-delay: 0.45s;
}

@keyframes voice-wave {
  0% {
    transform: scaleY(0.5);
  }
  100% {
    transform: scaleY(1.4);
  }
}

.voice-bubble__duration {
  flex-shrink: 0;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  opacity: 0.8;
}

/* ---- 通知卡片 ---- */
.notify-card {
  width: 280px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  background: var(--el-bg-color);
  box-shadow: 0 1px 4px rgb(0 0 0 / 0.06);
}

.notify-card--clickable {
  cursor: pointer;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.notify-card--clickable:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 2px 8px rgb(0 0 0 / 0.1);
}

.notify-card__header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px 0;
}

.notify-card__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.notify-card__body {
  padding: 8px 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.notify-card__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
  padding: 0 12px 10px;
  font-size: 12px;
  color: var(--el-color-primary);
}
</style>
