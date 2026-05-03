import { requestClient } from '#/api/request';

/**
 * 岗位相关类型定义
 */
export interface Post {
  id: string;
  name: string;
  code: string;
  post_type: number;
  post_level: number;
  status: boolean;
  description?: string;
  dept_id?: string;
  post_type_display?: string;
  post_level_display?: string;
  dept_name?: string;
  user_count?: number;
  can_delete?: boolean;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface PostCreateInput {
  name: string;
  code: string;
  post_type?: number;
  post_level?: number;
  status?: boolean;
  description?: string;
  dept_id?: string;
}

export interface PostUpdateInput extends Partial<PostCreateInput> {}

export interface PostBatchDeleteInput {
  ids: string[];
}

export interface PostBatchUpdateStatusInput {
  ids: string[];
  status: boolean;
}

export interface PostListParams {
  page?: number;
  pageSize?: number;
  name?: string;
  code?: string;
  post_type?: number;
  post_level?: number;
  status?: boolean;
  dept_id?: string;
}

export interface PostUser {
  id: string;
  username: string;
  name?: string;
  email?: string;
  mobile?: string;
  dept_name?: string;
}

export interface PostStats {
  total_count: number;
  active_count: number;
  inactive_count: number;
  type_counts: Record<string, number>;
  level_counts: Record<string, number>;
  total_users: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

/**
 * 创建岗位
 */
export async function createPostApi(data: PostCreateInput) {
  return requestClient.post<Post>('/api/core/post', data);
}

/**
 * 获取岗位列表（分页）
 */
export async function getPostListApi(params?: PostListParams) {
  return requestClient.get<PaginatedResponse<Post>>('/api/core/post', {
    params,
  });
}

/**
 * 获取岗位详情
 */
export async function getPostDetailApi(postId: string) {
  return requestClient.get<Post>(`/api/core/post/${postId}`);
}

/**
 * 更新岗位
 */
export async function updatePostApi(postId: string, data: PostUpdateInput) {
  return requestClient.put<Post>(`/api/core/post/${postId}`, data);
}

/**
 * 删除岗位
 */
export async function deletePostApi(postId: string) {
  return requestClient.delete<Post>(`/api/core/post/${postId}`);
}

/**
 * 批量删除岗位
 */
export async function batchDeletePostApi(data: PostBatchDeleteInput) {
  return requestClient.post<{ count: number }>(
    '/api/core/post/batch_delete',
    data,
  );
}

/**
 * 批量更新岗位状态
 */
export async function batchUpdatePostStatusApi(
  data: PostBatchUpdateStatusInput,
) {
  return requestClient.post<{ count: number }>(
    '/api/core/post/batch_update_status',
    data,
  );
}

/**
 * 根据部门ID获取岗位列表
 */
export async function getPostsByDeptApi(deptId: string) {
  return requestClient.get<Post[]>(`/api/core/post/by_dept/${deptId}`);
}

/**
 * 获取岗位用户列表
 */
export async function getPostUsersApi(
  postId: string,
  params?: { page?: number; pageSize?: number; username?: string },
) {
  return requestClient.get<PaginatedResponse<PostUser>>(
    '/api/core/post/users/by/post_id',
    { params: { ...params, post_id: postId } },
  );
}

/**
 * 为岗位添加用户
 */
export async function addPostUsersApi(
  postId: string,
  data: { user_ids: string[] },
) {
  return requestClient.post<{ count: number }>(
    '/api/core/post/users/by/post_id',
    { ...data, post_id: postId },
  );
}

/**
 * 从岗位移除用户
 */
export async function removePostUsersApi(
  postId: string,
  data: { user_ids: string[] },
) {
  return requestClient.delete<{ count: number }>(
    '/api/core/post/users/by/post_id',
    { data: { ...data, post_id: postId } },
  );
}

/**
 * 获取岗位统计信息
 */
export async function getPostStatsApi() {
  return requestClient.get<PostStats>('/api/core/post/stats');
}

/**
 * 导出岗位数据
 */
export async function exportPostApi(params?: PostListParams) {
  return requestClient.get<Blob>('/api/core/post/export', {
    params,
    responseType: 'blob',
  });
}

/**
 * 导入岗位数据
 */
export async function importPostApi(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return requestClient.post<{ error_count: number; success_count: number }>(
    '/api/core/post/import',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
  );
}

/**
 * 获取简单岗位列表（用于选择器）
 */
export async function getSimplePostListApi() {
  return requestClient.get<Post[]>('/api/core/post/simple');
}

/**
 * 根据ID列表获取岗位
 */
export async function getPostsByIds(ids: string[]) {
  if (!ids || ids.length === 0) return [];
  return requestClient.get<Post[]>('/api/core/post/by/ids', {
    params: { ids: ids.join(',') },
  });
}
