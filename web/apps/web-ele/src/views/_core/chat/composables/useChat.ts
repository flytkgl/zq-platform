import type {
  ChatMessage,
  Conversation,
  ConversationMember,
} from '#/api/core/chat';
import type { WebSocketManager } from '#/api/core/websocket';

import { computed, nextTick, ref } from 'vue';

import { $t } from '@vben/locales';
import { useAccessStore, useUserStore } from '@vben/stores';

import {
  createGroupConversationApi,
  createPrivateConversationApi,
  getConversationsApi,
  getMembersApi,
  getMessagesApi,
  getOnlineUsersApi,
  getUnreadChatMessagesApi,
  markConversationReadApi,
  recallMessageApi,
  sendChatMessageApi,
  toggleMuteApi,
  togglePinApi,
} from '#/api/core/chat';
import { createChatWebSocket } from '#/api/core/websocket';

import {
  addCachedMessage,
  clearChatCache,
  getCachedConversations,
  getCachedMessages,
  setCachedConversations,
  setCachedMessages,
  setLastSyncTime,
  updateCachedConversation,
  updateCachedMessage,
} from './chatStorage';
import { showBrowserNotification, showChatToast } from './useChatNotification';
import { playMessageSound } from './useChatSound';

// ============ 状态 ============
const conversations = ref<Conversation[]>([]);
const currentConversation = ref<Conversation | null>(null);
const messages = ref<ChatMessage[]>([]);
const members = ref<ConversationMember[]>([]);
const hasMoreMessages = ref(false);
const loadingConversations = ref(false);
const loadingMessages = ref(false);
const loadingMembers = ref(false);
const sending = ref(false);
const isLoadingMore = ref(false);
const typingUsers = ref<Map<string, string>>(new Map());
// 待跳转的会话ID（从其他页面点击通知后跳转到聊天页时使用）
const pendingConversationId = ref<null | string>(null);

const unreadChatMessages = ref<ChatMessage[]>([]);
const onlineUsers = ref<Set<string>>(new Set());

let wsManager: null | WebSocketManager = null;
const typingTimers: Map<string, ReturnType<typeof setTimeout>> = new Map();
let tempIdCounter = 0;

// ============ 计算属性 ============
const totalUnread = computed(() =>
  conversations.value.reduce((sum, c) => sum + (c.unread_count || 0), 0),
);

// ============ WebSocket ============
function connectChat() {
  if (wsManager?.isConnected) return;

  const accessStore = useAccessStore();
  if (!accessStore.accessToken) return;

  wsManager = createChatWebSocket({
    onOpen: () => {
      console.log('[Chat WS] Connected');
    },
    onMessage: (message) => {
      handleWsMessage(message);
    },
    onClose: () => {
      console.log('[Chat WS] Disconnected');
    },
    onError: () => {
      console.error('[Chat WS] Error');
    },
  });

  wsManager.connect().catch((error) => {
    console.error('[Chat WS] Connect failed:', error);
  });
}

function disconnectChat() {
  wsManager?.close();
  wsManager = null;
}

function handleWsMessage(data: any) {
  const type = data.type;
  const payload = data.data;

  switch (type) {
    case 'chat.message': {
      handleIncomingMessage(payload);
      break;
    }
    case 'chat.presence': {
      handlePresence(payload);
      break;
    }
    case 'chat.read_receipt': {
      handleReadReceipt(payload);
      break;
    }
    case 'chat.recalled': {
      handleRecalledMessage(payload);
      break;
    }
    case 'chat.typing': {
      handleTypingNotification(payload);
      break;
    }
  }
}

function handleIncomingMessage(msg: ChatMessage) {
  // 如果是当前会话的消息，添加到消息列表
  if (
    currentConversation.value &&
    msg.conversation_id === currentConversation.value.id
  ) {
    // 查找是否有对应的临时消息（乐观更新），用服务器确认的消息替换
    const userStore = useUserStore();
    const currentUserId = userStore.userInfo?.userId || '';
    const tempIndex =
      msg.sender_id === currentUserId
        ? messages.value.findIndex(
            (m) =>
              m._sending &&
              m._tempId &&
              m.msg_type === msg.msg_type &&
              (m.msg_type === 'text'
                ? m.content === msg.content
                : m.file_id === msg.file_id),
          )
        : -1;
    if (tempIndex >= 0) {
      // 释放本地 blob URL
      const tempMsg = messages.value[tempIndex];
      if (tempMsg?._localUrl) {
        URL.revokeObjectURL(tempMsg._localUrl);
      }
      messages.value.splice(tempIndex, 1, msg);
    } else {
      const exists = messages.value.some((m) => m.id === msg.id);
      if (!exists) {
        messages.value.push(msg);
      }
    }
  }

  // 缓存新消息到本地
  addCachedMessage(msg);

  // 非自己发的消息：提示音 + 通知 + 更新未读消息列表
  const userId = getCurrentUserId();
  if (msg.sender_id !== userId) {
    // 实时添加到未读消息列表（通知中心用）
    if (
      !currentConversation.value ||
      msg.conversation_id !== currentConversation.value.id
    ) {
      unreadChatMessages.value.unshift(msg);
    }

    playMessageSound();
    // 不是当前会话的消息才显示 Toast
    if (
      !currentConversation.value ||
      msg.conversation_id !== currentConversation.value.id
    ) {
      const conv = conversations.value.find(
        (c) => c.id === msg.conversation_id,
      );
      showChatToast(msg, () => {
        // 设置待跳转会话，导航到聊天页后自动选中
        pendingConversationId.value = msg.conversation_id;
        // 使用 window.location 检查是否已在聊天页
        if (
          window.location.hash?.includes('/chat') ||
          window.location.pathname?.includes('/chat')
        ) {
          // 已在聊天页，直接选中会话
          if (conv) selectConversation(conv);
          pendingConversationId.value = null;
        } else {
          // 不在聊天页，通过动态 import router 导航
          import('#/router').then(({ router }) => {
            router.push('/chat');
          });
        }
      });
      showBrowserNotification(msg);
    }
  }

  // 更新会话列表
  const convIndex = conversations.value.findIndex(
    (c) => c.id === msg.conversation_id,
  );
  if (convIndex !== -1) {
    const conv = { ...conversations.value[convIndex]! };
    conv.last_message_preview =
      msg.content || `[${$t(`chat.${msg.msg_type}`) || msg.msg_type}]`;
    conv.last_message_time = msg.sys_create_datetime || '';
    // 如果不是当前会话，增加未读数
    if (
      !currentConversation.value ||
      msg.conversation_id !== currentConversation.value.id
    ) {
      conv.unread_count = (conv.unread_count || 0) + 1;
    }
    conversations.value.splice(convIndex, 1);
    conversations.value.unshift(conv);
    // 更新会话缓存
    const userId = getCurrentUserId();
    if (userId) {
      updateCachedConversation(userId, conv);
    }
  }
}

function handleTypingNotification(payload: {
  conversation_id: string;
  user_id: string;
  user_name: string;
}) {
  if (
    currentConversation.value &&
    payload.conversation_id === currentConversation.value.id
  ) {
    typingUsers.value.set(payload.user_id, payload.user_name);

    // 清除之前的定时器
    const existingTimer = typingTimers.get(payload.user_id);
    if (existingTimer) clearTimeout(existingTimer);

    // 3秒后自动清除
    typingTimers.set(
      payload.user_id,
      setTimeout(() => {
        typingUsers.value.delete(payload.user_id);
        typingTimers.delete(payload.user_id);
      }, 3000),
    );
  }
}

function handleRecalledMessage(payload: {
  conversation_id: string;
  message_id: string;
}) {
  if (
    currentConversation.value &&
    payload.conversation_id === currentConversation.value.id
  ) {
    const msg = messages.value.find((m) => m.id === payload.message_id);
    if (msg) {
      msg.is_recalled = true;
      msg.content = null as any;
      // 更新缓存中的撤回状态
      updateCachedMessage(msg);
    }
  }
}

function handleReadReceipt(_payload: {
  conversation_id: string;
  message_id: string;
  user_id: string;
}) {
  // 可用于显示已读状态
}

function handlePresence(payload: { status: string; user_id: string }) {
  if (payload.status === 'online') {
    onlineUsers.value.add(payload.user_id);
  } else {
    onlineUsers.value.delete(payload.user_id);
  }
  // 触发响应式更新
  onlineUsers.value = new Set(onlineUsers.value);
}

// ============ 辅助函数 ============
function getCurrentUserId(): string {
  const userStore = useUserStore();
  return userStore.userInfo?.userId || '';
}

// ============ API 操作 ============
async function loadConversations() {
  loadingConversations.value = true;
  const userId = getCurrentUserId();

  // 1. 先从本地缓存加载，立即渲染
  if (userId) {
    try {
      const cached = await getCachedConversations(userId);
      if (cached.length > 0 && conversations.value.length === 0) {
        conversations.value = cached;
      }
    } catch (error) {
      console.warn('[Chat] Load cache failed:', error);
    }
  }

  // 2. 从服务端同步最新数据
  try {
    const res = await getConversationsApi();
    conversations.value = res.items || [];
    // 写入缓存
    if (userId) {
      setCachedConversations(userId, conversations.value);
      setLastSyncTime(userId);
    }
  } catch (error) {
    console.error('加载会话列表失败:', error);
  } finally {
    loadingConversations.value = false;
  }
}

async function selectConversation(conv: Conversation) {
  currentConversation.value = conv;
  messages.value = [];
  hasMoreMessages.value = false;
  typingUsers.value.clear();

  // 等待 key 变化触发 MessageList 重建后再加载数据
  await nextTick();

  // 确保切换期间用户没有再次切换到其他会话
  if (currentConversation.value?.id !== conv.id) return;

  // 先从缓存加载消息（此时新 MessageList 已创建，不会闪现旧消息）
  try {
    const cached = await getCachedMessages(conv.id, 30);
    if (currentConversation.value?.id !== conv.id) return;
    if (cached.items.length > 0 && messages.value.length === 0) {
      // 只有当 messages 仍为空时才使用缓存（避免覆盖已加载的服务端数据）
      messages.value = cached.items;
      hasMoreMessages.value = cached.has_more;
    }
  } catch (error) {
    console.warn('[Chat] Load cached messages failed:', error);
  }

  // 从服务端加载最新数据
  if (currentConversation.value?.id !== conv.id) return;
  await Promise.all([loadMessages(), loadMembers()]);

  // 标记已读
  if (conv.unread_count > 0 && messages.value.length > 0) {
    const lastMsg = messages.value[messages.value.length - 1];
    if (lastMsg) {
      await markConversationReadApi(conv.id, lastMsg.id);
      const c = conversations.value.find((item) => item.id === conv.id);
      if (c) c.unread_count = 0;
      // 从未读消息列表中移除该会话的消息
      unreadChatMessages.value = unreadChatMessages.value.filter(
        (m) => m.conversation_id !== conv.id,
      );
    }
  }
}

async function loadMessages(loadMore = false) {
  if (!currentConversation.value) return;
  const convId = currentConversation.value.id;
  loadingMessages.value = true;
  if (loadMore) isLoadingMore.value = true;
  try {
    const beforeId =
      loadMore && messages.value.length > 0 ? messages.value[0]?.id : undefined;
    const res = await getMessagesApi(convId, {
      beforeId,
      limit: 30,
    });
    // 请求返回后检查会话是否已切换
    if (currentConversation.value?.id !== convId) return;

    const items = res.items || [];
    hasMoreMessages.value = res.has_more || false;

    if (loadMore) {
      // 使用 splice 原地插入，避免替换数组引用触发整体替换的 watch
      messages.value.splice(0, 0, ...items);
    } else {
      messages.value = items;
    }
    // 缓存到本地
    if (items.length > 0) {
      setCachedMessages(convId, items);
    }
  } catch (error) {
    console.error('加载消息失败:', error);
  } finally {
    loadingMessages.value = false;
    if (loadMore) isLoadingMore.value = false;
  }
}

async function loadMembers() {
  if (!currentConversation.value) return;
  loadingMembers.value = true;
  try {
    const res = await getMembersApi(currentConversation.value.id);
    members.value = Array.isArray(res) ? res : [];
  } catch (error) {
    console.error('加载成员失败:', error);
  } finally {
    loadingMembers.value = false;
  }
}

async function sendMessage(
  content: string,
  msgType = 'text',
  fileId?: string,
  replyToId?: string,
  fileName?: string,
  localUrl?: string,
  extra?: Record<string, any>,
) {
  if (!currentConversation.value) return;
  sending.value = true;

  // 乐观更新：立即插入临时消息
  const userStore = useUserStore();
  const tempId = `_temp_${++tempIdCounter}_${Date.now()}`;
  const tempMsg: ChatMessage = {
    id: tempId,
    conversation_id: currentConversation.value.id,
    sender_id: userStore.userInfo?.userId || '',
    msg_type: msgType,
    content: msgType === 'text' ? content : undefined,
    file_id: fileId,
    file_name: fileName,
    reply_to_id: replyToId,
    is_recalled: false,
    sys_create_datetime: new Date().toISOString(),
    sender_name:
      userStore.userInfo?.realName || userStore.userInfo?.username || '',
    sender_avatar: userStore.userInfo?.avatar || '',
    extra,
    _sending: true,
    _tempId: tempId,
    _localUrl: localUrl,
  };
  messages.value.push(tempMsg);

  try {
    // 优先走 WebSocket
    if (wsManager?.isConnected) {
      wsManager.send({
        type: 'chat.send',
        data: {
          conversation_id: currentConversation.value.id,
          msg_type: msgType,
          content: msgType === 'text' ? content : undefined,
          file_id: fileId,
          reply_to_id: replyToId,
          extra,
        },
      });
    } else {
      // 降级走 REST
      const result = await sendChatMessageApi(currentConversation.value.id, {
        msg_type: msgType,
        content: msgType === 'text' ? content : undefined,
        file_id: fileId,
        reply_to_id: replyToId,
        extra,
      });
      // REST 返回后替换临时消息
      const idx = messages.value.findIndex((m) => m._tempId === tempId);
      if (idx !== -1 && result) {
        messages.value.splice(idx, 1, result as ChatMessage);
        // 缓存已确认的消息
        addCachedMessage(result as ChatMessage);
      } else if (idx !== -1) {
        messages.value[idx]!._sending = false;
      }
    }
  } catch (error) {
    // 发送失败，移除临时消息
    const idx = messages.value.findIndex((m) => m._tempId === tempId);
    if (idx !== -1) {
      messages.value.splice(idx, 1);
    }
    console.error('发送消息失败:', error);
    throw error;
  } finally {
    sending.value = false;
  }
}

function sendTyping() {
  if (!currentConversation.value || !wsManager?.isConnected) return;
  wsManager.send({
    type: 'chat.typing',
    data: { conversation_id: currentConversation.value.id },
  });
}

async function recallMessage(messageId: string) {
  await recallMessageApi(messageId);
  // 立即更新本地消息状态（撤回者自己不会收到 chat.recalled WebSocket 事件）
  const msg = messages.value.find((m) => m.id === messageId);
  if (msg) {
    msg.is_recalled = true;
    msg.content = null as any;
    // 同步更新缓存
    updateCachedMessage(msg);
  }
}

async function createPrivateChat(userId: string) {
  const conv = await createPrivateConversationApi(userId);
  // 添加到列表前面
  const exists = conversations.value.findIndex((c) => c.id === conv.id);
  if (exists !== -1) {
    conversations.value.splice(exists, 1);
  }
  conversations.value.unshift(conv);
  await selectConversation(conv);
  return conv;
}

async function createGroupChat(name: string, memberIds: string[]) {
  const conv = await createGroupConversationApi({
    name,
    member_ids: memberIds,
  });
  conversations.value.unshift(conv);
  await selectConversation(conv);
  return conv;
}

async function loadUnreadChatMessages() {
  try {
    const res = await getUnreadChatMessagesApi(50);
    unreadChatMessages.value = res.items || [];
  } catch (error) {
    console.error('[Chat] Failed to load unread messages:', error);
  }
}

async function loadOnlineUsers() {
  try {
    const res = await getOnlineUsersApi();
    onlineUsers.value = new Set(res.user_ids || []);
  } catch (error) {
    console.error('[Chat] Failed to load online users:', error);
  }
}

async function togglePin(conversationId: string, value: boolean) {
  await togglePinApi(conversationId, value);
  const conv = conversations.value.find((c) => c.id === conversationId);
  if (conv) conv.is_pinned = value;
}

async function toggleMute(conversationId: string, value: boolean) {
  await toggleMuteApi(conversationId, value);
  const conv = conversations.value.find((c) => c.id === conversationId);
  if (conv) conv.is_muted = value;
}

// ============ 导出 ============
export function useChat() {
  return {
    // 状态
    conversations,
    currentConversation,
    messages,
    members,
    hasMoreMessages,
    loadingConversations,
    loadingMessages,
    loadingMembers,
    sending,
    isLoadingMore,
    typingUsers,
    totalUnread,
    pendingConversationId,
    unreadChatMessages,
    onlineUsers,
    // WebSocket
    connectChat,
    disconnectChat,
    // 操作
    loadConversations,
    loadUnreadChatMessages,
    loadOnlineUsers,
    selectConversation,
    loadMessages,
    loadMembers,
    sendMessage,
    sendTyping,
    recallMessage,
    createPrivateChat,
    createGroupChat,
    togglePin,
    toggleMute,
    clearChatCache,
  };
}
