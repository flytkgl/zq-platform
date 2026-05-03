import { requestClient } from '#/api/request';

const BASE_URL = '/api/core/chat';

// ============ 类型定义 ============

export interface Conversation {
  id: string;
  type: 'group' | 'private';
  name?: string;
  avatar?: string;
  owner_id?: string;
  last_message_time?: string;
  last_message_preview?: string;
  member_count: number;
  sys_create_datetime?: string;
  unread_count: number;
  is_muted: boolean;
  is_pinned: boolean;
  peer_user_id?: string;
  peer_user_name?: string;
  peer_user_avatar?: string;
}

export interface ConversationMember {
  id: string;
  user_id: string;
  role: string;
  nickname?: string;
  is_muted: boolean;
  is_pinned: boolean;
  unread_count: number;
  joined_at?: string;
  user_name?: string;
  user_avatar?: string;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender_id: string;
  msg_type: string;
  content?: string;
  file_id?: string;
  reply_to_id?: string;
  is_recalled: boolean;
  recalled_at?: string;
  extra?: Record<string, any>;
  sys_create_datetime?: string;
  sender_name?: string;
  sender_avatar?: string;
  reply_to_preview?: string;
  reply_to_sender_name?: string;
  file_name?: string;
  file_url?: string;
  file_size?: number;
  file_ext?: string;
  _sending?: boolean;
  _tempId?: string;
  _localUrl?: string;
}

// ============ 会话 API ============

/** 获取会话列表 */
export async function getConversationsApi() {
  return requestClient.get<{ items: Conversation[]; total: number }>(
    `${BASE_URL}/conversations`,
  );
}

/** 创建/获取单聊 */
export async function createPrivateConversationApi(userId: string) {
  return requestClient.post<Conversation>(`${BASE_URL}/conversations/private`, {
    user_id: userId,
  });
}

/** 创建群聊 */
export async function createGroupConversationApi(data: {
  avatar?: string;
  member_ids: string[];
  name: string;
}) {
  return requestClient.post<Conversation>(
    `${BASE_URL}/conversations/group`,
    data,
  );
}

/** 获取会话详情 */
export async function getConversationApi(conversationId: string) {
  return requestClient.get<Conversation>(
    `${BASE_URL}/conversations/${conversationId}`,
  );
}

/** 更新群聊信息 */
export async function updateConversationApi(
  conversationId: string,
  data: { avatar?: string; name?: string },
) {
  return requestClient.put<Conversation>(
    `${BASE_URL}/conversations/${conversationId}`,
    data,
  );
}

/** 解散群聊 */
export async function deleteConversationApi(conversationId: string) {
  return requestClient.delete(`${BASE_URL}/conversations/${conversationId}`);
}

// ============ 成员 API ============

/** 获取成员列表 */
export async function getMembersApi(conversationId: string) {
  return requestClient.get<ConversationMember[]>(
    `${BASE_URL}/conversations/${conversationId}/members`,
  );
}

/** 添加成员 */
export async function addMembersApi(conversationId: string, userIds: string[]) {
  return requestClient.post(
    `${BASE_URL}/conversations/${conversationId}/members`,
    { user_ids: userIds },
  );
}

/** 移除成员 */
export async function removeMemberApi(conversationId: string, userId: string) {
  return requestClient.delete(
    `${BASE_URL}/conversations/${conversationId}/members/${userId}`,
  );
}

// ============ 会话设置 API ============

/** 置顶/取消置顶 */
export async function togglePinApi(conversationId: string, value: boolean) {
  return requestClient.put(`${BASE_URL}/conversations/${conversationId}/pin`, {
    value,
  });
}

/** 免打扰设置 */
export async function toggleMuteApi(conversationId: string, value: boolean) {
  return requestClient.put(`${BASE_URL}/conversations/${conversationId}/mute`, {
    value,
  });
}

// ============ 消息 API ============

/** 获取消息列表（游标分页） */
export async function getMessagesApi(
  conversationId: string,
  params?: { beforeId?: string; limit?: number },
) {
  return requestClient.get<{ has_more: boolean; items: ChatMessage[] }>(
    `${BASE_URL}/conversations/${conversationId}/messages`,
    { params },
  );
}

/** 发送消息（REST备用） */
export async function sendChatMessageApi(
  conversationId: string,
  data: {
    content?: string;
    extra?: Record<string, any>;
    file_id?: string;
    msg_type?: string;
    reply_to_id?: string;
  },
) {
  return requestClient.post<ChatMessage>(
    `${BASE_URL}/conversations/${conversationId}/messages`,
    data,
  );
}

/** 撤回消息 */
export async function recallMessageApi(messageId: string) {
  return requestClient.post(`${BASE_URL}/messages/${messageId}/recall`);
}

/** 获取所有未读聊天消息 */
export async function getUnreadChatMessagesApi(limit = 50) {
  return requestClient.get<{ items: ChatMessage[]; total: number }>(
    `${BASE_URL}/messages/unread`,
    { params: { limit } },
  );
}

/** 获取在线用户ID列表 */
export async function getOnlineUsersApi() {
  return requestClient.get<{ user_ids: string[] }>(`${BASE_URL}/users/online`);
}

/** 标记已读 */
export async function markConversationReadApi(
  conversationId: string,
  messageId: string,
) {
  return requestClient.post(
    `${BASE_URL}/conversations/${conversationId}/read`,
    { message_id: messageId },
  );
}
