import { requestClient } from '#/api/request';

// Redis配置信息
export interface RedisConfig {
  host: string;
  port: number;
  database: number;
  has_password: boolean;
  redis_url: string;
}

// Redis基础信息
export interface RedisInfo {
  redis_version: string;
  redis_mode: string;
  role: string;
  os: string;
  arch_bits: number;
  uptime_in_seconds: number;
  uptime_in_days: number;
  tcp_port: number;
  connected_clients: number;
  blocked_clients: number;
}

// Redis内存信息
export interface RedisMemory {
  used_memory: number;
  used_memory_human: string;
  used_memory_rss: number;
  used_memory_peak: number;
  used_memory_peak_human: string;
  total_system_memory: number;
  total_system_memory_human: string;
  used_memory_dataset: number;
  used_memory_dataset_perc: string;
  allocator_allocated: number;
  allocator_active: number;
  maxmemory: number;
  maxmemory_human: string;
  maxmemory_policy: string;
  mem_fragmentation_ratio: number;
}

// Redis统计信息
export interface RedisStats {
  total_connections_received: number;
  total_commands_processed: number;
  instantaneous_ops_per_sec: number;
  total_net_input_bytes: number;
  total_net_output_bytes: number;
  instantaneous_input_kbps: number;
  instantaneous_output_kbps: number;
  rejected_connections: number;
  sync_full: number;
  sync_partial_ok: number;
  sync_partial_err: number;
  expired_keys: number;
  evicted_keys: number;
  keyspace_hits: number;
  keyspace_misses: number;
  pubsub_channels: number;
  pubsub_patterns: number;
  latest_fork_usec: number;
  migrate_cached_sockets: number;
}

// Redis键空间信息
export interface RedisKeyspace {
  db_id: number;
  keys: number;
  expires: number;
  avg_ttl: number;
}

// Redis客户端信息
export interface RedisClient {
  id: string;
  addr: string;
  fd: number;
  name: string;
  age: number;
  idle: number;
  flags: string;
  db: number;
  sub: number;
  psub: number;
  multi: number;
  qbuf: number;
  qbuf_free: number;
  obl: number;
  oll: number;
  omem: number;
  events: string;
  cmd: string;
}

// Redis慢日志
export interface RedisSlowLog {
  id: number;
  timestamp: number;
  duration: number;
  command: string;
  client_ip: string;
  client_name: string;
}

// Redis监控概览
export interface RedisMonitorOverview {
  connection_id: string;
  connection_name: string;
  status: string;
  info: RedisInfo;
  memory: RedisMemory;
  stats: RedisStats;
  keyspace: RedisKeyspace[];
  clients: RedisClient[];
  slow_log: RedisSlowLog[];
  timestamp: string;
}

// Redis实时统计
export interface RedisRealtimeStats {
  connection_id: string;
  used_memory: number;
  memory_usage_percent: number;
  connected_clients: number;
  ops_per_sec: number;
  hit_rate: number;
  keyspace_hits: number;
  keyspace_misses: number;
  timestamp: string;
}

/**
 * 获取Redis配置信息
 */
export async function getRedisConfigApi() {
  return requestClient.get<RedisConfig>('/api/core/redis_monitor/config');
}

/**
 * 获取Redis监控概览
 */
export async function getRedisMonitorOverviewApi() {
  return requestClient.get<RedisMonitorOverview>(
    '/api/core/redis_monitor/overview',
  );
}

/**
 * 获取Redis实时统计
 */
export async function getRedisRealtimeStatsApi() {
  return requestClient.get<RedisRealtimeStats>(
    '/api/core/redis_monitor/realtime',
  );
}

/**
 * 测试Redis连接
 */
export async function testRedisConnectionApi() {
  return requestClient.post<{
    message: string;
    redis_version?: string;
    response_time?: number;
    success: boolean;
  }>('/api/core/redis_monitor/test');
}
