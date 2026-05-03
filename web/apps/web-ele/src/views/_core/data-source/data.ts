import type { DataSource } from '#/api/core/data-source';

import { $t } from '@vben/locales';

/**
 * 数据源类型选项
 */
export const getSourceTypeOptions = () => [
  { label: $t('data-source.apiInterface'), value: 'api' },
  { label: $t('data-source.sqlQuery'), value: 'sql' },
  { label: $t('data-source.staticData'), value: 'static' },
];

/**
 * 结果类型选项
 */
export const getResultTypeOptions = () => [
  {
    label: $t('data-source.resultTypeList'),
    value: 'list',
    description: $t('data-source.resultTypeListDesc'),
  },
  {
    label: $t('data-source.resultTypeTree'),
    value: 'tree',
    description: $t('data-source.resultTypeTreeDesc'),
  },
  {
    label: $t('data-source.resultTypeSingleObject'),
    value: 'object',
    description: $t('data-source.resultTypeObjectDesc'),
  },
  {
    label: $t('data-source.resultTypeSingleValue'),
    value: 'value',
    description: $t('data-source.resultTypeValueDesc'),
  },
  {
    label: $t('data-source.resultTypeAxisChart'),
    value: 'chart-axis',
    description: $t('data-source.resultTypeChartAxisDesc'),
  },
  {
    label: $t('data-source.resultTypePieChart'),
    value: 'chart-pie',
    description: $t('data-source.resultTypeChartPieDesc'),
  },
  {
    label: $t('data-source.resultTypeGauge'),
    value: 'chart-gauge',
    description: $t('data-source.resultTypeChartGaugeDesc'),
  },
  {
    label: $t('data-source.resultTypeRadarChart'),
    value: 'chart-radar',
    description: $t('data-source.resultTypeChartRadarDesc'),
  },
  {
    label: $t('data-source.resultTypeScatterChart'),
    value: 'chart-scatter',
    description: $t('data-source.resultTypeChartScatterDesc'),
  },
  {
    label: $t('data-source.resultTypeHeatmap'),
    value: 'chart-heatmap',
    description: $t('data-source.resultTypeChartHeatmapDesc'),
  },
];

/**
 * HTTP 方法选项
 */
export const httpMethodOptions = [
  { label: 'GET', value: 'GET' },
  { label: 'POST', value: 'POST' },
  { label: 'PUT', value: 'PUT' },
  { label: 'DELETE', value: 'DELETE' },
  { label: 'PATCH', value: 'PATCH' },
];

/**
 * 认证类型选项
 */
export const getAuthTypeOptions = () => [
  { label: $t('data-source.authNone'), value: 'none' },
  { label: 'Bearer Token', value: 'bearer_token' },
  { label: 'Basic Auth', value: 'basic_auth' },
  { label: 'API Key', value: 'api_key' },
];

/**
 * 请求体类型选项
 */
export const getBodyTypeOptions = () => [
  { label: $t('data-source.bodyTypeNone'), value: 'none' },
  { label: 'JSON', value: 'json' },
  { label: 'Form Data', value: 'form-data' },
  { label: 'x-www-form-urlencoded', value: 'x-www-form-urlencoded' },
  { label: 'Raw', value: 'raw' },
];

/**
 * API Key 位置选项
 */
export const getKeyPositionOptions = () => [
  { label: 'Header', value: 'header' },
  { label: 'Query Param', value: 'query' },
];

/**
 * 参数类型选项
 */
export const getParamTypeOptions = () => [
  { label: $t('data-source.paramTypeString'), value: 'string' },
  { label: $t('data-source.paramTypeInteger'), value: 'integer' },
  { label: $t('data-source.paramTypeFloat'), value: 'float' },
  { label: $t('data-source.paramTypeBoolean'), value: 'boolean' },
  { label: $t('data-source.paramTypeDate'), value: 'date' },
  { label: $t('data-source.paramTypeDatetime'), value: 'datetime' },
];

/**
 * 默认数据源配置
 */
export const defaultDataSource: Partial<DataSource> = {
  name: '',
  code: '',
  source_type: 'sql',
  description: '',
  status: true,
  // API 配置
  api_url: '',
  api_method: 'GET',
  api_headers: {},
  api_query_params: [],
  api_body_type: 'none',
  api_body: {},
  api_content_type: '',
  api_timeout: 30,
  api_data_path: '',
  // API 认证
  api_auth_type: 'none',
  api_auth_config: {},
  // API 高级
  api_retry_count: 0,
  api_retry_interval: 1,
  api_success_condition: {},
  api_proxy: '',
  api_follow_redirects: true,
  api_verify_ssl: true,
  // SQL 配置
  sql_content: '',
  db_connection: 'default',
  // 静态数据
  static_data: [],
  // 参数
  params: [],
  // 结果处理
  result_type: 'list',
  tree_config: {},
  field_mapping: {},
  chart_config: {},
  // 缓存
  cache_enabled: false,
  cache_ttl: 300,
};
