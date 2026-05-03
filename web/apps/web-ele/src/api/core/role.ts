import { requestClient } from '#/api/request';

/**
 * 角色相关类型定义
 */
export interface Role {
  id: string;
  name: string;
  code: string;
  role_type: number;
  status: boolean;
  priority: number;
  description?: string;
  remark?: string;
  role_type_display?: string;
  user_count?: number;
  menu_count?: number;
  permission_count?: number;
  can_delete?: boolean;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface RoleCreateInput {
  name: string;
  code: string;
  role_type?: number;
  status?: boolean;
  priority?: number;
  description?: string;
  remark?: string;
  menu?: string[];
  permission?: string[];
  group?: string[];
}

export interface RoleUpdateInput extends Partial<RoleCreateInput> {}

export interface RoleBatchDeleteInput {
  ids: string[];
}

export interface RoleBatchUpdateStatusInput {
  ids: string[];
  status: boolean;
}

export interface RoleUserInput {
  user_ids: string[];
}

export interface RoleListParams {
  page?: number;
  pageSize?: number;
  name?: string;
  code?: string;
  status?: boolean;
  role_type?: number;
  id?: string[];
}

export interface RoleUser {
  id: string;
  username: string;
  name?: string;
  email?: string;
  mobile?: string;
  dept_name?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface MenuPermissionTree {
  menu_tree: any[];
  permission_tree: any[];
  selected_menu_ids: string[];
  selected_permission_ids: string[];
}

/**
 * 创建角色
 */
export async function createRoleApi(data: RoleCreateInput) {
  return requestClient.post<Role>('/api/core/role', data);
}

/**
 * 获取角色列表（分页）
 */
export async function getRoleListApi(params?: RoleListParams) {
  return requestClient.get<PaginatedResponse<Role>>('/api/core/role', {
    params,
  });
}

/**
 * 获取角色详情
 */
export async function getRoleDetailApi(roleId: string) {
  return requestClient.get<Role>(`/api/core/role/${roleId}`);
}

/**
 * 更新角色
 */
export async function updateRoleApi(roleId: string, data: RoleUpdateInput) {
  return requestClient.put<Role>(`/api/core/role/${roleId}`, data);
}

/**
 * 删除角色
 */
export async function deleteRoleApi(roleId: string) {
  return requestClient.delete<Role>(`/api/core/role/${roleId}`);
}

/**
 * 批量删除角色
 */
export async function batchDeleteRoleApi(data: RoleBatchDeleteInput) {
  return requestClient.post<{ count: number }>(
    '/api/core/role/batch_delete',
    data,
  );
}

/**
 * 批量更新角色状态
 */
export async function batchUpdateRoleStatusApi(
  data: RoleBatchUpdateStatusInput,
) {
  return requestClient.post<{ count: number }>(
    '/api/core/role/batch_update_status',
    data,
  );
}

/**
 * 获取角色用户列表
 */
export async function getRoleUsersApi(
  roleId: string,
  params?: { page?: number; pageSize?: number; username?: string },
) {
  return requestClient.get<PaginatedResponse<RoleUser>>(
    '/api/core/role/users/by/role_id',
    { params: { ...params, role_id: roleId } },
  );
}

/**
 * 为角色添加用户
 */
export async function addRoleUsersApi(roleId: string, data: RoleUserInput) {
  return requestClient.post<{ count: number }>(
    '/api/core/role/users/by/role_id',
    { ...data, role_id: roleId },
  );
}

/**
 * 从角色移除用户
 */
export async function removeRoleUsersApi(roleId: string, data: RoleUserInput) {
  return requestClient.delete<{ count: number }>(
    '/api/core/role/users/by/role_id',
    { data: { ...data, role_id: roleId } },
  );
}

/**
 * 获取角色的菜单权限树
 */
export async function getRoleMenuPermissionTreeApi(roleId: string) {
  return requestClient.get<MenuPermissionTree>(
    `/api/core/role/menu-permission-tree/${roleId}`,
  );
}

/**
 * 获取简单角色列表（用于选择器）
 */
export async function getSimpleRoleListApi() {
  return requestClient.get<Role[]>('/api/core/role/all');
}

/**
 * 获取角色权限列表（按菜单分组）
 */
export async function getRolePermissionTreeApi(roleId: string) {
  return requestClient.get<MenuPermissionTree>(
    `/api/core/role/menu-permission-tree/${roleId}`,
  );
}

/**
 * 更新角色权限
 */
export async function updateRolePermissionsApi(
  roleId: string,
  data: { permission_ids: string[] },
) {
  return requestClient.put(`/api/core/role/${roleId}/permissions`, data);
}

/**
 * 更新角色菜单和权限
 */
export async function updateRoleMenusPermissionsApi(
  roleId: string,
  data: { menu_ids: string[]; permission_ids: string[] },
) {
  return requestClient.put(`/api/core/role/${roleId}/menus-permissions`, data);
}

/**
 * 获取角色菜单列表（不包含权限）
 * @param roleId 角色ID
 * @param applicationId 应用ID，子应用访问时只显示该应用的菜单
 */
export async function getRoleMenusApi(roleId: string, applicationId?: string) {
  return requestClient.get<{
    menu_tree: any[];
    selected_menu_ids: string[];
  }>(`/api/core/role/${roleId}/menus`, {
    params: applicationId ? { applicationId } : undefined,
  });
}

/**
 * 获取菜单的权限列表
 */
export async function getMenuPermissionsApi(roleId: string, menuId: string) {
  return requestClient.get<{
    menu_id: string;
    permissions: any[];
  }>(`/api/core/role/${roleId}/menu/${menuId}/permissions`);
}

/**
 * 根据ID列表获取角色
 */
export async function getRolesByIds(ids: string[]) {
  if (!ids || ids.length === 0) return [];
  return requestClient.get<Role[]>('/api/core/role/by/ids', {
    params: { ids: ids.join(',') },
  });
}
