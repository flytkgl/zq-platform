import { requestClient } from '#/api/request';

/**
 * 服务器监控相关类型定义
 */

// 基础信息
export interface BasicInfo {
  hostname: string;
  ip_address: string;
  system: string;
  platform: string;
  architecture: string;
  processor: string;
  python_version: string;
  machine: string;
  node: string;
  release: string;
  version: string;
}

// CPU信息
export interface CpuInfo {
  physical_cores: number;
  total_cores: number;
  cpu_percent: number;
  cpu_percent_per_core: number[];
  max_frequency: number;
  min_frequency: number;
  current_frequency: number;
  cpu_times: Record<string, any>;
  cpu_stats: Record<string, any>;
}

// 内存信息
export interface MemoryVirtual {
  total: number;
  available: number;
  used: number;
  free: number;
  percent: number;
  active: number;
  inactive: number;
  buffers: number;
  cached: number;
  shared: number;
}

export interface MemorySwap {
  total: number;
  used: number;
  free: number;
  percent: number;
  sin: number;
  sout: number;
}

export interface MemoryInfo {
  virtual: MemoryVirtual;
  swap: MemorySwap;
}

// 磁盘信息
export interface DiskPartition {
  device: string;
  mountpoint: string;
  file_system: string;
  total_size: number;
  used: number;
  free: number;
  percent: number;
}

export interface DiskInfo {
  partitions: DiskPartition[];
  total_read_bytes: number;
  total_write_bytes: number;
  total_read_count: number;
  total_write_count: number;
  total_read_time?: number;
  total_write_time?: number;
}

// 网络信息
export interface NetworkTotal {
  bytes_sent: number;
  bytes_recv: number;
  packets_sent: number;
  packets_recv: number;
  errin: number;
  errout: number;
  dropin: number;
  dropout: number;
}

export interface NetworkInterfaceStats {
  bytes_sent: number;
  bytes_recv: number;
  packets_sent: number;
  packets_recv: number;
  errin: number;
  errout: number;
  dropin: number;
  dropout: number;
}

export interface NetworkAddress {
  family: string;
  address: string;
  netmask?: string;
  broadcast?: string;
}

export interface NetworkInterfaceStatsDetail {
  is_up: boolean;
  duplex: string;
  speed: number;
  mtu: number;
}

export interface NetworkInterface {
  addresses: NetworkAddress[];
  stats: NetworkInterfaceStatsDetail;
}

export interface NetworkConnection {
  local_address: string;
  status: string;
  pid?: number;
}

export interface NetworkInfo {
  total: NetworkTotal;
  per_interface: Record<string, NetworkInterfaceStats>;
  interfaces: Record<string, NetworkInterface>;
  connections: NetworkConnection[];
}

// 进程信息
export interface Process {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_percent: number;
  status: string;
  create_time: string;
}

export interface ProcessInfo {
  total_processes: number;
  top_processes: Process[];
  running_processes: number;
  sleeping_processes: number;
}

// 系统负载
export interface SystemLoad {
  load_1min: number;
  load_5min: number;
  load_15min: number;
  cpu_count: number;
}

// 启动时间
export interface BootTime {
  boot_time: string;
  uptime_seconds: number;
  uptime_formatted: string;
  uptime_days: number;
  uptime_hours: number;
  uptime_minutes: number;
}

// 用户信息
export interface UserInfo {
  name: string;
  terminal?: string;
  host?: string;
  started?: string;
  pid?: number;
}

// 电池信息
export interface BatteryInfo {
  percent: number;
  power_plugged: boolean;
  seconds_left?: number;
}

// 实时统计
export interface RealtimeStats {
  cpu_percent: number;
  memory_percent: number;
  disk_io: {
    read_speed: number;
    write_speed: number;
  };
  network_io: {
    download_speed: number;
    upload_speed: number;
  };
  network_total: {
    bytes_recv: number;
    bytes_sent: number;
  };
  disk_total: {
    read_bytes: number;
    write_bytes: number;
  };
  cpu_details: Record<string, any>;
  memory_details: Record<string, number>;
  system_load: Record<string, number>;
  process_stats: Record<string, number>;
  process_info: ProcessInfo;
  network_interfaces: Record<string, Record<string, number>>;
  network_connections: Array<Record<string, any>>;
  timestamp: string;
}

// 服务器监控完整响应
export interface ServerMonitorResponse {
  basic_info: BasicInfo;
  cpu_info: CpuInfo;
  memory_info: MemoryInfo;
  disk_info: DiskInfo;
  network_info: NetworkInfo;
  process_info: ProcessInfo;
  system_load: SystemLoad;
  boot_time: BootTime;
  users_info: UserInfo[];
  timestamp: string;
}

/**
 * API调用函数
 */

/**
 * 获取服务器完整监控信息
 */
export async function getServerOverviewApi() {
  return requestClient.get<ServerMonitorResponse>(
    '/api/core/server_monitor/overview',
  );
}

/**
 * 获取实时统计信息
 */
export async function getRealtimeStatsApi() {
  return requestClient.get<RealtimeStats>('/api/core/server_monitor/realtime');
}

/**
 * 获取基础系统信息
 */
export async function getBasicInfoApi() {
  return requestClient.get<BasicInfo>('/api/core/server_monitor/basic_info');
}

/**
 * 获取CPU信息
 */
export async function getCpuInfoApi() {
  return requestClient.get<CpuInfo>('/api/core/server_monitor/cpu_info');
}

/**
 * 获取内存信息
 */
export async function getMemoryInfoApi() {
  return requestClient.get<MemoryInfo>('/api/core/server_monitor/memory_info');
}

/**
 * 获取磁盘信息
 */
export async function getDiskInfoApi() {
  return requestClient.get<DiskInfo>('/api/core/server_monitor/disk_info');
}

/**
 * 获取网络信息
 */
export async function getNetworkInfoApi() {
  return requestClient.get<NetworkInfo>(
    '/api/core/server_monitor/network_info',
  );
}

/**
 * 获取进程信息
 */
export async function getProcessInfoApi() {
  return requestClient.get<ProcessInfo>(
    '/api/core/server_monitor/process_info',
  );
}

/**
 * 获取系统负载信息
 */
export async function getSystemLoadApi() {
  return requestClient.get<SystemLoad>('/api/core/server_monitor/system_load');
}

/**
 * 获取系统启动时间信息
 */
export async function getBootTimeApi() {
  return requestClient.get<BootTime>('/api/core/server_monitor/boot_time');
}

/**
 * 获取用户信息
 */
export async function getUsersInfoApi() {
  return requestClient.get<UserInfo[]>('/api/core/server_monitor/users_info');
}

/**
 * 获取温度信息
 */
export async function getTemperatureInfoApi() {
  return requestClient.get<Record<string, any>>(
    '/api/core/server_monitor/temperature_info',
  );
}

/**
 * 获取电池信息
 */
export async function getBatteryInfoApi() {
  return requestClient.get<BatteryInfo>(
    '/api/core/server_monitor/battery_info',
  );
}
