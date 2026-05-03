/**
 * 消息中心 API
 */
import { requestClient } from '#/api/request';

const BASE_URL = '/api/core/message';

// ============ 类型定义 ============

export interface Message {
  id: string;
  title: string;
  content: string;
  msg_type: 'announcement' | 'system' | 'todo' | 'workflow';
  status: 'read' | 'unread';
  link_type: string;
  link_id: string;
  sender_id?: string;
  sender_name?: string;
  read_at?: string;
  created_at: string;
}

export interface UnreadCount {
  total: number;
  by_type: Record<string, number>;
}

// ============ API 函数 ============

/**
 * 获取消息列表
 */
export async function getMessageListApi(params?: {
  msg_type?: string;
  page?: number;
  pageSize?: number;
  status?: string;
}) {
  return requestClient.get<{
    items: Message[];
    total: number;
  }>(`${BASE_URL}/list`, { params });
}

/**
 * 获取未读消息数量
 */
export async function getUnreadCountApi() {
  return requestClient.get<UnreadCount>(`${BASE_URL}/unread-count`);
}

/**
 * 获取消息详情
 */
export async function getMessageDetailApi(messageId: string) {
  return requestClient.get<Message>(`${BASE_URL}/${messageId}`);
}

/**
 * 标记单条消息为已读
 */
export async function markAsReadApi(messageId: string) {
  return requestClient.post(`${BASE_URL}/${messageId}/read`);
}

/**
 * 标记所有消息为已读
 */
export async function markAllAsReadApi(msgType?: string) {
  return requestClient.post(`${BASE_URL}/read-all`, { msg_type: msgType });
}

/**
 * 删除消息
 */
export async function deleteMessageApi(messageId: string) {
  return requestClient.delete(`${BASE_URL}/${messageId}`);
}

/**
 * 清空已读消息
 */
export async function clearReadMessagesApi() {
  return requestClient.delete(`${BASE_URL}/clear-read`);
}

/**
 * 发送消息
 */
export async function sendMessageApi(data: {
  channels?: string[];
  content: string;
  msg_type?: string;
  recipient_ids: string[];
  title: string;
}) {
  return requestClient.post<{
    data: { recipient_count: number; results: Record<string, boolean> };
    message: string;
  }>(`${BASE_URL}/send`, data);
}
