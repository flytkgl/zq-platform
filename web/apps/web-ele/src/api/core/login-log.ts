import type { PaginatedResponse } from './user';

import { requestClient } from '#/api/request';

/**
 * 登录日志相关类型定义
 */
export interface LoginLog {
  id: string;
  user_id?: string;
  username: string;
  status: number;
  failure_reason?: number;
  failure_message?: string;
  login_ip: string;
  ip_location?: string;
  user_agent?: string;
  browser_type?: string;
  os_type?: string;
  device_type?: string;
  duration?: number;
  session_id?: string;
  remark?: string;
  status_display?: string;
  failure_reason_display?: string;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface LoginLogListParams {
  page?: number;
  pageSize?: number;
  username?: string;
  user_id?: string;
  status?: number;
  failure_reason?: number;
  login_ip?: string;
  device_type?: string;
  browser_type?: string;
  os_type?: string;
  start_datetime?: string;
  end_datetime?: string;
}

export interface LoginLogStats {
  total_logins: number;
  success_logins: number;
  failed_logins: number;
  success_rate: number;
  unique_users: number;
  unique_ips: number;
}

export interface LoginLogIpStats {
  login_ip: string;
  ip_location?: string;
  login_count: number;
  failed_count: number;
  last_login_time?: string;
}

export interface LoginLogDeviceStats {
  device_type?: string;
  browser_type?: string;
  os_type?: string;
  login_count: number;
  last_login_time?: string;
}

export interface LoginLogUserStats {
  user_id?: string;
  username: string;
  total_logins: number;
  failed_logins: number;
  last_login_time?: string;
  last_login_ip?: string;
}

export interface LoginLogDailyStats {
  date: string;
  total_logins: number;
  success_logins: number;
  failed_logins: number;
  unique_users: number;
}

export interface LoginLogBatchDeleteInput {
  ids: string[];
}

/**
 * 获取登录日志列表（分页）
 */
export async function getLoginLogListApi(params?: LoginLogListParams) {
  return requestClient.get<PaginatedResponse<LoginLog>>('/api/core/login-log', {
    params,
  });
}

/**
 * 获取登录日志详情
 */
export async function getLoginLogDetailApi(logId: string) {
  return requestClient.get<LoginLog>(`/api/core/login-log/${logId}`);
}

/**
 * 删除登录日志
 */
export async function deleteLoginLogApi(logId: string) {
  return requestClient.delete(`/api/core/login-log/${logId}`);
}

/**
 * 批量删除登录日志
 */
export async function batchDeleteLoginLogApi(ids: string[]) {
  return requestClient.delete('/api/core/login-log/batch/delete', {
    params: { ids },
  });
}

/**
 * 获取登录统计概览
 */
export async function getLoginStatsApi(days: number = 30) {
  return requestClient.get<LoginLogStats>(
    '/api/core/login-log/stats/overview',
    {
      params: { days },
    },
  );
}

/**
 * 获取IP登录统计
 */
export async function getIpStatsApi(days: number = 30, limit: number = 10) {
  return requestClient.get<LoginLogIpStats[]>('/api/core/login-log/stats/ip', {
    params: { days, limit },
  });
}

/**
 * 获取设备登录统计
 */
export async function getDeviceStatsApi(days: number = 30) {
  return requestClient.get<LoginLogDeviceStats[]>(
    '/api/core/login-log/stats/device',
    {
      params: { days },
    },
  );
}

/**
 * 获取用户登录统计
 */
export async function getUserStatsApi(days: number = 30, limit: number = 10) {
  return requestClient.get<LoginLogUserStats[]>(
    '/api/core/login-log/stats/user',
    {
      params: { days, limit },
    },
  );
}

/**
 * 获取每日登录统计
 */
export async function getDailyStatsApi(days: number = 30) {
  return requestClient.get<LoginLogDailyStats[]>(
    '/api/core/login-log/stats/daily',
    {
      params: { days },
    },
  );
}

/**
 * 获取用户的登录日志
 */
export async function getUserLoginLogsApi(
  userId: string,
  days: number = 30,
  page: number = 1,
  pageSize: number = 10,
) {
  return requestClient.get<PaginatedResponse<LoginLog>>(
    `/api/core/login-log/user/${userId}`,
    {
      params: { days, page, pageSize },
    },
  );
}

/**
 * 获取用户登录次数
 */
export async function getUserLoginCountApi(userId: string, days: number = 30) {
  return requestClient.get<{
    failed_logins: number;
    success_logins: number;
    total_logins: number;
    user_id: string;
  }>(`/api/core/login-log/user/${userId}/count`, {
    params: { days },
  });
}

/**
 * 获取用户最后一次登录
 */
export async function getUserLastLoginApi(userId: string) {
  return requestClient.get<LoginLog>(`/api/core/login-log/user/${userId}/last`);
}

/**
 * 获取用户登录过的IP地址
 */
export async function getUserLoginIpsApi(userId: string, days: number = 30) {
  return requestClient.get<{
    ip_count: number;
    ips: string[];
    user_id: string;
  }>(`/api/core/login-log/user/${userId}/ips`, {
    params: { days },
  });
}

/**
 * 获取可疑登录记录
 */
export async function getSuspiciousLoginsApi(
  failedThreshold: number = 5,
  hours: number = 1,
) {
  return requestClient.get<{
    records: any[];
    suspicious_count: number;
  }>('/api/core/login-log/suspicious', {
    params: { failed_threshold: failedThreshold, hours },
  });
}

/**
 * 清理旧的登录日志
 */
export async function cleanOldLogsApi(days: number = 90) {
  return requestClient.post<{ deleted_count: number }>(
    '/api/core/login-log/clean',
    {},
    {
      params: { days },
    },
  );
}

/**
 * 根据用户名获取登录日志
 */
export async function getLogsByUsernameApi(
  username: string,
  days: number = 30,
  page: number = 1,
  pageSize: number = 10,
) {
  return requestClient.get<PaginatedResponse<LoginLog>>(
    `/api/core/login-log/username/${username}`,
    {
      params: { days, page, pageSize },
    },
  );
}

/**
 * 根据IP地址获取登录日志
 */
export async function getLogsByIpApi(
  loginIp: string,
  days: number = 30,
  page: number = 1,
  pageSize: number = 10,
) {
  return requestClient.get<PaginatedResponse<LoginLog>>(
    `/api/core/login-log/ip/${loginIp}`,
    {
      params: { days, page, pageSize },
    },
  );
}

/**
 * 获取用户登录失败次数
 */
export async function getFailedAttemptsApi(
  username: string,
  hours: number = 1,
) {
  return requestClient.get<{
    failed_attempts: number;
    should_lock: boolean;
    username: string;
  }>(`/api/core/login-log/failed-attempts/${username}`, {
    params: { hours },
  });
}
