<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import type {
  AuthConfig,
  DataSource,
  ParamDefinition,
  QueryParamItem,
  SuccessCondition,
} from '#/api/core/data-source';
import type { ZqTabItem } from '#/components/zq-tabs/index.vue';

import { computed, nextTick, reactive, ref, watch } from 'vue';

import { CirclePlus, Eye, Play, Settings, Sparkles, Trash } from '@vben/icons';
import { $t } from '@vben/locales';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  ElAlert,
  ElButton,
  ElCard,
  ElCol,
  ElDialog,
  ElDivider,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElRadioButton,
  ElRadioGroup,
  ElRow,
  ElScrollbar,
  ElSelect,
  ElSplitter,
  ElSplitterPanel,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTooltip,
} from 'element-plus';

import {
  createDataSourceApi,
  getDataSourceDetailApi,
  testDataSourceApi,
  updateDataSourceApi,
} from '#/api/core/data-source';
import { CodeEditor } from '#/components/zq-form/code-editor';
import ZqTabs from '#/components/zq-tabs/index.vue';
import { useAppContextStore } from '#/store/app-context';

import {
  defaultDataSource,
  getAuthTypeOptions,
  getBodyTypeOptions,
  getKeyPositionOptions,
  getParamTypeOptions,
  getResultTypeOptions,
  getSourceTypeOptions,
  httpMethodOptions,
} from '../data';
import DbSchemaPanel from './db-schema-panel.vue';

interface Props {
  modelValue: boolean;
  dataSourceId?: null | string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  save: [];
  'update:modelValue': [value: boolean];
}>();

const appContextStore = useAppContextStore();
const loading = ref(false);
const currentStep = ref(0);

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const isEditMode = computed(() => !!props.dataSourceId);

// 步骤定义
const steps = [
  { title: $t('data-source.basicInfo'), index: 1 },
  { title: $t('data-source.dataSourceConfig'), index: 2 },
];

// 表单数据
const formData = reactive<DataSource>({
  ...defaultDataSource,
} as DataSource);

// 测试相关
const testLoading = ref(false);
const testParams = ref<Record<string, any>>({});
const testResult = ref<null | {
  data: any[];
  limited: number;
  success: boolean;
  total: number;
}>(null);
const configActiveTab = ref('result');

// SQL 编辑器引用
const sqlEditorRef = ref<InstanceType<typeof CodeEditor>>();

// 当前选中的数据库上下文
const dbContext = ref<null | {
  database?: string;
  dbName: string;
  schema?: string;
}>(null);

// 数据库上下文显示文本
const dbContextDisplay = computed(() => {
  if (!dbContext.value) return $t('data-source.noData');
  const parts = [dbContext.value.dbName];
  if (dbContext.value.database) parts.push(dbContext.value.database);
  if (dbContext.value.schema) parts.push(dbContext.value.schema);
  return parts.join(' / ');
});

// SQL 编辑模式：manual（手动）或 ai（AI 辅助），默认为 AI 模式
const sqlEditMode = ref<'ai' | 'manual'>('manual');

// AI 模式相关
const aiUserQuestion = ref('');
const aiGenerating = ref(false);
const aiResult = ref<null | {
  params: ParamDefinition[];
  sql: string;
  thought: string;
}>(null);

// 快速示例
const quickExamples = [
  '查询最近7天的活跃用户',
  '统计每个部门的员工数量',
  '查询销售额前10的商品',
];

// SQL/API 配置 Tabs（参数定义放第一个）
const configTabs = computed<ZqTabItem[]>(() => [
  { key: 'params', label: $t('data-source.paramDefinition'), icon: Settings },
  { key: 'result', label: $t('data-source.resultProcessing'), icon: Settings },
  { key: 'test', label: $t('data-source.testResult'), icon: Play },
]);

// 图表引用
const previewChartRef = ref<EchartsUIType>();
const { renderEcharts: renderPreviewChart } = useEcharts(previewChartRef);

// API 模式图表引用
const apiPreviewChartRef = ref<EchartsUIType>();
const { renderEcharts: renderApiPreviewChart } = useEcharts(apiPreviewChartRef);

// 是否显示图表类型（只有图表相关的结果类型才显示图表切换）
const isChartResultType = computed(() => {
  return [
    'chart-axis',
    'chart-gauge',
    'chart-heatmap',
    'chart-pie',
    'chart-radar',
    'chart-scatter',
  ].includes(formData.result_type || '');
});

// 渲染预览图表（支持 SQL 和 API 模式）
function renderResultChart() {
  if (!testResult.value?.data || !isChartResultType.value) return;

  const data = testResult.value.data;
  const resultType = formData.result_type;
  // 根据数据源类型选择渲染函数
  const isApiMode = formData.source_type === 'api';
  const renderFn = isApiMode ? renderApiPreviewChart : renderPreviewChart;

  switch (resultType) {
    case 'chart-axis': {
      renderAxisChart(data, renderFn);
      break;
    }
    case 'chart-gauge': {
      renderGaugeChart(data, renderFn);
      break;
    }
    case 'chart-heatmap': {
      renderHeatmapChart(data, renderFn);
      break;
    }
    case 'chart-pie': {
      renderPieChart(data, renderFn);
      break;
    }
    case 'chart-radar': {
      renderRadarChart(data, renderFn);
      break;
    }
    case 'chart-scatter': {
      renderScatterChart(data, renderFn);
      break;
    }
  }
}

// 轴向图表（柱状图/折线图）
function renderAxisChart(data: any, renderFn = renderPreviewChart) {
  // 后端返回的格式：{xAxisData: [], seriesData: [{name, data}]}
  if (!data || !data.xAxisData || !data.seriesData) return;

  const { xAxisData, seriesData } = data;

  renderFn({
    tooltip: { trigger: 'axis' as const },
    legend: { data: seriesData.map((s: any) => s.name) },
    xAxis: { type: 'category' as const, data: xAxisData },
    yAxis: { type: 'value' as const },
    series: seriesData.map((s: any) => ({
      name: s.name,
      type: 'bar' as const,
      data: s.data,
    })),
  });
}

// 饼图
function renderPieChart(data: any, renderFn = renderPreviewChart) {
  // 后端返回格式：{seriesData: [{name, value}]}
  let pieData = [];

  if (data?.seriesData && Array.isArray(data.seriesData)) {
    pieData = data.seriesData;
  } else if (Array.isArray(data) && data.length > 0) {
    // 兼容数组格式
    const keys = Object.keys(data[0]);
    const firstKey = keys[0] || 'name';
    const secondKey = keys[1] || 'value';
    pieData = data.map((item) => ({
      name: item.name || item.label || item[firstKey],
      value: item.value || item.count || item[secondKey],
    }));
  } else {
    return;
  }

  renderFn({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { data: pieData.map((d: any) => d.name) },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        data: pieData,
        label: { show: true, formatter: '{b}: {d}%' },
      },
    ],
  });
}

// 仪表盘
function renderGaugeChart(data: any, renderFn = renderPreviewChart) {
  let value = 0;

  // 后端返回格式：{value: number} 或 {seriesData: [{value}]}
  if (data?.value !== undefined) {
    value = data.value;
  } else if (data?.seriesData?.[0]?.value !== undefined) {
    value = data.seriesData[0].value;
  } else if (Array.isArray(data) && data.length > 0) {
    const firstKey = Object.keys(data[0])[0] || 'value';
    value = data[0].value || data[0][firstKey] || 0;
  }

  renderFn({
    series: [
      {
        type: 'gauge' as const,
        progress: { show: true, width: 18 },
        axisLine: { lineStyle: { width: 18 } },
        detail: {
          valueAnimation: true,
          fontSize: 28,
          offsetCenter: [0, '70%'],
        },
        data: [{ value }],
      },
    ],
  });
}

// 雷达图
function renderRadarChart(data: any, renderFn = renderPreviewChart) {
  // 后端返回格式：{indicator: [{name, max}], seriesData: [{name, value: []}]}
  let indicator: any[] = [];
  let seriesData: any[] = [];

  if (data?.indicator && data?.seriesData) {
    indicator = data.indicator;
    seriesData = data.seriesData;
  } else if (Array.isArray(data) && data.length > 0) {
    // 兼容数组格式
    const keys = Object.keys(data[0]).filter(
      (k) => typeof data[0][k] === 'number',
    );
    indicator = keys.map((k) => ({
      name: k,
      max: Math.max(...data.map((d: any) => d[k])) * 1.2,
    }));
    seriesData = data.map((item: any) => ({
      name: item.name || item.label || 'Data',
      value: keys.map((k) => item[k]),
    }));
  } else {
    return;
  }

  renderFn({
    tooltip: {},
    radar: { indicator },
    series: [{ type: 'radar' as const, data: seriesData }],
  });
}

// 散点图
function renderScatterChart(data: any, renderFn = renderPreviewChart) {
  // 后端返回格式：{seriesData: [[x, y], ...]} 或数组格式
  let scatterData: any[] = [];

  if (data?.seriesData && Array.isArray(data.seriesData)) {
    scatterData = data.seriesData;
  } else if (Array.isArray(data) && data.length > 0) {
    // 兼容数组格式
    const keys = Object.keys(data[0]).filter(
      (k) => typeof data[0][k] === 'number',
    );
    const xKey = keys[0] || 'x';
    const yKey = keys[1] || 'y';
    scatterData = data.map((item: any) => [item[xKey] || 0, item[yKey] || 0]);
  } else {
    return;
  }

  renderFn({
    tooltip: { trigger: 'item' as const },
    xAxis: { type: 'value' as const },
    yAxis: { type: 'value' as const },
    series: [{ type: 'scatter' as const, data: scatterData, symbolSize: 10 }],
  });
}

// 热力图
function renderHeatmapChart(data: any, renderFn = renderPreviewChart) {
  // 后端返回格式：{xAxisData, yAxisData, seriesData: [[x, y, value], ...]}
  let xLabels: any[] = [];
  let yLabels: any[] = [];
  let heatmapData: any[] = [];
  let maxVal = 100;

  if (data?.xAxisData && data?.yAxisData && data?.seriesData) {
    xLabels = data.xAxisData;
    yLabels = data.yAxisData;
    heatmapData = data.seriesData;
    maxVal =
      heatmapData.length > 0
        ? Math.max(...heatmapData.map((d: any) => d[2] ?? 0))
        : 100;
  } else if (Array.isArray(data) && data.length > 0) {
    // 兼容数组格式
    heatmapData = data.flatMap((item: any, i: number) => {
      const values = Object.values(item).filter(
        (v) => typeof v === 'number',
      ) as number[];
      return values.map((v, j) => [j, i, v]);
    });
    xLabels = Object.keys(data[0]).filter(
      (k) => typeof data[0][k] === 'number',
    );
    yLabels = data.map((_: any, i: number) => `Row ${i + 1}`);
    maxVal =
      heatmapData.length > 0
        ? Math.max(...heatmapData.map((d: any) => d[2] ?? 0))
        : 100;
  } else {
    return;
  }

  renderFn({
    tooltip: { position: 'top' },
    xAxis: { type: 'category' as const, data: xLabels },
    yAxis: { type: 'category' as const, data: yLabels },
    visualMap: { min: 0, max: maxVal, calculable: true },
    series: [
      { type: 'heatmap' as const, data: heatmapData, label: { show: true } },
    ],
  });
}

// 监听测试结果变化，自动渲染图表
watch(
  () => testResult.value,
  async () => {
    if (isChartResultType.value && testResult.value?.data) {
      await nextTick();
      setTimeout(renderResultChart, 200);
    }
  },
  { deep: true },
);

// 监听结果类型变化，如果已有测试结果则重新执行测试
watch(
  () => formData.result_type,
  async (newType) => {
    // 如果已有测试结果且切换了结果类型，重新执行测试以获取正确格式的数据
    if (newType && testResult.value?.data) {
      await handleTest();
    }
  },
);

// 监听 Tab 切换，切换到测试 Tab 时自动执行测试
watch(configActiveTab, (newTab) => {
  if (newTab === 'test') {
    handleTest();
  }
});

// JSON 字符串编辑（用于 textarea）
const apiBodyStr = computed({
  get: () => JSON.stringify(formData.api_body || {}, null, 2),
  set: (v: string) => {
    try {
      formData.api_body = JSON.parse(v);
    } catch {
      // 忽略解析错误
    }
  },
});

const staticDataStr = computed({
  get: () => JSON.stringify(formData.static_data || [], null, 2),
  set: (v: string) => {
    try {
      formData.static_data = JSON.parse(v);
    } catch {
      // 忽略解析错误
    }
  },
});

// 图表配置 - 系列字段（逗号分隔字符串）
const chartSeriesFieldsStr = computed({
  get: () => (formData.chart_config?.series_fields || []).join(', '),
  set: (v: string) => {
    if (!formData.chart_config) formData.chart_config = {};
    formData.chart_config.series_fields = v
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
  },
});

// 图表配置 - 系列名称（逗号分隔字符串）
const chartSeriesNamesStr = computed({
  get: () => (formData.chart_config?.series_names || []).join(', '),
  set: (v: string) => {
    if (!formData.chart_config) formData.chart_config = {};
    formData.chart_config.series_names = v
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
  },
});

// 图表配置 - 数值字段（雷达图用，逗号分隔字符串）
const chartValueFieldsStr = computed({
  get: () => (formData.chart_config?.value_fields || []).join(', '),
  set: (v: string) => {
    if (!formData.chart_config) formData.chart_config = {};
    formData.chart_config.value_fields = v
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
  },
});

// 标题
const title = computed(() =>
  isEditMode.value
    ? $t('data-source.editDataSource')
    : $t('data-source.createDataSource'),
);

// 选项列表（国际化）
const sourceTypeOptions = computed(() => getSourceTypeOptions());
const resultTypeOptions = computed(() => getResultTypeOptions());
const paramTypeOptions = computed(() => getParamTypeOptions());
const authTypeOptions = computed(() => getAuthTypeOptions());
const bodyTypeOptions = computed(() => getBodyTypeOptions());
const keyPositionOptions = computed(() => getKeyPositionOptions());

// API 配置内部 Tab
const apiConfigTab = ref('basic');

// API 配置 Tabs（使用 ZqTabs）
const apiConfigTabs = computed<ZqTabItem[]>(() => {
  const tabs: ZqTabItem[] = [
    { key: 'basic', label: $t('data-source.apiTabBasic') },
    { key: 'headers', label: $t('data-source.apiTabHeaders') },
    // { key: 'auth', label: $t('data-source.apiTabAuth') },
    { key: 'query', label: $t('data-source.apiTabQueryParams') },
  ];
  if (showBodyTab.value) {
    tabs.push({ key: 'body', label: $t('data-source.apiTabBody') });
  }
  tabs.push({ key: 'advanced', label: $t('data-source.apiTabAdvanced') });
  return tabs;
});

// 是否显示请求体（GET/DELETE 一般不带 body）
const showBodyTab = computed(() => {
  const method = formData.api_method?.toUpperCase();
  return method !== 'GET' && method !== 'DELETE';
});

// 请求体 placeholder
const bodyPlaceholder = computed(() => {
  if (formData.api_body_type === 'json') {
    return '{"page": 1, "pageSize": 10}';
  }
  return 'key=value&key2=value2';
});

// ---- Headers 管理（key-value 列表） ----
interface HeaderItem {
  key: string;
  value: string;
  enabled: boolean;
}
const headerItems = ref<HeaderItem[]>([]);

function syncHeadersFromObject() {
  const headers = formData.api_headers || {};
  headerItems.value = Object.entries(headers).map(([k, v]) => ({
    key: k,
    value: String(v),
    enabled: true,
  }));
}

function syncHeadersToObject() {
  const obj: Record<string, string> = {};
  for (const item of headerItems.value) {
    if (item.enabled && item.key.trim()) {
      obj[item.key.trim()] = item.value;
    }
  }
  formData.api_headers = obj;
}

function addHeaderItem() {
  headerItems.value.push({ key: '', value: '', enabled: true });
}

function removeHeaderItem(index: number) {
  headerItems.value.splice(index, 1);
  syncHeadersToObject();
}

watch(headerItems, () => syncHeadersToObject(), { deep: true });

// ---- URL ↔ Query 参数双向同步 ----
let _syncingUrl = false;

function parseUrlQueryParams(url: string): {
  baseUrl: string;
  params: QueryParamItem[];
} {
  try {
    const qIdx = url.indexOf('?');
    if (qIdx === -1) return { baseUrl: url, params: [] };
    const baseUrl = url.slice(0, Math.max(0, qIdx));
    const search = url.slice(Math.max(0, qIdx + 1));
    const params: QueryParamItem[] = [];
    if (search) {
      for (const part of search.split('&')) {
        const eqIdx = part.indexOf('=');
        if (eqIdx !== -1) {
          params.push({
            key: decodeURIComponent(part.slice(0, Math.max(0, eqIdx))),
            value: decodeURIComponent(part.slice(Math.max(0, eqIdx + 1))),
            description: '',
            enabled: true,
          });
        } else if (part.trim()) {
          params.push({
            key: decodeURIComponent(part),
            value: '',
            description: '',
            enabled: true,
          });
        }
      }
    }
    return { baseUrl, params };
  } catch {
    return { baseUrl: url, params: [] };
  }
}

function buildUrlWithParams(baseUrl: string, params: QueryParamItem[]): string {
  const enabled = (params || []).filter((p) => p.enabled && p.key.trim());
  if (enabled.length === 0) return baseUrl;
  // 显示时不编码，保持中文可读性（实际请求时后端会处理编码）
  const qs = enabled.map((p) => `${p.key}=${p.value || ''}`).join('&');
  return `${baseUrl}?${qs}`;
}

function getBaseUrl(): string {
  const url = formData.api_url || '';
  const qIdx = url.indexOf('?');
  return qIdx === -1 ? url : url.slice(0, Math.max(0, qIdx));
}

watch(
  () => formData.api_url,
  (newUrl) => {
    if (_syncingUrl || !newUrl) return;
    const { params: urlParams } = parseUrlQueryParams(newUrl);
    if (!formData.api_query_params) formData.api_query_params = [];
    const existing = formData.api_query_params;
    for (const up of urlParams) {
      const found = existing.find((p) => p.key === up.key);
      if (found) {
        found.value = up.value;
        found.enabled = true;
      } else {
        existing.push(up);
      }
    }
  },
);

watch(
  () => formData.api_query_params,
  (params) => {
    _syncingUrl = true;
    formData.api_url = buildUrlWithParams(getBaseUrl(), params || []);
    _syncingUrl = false;
  },
  { deep: true },
);

// ---- 查看完整请求 ----
const showRequestPreview = ref(false);

const fullRequestPreview = computed(() => {
  const method = (formData.api_method || 'GET').toUpperCase();
  const url = formData.api_url || '';
  const headers = formData.api_headers || {};
  const authType = formData.api_auth_type || 'none';
  const authConfig = formData.api_auth_config || {};

  const effectiveHeaders: Record<string, string> = { ...headers };
  if (authType === 'bearer_token' && authConfig.token) {
    effectiveHeaders.Authorization = `Bearer ${authConfig.token}`;
  } else if (authType === 'basic_auth' && authConfig.username) {
    effectiveHeaders.Authorization = `Basic ${btoa(`${authConfig.username}:${authConfig.password || ''}`)}`;
  } else if (
    authType === 'api_key' &&
    authConfig.key_name &&
    authConfig.key_position === 'header'
  ) {
    effectiveHeaders[authConfig.key_name] = authConfig.key_value || '';
  }

  let body: any = null;
  if (
    showBodyTab.value &&
    formData.api_body_type &&
    formData.api_body_type !== 'none'
  ) {
    body = formData.api_body;
  }

  return JSON.stringify(
    { method, url, headers: effectiveHeaders, body },
    null,
    2,
  );
});

// Query 参数操作
function addQueryParam() {
  if (!formData.api_query_params) {
    formData.api_query_params = [];
  }
  formData.api_query_params.push({
    key: '',
    value: '',
    description: '',
    enabled: true,
  } as QueryParamItem);
}

function removeQueryParam(index: number) {
  formData.api_query_params?.splice(index, 1);
}

// 认证配置初始化
function ensureAuthConfig(): AuthConfig {
  if (!formData.api_auth_config) {
    formData.api_auth_config = {};
  }
  return formData.api_auth_config;
}

// 成功条件配置初始化
function ensureSuccessCondition(): SuccessCondition {
  if (!formData.api_success_condition) {
    formData.api_success_condition = {};
  }
  return formData.api_success_condition;
}

// 步骤验证
const canGoNext = computed(() => {
  if (currentStep.value === 0) {
    return formData.name && formData.code && formData.source_type;
  }
  return true;
});

const canGoPrev = computed(() => currentStep.value > 0);
const isLastStep = computed(() => currentStep.value === steps.length - 1);

// 监听弹窗打开，加载数据
watch(
  () => props.modelValue,
  async (visible) => {
    if (visible) {
      currentStep.value = 0;
      testResult.value = null;
      testParams.value = {};
      configActiveTab.value = 'result';
      Object.assign(formData, defaultDataSource);

      if (props.dataSourceId) {
        loading.value = true;
        try {
          const data = await getDataSourceDetailApi(props.dataSourceId);
          Object.assign(formData, data);
          syncHeadersFromObject();
          initTestParams();
        } catch {
          ElMessage.error($t('data-source.loadDataSourceFailed'));
          dialogVisible.value = false;
        } finally {
          loading.value = false;
        }
      }
    }
  },
);

/**
 * 初始化测试参数默认值
 */
function initTestParams() {
  testParams.value = {};
  if (formData.params && formData.params.length > 0) {
    for (const param of formData.params) {
      if (param.default !== undefined && param.default !== null) {
        testParams.value[param.name] = param.default;
      }
    }
  }
}

/**
 * 下一步
 */
function handleNext() {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++;
  }
}

/**
 * 上一步
 */
function handlePrev() {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
}

/**
 * 关闭弹窗
 */
function handleClose() {
  dialogVisible.value = false;
}

/**
 * 保存
 */
async function handleSave() {
  loading.value = true;
  try {
    if (isEditMode.value && props.dataSourceId) {
      await updateDataSourceApi(props.dataSourceId, formData);
      ElMessage.success($t('data-source.updateDataSourceSuccess'));
    } else {
      formData.application_id = appContextStore.currentApp?.id;
      await createDataSourceApi(formData);
      ElMessage.success($t('data-source.createDataSourceSuccess'));
    }
    emit('save');
    handleClose();
  } catch (error: any) {
    ElMessage.error(error?.message || $t('data-source.error'));
  } finally {
    loading.value = false;
  }
}

/**
 * 测试数据源
 */
async function handleTest() {
  testLoading.value = true;
  testResult.value = null;

  try {
    const result = await testDataSourceApi({
      source_type: formData.source_type,
      api_url: formData.api_url,
      api_method: formData.api_method,
      api_headers: formData.api_headers,
      api_query_params: formData.api_query_params,
      api_body_type: formData.api_body_type,
      api_body: formData.api_body,
      api_content_type: formData.api_content_type,
      api_timeout: formData.api_timeout,
      api_data_path: formData.api_data_path,
      api_auth_type: formData.api_auth_type,
      api_auth_config: formData.api_auth_config,
      api_retry_count: formData.api_retry_count,
      api_retry_interval: formData.api_retry_interval,
      api_success_condition: formData.api_success_condition,
      api_proxy: formData.api_proxy,
      api_follow_redirects: formData.api_follow_redirects,
      api_verify_ssl: formData.api_verify_ssl,
      sql_content: formData.sql_content,
      db_connection: formData.db_connection,
      static_data: formData.static_data,
      params_def: formData.params,
      params: testParams.value,
      result_type: formData.result_type,
      tree_config: formData.tree_config,
      field_mapping: formData.field_mapping,
      chart_config: formData.chart_config,
    });

    testResult.value = result;
    if (result.success) {
      ElMessage.success($t('data-source.testConnectionSuccess'));
      // 立即尝试渲染图表
      if (isChartResultType.value && result.data) {
        await nextTick();
        setTimeout(renderResultChart, 300);
      }
    }
  } catch (error: any) {
    ElMessage.error(error?.message || $t('data-source.testDataSourceFailed'));
  } finally {
    testLoading.value = false;
  }
}

/**
 * 添加参数
 */
function addParam() {
  if (!formData.params) {
    formData.params = [];
  }
  formData.params.push({
    name: '',
    label: $t('data-source.paramLabel'),
    type: 'string',
    required: false,
    default: null,
  });
}

/**
 * 删除参数
 */
function removeParam(index: number) {
  formData.params?.splice(index, 1);
}

/**
 * 添加字段映射
 */
function addFieldMapping() {
  if (!formData.field_mapping) {
    formData.field_mapping = {};
  }
  const key = `field_${Object.keys(formData.field_mapping).length + 1}`;
  formData.field_mapping[key] = '';
}

/**
 * 删除字段映射
 */
function removeFieldMapping(key: string) {
  if (formData.field_mapping) {
    delete formData.field_mapping[key];
  }
}

/**
 * 更新字段映射键
 */
function updateFieldMappingKey(oldKey: string, newKey: string) {
  if (formData.field_mapping && oldKey !== newKey) {
    const value = formData.field_mapping[oldKey];
    delete formData.field_mapping[oldKey];
    formData.field_mapping[newKey] = value || '';
  }
}

/**
 * 插入表名到 SQL 编辑器
 */
function handleInsertTable(tableName: string) {
  if (formData.source_type === 'sql' && sqlEditorRef.value) {
    const view = sqlEditorRef.value.getView();
    if (view) {
      const { from, to } = view.state.selection.main;
      view.dispatch({
        changes: { from, to, insert: tableName },
        selection: { anchor: from + tableName.length },
      });
      view.focus();
    }
  }
}

/**
 * 插入字段名到 SQL 编辑器
 */
function handleInsertField(tableName: string, fieldName: string) {
  if (formData.source_type === 'sql' && sqlEditorRef.value) {
    const view = sqlEditorRef.value.getView();
    if (view) {
      const insertText = `${tableName}.${fieldName}`;
      const { from, to } = view.state.selection.main;
      view.dispatch({
        changes: { from, to, insert: insertText },
        selection: { anchor: from + insertText.length },
      });
      view.focus();
    }
  }
}

/**
 * 处理数据库上下文选择
 */
function handleSelectContext(context: {
  database?: string;
  dbName: string;
  schema?: string;
}) {
  dbContext.value = context;
  // 更新 formData 的数据库连接
  formData.db_connection = context.dbName;
}

/**
 * 快速测试（在配置区直接测试）
 */
async function handleQuickTest() {
  // 切换到测试 Tab 并执行测试
  configActiveTab.value = 'test';
  await handleTest();
}
</script>

<template>
  <ElDialog
    v-model="dialogVisible"
    :show-close="false"
    fullscreen
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    body-class="h-[calc(100vh-80px)]"
    header-class="!pb-0"
    class="!pb-0"
  >
    <template #header>
      <div
        class="bg-background-deep flex h-14 w-full items-center justify-between rounded-lg px-6 shadow-sm"
      >
        <!-- 左侧：Logo和标题 -->
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <div
              class="bg-primary flex h-8 w-8 items-center justify-center rounded"
            >
              <span class="text-sm font-bold text-white">D</span>
            </div>
            <span class="text-foreground/70 text-base font-medium">{{
              title
            }}</span>
            <ElTag v-if="formData.code" size="small" type="info">
              {{ formData.code }}
            </ElTag>
          </div>
        </div>

        <!-- 中间：步骤条 -->
        <div class="absolute left-1/2 flex -translate-x-1/2 items-center">
          <template v-for="(step, index) in steps" :key="index">
            <div
              class="flex cursor-pointer items-center px-4 py-1"
              @click="index < currentStep ? (currentStep = index) : null"
            >
              <div
                class="flex items-center justify-center rounded-full border px-3 py-1 text-sm transition-all"
                :class="[
                  index === currentStep
                    ? 'border-primary bg-primary/10 text-primary font-medium'
                    : index < currentStep
                      ? 'border-primary/50 text-primary/80 bg-transparent'
                      : 'border-border text-muted-foreground bg-transparent',
                ]"
              >
                <span
                  class="mr-2 flex h-5 w-5 items-center justify-center rounded-full text-xs"
                  :class="
                    index === currentStep
                      ? 'bg-primary text-white'
                      : index < currentStep
                        ? 'bg-primary/80 text-white'
                        : 'bg-muted text-muted-foreground'
                  "
                >
                  {{ step.index }}
                </span>
                {{ step.title }}
              </div>
            </div>
            <div
              v-if="index < steps.length - 1"
              class="bg-border h-[1px] w-8"
              :class="{ 'bg-primary/50': index < currentStep }"
            ></div>
          </template>
        </div>

        <!-- 右侧：操作按钮 -->
        <div class="flex items-center gap-3">
          <ElButton v-if="canGoPrev" @click="handlePrev">
            {{ $t('data-source.previousStep') }}
          </ElButton>
          <ElButton
            v-if="!isLastStep"
            type="primary"
            :disabled="!canGoNext"
            @click="handleNext"
          >
            {{ $t('data-source.nextStep') }}
          </ElButton>
          <ElButton
            v-if="isLastStep"
            type="primary"
            :loading="loading"
            @click="handleSave"
          >
            {{ $t('data-source.save') }}
          </ElButton>
          <ElButton @click="handleClose">
            {{ $t('data-source.close') }}
          </ElButton>
        </div>
      </div>
    </template>

    <!-- 步骤内容 -->
    <div class="h-full overflow-hidden">
      <!-- 步骤1: 基础信息 -->
      <div
        v-show="currentStep === 0"
        class="flex h-full items-center justify-center overflow-y-auto"
      >
        <div class="align-self-center w-[600px]">
          <div class="border-border bg-card rounded-lg border p-8 shadow-sm">
            <h3 class="mb-6 text-center text-lg font-medium">
              {{ $t('data-source.basicInfoConfig') }}
            </h3>
            <ElForm :model="formData" label-width="100px" label-position="top">
              <ElFormItem :label="$t('data-source.dataSourceName')" required>
                <ElInput
                  v-model="formData.name"
                  :placeholder="$t('data-source.inputDataSourceName')"
                  clearable
                />
              </ElFormItem>
              <ElFormItem :label="$t('data-source.code')" required>
                <ElInput
                  v-model="formData.code"
                  :placeholder="$t('data-source.codePlaceholder')"
                  :disabled="isEditMode"
                  clearable
                />
                <div
                  v-if="
                    formData.code &&
                    !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(formData.code)
                  "
                  class="el-form-item__error"
                >
                  {{ $t('data-source.codeFormatError') }}
                </div>
              </ElFormItem>
              <ElFormItem :label="$t('data-source.dataSourceType')" required>
                <ElRadioGroup v-model="formData.source_type" class="w-full">
                  <ElRadioButton
                    v-for="opt in sourceTypeOptions"
                    :key="opt.value"
                    :value="opt.value"
                  >
                    {{ opt.label }}
                  </ElRadioButton>
                </ElRadioGroup>
              </ElFormItem>
              <ElFormItem :label="$t('data-source.status')">
                <ElSwitch
                  v-model="formData.status"
                  :active-text="$t('data-source.enable')"
                  :inactive-text="$t('data-source.disable')"
                />
              </ElFormItem>
              <ElFormItem :label="$t('data-source.dataSourceDescription')">
                <ElInput
                  v-model="formData.description"
                  type="textarea"
                  :rows="3"
                  :placeholder="$t('data-source.inputDataSourceDescription')"
                />
              </ElFormItem>
            </ElForm>
          </div>
        </div>
      </div>

      <!-- 步骤2: 数据源配置 -->
      <div v-show="currentStep === 1" class="mt-3 h-full overflow-hidden pb-3">
        <!-- SQL 类型：使用 Splitter 布局 -->
        <template v-if="formData.source_type === 'sql'">
          <ElSplitter class="h-full">
            <!-- 左侧面板：手动模式显示数据库结构，AI模式显示AI配置 -->
            <ElSplitterPanel
              :size="20"
              class="bg-background mr-3 rounded-[8px] border"
            >
              <!-- 手动模式：数据库结构面板 -->
              <div v-show="sqlEditMode === 'manual'" class="h-full">
                <DbSchemaPanel
                  @insert-table="handleInsertTable"
                  @insert-field="handleInsertField"
                  @select-context="handleSelectContext"
                />
              </div>
              <!-- AI模式：AI配置面板 -->
              <div v-show="sqlEditMode === 'ai'" class="h-full">
                <AiSqlConfigPanel
                  ref="aiConfigPanelRef"
                  :db-connection="formData.db_connection"
                />
              </div>
            </ElSplitterPanel>

            <!-- 右侧面板：SQL 编辑器 + 配置 -->
            <ElSplitterPanel :size="80" class="rounded-[8px]">
              <ElSplitter layout="vertical" class="h-full">
                <!-- 右上：SQL 编辑器区域 -->
                <ElSplitterPanel
                  :size="55"
                  :min="30"
                  class="bg-background rounded-[8px] border"
                >
                  <div class="flex h-full flex-col">
                    <!-- 工具栏 -->
                    <div
                      class="border-border flex items-center justify-between border-b px-4 py-2"
                    >
                      <div class="flex items-center gap-2">
                        <!-- 模式切换按钮 -->
                        <!--                        <ElRadioGroup v-model="sqlEditMode">-->
                        <!--                          <ElRadioButton value="ai">-->
                        <!--                            <div class="flex items-center gap-1">-->
                        <!--                              <Sparkles class="h-3.5 w-3.5" />-->
                        <!--                              <span>{{ $t('data-source.aiMode') }}</span>-->
                        <!--                            </div>-->
                        <!--                          </ElRadioButton>-->
                        <!--                          <ElRadioButton value="manual">-->
                        <!--                            {{ $t('data-source.manualMode') }}-->
                        <!--                          </ElRadioButton>-->
                        <!--                        </ElRadioGroup>-->
                      </div>
                      <div class="flex items-center gap-4">
                        <div
                          v-if="sqlEditMode === 'manual'"
                          class="flex items-center gap-4"
                        >
                          <span class="text-sm font-medium"
                            >{{ $t('data-source.dbSchema') }}:</span
                          >
                          <div class="flex items-center gap-2">
                            <ElTag v-if="dbContext" type="primary" size="small">
                              {{ dbContextDisplay }}
                            </ElTag>
                            <span v-else class="text-muted-foreground text-sm">
                              {{ $t('data-source.selectDbSchema') }}
                            </span>
                          </div>
                        </div>

                        <ElTooltip
                          :content="$t('data-source.testConnection')"
                          placement="bottom"
                        >
                          <ElButton
                            type="primary"
                            plain
                            :icon="Play"
                            :loading="testLoading"
                            @click="handleQuickTest"
                          />
                        </ElTooltip>
                      </div>
                    </div>

                    <!-- 手动模式：单独的 SQL 编辑器 -->
                    <div
                      v-if="sqlEditMode === 'manual'"
                      class="flex-1 overflow-hidden p-3"
                    >
                      <CodeEditor
                        ref="sqlEditorRef"
                        v-model="formData.sql_content"
                        language="sql"
                        height="100%"
                        placeholder="SELECT u.id, u.username, u.nickname
FROM core_user u
WHERE u.is_deleted = 0
  AND (:status IS NULL OR u.status = :status)
ORDER BY u.sys_create_datetime DESC"
                        :line-numbers="true"
                        :line-wrapping="false"
                        :fold-gutter="true"
                        :highlight-active-line="true"
                        :bracket-matching="true"
                        :autocompletion="true"
                      />
                    </div>

                    <!-- AI模式：左侧问题输入 + 右侧代码显示 -->
                    <div v-else class="flex flex-1 overflow-hidden">
                      <!-- 左侧：问题输入区域 -->
                      <div class="border-border flex w-2/5 flex-col border-r">
                        <!-- <div class="border-border border-b px-3 py-2">
                          <span class="text-sm font-medium">{{
                            $t('data-source.describeYourQuery')
                          }}</span>
                        </div> -->
                        <div class="flex flex-1 flex-col gap-3 p-3">
                          <ElInput
                            v-model="aiUserQuestion"
                            type="textarea"
                            :rows="6"
                            :placeholder="$t('data-source.queryPlaceholder')"
                            resize="none"
                          />
                          <!-- 快速示例 -->
                          <div>
                            <div class="text-muted-foreground mb-1 text-xs">
                              {{ $t('data-source.quickExamples') }}:
                            </div>
                            <div class="flex flex-wrap gap-1">
                              <ElButton
                                v-for="example in quickExamples"
                                :key="example"
                                size="small"
                                text
                                class="!px-1 !text-xs"
                                @click="aiUserQuestion = example"
                              >
                                {{ example }}
                              </ElButton>
                            </div>
                          </div>
                          <!-- 生成按钮 -->
                          <ElButton
                            type="primary"
                            :loading="aiGenerating"
                            plain
                            :disabled="!aiUserQuestion.trim()"
                            @click="handleAiGenerate"
                          >
                            <Sparkles class="mr-1 h-4 w-4" />
                            {{
                              aiGenerating
                                ? $t('data-source.generating')
                                : $t('data-source.generateSql')
                            }}
                          </ElButton>
                          <!-- 生成思路 -->
                          <div
                            v-if="aiResult?.thought"
                            class="bg-muted/50 rounded p-2"
                          >
                            <div
                              class="text-muted-foreground mb-1 text-xs font-medium"
                            >
                              {{ $t('data-source.generationThought') }}
                            </div>
                            <div class="text-muted-foreground text-xs">
                              {{ aiResult.thought }}
                            </div>
                          </div>
                        </div>
                      </div>
                      <!-- 右侧：代码显示区域 -->
                      <div class="flex w-3/5 flex-col">
                        <!-- <div class="border-border border-b px-3 py-2">
                          <span class="text-sm font-medium">{{
                            $t('data-source.generatedSql')
                          }}</span>
                        </div> -->
                        <div class="flex-1 overflow-hidden p-3">
                          <CodeEditor
                            ref="sqlEditorRef"
                            v-model="formData.sql_content"
                            language="sql"
                            height="100%"
                            :placeholder="$t('data-source.aiSqlPlaceholder')"
                            :line-numbers="true"
                            :line-wrapping="false"
                            :fold-gutter="true"
                            :highlight-active-line="true"
                            :bracket-matching="true"
                            :autocompletion="true"
                          />
                        </div>
                      </div>
                    </div>

                    <!-- 提示 -->
                    <!-- <div class="border-border border-t px-4 py-1.5">
                      <span class="text-muted-foreground text-xs">
                        {{ $t('data-source.tip') }}:
                        {{ $t('data-source.useParamPlaceholder') }}
                        <code class="bg-muted rounded px-1">:param</code>
                        {{ $t('data-source.onlySelectQuery') }}
                      </span>
                    </div> -->
                  </div>
                </ElSplitterPanel>

                <!-- 右下：配置 Tabs -->
                <ElSplitterPanel
                  :size="45"
                  :min="25"
                  class="bg-background mt-3 rounded-[8px] border"
                >
                  <div class="flex h-full overflow-hidden">
                    <!-- 左侧：竖向 Tab 切换 -->
                    <div class="h-full flex-shrink-0 p-2">
                      <ZqTabs
                        v-model="configActiveTab"
                        :items="configTabs"
                        vertical
                      />
                    </div>

                    <!-- 右侧：内容区域 -->
                    <div class="flex flex-1 flex-col overflow-hidden">
                      <!-- 公共部分：结果类型选择（仅在结果处理和测试结果 Tab 下显示） -->
                      <div
                        v-show="
                          configActiveTab === 'result' ||
                          configActiveTab === 'test'
                        "
                        class="flex-shrink-0 pt-4"
                      >
                        <!-- <div
                          class="text-muted-foreground mb-1 text-xs font-medium"
                        >
                          {{ $t('data-source.resultType') }}
                        </div> -->
                        <ElRadioGroup v-model="formData.result_type">
                          <ElRadioButton
                            v-for="opt in resultTypeOptions"
                            :key="opt.value"
                            :value="opt.value"
                          >
                            {{ opt.label }}
                          </ElRadioButton>
                        </ElRadioGroup>
                      </div>

                      <!-- Tab 内容 -->
                      <div class="flex-1 overflow-hidden">
                        <!-- 参数定义 -->
                        <div
                          v-show="configActiveTab === 'params'"
                          class="h-full"
                        >
                          <ElScrollbar class="h-full">
                            <div class="p-4">
                              <div
                                class="mb-3 flex items-center justify-between"
                              >
                                <span class="text-muted-foreground text-sm">{{
                                  $t('data-source.defineDataSourceParams')
                                }}</span>
                                <ElButton
                                  type="primary"
                                  :icon="CirclePlus"
                                  size="small"
                                  @click="addParam"
                                >
                                  {{ $t('data-source.addParam') }}
                                </ElButton>
                              </div>
                              <ElTable
                                :data="formData.params || []"
                                border
                                stripe
                                max-height="180"
                              >
                                <ElTableColumn
                                  :label="$t('data-source.paramName')"
                                  width="140"
                                >
                                  <template #default="{ row }">
                                    <ElInput
                                      v-model="row.name"
                                      placeholder="name"
                                      size="small"
                                    />
                                  </template>
                                </ElTableColumn>
                                <ElTableColumn
                                  :label="$t('data-source.paramLabel')"
                                  width="140"
                                >
                                  <template #default="{ row }">
                                    <ElInput
                                      v-model="row.label"
                                      placeholder="名称"
                                      size="small"
                                    />
                                  </template>
                                </ElTableColumn>
                                <ElTableColumn
                                  :label="$t('data-source.paramType')"
                                  width="110"
                                >
                                  <template #default="{ row }">
                                    <ElSelect
                                      v-model="row.type"
                                      size="small"
                                      class="w-full"
                                    >
                                      <ElOption
                                        v-for="opt in paramTypeOptions"
                                        :key="opt.value"
                                        :label="opt.label"
                                        :value="opt.value"
                                      />
                                    </ElSelect>
                                  </template>
                                </ElTableColumn>
                                <ElTableColumn
                                  :label="$t('data-source.paramValue')"
                                  width="120"
                                >
                                  <template #default="{ row }">
                                    <ElInput
                                      v-model="row.default"
                                      placeholder="默认值"
                                      size="small"
                                    />
                                  </template>
                                </ElTableColumn>
                                <ElTableColumn
                                  :label="$t('data-source.required')"
                                  width="70"
                                  align="center"
                                >
                                  <template #default="{ row }">
                                    <ElSwitch
                                      v-model="row.required"
                                      size="small"
                                    />
                                  </template>
                                </ElTableColumn>
                                <ElTableColumn
                                  :label="$t('data-source.action')"
                                  width="70"
                                  align="center"
                                >
                                  <template #default="{ $index }">
                                    <ElButton
                                      type="danger"
                                      :icon="Trash"
                                      size="small"
                                      circle
                                      @click="removeParam($index)"
                                    />
                                  </template>
                                </ElTableColumn>
                              </ElTable>
                            </div>
                          </ElScrollbar>
                        </div>

                        <!-- 结果处理 -->
                        <div
                          v-show="configActiveTab === 'result'"
                          class="h-full"
                        >
                          <ElSplitter class="h-full">
                            <!-- 左侧：结果处理配置 -->
                            <ElSplitterPanel :size="50">
                              <ElScrollbar class="h-full">
                                <div class="p-4">
                                  <ElForm :model="formData" label-width="100px">
                                    <!-- 结果类型提示 -->
                                    <ElAlert
                                      v-if="formData.result_type === 'list'"
                                      type="primary"
                                      show-icon
                                      class="mb-4"
                                      :title="
                                        $t('data-source.resultTypeListDesc')
                                      "
                                    />
                                    <ElAlert
                                      v-else-if="
                                        formData.result_type === 'tree'
                                      "
                                      type="primary"
                                      show-icon
                                      class="mb-4"
                                      :title="
                                        $t('data-source.resultTypeTreeDesc')
                                      "
                                    />
                                    <ElAlert
                                      v-else-if="
                                        formData.result_type === 'object'
                                      "
                                      type="primary"
                                      show-icon
                                      class="mb-4"
                                      :title="
                                        $t('data-source.resultTypeObjectDesc')
                                      "
                                    />
                                    <ElAlert
                                      v-else-if="
                                        formData.result_type === 'value'
                                      "
                                      type="primary"
                                      show-icon
                                      class="mb-4"
                                      :title="
                                        $t('data-source.resultTypeValueDesc')
                                      "
                                    />
                                    <ElAlert
                                      v-else-if="
                                        formData.result_type === 'chart-axis'
                                      "
                                      type="primary"
                                      show-icon
                                      class="mb-4"
                                      :title="
                                        $t(
                                          'data-source.resultTypeChartAxisDesc',
                                        )
                                      "
                                    />
                                    <ElAlert
                                      v-else-if="
                                        formData.result_type === 'chart-pie'
                                      "
                                      type="primary"
                                      show-icon
                                      class="mb-4"
                                      :title="
                                        $t('data-source.resultTypeChartPieDesc')
                                      "
                                    />
                                    <ElAlert
                                      v-else-if="
                                        formData.result_type === 'chart-gauge'
                                      "
                                      type="primary"
                                      show-icon
                                      class="mb-4"
                                      :title="
                                        $t(
                                          'data-source.resultTypeChartGaugeDesc',
                                        )
                                      "
                                    />
                                    <ElAlert
                                      v-else-if="
                                        formData.result_type === 'chart-radar'
                                      "
                                      type="primary"
                                      show-icon
                                      class="mb-4"
                                      :title="
                                        $t(
                                          'data-source.resultTypeChartRadarDesc',
                                        )
                                      "
                                    />
                                    <ElAlert
                                      v-else-if="
                                        formData.result_type === 'chart-scatter'
                                      "
                                      type="primary"
                                      show-icon
                                      class="mb-4"
                                      :title="
                                        $t(
                                          'data-source.resultTypeChartScatterDesc',
                                        )
                                      "
                                    />
                                    <ElAlert
                                      v-else-if="
                                        formData.result_type === 'chart-heatmap'
                                      "
                                      type="primary"
                                      show-icon
                                      class="mb-4"
                                      :title="
                                        $t(
                                          'data-source.resultTypeChartHeatmapDesc',
                                        )
                                      "
                                    />
                                    <!-- 树形配置 -->
                                    <template
                                      v-if="formData.result_type === 'tree'"
                                    >
                                      <ElDivider content-position="left">
                                        {{
                                          $t('data-source.treeConversionConfig')
                                        }}
                                      </ElDivider>
                                      <ElRow :gutter="16">
                                        <ElCol :span="8">
                                          <ElFormItem label="ID字段">
                                            <ElInput
                                              v-model="
                                                formData.tree_config!.id_field
                                              "
                                              placeholder="id"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                        <ElCol :span="8">
                                          <ElFormItem label="父级字段">
                                            <ElInput
                                              v-model="
                                                formData.tree_config!
                                                  .parent_field
                                              "
                                              placeholder="parent_id"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                        <ElCol :span="8">
                                          <ElFormItem label="子节点字段">
                                            <ElInput
                                              v-model="
                                                formData.tree_config!
                                                  .children_field
                                              "
                                              placeholder="children"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                      </ElRow>
                                    </template>
                                    <!-- 轴向图表配置 -->
                                    <template
                                      v-if="
                                        formData.result_type === 'chart-axis'
                                      "
                                    >
                                      <ElDivider content-position="left">
                                        {{ $t('data-source.axisChartConfig') }}
                                        <ElTooltip
                                          content="适用于折线图、柱状图、面积图"
                                        >
                                          <span
                                            class="text-muted-foreground ml-1 cursor-help"
                                            >(?)</span>
                                        </ElTooltip>
                                      </ElDivider>
                                      <ElFormItem
                                        :label="$t('data-source.xAxisField')"
                                      >
                                        <ElInput
                                          v-model="
                                            formData.chart_config!.x_field
                                          "
                                          placeholder="如：month"
                                        />
                                      </ElFormItem>
                                      <ElFormItem
                                        :label="$t('data-source.seriesField')"
                                      >
                                        <ElInput
                                          v-model="chartSeriesFieldsStr"
                                          :placeholder="
                                            $t(
                                              'data-source.multipleFieldsComma',
                                              { example: 'sales,profit' },
                                            )
                                          "
                                        />
                                        <div
                                          class="text-muted-foreground mt-1 text-xs"
                                        >
                                          {{
                                            $t('data-source.dataFieldsForChart')
                                          }}
                                        </div>
                                      </ElFormItem>
                                      <ElFormItem
                                        :label="$t('data-source.seriesName')"
                                      >
                                        <ElInput
                                          v-model="chartSeriesNamesStr"
                                          :placeholder="
                                            $t(
                                              'data-source.multipleNamesComma',
                                              { example: '销售额,利润' },
                                            )
                                          "
                                        />
                                        <div
                                          class="text-muted-foreground mt-1 text-xs"
                                        >
                                          {{
                                            $t(
                                              'data-source.optionalLegendNames',
                                            )
                                          }}
                                        </div>
                                      </ElFormItem>
                                    </template>
                                    <!-- 饼图配置 -->
                                    <template
                                      v-if="
                                        formData.result_type === 'chart-pie'
                                      "
                                    >
                                      <ElDivider content-position="left">
                                        {{ $t('data-source.pieChartConfig') }}
                                        <ElTooltip content="适用于饼图、漏斗图">
                                          <span
                                            class="text-muted-foreground ml-1 cursor-help"
                                            >(?)</span>
                                        </ElTooltip>
                                      </ElDivider>
                                      <ElRow :gutter="16">
                                        <ElCol :span="12">
                                          <ElFormItem
                                            :label="$t('data-source.nameField')"
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!
                                                  .name_field
                                              "
                                              placeholder="如：category"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                        <ElCol :span="12">
                                          <ElFormItem
                                            :label="
                                              $t('data-source.valueField')
                                            "
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!
                                                  .value_field
                                              "
                                              placeholder="如：amount"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                      </ElRow>
                                    </template>
                                    <!-- 仪表盘配置 -->
                                    <template
                                      v-if="
                                        formData.result_type === 'chart-gauge'
                                      "
                                    >
                                      <ElDivider content-position="left">
                                        {{ $t('data-source.gaugeChartConfig') }}
                                        <ElTooltip
                                          content="适用于仪表盘、进度图"
                                        >
                                          <span
                                            class="text-muted-foreground ml-1 cursor-help"
                                            >(?)</span>
                                        </ElTooltip>
                                      </ElDivider>
                                      <ElRow :gutter="16">
                                        <ElCol :span="8">
                                          <ElFormItem
                                            :label="
                                              $t('data-source.valueField')
                                            "
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!
                                                  .value_field
                                              "
                                              placeholder="如：value"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                        <ElCol :span="8">
                                          <ElFormItem
                                            :label="$t('data-source.nameField')"
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!
                                                  .name_field
                                              "
                                              :placeholder="
                                                $t('data-source.optionalName')
                                              "
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                        <ElCol :span="8">
                                          <ElFormItem
                                            :label="$t('data-source.maxField')"
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!.max_field
                                              "
                                              :placeholder="
                                                $t('data-source.optionalMax')
                                              "
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                      </ElRow>
                                    </template>
                                    <!-- 雷达图配置 -->
                                    <template
                                      v-if="
                                        formData.result_type === 'chart-radar'
                                      "
                                    >
                                      <ElDivider content-position="left">
                                        {{ $t('data-source.radarChartConfig') }}
                                      </ElDivider>
                                      <ElRow :gutter="16">
                                        <ElCol :span="12">
                                          <ElFormItem
                                            :label="
                                              $t(
                                                'data-source.indicatorNameField',
                                              )
                                            "
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!
                                                  .indicator_field
                                              "
                                              placeholder="如：name"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                        <ElCol :span="12">
                                          <ElFormItem
                                            :label="$t('data-source.maxField')"
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!.max_field
                                              "
                                              placeholder="如：max"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                      </ElRow>
                                      <ElFormItem
                                        :label="$t('data-source.valueField')"
                                      >
                                        <ElInput
                                          v-model="chartValueFieldsStr"
                                          :placeholder="
                                            $t(
                                              'data-source.multipleFieldsComma',
                                              { example: 'budget,actual' },
                                            )
                                          "
                                        />
                                        <div
                                          class="text-muted-foreground mt-1 text-xs"
                                        >
                                          {{
                                            $t('data-source.oneFieldPerSeries')
                                          }}
                                        </div>
                                      </ElFormItem>
                                      <ElFormItem
                                        :label="$t('data-source.seriesName')"
                                      >
                                        <ElInput
                                          v-model="chartSeriesNamesStr"
                                          :placeholder="
                                            $t(
                                              'data-source.multipleNamesComma',
                                              { example: '预算,实际' },
                                            )
                                          "
                                        />
                                      </ElFormItem>
                                    </template>
                                    <!-- 散点图配置 -->
                                    <template
                                      v-if="
                                        formData.result_type === 'chart-scatter'
                                      "
                                    >
                                      <ElDivider content-position="left">
                                        {{
                                          $t('data-source.scatterChartConfig')
                                        }}
                                        <ElTooltip
                                          content="适用于散点图、气泡图"
                                        >
                                          <span
                                            class="text-muted-foreground ml-1 cursor-help"
                                            >(?)</span>
                                        </ElTooltip>
                                      </ElDivider>
                                      <ElRow :gutter="16">
                                        <ElCol :span="12">
                                          <ElFormItem
                                            :label="
                                              $t('data-source.xCoordinateField')
                                            "
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!.x_field
                                              "
                                              placeholder="如：x"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                        <ElCol :span="12">
                                          <ElFormItem
                                            :label="
                                              $t('data-source.yCoordinateField')
                                            "
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!.y_field
                                              "
                                              placeholder="如：y"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                      </ElRow>
                                      <ElRow :gutter="16">
                                        <ElCol :span="12">
                                          <ElFormItem
                                            :label="$t('data-source.sizeField')"
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!
                                                  .size_field
                                              "
                                              :placeholder="
                                                $t(
                                                  'data-source.optionalBubbleChart',
                                                )
                                              "
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                        <ElCol :span="12">
                                          <ElFormItem
                                            :label="$t('data-source.nameField')"
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!
                                                  .name_field
                                              "
                                              :placeholder="
                                                $t('data-source.optionalName')
                                              "
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                      </ElRow>
                                    </template>
                                    <!-- 热力图配置 -->
                                    <template
                                      v-if="
                                        formData.result_type === 'chart-heatmap'
                                      "
                                    >
                                      <ElDivider content-position="left">
                                        {{
                                          $t('data-source.heatmapChartConfig')
                                        }}
                                      </ElDivider>
                                      <ElRow :gutter="16">
                                        <ElCol :span="8">
                                          <ElFormItem
                                            :label="
                                              $t('data-source.xCoordinateField')
                                            "
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!.x_field
                                              "
                                              placeholder="如：x"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                        <ElCol :span="8">
                                          <ElFormItem
                                            :label="
                                              $t('data-source.yCoordinateField')
                                            "
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!.y_field
                                              "
                                              placeholder="如：y"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                        <ElCol :span="8">
                                          <ElFormItem
                                            :label="
                                              $t('data-source.valueField')
                                            "
                                          >
                                            <ElInput
                                              v-model="
                                                formData.chart_config!
                                                  .value_field
                                              "
                                              placeholder="如：value"
                                            />
                                          </ElFormItem>
                                        </ElCol>
                                      </ElRow>
                                    </template>
                                    <!-- 字段映射 -->
                                    <ElDivider content-position="left">
                                      {{ $t('data-source.fieldMapping') }}
                                      <ElTooltip
                                        :content="
                                          $t('data-source.fieldNameMapping')
                                        "
                                      >
                                        <span
                                          class="text-muted-foreground ml-1 cursor-help"
                                          >(?)</span
                                        >
                                      </ElTooltip>
                                    </ElDivider>
                                    <div class="mb-2">
                                      <ElButton
                                        type="primary"
                                        :icon="CirclePlus"
                                        size="small"
                                        @click="addFieldMapping"
                                      >
                                        {{ $t('data-source.addMapping') }}
                                      </ElButton>
                                    </div>
                                    <div
                                      v-for="(_, key) in formData.field_mapping"
                                      :key="key"
                                      class="mb-2 flex items-center gap-2"
                                    >
                                      <ElInput
                                        :model-value="key"
                                        :placeholder="
                                          $t('data-source.originalField')
                                        "
                                        class="w-40"
                                        @update:model-value="
                                          (v: string) =>
                                            updateFieldMappingKey(
                                              key as string,
                                              v,
                                            )
                                        "
                                      />
                                      <span class="text-muted-foreground">-></span>
                                      <ElInput
                                        v-model="
                                          formData.field_mapping![key as string]
                                        "
                                        :placeholder="
                                          $t('data-source.mappedField')
                                        "
                                        class="w-40"
                                      />
                                      <ElButton
                                        type="danger"
                                        :icon="Trash"
                                        size="small"
                                        circle
                                        @click="
                                          removeFieldMapping(key as string)
                                        "
                                      />
                                    </div>
                                    <!-- 缓存配置 -->
                                    <ElDivider content-position="left">
                                      {{ $t('data-source.cacheConfig') }}
                                    </ElDivider>
                                    <ElRow :gutter="16">
                                      <ElCol :span="8">
                                        <ElFormItem
                                          :label="$t('data-source.enableCache')"
                                        >
                                          <ElSwitch
                                            v-model="formData.cache_enabled"
                                          />
                                        </ElFormItem>
                                      </ElCol>
                                      <ElCol :span="16">
                                        <ElFormItem
                                          v-if="formData.cache_enabled"
                                          :label="$t('data-source.cacheTime')"
                                        >
                                          <ElInputNumber
                                            v-model="formData.cache_ttl"
                                            :min="0"
                                            :max="86400"
                                          />
                                          <span
                                            class="text-muted-foreground ml-2 text-xs"
                                            >{{
                                              $t('data-source.cacheTimeUnit')
                                            }}</span
                                          >
                                        </ElFormItem>
                                      </ElCol>
                                    </ElRow>
                                  </ElForm>
                                </div>
                              </ElScrollbar>
                            </ElSplitterPanel>
                          </ElSplitter>
                        </div>

                        <!-- 测试 -->
                        <div v-show="configActiveTab === 'test'" class="h-full">
                          <div class="flex h-full flex-col">
                            <!-- 顶部：测试参数和按钮 -->
                            <div class="flex-shrink-0 p-4 pb-2">
                              <!-- 测试参数 -->
                              <ElCard
                                v-if="
                                  formData.params && formData.params.length > 0
                                "
                                shadow="never"
                                class="mb-3"
                              >
                                <template #header>
                                  <span class="text-sm font-medium">{{
                                    $t('data-source.testParams')
                                  }}</span>
                                </template>
                                <ElForm label-width="100px">
                                  <ElRow :gutter="16">
                                    <ElCol
                                      v-for="param in formData.params"
                                      :key="param.name"
                                      :span="12"
                                    >
                                      <ElFormItem
                                        :label="param.label || param.name"
                                      >
                                        <ElInput
                                          v-model="testParams[param.name]"
                                          :placeholder="
                                            param.default !== null
                                              ? String(param.default)
                                              : ''
                                          "
                                        />
                                      </ElFormItem>
                                    </ElCol>
                                  </ElRow>
                                </ElForm>
                              </ElCard>
                              <!-- 测试按钮 -->
                              <!-- <div class="flex justify-center">
                              <ElButton
                                type="primary"
                                :icon="Play"
                                :loading="testLoading"
                                @click="handleTest"
                              >
                                {{ $t('data-source.executeTest') }}
                              </ElButton>
                            </div> -->
                            </div>

                            <!-- 底部：测试结果（左右分栏） -->
                            <div class="min-h-0 flex-1">
                              <!-- 加载状态 -->
                              <div
                                v-show="testLoading"
                                class="flex h-full items-center justify-center"
                              >
                                <div class="flex flex-col items-center">
                                  <ElIcon class="is-loading mb-2" :size="32">
                                    <Loading />
                                  </ElIcon>
                                  <span class="text-muted-foreground text-sm">{{
                                    $t('data-source.querying')
                                  }}</span>
                                </div>
                              </div>

                              <!-- 测试结果 -->
                              <div
                                v-show="!testLoading && testResult"
                                class="bg-background flex h-full flex-col rounded-[8px]"
                              >
                                <!-- Header -->
                                <div
                                  class="border-border m-3 flex items-center gap-2"
                                >
                                  <span class="text-sm font-medium">{{
                                    $t('data-source.testResult')
                                  }}</span>
                                  <ElTag
                                    :type="
                                      testResult?.success ? 'success' : 'danger'
                                    "
                                    size="small"
                                  >
                                    {{
                                      testResult?.success
                                        ? $t('data-source.success')
                                        : $t('data-source.failed')
                                    }}
                                  </ElTag>
                                  <span class="text-muted-foreground text-xs">
                                    {{
                                      $t('data-source.returnedData', {
                                        count: testResult?.total || 0,
                                      })
                                    }}
                                  </span>
                                  <ElTag
                                    v-if="
                                      testResult?.total &&
                                      testResult?.limited &&
                                      testResult.total >= testResult.limited
                                    "
                                    type="warning"
                                    size="small"
                                  >
                                    {{
                                      $t('data-source.reachedLimit', {
                                        limit: testResult?.limited,
                                      })
                                    }}
                                  </ElTag>
                                </div>

                                <!-- 左右分栏：图表/表格 + 数据 -->
                                <ElSplitter class="flex-1">
                                  <!-- 左侧：图表或表格 -->
                                  <ElSplitterPanel :size="50">
                                    <div class="h-full p-2">
                                      <!-- 图表类型：显示 ECharts -->
                                      <EchartsUI
                                        v-show="isChartResultType"
                                        ref="previewChartRef"
                                        class="h-full w-full"
                                      />

                                      <!-- 非图表类型：显示表格 -->
                                      <ElScrollbar
                                        v-show="
                                          !isChartResultType &&
                                          testResult?.data !== undefined
                                        "
                                        class="h-full"
                                      >
                                        <!-- 列表类型：数组数据 -->
                                        <ElTable
                                          v-if="
                                            Array.isArray(testResult?.data) &&
                                            testResult.data.length > 0
                                          "
                                          :data="testResult.data"
                                          border
                                          stripe
                                          size="small"
                                          max-height="100%"
                                        >
                                          <ElTableColumn
                                            v-for="key in Object.keys(
                                              testResult.data[0],
                                            )"
                                            :key="key"
                                            :prop="key"
                                            :label="key"
                                            min-width="120"
                                            show-overflow-tooltip
                                          />
                                        </ElTable>

                                        <!-- 单对象类型：对象数据显示为一行 -->
                                        <ElTable
                                          v-else-if="
                                            testResult?.data &&
                                            typeof testResult.data ===
                                              'object' &&
                                            !Array.isArray(testResult.data)
                                          "
                                          :data="[testResult.data]"
                                          border
                                          stripe
                                          size="small"
                                          max-height="100%"
                                        >
                                          <ElTableColumn
                                            v-for="key in Object.keys(
                                              testResult.data,
                                            )"
                                            :key="key"
                                            :prop="key"
                                            :label="key"
                                            min-width="120"
                                            show-overflow-tooltip
                                          />
                                        </ElTable>

                                        <!-- 单值类型：显示为一行一列 -->
                                        <ElTable
                                          v-else-if="
                                            testResult?.data !== null &&
                                            testResult?.data !== undefined &&
                                            (typeof testResult.data ===
                                              'string' ||
                                              typeof testResult.data ===
                                                'number' ||
                                              typeof testResult.data ===
                                                'boolean')
                                          "
                                          :data="[{ value: testResult.data }]"
                                          border
                                          stripe
                                          size="small"
                                          max-height="100%"
                                        >
                                          <ElTableColumn
                                            prop="value"
                                            label="Value"
                                            min-width="120"
                                            show-overflow-tooltip
                                          />
                                        </ElTable>

                                        <div
                                          v-else
                                          class="text-muted-foreground flex h-full items-center justify-center text-sm"
                                        >
                                          {{ $t('data-source.noData') }}
                                        </div>
                                      </ElScrollbar>
                                    </div>
                                  </ElSplitterPanel>
                                  <!-- 右侧：数据 -->
                                  <ElSplitterPanel :size="50">
                                    <ElScrollbar class="h-full">
                                      <pre
                                        class="bg-muted m-2 rounded p-3 text-xs"
                                        >{{
                                          JSON.stringify(
                                            testResult?.data,
                                            null,
                                            2,
                                          )
                                        }}</pre>
                                    </ElScrollbar>
                                  </ElSplitterPanel>
                                </ElSplitter>
                              </div>

                              <!-- 无结果提示 -->
                              <div
                                v-show="!testLoading && !testResult"
                                class="text-muted-foreground flex h-full items-center justify-center text-sm"
                              >
                                {{ $t('data-source.clickTestToExecute') }}
                              </div>
                            </div>
                          </div>
                        </div>
                        <!-- 关闭 Tab 内容 div -->
                      </div>
                      <!-- 关闭右侧内容区域 div -->
                    </div>
                    <!-- 关闭 bg-card flex h-full overflow-hidden div -->
                  </div>
                </ElSplitterPanel>
              </ElSplitter>
            </ElSplitterPanel>
          </ElSplitter>
        </template>

        <!-- API/静态数据类型：保持原有布局 -->
        <div v-else class="flex h-full gap-3 overflow-hidden p-4">
          <!-- 主配置区 -->
          <div
            class="border-border bg-card w-[50%] flex-shrink-0 rounded-lg border p-4"
          >
            <!-- API 配置 -->
            <template v-if="formData.source_type === 'api'">
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-medium">{{
                  $t('data-source.apiConfig')
                }}</span>
                <div class="flex items-center gap-2">
                  <ElButton
                    size="small"
                    :icon="Eye"
                    @click="showRequestPreview = true"
                  >
                    {{ $t('data-source.viewRequest') }}
                  </ElButton>
                  <ElButton
                    type="primary"
                    size="small"
                    :icon="Play"
                    :loading="testLoading"
                    @click="handleQuickTest"
                  >
                    {{ $t('data-source.test') }}
                  </ElButton>
                </div>
              </div>
              <!-- URL 输入行 -->
              <div class="mb-3 flex items-center gap-2">
                <ElSelect
                  v-model="formData.api_method"
                  style="width: 110px"
                  class="flex-shrink-0"
                >
                  <ElOption
                    v-for="opt in httpMethodOptions"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </ElSelect>
                <ElInput
                  v-model="formData.api_url"
                  :placeholder="$t('data-source.urlPlaceholder')"
                  class="flex-1"
                />
              </div>
              <!-- API 配置 Tabs -->
              <ZqTabs
                v-model="apiConfigTab"
                :items="apiConfigTabs"
                class="mb-3 w-[500px]"
              />

              <!-- 基本 Panel -->
              <div v-if="apiConfigTab === 'basic'" class="api-tab-panel">
                <ElForm :model="formData" label-width="100px">
                  <ElRow :gutter="16">
                    <ElCol :span="12">
                      <ElFormItem :label="$t('data-source.timeout')">
                        <div class="flex items-center">
                          <ElInputNumber
                            v-model="formData.api_timeout"
                            :min="1"
                            :max="300"
                            class="w-full"
                          />
                          <span
                            class="text-muted-foreground ml-2 flex-shrink-0 text-xs"
                            >{{ $t('data-source.second') }}</span
                          >
                        </div>
                      </ElFormItem>
                    </ElCol>
                    <ElCol :span="12">
                      <ElFormItem :label="$t('data-source.dataPath')">
                        <ElInput
                          v-model="formData.api_data_path"
                          :placeholder="$t('data-source.dataPathPlaceholder')"
                        />
                      </ElFormItem>
                    </ElCol>
                  </ElRow>
                </ElForm>
              </div>

              <!-- 认证 Panel -->
              <div v-else-if="apiConfigTab === 'auth'" class="api-tab-panel">
                <ElForm :model="formData" label-width="100px">
                  <ElFormItem :label="$t('data-source.authType')">
                    <ElRadioGroup v-model="formData.api_auth_type">
                      <ElRadioButton
                        v-for="opt in authTypeOptions"
                        :key="opt.value"
                        :value="opt.value"
                      >
                        {{ opt.label }}
                      </ElRadioButton>
                    </ElRadioGroup>
                  </ElFormItem>
                  <!-- Bearer Token -->
                  <template v-if="formData.api_auth_type === 'bearer_token'">
                    <ElFormItem label="Token">
                      <ElInput
                        v-model="ensureAuthConfig().token"
                        :placeholder="$t('data-source.bearerTokenPlaceholder')"
                        type="password"
                        show-password
                      />
                    </ElFormItem>
                  </template>
                  <!-- Basic Auth -->
                  <template v-if="formData.api_auth_type === 'basic_auth'">
                    <ElRow :gutter="16">
                      <ElCol :span="12">
                        <ElFormItem :label="$t('data-source.username')">
                          <ElInput
                            v-model="ensureAuthConfig().username"
                            :placeholder="$t('data-source.usernamePlaceholder')"
                          />
                        </ElFormItem>
                      </ElCol>
                      <ElCol :span="12">
                        <ElFormItem :label="$t('data-source.password')">
                          <ElInput
                            v-model="ensureAuthConfig().password"
                            type="password"
                            show-password
                            :placeholder="$t('data-source.passwordPlaceholder')"
                          />
                        </ElFormItem>
                      </ElCol>
                    </ElRow>
                  </template>
                  <!-- API Key -->
                  <template v-if="formData.api_auth_type === 'api_key'">
                    <ElRow :gutter="16">
                      <ElCol :span="8">
                        <ElFormItem :label="$t('data-source.keyPosition')">
                          <ElSelect
                            v-model="ensureAuthConfig().key_position"
                            class="w-full"
                          >
                            <ElOption
                              v-for="opt in keyPositionOptions"
                              :key="opt.value"
                              :label="opt.label"
                              :value="opt.value"
                            />
                          </ElSelect>
                        </ElFormItem>
                      </ElCol>
                      <ElCol :span="8">
                        <ElFormItem :label="$t('data-source.keyName')">
                          <ElInput
                            v-model="ensureAuthConfig().key_name"
                            placeholder="X-API-Key"
                          />
                        </ElFormItem>
                      </ElCol>
                      <ElCol :span="8">
                        <ElFormItem :label="$t('data-source.keyValue')">
                          <ElInput
                            v-model="ensureAuthConfig().key_value"
                            type="password"
                            show-password
                          />
                        </ElFormItem>
                      </ElCol>
                    </ElRow>
                  </template>
                </ElForm>
              </div>

              <!-- Query 参数 Panel -->
              <div v-else-if="apiConfigTab === 'query'" class="api-tab-panel">
                <div class="mb-2 flex items-center justify-between">
                  <span class="text-muted-foreground text-xs">
                    {{ $t('data-source.queryParamsHint') }}
                  </span>
                  <ElButton
                    type="primary"
                    :icon="CirclePlus"
                    size="small"
                    @click="addQueryParam"
                  >
                    {{ $t('data-source.addParam') }}
                  </ElButton>
                </div>
                <div class="kv-list">
                  <div class="kv-list__header">
                    <span class="kv-list__col kv-list__col--switch"></span>
                    <span class="kv-list__col kv-list__col--key">{{
                      $t('data-source.paramName')
                    }}</span>
                    <span class="kv-list__col kv-list__col--value">{{
                      $t('data-source.paramValue')
                    }}</span>
                    <span class="kv-list__col kv-list__col--desc">{{
                      $t('data-source.description')
                    }}</span>
                    <span class="kv-list__col kv-list__col--action"></span>
                  </div>
                  <div
                    v-for="(item, idx) in formData.api_query_params || []"
                    :key="idx"
                    class="kv-list__row"
                    :class="{ 'kv-list__row--disabled': !item.enabled }"
                  >
                    <span class="kv-list__col kv-list__col--switch">
                      <ElSwitch v-model="item.enabled" size="small" />
                    </span>
                    <span class="kv-list__col kv-list__col--key">
                      <ElInput
                        v-model="item.key"
                        placeholder="key"
                        size="small"
                      />
                    </span>
                    <span class="kv-list__col kv-list__col--value">
                      <ElInput
                        v-model="item.value"
                        placeholder="value"
                        size="small"
                      />
                    </span>
                    <span class="kv-list__col kv-list__col--desc">
                      <ElInput
                        v-model="item.description"
                        :placeholder="$t('data-source.description')"
                        size="small"
                      />
                    </span>
                    <span class="kv-list__col kv-list__col--action">
                      <ElButton
                        type="danger"
                        :icon="Trash"
                        size="small"
                        circle
                        @click="removeQueryParam(idx)"
                      />
                    </span>
                  </div>
                  <div
                    v-if="!formData.api_query_params?.length"
                    class="kv-list__empty"
                  >
                    {{ $t('data-source.noQueryParams') }}
                  </div>
                </div>
              </div>

              <!-- 请求头 Panel -->
              <div v-else-if="apiConfigTab === 'headers'" class="api-tab-panel">
                <div class="mb-2 flex items-center justify-between">
                  <span class="text-muted-foreground text-xs">
                    {{ $t('data-source.headersHint') }}
                  </span>
                  <ElButton
                    type="primary"
                    :icon="CirclePlus"
                    size="small"
                    @click="addHeaderItem"
                  >
                    {{ $t('data-source.addHeader') }}
                  </ElButton>
                </div>
                <div class="kv-list">
                  <div class="kv-list__header">
                    <span class="kv-list__col kv-list__col--switch"></span>
                    <span class="kv-list__col kv-list__col--key">{{
                      $t('data-source.headerName')
                    }}</span>
                    <span class="kv-list__col kv-list__col--value">{{
                      $t('data-source.headerValue')
                    }}</span>
                    <span class="kv-list__col kv-list__col--action"></span>
                  </div>
                  <div
                    v-for="(item, idx) in headerItems"
                    :key="idx"
                    class="kv-list__row"
                    :class="{ 'kv-list__row--disabled': !item.enabled }"
                  >
                    <span class="kv-list__col kv-list__col--switch">
                      <ElSwitch v-model="item.enabled" size="small" />
                    </span>
                    <span class="kv-list__col kv-list__col--key">
                      <ElInput
                        v-model="item.key"
                        placeholder="Content-Type"
                        size="small"
                      />
                    </span>
                    <span class="kv-list__col kv-list__col--value">
                      <ElInput
                        v-model="item.value"
                        placeholder="application/json"
                        size="small"
                      />
                    </span>
                    <span class="kv-list__col kv-list__col--action">
                      <ElButton
                        type="danger"
                        :icon="Trash"
                        size="small"
                        circle
                        @click="removeHeaderItem(idx)"
                      />
                    </span>
                  </div>
                  <div v-if="headerItems.length === 0" class="kv-list__empty">
                    {{ $t('data-source.noHeaders') }}
                  </div>
                </div>
              </div>

              <!-- 请求体 Panel -->
              <div
                v-else-if="apiConfigTab === 'body' && showBodyTab"
                class="api-tab-panel"
              >
                <ElForm :model="formData" label-width="100px">
                  <ElFormItem :label="$t('data-source.bodyType')">
                    <ElRadioGroup v-model="formData.api_body_type">
                      <ElRadioButton
                        v-for="opt in bodyTypeOptions"
                        :key="opt.value"
                        :value="opt.value"
                      >
                        {{ opt.label }}
                      </ElRadioButton>
                    </ElRadioGroup>
                  </ElFormItem>
                  <template
                    v-if="
                      formData.api_body_type &&
                      formData.api_body_type !== 'none'
                    "
                  >
                    <ElFormItem
                      v-if="formData.api_body_type === 'raw'"
                      :label="$t('data-source.contentType')"
                    >
                      <ElInput
                        v-model="formData.api_content_type"
                        placeholder="text/plain"
                      />
                    </ElFormItem>
                    <ElFormItem :label="$t('data-source.requestBody')">
                      <ElInput
                        v-model="apiBodyStr"
                        type="textarea"
                        :rows="5"
                        :placeholder="bodyPlaceholder"
                        class="font-mono"
                      />
                    </ElFormItem>
                  </template>
                </ElForm>
              </div>

              <!-- 高级 Panel -->
              <div
                v-else-if="apiConfigTab === 'advanced'"
                class="api-tab-panel"
              >
                <ElForm :model="formData" label-width="120px">
                  <ElRow :gutter="16">
                    <ElCol :span="12">
                      <ElFormItem :label="$t('data-source.retryCount')">
                        <ElInputNumber
                          v-model="formData.api_retry_count"
                          :min="0"
                          :max="10"
                          class="w-full"
                        />
                      </ElFormItem>
                    </ElCol>
                    <ElCol :span="12">
                      <ElFormItem :label="$t('data-source.retryInterval')">
                        <div class="flex items-center">
                          <ElInputNumber
                            v-model="formData.api_retry_interval"
                            :min="1"
                            :max="60"
                            class="w-full"
                          />
                          <span
                            class="text-muted-foreground ml-2 flex-shrink-0 text-xs"
                            >{{ $t('data-source.second') }}</span
                          >
                        </div>
                      </ElFormItem>
                    </ElCol>
                  </ElRow>
                  <ElFormItem :label="$t('data-source.proxy')">
                    <ElInput
                      v-model="formData.api_proxy"
                      placeholder="http://proxy:8080"
                    />
                  </ElFormItem>
                  <ElRow :gutter="16">
                    <ElCol :span="12">
                      <ElFormItem :label="$t('data-source.followRedirects')">
                        <ElSwitch v-model="formData.api_follow_redirects" />
                      </ElFormItem>
                    </ElCol>
                    <ElCol :span="12">
                      <ElFormItem :label="$t('data-source.verifySSL')">
                        <ElSwitch v-model="formData.api_verify_ssl" />
                      </ElFormItem>
                    </ElCol>
                  </ElRow>
                  <ElDivider>
                    {{ $t('data-source.successCondition') }}
                  </ElDivider>
                  <ElFormItem :label="$t('data-source.successStatusCodes')">
                    <ElInput
                      :model-value="
                        (ensureSuccessCondition().status_codes || []).join(', ')
                      "
                      :placeholder="
                        $t('data-source.successStatusCodesPlaceholder')
                      "
                      @update:model-value="
                        (v: string) => {
                          ensureSuccessCondition().status_codes = v
                            .split(',')
                            .map((s) => Number(s.trim()))
                            .filter((n) => !isNaN(n) && n > 0);
                        }
                      "
                    />
                  </ElFormItem>
                  <ElRow :gutter="16">
                    <ElCol :span="12">
                      <ElFormItem :label="$t('data-source.successFieldPath')">
                        <ElInput
                          v-model="ensureSuccessCondition().field_path"
                          :placeholder="
                            $t('data-source.successFieldPathPlaceholder')
                          "
                        />
                      </ElFormItem>
                    </ElCol>
                    <ElCol :span="12">
                      <ElFormItem :label="$t('data-source.successFieldValue')">
                        <ElInput
                          v-model="ensureSuccessCondition().field_value"
                          placeholder="0"
                        />
                      </ElFormItem>
                    </ElCol>
                  </ElRow>
                </ElForm>
              </div>

              <!-- 查看完整请求弹窗 -->
              <ElDialog
                v-model="showRequestPreview"
                :title="$t('data-source.viewRequest')"
                width="600px"
                append-to-body
              >
                <ElInput
                  :model-value="fullRequestPreview"
                  type="textarea"
                  :rows="18"
                  readonly
                  class="font-mono"
                />
              </ElDialog>
            </template>

            <!-- 静态数据配置 -->
            <template v-else-if="formData.source_type === 'static'">
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-medium">静态数据 (JSON 数组)</span>
                <ElButton
                  type="primary"
                  size="small"
                  :icon="Play"
                  :loading="testLoading"
                  @click="handleQuickTest"
                >
                  测试
                </ElButton>
              </div>
              <ElInput
                v-model="staticDataStr"
                type="textarea"
                :rows="12"
                class="font-mono"
              />
            </template>
          </div>

          <!-- 底部 Tabs: 结果处理 / 测试结果（与 SQL 模式一致的布局） -->
          <div
            class="border-border bg-card flex-1 overflow-hidden rounded-lg border"
          >
            <div class="flex h-full overflow-hidden">
              <!-- 左侧：竖向 Tab 切换 -->
              <div class="h-full flex-shrink-0 p-2">
                <ZqTabs
                  v-model="configActiveTab"
                  :items="configTabs"
                  vertical
                />
              </div>

              <!-- 右侧：内容区域 -->
              <div class="flex flex-1 flex-col overflow-hidden">
                <!-- 公共部分：结果类型选择（仅在结果处理和测试结果 Tab 下显示） -->
                <div
                  v-show="
                    configActiveTab === 'result' || configActiveTab === 'test'
                  "
                  class="flex-shrink-0 pt-4"
                >
                  <ElRadioGroup v-model="formData.result_type">
                    <ElRadioButton
                      v-for="opt in resultTypeOptions"
                      :key="opt.value"
                      :value="opt.value"
                    >
                      {{ opt.label }}
                    </ElRadioButton>
                  </ElRadioGroup>
                </div>

                <!-- Tab 内容 -->
                <div class="flex-1 overflow-hidden">
                  <!-- 参数定义 -->
                  <div v-show="configActiveTab === 'params'" class="h-full">
                    <ElScrollbar class="h-full">
                      <div class="p-4">
                        <div class="mb-3 flex items-center justify-between">
                          <span class="text-muted-foreground text-sm">{{
                            $t('data-source.defineDataSourceParams')
                          }}</span>
                          <ElButton
                            type="primary"
                            :icon="CirclePlus"
                            size="small"
                            @click="addParam"
                          >
                            {{ $t('data-source.addParam') }}
                          </ElButton>
                        </div>
                        <ElTable
                          :data="formData.params || []"
                          border
                          stripe
                          max-height="180"
                        >
                          <ElTableColumn
                            :label="$t('data-source.paramName')"
                            width="140"
                          >
                            <template #default="{ row }">
                              <ElInput
                                v-model="row.name"
                                placeholder="name"
                                size="small"
                              />
                            </template>
                          </ElTableColumn>
                          <ElTableColumn
                            :label="$t('data-source.paramLabel')"
                            width="140"
                          >
                            <template #default="{ row }">
                              <ElInput
                                v-model="row.label"
                                placeholder="名称"
                                size="small"
                              />
                            </template>
                          </ElTableColumn>
                          <ElTableColumn
                            :label="$t('data-source.paramType')"
                            width="110"
                          >
                            <template #default="{ row }">
                              <ElSelect
                                v-model="row.type"
                                size="small"
                                class="w-full"
                              >
                                <ElOption
                                  v-for="opt in paramTypeOptions"
                                  :key="opt.value"
                                  :label="opt.label"
                                  :value="opt.value"
                                />
                              </ElSelect>
                            </template>
                          </ElTableColumn>
                          <ElTableColumn
                            :label="$t('data-source.paramValue')"
                            width="120"
                          >
                            <template #default="{ row }">
                              <ElInput
                                v-model="row.default"
                                placeholder="默认值"
                                size="small"
                              />
                            </template>
                          </ElTableColumn>
                          <ElTableColumn
                            :label="$t('data-source.required')"
                            width="70"
                            align="center"
                          >
                            <template #default="{ row }">
                              <ElSwitch v-model="row.required" size="small" />
                            </template>
                          </ElTableColumn>
                          <ElTableColumn
                            :label="$t('data-source.action')"
                            align="center"
                          >
                            <template #default="{ $index }">
                              <ElButton
                                type="danger"
                                :icon="Trash"
                                size="small"
                                circle
                                @click="removeParam($index)"
                              />
                            </template>
                          </ElTableColumn>
                        </ElTable>
                      </div>
                    </ElScrollbar>
                  </div>

                  <!-- 结果处理 -->
                  <div v-show="configActiveTab === 'result'" class="h-full">
                    <ElScrollbar class="h-full">
                      <div class="p-4">
                        <ElForm :model="formData" label-width="100px">
                          <!-- 树形配置 -->
                          <template v-if="formData.result_type === 'tree'">
                            <ElDivider content-position="left">
                              {{ $t('data-source.treeConversionConfig') }}
                            </ElDivider>
                            <ElRow :gutter="16">
                              <ElCol :span="8">
                                <ElFormItem label="ID字段">
                                  <ElInput
                                    v-model="formData.tree_config!.id_field"
                                    placeholder="id"
                                  />
                                </ElFormItem>
                              </ElCol>
                              <ElCol :span="8">
                                <ElFormItem label="父级字段">
                                  <ElInput
                                    v-model="formData.tree_config!.parent_field"
                                    placeholder="parent_id"
                                  />
                                </ElFormItem>
                              </ElCol>
                              <ElCol :span="8">
                                <ElFormItem label="子节点字段">
                                  <ElInput
                                    v-model="
                                      formData.tree_config!.children_field
                                    "
                                    placeholder="children"
                                  />
                                </ElFormItem>
                              </ElCol>
                            </ElRow>
                          </template>
                          <!-- 轴向图表配置 -->
                          <template
                            v-if="formData.result_type === 'chart-axis'"
                          >
                            <ElDivider content-position="left">
                              {{ $t('data-source.axisChartConfig') }}
                              <ElTooltip content="适用于折线图、柱状图、面积图">
                                <span
                                  class="text-muted-foreground ml-1 cursor-help"
                                  >(?)</span>
                              </ElTooltip>
                            </ElDivider>
                            <ElFormItem :label="$t('data-source.xAxisField')">
                              <ElInput
                                v-model="formData.chart_config!.x_field"
                                placeholder="如：month"
                              />
                            </ElFormItem>
                            <ElFormItem :label="$t('data-source.seriesField')">
                              <ElInput
                                v-model="chartSeriesFieldsStr"
                                :placeholder="
                                  $t('data-source.multipleFieldsComma', {
                                    example: 'sales,profit',
                                  })
                                "
                              />
                              <div class="text-muted-foreground mt-1 text-xs">
                                {{ $t('data-source.dataFieldsForChart') }}
                              </div>
                            </ElFormItem>
                            <ElFormItem :label="$t('data-source.seriesName')">
                              <ElInput
                                v-model="chartSeriesNamesStr"
                                :placeholder="
                                  $t('data-source.multipleNamesComma', {
                                    example: '销售额,利润',
                                  })
                                "
                              />
                              <div class="text-muted-foreground mt-1 text-xs">
                                {{ $t('data-source.optionalLegendNames') }}
                              </div>
                            </ElFormItem>
                          </template>
                          <!-- 饼图配置 -->
                          <template v-if="formData.result_type === 'chart-pie'">
                            <ElDivider content-position="left">
                              {{ $t('data-source.pieChartConfig') }}
                              <ElTooltip content="适用于饼图、漏斗图">
                                <span
                                  class="text-muted-foreground ml-1 cursor-help"
                                  >(?)</span>
                              </ElTooltip>
                            </ElDivider>
                            <ElRow :gutter="16">
                              <ElCol :span="12">
                                <ElFormItem
                                  :label="$t('data-source.nameField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.name_field"
                                    placeholder="如：category"
                                  />
                                </ElFormItem>
                              </ElCol>
                              <ElCol :span="12">
                                <ElFormItem
                                  :label="$t('data-source.valueField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.value_field"
                                    placeholder="如：amount"
                                  />
                                </ElFormItem>
                              </ElCol>
                            </ElRow>
                          </template>
                          <!-- 仪表盘配置 -->
                          <template
                            v-if="formData.result_type === 'chart-gauge'"
                          >
                            <ElDivider content-position="left">
                              {{ $t('data-source.gaugeChartConfig') }}
                              <ElTooltip content="适用于仪表盘、进度图">
                                <span
                                  class="text-muted-foreground ml-1 cursor-help"
                                  >(?)</span>
                              </ElTooltip>
                            </ElDivider>
                            <ElRow :gutter="16">
                              <ElCol :span="8">
                                <ElFormItem
                                  :label="$t('data-source.valueField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.value_field"
                                    placeholder="如：value"
                                  />
                                </ElFormItem>
                              </ElCol>
                              <ElCol :span="8">
                                <ElFormItem
                                  :label="$t('data-source.nameField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.name_field"
                                    :placeholder="
                                      $t('data-source.optionalName')
                                    "
                                  />
                                </ElFormItem>
                              </ElCol>
                              <ElCol :span="8">
                                <ElFormItem :label="$t('data-source.maxField')">
                                  <ElInput
                                    v-model="formData.chart_config!.max_field"
                                    :placeholder="$t('data-source.optionalMax')"
                                  />
                                </ElFormItem>
                              </ElCol>
                            </ElRow>
                          </template>
                          <!-- 雷达图配置 -->
                          <template
                            v-if="formData.result_type === 'chart-radar'"
                          >
                            <ElDivider content-position="left">
                              {{ $t('data-source.radarChartConfig') }}
                            </ElDivider>
                            <ElRow :gutter="16">
                              <ElCol :span="12">
                                <ElFormItem
                                  :label="$t('data-source.indicatorNameField')"
                                >
                                  <ElInput
                                    v-model="
                                      formData.chart_config!.indicator_field
                                    "
                                    placeholder="如：name"
                                  />
                                </ElFormItem>
                              </ElCol>
                              <ElCol :span="12">
                                <ElFormItem :label="$t('data-source.maxField')">
                                  <ElInput
                                    v-model="formData.chart_config!.max_field"
                                    placeholder="如：max"
                                  />
                                </ElFormItem>
                              </ElCol>
                            </ElRow>
                            <ElFormItem :label="$t('data-source.valueField')">
                              <ElInput
                                v-model="chartValueFieldsStr"
                                :placeholder="
                                  $t('data-source.multipleFieldsComma', {
                                    example: 'budget,actual',
                                  })
                                "
                              />
                              <div class="text-muted-foreground mt-1 text-xs">
                                {{ $t('data-source.oneFieldPerSeries') }}
                              </div>
                            </ElFormItem>
                            <ElFormItem :label="$t('data-source.seriesName')">
                              <ElInput
                                v-model="chartSeriesNamesStr"
                                :placeholder="
                                  $t('data-source.multipleNamesComma', {
                                    example: '预算,实际',
                                  })
                                "
                              />
                            </ElFormItem>
                          </template>
                          <!-- 散点图配置 -->
                          <template
                            v-if="formData.result_type === 'chart-scatter'"
                          >
                            <ElDivider content-position="left">
                              {{ $t('data-source.scatterChartConfig') }}
                              <ElTooltip content="适用于散点图、气泡图">
                                <span
                                  class="text-muted-foreground ml-1 cursor-help"
                                  >(?)</span>
                              </ElTooltip>
                            </ElDivider>
                            <ElRow :gutter="16">
                              <ElCol :span="12">
                                <ElFormItem
                                  :label="$t('data-source.xCoordinateField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.x_field"
                                    placeholder="如：x"
                                  />
                                </ElFormItem>
                              </ElCol>
                              <ElCol :span="12">
                                <ElFormItem
                                  :label="$t('data-source.yCoordinateField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.y_field"
                                    placeholder="如：y"
                                  />
                                </ElFormItem>
                              </ElCol>
                            </ElRow>
                            <ElRow :gutter="16">
                              <ElCol :span="12">
                                <ElFormItem
                                  :label="$t('data-source.sizeField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.size_field"
                                    :placeholder="
                                      $t('data-source.optionalBubbleChart')
                                    "
                                  />
                                </ElFormItem>
                              </ElCol>
                              <ElCol :span="12">
                                <ElFormItem
                                  :label="$t('data-source.nameField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.name_field"
                                    :placeholder="
                                      $t('data-source.optionalName')
                                    "
                                  />
                                </ElFormItem>
                              </ElCol>
                            </ElRow>
                          </template>
                          <!-- 热力图配置 -->
                          <template
                            v-if="formData.result_type === 'chart-heatmap'"
                          >
                            <ElDivider content-position="left">
                              {{ $t('data-source.heatmapChartConfig') }}
                            </ElDivider>
                            <ElRow :gutter="16">
                              <ElCol :span="8">
                                <ElFormItem
                                  :label="$t('data-source.xCoordinateField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.x_field"
                                    placeholder="如：x"
                                  />
                                </ElFormItem>
                              </ElCol>
                              <ElCol :span="8">
                                <ElFormItem
                                  :label="$t('data-source.yCoordinateField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.y_field"
                                    placeholder="如：y"
                                  />
                                </ElFormItem>
                              </ElCol>
                              <ElCol :span="8">
                                <ElFormItem
                                  :label="$t('data-source.valueField')"
                                >
                                  <ElInput
                                    v-model="formData.chart_config!.value_field"
                                    placeholder="如：value"
                                  />
                                </ElFormItem>
                              </ElCol>
                            </ElRow>
                          </template>

                          <!-- 字段映射 -->
                          <ElDivider content-position="left">
                            字段映射
                            <ElTooltip
                              content="将原字段名映射为新字段名，如 id -> value"
                            >
                              <span
                                class="text-muted-foreground ml-1 cursor-help"
                                >(?)</span>
                            </ElTooltip>
                          </ElDivider>
                          <div class="mb-2">
                            <ElButton
                              type="primary"
                              :icon="CirclePlus"
                              size="small"
                              @click="addFieldMapping"
                            >
                              添加映射
                            </ElButton>
                          </div>
                          <div
                            v-for="(_, key) in formData.field_mapping"
                            :key="key"
                            class="mb-2 flex items-center gap-2"
                          >
                            <ElInput
                              :model-value="key"
                              placeholder="原字段"
                              class="w-40"
                              @change="
                                (v: string) =>
                                  updateFieldMappingKey(key as string, v)
                              "
                            />
                            <span class="text-muted-foreground">-></span>
                            <ElInput
                              v-model="formData.field_mapping![key as string]"
                              placeholder="新字段"
                              class="w-40"
                            />
                            <ElButton
                              type="danger"
                              :icon="Trash"
                              size="small"
                              circle
                              @click="removeFieldMapping(key as string)"
                            />
                          </div>

                          <!-- 缓存配置 -->
                          <ElDivider content-position="left">
                            缓存配置
                          </ElDivider>
                          <ElRow :gutter="16">
                            <ElCol :span="8">
                              <ElFormItem label="启用缓存">
                                <ElSwitch v-model="formData.cache_enabled" />
                              </ElFormItem>
                            </ElCol>
                            <ElCol :span="16">
                              <ElFormItem
                                v-if="formData.cache_enabled"
                                label="缓存时间"
                              >
                                <ElInputNumber
                                  v-model="formData.cache_ttl"
                                  :min="0"
                                  :max="86400"
                                />
                                <span class="text-muted-foreground ml-2 text-xs"
                                  >秒（0表示不缓存）</span
                                >
                              </ElFormItem>
                            </ElCol>
                          </ElRow>
                        </ElForm>
                      </div>
                    </ElScrollbar>
                  </div>

                  <!-- 测试结果 -->
                  <div v-show="configActiveTab === 'test'" class="h-full">
                    <div class="flex h-full flex-col">
                      <!-- 顶部：测试参数和按钮 -->
                      <div class="flex-shrink-0 p-4 pb-2">
                        <!-- 测试参数 -->
                        <ElCard
                          v-if="formData.params && formData.params.length > 0"
                          shadow="never"
                          class="mb-3"
                        >
                          <template #header>
                            <span class="text-sm font-medium">{{
                              $t('data-source.testParams')
                            }}</span>
                          </template>
                          <ElForm label-width="100px">
                            <ElRow :gutter="16">
                              <ElCol
                                v-for="param in formData.params"
                                :key="param.name"
                                :span="12"
                              >
                                <ElFormItem :label="param.label || param.name">
                                  <ElInput
                                    v-model="testParams[param.name]"
                                    :placeholder="
                                      param.default !== null
                                        ? String(param.default)
                                        : ''
                                    "
                                  />
                                </ElFormItem>
                              </ElCol>
                            </ElRow>
                          </ElForm>
                        </ElCard>
                      </div>

                      <!-- 底部：测试结果（左右分栏） -->
                      <div class="min-h-0 flex-1">
                        <!-- 加载状态 -->
                        <div
                          v-show="testLoading"
                          class="flex h-full items-center justify-center"
                        >
                          <div class="flex flex-col items-center">
                            <ElIcon class="is-loading mb-2" :size="32">
                              <Loading />
                            </ElIcon>
                            <span class="text-muted-foreground text-sm">{{
                              $t('data-source.querying')
                            }}</span>
                          </div>
                        </div>

                        <!-- 测试结果 -->
                        <div
                          v-show="!testLoading && testResult"
                          class="bg-background flex h-full flex-col rounded-[8px]"
                        >
                          <!-- Header -->
                          <div
                            class="border-border m-3 flex items-center gap-2"
                          >
                            <span class="text-sm font-medium">{{
                              $t('data-source.testResult')
                            }}</span>
                            <ElTag
                              :type="testResult?.success ? 'success' : 'danger'"
                              size="small"
                            >
                              {{
                                testResult?.success
                                  ? $t('data-source.success')
                                  : $t('data-source.failed')
                              }}
                            </ElTag>
                            <span class="text-muted-foreground text-xs">
                              {{
                                $t('data-source.returnedData', {
                                  count: testResult?.total || 0,
                                })
                              }}
                            </span>
                            <ElTag
                              v-if="
                                testResult?.total &&
                                testResult?.limited &&
                                testResult.total >= testResult.limited
                              "
                              type="warning"
                              size="small"
                            >
                              {{
                                $t('data-source.reachedLimit', {
                                  limit: testResult?.limited,
                                })
                              }}
                            </ElTag>
                          </div>

                          <!-- 左右分栏：图表/表格 + 数据 -->
                          <ElSplitter class="flex-1">
                            <!-- 左侧：图表或表格 -->
                            <ElSplitterPanel :size="50">
                              <div class="h-full p-2">
                                <!-- 图表类型：显示 ECharts -->
                                <EchartsUI
                                  v-show="isChartResultType"
                                  ref="apiPreviewChartRef"
                                  class="h-full w-full"
                                />

                                <!-- 非图表类型：显示表格 -->
                                <ElScrollbar
                                  v-show="
                                    !isChartResultType &&
                                    testResult?.data !== undefined
                                  "
                                  class="h-full"
                                >
                                  <!-- 列表类型：数组数据 -->
                                  <ElTable
                                    v-if="
                                      Array.isArray(testResult?.data) &&
                                      testResult.data.length > 0
                                    "
                                    :data="testResult.data"
                                    border
                                    stripe
                                    size="small"
                                    max-height="100%"
                                  >
                                    <ElTableColumn
                                      v-for="col in Object.keys(
                                        testResult.data[0] || {},
                                      )"
                                      :key="col"
                                      :prop="col"
                                      :label="col"
                                      min-width="100"
                                    />
                                  </ElTable>

                                  <!-- 单值/对象类型 -->
                                  <div
                                    v-else-if="
                                      testResult?.data !== undefined &&
                                      !Array.isArray(testResult.data)
                                    "
                                    class="p-2"
                                  >
                                    <pre class="bg-muted rounded p-3 text-xs">{{
                                      JSON.stringify(testResult.data, null, 2)
                                    }}</pre>
                                  </div>
                                </ElScrollbar>
                              </div>
                            </ElSplitterPanel>

                            <!-- 右侧：原始数据 -->
                            <ElSplitterPanel :size="50">
                              <div class="h-full p-2">
                                <div
                                  class="text-muted-foreground mb-2 text-xs font-medium"
                                >
                                  {{ $t('data-source.rawData') }}
                                </div>
                                <ElScrollbar class="h-[calc(100%-24px)]">
                                  <pre class="bg-muted rounded p-3 text-xs">{{
                                    JSON.stringify(testResult?.data, null, 2)
                                  }}</pre>
                                </ElScrollbar>
                              </div>
                            </ElSplitterPanel>
                          </ElSplitter>
                        </div>

                        <!-- 无结果时的提示 -->
                        <div
                          v-show="!testLoading && !testResult"
                          class="flex h-full items-center justify-center"
                        >
                          <div class="text-center">
                            <Play
                              class="text-muted-foreground mx-auto mb-2 h-12 w-12"
                            />
                            <p class="text-muted-foreground text-sm">
                              {{ $t('data-source.clickTestToExecute') }}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </ElDialog>
</template>

<style scoped>
:deep(.el-tabs__header) {
  padding: 0 16px;
  margin-bottom: 0;
  border-bottom: 1px solid var(--el-border-color);
}

:deep(.el-tabs__content) {
  height: calc(100% - 40px);
  overflow: hidden;
}

:deep(.el-tab-pane) {
  height: 100%;
  overflow: hidden;
}

:deep(.el-textarea__inner) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

/* SQL 配置区域的 Tabs 样式 */
:deep(.sql-config-tabs .el-tabs__header) {
  padding: 0 12px;
  background-color: var(--el-fill-color-lighter);
}

:deep(.sql-config-tabs .el-tabs__content) {
  height: calc(100% - 40px);
}

/* API Tab Panel */
.api-tab-panel {
  padding: 8px 0;
}

/* KV List 样式 */
.kv-list {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  overflow: hidden;
}

.kv-list__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  background-color: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.kv-list__row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  transition: background-color 0.15s;
}

.kv-list__row:not(:last-child) {
  border-bottom: 1px solid var(--el-border-color-extra-light);
}

.kv-list__row:hover {
  background-color: var(--el-fill-color-lighter);
}

.kv-list__row--disabled {
  opacity: 0.5;
}

.kv-list__col {
  display: flex;
  align-items: center;
}

.kv-list__col--switch {
  flex: 0 0 40px;
  justify-content: center;
}

.kv-list__col--key {
  flex: 1;
  min-width: 0;
}

.kv-list__col--value {
  flex: 1.2;
  min-width: 0;
}

.kv-list__col--desc {
  flex: 1;
  min-width: 0;
}

.kv-list__col--action {
  flex: 0 0 36px;
  justify-content: center;
}

.kv-list__empty {
  padding: 24px 0;
  text-align: center;
  font-size: 13px;
  color: var(--el-text-color-placeholder);
}

/* 隐藏分隔线 - 将分隔线设置为透明 */
:deep(.el-splitter-bar__dragger)::before,
:deep(.el-splitter-bar__dragger)::after {
  background-color: transparent !important;
}

/* 隐藏折叠图标 */
:deep(.el-splitter-bar__collapse-icon) {
  background: transparent !important;
  opacity: 0 !important;
}
</style>
