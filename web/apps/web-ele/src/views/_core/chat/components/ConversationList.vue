<script setup lang="ts">
import type { Conversation } from '#/api/core/chat';

import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

import { BellOff, Eye, Pin, PinOff, Search, Trash2, Users } from '@vben/icons';
import { $t } from '@vben/locales';

import dayjs from 'dayjs';
import {
  ElBadge,
  ElEmpty,
  ElInput,
  ElScrollbar,
  ElSkeletonItem,
} from 'element-plus';

import UserAvatar from '#/components/user-avatar/index.vue';

const props = defineProps<{
  conversations: Conversation[];
  currentId?: string;
  loading?: boolean;
  onlineUsers?: Set<string>;
}>();

const emit = defineEmits<{
  delete: [conv: Conversation];
  markUnread: [conv: Conversation];
  select: [conv: Conversation];
  toggleMute: [conv: Conversation, value: boolean];
  togglePin: [conv: Conversation, value: boolean];
}>();

const searchKeyword = ref('');

const filteredConversations = computed(() => {
  let list = [...props.conversations];
  const kw = searchKeyword.value.trim().toLowerCase();
  if (kw) {
    list = list.filter((c) => getDisplayName(c).toLowerCase().includes(kw));
  }
  list.sort((a, b) => {
    if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1;
    const ta = a.last_message_time || a.sys_create_datetime || '';
    const tb = b.last_message_time || b.sys_create_datetime || '';
    return tb.localeCompare(ta);
  });
  return list;
});

function getDisplayName(conv: Conversation): string {
  if (conv.type === 'private') {
    return conv.peer_user_name || $t('chat.private');
  }
  return conv.name || $t('chat.group');
}

function getAvatar(conv: Conversation): string | undefined {
  if (conv.type === 'private') {
    return conv.peer_user_avatar || undefined;
  }
  return conv.avatar || undefined;
}

function formatTime(time?: string): string {
  if (!time) return '';
  const d = dayjs(time);
  const now = dayjs();
  if (d.isSame(now, 'day')) return d.format('HH:mm');
  if (d.isSame(now.subtract(1, 'day'), 'day')) return $t('chat.yesterday');
  if (d.isSame(now, 'year')) return d.format('MM/DD');
  return d.format('YYYY/MM/DD');
}

// ---- 右键菜单 ----
const contextMenu = ref<{
  conversation: Conversation | null;
  visible: boolean;
  x: number;
  y: number;
}>({
  visible: false,
  x: 0,
  y: 0,
  conversation: null,
});

function handleContextMenu(e: MouseEvent, conv: Conversation) {
  e.preventDefault();
  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    conversation: conv,
  };
}

function closeContextMenu() {
  contextMenu.value.visible = false;
  contextMenu.value.conversation = null;
}

function onDocumentClick() {
  if (contextMenu.value.visible) {
    closeContextMenu();
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick);
});
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 搜索 -->
    <div class="shrink-0 px-3 pb-2 pt-3">
      <ElInput
        v-model="searchKeyword"
        :placeholder="$t('chat.search')"
        clearable
        size="small"
      >
        <template #prefix>
          <Search class="h-3.5 w-3.5 text-[var(--el-text-color-placeholder)]" />
        </template>
      </ElInput>
    </div>

    <!-- 列表 -->
    <ElScrollbar class="flex-1">
      <!-- 骨架屏 -->
      <template v-if="loading">
        <div
          v-for="i in 6"
          :key="i"
          class="flex items-center gap-3 px-3 py-2.5"
        >
          <ElSkeletonItem variant="circle" style="width: 40px; height: 40px" />
          <div class="flex-1">
            <ElSkeletonItem variant="text" style="width: 60%" />
            <ElSkeletonItem
              variant="text"
              style="width: 80%; margin-top: 6px"
            />
          </div>
        </div>
      </template>

      <!-- 空状态 -->
      <ElEmpty
        v-else-if="filteredConversations.length === 0"
        :description="$t('chat.noConversations')"
        :image-size="80"
        class="mt-10"
      />

      <!-- 会话列表 -->
      <template v-else>
        <div
          v-for="conv in filteredConversations"
          :key="conv.id"
          class="group flex cursor-pointer items-center gap-3 px-3 py-2.5 transition-colors hover:bg-[var(--el-fill-color-light)]"
          :class="{
            'bg-[var(--el-color-primary-light-9)]': currentId === conv.id,
          }"
          @click="emit('select', conv)"
          @contextmenu="handleContextMenu($event, conv)"
        >
          <!-- 头像 -->
          <div
            v-if="conv.type === 'private' && conv.peer_user_id"
            class="relative shrink-0"
          >
            <UserAvatar
              :user-id="conv.peer_user_id"
              :name="conv.peer_user_name"
              :avatar="conv.peer_user_avatar"
              :size="40"
              :font-size="16"
              :shadow="false"
              :show-popover="true"
            />
            <span
              class="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-[var(--el-bg-color)]"
              :class="
                props.onlineUsers?.has(conv.peer_user_id)
                  ? 'bg-[var(--el-color-success)]'
                  : 'bg-[var(--el-text-color-placeholder)]'
              "
            ></span>
          </div>
          <div
            v-else
            class="flex shrink-0 items-center justify-center rounded-full bg-[var(--el-color-primary-light-7)] text-white"
            :style="{ width: '40px', height: '40px' }"
          >
            <Users class="h-5 w-5" />
          </div>

          <!-- 信息 -->
          <div class="min-w-0 flex-1">
            <div class="flex items-center justify-between">
              <span
                class="truncate text-sm font-medium text-[var(--el-text-color-primary)]"
              >
                {{ getDisplayName(conv) }}
              </span>
              <span
                class="ml-2 shrink-0 text-xs text-[var(--el-text-color-placeholder)]"
              >
                {{ formatTime(conv.last_message_time) }}
              </span>
            </div>
            <div class="mt-0.5 flex items-center justify-between gap-1">
              <div class="flex min-w-0 items-center gap-1">
                <Pin
                  v-if="conv.is_pinned"
                  class="h-3 w-3 shrink-0 text-[var(--el-color-primary)]"
                />
                <span
                  class="truncate text-xs text-[var(--el-text-color-secondary)]"
                >
                  {{ conv.last_message_preview || '' }}
                </span>
              </div>
              <div class="flex shrink-0 items-center gap-1">
                <BellOff
                  v-if="conv.is_muted"
                  class="h-3 w-3 text-[var(--el-text-color-placeholder)]"
                />
                <ElBadge
                  v-if="conv.unread_count > 0"
                  :value="conv.unread_count"
                  :max="99"
                />
              </div>
            </div>
          </div>
        </div>
      </template>
    </ElScrollbar>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <Transition name="ctx-menu">
        <div
          v-if="contextMenu.visible && contextMenu.conversation"
          class="conv-context-menu"
          :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }"
          @contextmenu.prevent
        >
          <!-- 置顶/取消置顶 -->
          <div
            class="conv-context-menu-item"
            @click="
              emit(
                'togglePin',
                contextMenu.conversation!,
                !contextMenu.conversation!.is_pinned,
              );
              closeContextMenu();
            "
          >
            <PinOff
              v-if="contextMenu.conversation!.is_pinned"
              class="h-4 w-4"
            />
            <Pin v-else class="h-4 w-4" />
            <span>{{
              contextMenu.conversation!.is_pinned
                ? $t('chat.unpin')
                : $t('chat.pin')
            }}</span>
          </div>
          <!-- 标记未读 -->
          <div
            class="conv-context-menu-item"
            @click="
              emit('markUnread', contextMenu.conversation!);
              closeContextMenu();
            "
          >
            <Eye class="h-4 w-4" />
            <span>{{ $t('chat.markUnread') }}</span>
          </div>
          <!-- 免打扰/取消免打扰 -->
          <div
            class="conv-context-menu-item"
            @click="
              emit(
                'toggleMute',
                contextMenu.conversation!,
                !contextMenu.conversation!.is_muted,
              );
              closeContextMenu();
            "
          >
            <BellOff class="h-4 w-4" />
            <span>{{
              contextMenu.conversation!.is_muted
                ? $t('chat.unmute')
                : $t('chat.mute')
            }}</span>
          </div>
          <!-- 删除记录 -->
          <div
            class="conv-context-menu-item conv-context-menu-item--danger"
            @click="
              emit('delete', contextMenu.conversation!);
              closeContextMenu();
            "
          >
            <Trash2 class="h-4 w-4" />
            <span>{{ $t('chat.deleteConversation') }}</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.conv-context-menu {
  position: fixed;
  z-index: 9999;
  min-width: 140px;
  padding: 4px 0;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  box-shadow: var(--el-box-shadow-light);
}

.conv-context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: background-color 0.15s;
}

.conv-context-menu-item:hover {
  background: var(--el-fill-color-light);
}

.conv-context-menu-item--danger:hover {
  color: var(--el-color-danger);
  background: var(--el-color-danger-light-9);
}

.ctx-menu-enter-active {
  transition: all 0.15s ease-out;
}

.ctx-menu-leave-active {
  transition: all 0.1s ease-in;
}

.ctx-menu-enter-from,
.ctx-menu-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
