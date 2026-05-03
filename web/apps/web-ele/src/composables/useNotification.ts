import type { WebSocketManager } from '#/api/core/websocket';

/**
 * 消息通知 Composable
 * 集成 WebSocket 实时推送、消息和公告 API
 */
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';

import { useAccessStore } from '@vben/stores';

import {
  getUnreadAnnouncementCountApi,
  getUserAnnouncementListApi,
  markAnnouncementReadApi,
} from '#/api/core/announcement';
import {
  clearReadMessagesApi,
  getMessageListApi,
  getUnreadCountApi,
  markAllAsReadApi,
  markAsReadApi,
} from '#/api/core/message';
import { createNotificationWebSocket } from '#/api/core/websocket';
import { $t } from '#/locales';

// 通知项类型
export interface NotificationItem {
  id: string;
  avatar: string;
  title: string;
  message: string;
  date: string;
  isRead: boolean;
  linkType?: string;
  linkId?: string;
  priority?: number;
  isTop?: boolean;
  senderId?: string;
  senderName?: string;
}

// 公告项类型
export interface AnnouncementItem {
  id: string;
  title: string;
  summary: string;
  content: string;
  date: string;
  isRead: boolean;
  priority: number;
  isTop: boolean;
  publisherName: string;
}

// WebSocket 连接状态
const wsConnected = ref(false);
let wsManagerInstance: null | WebSocketManager = null;

// 消息数据
const notifications = ref<NotificationItem[]>([]);
const messageUnreadCount = ref(0);
const unreadByType = ref<Record<string, number>>({});

// 公告数据
const announcements = ref<AnnouncementItem[]>([]);
const announcementUnreadCount = ref(0);

// 当前激活的 Tab
const activeTab = ref<'announcement' | 'chat' | 'message'>('message');

// 消息类型图标映射
const typeAvatarMap: Record<string, string> = {
  system: 'https://avatar.vercel.sh/system?text=SYS',
  workflow: 'https://avatar.vercel.sh/workflow?text=WF',
  todo: 'https://avatar.vercel.sh/todo?text=TD',
  announcement: 'https://avatar.vercel.sh/announcement?text=AN',
};

export function useNotification() {
  const router = useRouter();
  const accessStore = useAccessStore();

  // 总未读数量
  const totalUnreadCount = computed(
    () => messageUnreadCount.value + announcementUnreadCount.value,
  );

  // 是否显示红点
  const showDot = computed(() => totalUnreadCount.value > 0);

  // 加载消息列表
  async function loadMessages() {
    try {
      const res = await getMessageListApi({ page: 1, pageSize: 10 });
      notifications.value = (res.items || []).map((msg) => ({
        id: msg.id,
        avatar: typeAvatarMap[msg.msg_type] ?? typeAvatarMap.system!,
        title: msg.title,
        message: msg.content,
        date: formatDate(msg.created_at),
        isRead: msg.status === 'read',
        linkType: msg.link_type,
        linkId: msg.link_id,
        senderId: msg.sender_id,
        senderName: msg.sender_name,
      }));
    } catch (error) {
      console.error('加载消息失败:', error);
    }
  }

  // 加载未读数量
  async function loadUnreadCount() {
    try {
      const res = await getUnreadCountApi();
      messageUnreadCount.value = res.total;
      unreadByType.value = res.by_type;
    } catch (error) {
      console.error('加载未读数量失败:', error);
    }
  }

  // 加载公告列表
  async function loadAnnouncements() {
    try {
      const res = await getUserAnnouncementListApi({ page: 1, pageSize: 10 });
      announcements.value = (res.items || []).map((item) => ({
        id: item.id,
        title: item.title,
        summary: item.summary,
        content: item.content,
        date: formatDate(item.publish_time || ''),
        isRead: item.is_read,
        priority: item.priority,
        isTop: item.is_top,
        publisherName: item.publisher_name,
      }));
    } catch (error) {
      console.error('加载公告失败:', error);
    }
  }

  // 加载公告未读数量
  async function loadAnnouncementUnreadCount() {
    try {
      const res = await getUnreadAnnouncementCountApi();
      announcementUnreadCount.value = res.count;
    } catch (error) {
      console.error('加载公告未读数量失败:', error);
    }
  }

  // 标记消息已读并从列表中移除
  async function markAsRead(item: NotificationItem) {
    // 先跳转
    handleNavigate(item);

    // 从列表中移除
    const index = notifications.value.findIndex((n) => n.id === item.id);
    if (index !== -1) {
      notifications.value.splice(index, 1);
    }

    // 如果未读，调用API标记已读
    if (!item.isRead) {
      try {
        await markAsReadApi(item.id as string);
        messageUnreadCount.value = Math.max(0, messageUnreadCount.value - 1);
      } catch (error) {
        console.error('标记已读失败:', error);
      }
    }
  }

  // 标记公告已读并从列表中移除
  async function markAnnouncementAsRead(item: AnnouncementItem) {
    // 先跳转
    viewAnnouncementDetail(item);

    // 从列表中移除
    const index = announcements.value.findIndex((a) => a.id === item.id);
    if (index !== -1) {
      announcements.value.splice(index, 1);
    }

    // 如果未读，调用API标记已读
    if (!item.isRead) {
      try {
        await markAnnouncementReadApi(item.id);
        announcementUnreadCount.value = Math.max(
          0,
          announcementUnreadCount.value - 1,
        );
      } catch (error) {
        console.error('标记公告已读失败:', error);
      }
    }
  }

  // 标记全部消息已读
  async function markAllAsRead() {
    try {
      await markAllAsReadApi();
      notifications.value.forEach((item) => (item.isRead = true));
      messageUnreadCount.value = 0;
      unreadByType.value = {};
    } catch (error) {
      console.error('标记全部已读失败:', error);
    }
  }

  // 清空已读消息
  async function clearReadMessages() {
    try {
      await clearReadMessagesApi();
      // 重新加载消息列表和未读数量
      await loadMessages();
      await loadUnreadCount();
    } catch (error) {
      console.error('清空已读消息失败:', error);
    }
  }

  // 跳转到消息关联页面
  function handleNavigate(item: NotificationItem) {
    const linkType = item.linkType;
    const linkId = item.linkId;

    if (!linkType || !linkId) return;

    // 根据关联类型跳转（新开tab）
    let path = '';
    switch (linkType) {
      case 'announcement': {
        path = `/message/announcement-list`;
        break;
      }
      case 'workflow_instance': {
        path = `/app/workflow_center/workflow/initiated?id=${linkId}`;
        break;
      }
      case 'workflow_task': {
        path = `/app/workflow_center/workflow/pending?id=${linkId}`;
        break;
      }
      // No default
    }
    if (path) {
      const url = router.resolve(path).href;
      window.open(url, '_blank');
    }
  }

  // 查看公告详情
  function viewAnnouncementDetail(_item: AnnouncementItem) {
    // 跳转到公告列表页（新开tab）
    const url = router.resolve(`/message/announcement-list`).href;
    window.open(url, '_blank');
  }

  // 查看全部（根据当前 Tab 跳转）
  function viewAllMessages() {
    if (activeTab.value === 'announcement') {
      router.push('/message/announcement-list');
    } else {
      router.push('/message/list');
    }
  }

  // 连接 WebSocket
  function connectWebSocket() {
    const token = accessStore.accessToken;
    if (!token) return;

    // 使用统一的 WebSocketManager
    wsManagerInstance = createNotificationWebSocket({
      onOpen: () => {
        wsConnected.value = true;
        // 发送订阅消息
        wsManagerInstance?.send({ type: 'subscribe' });
      },
      onMessage: (message) => {
        handleWebSocketMessage(message);
      },
      onClose: () => {
        wsConnected.value = false;
      },
      onError: () => {
        wsConnected.value = false;
      },
    });

    wsManagerInstance.connect().catch((error) => {
      console.error('WebSocket 连接失败:', error);
    });
  }

  // 处理 WebSocket 消息
  function handleWebSocketMessage(data: any) {
    if (data.type === 'notification') {
      // 收到新通知
      const msgData = data.data;
      const newNotification: NotificationItem = {
        id: msgData.id,
        avatar: typeAvatarMap[msgData.msg_type] ?? typeAvatarMap.system!,
        title: msgData.title,
        message: msgData.content,
        date: $t('message.drawer.justNow'),
        isRead: false,
        linkType: msgData.link_type,
        linkId: msgData.link_id,
        senderId: msgData.sender_id,
        senderName: msgData.sender_name,
      };

      // 添加到列表头部
      notifications.value.unshift(newNotification);
      // 只保留最近10条
      if (notifications.value.length > 10) {
        notifications.value.pop();
      }
      // 更新未读数量
      messageUnreadCount.value += 1;
    } else if (data.type === 'announcement') {
      // 收到新公告推送，刷新公告列表和未读数
      loadAnnouncements();
      loadAnnouncementUnreadCount();
    }
  }

  // 断开 WebSocket
  function disconnectWebSocket() {
    if (wsManagerInstance) {
      wsManagerInstance.close();
      wsManagerInstance = null;
    }
  }

  // 格式化日期
  function formatDate(dateStr: string): string {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    if (diff < 60_000) return $t('message.drawer.justNow');
    if (diff < 3_600_000)
      return $t('message.drawer.minutesAgo', {
        count: Math.floor(diff / 60_000),
      });
    if (diff < 86_400_000)
      return $t('message.drawer.hoursAgo', {
        count: Math.floor(diff / 3_600_000),
      });
    if (diff < 604_800_000)
      return $t('message.drawer.daysAgo', {
        count: Math.floor(diff / 86_400_000),
      });

    return date.toLocaleDateString();
  }

  // 初始化
  function init() {
    loadMessages();
    loadUnreadCount();
    loadAnnouncements();
    loadAnnouncementUnreadCount();
    connectWebSocket();
  }

  // 清理
  function cleanup() {
    disconnectWebSocket();
  }

  return {
    // 消息
    notifications,
    messageUnreadCount,
    unreadByType,
    // 公告
    announcements,
    announcementUnreadCount,
    // 通用
    activeTab,
    totalUnreadCount,
    showDot,
    wsConnected,
    // 方法
    loadMessages,
    loadUnreadCount,
    loadAnnouncements,
    loadAnnouncementUnreadCount,
    markAsRead,
    markAnnouncementAsRead,
    markAllAsRead,
    clearReadMessages,
    viewAllMessages,
    init,
    cleanup,
  };
}
