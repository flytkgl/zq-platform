import { requestClient } from '#/api/request';

export interface TestConnectionParams {
  corp_id?: string;
  corp_secret?: string;
}

export interface WecomSyncConfig {
  callback_aes_key?: string;
  callback_token?: string;
  callback_url?: string;
  corp_id?: string;
  corp_secret?: string;
  sync_dept_id?: string;
  sync_root_dept_id?: string;
  enable_dept_event?: string;
  enable_user_event?: string;
}

export interface CallbackStatus {
  registered: boolean;
  callback_url?: string;
  subscribed_events?: string[];
}

export interface SyncTypeStats {
  total_count: number;
  success_count: number;
  fail_count: number;
  not_synced: number;
  status: null | string;
  sync_time: null | string;
}

export interface SyncStats {
  dept: SyncTypeStats;
  user: SyncTypeStats;
}

export interface WecomDeptTreeNode {
  dept_id: number;
  name: string;
  children?: WecomDeptTreeNode[];
}

export async function testConnectionApi(data: TestConnectionParams) {
  return requestClient.post('/api/core/wecom-sync/test-connection', data);
}

export async function getSyncConfigApi() {
  return requestClient.get<Record<string, any>>(
    '/api/core/wecom-sync/config',
  );
}

export async function updateSyncConfigApi(data: WecomSyncConfig) {
  return requestClient.put('/api/core/wecom-sync/config', data);
}

export async function syncDeptApi() {
  return requestClient.post('/api/core/wecom-sync/sync/dept');
}

export async function syncUserApi() {
  return requestClient.post('/api/core/wecom-sync/sync/user');
}

export async function getSyncStatsApi() {
  return requestClient.get<SyncStats>('/api/core/wecom-sync/stats');
}

export async function getDeptTreeApi(data?: TestConnectionParams) {
  return requestClient.post<WecomDeptTreeNode[]>(
    '/api/core/wecom-sync/dept-tree',
    data || {},
  );
}

export async function getCallbackStatusApi() {
  return requestClient.get<CallbackStatus>(
    '/api/core/wecom-sync/callback/status',
  );
}
