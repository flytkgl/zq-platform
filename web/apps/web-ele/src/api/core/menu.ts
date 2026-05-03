import type { RouteRecordStringComponent } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * 菜单相关类型定义
 */
export interface Menu {
  id: string;
  application_id?: string;
  is_system?: boolean;
  parent_id?: string;
  name: string;
  title?: string;
  authCode?: string;
  path: string;
  type: string;
  component?: string;
  redirect?: string;
  activePath?: string;
  query?: Record<string, any>;
  noBasicLayout?: boolean;
  icon?: string;
  activeIcon?: string;
  order: number;
  hideInMenu?: boolean;
  hideChildrenInMenu?: boolean;
  hideInBreadcrumb?: boolean;
  hideInTab?: boolean;
  affixTab?: boolean;
  affixTabOrder?: number;
  keepAlive?: boolean;
  maxNumOfOpenTab?: number;
  fullPathKey?: boolean;
  link?: string;
  iframeSrc?: string;
  openInNewWindow?: boolean;
  badge?: string;
  badgeType?: string;
  badgeVariants?: string;
  level?: number;
  child_count?: number;
  full_path?: string;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface MenuTreeNode extends Menu {
  children?: MenuTreeNode[];
}

export interface MenuCreateInput {
  application_id?: string;
  is_system?: boolean;
  parent_id?: string;
  name: string;
  title?: string;
  authCode?: string;
  path: string;
  type: string;
  component?: string;
  redirect?: string;
  activePath?: string;
  query?: Record<string, any>;
  noBasicLayout?: boolean;
  icon?: string;
  activeIcon?: string;
  order?: number;
  hideInMenu?: boolean;
  hideChildrenInMenu?: boolean;
  hideInBreadcrumb?: boolean;
  hideInTab?: boolean;
  affixTab?: boolean;
  affixTabOrder?: number;
  keepAlive?: boolean;
  maxNumOfOpenTab?: number;
  fullPathKey?: boolean;
  link?: string;
  iframeSrc?: string;
  openInNewWindow?: boolean;
  badge?: string;
  badgeType?: string;
  badgeVariants?: string;
}

export interface MenuUpdateInput extends Partial<MenuCreateInput> {}

export interface MenuMoveInput {
  target_parent_id?: string;
  position?: number;
}

export interface MenuListParams {
  page?: number;
  pageSize?: number;
  name?: string;
  title?: string;
  type?: string;
  parent_id?: string;
  applicationId?: string;
}

export interface MenuStats {
  total_count: number;
  type_counts: Record<string, number>;
  max_level: number;
  type_choices: Array<[string, string]>;
}

/**
 * 获取用户所有菜单（路由树）
 * @param applicationCode 应用编码，用于过滤应用专属菜单
 * @param devMode 开发模式：true只返回系统菜单，false只返回应用菜单
 */
export async function getAllMenusApi(
  applicationCode?: string,
  devMode?: boolean,
) {
  const params: Record<string, any> = {};
  if (applicationCode) {
    params.application_code = applicationCode;
  }
  if (devMode !== undefined) {
    params.devMode = devMode;
  }
  return requestClient.get<RouteRecordStringComponent[]>(
    '/api/core/menu/route/tree',
    { params },
  );
}

/**
 * 获取用户路由树（Core 版本）
 */
export async function getUserRouteTreeApi() {
  return requestClient.get<MenuTreeNode[]>('/api/core/menu/user_route_tree');
}

/**
 * 创建菜单
 */
export async function createMenuApi(data: MenuCreateInput) {
  return requestClient.post<Menu>('/api/core/menu', data);
}

/**
 * 获取菜单列表（分页）
 */
export async function getMenuListApi(params?: MenuListParams) {
  return requestClient.get<Menu[]>('/api/core/menu', { params });
}

/**
 * 获取所有菜单（树形结构）
 */
export async function getAllMenuTreeApi(
  applicationId?: string,
  useCache: boolean = true,
  includeSystem: boolean = true,
) {
  const params: any = { use_cache: useCache, includeSystem };
  if (applicationId) {
    params.applicationId = applicationId;
  }
  return requestClient.get<MenuTreeNode[]>('/api/core/menu/get/tree', {
    params,
  });
}

/**
 * 获取菜单详情
 */
export async function getMenuDetailApi(menuId: string) {
  return requestClient.get<Menu>(`/api/core/menu/${menuId}`);
}

/**
 * 更新菜单
 */
export async function updateMenuApi(menuId: string, data: MenuUpdateInput) {
  return requestClient.put<Menu>(`/api/core/menu/${menuId}`, data);
}

/**
 * 删除菜单
 */
export async function deleteMenuApi(menuId: string) {
  return requestClient.delete<Menu>(`/api/core/menu/${menuId}`);
}

/**
 * 根据父菜单ID获取子菜单
 */
export async function getMenuByParentApi(parentId?: string) {
  // 后端使用 "null" 字符串表示根菜单
  const id = parentId || 'null';
  return requestClient.get<Menu[]>(`/api/core/menu/by/parent/${id}`);
}

/**
 * 搜索菜单
 */
export async function searchMenuApi(keyword: string) {
  return requestClient.get<Menu[]>('/api/core/menu/search', {
    params: { keyword },
  });
}

/**
 * 移动菜单
 */
export async function moveMenuApi(menuId: string, data: MenuMoveInput) {
  return requestClient.post<Menu>(`/api/core/menu/${menuId}/move`, data);
}

/**
 * 获取菜单路径
 */
export async function getMenuPathApi(menuId: string) {
  return requestClient.get<Menu[]>(`/api/core/menu/${menuId}/path`);
}

/**
 * 获取菜单统计信息
 */
export async function getMenuStatsApi() {
  return requestClient.get<MenuStats>('/api/core/menu/stats');
}

/**
 * 检查菜单名称是否存在
 */
export async function checkMenuNameApi(
  name: string,
  excludeId?: string,
  applicationId?: string,
) {
  const params = applicationId ? { applicationId } : {};
  return requestClient.post<{ exists: boolean; message?: string }>(
    '/api/core/menu/check/name',
    { name, exclude_id: excludeId },
    { params },
  );
}

/**
 * 检查路由路径是否存在
 */
export async function checkMenuPathApi(
  path: string,
  excludeId?: string,
  applicationId?: string,
) {
  const params = applicationId ? { applicationId } : {};
  return requestClient.post<{ exists: boolean; message?: string }>(
    '/api/core/menu/check/path',
    { path, exclude_id: excludeId },
    { params },
  );
}
