import { requestClient } from '#/api/request';

/**
 * 应用管理 API
 * 低代码平台的顶层容器，管理表单、页面、工作流等资源
 */

// ============ 类型定义 ============

/** 应用类型 */
export type AppType =
  | 'ai'
  | 'dashboard'
  | 'form'
  | 'mixed'
  | 'screen'
  | 'workflow';

/** 应用状态 */
export type AppStatus = 'disabled' | 'draft' | 'published';

/** 应用信息 */
export interface Application {
  id: string;
  name: string;
  code: string;
  description: string;
  icon: string;
  cover: string;
  app_type: AppType;
  status: AppStatus;
  home_path: null | string;
  version: number;
  config: Record<string, any>;
  owner_id: null | string;
  team_ids: string[];
  system_menu_ids: string[];
  sort: number;
  is_deleted: boolean;
  sys_create_datetime: string;
  sys_update_datetime: string;
}

/** 应用列表项 */
export interface ApplicationListItem {
  id: string;
  name: string;
  code: string;
  description: string;
  icon: string;
  cover: string;
  app_type: AppType;
  status: AppStatus;
  home_path: null | string;
  version: number;
  owner_id: null | string;
  system_menu_ids: string[];
  sys_create_datetime: string;
}

/** 创建应用请求 */
export interface ApplicationCreateInput {
  name: string;
  code: string;
  description?: string;
  icon?: string;
  cover?: string;
  app_type?: AppType;
  home_path?: string;
  config?: Record<string, any>;
  system_menu_ids?: string[];
}

/** 更新应用请求 */
export interface ApplicationUpdateInput {
  name?: string;
  code?: string;
  description?: string;
  icon?: string;
  cover?: string;
  app_type?: AppType;
  home_path?: string;
  status?: AppStatus;
  config?: Record<string, any>;
  team_ids?: string[];
  system_menu_ids?: string[];
}

/** 列表查询参数 */
export interface ApplicationListParams {
  page?: number;
  pageSize?: number;
  keyword?: string;
  appType?: AppType;
  status?: AppStatus;
}

/** 分页响应 */
interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

/** 统计信息 */
export interface ApplicationStats {
  total: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
}

// ============ 应用管理 API ============

/**
 * 获取应用列表（分页）
 */
export async function getApplicationListApi(params?: ApplicationListParams) {
  return requestClient.get<PaginatedResponse<ApplicationListItem>>(
    '/api/core/applications/',
    { params },
  );
}

/**
 * 获取应用统计信息
 */
export async function getApplicationStatsApi() {
  return requestClient.get<{ data: ApplicationStats }>(
    '/api/core/applications/stats',
  );
}

/**
 * 检查字段唯一性
 */
export async function checkApplicationUniqueApi(
  field: 'code' | 'name',
  value: string,
  excludeId?: string,
) {
  return requestClient.get<{ data: { unique: boolean } }>(
    '/api/core/applications/check/unique',
    {
      params: { field, value, excludeId },
    },
  );
}

/**
 * 根据编码获取应用
 */
export async function getApplicationByCodeApi(code: string) {
  return requestClient.get<Application>(`/api/core/applications/code/${code}`);
}

/**
 * 获取应用详情
 */
export async function getApplicationDetailApi(id: string) {
  return requestClient.get<Application>(`/api/core/applications/${id}`);
}

/**
 * 创建应用
 */
export async function createApplicationApi(data: ApplicationCreateInput) {
  return requestClient.post<Application>('/api/core/applications/', data);
}

/**
 * 更新应用
 */
export async function updateApplicationApi(
  id: string,
  data: ApplicationUpdateInput,
) {
  return requestClient.put<Application>(`/api/core/applications/${id}`, data);
}

/**
 * 发布应用
 */
export async function publishApplicationApi(id: string) {
  return requestClient.post<Application>(
    `/api/core/applications/${id}/publish`,
  );
}

/**
 * 停用应用
 */
export async function disableApplicationApi(id: string) {
  return requestClient.post<Application>(
    `/api/core/applications/${id}/disable`,
  );
}

/**
 * 删除应用
 */
export async function deleteApplicationApi(id: string, hard = false) {
  return requestClient.delete(`/api/core/applications/${id}`, {
    params: { hard },
  });
}
