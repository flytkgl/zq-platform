import { requestClient } from '#/api/request';

/**
 * 连接测试请求
 */
export interface TestConnectionParams {
  app_id?: string;
  app_secret?: string;
}

/**
 * 同步配置
 */
export interface FeishuSyncConfig {
  app_id?: string;
  app_secret?: string;
  sync_dept_id?: string;
  sync_root_dept_id?: string;
  enable_dept_event?: string;
  enable_user_event?: string;
  encrypt_key?: string;
  verification_token?: string;
  callback_url?: string;
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
 * 飞书部门树节点
 */
export interface FeishuDeptTreeNode {
  dept_id: string;
  name: string;
  children?: FeishuDeptTreeNode[];
}

/**
 * 连接测试
 */
export async function testConnectionApi(data: TestConnectionParams) {
  return requestClient.post('/api/core/feishu-sync/test-connection', data);
}

/**
 * 获取同步配置
 */
export async function getSyncConfigApi() {
  return requestClient.get<Record<string, any>>(
    '/api/core/feishu-sync/config',
  );
}

/**
 * 保存同步配置
 */
export async function updateSyncConfigApi(data: FeishuSyncConfig) {
  return requestClient.put('/api/core/feishu-sync/config', data);
}

/**
 * 同步组织架构
 */
export async function syncDeptApi() {
  return requestClient.post('/api/core/feishu-sync/sync/dept');
}

/**
 * 同步用户
 */
export async function syncUserApi() {
  return requestClient.post('/api/core/feishu-sync/sync/user');
}

/**
 * 获取同步统计
 */
export async function getSyncStatsApi() {
  return requestClient.get<SyncStats>('/api/core/feishu-sync/stats');
}

/**
 * 获取同步日志
 */
export async function getSyncLogsApi(page: number = 1, pageSize: number = 20) {
  return requestClient.get('/api/core/feishu-sync/logs', {
    params: { page, page_size: pageSize },
  });
}

/**
 * 获取飞书部门树（选择同步范围）
 */
export async function getDeptTreeApi(data?: TestConnectionParams) {
  return requestClient.post<FeishuDeptTreeNode[]>(
    '/api/core/feishu-sync/dept-tree',
    data || {},
  );
}

/**
 * 查询回调注册状态
 */
export async function getCallbackStatusApi() {
  return requestClient.get<CallbackStatus>(
    '/api/core/feishu-sync/callback/status',
  );
}
