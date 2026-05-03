import { requestClient } from '#/api/request';

/**
 * UI配置相关类型定义
 */
export interface UIConfig {
  id: string;
  config_key: string;
  config_value?: string;
  config_type: string;
  description?: string;
  status: boolean;
  sort: number;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface UIConfigCreateInput {
  config_key: string;
  config_value?: string;
  config_type?: string;
  description?: string;
  status?: boolean;
  sort?: number;
}

export interface UIConfigUpdateInput extends Partial<UIConfigCreateInput> {}

export interface UIConfigListParams {
  page?: number;
  pageSize?: number;
  configKey?: string;
  configType?: string;
  status?: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

export interface LoginConfig {
  enableThirdPartyLogin?: boolean;
  enabledProviders?: string[];
}

export interface PreferencesConfig {
  app?: Record<string, any>;
  theme?: Record<string, any>;
  logo?: Record<string, any>;
  copyright?: Record<string, any>;
  sidebar?: Record<string, any>;
  header?: Record<string, any>;
  footer?: Record<string, any>;
  tabbar?: Record<string, any>;
  breadcrumb?: Record<string, any>;
  navigation?: Record<string, any>;
  shortcutKeys?: Record<string, any>;
  transition?: Record<string, any>;
  widget?: Record<string, any>;
  loginConfig?: LoginConfig;
}

// ============ 前端偏好配置API ============

/**
 * 获取前端偏好配置（无需认证）
 * @param applicationId 应用ID，不传则获取主应用配置
 */
export async function getPreferencesConfigApi(applicationId?: string) {
  return requestClient.get<PreferencesConfig>(
    '/api/core/ui_config/preferences',
    {
      params: applicationId ? { applicationId } : undefined,
    },
  );
}

/**
 * 更新前端偏好配置
 * @param data 配置数据
 * @param applicationId 应用ID，不传则更新主应用配置
 */
export async function updatePreferencesConfigApi(
  data: PreferencesConfig,
  applicationId?: string,
) {
  return requestClient.put<{ id: string }>(
    '/api/core/ui_config/preferences',
    data,
    {
      params: applicationId ? { applicationId } : undefined,
    },
  );
}

// ============ UI配置CRUD API ============

/**
 * 创建UI配置
 */
export async function createUIConfigApi(data: UIConfigCreateInput) {
  return requestClient.post<UIConfig>('/api/core/ui_config', data);
}

/**
 * 获取UI配置列表（分页）
 */
export async function getUIConfigListApi(params?: UIConfigListParams) {
  return requestClient.get<PaginatedResponse<UIConfig>>('/api/core/ui_config', {
    params,
  });
}

/**
 * 获取所有UI配置（不分页）
 */
export async function getAllUIConfigApi() {
  return requestClient.get<UIConfig[]>('/api/core/ui_config/all');
}

/**
 * 获取UI配置详情
 */
export async function getUIConfigDetailApi(configId: string) {
  return requestClient.get<UIConfig>(`/api/core/ui_config/${configId}`);
}

/**
 * 根据配置键获取UI配置
 */
export async function getUIConfigByKeyApi(configKey: string) {
  return requestClient.get<UIConfig>(`/api/core/ui_config/by/key/${configKey}`);
}

/**
 * 根据配置类型获取UI配置列表
 */
export async function getUIConfigByTypeApi(configType: string) {
  return requestClient.get<UIConfig[]>(
    `/api/core/ui_config/by/type/${configType}`,
  );
}

/**
 * 获取配置值
 */
export async function getUIConfigValueApi(configKey: string) {
  return requestClient.get<any>(`/api/core/ui_config/value/${configKey}`);
}

/**
 * 更新配置值
 */
export async function updateUIConfigValueApi(
  configKey: string,
  configValue: string,
) {
  return requestClient.put(`/api/core/ui_config/value/${configKey}`, {
    config_value: configValue,
  });
}

/**
 * 更新UI配置
 */
export async function updateUIConfigApi(
  configId: string,
  data: UIConfigUpdateInput,
) {
  return requestClient.put<UIConfig>(`/api/core/ui_config/${configId}`, data);
}

/**
 * 删除UI配置
 */
export async function deleteUIConfigApi(configId: string) {
  return requestClient.delete(`/api/core/ui_config/${configId}`);
}

/**
 * 检查配置键唯一性
 */
export async function checkUIConfigUniqueApi(
  field: string,
  value: string,
  excludeId?: string,
) {
  return requestClient.get<{ unique: boolean }>(
    '/api/core/ui_config/check/unique',
    {
      params: { field, value, excludeId },
    },
  );
}
