import { requestClient } from '#/api/request';

/**
 * 权限相关类型定义
 */
export interface Permission {
  id: string;
  menu_id: string;
  name: string;
  code: string;
  permission_type: number;
  api_path?: string;
  http_method?: number;
  description?: string;
  is_active: boolean;
  permission_type_display?: string;
  http_method_display?: string;
  menu_name?: string;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface PermissionCreateInput {
  menu_id: string;
  name: string;
  code: string;
  permission_type?: number;
  api_path?: string;
  http_method?: number;
  description?: string;
  is_active?: boolean;
}

export interface PermissionUpdateInput extends Partial<PermissionCreateInput> {}

export interface PermissionBatchDeleteInput {
  ids: string[];
}

export interface PermissionBatchUpdateStatusInput {
  ids: string[];
  is_active: boolean;
}

export interface PermissionListParams {
  page?: number;
  pageSize?: number;
  name?: string;
  code?: string;
  permission_type?: number;
  is_active?: boolean;
  menu_id?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface PermissionStats {
  total_count: number;
  active_count: number;
  inactive_count: number;
  type_counts: Record<string, number>;
}

/**
 * 创建权限
 */
export async function createPermissionApi(data: PermissionCreateInput) {
  return requestClient.post<Permission>('/api/core/permission', data);
}

/**
 * 获取权限列表（分页）
 */
export async function getPermissionListApi(params?: PermissionListParams) {
  return requestClient.get<PaginatedResponse<Permission>>(
    '/api/core/permission',
    { params },
  );
}

/**
 * 获取权限详情
 */
export async function getPermissionDetailApi(permissionId: string) {
  return requestClient.get<Permission>(`/api/core/permission/${permissionId}`);
}

/**
 * 更新权限
 */
export async function updatePermissionApi(
  permissionId: string,
  data: PermissionUpdateInput,
) {
  return requestClient.put<Permission>(
    `/api/core/permission/${permissionId}`,
    data,
  );
}

/**
 * 删除权限
 */
export async function deletePermissionApi(permissionId: string) {
  return requestClient.delete<Permission>(
    `/api/core/permission/${permissionId}`,
  );
}

/**
 * 批量删除权限
 */
export async function batchDeletePermissionApi(
  data: PermissionBatchDeleteInput,
) {
  return requestClient.post<{ count: number }>(
    '/api/core/permission/batch/delete',
    data,
  );
}

/**
 * 批量更新权限状态
 */
export async function batchUpdatePermissionStatusApi(
  data: PermissionBatchUpdateStatusInput,
) {
  return requestClient.post<{ count: number }>(
    '/api/core/permission/batch_update_status',
    data,
  );
}

/**
 * 根据菜单ID获取权限列表
 */
export async function getPermissionsByMenuApi(menuId: string) {
  return requestClient.get<Permission[]>(
    `/api/core/permission/by_menu/${menuId}`,
  );
}

/**
 * 获取权限统计信息
 */
export async function getPermissionStatsApi() {
  return requestClient.get<PermissionStats>('/api/core/permission/stats');
}

/**
 * 检查权限编码是否可用
 */
export async function checkPermissionCodeApi(code: string, menuId: string) {
  return requestClient.get<{ available: boolean }>(
    '/api/core/permission/check_code',
    {
      params: { code, menu_id: menuId },
    },
  );
}

/**
 * 获取所有可用的 API 路由
 */
export async function getAllRoutesApi() {
  return requestClient.get<any[]>('/api/core/permission/all/routes');
}

/**
 * 从路由批量创建权限
 */
export async function batchCreatePermissionsFromRoutesApi(data: {
  menu_id: string;
  routes: any[];
}) {
  return requestClient.post<{
    created: number;
    errors: string[];
    failed: number;
    skipped: number;
  }>('/api/core/permission/batch/create-from-routes', data);
}

/**
 * 从 Router 自动扫描并生成权限
 */
export async function autoScanPermissionsApi(dryRun: boolean = false) {
  return requestClient.post<{
    created: number;
    failed: number;
    permissions: any[];
    skipped: number;
  }>('/api/core/permission/auto/scan', { dry_run: dryRun });
}
