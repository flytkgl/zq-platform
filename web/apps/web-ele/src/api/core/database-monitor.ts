import { requestClient } from '#/api/request';

// 数据库基本信息
export interface DatabaseBasicInfo {
  db_type: string;
  host: string;
  port: number;
  database: string;
  version: string;
  uptime: string;
  timezone: string;
  charset: string;
}

// 数据库连接信息
export interface DatabaseConnectionInfo {
  total_connections: number;
  max_connections: number;
  active_connections: number;
  idle_connections: number;
  connection_usage_percent: number;
}

// 数据库大小信息
export interface DatabaseSize {
  database_size_bytes: number;
  database_size_mb: number;
  database_size_gb: number;
}

// 数据库性能统计
export interface DatabasePerformanceStats {
  // PostgreSQL
  total_backends?: number;
  transactions_commit?: number;
  transactions_rollback?: number;
  tuples_returned?: number;
  tuples_fetched?: number;
  tuples_inserted?: number;
  tuples_updated?: number;
  tuples_deleted?: number;

  // MySQL
  total_queries?: number;
  total_connections?: number;
  slow_queries?: number;
  bytes_received?: number;
  bytes_sent?: number;

  // SQL Server
  batch_requests_per_sec?: number;
  page_life_expectancy?: number;
  buffer_cache_hit_ratio?: number;

  // 通用
  cache_hit_ratio: number;
}

// 数据库表统计
export interface DatabaseTableStats {
  // PostgreSQL
  schemaname?: string;
  tablename?: string;
  inserts?: number;
  updates?: number;
  deletes?: number;
  live_tuples?: number;
  dead_tuples?: number;
  size?: string;
  size_bytes?: number;
  total_size?: string;
  total_size_bytes?: number;

  // MySQL
  table_name?: string;
  table_rows?: number;
  data_length?: number;
  index_length?: number;
  auto_increment?: number;

  // SQL Server
  total_size_kb?: number;
  used_size_kb?: number;
  data_size_kb?: number;
}

// 数据库概览
export interface DatabaseMonitorOverview {
  connection_id: string;
  connection_name: string;
  status: string;
  basic_info: DatabaseBasicInfo;
  connection_info: DatabaseConnectionInfo;
  database_size: DatabaseSize;
  performance_stats: DatabasePerformanceStats;
  table_stats: DatabaseTableStats[];
  timestamp: string;
}

// 数据库实时统计
export interface DatabaseRealtimeStats {
  connection_id: string;
  connections_used: number;
  connection_usage_percent: number;
  database_size_mb: number;
  cache_hit_ratio: number;
  active_connections: number;
  timestamp: string;
}

// 数据库连接测试
export interface DatabaseConnectionTest {
  success: boolean;
  message: string;
  response_time?: number;
  version?: string;
  db_type: string;
}

// 数据库配置
export interface DatabaseConfig {
  name: string;
  db_name: string; // Django配置的key（如'default'），用于API调用
  db_type: string;
  host: string;
  port: number;
  database: string; // 实际数据库名
  user: string;
  has_password: boolean;
}

/**
 * 获取数据库监控配置列表
 */
export async function getDatabaseMonitorConfigsApi() {
  return requestClient.get<DatabaseConfig[]>(
    '/api/core/database_monitor/configs',
  );
}

/**
 * 获取数据库概览信息
 */
export async function getDatabaseMonitorOverviewApi(dbName: string) {
  return requestClient.get<DatabaseMonitorOverview>(
    `/api/core/database_monitor/${dbName}/overview`,
  );
}

/**
 * 获取数据库实时统计信息
 */
export async function getDatabaseRealtimeStatsApi(dbName: string) {
  return requestClient.get<DatabaseRealtimeStats>(
    `/api/core/database_monitor/${dbName}/realtime`,
  );
}

/**
 * 测试数据库连接
 */
export async function testDatabaseConnectionApi(dbName: string) {
  return requestClient.post<DatabaseConnectionTest>(
    `/api/core/database_monitor/${dbName}/test`,
  );
}
