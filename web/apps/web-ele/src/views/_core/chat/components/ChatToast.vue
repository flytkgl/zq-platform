<script setup lang="ts">
import { X } from '@vben/icons';

import UserAvatar from '#/components/user-avatar/index.vue';

defineProps<{
  content: string;
  senderAvatar?: string;
  senderId?: string;
  senderName: string;
}>();

const emit = defineEmits<{
  click: [];
  close: [];
}>();
</script>

<template>
  <div class="chat-toast" @click="emit('click')">
    <UserAvatar
      :user-id="senderId"
      :name="senderName"
      :avatar="senderAvatar"
      :size="40"
      :font-size="16"
      :show-popover="false"
      class="shrink-0"
    />
    <div class="chat-toast-body">
      <div class="chat-toast-sender">{{ senderName }}</div>
      <div class="chat-toast-content">{{ content }}</div>
    </div>
    <button class="chat-toast-close" @click.stop="emit('close')">
      <X class="h-3.5 w-3.5" />
    </button>
  </div>
</template>

<style>
.chat-toast {
  display: flex;
  gap: 10px;
  align-items: center;
  width: 320px;
  padding: 12px 14px;
  border-radius: 12px;
  cursor: pointer;
  color: var(--el-text-color-primary);
  background: var(--el-bg-color-overlay);
  box-shadow:
    0 4px 12px rgb(0 0 0 / 8%),
    0 1px 3px rgb(0 0 0 / 12%);
  backdrop-filter: blur(12px);
  animation: chat-toast-enter 0.3s ease;
  transition: transform 0.2s ease;
}

.chat-toast:hover {
  transform: translateX(-4px);
}

.chat-toast-body {
  flex: 1;
  min-width: 0;
}

.chat-toast-sender {
  overflow: hidden;
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
}

.chat-toast-content {
  overflow: hidden;
  margin-top: 2px;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-secondary);
}

.chat-toast-close {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--el-text-color-placeholder);
  background: transparent;
  opacity: 0;
  transition: all 0.2s;
}

.chat-toast:hover .chat-toast-close {
  opacity: 1;
}

.chat-toast-close:hover {
  color: var(--el-text-color-primary);
  background: var(--el-fill-color-light);
}

@keyframes chat-toast-enter {
  from {
    opacity: 0;
    transform: translateX(100%);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>

<style>
.chat-toast-exit .chat-toast {
  opacity: 0;
  transform: translateX(100%);
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
}
</style>
