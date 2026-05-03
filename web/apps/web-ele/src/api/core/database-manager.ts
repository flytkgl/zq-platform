/**
 * 数据库管理API
 */
import { requestClient } from '#/api/request';

// ==================== 类型定义 ====================

/**
 * 数据库配置
 */
export interface DatabaseConfig {
  db_name: string;
  name: string;
  db_type: string;
  host: string;
  port: number;
  database: string;
  user: string;
  has_password: boolean;
}

/**
 * 数据库信息
 */
export interface DatabaseInfo {
  name: string;
  owner?: string;
  encoding?: string;
  collation?: string;
  size?: string;
  size_bytes?: number;
  tables_count?: number;
  description?: string;
}

/**
 * Schema信息
 */
export interface SchemaInfo {
  name: string;
  owner?: string;
  tables_count?: number;
}

/**
 * 表信息
 */
export interface TableInfo {
  schema_name?: string;
  table_name: string;
  table_type?: string;
  row_count?: number;
  total_size?: string;
  total_size_bytes?: number;
  description?: string;
}

/**
 * 字段信息
 */
export interface ColumnInfo {
  column_name: string;
  data_type: string;
  is_nullable: boolean;
  column_default?: string;
  character_maximum_length?: number;
  numeric_precision?: number;
  numeric_scale?: number;
  ordinal_position?: number;
  is_primary_key: boolean;
  is_unique: boolean;
  description?: string;
}

/**
 * 索引信息
 */
export interface IndexInfo {
  index_name: string;
  index_type?: string;
  columns: string;
  is_unique: boolean;
  is_primary: boolean;
  definition?: string;
}

/**
 * 约束信息
 */
export interface ConstraintInfo {
  constraint_name: string;
  constraint_type: string;
  columns?: string;
  definition?: string;
  referenced_table?: string;
  referenced_columns?: string;
}

/**
 * 表结构
 */
export interface TableStructure {
  table_info: TableInfo;
  columns: ColumnInfo[];
  indexes: IndexInfo[];
  constraints: ConstraintInfo[];
}

/**
 * 查询数据参数
 */
export interface QueryDataParams {
  table_name: string;
  schema_name?: string;
  page: number;
  page_size: number;
  where?: string;
  order_by?: string;
}

/**
 * 查询数据响应
 */
export interface QueryDataResponse {
  columns: string[];
  rows: Record<string, any>[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * SQL执行参数
 */
export interface ExecuteSQLParams {
  sql: string;
  is_query: boolean;
}

/**
 * SQL执行响应
 */
export interface ExecuteSQLResponse {
  success: boolean;
  message: string;
  columns?: string[];
  rows?: Record<string, any>[];
  affected_rows?: number;
  execution_time: number;
}

/**
 * 连接测试响应
 */
export interface ConnectionTestResponse {
  success: boolean;
  message: string;
  db_name: string;
  db_type: string;
}

// ==================== API接口 ====================

/**
 * 获取数据库配置列表
 */
export async function getDatabaseConfigsApi() {
  return requestClient.get<DatabaseConfig[]>(
    '/api/core/database_manager/configs',
  );
}

/**
 * 测试数据库连接
 */
export async function testDatabaseConnectionApi(dbName: string) {
  return requestClient.post<ConnectionTestResponse>(
    `/api/core/database_manager/${dbName}/test`,
  );
}

/**
 * 获取数据库列表
 */
export async function getDatabasesApi(dbName: string) {
  return requestClient.get<DatabaseInfo[]>(
    `/api/core/database_manager/${dbName}/databases`,
  );
}

/**
 * 获取Schema列表（PostgreSQL）
 */
export async function getSchemasApi(dbName: string, database?: string) {
  return requestClient.get<SchemaInfo[]>(
    `/api/core/database_manager/${dbName}/schemas`,
    { params: { database } },
  );
}

/**
 * 获取表列表
 */
export async function getTablesApi(
  dbName: string,
  database?: string,
  schemaName?: string,
) {
  return requestClient.get<TableInfo[]>(
    `/api/core/database_manager/${dbName}/tables`,
    { params: { database, schema_name: schemaName } },
  );
}

/**
 * 获取表结构
 */
export async function getTableStructureApi(
  dbName: string,
  tableName: string,
  database?: string,
  schemaName?: string,
) {
  return requestClient.get<TableStructure>(
    `/api/core/database_manager/${dbName}/tables/${tableName}/structure`,
    { params: { database, schema_name: schemaName } },
  );
}

/**
 * 获取表字段
 */
export async function getTableColumnsApi(
  dbName: string,
  tableName: string,
  database?: string,
  schemaName?: string,
) {
  return requestClient.get<ColumnInfo[]>(
    `/api/core/database_manager/${dbName}/tables/${tableName}/columns`,
    { params: { database, schema_name: schemaName } },
  );
}

/**
 * 获取表索引
 */
export async function getTableIndexesApi(
  dbName: string,
  tableName: string,
  database?: string,
  schemaName?: string,
) {
  return requestClient.get<IndexInfo[]>(
    `/api/core/database_manager/${dbName}/tables/${tableName}/indexes`,
    { params: { database, schema_name: schemaName } },
  );
}

/**
 * 获取表约束
 */
export async function getTableConstraintsApi(
  dbName: string,
  tableName: string,
  database?: string,
  schemaName?: string,
) {
  return requestClient.get<ConstraintInfo[]>(
    `/api/core/database_manager/${dbName}/tables/${tableName}/constraints`,
    { params: { database, schema_name: schemaName } },
  );
}

/**
 * 查询表数据
 */
export async function queryTableDataApi(
  dbName: string,
  params: QueryDataParams,
) {
  return requestClient.post<QueryDataResponse>(
    `/api/core/database_manager/${dbName}/query`,
    params,
  );
}

/**
 * 执行SQL
 */
export async function executeSQLApi(
  dbName: string,
  data: ExecuteSQLParams,
): Promise<ExecuteSQLResponse> {
  return requestClient.post(`/core/database_manager/${dbName}/execute`, data);
}

/**
 * 获取表DDL语句
 */
export async function getTableDDLApi(
  dbName: string,
  tableName: string,
  database?: string,
  schemaName?: string,
): Promise<{ ddl: string }> {
  return requestClient.get(
    `/api/core/database_manager/${dbName}/tables/${tableName}/ddl`,
    { params: { database, schema_name: schemaName } },
  );
}

// ============ 视图管理 ============

/**
 * 获取视图列表
 */
export async function getViewsApi(
  dbName: string,
  database?: string,
  schemaName?: string,
): Promise<any[]> {
  return requestClient.get(`/api/core/database_manager/${dbName}/views`, {
    params: { database, schema_name: schemaName },
  });
}

/**
 * 获取视图结构
 */
export async function getViewStructureApi(
  dbName: string,
  viewName: string,
  schemaName?: string,
): Promise<any> {
  return requestClient.get(
    `/api/core/database_manager/${dbName}/views/${viewName}/structure`,
    {
      params: { schema_name: schemaName },
    },
  );
}

/**
 * 获取视图定义SQL
 */
export async function getViewDefinitionApi(
  dbName: string,
  viewName: string,
  schemaName?: string,
): Promise<{ definition: string }> {
  return requestClient.get(
    `/api/core/database_manager/${dbName}/views/${viewName}/definition`,
    {
      params: { schema_name: schemaName },
    },
  );
}

/**
 * 获取视图依赖的表
 */
export async function getViewDependenciesApi(
  dbName: string,
  viewName: string,
  schemaName?: string,
): Promise<string[]> {
  return requestClient.get(
    `/api/core/database_manager/${dbName}/views/${viewName}/dependencies`,
    {
      params: { schema_name: schemaName },
    },
  );
}

/**
 * 执行DDL语句
 */
export async function executeDDLApi(
  dbName: string,
  data: {
    database?: string;
    schema_name?: string;
    sql: string;
  },
) {
  return requestClient.post<{
    affected_rows: number;
    message: string;
    success: boolean;
  }>(`/api/core/database_manager/${dbName}/execute/ddl`, data);
}
