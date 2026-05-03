import { requestClient } from '#/api/request';

/**
 * 资源数据权限配置相关类型定义
 */

// 资源类型信息
export interface ResourceType {
  resource_type: string;
  display_name: string;
  model_name?: string;
  table_name?: string;
}

// 资源权限配置
export interface ResourceScopeConfig {
  id?: string;
  role_id: string;
  resource_type: string;
  data_scope: number;
  dept_ids?: null | string[];
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

// 角色资源权限配置（用于批量更新）
export interface RoleResourceScopeConfig {
  resource_type: string;
  data_scope: number;
  dept_ids?: null | string[];
}

export interface RoleResourceScopeBatchUpdate {
  role_id: string;
  configs: RoleResourceScopeConfig[];
}

// 数据权限范围选项
export const DATA_SCOPE_OPTIONS = [
  { label: '全部数据', value: 0 },
  { label: '仅本人数据', value: 1 },
  { label: '本部门数据', value: 2 },
  { label: '本部门及下级部门数据', value: 3 },
  { label: '自定义数据', value: 4 },
];

/**
 * 获取所有资源类型
 * @param applicationId 应用ID，子应用访问时只显示该应用的资源
 */
export async function getResourceTypesApi(applicationId?: string) {
  return requestClient.get<ResourceType[]>('/api/core/resource-scope/types', {
    params: applicationId ? { applicationId } : undefined,
  });
}

/**
 * 获取资源类型列表（简单）
 */
export async function getResourceTypeListApi() {
  return requestClient.get<string[]>('/api/core/resource-scope/types/list');
}

/**
 * 获取注册表信息
 */
export async function getRegistryInfoApi() {
  return requestClient.get<{
    data: {
      resource_types: string[];
      resources: ResourceType[];
      total_count: number;
    };
    message: string;
  }>('/api/core/resource-scope/registry/info');
}

/**
 * 获取角色的资源权限配置
 */
export async function getRoleResourceScopesApi(roleId: string) {
  return requestClient.get<ResourceScopeConfig[]>(
    `/api/core/resource-scope/role/${roleId}`,
  );
}

/**
 * 批量更新角色的资源权限配置
 */
export async function batchUpdateRoleResourceScopesApi(
  data: RoleResourceScopeBatchUpdate,
) {
  return requestClient.put<ResourceScopeConfig[]>(
    '/api/core/resource-scope/role/batch',
    data,
  );
}

/**
 * 创建资源权限配置
 */
export async function createResourceScopeConfigApi(
  data: Omit<ResourceScopeConfig, 'id'>,
) {
  return requestClient.post<ResourceScopeConfig>(
    '/api/core/resource-scope',
    data,
  );
}

/**
 * 更新资源权限配置
 */
export async function updateResourceScopeConfigApi(
  configId: string,
  data: Partial<ResourceScopeConfig>,
) {
  return requestClient.put<ResourceScopeConfig>(
    `/api/core/resource-scope/${configId}`,
    data,
  );
}

/**
 * 删除资源权限配置
 */
export async function deleteResourceScopeConfigApi(configId: string) {
  return requestClient.delete(`/api/core/resource-scope/${configId}`);
}
