<script lang="ts" setup>
import type { ChatMessage } from '#/api/core/chat';

import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';

import { AuthenticationLoginExpiredModal } from '@vben/common-ui';
import { useWatermark } from '@vben/hooks';
import { BookOpen } from '@vben/icons';
import { BasicLayout, LockScreen, UserDropdown } from '@vben/layouts';
import { $t } from '@vben/locales';
import { preferences } from '@vben/preferences';
import { useAccessStore, useUserStore } from '@vben/stores';
import { openWindow } from '@vben/utils';

import { ElTooltip } from 'element-plus';

import NotificationPopup from '#/components/notification/NotificationPopup.vue';
import { getFileUrl } from '#/composables/useFileUrl';
import { useNotification } from '#/composables/useNotification';
import { useAuthStore } from '#/store';
import LoginForm from '#/views/_core/authentication/login.vue';
import { useChat } from '#/views/_core/chat/composables/useChat';

// 使用消息通知 composable
const {
  notifications,
  messageUnreadCount,
  announcements,
  announcementUnreadCount,
  activeTab,
  showDot,
  markAsRead,
  markAnnouncementAsRead,
  markAllAsRead,
  clearReadMessages,
  viewAllMessages,
  init: initNotification,
  cleanup: cleanupNotification,
} = useNotification();

const userStore = useUserStore();
const authStore = useAuthStore();
const accessStore = useAccessStore();
const { destroyWatermark, updateWatermark } = useWatermark();

// 初始化消息通知
const router = useRouter();
const {
  connectChat,
  disconnectChat,
  loadConversations,
  loadUnreadChatMessages,
  unreadChatMessages,
  totalUnread: chatTotalUnread,
} = useChat();

onMounted(() => {
  initNotification();
  // 全局初始化聊天 WebSocket，确保任何页面都能收到消息通知
  connectChat();
  loadConversations();
  loadUnreadChatMessages();
});

onUnmounted(() => {
  cleanupNotification();
  disconnectChat();
});

const menus = computed(() => [
  // {
  //   handler: () => {
  //     openWindow(VBEN_DOC_URL, {
  //       target: '_blank',
  //     });
  //   },
  //   icon: BookOpenText,
  //   text: $t('ui.widgets.document'),
  // },
  // {
  //   handler: () => {
  //     openWindow(VBEN_GITHUB_URL, {
  //       target: '_blank',
  //     });
  //   },
  //   icon: SvgGithubIcon,
  //   text: 'GitHub',
  // },
  // {
  //   handler: () => {
  //     openWindow(`${VBEN_GITHUB_URL}/issues`, {
  //       target: '_blank',
  //     });
  //   },
  //   icon: CircleHelp,
  //   text: $t('ui.widgets.qa'),
  // },
]);

const ZQ_PLATFORM_GITHUB_URL = 'https://github.com/jiangzhikj/zq-platform';
const ZQ_PLATFORM_OFFICIAL_URL = 'https://zq-platform.com/';
/** 双列仅第一列窄条展示时的短文案 */
const ZQ_PLATFORM_BRAND_SHORT = 'ZQ Platform';

function handleOpenZqOfficialSite() {
  openWindow(ZQ_PLATFORM_OFFICIAL_URL, { target: '_blank' });
}

// 头像URL（响应式）
const avatar = ref('');

// 异步加载头像URL
async function loadAvatarUrl() {
  const avatarPath = userStore.userInfo?.avatar;
  avatar.value = avatarPath ? await getFileUrl(avatarPath) : '';
}

// 监听用户信息变化，加载头像URL
watch(
  () => userStore.userInfo?.avatar,
  () => {
    loadAvatarUrl();
  },
  { immediate: true },
);

function handleOpenWiki() {
  const url = router.resolve('/wiki').href;
  window.open(url, '_blank');
}

async function handleLogout() {
  await authStore.logout(false);
}

function handleNoticeClear() {
  clearReadMessages();
}

function handleMakeAll() {
  markAllAsRead();
}

function handleNoticeRead(item: any) {
  markAsRead(item);
}

function handleAnnouncementRead(item: any) {
  markAnnouncementAsRead(item);
}

function handleViewAll() {
  viewAllMessages();
}

function handleTabChange(tab: 'announcement' | 'chat' | 'message') {
  activeTab.value = tab;
}

function handleChatClick(msg: ChatMessage) {
  // 新开tab跳转到聊天页面，带上会话ID
  const url = router.resolve(
    `/chat?conversationId=${msg.conversation_id}`,
  ).href;
  window.open(url, '_blank');

  // 从未读聊天列表中移除
  const index = unreadChatMessages.value.findIndex((m) => m.id === msg.id);
  if (index !== -1) {
    unreadChatMessages.value.splice(index, 1);
  }
}
watch(
  () => ({
    enable: preferences.app.watermark,
    content: preferences.app.watermarkContent,
  }),
  async ({ enable, content }) => {
    if (enable) {
      await updateWatermark({
        content:
          content ||
          `${userStore.userInfo?.username} - ${userStore.userInfo?.realName}`,
      });
    } else {
      destroyWatermark();
    }
  },
  {
    immediate: true,
  },
);
</script>

<template>
  <BasicLayout @clear-preferences-and-logout="handleLogout">
    <template #user-dropdown>
      <UserDropdown
        :avatar
        :menus
        :text="userStore.userInfo?.realName"
        :description="
          userStore.userInfo?.email || userStore.userInfo?.username || ''
        "
        tag-text="Pro"
        @logout="handleLogout"
      />
    </template>
    <template #header-right-55>
      <ElTooltip :content="$t('wiki.title')" placement="bottom">
        <div
          class="flex-center mr-2 cursor-pointer"
          @click="handleOpenWiki"
        >
          <BookOpen
            class="size-4 text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
          />
        </div>
      </ElTooltip>
    </template>
    <template #notification>
      <NotificationPopup
        :dot="showDot || chatTotalUnread > 0"
        :notifications="notifications"
        :message-unread-count="messageUnreadCount"
        :announcements="announcements"
        :announcement-unread-count="announcementUnreadCount"
        :unread-chats="unreadChatMessages"
        :chat-unread-count="chatTotalUnread"
        :active-tab="activeTab"
        @clear="handleNoticeClear"
        @click-chat="handleChatClick"
        @make-all="handleMakeAll"
        @read-message="handleNoticeRead"
        @read-announcement="handleAnnouncementRead"
        @view-all="handleViewAll"
        @update:active-tab="handleTabChange"
      />
    </template>
    <template #sidebar-footer="sidebarFooterProps">
      <button
        type="button"
        class="text-muted-foreground hover:text-foreground max-w-full px-1 py-0.5 text-center text-[11px] leading-tight transition-colors"
        :title="
          sidebarFooterProps?.compact
            ? ZQ_PLATFORM_BRAND_SHORT
            : $t('ui.layout.poweredBy')
        "
        @click="handleOpenZqOfficialSite"
      >
        <span
          v-show="sidebarFooterProps?.compact || !preferences.sidebar.collapsed"
          class="truncate"
          >{{
            sidebarFooterProps?.compact
              ? ZQ_PLATFORM_BRAND_SHORT
              : $t('ui.layout.poweredBy')
          }}</span>
      </button>
    </template>
    <template #extra>
      <AuthenticationLoginExpiredModal
        v-model:open="accessStore.loginExpired"
        :avatar
      >
        <LoginForm />
      </AuthenticationLoginExpiredModal>
    </template>
    <template #lock-screen>
      <LockScreen :avatar @to-login="handleLogout" />
    </template>
  </BasicLayout>
</template>
