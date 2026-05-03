import { requestClient } from '#/api/request';

/**
 * 配置分组定义
 */
export interface ConfigGroupDef {
  key: string;
  fields: string[];
}

/**
 * 分组配置更新参数
 */
export interface GroupConfigUpdateInput {
  configs: Record<string, null | string>;
}

/**
 * 获取所有配置分组定义
 */
export async function getConfigGroupsApi() {
  return requestClient.get<ConfigGroupDef[]>('/api/core/system-config/groups');
}

/**
 * 获取所有分组配置（敏感字段脱敏）
 */
export async function getAllConfigsApi() {
  return requestClient.get<Record<string, Record<string, any>>>(
    '/api/core/system-config/all',
  );
}

/**
 * 获取指定分组配置
 */
export async function getGroupConfigApi(group: string) {
  return requestClient.get<Record<string, any>>(
    `/api/core/system-config/group/${group}`,
  );
}

/**
 * 更新指定分组配置
 */
export async function updateGroupConfigApi(
  group: string,
  data: GroupConfigUpdateInput,
) {
  return requestClient.put(`/api/core/system-config/group/${group}`, data);
}

/**
 * 删除指定分组配置（恢复默认）
 */
export async function deleteGroupConfigApi(group: string) {
  return requestClient.delete(`/api/core/system-config/group/${group}`);
}

/**
 * 预热配置缓存
 */
export async function warmupCacheApi() {
  return requestClient.post('/api/core/system-config/cache/warmup');
}

/**
 * 清除配置缓存
 */
export async function clearCacheApi() {
  return requestClient.delete('/api/core/system-config/cache');
}
