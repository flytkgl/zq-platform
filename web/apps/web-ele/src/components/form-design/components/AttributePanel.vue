<script setup lang="ts">
import type { DataSourceType, DataSourceParamConfig, FormDataFilter, OcrSchemaField } from '../store/formDesignStore';

import type { DataSource, DataSourceSimple, ParamDefinition } from '#/api/core/data-source';
import type { Dict } from '#/api/core/dict';

import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';
import { CircleHelp } from '@vben/icons';
import {
  ArrowDown,
  ArrowRight,
  Close,
  Delete,
  Edit,
  Rank,
} from '@element-plus/icons-vue';
import {
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElColorPicker,
  ElDatePicker,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElRadioButton,
  ElRadioGroup,
  ElRate,
  ElScrollbar,
  ElSelect,
  ElSlider,
  ElSwitch,
  ElTag,
  ElTimePicker,
  ElTooltip,
} from 'element-plus';
import { storeToRefs } from 'pinia';
import draggable from 'vuedraggable';

import { getAllDataSourceApi, getDataSourceByCodeApi } from '#/api/core/data-source';
import { getAllDictApi } from '#/api/core/dict';
import { getPublishedFormsSimpleApi, type PublishedFormSimple } from '#/api/online-dev/form-manager';
import { useAppContextStore } from '#/store/app-context';

import { useFormDesignStore } from '../store/formDesignStore';
import ZqTabs from '../../zq-tabs/index.vue';
import ConditionBuilder from './ConditionBuilder.vue';
import OptionsEditor from './OptionsEditor.vue';
// import SchemaConfigDialog from '#/views/ai-platform/workflow/editor/components/SchemaConfigDialog.vue';

// 数据来源类型选项
const DATA_SOURCE_OPTIONS: { label: string; value: DataSourceType }[] = [
  { label: $t('form-design.attribute.staticData'), value: 'static' },
  { label: $t('form-design.attribute.dictData'), value: 'dict' },
  { label: $t('form-design.attribute.dataSource'), value: 'dataSource' },
  { label: $t('form-design.attribute.formData'), value: 'formData' },
];

// 字典列表
const dictList = ref<Dict[]>([]);
const loadingDict = ref(false);

// 数据源列表
const dataSourceList = ref<DataSourceSimple[]>([]);
const loadingDataSource = ref(false);

// 已发布表单列表
const publishedFormList = ref<PublishedFormSimple[]>([]);
const loadingPublishedForms = ref(false);

// 加载字典列表
async function loadDictList() {
  if (dictList.value.length > 0) return; // 已加载过
  try {
    loadingDict.value = true;
    const appContextStore = useAppContextStore();
    const data = await getAllDictApi(appContextStore.currentApp?.id);
    dictList.value = data || [];
  } catch (error) {
    console.error($t('common.loadError'), error);
  } finally {
    loadingDict.value = false;
  }
}

// 加载数据源列表
async function loadDataSourceList() {
  if (dataSourceList.value.length > 0) return; // 已加载过
  try {
    loadingDataSource.value = true;
    const appContextStore = useAppContextStore();
    const data = await getAllDataSourceApi(appContextStore.currentApp?.id);
    dataSourceList.value = data || [];
  } catch (error) {
    console.error($t('common.loadError'), error);
  } finally {
    loadingDataSource.value = false;
  }
}

// 当前选中数据源的详情（包含参数定义）
const currentDataSourceDetail = ref<DataSource | null>(null);
const loadingDataSourceDetail = ref(false);

// 加载数据源详情（获取参数定义）
async function loadDataSourceDetail(code: string) {
  if (!code) {
    currentDataSourceDetail.value = null;
    return;
  }
  try {
    loadingDataSourceDetail.value = true;
    const data = await getDataSourceByCodeApi(code);
    currentDataSourceDetail.value = data;
    // 自动初始化参数配置
    initDataSourceParams(data.params || []);
  } catch (error) {
    console.error($t('common.loadError'), error);
    currentDataSourceDetail.value = null;
  } finally {
    loadingDataSourceDetail.value = false;
  }
}

// 初始化数据源参数配置
function initDataSourceParams(paramDefs: ParamDefinition[]) {
  if (!activeItem.value?.dataSource) return;

  const existingParams = activeItem.value.dataSource.dataSourceParams || [];
  const newParams: DataSourceParamConfig[] = [];

  for (const paramDef of paramDefs) {
    // 查找已有配置
    const existing = existingParams.find(p => p.name === paramDef.name);
    if (existing) {
      // 更新数据源定义中的元数据（label, type, required, default），但保留用户配置（valueSource, fixedValue, sourceField）
      newParams.push({
        ...existing,
        label: paramDef.label || paramDef.name,
        type: paramDef.type || 'string',
        required: paramDef.required || false,
        default: paramDef.default, // 始终从数据源定义获取最新默认值
      });
    } else {
      // 创建新配置，默认使用固定值
      newParams.push({
        name: paramDef.name,
        label: paramDef.label || paramDef.name,
        type: paramDef.type || 'string',
        required: paramDef.required || false,
        default: paramDef.default,
        valueSource: 'fixed',
        fixedValue: undefined, // 不自动填充默认值，让用户手动设置
      });
    }
  }

  activeItem.value.dataSource.dataSourceParams = newParams;
}

// 参数值来源选项
const PARAM_VALUE_SOURCE_OPTIONS = [
  { label: $t('form-design.attribute.paramSource.fixed'), value: 'fixed' },
  { label: $t('form-design.attribute.paramSource.field'), value: 'field' },
  { label: $t('form-design.attribute.paramSource.search'), value: 'search' },
];

// 获取当前表单所有字段（用于参数来源选择）
const allFormFields = computed(() => {
  const store = useFormDesignStore();
  const fields: { field: string; label: string }[] = [];

  function collectFields(items: any[]) {
    for (const item of items) {
      if (item.field && item.label) {
        fields.push({ field: item.field, label: item.label });
      }
      if (item.children) {
        collectFields(item.children);
      }
      if (item.columns) {
        for (const col of item.columns) {
          if (col.children) {
            collectFields(col.children);
          }
        }
      }
    }
  }

  // 使用 formConf.items 而不是 formItems
  if (store.formConf?.items && Array.isArray(store.formConf.items)) {
    collectFields(store.formConf.items);
  }
  return fields;
});

// 加载已发布表单列表
async function loadPublishedFormList(forceReload = false) {
  if (!forceReload && publishedFormList.value.length > 0) return; // 已加载过
  try {
    loadingPublishedForms.value = true;
    const appContextStore = useAppContextStore();
    const data = await getPublishedFormsSimpleApi(appContextStore.currentApp?.id);
    publishedFormList.value = data || [];
  } catch (error) {
    console.error($t('common.loadError'), error);
  } finally {
    loadingPublishedForms.value = false;
  }
}

// === 默认值动态选项（根据数据源类型加载） ===
const defaultValueDynamicOptions = ref<{ label: string; value: any }[]>([]);
const loadingDefaultValueOptions = ref(false);

async function loadDefaultValueDictOptions(dictCode: string) {
  try {
    loadingDefaultValueOptions.value = true;
    const data = await getDictItemByCodeApi(dictCode);
    defaultValueDynamicOptions.value = (data || []).map((item: any) => ({
      label: item.label,
      value: item.value,
    }));
  } catch {
    defaultValueDynamicOptions.value = [];
  } finally {
    loadingDefaultValueOptions.value = false;
  }
}

async function loadDefaultValueDataSourceOptions(config: any) {
  if (!config.dataSourceCode) return;
  try {
    loadingDefaultValueOptions.value = true;
    const response = await executeDataSourceGetApi(config.dataSourceCode);
    const data = Array.isArray(response) ? response : response?.list || response?.data || [];
    const labelField = config.labelField || 'label';
    const valueField = config.valueField || 'value';
    if (Array.isArray(data) && data.length > 0 && data[0]?.label !== undefined && data[0]?.value !== undefined) {
      defaultValueDynamicOptions.value = data;
    } else {
      defaultValueDynamicOptions.value = data.map((item: any) => ({
        label: item[labelField] ?? '',
        value: item[valueField] ?? '',
      }));
    }
  } catch {
    defaultValueDynamicOptions.value = [];
  } finally {
    loadingDefaultValueOptions.value = false;
  }
}

async function loadDefaultValueFormDataOptions(config: any) {
  if (!config.formCode || !config.formLabelField || !config.formValueField) return;
  try {
    loadingDefaultValueOptions.value = true;
    const params: Record<string, any> = { page: 1, pageSize: config.formPageSize || 100 };
    const response = await requestClient.get(
      `/api/online_dev/form-data/${config.formCode}/list`,
      { params },
    );
    const items = response?.items || [];
    defaultValueDynamicOptions.value = items
      .map((item: any) => ({
        label: item[config.formLabelField] ?? '',
        value: item[config.formValueField] ?? '',
      }))
      .filter((opt: any) => opt.value !== '' && opt.value !== null && opt.value !== undefined);
  } catch {
    defaultValueDynamicOptions.value = [];
  } finally {
    loadingDefaultValueOptions.value = false;
  }
}

// 获取选中表单的字段列表
const selectedFormFields = computed(() => {
  // 支持 table-selector 的 dataSource.formCode 和 form-selector 的 formSelectorConfig.formCode
  const formCode = activeItem.value?.dataSource?.formCode || activeItem.value?.formSelectorConfig?.formCode;
  if (!formCode) return [];
  const form = publishedFormList.value.find(
    (f) => f.code === formCode,
  );
  return form?.fields || [];
});

// 表格选择器可用字段列表（根据数据源类型）
const tableSelectorAvailableFields = computed(() => {
  if (activeItem.value?.type !== 'table-selector') return [];
  const dataSource = activeItem.value?.dataSource;
  if (!dataSource) return [];

  // 表单数据模式：使用 selectedFormFields
  if (dataSource.type === 'formData' && dataSource.formCode) {
    return selectedFormFields.value;
  }

  // 字典模式：固定字段
  if (dataSource.type === 'dict') {
    return [
      { field: 'label', label: '标签' },
      { field: 'value', label: '值' },
      { field: 'sort', label: '排序' },
    ];
  }

  // 数据源模式：使用配置的字段映射
  if (dataSource.type === 'dataSource') {
    return [
      { field: dataSource.labelField || 'label', label: '标签' },
      { field: dataSource.valueField || 'value', label: '值' },
    ];
  }

  return [];
});

// 表单选择器可用字段列表
const formSelectorAvailableFields = computed(() => {
  if (activeItem.value?.type !== 'form-selector') return [];
  const config = activeItem.value?.formSelectorConfig;
  if (!config?.formCode) return [];
  // 直接从 publishedFormList 中查找，确保响应式更新
  const form = publishedFormList.value.find(f => f.code === config.formCode);
  return form?.fields || [];
});

// 列配置字段变更时自动填充标题
function handleColumnFieldChange(col: any, field: string) {
  col.field = field;
  // 自动填充标题
  const fieldInfo = tableSelectorAvailableFields.value.find((f: any) => f.field === field);
  if (fieldInfo && !col.label) {
    col.label = fieldInfo.label;
  }
}

// 结果类型标签映射
const resultTypeLabelMap: Record<string, string> = {
  list: $t('form-design.attribute.resultType.list'),
  tree: $t('form-design.attribute.resultType.tree'),
  object: $t('form-design.attribute.resultType.object'),
  value: $t('form-design.attribute.resultType.value'),
  'chart-axis': $t('form-design.attribute.resultType.chartAxis'),
  'chart-pie': $t('form-design.attribute.resultType.chartPie'),
  'chart-gauge': $t('form-design.attribute.resultType.chartGauge'),
  'chart-radar': $t('form-design.attribute.resultType.chartRadar'),
  'chart-scatter': $t('form-design.attribute.resultType.chartScatter'),
  'chart-heatmap': $t('form-design.attribute.resultType.chartHeatmap'),
};

// 获取结果类型标签
function getResultTypeLabel(resultType: string): string {
  return resultTypeLabelMap[resultType] || resultType;
}

// AI OCR Schema配置Dialog显示状态
const schemaDialogVisible = ref(false);

// AI OCR 预设模板配置
const OCR_TEMPLATES: Record<string, { name: string; schema: OcrSchemaField[] }> = {
  custom: {
    name: $t('form-design.aiImageOcr.customTemplate'),
    schema: [],
  },
  id_card: {
    name: $t('form-design.aiImageOcr.idCard'),
    schema: [
      { name: 'name', type: 'string', description: '姓名', required: true },
      { name: 'gender', type: 'string', description: '性别', required: false },
      { name: 'nation', type: 'string', description: '民族', required: false },
      { name: 'birth_date', type: 'string', description: '出生日期', required: false },
      { name: 'address', type: 'string', description: '住址', required: false },
      { name: 'id_number', type: 'string', description: '身份证号码', required: true },
    ],
  },
  business_license: {
    name: $t('form-design.aiImageOcr.businessLicense'),
    schema: [
      { name: 'company_name', type: 'string', description: '企业名称', required: true },
      { name: 'unified_social_credit_code', type: 'string', description: '统一社会信用代码', required: true },
      { name: 'legal_representative', type: 'string', description: '法定代表人', required: false },
      { name: 'registered_capital', type: 'string', description: '注册资本', required: false },
      { name: 'establishment_date', type: 'string', description: '成立日期', required: false },
      { name: 'business_scope', type: 'string', description: '经营范围', required: false },
      { name: 'address', type: 'string', description: '住所', required: false },
    ],
  },
  invoice: {
    name: $t('form-design.aiImageOcr.invoice'),
    schema: [
      { name: 'invoice_code', type: 'string', description: '发票代码', required: false },
      { name: 'invoice_number', type: 'string', description: '发票号码', required: true },
      { name: 'invoice_date', type: 'string', description: '开票日期', required: true },
      { name: 'buyer_name', type: 'string', description: '购买方名称', required: false },
      { name: 'seller_name', type: 'string', description: '销售方名称', required: false },
      { name: 'total_amount', type: 'number', description: '合计金额', required: true },
      { name: 'tax_amount', type: 'number', description: '税额', required: false },
      { name: 'total_with_tax', type: 'number', description: '价税合计', required: false },
    ],
  },
  receipt: {
    name: $t('form-design.aiImageOcr.receipt'),
    schema: [
      { name: 'merchant_name', type: 'string', description: '商户名称', required: false },
      { name: 'transaction_date', type: 'string', description: '交易日期', required: true },
      { name: 'total_amount', type: 'number', description: '总金额', required: true },
      { name: 'payment_method', type: 'string', description: '支付方式', required: false },
      { name: 'items', type: 'array', description: '商品明细', required: false, items: { name: 'item', type: 'object', description: '', required: false, properties: [
        { name: 'name', type: 'string', description: '商品名称', required: true },
        { name: 'quantity', type: 'number', description: '数量', required: false },
        { name: 'price', type: 'number', description: '单价', required: false },
      ]}},
    ],
  },
  contract: {
    name: $t('form-design.aiImageOcr.contract'),
    schema: [
      { name: 'contract_title', type: 'string', description: '合同标题', required: true },
      { name: 'contract_number', type: 'string', description: '合同编号', required: false },
      { name: 'party_a', type: 'string', description: '甲方', required: true },
      { name: 'party_b', type: 'string', description: '乙方', required: true },
      { name: 'sign_date', type: 'string', description: '签订日期', required: false },
      { name: 'effective_date', type: 'string', description: '生效日期', required: false },
      { name: 'contract_amount', type: 'number', description: '合同金额', required: false },
    ],
  },
};

// 打开Schema配置Dialog
function openSchemaDialog() {
  schemaDialogVisible.value = true;
}

// Schema配置确认
function handleSchemaConfirm(schema: OcrSchemaField[]) {
  if (!activeItem.value?.aiOcrConfig) return;
  activeItem.value.aiOcrConfig.outputSchema = schema;
}

// 处理模板类型变更
function handleTemplateChange(templateType: string) {
  if (!activeItem.value?.aiOcrConfig) return;
  const template = OCR_TEMPLATES[templateType];
  if (template && templateType !== 'custom') {
    // 深拷贝模板schema
    activeItem.value.aiOcrConfig.outputSchema = JSON.parse(JSON.stringify(template.schema));
  }
}

// 计算当前Schema的字段列表（用于字段映射下拉框）
const ocrSchemaFields = computed(() => {
  if (!activeItem.value?.aiOcrConfig?.outputSchema) return [];
  const fields: { label: string; value: string }[] = [];

  const extractFields = (schema: OcrSchemaField[], prefix = '') => {
    for (const field of schema) {
      if (!field.name) continue;
      const fullName = prefix ? `${prefix}.${field.name}` : field.name;
      fields.push({
        label: field.description ? `${field.name} (${field.description})` : field.name,
        value: fullName,
      });
      // 递归处理嵌套对象
      if (field.type === 'object' && field.properties) {
        extractFields(field.properties, fullName);
      }
    }
  };

  extractFields(activeItem.value.aiOcrConfig.outputSchema);
  return fields;
});

// 计算Schema预览JSON
const schemaPreviewJson = computed(() => {
  if (!activeItem.value?.aiOcrConfig?.outputSchema?.length) return '';

  const buildSchema = (fields: OcrSchemaField[]): any => {
    const properties: Record<string, any> = {};
    const required: string[] = [];

    for (const field of fields) {
      if (!field.name) continue;

      const prop: any = {
        type: field.type,
        description: field.description || undefined,
      };

      if (field.type === 'object' && field.properties) {
        const nested = buildSchema(field.properties);
        prop.properties = nested.properties;
        if (nested.required?.length > 0) {
          prop.required = nested.required;
        }
      } else if (field.type === 'array' && field.items) {
        if (field.items.type === 'object' && field.items.properties) {
          const nested = buildSchema(field.items.properties);
          prop.items = {
            type: 'object',
            properties: nested.properties,
          };
          if (nested.required?.length > 0) {
            prop.items.required = nested.required;
          }
        } else {
          prop.items = { type: field.items.type };
        }
      }

      properties[field.name] = prop;
      if (field.required) {
        required.push(field.name);
      }
    }

    return { properties, required };
  };

  return JSON.stringify(buildSchema(activeItem.value.aiOcrConfig.outputSchema), null, 2);
});

// AI OCR 字段映射操作
function addAiOcrFieldMapping() {
  if (!activeItem.value?.aiOcrConfig) return;
  if (!activeItem.value.aiOcrConfig.fieldMapping) {
    activeItem.value.aiOcrConfig.fieldMapping = [];
  }
  activeItem.value.aiOcrConfig.fieldMapping.push({
    source: '',
    target: '',
  });
}

function removeAiOcrFieldMapping(index: number) {
  if (!activeItem.value?.aiOcrConfig?.fieldMapping) return;
  activeItem.value.aiOcrConfig.fieldMapping.splice(index, 1);
}

// 表格选择器列配置操作
function addTableSelectorColumn() {
  if (!activeItem.value?.tableSelectorConfig) return;
  if (!activeItem.value.tableSelectorConfig.columns) {
    activeItem.value.tableSelectorConfig.columns = [];
  }
  activeItem.value.tableSelectorConfig.columns.push({
    field: '',
    label: '',
    width: undefined,
  });
}

function removeTableSelectorColumn(index: number) {
  if (!activeItem.value?.tableSelectorConfig?.columns) return;
  activeItem.value.tableSelectorConfig.columns.splice(index, 1);
}

// 表单选择器表单变更时加载字段
async function handleFormSelectorFormChange(_formCode: string) {
  // formCode 变更后，formSelectorAvailableFields 会自动重新计算
}

const activeTab = ref('props');

const tabItems = [
  { key: 'props', label: $t('form-design.attribute.componentProps') },
  { key: 'form', label: $t('form-design.attribute.formProps') },
];
const store = useFormDesignStore();
const { formConf, activeId, dataSource } = storeToRefs(store);

// 查找包含当前组件的子表单（返回 children 数组）
const findParentSubTable = (items: any[], targetId: string): any[] | null => {
  for (const item of items) {
    if (item.type === 'sub-table' && item.children) {
      for (const child of item.children) {
        if (child.id === targetId) {
          return item.children;
        }
      }
    }
    if (item.columns) {
      for (const col of item.columns) {
        const result = findParentSubTable(col.children || [], targetId);
        if (result) return result;
      }
    }
    if (item.items) {
      for (const subItem of item.items) {
        const result = findParentSubTable(subItem.children || [], targetId);
        if (result) return result;
      }
    }
    if (item.children && item.type !== 'sub-table') {
      const result = findParentSubTable(item.children, targetId);
      if (result) return result;
    }
  }
  return null;
};

// 查找包含当前组件的子表单（返回子表单对象本身）
const findParentSubTableItem = (items: any[], targetId: string): any | null => {
  for (const item of items) {
    if (item.type === 'sub-table' && item.children) {
      for (const child of item.children) {
        if (child.id === targetId) {
          return item;
        }
      }
    }
    if (item.columns) {
      for (const col of item.columns) {
        const result = findParentSubTableItem(col.children || [], targetId);
        if (result) return result;
      }
    }
    if (item.items) {
      for (const subItem of item.items) {
        const result = findParentSubTableItem(subItem.children || [], targetId);
        if (result) return result;
      }
    }
    if (item.children && item.type !== 'sub-table') {
      const result = findParentSubTableItem(item.children, targetId);
      if (result) return result;
    }
  }
  return null;
};

// 当前列的父子表是否开启了合计
const parentSubTableHasSummary = computed(() => {
  if (!isInsideSubTable.value || !activeId.value) return false;
  const parent = findParentSubTableItem(formConf.value?.items || [], activeId.value);
  return parent?.props?.summary === true;
});

// 支持公式计算的组件类型（除 formula-input 专用组件外）
const FORMULA_CAPABLE_TYPES = [
  'input-number',
  'money-input',
  'slider',
  'rate',
];

// 判断当前组件是否支持公式计算配置
const supportsFormula = computed(() => {
  if (!activeItem.value) return false;
  return FORMULA_CAPABLE_TYPES.includes(activeItem.value.type);
});

// 公式计算可用字段列表（数字类型字段，主表单+子表单全部可选）
const formulaAvailableFields = computed(() => {
  if (activeItem.value?.type !== 'formula-input' && !FORMULA_CAPABLE_TYPES.includes(activeItem.value?.type || '')) return [];

  const numericFields: Array<{ field: string; label: string; group?: string; isSubTableField?: boolean; subTableField?: string }> = [];
  const numericTypes = ['input-number', 'money-input', 'slider', 'rate', 'formula-input'];
  const currentField = activeItem.value?.field;

  // 找到当前组件所在的子表单 field（如果有）
  let currentSubTableField = '';
  if (isInsideSubTable.value && activeId.value) {
    const items = formConf.value?.items || [];
    for (const item of items) {
      if (item.type === 'sub-table' && item.children) {
        const found = item.children.some((child: any) => child.id === activeId.value);
        if (found) {
          currentSubTableField = item.field;
          break;
        }
      }
    }
  }

  // 收集所有数字字段
  // subTableField: 子表单的 field 名（空字符串表示主表单）
  // subTableLabel: 子表单的 label（用于分组显示）
  function collectFields(items: any[], subTableField = '', subTableLabel = '') {
    if (!items || !Array.isArray(items)) return;
    for (const item of items) {
      if (item.type === 'sub-table') {
        const stField = item.field;
        const stLabel = item.label || item.field;
        if (item.children) {
          collectFields(item.children, stField, stLabel);
        }
        continue;
      }
      if (numericTypes.includes(item.type)) {
        if (item.field && item.field !== currentField) {
          // 判断是否跨表引用
          const isCrossTable = subTableField
            ? (currentSubTableField !== subTableField) // 子表单字段，但不在当前子表单
            : !!currentSubTableField; // 主表单字段，但当前在子表单内（也算跨表，不过主表单字段直接引用即可）

          if (subTableField && currentSubTableField !== subTableField) {
            // 跨表引用子表单字段：用 subTableField.childField 格式，默认 SUM 聚合
            numericFields.push({
              field: `${subTableField}.${item.field}`,
              label: item.label || item.field,
              group: subTableLabel,
              isSubTableField: true,
              subTableField,
            });
          } else {
            // 同表引用（主表单引用主表单、子表单引用同一子表单）
            numericFields.push({
              field: item.field,
              label: item.label || item.field,
              group: subTableLabel || $t('form-design.attribute.mainForm'),
            });
          }
        }
      }
      if (item.columns) {
        for (const col of item.columns) {
          collectFields(col.children || [], subTableField, subTableLabel);
        }
      }
      if (item.items) {
        for (const subItem of item.items) {
          collectFields(subItem.children || [], subTableField, subTableLabel);
        }
      }
      if (item.children && item.type !== 'sub-table') {
        collectFields(item.children, subTableField, subTableLabel);
      }
    }
  }

  collectFields(formConf.value?.items || []);
  return numericFields;
});

// 公式可用字段按分组（主表单/各子表单）
const formulaFieldGroups = computed(() => {
  const groups: Array<{ group: string; fields: typeof formulaAvailableFields.value }> = [];
  const groupMap = new Map<string, typeof formulaAvailableFields.value>();
  for (const field of formulaAvailableFields.value) {
    const g = field.group || $t('form-design.attribute.mainForm');
    if (!groupMap.has(g)) {
      groupMap.set(g, []);
    }
    groupMap.get(g)!.push(field);
  }
  for (const [group, fields] of groupMap) {
    groups.push({ group, fields });
  }
  return groups;
});

// 插入公式字段（子表单字段自动包裹 SUM 聚合函数）
function insertFormulaField(field: string, isSubTableField = false) {
  if (!activeItem.value) return;
  const currentFormula = activeItem.value.props.formula || '';
  if (isSubTableField) {
    activeItem.value.props.formula = currentFormula + `SUM{${field}}`;
  } else {
    activeItem.value.props.formula = currentFormula + `{${field}}`;
  }
}

// 公式计算可用日期字段列表（用于 DATEDIFF 函数）
const formulaDateFields = computed(() => {
  if (activeItem.value?.type !== 'formula-input' && !FORMULA_CAPABLE_TYPES.includes(activeItem.value?.type || '')) return [];

  const dateFields: Array<{ field: string; label: string; group?: string }> = [];
  const dateTypes = ['date', 'current-datetime'];
  const currentField = activeItem.value?.field;

  // 找到当前组件所在的子表单 field（如果有）
  let currentSubTableField = '';
  if (isInsideSubTable.value && activeId.value) {
    const items = formConf.value?.items || [];
    for (const item of items) {
      if (item.type === 'sub-table' && item.children) {
        const found = item.children.some((child: any) => child.id === activeId.value);
        if (found) {
          currentSubTableField = item.field;
          break;
        }
      }
    }
  }

  function collectDateFields(items: any[], subTableField = '', subTableLabel = '') {
    if (!items || !Array.isArray(items)) return;
    for (const item of items) {
      if (item.type === 'sub-table') {
        if (item.children) {
          collectDateFields(item.children, item.field, item.label || item.field);
        }
        continue;
      }
      if (dateTypes.includes(item.type)) {
        if (item.field && item.field !== currentField) {
          // 同表引用：主表单引用主表单日期字段，或子表单引用同一子表单日期字段
          if (subTableField === currentSubTableField) {
            dateFields.push({
              field: item.field,
              label: item.label || item.field,
              group: subTableLabel || $t('form-design.attribute.mainForm'),
            });
          }
        }
      }
      if (item.columns) {
        for (const col of item.columns) {
          collectDateFields(col.children || [], subTableField, subTableLabel);
        }
      }
      if (item.items) {
        for (const subItem of item.items) {
          collectDateFields(subItem.children || [], subTableField, subTableLabel);
        }
      }
      if (item.children && item.type !== 'sub-table') {
        collectDateFields(item.children, subTableField, subTableLabel);
      }
    }
  }

  collectDateFields(formConf.value?.items || []);
  return dateFields;
});

// 日期关联：收集当前表单中可供关联的日期字段（排除自身）
const dateLinkedFields = computed(() => {
  if (activeItem.value?.type !== 'date') return [];
  const fields: Array<{ field: string; label: string }> = [];
  const currentField = activeItem.value?.field;

  function collect(items: any[]) {
    if (!items || !Array.isArray(items)) return;
    for (const item of items) {
      if (item.type === 'date' && item.field && item.field !== currentField) {
        fields.push({ field: item.field, label: item.label || item.field });
      }
      if (item.columns) {
        for (const col of item.columns) {
          collect(col.children || []);
        }
      }
      if (item.items) {
        for (const subItem of item.items) {
          collect(subItem.children || []);
        }
      }
      if (item.children && item.type !== 'sub-table') {
        collect(item.children);
      }
    }
  }

  collect(formConf.value?.items || []);
  return fields;
});

// 插入 DATEDIFF 公式模板
const dateDiffEndField = ref('');
const dateDiffStartField = ref('');
const dateDiffUnit = ref('days');

function insertDateDiffFormula(endField: string, startField: string, unit: string = 'days') {
  if (!activeItem.value) return;
  const currentFormula = activeItem.value.props.formula || '';
  activeItem.value.props.formula = currentFormula + `DATEDIFF{${endField}, ${startField}, ${unit}}`;
}

// 关联字段可用的源字段列表（选择类组件）
const linkedFieldSourceFields = computed(() => {
  const selectFields: Array<{ field: string; label: string; type: string }> = [];
  const selectTypes = ['select', 'cascader', 'tree-select', 'table-selector', 'form-selector', 'user-selector', 'dept-selector', 'post-selector', 'role-selector'];

  // 如果当前组件在子表单内，只收集同一子表单内的选择类组件
  if (isInsideSubTable.value && activeId.value) {
    const subTableChildren = findParentSubTable(formConf.value?.items || [], activeId.value);
    if (subTableChildren) {
      for (const item of subTableChildren) {
        if (selectTypes.includes(item.type)) {
          if (item.field && item.field !== activeItem.value?.field) {
            selectFields.push({
              field: item.field,
              label: item.label || item.field,
              type: item.type,
            });
          }
        }
      }
      return selectFields;
    }
  }

  // 主表单：收集所有非子表单内的选择类组件
  function collectFields(items: any[], skipSubTable = true) {
    if (!items || !Array.isArray(items)) return;
    for (const item of items) {
      // 跳过子表单内部的字段
      if (item.type === 'sub-table' && skipSubTable) {
        continue;
      }
      // 选择类组件
      if (selectTypes.includes(item.type)) {
        if (item.field && item.field !== activeItem.value?.field) {
          selectFields.push({
            field: item.field,
            label: item.label || item.field,
            type: item.type,
          });
        }
      }
      if (item.columns) {
        for (const col of item.columns) {
          collectFields(col.children || [], skipSubTable);
        }
      }
      if (item.items) {
        for (const subItem of item.items) {
          collectFields(subItem.children || [], skipSubTable);
        }
      }
      if (item.children && item.type !== 'sub-table') {
        collectFields(item.children, skipSubTable);
      }
    }
  }

  collectFields(formConf.value?.items || []);
  return selectFields;
});

// 关联字段可用的显示字段列表（根据源字段类型动态获取）
// 支持 linked-field 组件的 sourceField 和其他组件的 valueSourceField
const linkedFieldDisplayFields = computed(() => {
  // 优先使用 linked-field 的 sourceField，其次使用值关联的 valueSourceField
  const sourceField = activeItem.value?.props?.sourceField || activeItem.value?.props?.valueSourceField;
  if (!sourceField) return [];

  const sourceItem = linkedFieldSourceFields.value.find(f => f.field === sourceField);

  if (!sourceItem) return [];

  // 根据源字段类型返回常用字段
  const commonFields = [
    { field: 'id', label: 'ID' },
    { field: 'code', label: '编码' },
    { field: 'name', label: '名称' },
    { field: 'label', label: '标签' },
    { field: 'value', label: '值' },
  ];

  // 根据不同类型添加特定字段
  if (sourceItem.type === 'user-selector') {
    return [
      { field: 'id', label: '用户ID' },
      { field: 'username', label: '用户名' },
      { field: 'nickname', label: '昵称' },
      { field: 'email', label: '邮箱' },
      { field: 'phone', label: '手机号' },
      { field: 'deptId', label: '部门ID' },
      { field: 'deptName', label: '部门名称' },
    ];
  } else if (sourceItem.type === 'dept-selector') {
    return [
      { field: 'id', label: '部门ID' },
      { field: 'code', label: '部门编码' },
      { field: 'name', label: '部门名称' },
      { field: 'parentId', label: '父部门ID' },
    ];
  } else if (sourceItem.type === 'post-selector') {
    return [
      { field: 'id', label: '岗位ID' },
      { field: 'code', label: '岗位编码' },
      { field: 'name', label: '岗位名称' },
    ];
  } else if (sourceItem.type === 'role-selector') {
    return [
      { field: 'id', label: '角色ID' },
      { field: 'code', label: '角色编码' },
      { field: 'name', label: '角色名称' },
    ];
  } else if (sourceItem.type === 'table-selector') {
    // 表格选择器：从配置的列中获取字段
    const tableItem = findItemByField(sourceField);
    if (tableItem?.tableSelectorConfig?.columns) {
      return tableItem.tableSelectorConfig.columns.map((col: any) => ({
        field: col.field,
        label: col.label || col.field,
      }));
    }
  } else if (sourceItem.type === 'form-selector') {
    // 表单选择器：从已发布表单列表中获取关联表单的字段
    const formItem = findItemByField(sourceField);
    const formCode = formItem?.formSelectorConfig?.formCode;
    if (formCode) {
      loadPublishedFormList();
      const form = publishedFormList.value.find(f => f.code === formCode);
      if (form?.fields && form.fields.length > 0) {
        return form.fields.map((f: any) => ({
          field: f.field,
          label: f.label || f.field,
        }));
      }
    }
  } else if (sourceItem.type === 'select') {
    // select 组件：根据数据源类型返回不同的字段
    const selectItem = findItemByField(sourceField);
    const dataSource = selectItem?.dataSource;

    if (dataSource?.type === 'formData' && dataSource.formCode) {
      // 表单数据源：从已发布表单列表中获取字段
      loadPublishedFormList();
      const form = publishedFormList.value.find(f => f.code === dataSource.formCode);
      if (form?.fields && form.fields.length > 0) {
        return form.fields.map((f: any) => ({
          field: f.field,
          label: f.label || f.field,
        }));
      }
    }

    // 其他数据源（dict/api/dataSource/static）：选项数据只有 label、value、desc 三个字段
    return [
      { field: 'label', label: '标签' },
      { field: 'value', label: '值' },
      { field: 'desc', label: '描述' },
    ];
  }

  return commonFields;
});

// 支持值关联的组件类型（非 linked-field 组件）
const VALUE_LINKABLE_TYPES = [
  'input',
  'textarea',
  'input-number',
  'money-input',
  'select',
  'switch',
  'slider',
  'rate',
  'color',
  'date',
  'time',
  'cascader',
  'tree-select',
  'region-selector',
];

// 判断当前组件是否支持值关联
const supportsValueLink = computed(() => {
  if (!activeItem.value) return false;
  return VALUE_LINKABLE_TYPES.includes(activeItem.value.type);
});

// 根据字段名查找组件
function findItemByField(field: string): any {
  function find(items: any[]): any {
    if (!items || !Array.isArray(items)) return null;
    for (const item of items) {
      if (item.field === field) return item;
      if (item.columns) {
        for (const col of item.columns) {
          const found = find(col.children || []);
          if (found) return found;
        }
      }
      if (item.items) {
        for (const subItem of item.items) {
          const found = find(subItem.children || []);
          if (found) return found;
        }
      }
      if (item.children) {
        const found = find(item.children);
        if (found) return found;
      }
    }
    return null;
  }
  return find(formConf.value?.items || []);
}

const showOptionsEditor = ref(false);

const activeSections = ref([
  'basic',
  'text',
  'select',
  'option-style',
  'date',
  'time',
  'number',
  'switch',
  'rate',
  'color',
  'cascader',
  'tree',
  'selector',
  'cron',
  'image',
  'file',
  'alert',
  'timeline',
  'subtable',
  'table-column',
  'grid',
  'collapse',
  'tabs',
  'title',
  'operation',
  'default-value',
  'advanced',
  'validation',
  'options',
  'formula',
  'linkedField',
  'valueLink',
  'current-user',
  'current-datetime',
  'codeGenerator',
  'money-input',
  'formula-input',
  // 表单属性折叠面板
  'form-basic',
  'form-spacing',
  'form-size',
  'form-style',
]);

const toggleSection = (section: string) => {
  const index = activeSections.value.indexOf(section);
  if (index === -1) {
    activeSections.value.push(section);
  } else {
    activeSections.value.splice(index, 1);
  }
};

const handleOptionsConfirm = (data: any[]) => {
  if (activeItem.value) {
    activeItem.value.options = data;
  }
};

// 组件类型选项
const COMPONENT_TYPES = [
  { label: $t('form-design.material.components.input'), value: 'input' },
  { label: $t('form-design.material.components.textarea'), value: 'textarea' },
  { label: $t('form-design.material.components.richText'), value: 'rich-text' },
  { label: $t('form-design.material.components.number'), value: 'input-number' },
  { label: $t('form-design.material.components.select'), value: 'select' },
  { label: $t('form-design.material.components.radio'), value: 'radio' },
  { label: $t('form-design.material.components.checkbox'), value: 'checkbox' },
  { label: $t('form-design.material.components.date'), value: 'date' },
  { label: $t('form-design.material.components.time'), value: 'time' },
  { label: $t('form-design.material.components.switch'), value: 'switch' },
  { label: $t('form-design.material.components.slider'), value: 'slider' },
  { label: $t('form-design.material.components.rate'), value: 'rate' },
  { label: $t('form-design.material.components.color'), value: 'color' },
  { label: $t('form-design.material.components.cascader'), value: 'cascader' },
  { label: $t('form-design.material.components.treeSelect'), value: 'tree-select' },
  { label: $t('form-design.material.components.dept'), value: 'dept-selector' },
  { label: $t('form-design.material.components.user'), value: 'user-selector' },
  { label: $t('form-design.material.components.role'), value: 'role-selector' },
  { label: $t('form-design.material.components.post'), value: 'post-selector' },
  { label: $t('form-design.material.components.cron'), value: 'cron-selector' },
  { label: $t('form-design.material.components.image'), value: 'image-selector' },
  { label: $t('form-design.material.components.file'), value: 'file-selector' },
  { label: $t('form-design.material.components.regionSelector'), value: 'region-selector' },
  { label: $t('form-design.material.components.aiImageOcr'), value: 'ai-image-ocr' },
  { label: $t('form-design.material.components.tableSelector'), value: 'table-selector' },
  { label: $t('form-design.material.components.formSelector'), value: 'form-selector' },
  { label: $t('form-design.material.components.formulaInput'), value: 'formula-input' },
  { label: $t('form-design.material.components.linkedField'), value: 'linked-field' },
  { label: $t('form-design.material.components.codeGenerator'), value: 'code-generator' },
  { label: $t('form-design.material.components.signaturePad'), value: 'signature-pad' },
  { label: $t('form-design.material.components.qrcodeGenerator'), value: 'qrcode-generator' },
];

// 切换组件类型
const handleTypeChange = (type: string) => {
  if (!activeItem.value) return;

  // 备份部分通用属性
  const placeholder = activeItem.value.props?.placeholder;

  // 初始化新属性
  const newProps: Record<string, any> = {
    width: '100%',
    placeholder,
    disabled: false,
  };

  // 根据类型设置特定的默认属性
  switch (type) {
    case 'date': {
      Object.assign(newProps, {
        type: 'date',
        format: 'YYYY-MM-DD',
        valueFormat: 'YYYY-MM-DD',
      });
      break;
    }
    case 'input': {
      Object.assign(newProps, {
        clearable: true,
        maxlength: null,
        showWordLimit: true,
        showPassword: false,
        readonly: false,
      });
      break;
    }
    case 'input-number': {
      Object.assign(newProps, { controls: true, min: 0, readonly: false });
      break;
    }
    case 'rate': {
      Object.assign(newProps, { max: 5 });
      break;
    }
    case 'rich-text': {
      Object.assign(newProps, {
        minHeight: 200,
        maxHeight: 500,
        toolbarConfig: {
          insert: {
            link: true,
            image: true,
            table: true,
            attachment: false,
            video: false,
          },
        },
      });
      break;
    }
    case 'slider': {
      Object.assign(newProps, { min: 0, max: 100 });
      break;
    }
    case 'cascader': {
      Object.assign(newProps, {
        clearable: true,
        separator: '/',
        filterable: false,
        emitPath: false,
        checkStrictly: false,
      });
      break;
    }
    case 'switch': {
      Object.assign(newProps, { width: 40 });
      break;
    }
    case 'textarea': {
      Object.assign(newProps, {
        type: 'textarea',
        rows: 3,
        maxlength: null,
        showWordLimit: true,
        readonly: false,
      });
      break;
    }
  }

  // 如果切换到选择类组件，初始化 options
  if (
    ['cascader', 'checkbox', 'radio', 'select', 'tree-select'].includes(type)
  ) {
    if (!activeItem.value.options && !activeItem.value.dataSource) {
      activeItem.value.options = [
        { label: `${$t('form-design.attribute.addOption')} 1`, value: 1 },
        { label: `${$t('form-design.attribute.addOption')} 2`, value: 2 },
      ];
    }
    // 清理 tableSelectorConfig 和 formSelectorConfig
    delete activeItem.value.tableSelectorConfig;
    delete activeItem.value.formSelectorConfig;
  } else if (type === 'table-selector') {
    // 表格选择器：初始化 tableSelectorConfig 和 options
    if (!activeItem.value.tableSelectorConfig) {
      activeItem.value.tableSelectorConfig = {
        dialogTitle: $t('form-design.attribute.selectData'),
        dialogWidth: '800px',
        columns: [],
        searchFields: [],
        collapseTags: false,
      };
    }
    if (!activeItem.value.options) {
      activeItem.value.options = [];
    }
    if (!activeItem.value.dataSource) {
      activeItem.value.dataSource = {
        type: 'static',
        formCode: '',
        formLabelField: '',
        formValueField: '',
      };
    }
    delete activeItem.value.formSelectorConfig;
  } else if (type === 'form-selector') {
    // 表单选择器：初始化 formSelectorConfig
    if (!activeItem.value.formSelectorConfig) {
      activeItem.value.formSelectorConfig = {
        formCode: '',
        valueField: 'id',
        labelField: '',
      };
    }
    Object.assign(newProps, {
      dialogTitle: $t('form-design.attribute.selectData'),
      dialogWidth: '1200px',
    });
    delete activeItem.value.options;
    delete activeItem.value.dataSource;
    delete activeItem.value.tableSelectorConfig;
  } else if (type === 'code-generator') {
    // 编码生成：设置默认属性
    Object.assign(newProps, {
      prefix: '',
      separator: '-',
      generateMode: 'date_seq',
      dateFormat: 'YYYYMMDD',
      seqLength: 4,
      seqResetRule: 'daily',
      randomLength: 8,
      businessType: 'default',
      disabled: true,
      readonly: true,
      generateOnMount: true,
    });
    delete activeItem.value.options;
    delete activeItem.value.dataSource;
    delete activeItem.value.tableSelectorConfig;
    delete activeItem.value.formSelectorConfig;
  } else if (type === 'formula-input') {
    // 公式计算：设置默认属性
    Object.assign(newProps, {
      formula: '',
      precision: 2,
      disabled: true,
      showFormula: true,
    });
    delete activeItem.value.options;
    delete activeItem.value.dataSource;
    delete activeItem.value.tableSelectorConfig;
    delete activeItem.value.formSelectorConfig;
  } else if (type === 'linked-field') {
    // 关联字段：设置默认属性
    Object.assign(newProps, {
      sourceField: '',
      displayField: '',
      disabled: true,
    });
    delete activeItem.value.options;
    delete activeItem.value.dataSource;
    delete activeItem.value.tableSelectorConfig;
    delete activeItem.value.formSelectorConfig;
  } else {
    // 非选择类组件，清理 options 和 dataSource 和 tableSelectorConfig 和 formSelectorConfig
    delete activeItem.value.options;
    delete activeItem.value.dataSource;
    delete activeItem.value.tableSelectorConfig;
    delete activeItem.value.formSelectorConfig;
  }

  // 公式计算属性处理
  if (FORMULA_CAPABLE_TYPES.includes(type)) {
    // 切换到支持公式的类型：保留已有的公式配置
    const oldProps = activeItem.value.props || {};
    if (oldProps.enableFormula) {
      newProps.enableFormula = oldProps.enableFormula;
      newProps.formula = oldProps.formula;
      newProps.formulaPrecision = oldProps.formulaPrecision ?? 2;
    }
  } else {
    // 切换到不支持公式的类型：清理公式相关属性
    delete newProps.enableFormula;
    delete newProps.formula;
    delete newProps.formulaPrecision;
  }

  // 根据新类型和当前标签自动更新占位提示
  if (activeItem.value.label) {
    newProps.placeholder = generatePlaceholder(type, activeItem.value.label);
  }

  // 切换类型时清理默认值（旧默认值可能与新类型不兼容）
  delete activeItem.value.defaultValue;

  // 应用更改
  activeItem.value.type = type;
  activeItem.value.props = newProps;

  ElMessage.success(
    $t('form-design.message.switchTypeSuccess', {
      type: COMPONENT_TYPES.find((t) => t.value === type)?.label,
    }),
  );
};

// 日期显示类型切换时，自动更新显示格式和值格式
const handleDateTypeChange = (dateType: string) => {
  if (!activeItem.value) return;
  const formatMap: Record<string, { format: string; valueFormat: string }> = {
    date: { format: 'YYYY-MM-DD', valueFormat: 'YYYY-MM-DD' },
    week: { format: 'YYYY [W]ww', valueFormat: 'YYYY-[W]ww' },
    month: { format: 'YYYY-MM', valueFormat: 'YYYY-MM' },
    year: { format: 'YYYY', valueFormat: 'YYYY' },
    datetime: { format: 'YYYY-MM-DD HH:mm:ss', valueFormat: 'YYYY-MM-DD HH:mm:ss' },
    daterange: { format: 'YYYY-MM-DD', valueFormat: 'YYYY-MM-DD' },
    datetimerange: { format: 'YYYY-MM-DD HH:mm:ss', valueFormat: 'YYYY-MM-DD HH:mm:ss' },
  };
  const mapping = formatMap[dateType];
  if (mapping) {
    activeItem.value.props.format = mapping.format;
    activeItem.value.props.valueFormat = mapping.valueFormat;
  }
};

// 获取当前选中的组件对象（支持递归查找）
const activeItem = computed(() => {
  if (!activeId.value) return null;

  function findItem(items: any[]): any {
    for (const item of items) {
      if (item.id === activeId.value) return item;

      // 递归查找 grid
      if (item.columns) {
        for (const col of item.columns) {
          const found = findItem(col.children);
          if (found) return found;
        }
      }

      // 递归查找 collapse / tabs
      if (item.items) {
        for (const subItem of item.items) {
          const found = findItem(subItem.children);
          if (found) return found;
        }
      }

      // 递归查找 sub-table 或其他直接 children
      if (item.children) {
        const found = findItem(item.children);
        if (found) return found;
      }
    }
    return null;
  }

  return findItem(formConf.value.items);
});

// === 默认值动态选项：依赖 activeItem 的部分 ===
function refreshDefaultValueOptions() {
  const ds = activeItem.value?.dataSource;
  if (!ds || ds.type === 'static') {
    defaultValueDynamicOptions.value = [];
    return;
  }
  if (ds.type === 'dict' && ds.dictCode) {
    loadDefaultValueDictOptions(ds.dictCode);
  } else if (ds.type === 'dataSource' && ds.dataSourceCode) {
    loadDefaultValueDataSourceOptions(ds);
  } else if (ds.type === 'formData' && ds.formCode && ds.formLabelField && ds.formValueField) {
    loadDefaultValueFormDataOptions(ds);
  } else {
    defaultValueDynamicOptions.value = [];
  }
}

const defaultValueOptionsForSelect = computed(() => {
  const ds = activeItem.value?.dataSource;
  if (!ds || ds.type === 'static') {
    return activeItem.value?.options || [];
  }
  return defaultValueDynamicOptions.value;
});

watch(
  () => {
    const ds = activeItem.value?.dataSource;
    if (!ds) return null;
    return `${ds.type}|${ds.dictCode || ''}|${ds.dataSourceCode || ''}|${ds.formCode || ''}|${ds.formLabelField || ''}|${ds.formValueField || ''}`;
  },
  () => {
    if (activeItem.value && ['select', 'radio', 'checkbox'].includes(activeItem.value.type)) {
      refreshDefaultValueOptions();
    }
  },
  { immediate: true },
);

// 表单内边距联动：上下联动、左右联动
watch(() => formConf.value.formPaddingTop, (val) => {
  if (formConf.value.formPaddingLinked) {
    formConf.value.formPaddingBottom = val;
  }
});
watch(() => formConf.value.formPaddingBottom, (val) => {
  if (formConf.value.formPaddingLinked) {
    formConf.value.formPaddingTop = val;
  }
});
watch(() => formConf.value.formPaddingLeft, (val) => {
  if (formConf.value.formPaddingLinked) {
    formConf.value.formPaddingRight = val;
  }
});
watch(() => formConf.value.formPaddingRight, (val) => {
  if (formConf.value.formPaddingLinked) {
    formConf.value.formPaddingLeft = val;
  }
});
// 表单外边距联动
watch(() => formConf.value.formMarginTop, (val) => {
  if (formConf.value.formMarginLinked) {
    formConf.value.formMarginBottom = val;
  }
});
watch(() => formConf.value.formMarginBottom, (val) => {
  if (formConf.value.formMarginLinked) {
    formConf.value.formMarginTop = val;
  }
});
watch(() => formConf.value.formMarginLeft, (val) => {
  if (formConf.value.formMarginLinked) {
    formConf.value.formMarginRight = val;
  }
});
watch(() => formConf.value.formMarginRight, (val) => {
  if (formConf.value.formMarginLinked) {
    formConf.value.formMarginLeft = val;
  }
});

// 监听 activeItem 变化，当组件类型为 form-selector 时自动加载表单列表
watch(
  () => activeItem.value?.type,
  (type) => {
    if (type === 'form-selector') {
      loadPublishedFormList();
    }
  },
  { immediate: true }
);

// 监听数据源编码变化，自动加载数据源详情（获取参数定义）
watch(
  () => activeItem.value?.dataSource?.dataSourceCode,
  (code) => {
    if (code) {
      loadDataSourceDetail(code);
    } else {
      currentDataSourceDetail.value = null;
    }
  },
  { immediate: true }
);

// 判断当前组件是否在子表单内
const isInsideSubTable = computed(() => {
  if (!activeId.value) return false;
  let isInside = false;

  function traverse(items: any[], inside: boolean): boolean {
    for (const item of items) {
      if (item.id === activeId.value) {
        isInside = inside;
        return true;
      }

      const childInside = inside || item.type === 'sub-table';

      if (item.columns) {
        for (const col of item.columns) {
          if (traverse(col.children, childInside)) return true;
        }
      }
      if (item.items) {
        for (const subItem of item.items) {
          if (traverse(subItem.children, childInside)) return true;
        }
      }
      if (item.children && traverse(item.children, childInside)) return true;
    }
    return false;
  }

  traverse(formConf.value.items, false);
  return isInside;
});

// 后端自动处理的系统字段（禁止选择，标注"自动处理"）
const AUTO_HANDLED_FIELDS = [
  'sys_create_datetime',
  'sys_update_datetime',
  'sys_creator_id',
  'sys_modifier_id',
  'sys_dept_id',
];

// 判断字段是否为系统字段（主键、ID、外键）
const isSystemField = (field: any, foreignKey?: string) => {
  return (
    field.isPrimaryKey ||
    field.name.toLowerCase() === 'id' ||
    (foreignKey && field.name === foreignKey)
  );
};

// 判断字段是否为自动处理字段（后端自动处理）
const isAutoHandledField = (fieldName: string) => {
  return AUTO_HANDLED_FIELDS.includes(fieldName);
};

// 可选字段列表（包含主键、ID、外键，但标记为系统字段；自动处理字段禁止选择）
const availableFields = computed(() => {
  if (isInsideSubTable.value) {
    // 子表单内，显示所有从表的字段（包括主键、ID、外键）
    return (dataSource.value.subTables || []).flatMap((t) =>
      t.fields.map((f) => {
        const autoHandled = isAutoHandledField(f.name);
        const systemField = isSystemField(f, t.foreignKey);
        let labelSuffix = '';
        if (autoHandled) {
          labelSuffix = ` [${$t('form-design.attribute.autoHandled')}]`;
        } else if (systemField) {
          labelSuffix = ` [${$t('form-design.attribute.system')}]`;
        }
        return {
          ...f,
          label: `${f.name} (${f.comment}) - [${t.tableName}]${labelSuffix}`,
          value: f.name,
          tableType: 'sub',
          foreignKey: t.foreignKey,
          isSystemField: systemField,
          isAutoHandled: autoHandled,
          disabled: autoHandled,
        };
      }),
    );
  } else {
    // 主表字段（包括主键、ID）
    return (dataSource.value.mainTable?.fields || []).map((f) => {
      const autoHandled = isAutoHandledField(f.name);
      const systemField = isSystemField(f);
      let labelSuffix = '';
      if (autoHandled) {
        labelSuffix = ` [${$t('form-design.attribute.autoHandled')}]`;
      } else if (systemField) {
        labelSuffix = ` [${$t('form-design.attribute.system')}]`;
      }
      return {
        ...f,
        label: `${f.name} (${f.comment})${labelSuffix}`,
        value: f.name,
        tableType: 'main',
        isSystemField: systemField,
        isAutoHandled: autoHandled,
        disabled: autoHandled,
      };
    });
  }
});

// 根据组件类型和字段标签自动生成占位提示
const generatePlaceholder = (type: string, label: string): string => {
  if (!label) return '';
  // 选择类组件用“请选择”
  const selectTypes = [
    'select', 'cascader', 'tree-select', 'radio', 'checkbox',
    'date', 'time', 'color', 'rate', 'slider',
    'dept-selector', 'user-selector', 'role-selector', 'post-selector',
    'cron-selector', 'image-selector', 'file-selector', 'region-selector',
    'table-selector', 'form-selector',
  ];
  // 自动生成类组件不需要占位提示
  const autoTypes = ['code-generator', 'current-user', 'current-datetime', 'formula-input', 'linked-field'];
  if (autoTypes.includes(type)) {
    return $t('form-design.attribute.systemAutoGenerate');
  }
  if (selectTypes.includes(type)) {
    return $t('common.selectPlaceholder') + label;
  }
  return $t('common.placeholder') + label;
};

// 字段变更处理
const onFieldChange = (val: string) => {
  if (!activeItem.value) return;

  const field = availableFields.value.find((f) => f.value === val);
  if (field) {
    // 自动同步属性
    // 如果当前 Label 是默认值或空，才覆盖
    // 或者始终覆盖？为了体验，既然选了字段，通常期望同步 Label
    activeItem.value.label = field.comment || field.name;

    // 自动填充占位提示
    if (activeItem.value.props) {
      activeItem.value.props.placeholder = generatePlaceholder(
        activeItem.value.type,
        activeItem.value.label,
      );
    }

    if (activeItem.value.type === 'input' && field.type) {
      // 解析长度
      const match = field.type.match(/\((\d+)\)/);
      if (match && match[1] && activeItem.value.props) {
        activeItem.value.props.maxlength = Number.parseInt(match[1], 10);
      }
    }

    ElMessage.success($t('form-design.message.fieldLinked', { name: field.name }));
  }
};

// 根据字段类型映射组件类型
const getComponentTypeByFieldType = (fieldType: string) => {
  const type = fieldType.toLowerCase();
  if (
    type.includes('int') ||
    type.includes('decimal') ||
    type.includes('numeric') ||
    type.includes('float') ||
    type.includes('double')
  ) {
    return 'input-number';
  }
  if (
    type.includes('datetime') ||
    type.includes('timestamp') ||
    type.includes('date')
  ) {
    return 'date';
  }
  if (type.includes('text') || type.includes('long') || type.includes('blob')) {
    return 'textarea';
  }
  if (type.includes('bool') || type.includes('tinyint(1)')) {
    return 'switch';
  }
  return 'input';
};

// 子表单关联从表变更处理
const onSubTableLinkChange = (tableName: string) => {
  if (!activeItem.value || activeItem.value.type !== 'sub-table') return;

  const subTable = dataSource.value.subTables.find(
    (t) => t.tableName === tableName,
  );
  if (subTable) {
    // 自动更新子表单的 field 和 label
    activeItem.value.field = subTable.tableName;
    activeItem.value.label = subTable.alias || subTable.tableName;
    ElMessage.success($t('form-design.message.tableLinked', { name: subTable.tableName }));
  }
};

// 自动填充子表单字段
const autoFillSubTableFields = () => {
  if (!activeItem.value || activeItem.value.type !== 'sub-table') return;

  const tableName = activeItem.value.field;
  const subTable = dataSource.value.subTables.find(
    (t) => t.tableName === tableName,
  );

  if (!subTable) {
    ElMessage.warning($t('form-design.message.selectSubTableFirst'));
    return;
  }

  // 生成子表单的子组件（包括主键、ID、外键，但设为禁用）
  const newChildren = subTable.fields.map((field) => {
    const type = getComponentTypeByFieldType(field.type);
    const isSystem = isSystemField(field, subTable.foreignKey);
    return store.cloneComponent({
      type,
      label: field.comment || field.name,
      field: field.name,
      props: {
        placeholder: isSystem
          ? $t('form-design.attribute.systemAutoGenerate')
          : $t('common.placeholder') + (field.comment || field.name),
        width: '100%',
        disabled: isSystem, // 系统字段默认禁用
      },
      isSystemField: isSystem,
    });
  });

  // 确保 children 数组存在
  if (!activeItem.value.children) {
    activeItem.value.children = [];
  }

  // 追加新字段（不覆盖已有的）
  const existingFields = new Set(
    activeItem.value.children.map((c: any) => c.field),
  );
  const fieldsToAdd = newChildren.filter((c) => !existingFields.has(c.field));

  if (fieldsToAdd.length === 0) {
    ElMessage.info($t('form-design.message.noNewFields'));
    return;
  }

  activeItem.value.children.push(...fieldsToAdd);
  ElMessage.success($t('form-design.message.fieldsAdded', { count: fieldsToAdd.length }));
};

// 检查当前组件是否有该属性
const hasProp = (propName: string) => {
  if (!activeItem.value) return false;
  return (
    activeItem.value.props &&
    Object.prototype.hasOwnProperty.call(activeItem.value.props, propName)
  );
};

// 选项管理
const addOption = () => {
  if (activeItem.value && activeItem.value.options) {
    activeItem.value.options.push({
      label: `${$t('form-design.attribute.addOption')} ${activeItem.value.options.length + 1}`,
      value: activeItem.value.options.length + 1,
    });
  }
};

const removeOption = (index: number) => {
  if (activeItem.value && activeItem.value.options) {
    activeItem.value.options.splice(index, 1);
  }
};

// 栅格列管理
const redistributeGridSpan = () => {
  if (!activeItem.value || activeItem.value.type !== 'grid' || !activeItem.value.columns) {
    return;
  }

  const columnCount = activeItem.value.columns.length;
  const averageSpan = Math.floor(24 / columnCount);
  const remainder = 24 % columnCount;

  activeItem.value.columns.forEach((col: any, index: number) => {
    // 前 remainder 列多分配 1 个单位
    col.span = averageSpan + (index < remainder ? 1 : 0);
  });
};

const addGridColumn = () => {
  if (!activeItem.value || !activeItem.value.columns) return;

  activeItem.value.columns.push({ span: 12, children: [] });
  redistributeGridSpan();
};

const removeGridColumn = (index: number) => {
  if (!activeItem.value || !activeItem.value.columns) return;
  if (activeItem.value.columns.length <= 1) return;

  activeItem.value.columns.splice(index, 1);
  redistributeGridSpan();
};

// 校验规则相关
const REG_PATTERNS = [
  { label: $t('form-design.attribute.custom'), pattern: 'custom', message: '' },
  {
    label: $t('form-design.attribute.mobile'),
    pattern: String.raw`/^1[3-9]\d{9}$/`,
    message: $t('form-design.attribute.mobile') + $t('form-design.attribute.errorMessageSuffix'),
  },
  {
    label: $t('form-design.attribute.email'),
    pattern: String.raw`/^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$/`,
    message: $t('form-design.attribute.email') + $t('form-design.attribute.errorMessageSuffix'),
  },
  {
    label: $t('form-design.attribute.idCard'),
    pattern: String.raw`/^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/`,
    message: $t('form-design.attribute.idCard') + $t('form-design.attribute.errorMessageSuffix'),
  },
  {
    label: $t('form-design.attribute.url'),
    pattern: String.raw`/^((https?|ftp|file):\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/`,
    message: $t('form-design.attribute.url') + $t('form-design.attribute.errorMessageSuffix'),
  },
  { label: $t('form-design.attribute.integer'), pattern: String.raw`/^-?\d+$/`, message: $t('common.placeholder') + $t('form-design.attribute.integer') },
  {
    label: $t('form-design.attribute.number'),
    pattern: String.raw`/^-?\d+(\.\d+)?$/`,
    message: $t('common.placeholder') + $t('form-design.attribute.number'),
  },
  {
    label: $t('form-design.attribute.code'),
    pattern: String.raw`/^[a-z][a-z0-9_]*$/`,
    message: $t('form-design.attribute.code') + $t('form-design.attribute.errorMessageSuffix'),
  },
];

const LAYOUT_TYPES = new Set(['collapse', 'divider', 'grid', 'spacer', 'steps', 'tabs', 'title']);

const isLayoutComponent = computed(() => {
  if (!activeItem.value) return false;
  return LAYOUT_TYPES.has(activeItem.value.type);
});

// 不支持默认值的组件类型（布局、自动生成、计算类、文件类等）
const NO_DEFAULT_VALUE_TYPES = new Set([
  ...LAYOUT_TYPES,
  'sub-table',
  'current-user',
  'current-datetime',
  'code-generator',
  'formula-input',
  'linked-field',
  'image-selector',
  'file-selector',
  'ai-image-ocr',
  'signature-pad',
  'rich-text',
  'alert',
  'cron-selector',
]);

const supportsDefaultValue = computed(() => {
  if (!activeItem.value) return false;
  return !NO_DEFAULT_VALUE_TYPES.has(activeItem.value.type);
});

// 需要显示正则校验的组件类型（仅文本输入类）
const REGEX_VALIDATION_TYPES = new Set(['input', 'textarea']);

const showValidation = computed(() => {
  if (!activeItem.value) return false;
  const type = activeItem.value.type;
  // 只有文本输入类组件才显示正则校验
  return REGEX_VALIDATION_TYPES.has(type);
});

const addRegRule = () => {
  if (!activeItem.value) return;
  if (!activeItem.value.regList) {
    activeItem.value.regList = [];
  }
  activeItem.value.regList.push({ pattern: '', message: '' });
};

const handlePatternChange = (val: string, rule: any) => {
  if (val === 'custom') {
    rule.pattern = '';
    rule.message = '';
    return;
  }
  const pattern = REG_PATTERNS.find((p) => p.pattern === val);
  if (pattern) {
    rule.pattern = pattern.pattern;
    rule.message = pattern.message;
  }
};

// 获取规则对应的 Select 值（预设正则返回对应值，否则返回 'custom'）
const getPatternSelectValue = (pattern: string) => {
  if (!pattern) return 'custom';
  const found = REG_PATTERNS.find(
    (p) => p.pattern === pattern && p.pattern !== 'custom',
  );
  return found ? found.pattern : 'custom';
};

// 唯一性校验：支持的组件类型
const UNIQUE_CHECK_TYPES = new Set(['input', 'input-number', 'textarea', 'money-input', 'select', 'code-generator']);

// 是否显示唯一性校验
const showUniqueCheck = computed(() => {
  if (!activeItem.value) return false;
  return UNIQUE_CHECK_TYPES.has(activeItem.value.type);
});

// 跨字段校验：支持的组件类型
const CROSS_VALIDATION_TYPES = new Set(['date', 'input-number', 'money-input', 'slider', 'rate']);

// 是否显示跨字段校验
const showCrossValidation = computed(() => {
  if (!activeItem.value) return false;
  return CROSS_VALIDATION_TYPES.has(activeItem.value.type);
});

// 跨字段校验运算符
const crossValidationOperators = computed(() => {
  const isDate = activeItem.value?.type === 'date';
  return [
    { value: 'gt', label: isDate ? $t('form-design.attribute.crossValidation.afterTarget') : $t('form-design.attribute.crossValidation.greaterThan') },
    { value: 'gte', label: isDate ? $t('form-design.attribute.crossValidation.afterOrEqualTarget') : $t('form-design.attribute.crossValidation.greaterThanOrEqual') },
    { value: 'lt', label: isDate ? $t('form-design.attribute.crossValidation.beforeTarget') : $t('form-design.attribute.crossValidation.lessThan') },
    { value: 'lte', label: isDate ? $t('form-design.attribute.crossValidation.beforeOrEqualTarget') : $t('form-design.attribute.crossValidation.lessThanOrEqual') },
    { value: 'eq', label: $t('form-design.attribute.crossValidation.equalTo') },
    { value: 'ne', label: $t('form-design.attribute.crossValidation.notEqualTo') },
  ];
});

// 收集可比较的字段（同类型：日期对日期，数字对数字）
const crossValidationFields = computed(() => {
  if (!activeItem.value) return [];
  const currentType = activeItem.value.type;
  const currentField = activeItem.value.field;
  const fields: Array<{ field: string; label: string }> = [];

  const dateTypes = new Set(['date', 'current-datetime']);
  const numberTypes = new Set(['input-number', 'money-input', 'slider', 'rate', 'formula-input']);

  const isDateType = dateTypes.has(currentType);
  const matchTypes = isDateType ? dateTypes : numberTypes;

  function collect(items: any[]) {
    if (!items || !Array.isArray(items)) return;
    for (const item of items) {
      if (matchTypes.has(item.type) && item.field && item.field !== currentField) {
        fields.push({ field: item.field, label: item.label || item.field });
      }
      if (item.columns) {
        for (const col of item.columns) collect(col.children || []);
      }
      if (item.items) {
        for (const subItem of item.items) collect(subItem.children || []);
      }
      if (item.children && item.type !== 'sub-table') {
        collect(item.children);
      }
    }
  }

  collect(formConf.value?.items || []);
  return fields;
});

function addCrossValidation() {
  if (!activeItem.value) return;
  if (!activeItem.value.props.crossValidations) {
    activeItem.value.props.crossValidations = [];
  }
  activeItem.value.props.crossValidations.push({
    targetField: '',
    operator: 'lte',
    message: '',
  });
}

function removeCrossValidation(index: number) {
  if (!activeItem.value?.props.crossValidations) return;
  activeItem.value.props.crossValidations.splice(index, 1);
}

// 获取当前数据来源类型
const currentDataSourceType = computed(() => {
  if (!activeItem.value) return 'static';
  return activeItem.value.dataSource?.type || 'static';
});

// 切换数据来源类型
const handleDataSourceTypeChange = (
  val: boolean | number | string | undefined,
) => {
  if (!activeItem.value || !val) return;
  const type = val as DataSourceType;

  // 切换数据源类型时清理默认值（旧默认值可能与新数据源不兼容）
  delete activeItem.value.defaultValue;

  if (type === 'static') {
    // 静态模式，清除 dataSource 配置
    activeItem.value.dataSource = undefined;
    defaultValueDynamicOptions.value = [];
  } else {
    // 初始化 dataSource 配置
    activeItem.value.dataSource = {
      type,
      labelField: 'label',
      valueField: 'value',
      descField: '',
      childrenField: 'children',
      apiMethod: 'GET',
    };

    // 如果是字典模式，加载字典列表
    if (type === 'dict') {
      loadDictList();
    }
    // 如果是数据源模式，加载数据源列表
    if (type === 'dataSource') {
      loadDataSourceList();
    }
    // 如果是表单数据模式，加载已发布表单列表
    if (type === 'formData') {
      loadPublishedFormList();
    }
  }
};

// 添加表单数据过滤条件
const addFormDataFilter = () => {
  if (!activeItem.value?.dataSource) return;
  if (!activeItem.value.dataSource.formFilters) {
    activeItem.value.dataSource.formFilters = [];
  }
  activeItem.value.dataSource.formFilters.push({
    targetField: '',
    sourceField: '',
    filterType: 'eq',
  } as FormDataFilter);
};

// 删除表单数据过滤条件
const removeFormDataFilter = (index: number) => {
  if (!activeItem.value?.dataSource?.formFilters) return;
  activeItem.value.dataSource.formFilters.splice(index, 1);
};

// 获取表单中所有可依赖的字段（排除自身和布局组件）
const dependableFields = computed(() => {
  if (!activeItem.value) return [];

  const fields: { label: string; value: string; type?: string }[] = [];
  const currentId = activeItem.value.id;

  function collectFields(items: any[]) {
    for (const item of items) {
      // 排除自身和布局组件
      if (
        item.id !== currentId &&
        !['collapse', 'divider', 'grid', 'tabs', 'sub-table', 'alert', 'timeline'].includes(item.type)
      ) {
        fields.push({
          label: item.label || item.field,
          value: item.field,
          type: item.type // 添加组件类型信息
        });
      }
      // 递归收集
      if (item.columns) {
        for (const col of item.columns) {
          collectFields(col.children || []);
        }
      }
      if (item.items) {
        for (const subItem of item.items) {
          collectFields(subItem.children || []);
        }
      }
      if (item.children) {
        collectFields(item.children);
      }
    }
  }

  collectFields(formConf.value.items);
  return fields;
});
</script>

<template>
  <div
    class="attribute-panel flex h-full w-[306px] flex-col rounded border-[var(--el-border-color)] bg-[var(--el-bg-color)]"
  >
    <div class="p-2">
      <ZqTabs v-model="activeTab" :items="tabItems" />
    </div>
    <div class="flex-1 overflow-hidden">
      <div v-if="activeTab === 'props'" class="h-full">
        <ElScrollbar v-if="activeItem" class="h-full">
          <div class="px-4 pb-4">
            <ElForm label-position="top" size="small">
              <!-- 基础属性 -->
              <div
                class="group-title mb-2 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                @click="toggleSection('basic')"
              >
                <span class="font-bold">{{ $t('form-design.attribute.basicSettings') }}</span>
                <ElIcon class="h-4 w-4">
                  <ArrowDown v-if="activeSections.includes('basic')" />
                  <ArrowRight v-else />
                </ElIcon>
              </div>
              <div v-show="activeSections.includes('basic')">
                <ElFormItem :label="$t('form-design.attribute.type')">
                  <ElSelect
                    :model-value="activeItem.type"
                    :placeholder="$t('form-design.attribute.type')"
                    filterable
                    class="w-full"
                    @change="handleTypeChange"
                  >
                    <ElOption
                      v-for="type in COMPONENT_TYPES"
                      :key="type.value"
                      :label="type.label"
                      :value="type.value"
                    />
                  </ElSelect>
                </ElFormItem>

                <ElFormItem :label="$t('form-design.attribute.field')">
                  <div class="flex w-full items-center gap-1">
                    <ElSelect
                      v-model="activeItem.field"
                      filterable
                      allow-create
                      default-first-option
                      :placeholder="$t('form-design.attribute.field')"
                      class="flex-1"
                      @change="onFieldChange"
                    >
                      <ElOption
                        v-for="field in availableFields"
                        :key="field.value"
                        :label="field.label"
                        :value="field.value"
                        :disabled="field.disabled"
                      >
                        <div class="flex items-center justify-between">
                          <span>{{ field.value }}</span>
                          <span
                            class="text-xs text-[var(--el-text-color-secondary)]"
                            >{{ field.comment }}</span
                          >
                        </div>
                      </ElOption>
                    </ElSelect>
                  </div>
                </ElFormItem>

                <ElFormItem :label="$t('form-design.attribute.label')">
                  <ElInput v-model="activeItem.label" />
                </ElFormItem>

                <ElFormItem :label="$t('form-design.attribute.hideLabel')">
                  <ElSwitch v-model="activeItem.hideLabel" />
                </ElFormItem>

                <ElFormItem
                  v-if="!['grid', 'tabs', 'collapse', 'sub-table', 'divider', 'alert', 'steps'].includes(activeItem.type)"
                  :label="$t('form-design.attribute.labelPosition')"
                >
                  <ElRadioGroup
                    v-model="activeItem.labelPosition"
                    size="small"
                  >
                    <ElRadioButton label="">
                      {{ $t('form-design.attribute.followForm') }}
                    </ElRadioButton>
                    <ElRadioButton label="left">
                      {{ $t('form-design.attribute.location.left') }}
                    </ElRadioButton>
                    <ElRadioButton label="right">
                      {{ $t('form-design.attribute.location.right') }}
                    </ElRadioButton>
                    <ElRadioButton label="top">
                      {{ $t('form-design.attribute.location.top') }}
                    </ElRadioButton>
                  </ElRadioGroup>
                </ElFormItem>

                <ElFormItem :label="$t('form-design.attribute.isHidden')">
                  <ElSwitch v-model="activeItem.isHidden" />
                </ElFormItem>

                <!-- 通用属性 -->
                <ElFormItem
                  :label="$t('form-design.attribute.width')"
                  v-if="hasProp('width') && activeItem.type !== 'switch'"
                >
                  <ElInput v-model="activeItem.props.width" />
                </ElFormItem>

                <ElFormItem
                  :label="$t('form-design.attribute.placeholder')"
                  v-if="hasProp('placeholder')"
                >
                  <ElInput v-model="activeItem.props.placeholder" />
                </ElFormItem>

                <ElFormItem
                  v-if="!isLayoutComponent"
                  :label="$t('form-design.attribute.helpText')"
                >
                  <ElSwitch v-model="activeItem.props.showHelp" />
                </ElFormItem>
                <template v-if="!isLayoutComponent && activeItem.props.showHelp">
                  <ElFormItem :label="$t('form-design.attribute.helpDisplayMode')">
                    <ElRadioGroup v-model="activeItem.props.helpDisplayMode" size="small">
                      <ElRadioButton value="text">{{ $t('form-design.attribute.helpModeText') }}</ElRadioButton>
                      <ElRadioButton value="icon">{{ $t('form-design.attribute.helpModeIcon') }}</ElRadioButton>
                    </ElRadioGroup>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.helpContent')">
                    <ElInput
                      v-model="activeItem.props.helpText"
                      type="textarea"
                      :rows="2"
                      :placeholder="$t('form-design.attribute.helpTextPlaceholder')"
                    />
                  </ElFormItem>
                </template>
              </div>

              <!-- Input / Textarea 特有属性 -->
              <template v-if="['input', 'textarea'].includes(activeItem.type)">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('text')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.textProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('text')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('text')">
                  <ElFormItem :label="$t('form-design.attribute.maxlength')">
                    <ElInputNumber
                      v-model="activeItem.props.maxlength"
                      :min="0"
                      controls-position="right"
                      class="w-full"
                    />
                  </ElFormItem>
                  <ElFormItem
                    :label="$t('form-design.attribute.rows')"
                    v-if="activeItem.type === 'textarea'"
                  >
                    <ElInputNumber
                      v-model="activeItem.props.rows"
                      :min="1"
                      controls-position="right"
                      class="w-full"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.showWordLimit')">
                    <ElSwitch v-model="activeItem.props.showWordLimit" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.readonly')">
                    <ElSwitch v-model="activeItem.props.readonly" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.password')" v-if="activeItem.type === 'input'">
                    <ElSwitch v-model="activeItem.props.showPassword" />
                  </ElFormItem>
                  <ElFormItem v-if="activeItem.type === 'input'" :label="$t('form-design.attribute.autoUppercase')">
                    <ElSwitch v-model="activeItem.props.autoUppercase" @change="(val: boolean) => { if (val) activeItem.props.autoLowercase = false }" />
                  </ElFormItem>
                  <ElFormItem v-if="activeItem.type === 'input'" :label="$t('form-design.attribute.autoLowercase')">
                    <ElSwitch v-model="activeItem.props.autoLowercase" @change="(val: boolean) => { if (val) activeItem.props.autoUppercase = false }" />
                  </ElFormItem>
                  <ElFormItem v-if="activeItem.type === 'input'" :label="$t('form-design.attribute.showAddon')">
                    <ElSwitch v-model="activeItem.props.showAddon" />
                  </ElFormItem>
                  <template v-if="activeItem.type === 'input' && activeItem.props.showAddon">
                    <ElFormItem :label="$t('form-design.attribute.addonBefore')">
                      <ElInput
                        v-model="activeItem.props.addonBefore"
                        :placeholder="$t('form-design.attribute.addonPlaceholder')"
                        clearable
                      />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.addonAfter')">
                      <ElInput
                        v-model="activeItem.props.addonAfter"
                        :placeholder="$t('form-design.attribute.addonPlaceholder')"
                        clearable
                      />
                    </ElFormItem>
                  </template>
                </div>
              </template>

              <!-- 值关联设置（适用于输入类组件） -->
              <template v-if="supportsValueLink">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('valueLink')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.valueLinkProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('valueLink')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('valueLink')">
                  <ElFormItem :label="$t('form-design.attribute.enableValueLink')">
                    <ElSwitch v-model="activeItem.props.enableValueLink" />
                  </ElFormItem>
                  <template v-if="activeItem.props.enableValueLink">
                    <ElFormItem :label="$t('form-design.attribute.isVirtualField')">
                      <ElSwitch v-model="activeItem.props.isVirtualField" />
                    </ElFormItem>
                    <div v-if="activeItem.props.isVirtualField" class="mb-2 text-xs text-[var(--el-text-color-secondary)]">
                      {{ $t('form-design.attribute.virtualFieldTip') }}
                    </div>
                    <ElFormItem :label="$t('form-design.attribute.linkedSourceField')">
                      <ElSelect
                        v-model="activeItem.props.valueSourceField"
                        :placeholder="$t('form-design.attribute.selectSourceField')"
                        filterable
                        clearable
                        class="w-full"
                      >
                        <ElOption
                          v-for="field in linkedFieldSourceFields"
                          :key="field.field"
                          :label="`${field.label} (${field.field})`"
                          :value="field.field"
                        />
                      </ElSelect>
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.linkedDisplayField')">
                      <ElSelect
                        v-model="activeItem.props.valueDisplayField"
                        :placeholder="$t('form-design.attribute.displayFieldPlaceholder')"
                        filterable
                        allow-create
                        clearable
                        class="w-full"
                        :disabled="!activeItem.props.valueSourceField"
                      >
                        <ElOption
                          v-for="field in linkedFieldDisplayFields"
                          :key="field.field"
                          :label="`${field.label} (${field.field})`"
                          :value="field.field"
                        />
                      </ElSelect>
                    </ElFormItem>
                    <div class="mb-2 text-xs text-[var(--el-text-color-secondary)]">
                      {{ $t('form-design.attribute.valueLinkTip') }}
                    </div>
                  </template>
                </div>
              </template>

              <!-- 公式计算设置（适用于数字类组件） -->
              <template v-if="supportsFormula">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('formulaCalc')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.formulaCalcProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('formulaCalc')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('formulaCalc')">
                  <ElFormItem :label="$t('form-design.attribute.enableFormula')">
                    <ElSwitch v-model="activeItem.props.enableFormula" />
                  </ElFormItem>
                  <template v-if="activeItem.props.enableFormula">
                    <ElFormItem :label="$t('form-design.attribute.formula')">
                      <ElInput
                        v-model="activeItem.props.formula"
                        type="textarea"
                        :rows="3"
                        :placeholder="$t('form-design.attribute.formulaPlaceholder')"
                      />
                    </ElFormItem>
                    <div class="mb-2 text-xs text-[var(--el-text-color-secondary)]">
                      {{ $t('form-design.attribute.formulaTip') }}
                    </div>
                    <!-- 可用字段列表（分组显示） -->
                    <div class="mb-2">
                      <div class="mb-1 text-xs font-medium">{{ $t('form-design.attribute.availableFields') }}</div>
                      <template v-for="group in formulaFieldGroups" :key="group.group">
                        <div class="mb-1 mt-2 text-xs text-[var(--el-text-color-secondary)]">{{ group.group }}</div>
                        <div class="flex flex-wrap gap-1">
                          <ElTag
                            v-for="field in group.fields"
                            :key="field.field"
                            size="small"
                            class="cursor-pointer"
                            @click="insertFormulaField(field.field, field.isSubTableField)"
                          >
                            {{ field.label }} ({{ field.isSubTableField ? 'SUM' : '' }}{{"{"}}{{ field.field }}{{"}"}}）
                          </ElTag>
                        </div>
                      </template>
                      <div v-if="formulaAvailableFields.length === 0 && formulaDateFields.length === 0" class="text-xs text-[var(--el-text-color-placeholder)]">
                        {{ $t('form-design.attribute.noAvailableFields') }}
                      </div>
                    </div>
                    <!-- 日期差值计算（DATEDIFF） -->
                    <div v-if="formulaDateFields.length >= 2" class="mb-2">
                      <!-- <div class="mb-1 text-xs font-medium">{{ $t('form-design.attribute.dateDiffTitle') }}</div> -->
                      <div class="mb-1 text-xs text-[var(--el-text-color-secondary)]">
                        {{ $t('form-design.attribute.dateDiffTip') }}
                      </div>
                      <div class="flex flex-col gap-2">
                        <ElSelect
                          v-model="dateDiffEndField"
                          :placeholder="$t('form-design.attribute.dateDiffEndField')"
                          size="small"
                          class="w-full"
                        >
                          <ElOption
                            v-for="field in formulaDateFields"
                            :key="field.field"
                            :label="`${field.label} (${field.field})`"
                            :value="field.field"
                          />
                        </ElSelect>
                        <ElSelect
                          v-model="dateDiffStartField"
                          :placeholder="$t('form-design.attribute.dateDiffStartField')"
                          size="small"
                          class="w-full"
                        >
                          <ElOption
                            v-for="field in formulaDateFields"
                            :key="field.field"
                            :label="`${field.label} (${field.field})`"
                            :value="field.field"
                          />
                        </ElSelect>
                        <ElSelect
                          v-model="dateDiffUnit"
                          :placeholder="$t('form-design.attribute.dateDiffUnit')"
                          size="small"
                          class="w-full"
                        >
                          <ElOption label="days" value="days" />
                          <ElOption label="hours" value="hours" />
                          <ElOption label="minutes" value="minutes" />
                        </ElSelect>
                        <ElButton
                          size="small"
                          type="primary"
                          plain
                          :disabled="!dateDiffEndField || !dateDiffStartField"
                          @click="insertDateDiffFormula(dateDiffEndField, dateDiffStartField, dateDiffUnit)"
                        >
                          {{ $t('form-design.attribute.insertDateDiff') }}
                        </ElButton>
                      </div>
                    </div>
                    <ElFormItem :label="$t('form-design.attribute.precision')">
                      <ElInputNumber
                        v-model="activeItem.props.formulaPrecision"
                        :min="0"
                        :max="10"
                        controls-position="right"
                      />
                    </ElFormItem>
                  </template>
                </div>
              </template>

              <!-- 富文本特有属性 -->
              <template v-if="activeItem.type === 'rich-text'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('richText')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.richTextProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('richText')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('richText')">
                  <ElFormItem :label="$t('form-design.attribute.minHeight')">
                    <ElInputNumber
                      v-model="activeItem.props.minHeight"
                      :min="100"
                      :max="800"
                      :step="50"
                      controls-position="right"
                      class="w-full"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.maxHeight')">
                    <ElInputNumber
                      v-model="activeItem.props.maxHeight"
                      :min="200"
                      :max="1200"
                      :step="50"
                      controls-position="right"
                      class="w-full"
                    />
                  </ElFormItem>
                  <template v-if="activeItem.props.toolbarConfig?.insert">
                    <div
                      class="mt-3 border-t border-[var(--el-border-color-lighter)] pt-3"
                    >
                      <div
                        class="mb-2 text-xs text-[var(--el-text-color-secondary)]"
                      >
                        {{ $t('form-design.attribute.toolbar') }}
                      </div>
                      <ElFormItem :label="$t('form-design.attribute.url')">
                        <ElSwitch
                          v-model="activeItem.props.toolbarConfig.insert.link"
                        />
                      </ElFormItem>
                      <ElFormItem :label="$t('form-design.material.components.image')">
                        <ElSwitch
                          v-model="activeItem.props.toolbarConfig.insert.image"
                        />
                      </ElFormItem>
                      <ElFormItem :label="$t('common.table')">
                        <ElSwitch
                          v-model="activeItem.props.toolbarConfig.insert.table"
                        />
                      </ElFormItem>
                      <ElFormItem :label="$t('form-design.material.components.file')">
                        <ElSwitch
                          v-model="
                            activeItem.props.toolbarConfig.insert.attachment
                          "
                        />
                      </ElFormItem>
                      <ElFormItem :label="$t('common.video')">
                        <ElSwitch
                          v-model="activeItem.props.toolbarConfig.insert.video"
                        />
                      </ElFormItem>
                    </div>
                  </template>
                </div>
              </template>

              <!-- Select 特有属性 -->
              <template v-if="activeItem.type === 'select'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('select')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.selectProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('select')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('select')">
                  <ElFormItem :label="$t('form-design.attribute.filterable')">
                    <ElSwitch v-model="activeItem.props.filterable" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.multiple')">
                    <ElSwitch v-model="activeItem.props.multiple" />
                  </ElFormItem>
                  <ElFormItem
                    :label="$t('form-design.attribute.collapseTags')"
                    v-if="activeItem.props.multiple"
                  >
                    <ElSwitch v-model="activeItem.props.collapseTags" />
                  </ElFormItem>
                </div>
              </template>
              <!-- 选项配置 (针对 Select/Radio/Checkbox/Cascader/TreeSelect/TableSelector) -->
              <div
                v-if="
                  [
                    'select',
                    'radio',
                    'checkbox',
                    'cascader',
                    'tree-select',
                    'table-selector',
                  ].includes(activeItem.type)
                "
                class="mt-4"
              >
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('options')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.dataConfig') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('options')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>

                <div v-show="activeSections.includes('options')">
                  <!-- 数据来源类型选择 - 单选按钮 -->
                  <ElFormItem label="">
                    <ElRadioGroup
                      :model-value="currentDataSourceType"
                      @change="handleDataSourceTypeChange"
                      class="flex flex-wrap"
                    >
                      <ElRadioButton
                        v-for="opt in DATA_SOURCE_OPTIONS"
                        :key="opt.value"
                        :value="opt.value"
                      >
                        {{ opt.label }}
                      </ElRadioButton>
                    </ElRadioGroup>
                  </ElFormItem>

                  <!-- 静态数据配置 -->
                  <template v-if="currentDataSourceType === 'static'">
                    <div class="mb-2 flex items-center justify-between">
                      <span class="text-xs">{{ $t('form-design.attribute.optionsList') }}</span>
                      <ElButton
                        type="primary"
                        link
                        size="small"
                        @click="addOption"
                        v-if="
                          ['select', 'radio', 'checkbox', 'table-selector'].includes(
                            activeItem.type,
                          )
                        "
                      >
                        {{ $t('form-design.attribute.addOption') }}
                      </ElButton>
                    </div>

                    <!-- 简单列表编辑 (Select/Radio/Checkbox/TableSelector) -->
                    <draggable
                      v-if="
                        ['select', 'radio', 'checkbox', 'table-selector'].includes(
                          activeItem.type,
                        )
                      "
                      v-model="activeItem.options"
                      item-key="value"
                      handle=".handle"
                      :animation="200"
                    >
                      <template #item="{ element, index }">
                        <div class="mb-2 flex items-center gap-2">
                          <ElIcon
                            class="handle w-4 cursor-move text-[var(--el-text-color-secondary)]"
                          >
                            <Rank />
                          </ElIcon>
                          <ElInput
                            v-model="element.label"
                            placeholder="Label"
                            size="small"
                          />
                          <ElInput
                            v-model="element.value"
                            placeholder="Value"
                            size="small"
                          />
                          <ElButton
                            type="danger"
                            link
                            size="small"
                            @click="removeOption(index)"
                          >
                            <ElIcon class="w-4"><Delete /></ElIcon>
                          </ElButton>
                        </div>
                      </template>
                    </draggable>

                    <!-- 复杂树形编辑 (Cascader/TreeSelect) -->
                    <div v-else class="flex flex-col gap-2">
                      <div
                        class="mb-2 text-xs text-[var(--el-text-color-secondary)]"
                      >
                        {{ $t('form-design.attribute.selectNodeTip') }}
                      </div>
                      <ElButton
                        type="primary"
                        plain
                        class="w-full"
                        @click="showOptionsEditor = true"
                      >
                        <ElIcon class="mr-1 h-4 w-4"><Edit /></ElIcon>
                        {{ $t('form-design.attribute.dataSource') }}
                      </ElButton>
                    </div>
                  </template>

                  <!-- 字典数据配置 -->
                  <template v-else-if="currentDataSourceType === 'dict'">
                    <ElFormItem :label="$t('form-design.attribute.dictData')">
                      <ElSelect
                        v-model="activeItem.dataSource!.dictCode"
                        :placeholder="$t('form-design.attribute.dictData')"
                        filterable
                        :loading="loadingDict"
                        class="w-full"
                        @focus="loadDictList"
                      >
                        <ElOption
                          v-for="dict in dictList"
                          :key="dict.code"
                          :label="dict.name"
                          :value="dict.code"
                        >
                          <div class="flex w-full items-center justify-between">
                            <span>{{ dict.name }}</span>
                            <span
                              class="ml-2 text-xs text-[var(--el-text-color-secondary)]"
                              >{{ dict.code }}</span
                            >
                          </div>
                        </ElOption>
                      </ElSelect>
                    </ElFormItem>
                  </template>

                  <!-- 数据源配置 -->
                  <template v-else-if="currentDataSourceType === 'dataSource'">
                    <ElFormItem :label="$t('form-design.attribute.dataSource')">
                      <ElSelect
                        v-model="activeItem.dataSource!.dataSourceCode"
                        :placeholder="$t('form-design.attribute.dataSource')"
                        filterable
                        :loading="loadingDataSource"
                        class="w-full"
                        @focus="loadDataSourceList"
                      >
                        <ElOption
                          v-for="ds in dataSourceList"
                          :key="ds.code"
                          :label="ds.name"
                          :value="ds.code"
                        >
                          <div class="flex w-full items-center justify-between">
                            <span>{{ ds.name }}</span>
                            <div class="ml-2 flex items-center gap-1">
                              <ElTag
                                v-if="ds.result_type"
                                size="small"
                                type="primary"
                              >
                                {{ getResultTypeLabel(ds.result_type) }}
                              </ElTag>
                              <span
                                class="text-xs text-[var(--el-text-color-secondary)]"
                                >{{ ds.code }}</span
                              >
                            </div>
                          </div>
                        </ElOption>
                      </ElSelect>
                    </ElFormItem>
                    <!-- 对象转选项配置 -->
                    <ElFormItem :label="$t('form-design.attribute.objectToOptions')">
                      <ElSwitch
                        v-model="activeItem.dataSource!.objectToOptions"
                        size="small"
                      />
                    </ElFormItem>
                    <div
                      v-if="activeItem.dataSource?.objectToOptions"
                      class="mb-2 rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
                    >
                      {{ $t('form-design.attribute.objectToOptionsTip') }}
                    </div>
                    <ElFormItem
                      v-if="activeItem.dataSource?.objectToOptions"
                      :label="$t('form-design.attribute.objectExcludeFields')"
                    >
                      <ElSelect
                        v-model="activeItem.dataSource!.objectExcludeFields"
                        multiple
                        filterable
                        allow-create
                        default-first-option
                        size="small"
                        class="w-full"
                        :placeholder="$t('form-design.attribute.objectExcludeFieldsPlaceholder')"
                      />
                    </ElFormItem>
                    <ElFormItem
                      v-if="activeItem.dataSource?.objectToOptions"
                      :label="$t('form-design.attribute.objectLabelMaxLength')"
                    >
                      <ElInputNumber
                        v-model="activeItem.dataSource!.objectLabelMaxLength"
                        :min="0"
                        :max="500"
                        :placeholder="$t('form-design.attribute.objectLabelMaxLengthPlaceholder')"
                        size="small"
                        class="w-full"
                        controls-position="right"
                      />
                    </ElFormItem>
                    <!-- 字段映射配置（对象转选项模式下隐藏） -->
                    <template v-if="!activeItem.dataSource?.objectToOptions">
                      <div
                        class="mb-2 border-t border-[var(--el-border-color)] pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                      >
                        {{ $t('form-design.attribute.mapping') }}
                      </div>
                      <ElFormItem :label="$t('form-design.attribute.formLabelField')">
                        <ElInput
                          v-model="activeItem.dataSource!.labelField"
                          placeholder="label"
                          size="small"
                        />
                      </ElFormItem>
                      <ElFormItem :label="$t('form-design.attribute.formValueField')">
                        <ElInput
                          v-model="activeItem.dataSource!.valueField"
                          placeholder="value"
                          size="small"
                        />
                      </ElFormItem>
                      <ElFormItem
                        v-if="activeItem.type !== 'table-selector'"
                        :label="$t('form-design.attribute.formDescField')"
                      >
                        <ElInput
                          v-model="activeItem.dataSource!.descField"
                          :placeholder="$t('form-design.attribute.selectDescField')"
                          size="small"
                          clearable
                        />
                      </ElFormItem>
                      <ElFormItem
                        v-if="
                          ['cascader', 'tree-select'].includes(activeItem.type)
                        "
                        :label="$t('form-design.attribute.nodeProps')"
                      >
                        <ElInput
                          v-model="activeItem.dataSource!.childrenField"
                          placeholder="children"
                          size="small"
                        />
                      </ElFormItem>
                      <div
                        class="rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
                      >
                        <p>{{ $t('form-design.attribute.mappingTip') }}</p>
                      </div>
                    </template>

                    <!-- 数据源参数配置 -->
                    <template v-if="activeItem.dataSource?.dataSourceParams?.length">
                      <div
                        class="mb-2 mt-3 border-t border-[var(--el-border-color)] pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                      >
                        {{ $t('form-design.attribute.paramConfig') }}
                      </div>
                      <div
                        v-for="(param, index) in activeItem.dataSource.dataSourceParams"
                        :key="param.name"
                        class="mb-3 rounded border border-[var(--el-border-color)] p-2"
                      >
                        <div class="mb-2 flex items-center justify-between">
                          <span class="text-sm font-medium">
                            {{ param.name }}
                            <span v-if="param.label && param.label !== param.name" class="text-xs text-[var(--el-text-color-secondary)]">({{ param.label }})</span>
                            <span v-if="param.required" class="text-[var(--el-color-danger)]">*</span>
                          </span>
                          <ElTag size="small" type="info">{{ param.type || 'string' }}</ElTag>
                        </div>
                        <div v-if="param.default !== undefined && param.default !== ''" class="mb-2 text-xs text-[var(--el-text-color-secondary)]">
                          {{ $t('form-design.attribute.defaultValue') }}: {{ param.default }}
                        </div>
                        <ElFormItem :label="$t('form-design.attribute.paramValueSource')" class="mb-2">
                          <ElSelect
                            v-model="param.valueSource"
                            size="small"
                            class="w-full"
                          >
                            <ElOption
                              v-for="opt in PARAM_VALUE_SOURCE_OPTIONS"
                              :key="opt.value"
                              :label="opt.label"
                              :value="opt.value"
                            />
                          </ElSelect>
                        </ElFormItem>
                        <!-- 固定值 -->
                        <ElFormItem
                          v-show="param.valueSource === 'fixed'"
                          :label="$t('form-design.attribute.paramFixedValue')"
                        >
                          <ElInput
                            v-model="param.fixedValue"
                            size="small"
                            :placeholder="param.default !== undefined ? String(param.default) : ''"
                          />
                        </ElFormItem>
                        <!-- 表单字段 -->
                        <ElFormItem
                          v-show="param.valueSource === 'field'"
                          :label="$t('form-design.attribute.paramSourceField')"
                        >
                          <ElSelect
                            v-model="param.sourceField"
                            size="small"
                            filterable
                            clearable
                            class="w-full"
                            :placeholder="$t('form-design.attribute.selectField')"
                          >
                            <ElOption
                              v-for="field in allFormFields"
                              :key="field.field"
                              :label="`${field.label} (${field.field})`"
                              :value="field.field"
                            />
                          </ElSelect>
                        </ElFormItem>
                        <!-- 搜索输入 -->
                        <div
                          v-show="param.valueSource === 'search'"
                          class="rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
                        >
                          {{ $t('form-design.attribute.paramSearchTip') }}
                        </div>
                      </div>
                    </template>
                    <div
                      v-else-if="loadingDataSourceDetail"
                      class="mt-2 text-center text-xs text-[var(--el-text-color-secondary)]"
                    >
                      {{ $t('common.loading') }}
                    </div>
                  </template>

                  <!-- 表单数据配置 -->
                  <template v-else-if="currentDataSourceType === 'formData'">
                    <ElFormItem :label="$t('form-design.attribute.formData')">
                      <ElSelect
                        v-model="activeItem.dataSource!.formCode"
                        :placeholder="$t('form-design.attribute.selectForm')"
                        filterable
                        :loading="loadingPublishedForms"
                        class="w-full"
                        @focus="loadPublishedFormList"
                      >
                        <ElOption
                          v-for="form in publishedFormList"
                          :key="form.code"
                          :label="form.name"
                          :value="form.code"
                        >
                          <div class="flex w-full items-center justify-between">
                            <span>{{ form.name }}</span>
                            <span
                              class="ml-2 text-xs text-[var(--el-text-color-secondary)]"
                            >{{ form.code }}</span>
                          </div>
                        </ElOption>
                      </ElSelect>
                    </ElFormItem>
                    <template v-if="activeItem.dataSource?.formCode">
                      <div
                        class="mb-2 border-t border-[var(--el-border-color)] pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                      >
                        {{ $t('form-design.attribute.mapping') }}
                      </div>
                      <ElFormItem :label="$t('form-design.attribute.formLabelField')">
                        <ElSelect
                          v-model="activeItem.dataSource!.formLabelField"
                          :placeholder="$t('form-design.attribute.selectLabelField')"
                          filterable
                          class="w-full"
                        >
                          <ElOption
                            v-for="field in selectedFormFields"
                            :key="field.field"
                            :label="`${field.label} (${field.field})`"
                            :value="field.field"
                          />
                        </ElSelect>
                      </ElFormItem>
                      <ElFormItem :label="$t('form-design.attribute.formValueField')">
                        <ElSelect
                          v-model="activeItem.dataSource!.formValueField"
                          :placeholder="$t('form-design.attribute.selectValueField')"
                          filterable
                          class="w-full"
                        >
                          <ElOption
                            v-for="field in selectedFormFields"
                            :key="field.field"
                            :label="`${field.label} (${field.field})`"
                            :value="field.field"
                          />
                        </ElSelect>
                      </ElFormItem>
                      <ElFormItem
                        v-if="activeItem.type !== 'table-selector'"
                        :label="$t('form-design.attribute.formDescField')"
                      >
                        <ElSelect
                          v-model="activeItem.dataSource!.formDescField"
                          :placeholder="$t('form-design.attribute.selectDescField')"
                          filterable
                          clearable
                          class="w-full"
                        >
                          <ElOption
                            v-for="field in selectedFormFields"
                            :key="field.field"
                            :label="`${field.label} (${field.field})`"
                            :value="field.field"
                          />
                        </ElSelect>
                      </ElFormItem>
                      <!-- 级联/树形选择 树形数据配置 -->
                      <template v-if="['cascader', 'tree-select'].includes(activeItem.type)">
                        <div
                          class="mb-2 border-t border-[var(--el-border-color)] pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                        >
                          {{ $t('form-design.attribute.cascaderTreeConfig') }}
                        </div>
                        <ElFormItem :label="$t('form-design.attribute.formParentField')">
                          <ElSelect
                            v-model="activeItem.dataSource!.formParentField"
                            :placeholder="'parent_id'"
                            filterable
                            clearable
                            class="w-full"
                          >
                            <ElOption
                              v-for="field in selectedFormFields"
                              :key="field.field"
                              :label="`${field.label} (${field.field})`"
                              :value="field.field"
                            />
                          </ElSelect>
                        </ElFormItem>
                        <div class="flex gap-2">
                          <ElFormItem :label="$t('form-design.attribute.formLazyLoad')" class="flex-1">
                            <ElSwitch
                              v-model="activeItem.dataSource!.formLazyLoad"
                              size="small"
                              :checked-value="true"
                              :unchecked-value="false"
                            />
                          </ElFormItem>
                        </div>
                        <div
                          class="mb-2 rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
                        >
                          {{ $t('form-design.attribute.formCascaderTip') }}
                        </div>
                      </template>
                      <!-- 分页和搜索配置（级联/树形选择不显示搜索，懒加载时无法后端搜索，全量时用前端 filterable） -->
                      <div class="flex gap-2">
                        <ElFormItem :label="$t('form-design.attribute.formPageSize')" class="flex-1">
                          <ElInputNumber
                            v-model="activeItem.dataSource!.formPageSize"
                            :min="10"
                            :max="1000"
                            :step="10"
                            size="small"
                            class="w-full"
                            :placeholder="'100'"
                          />
                        </ElFormItem>
                        <ElFormItem v-if="!['cascader', 'tree-select'].includes(activeItem.type)" :label="$t('form-design.attribute.formEnableSearch')" class="flex-1">
                          <ElSwitch
                            v-model="activeItem.dataSource!.formEnableSearch"
                            size="small"
                          />
                        </ElFormItem>
                      </div>
                      <div
                        v-if="!['cascader', 'tree-select'].includes(activeItem.type) && activeItem.dataSource?.formEnableSearch"
                        class="mb-2 rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
                      >
                        {{ $t('form-design.attribute.formSearchTip') }}
                      </div>
                      <!-- 过滤条件配置 -->
                      <div
                        class="mb-2 mt-3 pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                      >
                        {{ $t('form-design.attribute.formDataFilters') }}
                      </div>
                      <div class="mb-2 flex items-center justify-between">
                        <span class="text-xs text-[var(--el-text-color-secondary)]">
                          {{ $t('form-design.attribute.formDataFiltersTip') }}
                        </span>
                        <ElButton
                          type="primary"
                          link
                          size="small"
                          @click="addFormDataFilter"
                        >
                          {{ $t('form-design.attribute.addFilter') }}
                        </ElButton>
                      </div>
                      <div
                        v-for="(filter, filterIndex) in (activeItem.dataSource?.formFilters || []) as FormDataFilter[]"
                        :key="filterIndex"
                        class="mb-2 rounded border border-[var(--el-border-color)] p-2"
                      >
                        <div class="mb-2 flex items-center justify-between">
                          <span class="text-xs text-[var(--el-text-color-secondary)]">
                            {{ $t('form-design.attribute.filterCondition') }} {{ Number(filterIndex) + 1 }}
                          </span>
                          <ElButton
                            type="danger"
                            link
                            size="small"
                            :icon="Delete"
                            @click="removeFormDataFilter(Number(filterIndex))"
                          />
                        </div>
                        <ElFormItem :label="$t('form-design.attribute.filterSourceField')" class="mb-2">
                          <ElSelect
                            v-model="filter.sourceField"
                            :placeholder="$t('form-design.attribute.selectSourceField')"
                            filterable
                            class="w-full"
                            size="small"
                          >
                            <ElOption
                              v-for="field in dependableFields"
                              :key="field.value"
                              :label="field.label"
                              :value="field.value"
                            />
                          </ElSelect>
                        </ElFormItem>
                        <ElFormItem :label="$t('form-design.attribute.filterTargetField')" class="mb-2">
                          <ElSelect
                            v-model="filter.targetField"
                            :placeholder="$t('form-design.attribute.selectTargetField')"
                            filterable
                            class="w-full"
                            size="small"
                          >
                            <ElOption
                              v-for="field in selectedFormFields"
                              :key="field.field"
                              :label="`${field.label} (${field.field})`"
                              :value="field.field"
                            />
                          </ElSelect>
                        </ElFormItem>
                        <ElFormItem :label="$t('form-design.attribute.filterType')">
                          <ElSelect
                            v-model="filter.filterType"
                            class="w-full"
                            size="small"
                          >
                            <ElOption :label="$t('form-design.attribute.conditionBuilder.operators.equals')" value="eq" />
                            <ElOption :label="$t('form-design.attribute.conditionBuilder.operators.notEquals')" value="ne" />
                            <ElOption :label="$t('form-design.attribute.conditionBuilder.operators.greaterThan')" value="gt" />
                            <ElOption :label="$t('form-design.attribute.conditionBuilder.operators.greaterThanOrEqual')" value="gte" />
                            <ElOption :label="$t('form-design.attribute.conditionBuilder.operators.lessThan')" value="lt" />
                            <ElOption :label="$t('form-design.attribute.conditionBuilder.operators.lessThanOrEqual')" value="lte" />
                            <ElOption :label="$t('form-design.attribute.conditionBuilder.operators.contains')" value="like" />
                            <ElOption label="IN" value="in" />
                            <ElOption :label="$t('form-design.attribute.conditionBuilder.operators.isEmpty')" value="null" />
                            <ElOption :label="$t('form-design.attribute.conditionBuilder.operators.isNotEmpty')" value="not_null" />
                          </ElSelect>
                        </ElFormItem>
                      </div>
                      <div
                        class="rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
                      >
                        <p>{{ $t('form-design.attribute.formDataTip') }}</p>
                      </div>
                    </template>
                  </template>

                  <!-- API接口配置 -->
                  <template v-else-if="currentDataSourceType === 'api'">
                    <ElFormItem :label="$t('form-design.attribute.apiUrl')">
                      <ElInput
                        v-model="activeItem.dataSource!.apiUrl"
                        placeholder="/api/xxx/list"
                      />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.apiMethod')">
                      <ElRadioGroup v-model="activeItem.dataSource!.apiMethod">
                        <ElRadioButton label="GET">GET</ElRadioButton>
                        <ElRadioButton label="POST">POST</ElRadioButton>
                      </ElRadioGroup>
                    </ElFormItem>
                    <div
                      class="mb-2 border-t border-[var(--el-border-color)] pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                    >
                      {{ $t('form-design.attribute.mapping') }}
                    </div>
                    <div class="flex gap-2">
                      <ElFormItem :label="$t('form-design.attribute.sourceField')" class="flex-1">
                        <ElInput
                          v-model="activeItem.dataSource!.labelField"
                          placeholder="label"
                          size="small"
                        />
                      </ElFormItem>
                      <ElFormItem :label="$t('form-design.attribute.targetField')" class="flex-1">
                        <ElInput
                          v-model="activeItem.dataSource!.valueField"
                          placeholder="value"
                          size="small"
                        />
                      </ElFormItem>
                    </div>
                    <ElFormItem
                      v-if="
                        ['cascader', 'tree-select'].includes(activeItem.type)
                      "
                      :label="$t('form-design.attribute.nodeProps')"
                    >
                      <ElInput
                        v-model="activeItem.dataSource!.childrenField"
                        placeholder="children"
                        size="small"
                      />
                    </ElFormItem>
                    <div
                      class="rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
                    >
                      <p>{{ $t('form-design.attribute.apiTip') }}</p>
                      <code class="mt-1 block"
                        >[{ "label": "Option 1", "value": 1 }, ...]</code
                      >
                    </div>
                  </template>

                  <!-- 依赖字段配置 -->
                  <template v-else-if="currentDataSourceType === 'dependent'">
                    <ElFormItem :label="$t('form-design.attribute.dependField')">
                      <ElSelect
                        v-model="activeItem.dataSource!.dependField"
                        :placeholder="$t('form-design.attribute.dependField')"
                        class="w-full"
                      >
                        <ElOption
                          v-for="field in dependableFields"
                          :key="field.value"
                          :label="field.label"
                          :value="field.value"
                        />
                      </ElSelect>
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.apiUrl')">
                      <ElInput
                        v-model="activeItem.dataSource!.apiUrl"
                        placeholder="/api/xxx/list"
                      />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.paramName')">
                      <ElInput
                        v-model="activeItem.dataSource!.dependParamName"
                        :placeholder="$t('form-design.attribute.paramNamePlaceholder')"
                      />
                    </ElFormItem>
                    <div
                      class="mb-2 border-t border-[var(--el-border-color)] pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                    >
                      {{ $t('form-design.attribute.mapping') }}
                    </div>
                    <div class="flex gap-2">
                      <ElFormItem :label="$t('form-design.attribute.sourceField')" class="flex-1">
                        <ElInput
                          v-model="activeItem.dataSource!.labelField"
                          placeholder="label"
                          size="small"
                        />
                      </ElFormItem>
                      <ElFormItem :label="$t('form-design.attribute.targetField')" class="flex-1">
                        <ElInput
                          v-model="activeItem.dataSource!.valueField"
                          placeholder="value"
                          size="small"
                        />
                      </ElFormItem>
                    </div>
                    <div
                      class="rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
                    >
                      <p>
                        {{ $t('form-design.attribute.dependTip1') }}
                      </p>
                      <p>{{ $t('form-design.attribute.dependTip2') }}</p>
                    </div>
                  </template>
                </div>
              </div>
              <!-- Radio / Checkbox 特有属性 -->
              <template v-if="['radio', 'checkbox'].includes(activeItem.type)">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('option-style')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.optionStyle') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('option-style')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('option-style')">
                  <ElFormItem v-if="activeItem.type === 'radio'" :label="$t('form-design.attribute.buttonStyle')">
                    <ElSwitch v-model="activeItem.props.buttonStyle" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.showBorder')" v-if="!activeItem.props.buttonStyle">
                    <ElSwitch v-model="activeItem.props.border" />
                  </ElFormItem>
                </div>
              </template>

              <!-- Date 特有属性 -->
              <template v-if="activeItem.type === 'date'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('date')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.dateProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('date')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('date')">
                  <ElFormItem :label="$t('form-design.attribute.displayType')">
                    <ElSelect v-model="activeItem.props.type" @change="handleDateTypeChange">
                      <ElOption :label="$t('form-design.material.components.date') + ' (date)'" value="date" />
                      <ElOption :label="$t('form-design.attribute.week') + ' (week)'" value="week" />
                      <ElOption :label="$t('form-design.attribute.month') + ' (month)'" value="month" />
                      <ElOption :label="$t('form-design.attribute.year') + ' (year)'" value="year" />
                      <ElOption :label="$t('form-design.attribute.datetime') + ' (datetime)'" value="datetime" />
                      <ElOption
                        :label="$t('form-design.attribute.dateRange') + ' (daterange)'"
                        value="daterange"
                      />
                      <ElOption
                        :label="$t('form-design.attribute.datetimeRange') + ' (datetimerange)'"
                        value="datetimerange"
                      />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.displayFormat')">
                    <ElInput v-model="activeItem.props.format" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.valueFormat')">
                    <ElInput v-model="activeItem.props.valueFormat" />
                  </ElFormItem>
                  <template v-if="activeItem.props.type?.includes('range')">
                    <ElFormItem :label="$t('form-design.attribute.separator')">
                      <ElInput v-model="activeItem.props.rangeSeparator" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.startPlaceholder')">
                      <ElInput v-model="activeItem.props.startPlaceholder" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.endPlaceholder')">
                      <ElInput v-model="activeItem.props.endPlaceholder" />
                    </ElFormItem>
                  </template>
                  <ElFormItem :label="$t('form-design.attribute.editable')">
                    <ElSwitch v-model="activeItem.props.editable" />
                  </ElFormItem>
                  <template v-if="!activeItem.props.type?.includes('range')">
                    <ElFormItem :label="$t('form-design.attribute.dateLinkedField')">
                      <ElSelect
                        v-model="activeItem.props.dateLinkedField"
                        :placeholder="$t('ui.placeholder.select')"
                        clearable
                      >
                        <ElOption
                          v-for="f in dateLinkedFields"
                          :key="f.field"
                          :label="`${f.label} (${f.field})`"
                          :value="f.field"
                        />
                      </ElSelect>
                    </ElFormItem>
                    <ElFormItem
                      v-if="activeItem.props.dateLinkedField"
                      :label="$t('form-design.attribute.dateLinkedRule')"
                    >
                      <ElSelect v-model="activeItem.props.dateLinkedRule">
                        <ElOption
                          :label="$t('form-design.attribute.dateLinkRule.lt')"
                          value="lt"
                        />
                        <ElOption
                          :label="$t('form-design.attribute.dateLinkRule.lte')"
                          value="lte"
                        />
                        <ElOption
                          :label="$t('form-design.attribute.dateLinkRule.gt')"
                          value="gt"
                        />
                        <ElOption
                          :label="$t('form-design.attribute.dateLinkRule.gte')"
                          value="gte"
                        />
                      </ElSelect>
                    </ElFormItem>
                  </template>
                </div>
              </template>

              <!-- Time 特有属性 -->
              <template v-if="activeItem.type === 'time'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('time')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.timeProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('time')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('time')">
                  <ElFormItem :label="$t('form-design.attribute.displayFormat')">
                    <ElInput v-model="activeItem.props.format" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.valueFormat')">
                    <ElInput v-model="activeItem.props.valueFormat" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.arrowControl')">
                    <ElSwitch v-model="activeItem.props.arrowControl" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 数字/滑块相关属性 -->
              <template
                v-if="['input-number', 'slider'].includes(activeItem.type)"
              >
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-gray-500 hover:text-blue-500"
                  @click="toggleSection('number')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.textProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('number')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('number')">
                  <div class="mb-2 flex gap-2">
                    <ElFormItem :label="$t('form-design.attribute.min')" class="flex-1">
                      <ElInputNumber
                        v-model="activeItem.props.min"
                        controls-position="right"
                        class="w-full"
                      />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.max')" class="flex-1">
                      <ElInputNumber
                        v-model="activeItem.props.max"
                        controls-position="right"
                        class="w-full"
                      />
                    </ElFormItem>
                  </div>
                  <ElFormItem :label="$t('form-design.attribute.step')">
                    <ElInputNumber
                      v-model="activeItem.props.step"
                      :min="0"
                      controls-position="right"
                    />
                  </ElFormItem>

                  <template v-if="activeItem.type === 'input-number'">
                    <ElFormItem :label="$t('form-design.attribute.precision')">
                      <ElInputNumber
                        v-model="activeItem.props.precision"
                        :min="0"
                        controls-position="right"
                      />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.controls')">
                      <ElSwitch v-model="activeItem.props.controls" />
                    </ElFormItem>
                    <ElFormItem
                      :label="$t('form-design.attribute.controlsPosition')"
                      v-if="activeItem.props.controls"
                    >
                      <ElRadioGroup v-model="activeItem.props.controlsPosition">
                        <ElRadioButton label="">{{ $t('form-design.attribute.default') }}</ElRadioButton>
                        <ElRadioButton label="right">{{ $t('form-design.attribute.location.right') }}</ElRadioButton>
                      </ElRadioGroup>
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.readonly')">
                      <ElSwitch v-model="activeItem.props.readonly" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.showAddon')">
                      <ElSwitch v-model="activeItem.props.showAddon" />
                    </ElFormItem>
                    <template v-if="activeItem.props.showAddon">
                      <ElFormItem :label="$t('form-design.attribute.addonBefore')">
                        <ElInput
                          v-model="activeItem.props.addonBefore"
                          :placeholder="$t('form-design.attribute.addonPlaceholder')"
                          clearable
                        />
                      </ElFormItem>
                      <ElFormItem :label="$t('form-design.attribute.addonAfter')">
                        <ElInput
                          v-model="activeItem.props.addonAfter"
                          :placeholder="$t('form-design.attribute.addonPlaceholder')"
                          clearable
                        />
                      </ElFormItem>
                    </template>
                  </template>

                  <template v-if="activeItem.type === 'slider'">
                    <ElFormItem :label="$t('form-design.attribute.showInput')">
                      <ElSwitch v-model="activeItem.props.showInput" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.showStops')">
                      <ElSwitch v-model="activeItem.props.showStops" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.range')">
                      <ElSwitch v-model="activeItem.props.range" />
                    </ElFormItem>
                  </template>
                </div>
              </template>

              <!-- 开关相关属性 -->
              <template v-if="activeItem.type === 'switch'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('switch')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.switchProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('switch')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('switch')">
                  <ElFormItem :label="$t('form-design.attribute.width')">
                    <ElInputNumber
                      v-model="activeItem.props.width"
                      controls-position="right"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.inlinePrompt')">
                    <ElSwitch v-model="activeItem.props.inlinePrompt" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.activeText')">
                    <ElInput v-model="activeItem.props.activeText" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.inactiveText')">
                    <ElInput v-model="activeItem.props.inactiveText" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 编码生成属性 -->
              <template v-if="activeItem.type === 'code-generator'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('codeGenerator')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.codeGenerator.props') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('codeGenerator')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('codeGenerator')">
                  <ElFormItem :label="$t('form-design.attribute.codeGenerator.prefix')">
                    <ElInput
                      v-model="activeItem.props.prefix"
                      :placeholder="$t('form-design.attribute.codeGenerator.prefixPlaceholder')"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.codeGenerator.separator')">
                    <ElInput
                      v-model="activeItem.props.separator"
                      :placeholder="$t('form-design.attribute.codeGenerator.separatorPlaceholder')"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.codeGenerator.generateMode')">
                    <ElSelect v-model="activeItem.props.generateMode" class="w-full">
                      <ElOption value="date_seq" :label="$t('form-design.attribute.codeGenerator.modes.date_seq')" />
                      <ElOption value="datetime" :label="$t('form-design.attribute.codeGenerator.modes.datetime')" />
                      <ElOption value="random" :label="$t('form-design.attribute.codeGenerator.modes.random')" />
                      <ElOption value="uuid" :label="$t('form-design.attribute.codeGenerator.modes.uuid')" />
                      <ElOption value="snowflake" :label="$t('form-design.attribute.codeGenerator.modes.snowflake')" />
                    </ElSelect>
                  </ElFormItem>
                  <template v-if="activeItem.props.generateMode === 'date_seq' || activeItem.props.generateMode === 'datetime'">
                    <ElFormItem :label="$t('form-design.attribute.codeGenerator.dateFormat')">
                      <ElSelect v-model="activeItem.props.dateFormat" class="w-full">
                        <ElOption value="YYYYMMDD" :label="$t('form-design.attribute.codeGenerator.dateFormats.YYYYMMDD')" />
                        <ElOption value="YYMMDD" :label="$t('form-design.attribute.codeGenerator.dateFormats.YYMMDD')" />
                        <ElOption value="YYYYMM" :label="$t('form-design.attribute.codeGenerator.dateFormats.YYYYMM')" />
                        <ElOption value="YYMM" :label="$t('form-design.attribute.codeGenerator.dateFormats.YYMM')" />
                      </ElSelect>
                    </ElFormItem>
                  </template>
                  <template v-if="activeItem.props.generateMode === 'date_seq'">
                    <ElFormItem :label="$t('form-design.attribute.codeGenerator.seqLength')">
                      <ElInputNumber
                        v-model="activeItem.props.seqLength"
                        :min="1"
                        :max="10"
                        controls-position="right"
                      />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.codeGenerator.seqResetRule')">
                      <ElSelect v-model="activeItem.props.seqResetRule" class="w-full">
                        <ElOption value="daily" :label="$t('form-design.attribute.codeGenerator.resetRules.daily')" />
                        <ElOption value="monthly" :label="$t('form-design.attribute.codeGenerator.resetRules.monthly')" />
                        <ElOption value="yearly" :label="$t('form-design.attribute.codeGenerator.resetRules.yearly')" />
                        <ElOption value="never" :label="$t('form-design.attribute.codeGenerator.resetRules.never')" />
                      </ElSelect>
                    </ElFormItem>
                  </template>
                  <template v-if="activeItem.props.generateMode === 'random'">
                    <ElFormItem :label="$t('form-design.attribute.codeGenerator.randomLength')">
                      <ElInputNumber
                        v-model="activeItem.props.randomLength"
                        :min="4"
                        :max="20"
                        controls-position="right"
                      />
                    </ElFormItem>
                  </template>
                  <ElFormItem :label="$t('form-design.attribute.codeGenerator.businessType')">
                    <ElInput
                      v-model="activeItem.props.businessType"
                      :placeholder="$t('form-design.attribute.codeGenerator.businessTypePlaceholder')"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.codeGenerator.generateOnMount')">
                    <ElSwitch v-model="activeItem.props.generateOnMount" />
                    <span class="ml-2 text-xs text-[var(--el-text-color-secondary)]">
                      {{ $t('form-design.attribute.codeGenerator.generateOnMountTip') }}
                    </span>
                  </ElFormItem>
                </div>
              </template>

              <!-- 公式计算属性 -->
              <template v-if="activeItem.type === 'formula-input'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('formula')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.formulaProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('formula')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('formula')">
                  <ElFormItem :label="$t('form-design.attribute.formula')">
                    <ElInput
                      v-model="activeItem.props.formula"
                      type="textarea"
                      :rows="3"
                      :placeholder="$t('form-design.attribute.formulaPlaceholder')"
                    />
                  </ElFormItem>
                  <div class="mb-2 text-xs text-[var(--el-text-color-secondary)]">
                    {{ $t('form-design.attribute.formulaTip') }}
                  </div>
                  <!-- 可用字段列表（分组显示） -->
                  <div class="mb-2">
                    <div class="mb-1 text-xs font-medium">{{ $t('form-design.attribute.availableFields') }}</div>
                    <template v-for="group in formulaFieldGroups" :key="group.group">
                      <div class="mb-1 mt-2 text-xs text-[var(--el-text-color-secondary)]">{{ group.group }}</div>
                      <div class="flex flex-wrap gap-1">
                        <ElTag
                          v-for="field in group.fields"
                          :key="field.field"
                          size="small"
                          class="cursor-pointer"
                          @click="insertFormulaField(field.field, field.isSubTableField)"
                        >
                          {{ field.label }} ({{ field.isSubTableField ? 'SUM' : '' }}{{"{"}}{{ field.field }}{{"}"}}）
                        </ElTag>
                      </div>
                    </template>
                    <div v-if="formulaAvailableFields.length === 0 && formulaDateFields.length === 0" class="text-xs text-[var(--el-text-color-placeholder)]">
                      {{ $t('form-design.attribute.noAvailableFields') }}
                    </div>
                  </div>
                  <!-- 日期差值计算（DATEDIFF） -->
                  <div v-if="formulaDateFields.length >= 2" class="mb-2">
                    <!-- <div class="mb-1 text-xs font-medium">{{ $t('form-design.attribute.dateDiffTitle') }}</div> -->
                    <div class="mb-1 text-xs text-[var(--el-text-color-secondary)]">
                      {{ $t('form-design.attribute.dateDiffTip') }}
                    </div>
                    <div class="flex flex-col gap-2">
                      <ElSelect
                        v-model="dateDiffEndField"
                        :placeholder="$t('form-design.attribute.dateDiffEndField')"
                        size="small"
                        class="w-full"
                      >
                        <ElOption
                          v-for="field in formulaDateFields"
                          :key="field.field"
                          :label="`${field.label} (${field.field})`"
                          :value="field.field"
                        />
                      </ElSelect>
                      <ElSelect
                        v-model="dateDiffStartField"
                        :placeholder="$t('form-design.attribute.dateDiffStartField')"
                        size="small"
                        class="w-full"
                      >
                        <ElOption
                          v-for="field in formulaDateFields"
                          :key="field.field"
                          :label="`${field.label} (${field.field})`"
                          :value="field.field"
                        />
                      </ElSelect>
                      <ElSelect
                        v-model="dateDiffUnit"
                        :placeholder="$t('form-design.attribute.dateDiffUnit')"
                        size="small"
                        class="w-full"
                      >
                        <ElOption label="days" value="days" />
                        <ElOption label="hours" value="hours" />
                        <ElOption label="minutes" value="minutes" />
                      </ElSelect>
                      <ElButton
                        size="small"
                        type="primary"
                        plain
                        :disabled="!dateDiffEndField || !dateDiffStartField"
                        @click="insertDateDiffFormula(dateDiffEndField, dateDiffStartField, dateDiffUnit)"
                      >
                        {{ $t('form-design.attribute.insertDateDiff') }}
                      </ElButton>
                    </div>
                  </div>
                  <ElFormItem :label="$t('form-design.attribute.precision')">
                    <ElInputNumber
                      v-model="activeItem.props.precision"
                      :min="0"
                      :max="10"
                      controls-position="right"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.showFormula')">
                    <ElSwitch v-model="activeItem.props.showFormula" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 关联字段属性 -->
              <template v-if="activeItem.type === 'linked-field'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('linkedField')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.linkedFieldProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('linkedField')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('linkedField')">
                  <ElFormItem :label="$t('form-design.attribute.linkedSourceField')">
                    <ElSelect
                      v-model="activeItem.props.sourceField"
                      :placeholder="$t('form-design.attribute.selectSourceField')"
                      filterable
                      clearable
                      class="w-full"
                    >
                      <ElOption
                        v-for="field in linkedFieldSourceFields"
                        :key="field.field"
                        :label="`${field.label} (${field.field})`"
                        :value="field.field"
                      />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.linkedDisplayField')">
                    <ElSelect
                      v-model="activeItem.props.displayField"
                      :placeholder="$t('form-design.attribute.displayFieldPlaceholder')"
                      filterable
                      allow-create
                      clearable
                      class="w-full"
                      :disabled="!activeItem.props.sourceField"
                    >
                      <ElOption
                        v-for="field in linkedFieldDisplayFields"
                        :key="field.field"
                        :label="`${field.label} (${field.field})`"
                        :value="field.field"
                      />
                    </ElSelect>
                  </ElFormItem>
                  <div class="mb-2 text-xs text-[var(--el-text-color-secondary)]">
                    {{ $t('form-design.attribute.linkedFieldTip') }}
                  </div>
                </div>
              </template>

              <!-- 评分相关属性 -->
              <template v-if="activeItem.type === 'rate'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('rate')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.rateProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('rate')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('rate')">
                  <ElFormItem :label="$t('form-design.attribute.maxScore')">
                    <ElInputNumber
                      v-model="activeItem.props.max"
                      :min="1"
                      controls-position="right"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.allowHalf')">
                    <ElSwitch v-model="activeItem.props.allowHalf" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.showScore')">
                    <ElSwitch v-model="activeItem.props.showScore" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 颜色相关属性 -->
              <template v-if="activeItem.type === 'color'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('color')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.colorProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('color')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('color')">
                  <ElFormItem :label="$t('form-design.attribute.showAlpha')">
                    <ElSwitch v-model="activeItem.props.showAlpha" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 级联选择属性 -->
              <template v-if="activeItem.type === 'cascader'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('cascader')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.cascaderProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('cascader')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('cascader')">
                  <!-- <ElFormItem :label="$t('form-design.attribute.emitPath')">
                    <ElSwitch v-model="activeItem.props.emitPath" />
                  </ElFormItem> -->
                  <ElFormItem :label="$t('form-design.attribute.checkStrictly')">
                    <ElSwitch v-model="activeItem.props.checkStrictly" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.separator')">
                    <ElInput v-model="activeItem.props.separator" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.showAllLevels')">
                    <ElSwitch v-model="activeItem.props['show-all-levels']" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.filterable')">
                    <ElSwitch v-model="activeItem.props.filterable" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 树形选择属性 -->
              <template v-if="activeItem.type === 'tree-select'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('tree')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.treeProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('tree')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('tree')">
                  <ElFormItem :label="$t('form-design.attribute.multiple')">
                    <ElSwitch v-model="activeItem.props.multiple" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.showCheckbox')">
                    <ElSwitch v-model="activeItem.props.showCheckbox" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.checkStrictly')">
                    <ElSwitch v-model="activeItem.props.checkStrictly" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.filterable')">
                    <ElSwitch v-model="activeItem.props.filterable" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.checkOnClickNode')">
                    <ElSwitch v-model="activeItem.props.checkOnClickNode" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 部门/用户/角色/岗位选择通用属性 -->
              <template
                v-if="
                  [
                    'dept-selector',
                    'user-selector',
                    'role-selector',
                    'post-selector',
                  ].includes(activeItem.type)
                "
              >
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('selector')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.selectorProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('selector')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('selector')">
                  <ElFormItem :label="$t('form-design.attribute.multiple')">
                    <ElSwitch v-model="activeItem.props.multiple" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.filterable')">
                    <ElSwitch v-model="activeItem.props.filterable" />
                  </ElFormItem>

                  <!-- 用户选择器特有属性 -->
                  <template v-if="activeItem.type === 'user-selector'">
                    <ElFormItem :label="$t('form-design.attribute.displayMode')">
                      <ElRadioGroup v-model="activeItem.props.displayMode">
                        <ElRadioButton label="select">{{ $t('form-design.attribute.dropdown') }}</ElRadioButton>
                        <ElRadioButton label="button">{{ $t('form-design.attribute.button') }}</ElRadioButton>
                      </ElRadioGroup>
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.autoCurrentUser')">
                      <ElSwitch v-model="activeItem.props.autoCurrentUser" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.readonly')">
                      <ElSwitch v-model="activeItem.props.readonly" />
                    </ElFormItem>
                  </template>
                </div>
              </template>

              <!-- Cron表达式属性 -->
              <template v-if="activeItem.type === 'cron-selector'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('cron')"
                >
                  <span class="font-bold">{{ $t('form-design.material.components.cron') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('cron')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('cron')">
                  <ElFormItem :label="$t('form-design.attribute.hideSecond')">
                    <ElSwitch v-model="activeItem.props.hideSecond" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.hideYear')">
                    <ElSwitch v-model="activeItem.props.hideYear" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 图片选择属性 -->
              <template v-if="activeItem.type === 'image-selector'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('image')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.imageProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('image')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('image')">
                  <ElFormItem :label="$t('form-design.attribute.multiple')">
                    <ElSwitch v-model="activeItem.props.multiple" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.maxSize')">
                    <ElInputNumber
                      v-model="activeItem.props.maxSize"
                      :min="0"
                      controls-position="right"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.layout.column')">
                    <ElInputNumber
                      v-model="activeItem.props.gridColumns"
                      :min="1"
                      :max="12"
                      controls-position="right"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.enableCrop')">
                    <ElSwitch v-model="activeItem.props.enableCrop" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 手写签名属性 -->
              <template v-if="activeItem.type === 'signature-pad'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('signature')"
                >
                  <span class="font-bold">{{ $t('form-design.signaturePad.penColor') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('signature')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('signature')">
                  <ElFormItem :label="$t('form-design.signaturePad.penColor')">
                    <ElColorPicker v-model="activeItem.props.penColor" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.signaturePad.penWidth')">
                    <ElSlider
                      v-model="activeItem.props.penWidth"
                      :min="1"
                      :max="10"
                      :step="1"
                      show-input
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.signaturePad.backgroundColor')">
                    <ElColorPicker
                      v-model="activeItem.props.backgroundColor"
                      show-alpha
                      color-format="hex"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.signaturePad.height')">
                    <ElInputNumber
                      v-model="activeItem.props.height"
                      :min="100"
                      :max="500"
                      :step="10"
                      controls-position="right"
                    >
                      <template #suffix>px</template>
                    </ElInputNumber>
                  </ElFormItem>
                </div>
              </template>

              <!-- 二维码属性 -->
              <template v-if="activeItem.type === 'qrcode-generator'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('qrcode')"
                >
                  <span class="font-bold">{{ $t('form-design.qrcode.settings') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('qrcode')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('qrcode')">
                  <ElFormItem :label="$t('form-design.qrcode.dataSource')">
                    <ElSelect v-model="activeItem.props.dataSource">
                      <ElOption value="static" :label="$t('form-design.qrcode.dataSourceStatic')" />
                      <ElOption value="field" :label="$t('form-design.qrcode.dataSourceField')" />
                      <ElOption value="formula" :label="$t('form-design.qrcode.dataSourceFormula')" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem v-if="activeItem.props.dataSource === 'static'" :label="$t('form-design.qrcode.placeholder')">
                    <ElInput
                      v-model="activeItem.defaultValue"
                      type="textarea"
                      :rows="3"
                      :placeholder="$t('form-design.qrcode.placeholder')"
                    />
                  </ElFormItem>
                  <ElFormItem v-if="activeItem.props.dataSource === 'field'" :label="$t('form-design.qrcode.boundField')">
                    <ElSelect v-model="activeItem.props.boundField" filterable clearable>
                      <ElOption
                        v-for="field in availableFields"
                        :key="field.value"
                        :value="field.value"
                        :label="field.label"
                      />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem v-if="activeItem.props.dataSource === 'formula'" :label="$t('form-design.qrcode.formula')">
                    <ElInput
                      v-model="activeItem.props.formula"
                      type="textarea"
                      :rows="2"
                      :placeholder="$t('form-design.qrcode.formulaPlaceholder')"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.qrcode.qrcodeType')">
                    <ElSelect v-model="activeItem.props.qrcodeType">
                      <ElOption value="text" :label="$t('form-design.qrcode.typeText')" />
                      <ElOption value="url" :label="$t('form-design.qrcode.typeUrl')" />
                      <ElOption value="tel" :label="$t('form-design.qrcode.typeTel')" />
                      <ElOption value="sms" :label="$t('form-design.qrcode.typeSms')" />
                      <ElOption value="email" :label="$t('form-design.qrcode.typeEmail')" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.qrcode.size')">
                    <ElInputNumber
                      v-model="activeItem.props.size"
                      :min="100"
                      :max="500"
                      :step="10"
                      controls-position="right"
                    >
                      <template #suffix>px</template>
                    </ElInputNumber>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.qrcode.errorCorrectionLevel')">
                    <ElSelect v-model="activeItem.props.errorCorrectionLevel">
                      <ElOption value="L" label="L (7%)" />
                      <ElOption value="M" label="M (15%)" />
                      <ElOption value="Q" label="Q (25%)" />
                      <ElOption value="H" label="H (30%)" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.qrcode.foregroundColor')">
                    <ElColorPicker v-model="activeItem.props.foregroundColor" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.qrcode.backgroundColor')">
                    <ElColorPicker v-model="activeItem.props.backgroundColor" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.qrcode.logoUrl')">
                    <ElInput v-model="activeItem.props.logoUrl" :placeholder="$t('form-design.qrcode.logoUrlPlaceholder')" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.qrcode.showContent')">
                    <ElSwitch v-model="activeItem.props.showContent" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.qrcode.enableDownload')">
                    <ElSwitch v-model="activeItem.props.enableDownload" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.qrcode.enableCopy')">
                    <ElSwitch v-model="activeItem.props.enableCopy" />
                  </ElFormItem>
                </div>
              </template>

              <!-- AI图片识别属性 -->
              <template v-if="activeItem.type === 'ai-image-ocr'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('aiOcr')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.aiOcrProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('aiOcr')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('aiOcr')">
                  <ElFormItem :label="$t('form-design.attribute.aiOcrAcceptFileTypes')">
                    <ElCheckboxGroup v-model="activeItem.aiOcrConfig.acceptFileTypes">
                      <ElCheckbox label="image">{{ $t('form-design.aiImageOcr.imageFile') }}</ElCheckbox>
                      <ElCheckbox label="text">{{ $t('form-design.aiImageOcr.textFile') }}</ElCheckbox>
                      <ElCheckbox label="pdf">PDF</ElCheckbox>
                      <ElCheckbox label="word">Word</ElCheckbox>
                      <ElCheckbox label="excel">Excel</ElCheckbox>
                    </ElCheckboxGroup>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.maxSize')">
                    <ElInputNumber
                      v-model="activeItem.props.maxSize"
                      :min="0"
                      controls-position="right"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.height')">
                    <ElInputNumber
                      v-model="activeItem.props.height"
                      :min="0"
                      :placeholder="$t('form-design.attribute.heightPlaceholder')"
                      controls-position="right"
                      class="w-full"
                    >
                      <template #suffix>px</template>
                    </ElInputNumber>
                  </ElFormItem>

                  <!-- 预设模板选择 -->
                  <ElFormItem :label="$t('form-design.attribute.aiOcrTemplate')">
                    <ElSelect
                      v-model="activeItem.aiOcrConfig.templateType"
                      class="w-full"
                      @change="handleTemplateChange"
                    >
                      <ElOption
                        v-for="(template, key) in OCR_TEMPLATES"
                        :key="key"
                        :label="template.name"
                        :value="key"
                      />
                    </ElSelect>
                  </ElFormItem>

                  <!-- 结构化输出配置 -->
                  <div
                    class="mb-2 pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                  >
                    {{ $t('form-design.attribute.aiOcrOutputSchema') }}
                    <ElButton
                      size="small"
                      type="primary"
                      link
                      class="ml-2"
                      @click="openSchemaDialog"
                    >
                      {{ $t('form-design.attribute.aiOcrConfigSchema') }}
                    </ElButton>
                  </div>
                  <div
                    v-if="!activeItem.aiOcrConfig.outputSchema?.length"
                    class="mb-3 cursor-pointer rounded border border-dashed border-[var(--el-border-color)] p-3 text-center text-xs text-[var(--el-text-color-secondary)] hover:border-[var(--el-color-primary)]"
                    @click="openSchemaDialog"
                  >
                    {{ $t('form-design.attribute.aiOcrNoSchema') }}
                  </div>
                  <pre
                    v-else
                    class="mb-3 max-h-40 cursor-pointer overflow-auto rounded border border-[var(--el-border-color)] bg-[var(--el-fill-color-lighter)] p-2 text-xs hover:border-[var(--el-color-primary)]"
                    @click="openSchemaDialog"
                  >{{ schemaPreviewJson }}</pre>


                  <!-- 字段映射配置 -->
                  <div
                    class="mb-2 pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                  >
                    {{ $t('form-design.attribute.aiOcrFieldMapping') }}
                    <ElButton
                      size="small"
                      type="primary"
                      link
                      class="ml-2"
                      @click="addAiOcrFieldMapping"
                    >
                      + {{ $t('common.add') }}
                    </ElButton>
                  </div>
                  <div
                    v-for="(mapping, index) in activeItem.aiOcrConfig.fieldMapping"
                    :key="index"
                    class="mb-2 flex items-center gap-2"
                  >
                    <ElSelect
                      v-model="mapping.source"
                      :placeholder="$t('form-design.attribute.aiOcrSourceField')"
                      size="small"
                      class="flex-1"
                      filterable
                      allow-create
                    >
                      <ElOption
                        v-for="field in ocrSchemaFields"
                        :key="field.value"
                        :label="field.label"
                        :value="field.value"
                      />
                    </ElSelect>
                    <span class="text-[var(--el-text-color-secondary)]">→</span>
                    <ElSelect
                      v-model="mapping.target"
                      :placeholder="$t('form-design.attribute.aiOcrTargetField')"
                      size="small"
                      class="flex-1"
                      filterable
                    >
                      <ElOption
                        v-for="field in dependableFields"
                        :key="field.value"
                        :label="field.label"
                        :value="field.value"
                      />
                    </ElSelect>
                    <ElButton
                      size="small"
                      type="danger"
                      link
                      @click="removeAiOcrFieldMapping(Number(index))"
                    >
                      {{ $t('common.delete') }}
                    </ElButton>
                  </div>
                  <div
                    v-if="!activeItem.aiOcrConfig.fieldMapping?.length"
                    class="rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
                  >
                    {{ $t('form-design.attribute.aiOcrNoMapping') }}
                  </div>

                  <!-- 自定义提示词 -->
                  <ElFormItem :label="$t('form-design.attribute.aiOcrCustomPrompt')" class="mt-4">
                    <ElInput
                      v-model="activeItem.aiOcrConfig.customPrompt"
                      type="textarea"
                      :rows="3"
                      :placeholder="$t('form-design.attribute.aiOcrCustomPromptPlaceholder')"
                    />
                  </ElFormItem>
                </div>

                <!-- Schema 配置 Dialog -->
<!--                <SchemaConfigDialog-->
<!--                  v-model="schemaDialogVisible"-->
<!--                  :schema="activeItem.aiOcrConfig?.outputSchema || []"-->
<!--                  @confirm="handleSchemaConfirm"-->
<!--                />-->
              </template>

              <!-- 表格选择器属性 -->
              <template v-if="activeItem.type === 'table-selector'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('tableSelector')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.tableSelectorProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('tableSelector')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('tableSelector')">
                  <ElFormItem :label="$t('form-design.attribute.multiple')">
                    <ElSwitch v-model="activeItem.props.multiple" />
                  </ElFormItem>
                  <ElFormItem
                    v-if="activeItem.props.multiple"
                    :label="$t('form-design.attribute.collapseTags')"
                  >
                    <ElSwitch v-model="activeItem.tableSelectorConfig!.collapseTags" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.dialogTitle')">
                    <ElInput
                      v-model="activeItem.tableSelectorConfig!.dialogTitle"
                      :placeholder="$t('form-design.attribute.selectData')"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.dialogWidth')">
                    <ElInput
                      v-model="activeItem.tableSelectorConfig!.dialogWidth"
                      placeholder="800px"
                    />
                  </ElFormItem>

                  <!-- 显示列配置 -->
                  <div
                    class="mb-2 mt-3 border-t border-[var(--el-border-color)] pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                  >
                    {{ $t('form-design.attribute.tableColumns') }}
                  </div>
                  <div class="mb-2 flex items-center justify-between">
                    <span class="text-xs text-[var(--el-text-color-secondary)]">
                      {{ $t('form-design.attribute.tableColumns') }}
                    </span>
                    <ElButton
                      type="primary"
                      link
                      size="small"
                      @click="addTableSelectorColumn"
                      :disabled="tableSelectorAvailableFields.length === 0"
                    >
                      {{ $t('form-design.attribute.addColumn') }}
                    </ElButton>
                  </div>
                  <div
                    v-if="tableSelectorAvailableFields.length === 0"
                    class="mb-2 rounded bg-[var(--el-fill-color-light)] p-2 text-xs text-[var(--el-text-color-secondary)]"
                  >
                    {{ $t('form-design.attribute.selectDataSourceFirst') }}
                  </div>
                  <div
                    v-for="(col, index) in activeItem.tableSelectorConfig?.columns || []"
                    :key="index"
                    class="mb-2 flex items-center gap-2"
                  >
                    <ElSelect
                      :model-value="col.field"
                      :placeholder="$t('form-design.attribute.columnField')"
                      size="small"
                      class="flex-1"
                      filterable
                      @change="(val: string) => handleColumnFieldChange(col, val)"
                    >
                      <ElOption
                        v-for="field in tableSelectorAvailableFields"
                        :key="field.field"
                        :label="`${field.label} (${field.field})`"
                        :value="field.field"
                      />
                    </ElSelect>
                    <ElInputNumber
                      v-model="col.width"
                      :placeholder="$t('form-design.attribute.columnWidth')"
                      size="small"
                      :min="50"
                      controls-position="right"
                      class="w-24"
                    />
                    <ElButton
                      type="danger"
                      link
                      size="small"
                      @click="removeTableSelectorColumn(index)"
                    >
                      <ElIcon class="w-4"><Delete /></ElIcon>
                    </ElButton>
                  </div>

                  <!-- 搜索字段配置 -->
                  <div
                    class="mb-2 mt-3 border-t border-[var(--el-border-color)] pt-2 text-xs font-bold text-[var(--el-text-color-primary)]"
                  >
                    {{ $t('form-design.attribute.searchFields') }}
                  </div>
                  <ElFormItem :label="$t('form-design.attribute.searchFields')">
                    <ElSelect
                      v-model="activeItem.tableSelectorConfig!.searchFields"
                      :placeholder="$t('form-design.attribute.selectSearchFields')"
                      multiple
                      filterable
                      clearable
                      collapse-tags
                      collapse-tags-tooltip
                      class="w-full"
                      :disabled="tableSelectorAvailableFields.length === 0"
                    >
                      <ElOption
                        v-for="field in tableSelectorAvailableFields"
                        :key="field.field"
                        :label="`${field.label} (${field.field})`"
                        :value="field.field"
                      />
                    </ElSelect>
                  </ElFormItem>
                </div>
              </template>

              <!-- 表单选择器属性 -->
              <template v-if="activeItem.type === 'form-selector'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('formSelector')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.formSelectorProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('formSelector')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('formSelector')">
                  <ElFormItem :label="$t('form-design.attribute.formCode')">
                    <ElSelect
                      v-model="activeItem.formSelectorConfig!.formCode"
                      :placeholder="$t('form-design.attribute.selectForm')"
                      filterable
                      clearable
                      :loading="loadingPublishedForms"
                      class="w-full"
                      @focus="loadPublishedFormList"
                      @change="handleFormSelectorFormChange"
                    >
                      <ElOption
                        v-for="form in publishedFormList"
                        :key="form.code"
                        :label="`${form.name} (${form.code})`"
                        :value="form.code"
                      />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.valueField')">
                    <ElSelect
                      v-model="activeItem.formSelectorConfig!.valueField"
                      :placeholder="$t('form-design.attribute.selectValueField')"
                      filterable
                      class="w-full"
                      :disabled="formSelectorAvailableFields.length === 0"
                    >
                      <ElOption
                        v-for="field in formSelectorAvailableFields"
                        :key="field.field"
                        :label="`${field.label} (${field.field})`"
                        :value="field.field"
                      />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.labelField')">
                    <ElSelect
                      v-model="activeItem.formSelectorConfig!.labelField"
                      :placeholder="$t('form-design.attribute.selectLabelField')"
                      filterable
                      class="w-full"
                      :disabled="formSelectorAvailableFields.length === 0"
                    >
                      <ElOption
                        v-for="field in formSelectorAvailableFields"
                        :key="field.field"
                        :label="`${field.label} (${field.field})`"
                        :value="field.field"
                      />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.multiple')">
                    <ElSwitch v-model="activeItem.props.multiple" />
                  </ElFormItem>
                  <ElFormItem
                    v-if="activeItem.props.multiple && isInsideSubTable"
                    :label="$t('form-design.attribute.expandMultipleToRows')"
                  >
                    <ElSwitch v-model="activeItem.props.expandMultipleToRows" />
                  </ElFormItem>
                  <div
                    v-if="activeItem.props.multiple && isInsideSubTable && activeItem.props.expandMultipleToRows"
                    class="text-muted-foreground mb-3 text-xs"
                  >
                    {{ $t('form-design.attribute.expandMultipleToRowsTip') }}
                  </div>
                  <ElFormItem v-if="activeItem.props.multiple && !activeItem.props.expandMultipleToRows" :label="$t('form-design.attribute.collapseTags')">
                    <ElSwitch v-model="activeItem.props.collapseTags" />
                  </ElFormItem>
                  <ElFormItem v-if="activeItem.props.multiple && !activeItem.props.expandMultipleToRows && activeItem.props.collapseTags" :label="$t('form-design.attribute.maxCollapseTags')">
                    <ElInputNumber
                      v-model="activeItem.props.maxCollapseTags"
                      :min="1"
                      :max="10"
                      controls-position="right"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.dialogTitle')">
                    <ElInput
                      v-model="activeItem.props.dialogTitle"
                      :placeholder="$t('form-design.attribute.selectData')"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.dialogWidth')">
                    <ElInput
                      v-model="activeItem.props.dialogWidth"
                      placeholder="1200px"
                    />
                  </ElFormItem>
                </div>
              </template>

              <!-- 文件选择属性 -->
              <template v-if="activeItem.type === 'file-selector'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('file')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.fileProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('file')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('file')">
                  <ElFormItem :label="$t('form-design.attribute.multiple')">
                    <ElSwitch v-model="activeItem.props.multiple" />
                  </ElFormItem>
                  <ElFormItem
                    :label="$t('form-design.attribute.maxCount')"
                    v-if="activeItem.props.multiple"
                  >
                    <ElInputNumber
                      v-model="activeItem.props.limit"
                      :min="1"
                      controls-position="right"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.maxSize')">
                    <ElInputNumber
                      v-model="activeItem.props.maxSize"
                      :min="0"
                      controls-position="right"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.accept')">
                    <ElInput
                      v-model="activeItem.props.accept"
                      :placeholder="$t('form-design.attribute.acceptPlaceholder')"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.displayMode')">
                    <ElSelect v-model="activeItem.props.displayMode">
                      <ElOption :label="$t('form-design.attribute.list')" value="list" />
                      <ElOption :label="$t('form-design.attribute.popover')" value="popover" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.showSize')">
                    <ElSwitch v-model="activeItem.props.showSize" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.showIcon')">
                    <ElSwitch v-model="activeItem.props.showIcon" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 警告提示属性 -->
              <template v-if="activeItem.type === 'alert'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('alert')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.alertProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('alert')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('alert')">
                  <ElFormItem :label="$t('form-design.attribute.label')">
                    <ElInput v-model="activeItem.props.title" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.type')">
                    <ElSelect v-model="activeItem.props.type">
                      <ElOption :label="$t('common.primary')" value="primary" />
                      <ElOption :label="$t('common.success')" value="success" />
                      <ElOption :label="$t('common.warning')" value="warning" />
                      <ElOption :label="$t('common.info')" value="info" />
                      <ElOption :label="$t('common.error')" value="error" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.remark')">
                    <ElInput
                      v-model="activeItem.props.description"
                      type="textarea"
                      :rows="2"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.showIcon')">
                    <ElSwitch v-model="activeItem.props.showIcon" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.closable')">
                    <ElSwitch v-model="activeItem.props.closable" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.center')">
                    <ElSwitch v-model="activeItem.props.center" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 时间线属性 -->
              <template v-if="activeItem.type === 'timeline'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('timeline')"
                >
                  <span class="font-bold">{{ $t('form-design.material.components.timeline') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('timeline')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('timeline')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <ElFormItem :label="$t('form-design.attribute.sort')">
                    <ElSwitch v-model="activeItem.props.reverse" />
                  </ElFormItem>

                  <div
                    class="mb-3 border-b pb-2 font-bold text-[var(--el-text-color-primary)]"
                  >
                    {{ $t('form-design.attribute.basicSettings') }}
                  </div>
                  <div
                    class="mb-2 mt-2 flex items-center justify-between border-t pt-2 font-bold text-[var(--el-text-color-primary)]"
                  >
                    <span>{{ $t('form-design.attribute.optionsList') }}</span>
                    <ElButton
                      type="primary"
                      link
                      size="small"
                      @click="
                        activeItem?.items &&
                        activeItem.items.push({
                          timestamp: '2024-01-01',
                          content: $t('form-design.attribute.layout.addPanel'),
                          type: 'primary',
                        })
                      "
                    >
                      {{ $t('form-design.add') }}
                    </ElButton>
                  </div>

                  <draggable
                    v-model="activeItem.items"
                    item-key="timestamp"
                    handle=".handle"
                    :animation="200"
                  >
                    <template #item="{ element, index }">
                      <div
                        class="mb-2 flex flex-col gap-2 rounded border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-light)] p-2"
                      >
                        <div class="flex items-center justify-between">
                          <ElIcon
                            class="handle w-4 cursor-move text-[var(--el-text-color-secondary)]"
                          >
                            <Rank />
                          </ElIcon>
                          <span class="text-xs font-bold text-gray-500">{{ $t('form-design.attribute.layout.addPanel') }} {{ index + 1 }}</span>
                          <ElButton
                            type="danger"
                            link
                            size="small"
                            @click="
                              activeItem?.items &&
                              activeItem.items.splice(index as any, 1)
                            "
                            v-if="activeItem.items.length > 1"
                          >
                            <ElIcon class="w-4"><Delete /></ElIcon>
                          </ElButton>
                        </div>
                        <ElInput
                          v-model="element.content"
                          :placeholder="$t('form-design.attribute.label')"
                          size="small"
                        />
                        <ElInput
                          v-model="element.timestamp"
                          :placeholder="$t('form-design.material.components.currentDatetime')"
                          size="small"
                        />
                        <ElSelect
                          v-model="element.type"
                          :placeholder="$t('form-design.attribute.type')"
                          size="small"
                        >
                          <ElOption label="Primary" value="primary" />
                          <ElOption label="Success" value="success" />
                          <ElOption label="Warning" value="warning" />
                          <ElOption label="Danger" value="danger" />
                          <ElOption label="Info" value="info" />
                        </ElSelect>
                        <ElColorPicker
                          v-model="element.color"
                          show-alpha
                          size="small"
                        />
                      </div>
                    </template>
                  </draggable>
                </div>
              </template>

              <!-- 子表单属性 -->
              <template v-if="activeItem.type === 'sub-table'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('subtable')"
                >
                  <span class="font-bold">{{ $t('form-design.material.components.subTable') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('subtable')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('subtable')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <!-- 关联从表选择器 -->
                  <ElFormItem :label="$t('form-design.attribute.subTable.linkTable')">
                    <ElSelect
                      :model-value="activeItem.field"
                      :placeholder="$t('form-design.attribute.subTable.linkTable')"
                      clearable
                      class="w-full"
                      @change="onSubTableLinkChange"
                    >
                      <ElOption
                        v-for="table in dataSource.subTables"
                        :key="table.id"
                        :label="`${table.tableName} (${table.alias})`"
                        :value="table.tableName"
                      />
                    </ElSelect>
                  </ElFormItem>

                  <!-- 自动填充字段按钮 -->
                  <div class="mb-3">
                    <ElButton
                      type="primary"
                      plain
                      size="small"
                      class="w-full"
                      :disabled="
                        !dataSource.subTables.find(
                          (t) => t.tableName === activeItem.field,
                        )
                      "
                      @click="autoFillSubTableFields"
                    >
                      {{ $t('form-design.attribute.subTable.autoFill') }}
                    </ElButton>
                    <div
                      class="mt-1 text-[10px] text-[var(--el-text-color-secondary)]"
                    >
                      {{ $t('form-design.attribute.subTable.autoFillTip') }}
                    </div>
                  </div>

                  <div
                    class="mb-2 border-t border-[var(--el-border-color-lighter)] pt-2"
                  ></div>

                  <ElFormItem :label="$t('form-design.attribute.displayMode')">
                    <ElSelect
                      v-model="activeItem.props.displayMode"
                      :placeholder="$t('form-design.attribute.placeholder')"
                    >
                      <ElOption :label="$t('common.table')" value="table" />
                      <ElOption :label="$t('form-design.attribute.card')" value="card" />
                      <ElOption :label="$t('form-design.attribute.inline')" value="inline" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.buttonText')">
                    <ElInput
                      v-model="activeItem.props.addButtonText"
                      :placeholder="$t('form-design.add')"
                    />
                  </ElFormItem>

                  <ElFormItem :label="$t('form-design.attribute.subTable.stripe')">
                    <ElSwitch v-model="activeItem.props.stripe" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.subTable.showIndex')">
                    <ElSwitch v-model="activeItem.props.showIndex" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.subTable.summary')">
                    <ElSwitch v-model="activeItem.props.summary" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.subTable.addable')">
                    <ElSwitch v-model="activeItem.props.addable" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.subTable.deletable')">
                    <ElSwitch v-model="activeItem.props.deletable" />
                  </ElFormItem>

                  <div
                    class="mb-2 mt-2 border-t border-[var(--el-border-color-lighter)]"
                  ></div>
                  <div
                    class="mb-2 text-xs font-bold text-[var(--el-text-color-secondary)]"
                  >
                    {{ $t('form-design.attribute.rowControl') }}
                  </div>

                  <div class="flex gap-2">
                    <ElFormItem :label="$t('form-design.attribute.minRows')" class="flex-1">
                      <ElInputNumber
                        v-model="activeItem.props.minRows"
                        :min="0"
                        controls-position="right"
                        class="w-full"
                      />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.attribute.maxRows')" class="flex-1">
                      <ElInputNumber
                        v-model="activeItem.props.maxRows"
                        :min="0"
                        controls-position="right"
                        class="w-full"
                      />
                    </ElFormItem>
                  </div>

                  <ElFormItem :label="$t('form-design.attribute.sortable')">
                    <ElSwitch v-model="activeItem.props.sortable" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.showSortButtons')">
                    <ElSwitch v-model="activeItem.props.showSortButtons" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.copyable')">
                    <ElSwitch v-model="activeItem.props.copyable" />
                  </ElFormItem>

                  <div
                    class="mb-2 mt-2 border-t border-[var(--el-border-color-lighter)]"
                  ></div>
                  <div
                    class="mb-2 text-xs font-bold text-[var(--el-text-color-secondary)]"
                  >
                    {{ $t('form-design.attribute.pagination') }}
                  </div>
                  <ElFormItem :label="$t('form-design.attribute.enablePagination')">
                    <ElSwitch v-model="activeItem.props.pagination" />
                  </ElFormItem>
                  <ElFormItem
                    :label="$t('form-design.attribute.pageSize')"
                    v-if="activeItem.props.pagination"
                  >
                    <ElInputNumber
                      v-model="activeItem.props.pageSize"
                      :min="1"
                      :max="100"
                      controls-position="right"
                      class="w-full"
                    />
                  </ElFormItem>
                </div>
              </template>

              <!-- 省市区选择器属性 -->
              <template v-if="activeItem.type === 'region-selector'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('region')"
                >
                  <span class="font-bold">{{ $t('form-design.material.components.regionSelector') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('region')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('region')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <ElFormItem label="选择级别">
                    <ElSelect v-model="activeItem.props.level" class="w-full">
                      <ElOption label="省份" :value="1" />
                      <ElOption label="省/市" :value="2" />
                      <ElOption label="省/市/区" :value="3" />
                      <ElOption label="省/市/区/街道" :value="4" />
                      <ElOption label="省/市/区/街道/村庄" :value="5" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem label="悬停加载">
                    <ElSwitch
                      :model-value="activeItem.props.expandTrigger === 'hover'"
                      @update:model-value="(val) => activeItem.props.expandTrigger = val ? 'hover' : 'click'"
                    />
                  </ElFormItem>
                  <ElFormItem label="可选任意级别">
                    <ElSwitch v-model="activeItem.props.checkStrictly" />
                  </ElFormItem>
                  <ElFormItem label="显示完整路径">
                    <ElSwitch v-model="activeItem.props.showAllLevels" />
                  </ElFormItem>
                  <ElFormItem label="分隔符">
                    <ElInput
                      v-model="activeItem.props.separator"
                      placeholder="/"
                      style="width: 80px"
                    />
                  </ElFormItem>
                </div>
              </template>

              <!-- 表格列设置 (仅在子表单内部组件显示) -->
              <template v-if="isInsideSubTable">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('table-column')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.layout.column') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('table-column')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('table-column')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <ElFormItem :label="$t('form-design.attribute.width')">
                    <ElInput
                      v-model="activeItem.props.columnWidth"
                      :placeholder="$t('form-design.attribute.widthPlaceholder')"
                    />
                    <div
                      class="mt-1 text-xs text-[var(--el-text-color-secondary)]"
                    >
                      {{ $t('form-design.attribute.widthAutoTip') }}
                    </div>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.align')">
                    <ElSelect v-model="activeItem.props.columnAlign">
                      <ElOption :label="$t('form-design.attribute.location.left')" value="left" />
                      <ElOption :label="$t('form-design.attribute.location.middle')" value="center" />
                      <ElOption :label="$t('form-design.attribute.location.right')" value="right" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.fixed')">
                    <ElSelect v-model="activeItem.props.columnFixed">
                      <ElOption :label="$t('common.none')" value="" />
                      <ElOption :label="$t('form-design.attribute.location.left')" value="left" />
                      <ElOption :label="$t('form-design.attribute.location.right')" value="right" />
                    </ElSelect>
                  </ElFormItem>
                  <template v-if="parentSubTableHasSummary">
                    <ElFormItem :label="$t('form-design.attribute.subTable.enableColumnSummary')">
                      <ElSwitch v-model="activeItem.props.enableSummary" />
                    </ElFormItem>
                    <ElFormItem
                      v-if="activeItem.props.enableSummary"
                      :label="$t('form-design.attribute.subTable.summaryType')"
                    >
                      <ElSelect v-model="activeItem.props.summaryType" placeholder="sum">
                        <ElOption :label="$t('form-design.attribute.subTable.summarySum')" value="sum" />
                        <ElOption :label="$t('form-design.attribute.subTable.summaryAvg')" value="avg" />
                        <ElOption :label="$t('form-design.attribute.subTable.summaryMin')" value="min" />
                        <ElOption :label="$t('form-design.attribute.subTable.summaryMax')" value="max" />
                        <ElOption :label="$t('form-design.attribute.subTable.summaryCount')" value="count" />
                      </ElSelect>
                    </ElFormItem>
                  </template>
                </div>
              </template>

              <!-- 栅格布局属性 -->
              <template v-if="activeItem.type === 'grid' && activeItem.columns">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('grid')"
                >
                  <span class="font-bold">{{ $t('form-design.material.components.grid') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('grid')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('grid')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <ElFormItem :label="$t('form-design.attribute.layout.gutter')">
                    <ElInputNumber
                      v-model="activeItem.props.gutter"
                      :min="0"
                      controls-position="right"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.layout.justify')">
                    <ElSelect v-model="activeItem.props.justify">
                      <ElOption :label="$t('form-design.attribute.location.left')" value="start" />
                      <ElOption :label="$t('form-design.attribute.center')" value="center" />
                      <ElOption :label="$t('form-design.attribute.location.right')" value="end" />
                      <ElOption label="Space Between" value="space-between" />
                      <ElOption label="Space Around" value="space-around" />
                      <ElOption label="Space Evenly" value="space-evenly" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.layout.align')">
                    <ElSelect v-model="activeItem.props.align">
                      <ElOption :label="$t('form-design.attribute.location.top')" value="top" />
                      <ElOption :label="$t('form-design.attribute.location.middle')" value="middle" />
                      <ElOption :label="$t('form-design.attribute.location.bottom')" value="bottom" />
                    </ElSelect>
                  </ElFormItem>

                  <div
                    class="mb-3 border-b pb-2 font-bold text-[var(--el-text-color-primary)]"
                  >
                    {{ $t('form-design.attribute.basicSettings') }}
                  </div>
                  <div
                    class="mb-2 mt-2 border-t pt-2 font-bold text-[var(--el-text-color-primary)]"
                  >
                    {{ $t('form-design.attribute.layout.column') }}
                  </div>
                  <div
                    v-for="(col, index) in activeItem.columns"
                    :key="index"
                    class="mb-2 flex items-center gap-2"
                  >
                    <span class="w-10 text-xs">{{ $t('form-design.attribute.layout.column') }}{{ (index as any) + 1 }}</span>
                    <ElInputNumber
                      v-model="col.span"
                      :min="1"
                      :max="24"
                      size="small"
                      class="flex-1"
                    />
                    <ElButton
                      type="danger"
                      link
                      size="small"
                      @click="removeGridColumn(index as any)"
                      v-if="activeItem.columns.length > 1"
                    >
                      <ElIcon class="w-4"><Delete /></ElIcon>
                    </ElButton>
                  </div>
                  <ElButton
                    type="primary"
                    link
                    size="small"
                    @click="addGridColumn"
                  >
                    + {{ $t('form-design.attribute.layout.addTab') }}
                  </ElButton>
                </div>
              </template>

              <!-- 标题组件属性 -->
              <template v-if="activeItem.type === 'title'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('title')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.titleProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('title')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('title')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <ElFormItem :label="$t('form-design.attribute.titleText')">
                    <ElInput v-model="activeItem.props.text" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.titleFontSize')">
                    <ElSlider
                      v-model="activeItem.props.fontSize"
                      :min="12"
                      :max="28"
                      :step="1"
                      show-input
                      input-size="small"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.titleTheme')">
                    <ElSelect v-model="activeItem.props.theme">
                      <ElOption
                        v-for="t in ['primary', 'success', 'info', 'warning', 'danger']"
                        :key="t"
                        :label="t"
                        :value="t"
                      >
                        <div class="flex items-center gap-2">
                          <div
                            class="h-3 w-3 rounded-sm"
                            :style="{ backgroundColor: `var(--el-color-${t})` }"
                          />
                          <span>{{ t }}</span>
                        </div>
                      </ElOption>
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.titleShowBar')">
                    <ElSwitch v-model="activeItem.props.showBar" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.titleShowBorder')">
                    <ElSwitch v-model="activeItem.props.showBorder" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 间距占位属性 -->
              <template v-if="activeItem.type === 'spacer'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('spacer')"
                >
                  <span class="font-bold">{{ $t('form-design.material.components.spacer') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('spacer')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('spacer')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <ElFormItem :label="$t('form-design.attribute.spacerHeight')">
                    <ElSlider
                      v-model="activeItem.props.height"
                      :min="4"
                      :max="200"
                      :step="4"
                      show-input
                      input-size="small"
                    />
                  </ElFormItem>
                </div>
              </template>

              <!-- 步骤组件属性 -->
              <template v-if="activeItem.type === 'steps' && activeItem.items">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('steps')"
                >
                  <span class="font-bold">{{ $t('form-design.material.components.steps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('steps')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('steps')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <ElFormItem :label="$t('form-design.attribute.direction')">
                    <ElSelect v-model="activeItem.props.direction">
                      <ElOption :label="$t('form-design.attribute.horizontal')" value="horizontal" />
                      <ElOption :label="$t('form-design.attribute.vertical')" value="vertical" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.layout.alignCenter')">
                    <ElSwitch v-model="activeItem.props.alignCenter" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.layout.simple')">
                    <ElSwitch v-model="activeItem.props.simple" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.layout.finishStatus')">
                    <ElSelect v-model="activeItem.props.finishStatus">
                      <ElOption label="success" value="success" />
                      <ElOption label="error" value="error" />
                      <ElOption label="finish" value="finish" />
                      <ElOption label="process" value="process" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.layout.processStatus')">
                    <ElSelect v-model="activeItem.props.processStatus">
                      <ElOption label="wait" value="wait" />
                      <ElOption label="process" value="process" />
                      <ElOption label="finish" value="finish" />
                      <ElOption label="error" value="error" />
                      <ElOption label="success" value="success" />
                    </ElSelect>
                  </ElFormItem>

                  <div
                    class="mb-2 mt-2 flex items-center justify-between border-t pt-2 font-bold text-[var(--el-text-color-primary)]"
                  >
                    <span>{{ $t('form-design.attribute.layout.addStep') }}</span>
                    <ElButton
                      type="primary"
                      link
                      size="small"
                      @click="
                        activeItem?.items &&
                        activeItem.items.push({
                          title: $t('form-design.attribute.layout.addStep'),
                          description: '',
                          name: `${Date.now()}`,
                          children: [],
                        })
                      "
                    >
                      {{ $t('form-design.add') }}
                    </ElButton>
                  </div>

                  <draggable
                    v-model="activeItem.items"
                    item-key="name"
                    handle=".handle"
                    :animation="200"
                  >
                    <template #item="{ element, index }">
                      <div
                        class="mb-2 flex items-center gap-2 rounded border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-light)] p-2"
                      >
                        <ElIcon
                          class="handle w-4 cursor-move text-[var(--el-text-color-secondary)]"
                        >
                          <Rank />
                        </ElIcon>
                        <div class="flex flex-1 flex-col gap-1">
                          <ElInput
                            v-model="element.title"
                            :placeholder="$t('form-design.attribute.layout.stepTitle')"
                            size="small"
                          />
                          <ElInput
                            v-model="element.description"
                            :placeholder="$t('form-design.attribute.layout.stepDescription')"
                            size="small"
                          />
                        </div>
                        <ElButton
                          type="danger"
                          link
                          size="small"
                          @click="
                            activeItem?.items &&
                            activeItem.items.splice(index as any, 1)
                          "
                          v-if="activeItem.items.length > 1"
                        >
                          <ElIcon class="w-4"><Delete /></ElIcon>
                        </ElButton>
                      </div>
                    </template>
                  </draggable>
                </div>
              </template>

              <!-- 分割线属性 -->
              <template v-if="activeItem.type === 'divider'">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('divider')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.dividerProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('divider')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('divider')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <ElFormItem :label="$t('form-design.attribute.label')">
                    <ElInput v-model="activeItem.label" :placeholder="$t('form-design.material.components.divider')" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.contentPosition')">
                    <ElSelect v-model="activeItem.props.contentPosition">
                      <ElOption :label="$t('form-design.attribute.location.left')" value="left" />
                      <ElOption :label="$t('form-design.attribute.center')" value="center" />
                      <ElOption :label="$t('form-design.attribute.location.right')" value="right" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.borderStyle')">
                    <ElSelect v-model="activeItem.props.borderStyle">
                      <ElOption :label="$t('form-design.attribute.solid')" value="solid" />
                      <ElOption :label="$t('form-design.attribute.dashed')" value="dashed" />
                      <ElOption :label="$t('form-design.attribute.dotted')" value="dotted" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.direction')">
                    <ElSelect v-model="activeItem.props.direction">
                      <ElOption :label="$t('form-design.attribute.horizontal')" value="horizontal" />
                      <ElOption :label="$t('form-design.attribute.vertical')" value="vertical" />
                    </ElSelect>
                  </ElFormItem>
                </div>
              </template>

              <!-- 折叠面板属性 -->
              <template
                v-if="activeItem.type === 'collapse' && activeItem.items"
              >
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('collapse')"
                >
                  <span class="font-bold">{{ $t('form-design.material.components.collapse') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('collapse')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('collapse')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <ElFormItem :label="$t('form-design.attribute.layout.accordion')">
                    <ElSwitch v-model="activeItem.props.accordion" />
                  </ElFormItem>

                  <div
                    class="mb-3 border-b pb-2 font-bold text-[var(--el-text-color-primary)]"
                  >
                    {{ $t('form-design.attribute.basicSettings') }}
                  </div>
                  <div
                    class="mb-2 mt-2 flex items-center justify-between border-t pt-2 font-bold text-[var(--el-text-color-primary)]"
                  >
                    <span>{{ $t('form-design.attribute.layout.addPanel') }}</span>
                    <ElButton
                      type="primary"
                      link
                      size="small"
                      @click="
                        activeItem?.items &&
                        activeItem.items.push({
                          title: $t('form-design.attribute.layout.addPanel'),
                          name: `${Date.now()}`,
                          children: [],
                        })
                      "
                    >
                      {{ $t('form-design.add') }}
                    </ElButton>
                  </div>

                  <draggable
                    v-model="activeItem.items"
                    item-key="name"
                    handle=".handle"
                    :animation="200"
                  >
                    <template #item="{ element, index }">
                      <div
                        class="mb-2 flex items-center gap-2 rounded border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-light)] p-2"
                      >
                        <ElIcon
                          class="handle w-4 cursor-move text-[var(--el-text-color-secondary)]"
                        >
                          <Rank />
                        </ElIcon>
                        <div class="flex flex-1 flex-col gap-1">
                          <ElInput
                            v-model="element.title"
                            :placeholder="$t('form-design.attribute.label')"
                            size="small"
                          />
                          <ElInput
                            v-model="element.name"
                            placeholder="Name"
                            size="small"
                          />
                        </div>
                        <ElButton
                          type="danger"
                          link
                          size="small"
                          @click="
                            activeItem?.items &&
                            activeItem.items.splice(index as any, 1)
                          "
                          v-if="activeItem.items.length > 1"
                        >
                          <ElIcon class="w-4"><Delete /></ElIcon>
                        </ElButton>
                      </div>
                    </template>
                  </draggable>
                </div>
              </template>

              <!-- 标签页属性 -->
              <template v-if="activeItem.type === 'tabs' && activeItem.items">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('tabs')"
                >
                  <span class="font-bold">{{ $t('form-design.material.components.tabs') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('tabs')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-show="activeSections.includes('tabs')"
                  class="rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
                >
                  <ElFormItem :label="$t('form-design.attribute.layout.tabType')">
                    <ElSelect v-model="activeItem.props.type">
                      <ElOption :label="$t('form-design.attribute.default')" value="" />
                      <ElOption label="Card" value="card" />
                      <ElOption label="Border Card" value="border-card" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.layout.tabPosition')">
                    <ElRadioGroup
                      v-model="activeItem.props.tabPosition"
                      size="small"
                    >
                      <ElRadioButton label="top">{{ $t('form-design.attribute.location.top') }}</ElRadioButton>
                      <ElRadioButton label="right">{{ $t('form-design.attribute.location.right') }}</ElRadioButton>
                      <ElRadioButton label="bottom">{{ $t('form-design.attribute.location.bottom') }}</ElRadioButton>
                      <ElRadioButton label="left">{{ $t('form-design.attribute.location.left') }}</ElRadioButton>
                    </ElRadioGroup>
                  </ElFormItem>

                  <div
                    class="mb-3 border-b pb-2 font-bold text-[var(--el-text-color-primary)]"
                  >
                    {{ $t('form-design.attribute.basicSettings') }}
                  </div>
                  <div
                    class="mb-2 mt-2 flex items-center justify-between border-t pt-2 font-bold text-[var(--el-text-color-primary)]"
                  >
                    <span>{{ $t('form-design.attribute.layout.addTab') }}</span>
                    <ElButton
                      type="primary"
                      link
                      size="small"
                      @click="
                        activeItem?.items &&
                        activeItem.items.push({
                          label: $t('form-design.attribute.layout.addTab'),
                          name: `${Date.now()}`,
                          children: [],
                        })
                      "
                    >
                      {{ $t('form-design.add') }}
                    </ElButton>
                  </div>

                  <draggable
                    v-model="activeItem.items"
                    item-key="name"
                    handle=".handle"
                    :animation="200"
                  >
                    <template #item="{ element, index }">
                      <div
                        class="mb-2 flex items-center gap-2 rounded border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-light)] p-2"
                      >
                        <ElIcon
                          class="handle w-4 cursor-move text-[var(--el-text-color-secondary)]"
                        >
                          <Rank />
                        </ElIcon>
                        <div class="flex flex-1 flex-col gap-1">
                          <ElInput
                            v-model="element.label"
                            :placeholder="$t('form-design.attribute.label')"
                            size="small"
                          />
                          <ElInput
                            v-model="element.name"
                            placeholder="Name"
                            size="small"
                          />
                        </div>
                        <ElButton
                          type="danger"
                          link
                          size="small"
                          @click="
                            activeItem?.items &&
                            activeItem.items.splice(index as any, 1)
                          "
                          v-if="activeItem.items.length > 1"
                        >
                          <ElIcon class="w-4"><Delete /></ElIcon>
                        </ElButton>
                      </div>
                    </template>
                  </draggable>
                </div>
              </template>
              <!-- 操作属性 -->
              <template v-if="!isLayoutComponent">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('operation')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.operationProps') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('operation')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('operation')">
                  <ElFormItem :label="$t('form-design.attribute.clearable')" v-if="hasProp('clearable')">
                    <ElSwitch v-model="activeItem.props.clearable" />
                  </ElFormItem>
                  <ElFormItem :label="$t('common.disabled')" v-if="hasProp('disabled')">
                    <ElSwitch v-model="activeItem.props.disabled" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.required')">
                    <ElSwitch v-model="activeItem.props.required" />
                  </ElFormItem>
                </div>
              </template>

              <!-- 默认值 -->
              <template v-if="supportsDefaultValue">
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('default-value')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.defaultValue') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('default-value')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('default-value')">
                  <!-- 文本输入类 -->
                  <ElFormItem
                    v-if="['input', 'textarea'].includes(activeItem.type)"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElInput
                      v-model="activeItem.defaultValue"
                      :type="activeItem.type === 'textarea' ? 'textarea' : 'text'"
                      :rows="activeItem.type === 'textarea' ? 2 : undefined"
                      :placeholder="$t('form-design.attribute.defaultValuePlaceholder')"
                      clearable
                      size="small"
                    />
                  </ElFormItem>

                  <!-- 数字输入 -->
                  <ElFormItem
                    v-else-if="activeItem.type === 'input-number'"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElInputNumber
                      v-model="activeItem.defaultValue"
                      :min="activeItem.props?.min"
                      :max="activeItem.props?.max"
                      :step="activeItem.props?.step"
                      :precision="activeItem.props?.precision"
                      controls-position="right"
                      class="w-full"
                      size="small"
                    />
                  </ElFormItem>

                  <!-- 单选下拉/单选按钮 -->
                  <ElFormItem
                    v-else-if="['select', 'radio'].includes(activeItem.type) && !activeItem.props?.multiple"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElSelect
                      v-model="activeItem.defaultValue"
                      :placeholder="$t('form-design.attribute.defaultValuePlaceholder')"
                      :loading="loadingDefaultValueOptions"
                      clearable
                      class="w-full"
                      size="small"
                      @focus="refreshDefaultValueOptions"
                    >
                      <ElOption
                        v-for="opt in defaultValueOptionsForSelect"
                        :key="opt.value"
                        :label="opt.label"
                        :value="opt.value"
                      />
                    </ElSelect>
                  </ElFormItem>

                  <!-- 多选下拉 -->
                  <ElFormItem
                    v-else-if="activeItem.type === 'select' && activeItem.props?.multiple"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElSelect
                      v-model="activeItem.defaultValue"
                      :placeholder="$t('form-design.attribute.defaultValuePlaceholder')"
                      :loading="loadingDefaultValueOptions"
                      clearable
                      multiple
                      collapse-tags
                      class="w-full"
                      size="small"
                      @focus="refreshDefaultValueOptions"
                    >
                      <ElOption
                        v-for="opt in defaultValueOptionsForSelect"
                        :key="opt.value"
                        :label="opt.label"
                        :value="opt.value"
                      />
                    </ElSelect>
                  </ElFormItem>

                  <!-- 复选框 -->
                  <ElFormItem
                    v-else-if="activeItem.type === 'checkbox'"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElSelect
                      v-model="activeItem.defaultValue"
                      :placeholder="$t('form-design.attribute.defaultValuePlaceholder')"
                      :loading="loadingDefaultValueOptions"
                      clearable
                      multiple
                      collapse-tags
                      class="w-full"
                      size="small"
                      @focus="refreshDefaultValueOptions"
                    >
                      <ElOption
                        v-for="opt in defaultValueOptionsForSelect"
                        :key="opt.value"
                        :label="opt.label"
                        :value="opt.value"
                      />
                    </ElSelect>
                  </ElFormItem>

                  <!-- 开关 -->
                  <ElFormItem
                    v-else-if="activeItem.type === 'switch'"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElSwitch v-model="activeItem.defaultValue" />
                  </ElFormItem>

                  <!-- 日期 -->
                  <ElFormItem
                    v-else-if="activeItem.type === 'date'"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElDatePicker
                      v-model="activeItem.defaultValue"
                      :type="activeItem.props?.type || 'date'"
                      :format="activeItem.props?.format || 'YYYY-MM-DD'"
                      :value-format="activeItem.props?.valueFormat || 'YYYY-MM-DD'"
                      :placeholder="$t('form-design.attribute.defaultValuePlaceholder')"
                      class="!w-full"
                      size="small"
                    />
                  </ElFormItem>

                  <!-- 时间 -->
                  <ElFormItem
                    v-else-if="activeItem.type === 'time'"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElTimePicker
                      v-model="activeItem.defaultValue"
                      :format="activeItem.props?.format || 'HH:mm:ss'"
                      :value-format="activeItem.props?.valueFormat || 'HH:mm:ss'"
                      :placeholder="$t('form-design.attribute.defaultValuePlaceholder')"
                      class="!w-full"
                      size="small"
                    />
                  </ElFormItem>

                  <!-- 滑块 -->
                  <ElFormItem
                    v-else-if="activeItem.type === 'slider'"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElInputNumber
                      v-model="activeItem.defaultValue"
                      :min="activeItem.props?.min || 0"
                      :max="activeItem.props?.max || 100"
                      :step="activeItem.props?.step || 1"
                      controls-position="right"
                      class="w-full"
                      size="small"
                    />
                  </ElFormItem>

                  <!-- 评分 -->
                  <ElFormItem
                    v-else-if="activeItem.type === 'rate'"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElRate
                      v-model="activeItem.defaultValue"
                      :max="activeItem.props?.max || 5"
                      :allow-half="activeItem.props?.allowHalf"
                    />
                  </ElFormItem>

                  <!-- 颜色 -->
                  <ElFormItem
                    v-else-if="activeItem.type === 'color'"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElColorPicker
                      v-model="activeItem.defaultValue"
                      :show-alpha="activeItem.props?.showAlpha"
                    />
                  </ElFormItem>

                  <!-- 级联/树选择/选择器类（文本输入模式） -->
                  <ElFormItem
                    v-else-if="['cascader', 'tree-select', 'dept-selector', 'user-selector', 'role-selector', 'post-selector', 'region-selector', 'table-selector', 'form-selector', 'qrcode-generator'].includes(activeItem.type)"
                    :label="$t('form-design.attribute.defaultValue')"
                  >
                    <ElInput
                      v-model="activeItem.defaultValue"
                      :placeholder="$t('form-design.attribute.defaultValuePlaceholder')"
                      clearable
                      size="small"
                    />
                    <div class="mt-1 text-xs text-[var(--el-text-color-placeholder)]">
                      {{ $t('form-design.attribute.defaultValueIdHint') }}
                    </div>
                  </ElFormItem>
                </div>
              </template>

              <!-- 正则校验 -->
              <div v-if="showValidation" class="mt-4">
                <div
                  class="group-title mb-2 flex items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)]"
                >
                  <span>{{ $t('form-design.attribute.regex') }}</span>
                  <ElButton
                    type="primary"
                    link
                    style="font-size: smaller"
                    @click="addRegRule"
                  >
                    {{ $t('form-design.attribute.addRegRule') }}
                  </ElButton>
                </div>
                <div
                  v-for="(rule, index) in activeItem.regList"
                  :key="index"
                  class="relative mb-4 rounded border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-light)] p-2"
                >
                  <ElButton
                    type="danger"
                    link
                    size="small"
                    class="absolute right-1 top-1"
                    @click="
                      activeItem?.regList && activeItem.regList.splice(index as any, 1)
                    "
                  >
                    <ElIcon class="w-3"><Close /></ElIcon>
                  </ElButton>

                  <ElFormItem :label="$t('form-design.attribute.regex')" class="mb-1">
                    <ElSelect
                      :model-value="getPatternSelectValue(rule.pattern)"
                      @change="(val: string) => handlePatternChange(val, rule)"
                      :placeholder="$t('form-design.attribute.regex')"
                    >
                      <ElOption
                        v-for="item in REG_PATTERNS"
                        :key="item.pattern"
                        :label="item.label"
                        :value="item.pattern"
                      />
                    </ElSelect>
                  </ElFormItem>

                  <ElFormItem :label="$t('form-design.attribute.pattern')" class="mb-1">
                    <ElInput v-model="rule.pattern" placeholder="/^...$/ " />
                  </ElFormItem>

                  <ElFormItem :label="$t('form-design.attribute.errorMessage')" class="mb-0">
                    <ElInput
                      v-model="rule.message"
                      :placeholder="$t('form-design.attribute.errorMessage')"
                    />
                  </ElFormItem>
                </div>
                <div
                  v-if="!activeItem.regList || activeItem.regList.length === 0"
                  class="py-2 text-center text-xs text-[var(--el-text-color-placeholder)]"
                >
                  {{ $t('form-design.attribute.noValidationRuleTip') }}
                </div>
              </div>

              <!-- 跨字段校验 -->
              <div v-if="showCrossValidation" class="mt-4">
                <div
                  class="group-title mb-2 flex items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)]"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.crossValidation.title') }}</span>
                  <ElButton type="primary" link size="small" @click="addCrossValidation">
                    {{ $t('form-design.add') }}
                  </ElButton>
                </div>
                <div
                  v-for="(cv, index) in activeItem.props.crossValidations"
                  :key="index"
                  class="relative mb-4 rounded border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-light)] p-2"
                >
                  <ElButton
                    type="danger"
                    link
                    size="small"
                    class="absolute right-1 top-1"
                    @click="removeCrossValidation(index)"
                  >
                    <ElIcon class="w-3"><Close /></ElIcon>
                  </ElButton>
                  <ElFormItem :label="$t('form-design.attribute.crossValidation.targetField')" class="!mb-2">
                    <ElSelect v-model="cv.targetField" :placeholder="$t('ui.placeholder.select')" size="small">
                      <ElOption
                        v-for="f in crossValidationFields"
                        :key="f.field"
                        :label="`${f.label} (${f.field})`"
                        :value="f.field"
                      />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.crossValidation.operator')" class="!mb-2">
                    <ElSelect v-model="cv.operator" size="small">
                      <ElOption
                        v-for="op in crossValidationOperators"
                        :key="op.value"
                        :label="op.label"
                        :value="op.value"
                      />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.crossValidation.errorMessage')" class="!mb-0">
                    <ElInput
                      v-model="cv.message"
                      size="small"
                      :placeholder="$t('form-design.attribute.crossValidation.errorMessagePlaceholder')"
                    />
                  </ElFormItem>
                </div>
                <div
                  v-if="!activeItem.props.crossValidations || activeItem.props.crossValidations.length === 0"
                  class="py-2 text-center text-xs text-[var(--el-text-color-placeholder)]"
                >
                  {{ $t('form-design.attribute.crossValidation.noRuleTip') }}
                </div>
              </div>

              <!-- 唯一性校验 -->
              <div v-if="showUniqueCheck" class="mt-4">
                <div
                  class="group-title mb-2 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('unique-check')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.uniqueCheck.title') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('unique-check')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('unique-check')">
                  <ElFormItem :label="$t('form-design.attribute.uniqueCheck.enable')">
                    <ElSwitch v-model="activeItem.props.uniqueCheck" />
                    <ElTooltip :content="$t('form-design.attribute.uniqueCheck.enableTip')" placement="top">
                      <CircleHelp class="ml-1 cursor-help align-middle text-[var(--el-text-color-placeholder)]" :size="14" />
                    </ElTooltip>
                  </ElFormItem>
                  <ElFormItem
                    v-if="activeItem.props.uniqueCheck"
                    :label="$t('form-design.attribute.uniqueCheck.message')"
                  >
                    <ElInput
                      v-model="activeItem.props.uniqueCheckMessage"
                      size="small"
                      :placeholder="$t('form-design.attribute.uniqueCheck.messagePlaceholder')"
                    />
                  </ElFormItem>
                </div>
              </div>

              <!-- 高级设置 -->
              <!-- <div v-if="!isLayoutComponent"> -->
              <div>
                <div
                  class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                  @click="toggleSection('advanced')"
                >
                  <span class="font-bold">{{ $t('form-design.attribute.advancedSettings') }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('advanced')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('advanced')">
                  <ElFormItem :label="$t('form-design.attribute.showCondition')">
                    <ConditionBuilder
                      v-model="activeItem.showCondition"
                      :fields="dependableFields"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-design.attribute.hideCondition')">
                    <ConditionBuilder
                      v-model="activeItem.hideCondition"
                      :fields="dependableFields"
                    />
                  </ElFormItem>
                </div>
              </div>
            </ElForm>
          </div>
        </ElScrollbar>
        <div
          v-else
          class="flex h-full items-center justify-center p-4 text-sm text-[var(--el-text-color-placeholder)]"
        >
          {{ $t('form-design.attribute.selectComponentTip') }}
        </div>
      </div>

      <div v-else-if="activeTab === 'form'" class="h-full">
        <ElScrollbar class="h-full">
          <div class="p-4">
            <ElForm label-position="top" size="small">
              <!-- 基础属性 -->
              <div
                class="group-title mb-2 flex cursor-pointer select-none items-center justify-between border-b border-[var(--el-border-color-lighter)] pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                @click="toggleSection('form-basic')"
              >
                <span class="font-bold">{{ $t('form-design.attribute.basicSettings') }}</span>
                <ElIcon class="h-4 w-4">
                  <ArrowDown v-if="activeSections.includes('form-basic')" />
                  <ArrowRight v-else />
                </ElIcon>
              </div>
              <div v-show="activeSections.includes('form-basic')">
                <ElFormItem :label="$t('form-design.attribute.align')">
                  <ElRadioGroup v-model="formConf.labelPosition">
                    <ElRadioButton label="left">{{ $t('form-design.attribute.location.left') }}</ElRadioButton>
                    <ElRadioButton label="right">{{ $t('form-design.attribute.location.right') }}</ElRadioButton>
                    <ElRadioButton label="top">{{ $t('form-design.attribute.location.top') }}</ElRadioButton>
                  </ElRadioGroup>
                </ElFormItem>

                <ElFormItem :label="$t('form-design.attribute.labelWidth')">
                  <ElInputNumber
                    v-model="formConf.labelWidth"
                    :min="0"
                    :step="10"
                    controls-position="right"
                    class="w-full"
                  />
                </ElFormItem>

                <ElFormItem :label="$t('form-design.attribute.componentSize')">
                  <ElSelect v-model="formConf.size" class="w-full">
                    <ElOption :label="$t('form-design.attribute.default')" value="default" />
                    <ElOption :label="$t('form-design.attribute.large')" value="large" />
                    <ElOption :label="$t('form-design.attribute.small')" value="small" />
                  </ElSelect>
                </ElFormItem>

                <ElFormItem label="全局禁用">
                  <ElSwitch v-model="formConf.disabled" />
                  <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">
                    开启后所有表单项将禁用
                  </div>
                </ElFormItem>
              </div>

              <!-- 布局间距 -->
              <div
                class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b border-[var(--el-border-color-lighter)] pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                @click="toggleSection('form-spacing')"
              >
                <span class="font-bold">布局间距</span>
                <ElIcon class="h-4 w-4">
                  <ArrowDown v-if="activeSections.includes('form-spacing')" />
                  <ArrowRight v-else />
                </ElIcon>
              </div>
              <div v-show="activeSections.includes('form-spacing')">
                <!-- 表单内边距（四方向） -->
                <div class="mb-3">
                  <div class="mb-1 flex items-center justify-between">
                    <span class="text-xs text-[var(--el-text-color-regular)]">{{ $t('form-design.formProps.formPadding') }}</span>
                    <ElButton
                      :type="formConf.formPaddingLinked ? 'primary' : 'default'"
                      link
                      size="small"
                      @click="formConf.formPaddingLinked = !formConf.formPaddingLinked"
                    >
                      <span class="text-xs">{{ formConf.formPaddingLinked ? $t('form-design.formProps.linked') : $t('form-design.formProps.unlinked') }}</span>
                    </ElButton>
                  </div>
                  <div class="grid grid-cols-2 gap-2">
                    <ElFormItem :label="$t('form-design.formProps.top')" class="!mb-1">
                      <ElInputNumber v-model="formConf.formPaddingTop" :min="0" :max="100" :step="4" controls-position="right" class="w-full" size="small" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.formProps.bottom')" class="!mb-1">
                      <ElInputNumber v-model="formConf.formPaddingBottom" :min="0" :max="100" :step="4" controls-position="right" class="w-full" size="small" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.formProps.left')" class="!mb-1">
                      <ElInputNumber v-model="formConf.formPaddingLeft" :min="0" :max="100" :step="4" controls-position="right" class="w-full" size="small" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.formProps.right')" class="!mb-1">
                      <ElInputNumber v-model="formConf.formPaddingRight" :min="0" :max="100" :step="4" controls-position="right" class="w-full" size="small" />
                    </ElFormItem>
                  </div>
                </div>

                <!-- 表单外边距（四方向） -->
                <div class="mb-3">
                  <div class="mb-1 flex items-center justify-between">
                    <span class="text-xs text-[var(--el-text-color-regular)]">{{ $t('form-design.formProps.formMargin') }}</span>
                    <ElButton
                      :type="formConf.formMarginLinked ? 'primary' : 'default'"
                      link
                      size="small"
                      @click="formConf.formMarginLinked = !formConf.formMarginLinked"
                    >
                      <span class="text-xs">{{ formConf.formMarginLinked ? $t('form-design.formProps.linked') : $t('form-design.formProps.unlinked') }}</span>
                    </ElButton>
                  </div>
                  <div class="grid grid-cols-2 gap-2">
                    <ElFormItem :label="$t('form-design.formProps.top')" class="!mb-1">
                      <ElInputNumber v-model="formConf.formMarginTop" :min="0" :max="100" :step="4" controls-position="right" class="w-full" size="small" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.formProps.bottom')" class="!mb-1">
                      <ElInputNumber v-model="formConf.formMarginBottom" :min="0" :max="100" :step="4" controls-position="right" class="w-full" size="small" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.formProps.left')" class="!mb-1">
                      <ElInputNumber v-model="formConf.formMarginLeft" :min="0" :max="100" :step="4" controls-position="right" class="w-full" size="small" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-design.formProps.right')" class="!mb-1">
                      <ElInputNumber v-model="formConf.formMarginRight" :min="0" :max="100" :step="4" controls-position="right" class="w-full" size="small" />
                    </ElFormItem>
                  </div>
                </div>

                <ElFormItem label="表单项间距">
                  <ElInputNumber
                    v-model="formConf.itemSpacing"
                    :min="0"
                    :max="50"
                    :step="2"
                    controls-position="right"
                    class="w-full"
                  />
                  <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">
                    表单项之间的垂直间距（px）
                  </div>
                </ElFormItem>
              </div>

              <!-- 容器尺寸 -->
              <div
                class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b border-[var(--el-border-color-lighter)] pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                @click="toggleSection('form-size')"
              >
                <span class="font-bold">容器尺寸</span>
                <ElIcon class="h-4 w-4">
                  <ArrowDown v-if="activeSections.includes('form-size')" />
                  <ArrowRight v-else />
                </ElIcon>
              </div>
              <div v-show="activeSections.includes('form-size')">
                <ElFormItem label="表单宽度">
                  <ElInput
                    v-model="formConf.formWidth"
                    placeholder="100% 或 800px"
                  />
                  <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">
                    支持百分比或像素值
                  </div>
                </ElFormItem>

                <ElFormItem label="最大宽度">
                  <ElInput
                    v-model="formConf.formMaxWidth"
                    placeholder="留空表示不限制"
                  />
                  <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">
                    限制表单最大宽度（如：1200px）
                  </div>
                </ElFormItem>
              </div>

              <!-- 外观样式 -->
              <div
                class="group-title mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b border-[var(--el-border-color-lighter)] pb-2 text-xs text-[var(--el-text-color-regular)] hover:text-[var(--el-color-primary)]"
                @click="toggleSection('form-style')"
              >
                <span class="font-bold">外观样式</span>
                <ElIcon class="h-4 w-4">
                  <ArrowDown v-if="activeSections.includes('form-style')" />
                  <ArrowRight v-else />
                </ElIcon>
              </div>
              <div v-show="activeSections.includes('form-style')">
                <ElFormItem label="背景颜色">
                  <div class="flex items-center gap-2">
                    <ElColorPicker
                      v-model="formConf.formBackground"
                      show-alpha
                      :predefine="[
                        'rgba(255, 255, 255, 1)',
                        'rgba(245, 247, 250, 1)',
                        'rgba(64, 158, 255, 0.1)',
                        'rgba(103, 194, 58, 0.1)',
                        'rgba(230, 162, 60, 0.1)',
                        'rgba(245, 108, 108, 0.1)',
                      ]"
                    />
                    <ElInput
                      v-model="formConf.formBackground"
                      placeholder="留空使用默认，支持 rgba"
                      class="flex-1"
                    />
                  </div>
                  <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">
                    支持透明度，如：rgba(255, 255, 255, 0.5)
                  </div>
                </ElFormItem>

                <ElFormItem label="显示边框">
                  <ElSwitch v-model="formConf.formBorder" />
                </ElFormItem>

                <ElFormItem label="边框圆角" v-if="formConf.formBorder">
                  <ElInputNumber
                    v-model="formConf.formBorderRadius"
                    :min="0"
                    :max="50"
                    :step="2"
                    controls-position="right"
                    class="w-full"
                  />
                </ElFormItem>

                <ElFormItem label="显示阴影">
                  <ElSwitch v-model="formConf.formShadow" />
                  <div class="mt-1 text-xs text-[var(--el-text-color-secondary)]">
                    为表单容器添加阴影效果
                  </div>
                </ElFormItem>
              </div>
            </ElForm>
          </div>
        </ElScrollbar>
      </div>
    </div>

    <!-- 数据源编辑器弹窗 -->
    <OptionsEditor
      v-if="activeItem"
      v-model="showOptionsEditor"
      :data="activeItem.options || []"
      @confirm="handleOptionsConfirm"
    />
  </div>
</template>

<style scoped>
:deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
}
</style>
