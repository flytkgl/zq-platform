/**
 * 设备管理 API
 */
import { requestClient } from '#/api/request';

export namespace DeviceApi {
  /** 设备信息 */
  export interface DeviceInfo {
    device_id: string;
    device_name?: string;
    device_type?: string;
    browser_type?: string;
    os_type?: string;
    ip_address?: string;
    last_active_time?: string;
    is_current: boolean;
    is_online: boolean;
  }

  /** 设备列表响应 */
  export interface DeviceListResponse {
    current_device?: DeviceInfo;
    online_devices: DeviceInfo[];
    total_count: number;
  }

  /** 设备重命名请求 */
  export interface DeviceRenameRequest {
    device_name: string;
  }

  /** 统计信息响应 */
  export interface StatisticsResponse {
    online_count: number;
    total_count: number;
  }
}

/**
 * 获取设备列表
 */
export async function getDeviceListApi() {
  return requestClient.get<DeviceApi.DeviceListResponse>('/api/core/devices');
}

/**
 * 强制登出指定设备
 */
export async function logoutDeviceApi(deviceId: string) {
  return requestClient.delete(`/api/core/devices/${deviceId}`);
}

/**
 * 登出其他所有设备
 */
export async function logoutOtherDevicesApi() {
  return requestClient.delete('/api/core/devices/logout-others');
}

/**
 * 重命名设备
 */
export async function renameDeviceApi(
  deviceId: string,
  data: DeviceApi.DeviceRenameRequest,
) {
  return requestClient.post(`/api/core/devices/${deviceId}/rename`, data);
}

/**
 * 获取设备统计信息
 */
export async function getDeviceStatisticsApi() {
  return requestClient.get<DeviceApi.StatisticsResponse>(
    '/api/core/devices/statistics',
  );
}
