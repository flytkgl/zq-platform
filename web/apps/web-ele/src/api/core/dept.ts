import { requestClient } from '#/api/request';

/**
 * 部门相关类型定义
 */
export interface Dept {
  id: string;
  parent_id?: string;
  name: string;
  dept_type: string; // 'company' | 'department' | 'team' | 'other'
  code?: string;
  phone?: string;
  email?: string;
  status: boolean;
  description?: string;
  lead_id?: string;
  level: number;
  path: string;
  dept_type_display?: string;
  lead_name?: string;
  user_count?: number;
  child_count?: number;
  can_delete?: boolean;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface DeptTreeNode extends Dept {
  children?: DeptTreeNode[];
}

export interface DeptCreateInput {
  parent_id?: string;
  name: string;
  dept_type?: string; // 'company' | 'department' | 'team' | 'other'
  code?: string;
  phone?: string;
  email?: string;
  status?: boolean;
  description?: string;
  lead_id?: string;
}

export interface DeptUpdateInput extends Partial<DeptCreateInput> {}

export interface DeptBatchDeleteInput {
  ids: string[];
}

export interface DeptMoveInput {
  target_parent_id?: string;
  position?: number;
}

export interface DeptListParams {
  page?: number;
  pageSize?: number;
  name?: string;
  dept_type?: string;
  status?: boolean;
  parent_id?: string;
}

export interface DeptUser {
  id: string;
  username: string;
  name?: string;
  email?: string;
  mobile?: string;
  user_status?: number;
}

export interface DeptStats {
  total_count: number;
  active_count: number;
  inactive_count: number;
  type_counts: Record<string, number>;
  max_level: number;
  total_users: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

/**
 * 创建部门
 */
export async function createDeptApi(data: DeptCreateInput) {
  return requestClient.post<Dept>('/api/core/dept', data);
}

/**
 * 获取部门列表（分页）
 */
export async function getDeptListApi(params?: DeptListParams) {
  return requestClient.get<Dept[]>('/api/core/dept', { params });
}

/**
 * 获取部门树形结构
 */
export async function getDeptTreeApi() {
  return requestClient.get<DeptTreeNode[]>('/api/core/dept/tree');
}

/**
 * 获取部门详情
 */
export async function getDeptDetailApi(deptId: string) {
  return requestClient.get<Dept>(`/api/core/dept/${deptId}`);
}

/**
 * 更新部门
 */
export async function updateDeptApi(deptId: string, data: DeptUpdateInput) {
  return requestClient.put<Dept>(`/api/core/dept/${deptId}`, data);
}

/**
 * 删除部门
 */
export async function deleteDeptApi(deptId: string) {
  return requestClient.delete<Dept>(`/api/core/dept/${deptId}`);
}

/**
 * 批量删除部门
 */
export async function batchDeleteDeptApi(data: DeptBatchDeleteInput) {
  return requestClient.post<{ count: number }>(
    '/api/core/dept/batch_delete',
    data,
  );
}

/**
 * 根据父部门ID获取子部门
 */
export async function getDeptByParentApi(parentId?: string) {
  const url = parentId
    ? `/api/core/dept/by/parent/${parentId}`
    : '/api/core/dept/by/parent/null';
  return requestClient.get<Dept[]>(url);
}

/**
 * 搜索部门
 */
export async function searchDeptApi(keyword: string) {
  return requestClient.get<Dept[]>('/api/core/dept/search', {
    params: { keyword },
  });
}

/**
 * 移动部门
 */
export async function moveDeptApi(deptId: string, data: DeptMoveInput) {
  return requestClient.post<Dept>(`/api/core/dept/${deptId}/move`, data);
}

/**
 * 获取部门路径
 */
export async function getDeptPathApi(deptId: string) {
  return requestClient.get<Dept[]>(`/api/core/dept/${deptId}/path`);
}

/**
 * 获取部门用户列表
 */
export async function getDeptUsersApi(
  deptId: string,
  params?: {
    include_children?: boolean;
    page?: number;
    pageSize?: number;
    username?: string;
  },
) {
  return requestClient.get<PaginatedResponse<DeptUser>>(
    `/api/core/dept/users/${deptId}`,
    { params },
  );
}

/**
 * 为部门添加用户
 */
export async function addDeptUsersApi(
  deptId: string,
  data: { user_ids: string[] },
) {
  return requestClient.post<{ count: number }>(
    `/api/core/dept/users/${deptId}`,
    data,
  );
}

/**
 * 从部门移除用户
 */
export async function removeDeptUsersApi(
  deptId: string,
  data: { user_ids: string[] },
) {
  return requestClient.delete<{ count: number }>(
    `/api/core/dept/users/${deptId}`,
    { data },
  );
}

/**
 * 获取部门统计信息
 */
export async function getDeptStatsApi() {
  return requestClient.get<DeptStats>('/api/core/dept/stats');
}

/**
 * 获取简单部门列表（用于选择器）
 */
export async function getSimpleDeptListApi() {
  return requestClient.get<Dept[]>('/api/core/dept/simple');
}

/**
 * 根据ID列表获取部门
 */
export async function getDeptsByIds(ids: string[]) {
  if (!ids || ids.length === 0) return [];
  return requestClient.get<DeptTreeNode[]>('/api/core/dept/by/ids', {
    params: { ids: ids.join(',') },
  });
}
