/**
 * Redis管理API
 */
import { requestClient } from '#/api/request';

// ==================== 类型定义 ====================

/**
 * Redis键信息
 */
export interface RedisKey {
  key: string;
  type: 'hash' | 'list' | 'set' | 'string' | 'zset';
  ttl: number; // -1表示永不过期，-2表示已过期
  size?: number;
  length?: number;
  encoding?: string;
}

/**
 * Redis键详情
 */
export interface RedisKeyDetail {
  key: string;
  type: 'hash' | 'list' | 'set' | 'string' | 'zset';
  ttl: number;
  value: any;
  size?: number;
  encoding?: string;
  created_at?: string;
}

/**
 * Redis数据库信息
 */
export interface RedisDatabase {
  db_index: number;
  keys_count: number;
  expires_count: number;
  avg_ttl: number;
}

/**
 * 数据库列表响应
 */
export interface RedisDatabaseListResponse {
  databases: RedisDatabase[];
  total_keys: number;
}

/**
 * 键列表响应
 */
export interface RedisKeyListResponse {
  total: number;
  keys: RedisKey[];
  page: number;
  page_size: number;
}

/**
 * 键搜索参数
 */
export interface RedisKeySearchParams {
  pattern?: string;
  key_type?: string;
  page?: number;
  page_size?: number;
}

/**
 * 创建键参数
 */
export interface RedisKeyCreateParams {
  key: string;
  type: 'hash' | 'list' | 'set' | 'string' | 'zset';
  value: any;
  ttl?: number;
}

/**
 * 更新键参数
 */
export interface RedisKeyUpdateParams {
  value: any;
  ttl?: number;
}

/**
 * 重命名键参数
 */
export interface RedisKeyRenameParams {
  old_key: string;
  new_key: string;
}

/**
 * 设置过期时间参数
 */
export interface RedisKeyExpireParams {
  key: string;
  ttl: number;
}

/**
 * 批量删除参数
 */
export interface RedisBatchDeleteParams {
  keys: string[];
}

/**
 * 清空数据库参数
 */
export interface RedisFlushDBParams {
  db_index: number;
  confirm: boolean;
}

/**
 * 操作响应
 */
export interface RedisOperationResponse {
  success: boolean;
  message: string;
  data?: any;
}

// ==================== API接口 ====================

/**
 * 获取所有Redis数据库信息
 */
export async function getRedisDatabasesApi() {
  return requestClient.get<RedisDatabaseListResponse>(
    '/api/core/redis_manager/databases',
  );
}

/**
 * 搜索Redis键
 */
export async function searchRedisKeysApi(
  dbIndex: number,
  params: RedisKeySearchParams,
) {
  return requestClient.post<RedisKeyListResponse>(
    `/api/core/redis_manager/${dbIndex}/keys/search`,
    params,
  );
}

/**
 * 获取Redis键详情
 */
export async function getRedisKeyDetailApi(dbIndex: number, key: string) {
  return requestClient.get<RedisKeyDetail>(
    `/api/core/redis_manager/${dbIndex}/keys/${encodeURIComponent(key)}`,
  );
}

/**
 * 创建Redis键
 */
export async function createRedisKeyApi(
  dbIndex: number,
  data: RedisKeyCreateParams,
) {
  return requestClient.post<RedisOperationResponse>(
    `/api/core/redis_manager/${dbIndex}/keys`,
    data,
  );
}

/**
 * 更新Redis键
 */
export async function updateRedisKeyApi(
  dbIndex: number,
  key: string,
  data: RedisKeyUpdateParams,
) {
  return requestClient.put<RedisOperationResponse>(
    `/api/core/redis_manager/${dbIndex}/keys/${encodeURIComponent(key)}`,
    data,
  );
}

/**
 * 删除Redis键
 */
export async function deleteRedisKeyApi(dbIndex: number, key: string) {
  return requestClient.delete<RedisOperationResponse>(
    `/api/core/redis_manager/${dbIndex}/keys/${encodeURIComponent(key)}`,
  );
}

/**
 * 批量删除Redis键
 */
export async function batchDeleteRedisKeysApi(
  dbIndex: number,
  data: RedisBatchDeleteParams,
) {
  return requestClient.post<RedisOperationResponse>(
    `/api/core/redis_manager/${dbIndex}/keys/batch-delete`,
    data,
  );
}

/**
 * 重命名Redis键
 */
export async function renameRedisKeyApi(
  dbIndex: number,
  data: RedisKeyRenameParams,
) {
  return requestClient.post<RedisOperationResponse>(
    `/api/core/redis_manager/${dbIndex}/keys/rename`,
    data,
  );
}

/**
 * 设置Redis键过期时间
 */
export async function setRedisKeyExpireApi(
  dbIndex: number,
  data: RedisKeyExpireParams,
) {
  return requestClient.post<RedisOperationResponse>(
    `/api/core/redis_manager/${dbIndex}/keys/expire`,
    data,
  );
}

/**
 * 清空Redis数据库
 */
export async function flushRedisDBApi(
  dbIndex: number,
  data: RedisFlushDBParams,
) {
  return requestClient.post<RedisOperationResponse>(
    `/api/core/redis_manager/${dbIndex}/flush`,
    data,
  );
}
