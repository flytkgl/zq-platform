/**
 * 公告管理 API
 */
import { requestClient } from '#/api/request';

const BASE_URL = '/api/core/announcement';

// ============ 类型定义 ============

export interface Announcement {
  id: string;
  title: string;
  content: string;
  summary: string;
  status: 'draft' | 'expired' | 'published';
  priority: 0 | 1 | 2;
  is_top: boolean;
  target_type: 'all' | 'dept' | 'role' | 'user';
  target_ids: string[];
  publish_time?: string;
  expire_time?: string;
  publisher_id?: string;
  publisher_name: string;
  read_count: number;
  created_at: string;
}

export interface AnnouncementListItem {
  id: string;
  title: string;
  summary: string;
  status: string;
  priority: number;
  is_top: boolean;
  target_type: string;
  publisher_name: string;
  read_count: number;
  publish_time?: string;
  created_at: string;
}

export interface UserAnnouncement {
  id: string;
  title: string;
  summary: string;
  content: string;
  priority: number;
  is_top: boolean;
  is_read: boolean;
  publisher_name: string;
  publish_time?: string;
}

export interface AnnouncementCreate {
  title: string;
  content: string;
  summary?: string;
  status?: string;
  priority?: number;
  is_top?: boolean;
  target_type?: string;
  target_ids?: string[];
  publish_time?: string;
  expire_time?: string;
}

export interface AnnouncementUpdate {
  title?: string;
  content?: string;
  summary?: string;
  status?: string;
  priority?: number;
  is_top?: boolean;
  target_type?: string;
  target_ids?: string[];
  publish_time?: string;
  expire_time?: string;
}

export interface ReadStats {
  total_read: number;
  readers: Array<{
    read_at: string;
    user_id: string;
    user_name: string;
  }>;
}

// ============ 管理端 API ============

/**
 * 获取公告列表（管理端）
 */
export async function getAnnouncementListApi(params?: {
  keyword?: string;
  page?: number;
  pageSize?: number;
  status?: string;
}) {
  return requestClient.get<{
    items: AnnouncementListItem[];
    total: number;
  }>(`${BASE_URL}/admin/list`, { params });
}

/**
 * 获取公告详情（管理端）
 */
export async function getAnnouncementDetailApi(id: string) {
  return requestClient.get<Announcement>(`${BASE_URL}/admin/${id}`);
}

/**
 * 创建公告
 */
export async function createAnnouncementApi(data: AnnouncementCreate) {
  return requestClient.post<Announcement>(`${BASE_URL}/admin`, data);
}

/**
 * 更新公告
 */
export async function updateAnnouncementApi(
  id: string,
  data: AnnouncementUpdate,
) {
  return requestClient.put<Announcement>(`${BASE_URL}/admin/${id}`, data);
}

/**
 * 删除公告
 */
export async function deleteAnnouncementApi(id: string) {
  return requestClient.delete(`${BASE_URL}/admin/${id}`);
}

/**
 * 发布公告
 */
export async function publishAnnouncementApi(id: string) {
  return requestClient.post<Announcement>(`${BASE_URL}/admin/${id}/publish`);
}

/**
 * 获取阅读统计
 */
export async function getReadStatsApi(id: string) {
  return requestClient.get<ReadStats>(`${BASE_URL}/admin/${id}/stats`);
}

// ============ 用户端 API ============

/**
 * 获取我的公告列表
 */
export async function getUserAnnouncementListApi(params?: {
  page?: number;
  pageSize?: number;
  unread_only?: boolean;
}) {
  return requestClient.get<{
    items: UserAnnouncement[];
    total: number;
  }>(`${BASE_URL}/user/list`, { params });
}

/**
 * 获取未读公告数量
 */
export async function getUnreadAnnouncementCountApi() {
  return requestClient.get<{ count: number }>(`${BASE_URL}/user/unread-count`);
}

/**
 * 获取公告详情（用户端，会自动标记已读）
 */
export async function getUserAnnouncementDetailApi(id: string) {
  return requestClient.get<UserAnnouncement>(`${BASE_URL}/user/${id}`);
}

/**
 * 标记公告已读
 */
export async function markAnnouncementReadApi(id: string) {
  return requestClient.post(`${BASE_URL}/user/${id}/read`);
}
