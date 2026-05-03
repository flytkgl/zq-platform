import { computed } from 'vue';

import { $t } from '@vben/locales';

// 数据类型定义
export interface DataTypeOption {
  label: string;
  value: string;
  hasLength?: boolean;
  hasPrecision?: boolean;
  desc: string;
}

/**
 * 通用数据类型列表
 *
 * 前端统一使用通用类型，后端根据数据库类型自动转换：
 * - varchar: PostgreSQL=VARCHAR, MySQL=VARCHAR, SQL Server=VARCHAR
 * - text: PostgreSQL=TEXT, MySQL=TEXT, SQL Server=TEXT
 * - int: PostgreSQL=INTEGER, MySQL=INT, SQL Server=INT
 * - bigint: PostgreSQL=BIGINT, MySQL=BIGINT, SQL Server=BIGINT
 * - smallint: PostgreSQL=SMALLINT, MySQL=SMALLINT, SQL Server=SMALLINT
 * - decimal: PostgreSQL=DECIMAL, MySQL=DECIMAL, SQL Server=DECIMAL
 * - float: PostgreSQL=REAL, MySQL=FLOAT, SQL Server=FLOAT
 * - double: PostgreSQL=DOUBLE PRECISION, MySQL=DOUBLE, SQL Server=FLOAT
 * - datetime: PostgreSQL=TIMESTAMP, MySQL=DATETIME, SQL Server=DATETIME2
 * - date: PostgreSQL=DATE, MySQL=DATE, SQL Server=DATE
 * - time: PostgreSQL=TIME, MySQL=TIME, SQL Server=TIME
 * - boolean: PostgreSQL=BOOLEAN, MySQL=TINYINT(1), SQL Server=BIT
 * - json: PostgreSQL=JSON, MySQL=JSON, SQL Server=NVARCHAR(MAX)
 */
export const commonDataTypes = computed<DataTypeOption[]>(() => [
  {
    label: 'VARCHAR',
    value: 'varchar',
    hasLength: true,
    desc: $t('database-manager.dataTypes.varchar'),
  },
  {
    label: 'CHAR',
    value: 'char',
    hasLength: true,
    desc: $t('database-manager.dataTypes.char'),
  },
  { label: 'TEXT', value: 'text', desc: $t('database-manager.dataTypes.text') },
  { label: 'INT', value: 'int', desc: $t('database-manager.dataTypes.int') },
  {
    label: 'BIGINT',
    value: 'bigint',
    desc: $t('database-manager.dataTypes.bigint'),
  },
  {
    label: 'SMALLINT',
    value: 'smallint',
    desc: $t('database-manager.dataTypes.smallint'),
  },
  {
    label: 'DECIMAL',
    value: 'decimal',
    hasLength: true,
    hasPrecision: true,
    desc: $t('database-manager.dataTypes.decimal'),
  },
  {
    label: 'NUMERIC',
    value: 'numeric',
    hasLength: true,
    hasPrecision: true,
    desc: $t('database-manager.dataTypes.numeric'),
  },
  {
    label: 'FLOAT',
    value: 'float',
    desc: $t('database-manager.dataTypes.float'),
  },
  {
    label: 'DOUBLE',
    value: 'double',
    desc: $t('database-manager.dataTypes.double'),
  },
  {
    label: 'DATETIME',
    value: 'datetime',
    desc: $t('database-manager.dataTypes.datetime'),
  },
  { label: 'DATE', value: 'date', desc: $t('database-manager.dataTypes.date') },
  { label: 'TIME', value: 'time', desc: $t('database-manager.dataTypes.time') },
  {
    label: 'BOOLEAN',
    value: 'boolean',
    desc: $t('database-manager.dataTypes.boolean'),
  },
  { label: 'JSON', value: 'json', desc: $t('database-manager.dataTypes.json') },
]);

// 保留旧的类型列表以兼容现有代码（已弃用，建议使用 commonDataTypes）
export const postgresqlTypes = commonDataTypes;
export const mysqlTypes = commonDataTypes;
export const sqlserverTypes = commonDataTypes;

// 根据数据库类型获取数据类型列表（统一返回通用类型）
export function getDataTypesByDbType(_dbType: string): DataTypeOption[] {
  // 统一使用通用类型，后端会根据数据库类型自动转换
  return commonDataTypes.value;
}

// 判断字段类型是否需要长度
export function typeHasLength(types: DataTypeOption[], type: string): boolean {
  const typeOption = types.find((t) => t.value === type);
  return typeOption?.hasLength || false;
}

// 判断字段类型是否需要精度（小数位）
export function typeHasPrecision(
  types: DataTypeOption[],
  type: string,
): boolean {
  const typeOption = types.find((t) => t.value === type);
  return typeOption?.hasPrecision || false;
}

// NUMERIC 类型默认值
export const NUMERIC_DEFAULT_LENGTH = 10;
export const NUMERIC_DEFAULT_SCALE = 2;

/**
 * 数据库返回类型到通用类型的映射表
 * 用于将数据库返回的原生类型（如 INTEGER, TIMESTAMP）标准化为前端通用类型（如 int, datetime）
 */
const DB_TYPE_TO_COMMON_TYPE: Record<string, string> = {
  // PostgreSQL 类型映射
  integer: 'int',
  int4: 'int',
  int8: 'bigint',
  int2: 'smallint',
  'double precision': 'double',
  float4: 'float',
  float8: 'double',
  real: 'float',
  timestamp: 'datetime',
  'timestamp without time zone': 'datetime',
  'timestamp with time zone': 'datetime',
  timestamptz: 'datetime',
  bool: 'boolean',
  jsonb: 'json',
  'character varying': 'varchar',
  character: 'char',

  // MySQL 类型映射
  tinyint: 'boolean',
  'tinyint(1)': 'boolean',

  // SQL Server 类型映射
  datetime2: 'datetime',
  bit: 'boolean',
  'nvarchar(max)': 'json',
  nvarchar: 'varchar',
  nchar: 'char',
};

/**
 * 将数据库返回的类型标准化为前端通用类型
 * @param dbType 数据库返回的原生类型（如 INTEGER, TIMESTAMP, varchar(255)）
 * @returns 标准化后的通用类型（如 int, datetime, varchar）
 */
export function normalizeDbType(dbType: string): string {
  if (!dbType) return 'varchar';

  // 转小写并去除首尾空格
  const lowerType = dbType.toLowerCase().trim();

  // 先尝试直接匹配
  if (DB_TYPE_TO_COMMON_TYPE[lowerType]) {
    return DB_TYPE_TO_COMMON_TYPE[lowerType];
  }

  // 处理带长度的类型，如 varchar(255) -> varchar, numeric(10,2) -> numeric
  const baseType = lowerType.replace(/\(.*\)$/, '').trim();

  // 再次尝试匹配基础类型
  if (DB_TYPE_TO_COMMON_TYPE[baseType]) {
    return DB_TYPE_TO_COMMON_TYPE[baseType];
  }

  // 检查是否已经是通用类型
  const commonTypeValues = commonDataTypes.value.map((t) => t.value);
  if (commonTypeValues.includes(baseType)) {
    return baseType;
  }

  // 默认返回原类型（小写）
  return baseType;
}

/**
 * 通用类型到数据库特定类型的映射表
 * 用于生成 SQL 时将通用类型（如 int, datetime）转换为数据库特定类型（如 INTEGER, TIMESTAMP）
 */
const COMMON_TYPE_TO_DB_TYPE: Record<string, Record<string, string>> = {
  postgresql: {
    int: 'INTEGER',
    bigint: 'BIGINT',
    smallint: 'SMALLINT',
    float: 'REAL',
    double: 'DOUBLE PRECISION',
    datetime: 'TIMESTAMP',
    boolean: 'BOOLEAN',
    json: 'JSON',
    varchar: 'VARCHAR',
    char: 'CHAR',
    text: 'TEXT',
    decimal: 'DECIMAL',
    numeric: 'NUMERIC',
    date: 'DATE',
    time: 'TIME',
  },
  mysql: {
    int: 'INT',
    bigint: 'BIGINT',
    smallint: 'SMALLINT',
    float: 'FLOAT',
    double: 'DOUBLE',
    datetime: 'DATETIME',
    boolean: 'TINYINT(1)',
    json: 'JSON',
    varchar: 'VARCHAR',
    char: 'CHAR',
    text: 'TEXT',
    decimal: 'DECIMAL',
    numeric: 'DECIMAL',
    date: 'DATE',
    time: 'TIME',
  },
  sqlserver: {
    int: 'INT',
    bigint: 'BIGINT',
    smallint: 'SMALLINT',
    float: 'FLOAT',
    double: 'FLOAT',
    datetime: 'DATETIME2',
    boolean: 'BIT',
    json: 'NVARCHAR(MAX)',
    varchar: 'VARCHAR',
    char: 'CHAR',
    text: 'TEXT',
    decimal: 'DECIMAL',
    numeric: 'NUMERIC',
    date: 'DATE',
    time: 'TIME',
  },
};

/**
 * 将通用类型转换为数据库特定类型（用于生成 SQL）
 * @param commonType 通用类型（如 int, datetime, varchar）
 * @param dbType 数据库类型（postgresql, mysql, sqlserver）
 * @returns 数据库特定类型（如 INTEGER, TIMESTAMP, VARCHAR）
 */
export function mapToDbType(commonType: string, dbType: string): string {
  if (!commonType) return 'VARCHAR';

  const lowerCommonType = commonType.toLowerCase().trim();
  const lowerDbType = dbType.toLowerCase().trim();

  // 获取对应数据库的映射表，默认使用 PostgreSQL
  const typeMap: Record<string, string> =
    COMMON_TYPE_TO_DB_TYPE[lowerDbType] ?? COMMON_TYPE_TO_DB_TYPE.postgresql!;

  // 查找映射
  const mappedType = typeMap[lowerCommonType];
  if (mappedType) {
    return mappedType;
  }

  // 如果没有映射，返回原类型的大写形式
  return commonType.toUpperCase();
}
