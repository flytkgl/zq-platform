<script setup lang="ts">
import type { Conversation, ConversationMember } from '#/api/core/chat';

import { computed } from 'vue';

import { BellOff, Pin, PinOff, Trash2, UserPlus, Users } from '@vben/icons';
import { $t } from '@vben/locales';
import { useUserStore } from '@vben/stores';

import {
  ElButton,
  ElDivider,
  ElMessageBox,
  ElScrollbar,
  ElTag,
} from 'element-plus';

import UserAvatar from '#/components/user-avatar/index.vue';

const props = defineProps<{
  conversation: Conversation | null;
  loading?: boolean;
  members: ConversationMember[];
  onlineUsers?: Set<string>;
}>();

const emit = defineEmits<{
  addMember: [];
  dissolve: [];
  removeMember: [userId: string];
  toggleMute: [value: boolean];
  togglePin: [value: boolean];
}>();

const userStore = useUserStore();
const currentUserId = userStore.userInfo?.userId || '';

const isOwner = computed(() => {
  return props.conversation?.owner_id === currentUserId;
});

const isGroup = computed(() => {
  return props.conversation?.type === 'group';
});

function getRoleLabel(role: string): string {
  if (role === 'owner') return $t('chat.owner');
  if (role === 'admin') return $t('chat.admin');
  return '';
}

async function handleRemoveMember(userId: string) {
  try {
    await ElMessageBox.confirm($t('chat.removeMemberConfirm'), {
      type: 'warning',
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
    });
    emit('removeMember', userId);
  } catch {
    // cancelled
  }
}

async function handleDissolve() {
  try {
    await ElMessageBox.confirm($t('chat.dissolveGroupConfirm'), {
      type: 'warning',
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
    });
    emit('dissolve');
  } catch {
    // cancelled
  }
}
</script>

<template>
  <div v-if="conversation" class="flex h-full flex-col">
    <!-- 标题 -->
    <div
      class="shrink-0 border-b border-[var(--el-border-color-lighter)] px-4 py-3"
    >
      <h3 class="text-sm font-medium text-[var(--el-text-color-primary)]">
        {{ $t('chat.conversationInfo') }}
      </h3>
    </div>

    <ElScrollbar class="flex-1">
      <div class="p-4">
        <!-- 会话设置 -->
        <div class="mb-4 flex flex-col gap-2">
          <ElButton
            text
            class="!justify-start"
            @click="emit('togglePin', !conversation.is_pinned)"
          >
            <Pin v-if="!conversation.is_pinned" class="mr-2 h-4 w-4" />
            <PinOff v-else class="mr-2 h-4 w-4" />
            {{ conversation.is_pinned ? $t('chat.unpin') : $t('chat.pin') }}
          </ElButton>
          <ElButton
            text
            class="!justify-start"
            @click="emit('toggleMute', !conversation.is_muted)"
          >
            <BellOff class="mr-2 h-4 w-4" />
            {{ conversation.is_muted ? $t('chat.unmute') : $t('chat.mute') }}
          </ElButton>
        </div>

        <ElDivider />

        <!-- 成员列表 -->
        <div v-if="isGroup" class="mb-4">
          <div class="mb-2 flex items-center justify-between">
            <span
              class="text-sm font-medium text-[var(--el-text-color-primary)]"
            >
              <Users class="mr-1 inline h-4 w-4" />
              {{ $t('chat.members') }} ({{ members.length }})
            </span>
            <ElButton
              v-if="isOwner"
              text
              size="small"
              @click="emit('addMember')"
            >
              <UserPlus class="h-4 w-4" />
            </ElButton>
          </div>

          <div class="flex flex-col gap-1">
            <div
              v-for="m in members"
              :key="m.id"
              class="group flex items-center gap-2 rounded px-2 py-1.5 hover:bg-[var(--el-fill-color-light)]"
            >
              <div class="relative shrink-0">
                <UserAvatar
                  :user-id="m.user_id"
                  :name="m.user_name"
                  :avatar="m.user_avatar"
                  :size="28"
                  :font-size="12"
                  :shadow="false"
                  :show-popover="true"
                />
                <span
                  class="absolute bottom-0 right-0 h-2 w-2 rounded-full border-[1.5px] border-[var(--el-bg-color)]"
                  :class="
                    props.onlineUsers?.has(m.user_id)
                      ? 'bg-[var(--el-color-success)]'
                      : 'bg-[var(--el-text-color-placeholder)]'
                  "
                ></span>
              </div>
              <span
                class="flex-1 truncate text-sm text-[var(--el-text-color-primary)]"
              >
                {{ m.user_name || m.user_id }}
              </span>
              <ElTag v-if="getRoleLabel(m.role)" size="small" type="warning">
                {{ getRoleLabel(m.role) }}
              </ElTag>
              <Trash2
                v-if="isOwner && m.user_id !== currentUserId"
                class="h-3.5 w-3.5 shrink-0 cursor-pointer text-[var(--el-text-color-placeholder)] opacity-0 transition-opacity hover:text-[var(--el-color-danger)] group-hover:opacity-100"
                @click="handleRemoveMember(m.user_id)"
              />
            </div>
          </div>
        </div>

        <!-- 解散群聊 -->
        <div v-if="isGroup && isOwner">
          <ElDivider />
          <ElButton
            type="danger"
            text
            class="w-full !justify-start"
            @click="handleDissolve"
          >
            <Trash2 class="mr-2 h-4 w-4" />
            {{ $t('chat.dissolveGroup') }}
          </ElButton>
        </div>
      </div>
    </ElScrollbar>
  </div>
</template>
