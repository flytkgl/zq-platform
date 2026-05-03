<script lang="ts" setup>
import type { ChatMessage } from '#/api/core/chat';
import type {
  AnnouncementItem,
  NotificationItem,
} from '#/composables/useNotification';

import { computed, ref } from 'vue';

import { useVbenDrawer } from '@vben/common-ui';
import { Mail, MailCheck, Megaphone, MessageSquare, Trash2 } from '@vben/icons';

import { ElButton, ElEmpty, ElScrollbar, ElTooltip } from 'element-plus';

import UserAvatar from '#/components/user-avatar/index.vue';
import { ZqTabs } from '#/components/zq-tabs';
import { $t } from '#/locales';

interface Props {
  // 消息列表
  notifications?: NotificationItem[];
  // 消息未读数
  messageUnreadCount?: number;
  // 公告列表
  announcements?: AnnouncementItem[];
  // 公告未读数
  announcementUnreadCount?: number;
  // 未读聊天消息列表
  unreadChats?: ChatMessage[];
  // 聊天未读总数
  chatUnreadCount?: number;
  // 当前激活的 Tab
  activeTab?: 'announcement' | 'chat' | 'message';
}

defineOptions({ name: 'NotificationDrawer' });

const props = withDefaults(defineProps<Props>(), {
  notifications: () => [],
  messageUnreadCount: 0,
  announcements: () => [],
  announcementUnreadCount: 0,
  unreadChats: () => [],
  chatUnreadCount: 0,
  activeTab: 'message',
});

const emit = defineEmits<{
  clear: [];
  clickChat: [ChatMessage];
  makeAll: [];
  readAnnouncement: [AnnouncementItem];
  readMessage: [NotificationItem];
  'update:activeTab': ['announcement' | 'chat' | 'message'];
  viewAll: [];
}>();

const [Drawer] = useVbenDrawer();

const currentTab = ref(props.activeTab);

const tabItems = computed(() => [
  {
    key: 'message',
    label: `${$t('message.drawer.messageTab')}${props.messageUnreadCount > 0 ? ` (${props.messageUnreadCount})` : ''}`,
    icon: Mail,
  },
  {
    key: 'chat',
    label: `${$t('message.drawer.chatTab')}${props.chatUnreadCount > 0 ? ` (${props.chatUnreadCount})` : ''}`,
    icon: MessageSquare,
  },
  {
    key: 'announcement',
    label: `${$t('message.drawer.announcementTab')}${props.announcementUnreadCount > 0 ? ` (${props.announcementUnreadCount})` : ''}`,
    icon: Megaphone,
  },
]);

function handleTabChange(value: string) {
  currentTab.value = value as 'announcement' | 'chat' | 'message';
  emit('update:activeTab', currentTab.value);
}

function handleChatClick(msg: ChatMessage) {
  emit('clickChat', msg);
}

function getMessagePreview(msg: ChatMessage): string {
  if (msg.msg_type === 'text') return msg.content || '';
  if (msg.msg_type === 'image') return `[${$t('chat.image')}]`;
  if (msg.msg_type === 'file')
    return `[${$t('chat.file')}] ${msg.file_name || ''}`;
  if (msg.msg_type === 'voice') return `[${$t('chat.voice')}]`;
  return `[${msg.msg_type}]`;
}

function formatChatTime(datetime?: string): string {
  if (!datetime) return '';
  const date = new Date(datetime);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  if (isToday) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return date.toLocaleDateString([], { month: '2-digit', day: '2-digit' });
}

function handleViewAll() {
  emit('viewAll');
}

function handleMakeAll() {
  emit('makeAll');
}

function handleClear() {
  emit('clear');
}

function handleMessageClick(item: NotificationItem) {
  emit('readMessage', item);
}

function handleAnnouncementClick(item: AnnouncementItem) {
  emit('readAnnouncement', item);
}

// 优先级样式
function getPriorityClass(priority: number): string {
  if (priority === 2) return 'border-l-4 border-l-red-500';
  if (priority === 1) return 'border-l-4 border-l-orange-500';
  return '';
}
</script>

<template>
  <div>
    <Drawer
      :title="$t('message.drawer.title')"
      class="sm:max-w-md"
      :footer="false"
    >
      <template #extra>
        <div v-if="currentTab === 'message'" class="flex items-center gap-2">
          <ElTooltip
            :content="$t('message.drawer.markAllRead')"
            placement="bottom"
          >
            <ElButton
              :disabled="notifications.length <= 0"
              link
              @click="handleMakeAll"
            >
              <MailCheck class="size-4" />
            </ElButton>
          </ElTooltip>
          <ElTooltip
            :content="$t('message.drawer.clearRead')"
            placement="bottom"
          >
            <ElButton
              :disabled="notifications.length <= 0"
              link
              @click="handleClear"
            >
              <Trash2 class="size-4" />
            </ElButton>
          </ElTooltip>
        </div>
      </template>

      <div class="flex h-full flex-col">
        <!-- Tab 切换 -->
        <ZqTabs
          v-model="currentTab"
          :items="tabItems"
          class="mb-4"
          @change="handleTabChange"
        />

        <!-- 消息列表 -->
        <template v-if="currentTab === 'message'">
          <ElScrollbar v-if="notifications.length > 0" class="flex-1">
            <ul class="flex w-full flex-col gap-2">
              <template v-for="item in notifications" :key="item.id">
                <li
                  class="relative flex w-full cursor-pointer items-start gap-3 rounded-lg border border-[var(--el-border-color)] p-3 transition-colors hover:bg-[var(--el-fill-color-light)]"
                  @click="handleMessageClick(item)"
                >
                  <span
                    v-if="!item.isRead"
                    class="absolute right-2 top-2 h-2 w-2 rounded-full bg-[var(--el-color-danger)]"
                  ></span>

                  <UserAvatar
                    v-if="item.senderId"
                    :user-id="item.senderId"
                    :name="item.senderName || item.title"
                    :size="40"
                    :font-size="16"
                    :show-popover="false"
                    class="shrink-0"
                  />
                  <span
                    v-else
                    class="relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full"
                  >
                    <img
                      :src="item.avatar"
                      class="aspect-square h-full w-full object-cover"
                    />
                  </span>
                  <div class="flex flex-1 flex-col gap-1 leading-none">
                    <p class="text-sm font-medium">{{ item.title }}</p>
                    <p
                      class="line-clamp-2 text-xs text-[var(--el-text-color-secondary)]"
                    >
                      {{ item.message }}
                    </p>
                    <p class="text-xs text-[var(--el-text-color-placeholder)]">
                      {{ item.date }}
                    </p>
                  </div>
                </li>
              </template>
            </ul>
          </ElScrollbar>

          <template v-else>
            <div class="flex flex-1 items-center justify-center">
              <ElEmpty :description="$t('message.drawer.noMessages')">
                <template #image>
                  <Mail
                    class="size-16 text-[var(--el-text-color-placeholder)]"
                  />
                </template>
              </ElEmpty>
            </div>
          </template>
        </template>

        <!-- 聊天未读列表 -->
        <template v-else-if="currentTab === 'chat'">
          <ElScrollbar v-if="unreadChats.length > 0" class="flex-1">
            <ul class="flex w-full flex-col gap-2">
              <template v-for="msg in unreadChats" :key="msg.id">
                <li
                  class="relative flex w-full cursor-pointer items-center gap-3 rounded-lg border border-[var(--el-border-color)] p-3 transition-colors hover:bg-[var(--el-fill-color-light)]"
                  @click="handleChatClick(msg)"
                >
                  <UserAvatar
                    :user-id="msg.sender_id"
                    :name="msg.sender_name || ''"
                    :avatar="msg.sender_avatar"
                    :size="40"
                    :font-size="16"
                    :show-popover="false"
                    class="shrink-0"
                  />
                  <div class="flex flex-1 flex-col gap-1 leading-none">
                    <div class="flex items-center justify-between">
                      <p class="text-sm font-medium">
                        {{ msg.sender_name || '' }}
                      </p>
                      <span
                        class="text-xs text-[var(--el-text-color-placeholder)]"
                      >
                        {{ formatChatTime(msg.sys_create_datetime) }}
                      </span>
                    </div>
                    <p
                      class="truncate text-xs text-[var(--el-text-color-secondary)]"
                    >
                      {{ getMessagePreview(msg) }}
                    </p>
                  </div>
                </li>
              </template>
            </ul>
          </ElScrollbar>

          <template v-else>
            <div class="flex flex-1 items-center justify-center">
              <ElEmpty :description="$t('message.drawer.noChats')">
                <template #image>
                  <MessageSquare
                    class="size-16 text-[var(--el-text-color-placeholder)]"
                  />
                </template>
              </ElEmpty>
            </div>
          </template>
        </template>

        <!-- 公告列表 -->
        <template v-else>
          <ElScrollbar v-if="announcements.length > 0" class="flex-1">
            <ul class="flex w-full flex-col gap-2">
              <template v-for="item in announcements" :key="item.id">
                <li
                  class="relative flex w-full cursor-pointer flex-col gap-2 rounded-lg border border-[var(--el-border-color)] p-3 transition-colors hover:bg-[var(--el-fill-color-light)]"
                  :class="getPriorityClass(item.priority)"
                  @click="handleAnnouncementClick(item)"
                >
                  <span
                    v-if="!item.isRead"
                    class="absolute right-2 top-2 h-2 w-2 rounded-full bg-[var(--el-color-danger)]"
                  ></span>

                  <div class="flex items-center gap-2">
                    <span
                      v-if="item.isTop"
                      class="rounded bg-[var(--el-color-danger)] px-1.5 py-0.5 text-xs text-white"
                    >
                      {{ $t('message.drawer.pinned') }}
                    </span>
                    <span
                      v-if="item.priority === 2"
                      class="rounded bg-[var(--el-color-danger)] px-1.5 py-0.5 text-xs text-white"
                    >
                      {{ $t('message.drawer.urgent') }}
                    </span>
                    <span
                      v-else-if="item.priority === 1"
                      class="rounded bg-[var(--el-color-warning)] px-1.5 py-0.5 text-xs text-white"
                    >
                      {{ $t('message.drawer.important') }}
                    </span>
                    <p class="flex-1 truncate text-sm font-medium">
                      {{ item.title }}
                    </p>
                  </div>
                  <p
                    class="line-clamp-2 text-xs text-[var(--el-text-color-secondary)]"
                  >
                    {{ item.summary || item.content }}
                  </p>
                  <div
                    class="flex items-center justify-between text-xs text-[var(--el-text-color-placeholder)]"
                  >
                    <span>{{ item.publisherName }}</span>
                    <span>{{ item.date }}</span>
                  </div>
                </li>
              </template>
            </ul>
          </ElScrollbar>

          <template v-else>
            <div class="flex flex-1 items-center justify-center">
              <ElEmpty :description="$t('message.drawer.noAnnouncements')">
                <template #image>
                  <Megaphone
                    class="size-16 text-[var(--el-text-color-placeholder)]"
                  />
                </template>
              </ElEmpty>
            </div>
          </template>
        </template>

        <!-- 底部操作 -->
        <!-- <div class="mt-4 flex justify-center border-t border-[var(--el-border-color)] pt-4">
          <ElButton type="primary" @click="handleViewAll">
            查看全部
          </ElButton>
        </div> -->
      </div>
    </Drawer>
  </div>
</template>
