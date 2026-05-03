import { requestClient } from '#/api/request';

/**
 * 连接测试请求
 */
export interface TestConnectionParams {
  app_key?: string;
  app_secret?: string;
}

/**
 * 同步配置
 */
export interface DingtalkSyncConfig {
  callback_aes_key?: string;
  callback_token?: string;
  callback_url?: string;
  corp_id?: string;
  app_key?: string;
  app_secret?: string;
  sync_dept_id?: string;
  sync_root_dept_id?: string;
  enable_dept_event?: string;
  enable_user_event?: string;
}

/**
 * 回调状态
 */
export interface CallbackStatus {
  registered: boolean;
  callback_url?: string;
  subscribed_events?: string[];
}

/**
 * 同步统计项
 */
export interface SyncTypeStats {
  total_count: number;
  success_count: number;
  fail_count: number;
  not_synced: number;
  status: null | string;
  sync_time: null | string;
}

/**
 * 同步统计
 */
export interface SyncStats {
  dept: SyncTypeStats;
  user: SyncTypeStats;
}

/**
 * 钉钉部门树节点
 */
export interface DingtalkDeptTreeNode {
  dept_id: number;
  name: string;
  children?: DingtalkDeptTreeNode[];
}

/**
 * 连接测试
 */
export async function testConnectionApi(data: TestConnectionParams) {
  return requestClient.post('/api/core/dingtalk-sync/test-connection', data);
}

/**
 * 获取同步配置
 */
export async function getSyncConfigApi() {
  return requestClient.get<Record<string, any>>(
    '/api/core/dingtalk-sync/config',
  );
}

/**
 * 保存同步配置
 */
export async function updateSyncConfigApi(data: DingtalkSyncConfig) {
  return requestClient.put('/api/core/dingtalk-sync/config', data);
}

/**
 * 同步组织架构
 */
export async function syncDeptApi() {
  return requestClient.post('/api/core/dingtalk-sync/sync/dept');
}

/**
 * 同步用户
 */
export async function syncUserApi() {
  return requestClient.post('/api/core/dingtalk-sync/sync/user');
}

/**
 * 获取同步统计
 */
export async function getSyncStatsApi() {
  return requestClient.get<SyncStats>('/api/core/dingtalk-sync/stats');
}

/**
 * 获取同步日志
 */
export async function getSyncLogsApi(page: number = 1, pageSize: number = 20) {
  return requestClient.get('/api/core/dingtalk-sync/logs', {
    params: { page, page_size: pageSize },
  });
}

/**
 * 获取钉钉部门树（选择同步范围）
 */
export async function getDeptTreeApi(data?: TestConnectionParams) {
  return requestClient.post<DingtalkDeptTreeNode[]>(
    '/api/core/dingtalk-sync/dept-tree',
    data || {},
  );
}

/**
 * 注册事件回调
 */
export async function registerCallbackApi() {
  return requestClient.post('/api/core/dingtalk-sync/callback/register');
}

/**
 * 删除事件回调
 */
export async function deleteCallbackApi() {
  return requestClient.delete('/api/core/dingtalk-sync/callback/register');
}

/**
 * 查询回调注册状态
 */
export async function getCallbackStatusApi() {
  return requestClient.get<CallbackStatus>(
    '/api/core/dingtalk-sync/callback/status',
  );
}
