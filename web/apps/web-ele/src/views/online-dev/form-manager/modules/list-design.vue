<script lang="ts" setup>
import type { PublishedFormSimple } from '#/api/online-dev/form-manager';
import type { ZqTabItem } from '#/components/zq-tabs/index';

import { computed, onMounted, ref } from 'vue';

import {
  GripVertical,
  LayoutGrid,
  Search,
  TableProperties,
  Trash2,
} from '@vben/icons';
import { $t } from '@vben/locales';

import { ArrowDown, ArrowRight } from '@element-plus/icons-vue';
import {
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElOption,
  ElRadio,
  ElRadioGroup,
  ElScrollbar,
  ElSelect,
  ElSwitch,
  ElTag,
  ElDatePicker,
} from 'element-plus';
import draggable from 'vuedraggable';

import {
  getFormByCodeApi,
  getPublishedFormsSimpleApi,
} from '#/api/online-dev/form-manager';
import { getPageListApi } from '#/api/online-dev/page-manager';
import { DeptSelector } from '#/components/zq-form/dept-selector';
import { FormSelector } from '#/components/zq-form/form-selector';
import { PostSelector } from '#/components/zq-form/post-selector';
import { RoleSelector } from '#/components/zq-form/role-selector';
import { UserSelector } from '#/components/zq-form/user-selector';
import { ZqIconPicker } from '#/components/zq-form/zq-icon-picker';
import { ZqTabs } from '#/components/zq-tabs/index';
import { useAppContextStore } from '#/store/app-context';

// 从表单设计获取的字段数据
const props = defineProps<{
  formFields?: any[];
  formType?: 'normal' | 'workflow';
  subTables?: Array<{
    alias?: string;
    foreignKey: string;
    relatedField?: string;
    tableName: string;
  }>;
}>();

// 是否是流程表单
const isWorkflowForm = computed(() => props.formType === 'workflow');

// 确保有数据，避免为空报错
const availableFields = computed(() => props.formFields || []);

// 查询字段配置 (左侧表格数据)
const queryFields = ref<any[]>([]);

// 列表字段配置 (左侧表格数据)
const listColumns = ref<any[]>([]);

// 右侧 Checkbox 选中的值 (用于同步状态)
const selectedQueryFieldKeys = computed({
  get: () => queryFields.value.map((item) => item.field),
  set: (val) => {
    // 这里 set 主要用于处理全选等逻辑，实际增删通过 change 事件单独处理更可控
    // 但为了配合 ElCheckboxGroup v-model，我们需要处理值的变化
    const currentKeys = queryFields.value.map((item) => item.field);
    // 找出新增的
    val.forEach((key) => {
      if (!currentKeys.includes(key)) {
        const field = availableFields.value.find((f) => f.field === key);
        if (field) addQueryField(field);
      }
    });
    // 找出移除的
    currentKeys.forEach((key) => {
      if (!val.includes(key)) {
        const index = queryFields.value.findIndex((item) => item.field === key);
        if (index !== -1) removeQueryField(index);
      }
    });
  },
});

const selectedListColumnKeys = computed({
  get: () => listColumns.value.map((item) => item.field),
  set: (val) => {
    const currentKeys = listColumns.value.map((item) => item.field);
    val.forEach((key) => {
      if (!currentKeys.includes(key)) {
        const field = availableFields.value.find((f) => f.field === key);
        if (field) addListColumn(field);
      }
    });
    currentKeys.forEach((key) => {
      if (!val.includes(key)) {
        const index = listColumns.value.findIndex((item) => item.field === key);
        if (index !== -1) removeListColumn(index);
      }
    });
  },
});

const isQueryAllSelected = computed({
  get: () =>
    availableFields.value.length > 0 &&
    selectedQueryFieldKeys.value.length === availableFields.value.length,
  set: (val) => {
    selectedQueryFieldKeys.value = val
      ? availableFields.value.map((item) => item.field)
      : [];
  },
});

const isQueryIndeterminate = computed(() => {
  return (
    selectedQueryFieldKeys.value.length > 0 &&
    selectedQueryFieldKeys.value.length < availableFields.value.length
  );
});

const isListAllSelected = computed({
  get: () =>
    availableFields.value.length > 0 &&
    selectedListColumnKeys.value.length === availableFields.value.length,
  set: (val) => {
    selectedListColumnKeys.value = val
      ? availableFields.value.map((item) => item.field)
      : [];
  },
});

const isListIndeterminate = computed({
  get: () =>
    selectedListColumnKeys.value.length > 0 &&
    selectedListColumnKeys.value.length < availableFields.value.length,
  set: () => {}, // dummy setter
});

// 列表属性配置
const listSettings = ref({
  // 列表类型：table 或 card
  listType: 'table' as 'card' | 'table',
  // 容器类型：dialog、drawer、page 或 layout
  containerType: 'drawer' as 'dialog' | 'drawer' | 'layout' | 'page',
  // Table 属性
  table: {
    showPagination: true,
    pageSize: 20,
    showIndex: true,
    showSelection: true,
    stripe: true,
    border: true, // 默认开启边框以支持列宽拖拽
    size: 'default' as 'default' | 'large' | 'small',
    height: 'auto', // auto, 400, 500, 600 等
    // 排序规则（支持多字段排序）
    defaultSort: [] as Array<{
      field: string;
      order: 'asc' | 'desc';
    }>,
    // 默认过滤条件
    defaultFilters: [] as Array<{
      field: string;
      operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in' | 'null' | 'not_null';
      value: string;
    }>,
    // 表尾统计配置
    showSummary: false,
    summaryType: 'sum' as 'avg' | 'count' | 'max' | 'min' | 'sum',
    summaryPrecision: 2,
  },
  // Dialog 属性
  dialog: {
    width: '800px',
    fullscreen: false,
    draggable: true,
    closeOnClickModal: false,
    closeOnPressEscape: true,
  },
  // Drawer 属性
  drawer: {
    size: '800px',
    direction: 'rtl' as 'btt' | 'ltr' | 'rtl' | 'ttb',
    withHeader: true,
    closeOnClickModal: false,
    closeOnPressEscape: true,
  },
  // Page 属性
  page: {
    showBackButton: true,
    openInNewTab: true,
  },
  // Layout 属性（在系统布局中显示）
  layout: {
    showBackButton: true,
    renderMode: 'condition' as 'condition' | 'route', // 渲染模式：route-路由渲染，condition-条件渲染
  },
  // 按钮显示
  buttons: {
    showAdd: true,
    showEdit: true,
    showDelete: true,
    showView: true,
    showExport: true,
    showImport: false,
    showBatchDelete: true,
  },
  // Card 属性
  card: {
    columns: 4, // 每行显示数量 (1-6)
    gap: 16, // 卡片间距 (px)
    shadow: 'hover' as 'always' | 'hover' | 'never',
    pageSize: 12, // 每页数量
    showPagination: true, // 显示分页
  },
  // 卡片字段映射
  cardFields: {
    icon: null as any, // 图标字段
    title: null as any, // 标题字段（必填）
    subtitle: null as any, // 副标题字段
    description: null as any, // 描述字段
    tags: [] as any[], // 标签字段（最多3个）
    footerLeft: null as any, // 底部左侧字段
    footerRight: null as any, // 底部右侧字段
  },
  // 新增/编辑时显示确认按钮（流程表单默认关闭，其他类型默认打开）
  showConfirmButton: true,
  // 保存后行为：close-关闭返回列表, editMode-切换编辑模式, continueAdd-清空继续新增
  afterSaveAction: 'close' as 'close' | 'continueAdd' | 'editMode',
  // 新增时可发起流程（仅流程表单有效，流程表单默认打开）
  enableStartWorkflowOnAdd: false,
  // 子表操作按钮（用于打开子表独立表单）
  subTableButtons: [] as Array<{
    buttonIcon?: string; // 按钮图标
    buttonText: string; // 按钮文本
    buttonType?:
      | 'danger'
      | 'default'
      | 'info'
      | 'primary'
      | 'success'
      | 'warning';
    containerConfig: {
      direction?: 'btt' | 'ltr' | 'rtl' | 'ttb';
      fullscreen?: boolean;
      // Layout 配置
      renderMode?: 'condition' | 'route';
      // Drawer 配置
      size?: string;
      // Dialog 配置
      width?: string;
    };
    containerType: 'dialog' | 'drawer' | 'layout'; // 容器类型
    foreignKeyField?: string; // 外键字段名（自动从子表配置获取）
    id: string;
    sort: number;
    subFormCode: string; // 子表独立表单编码
    subTableName: string; // 子表名（对应数据源配置中的子表）
  }>,
  // 自定义按钮
  customButtons: [] as Array<{
    actionConfig: {
      apiHeaders?: Record<string, string>;
      apiMethod?: 'DELETE' | 'GET' | 'POST' | 'PUT';
      apiParams?: Record<string, any>;
      // api 类型
      apiUrl?: string;
      confirmMessage?: string;
      confirmTitle?: string;
      errorMessage?: string;
      // event 类型
      eventName?: string;
      openInNewTab?: boolean;
      reloadAfterSuccess?: boolean;
      successMessage?: string;
      // link 类型
      url?: string;
    };
    // 操作类型
    actionType:
      | 'agent'
      | 'api'
      | 'event'
      | 'generate_document'
      | 'link'
      | 'page';
    badge?: number | string;
    badgeType?: 'danger' | 'info' | 'primary' | 'success' | 'warning';
    circle?: boolean;
    // 状态控制
    disabled?: boolean;
    disabledCondition?: string;
    icon: string;
    id: string;
    link?: boolean;
    loading?: boolean;
    name: string;
    permissionCode?: string;
    // 样式属性
    plain?: boolean;
    position: 'row' | 'toolbar' | 'tools';
    round?: boolean;
    showCondition?: string;
    size?: 'default' | 'large' | 'small';
    sort: number;
    text?: boolean;
    // 提示和徽标
    tooltip?: string;
    type: 'danger' | 'default' | 'info' | 'primary' | 'success' | 'warning';
  }>,
  // 树形表格配置
  tree: {
    enabled: false, // 是否启用树形表格
    parentField: 'parent_id', // 父节点字段名（可选择其他字段）
    lazy: false, // 是否懒加载（关闭时一次加载全部，开启时按需加载子节点）
    defaultExpandAll: false, // 默认展开所有（仅非懒加载模式有效）
    indent: 16, // 缩进像素
    checkStrictly: false, // 父子节点不关联选择
  },
});

const activeTab = ref('query');

// Tabs 配置
const tabItems: ZqTabItem[] = [
  {
    key: 'query',
    label: $t('form-manager.listDesign.queryTab'),
    icon: undefined,
  },
  {
    key: 'columns',
    label: $t('form-manager.listDesign.listTab'),
    icon: undefined,
  },
  {
    key: 'properties',
    label: $t('form-manager.listDesign.propertyTab'),
    icon: undefined,
  },
];

// 折叠状态
const activeSections = ref([
  'table',
  'tree',
  'card',
  'container',
  'dialog',
  'drawer',
  'page',
  'layout',
  'buttons',
  'subTableButtons',
]);

const toggleSection = (section: string) => {
  const index = activeSections.value.indexOf(section);
  if (index === -1) {
    activeSections.value.push(section);
  } else {
    activeSections.value.splice(index, 1);
  }
};

function removeQueryField(index: number) {
  queryFields.value.splice(index, 1);
}

function removeListColumn(index: number) {
  const removedField = listColumns.value[index];
  listColumns.value.splice(index, 1);
  // 同步清除卡片字段配置中引用该字段的区域
  if (removedField) {
    removeCardFieldByFieldName(removedField.field);
  }
}

// 根据字段名清除卡片区域中引用该字段的配置
function removeCardFieldByFieldName(fieldName: string) {
  const cf = listSettings.value.cardFields;
  if (cf.icon?.field === fieldName) cf.icon = null;
  if (cf.title?.field === fieldName) cf.title = null;
  if (cf.subtitle?.field === fieldName) cf.subtitle = null;
  if (cf.description?.field === fieldName) cf.description = null;
  if (cf.footerLeft?.field === fieldName) cf.footerLeft = null;
  if (cf.footerRight?.field === fieldName) cf.footerRight = null;
  cf.tags = cf.tags.filter((t: any) => t.field !== fieldName);
  // 如果当前选中的卡片区域对应的字段被移除，清除选中状态
  if (selectedCardArea.value) {
    const areaField = getCardAreaField(selectedCardArea.value);
    if (!areaField || areaField.field === fieldName) {
      selectedCardArea.value = null;
    }
  }
}

// 添加排序字段
function addSortField() {
  listSettings.value.table.defaultSort.push({
    field: '',
    order: 'desc',
  });
}

// 删除排序字段
function removeSortField(index: number) {
  listSettings.value.table.defaultSort.splice(index, 1);
}

// 添加过滤条件
function addFilterCondition() {
  listSettings.value.table.defaultFilters.push({
    field: '',
    operator: 'eq',
    value: '',
  });
}

// 删除过滤条件
function removeFilterCondition(index: number) {
  listSettings.value.table.defaultFilters.splice(index, 1);
}

// 判断过滤操作符是否需要值输入
function filterOperatorNeedsValue(operator: string): boolean {
  return !['null', 'not_null'].includes(operator);
}

// 获取过滤条件中选中字段的配置
function getFilterFieldConfig(fieldName: string) {
  return availableFields.value.find((f: any) => f.field === fieldName);
}

// 获取过滤条件值输入的类型（根据字段组件类型）
function getFilterValueType(fieldName: string): string {
  const fieldConfig = getFilterFieldConfig(fieldName);
  if (!fieldConfig) return 'text';
  const comp = fieldConfig.component;
  if (comp === 'switch') return 'boolean';
  if (['number', 'slider', 'rate', 'stepper'].includes(comp)) return 'number';
  if (['select', 'radio', 'checkbox'].includes(comp) && fieldConfig.options?.length > 0) return 'select';
  if (['date', 'date-picker'].includes(comp)) return 'date';
  if (['datetime', 'datetime-picker'].includes(comp)) return 'datetime';
  if (['time', 'time-picker'].includes(comp)) return 'time';
  if (['user-selector', 'user-select'].includes(comp)) return 'user';
  if (['department-selector', 'dept-selector', 'dept-select'].includes(comp)) return 'dept';
  if (['position-selector', 'post-selector'].includes(comp)) return 'post';
  if (['role-selector'].includes(comp)) return 'role';
  if (comp === 'form-selector') return 'form-selector';
  return 'text';
}

// 获取过滤条件字段的选项列表
function getFilterFieldOptions(fieldName: string) {
  const fieldConfig = getFilterFieldConfig(fieldName);
  return fieldConfig?.options || [];
}

// Agent 列表管理
// const publishedAgents = ref<AgentListItem[]>([]);
const agentsLoading = ref(false);

// 加载已发布的 Agent 列表
async function loadPublishedAgents() {
  try {
    agentsLoading.value = true;
    publishedAgents.value = await getPublishedAgentsApi();
  } catch (error) {
    console.error('加载 Agent 列表失败:', error);
    publishedAgents.value = [];
  } finally {
    agentsLoading.value = false;
  }
}

// 页面列表管理
const appContextStore = useAppContextStore();
const publishedPages = ref<Array<{ code: string; name: string }>>([]);
const pagesLoading = ref(false);

// 加载已发布的页面列表
async function loadPublishedPages() {
  try {
    pagesLoading.value = true;
    const params: any = {
      page: 1,
      pageSize: 100,
      status: 'published',
    };

    // 只有当 applicationId 存在时才添加
    if (appContextStore.currentApp?.id) {
      params.applicationId = appContextStore.currentApp.id;
    }

    console.log('加载页面列表，参数:', params);
    const res = await getPageListApi(params);
    console.log('页面列表响应:', res);

    if (res && Array.isArray(res.items)) {
      publishedPages.value = res.items.map((item: any) => ({
        code: item.code,
        name: item.name,
      }));
      console.log('已发布页面列表:', publishedPages.value);
    } else {
      console.warn('页面列表响应格式不正确:', res);
      publishedPages.value = [];
    }
  } catch (error) {
    console.error('加载页面列表失败:', error);
    publishedPages.value = [];
  } finally {
    pagesLoading.value = false;
  }
}

// 已发布表单列表管理（用于子表操作按钮选择子表单）
const publishedForms = ref<PublishedFormSimple[]>([]);
const formsLoading = ref(false);

// 加载已发布的表单列表
async function loadPublishedForms() {
  try {
    formsLoading.value = true;
    publishedForms.value = await getPublishedFormsSimpleApi(
      appContextStore.currentApp?.id,
    );
  } catch (error) {
    console.error('加载表单列表失败:', error);
    publishedForms.value = [];
  } finally {
    formsLoading.value = false;
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadPublishedAgents();
  loadPublishedPages();
  loadPublishedForms();
});

// 子表操作按钮管理
const expandedSubTableButtons = ref<Set<string>>(new Set());

function toggleSubTableButtonExpand(buttonId: string) {
  if (expandedSubTableButtons.value.has(buttonId)) {
    expandedSubTableButtons.value.delete(buttonId);
  } else {
    expandedSubTableButtons.value.add(buttonId);
  }
}

function addSubTableButton() {
  const id = `sub_table_btn_${Date.now()}`;
  listSettings.value.subTableButtons.push({
    id,
    subTableName: '',
    subFormCode: '',
    buttonText: '',
    buttonIcon: 'lucide:list',
    buttonType: 'primary',
    containerType: 'layout',
    containerConfig: {
      width: '80%',
      size: '70%',
      direction: 'rtl',
      renderMode: 'condition',
    },
    foreignKeyField: '',
    sort: listSettings.value.subTableButtons.length,
  });
  // 新添加的按钮默认展开
  expandedSubTableButtons.value.add(id);
}

function removeSubTableButton(index: number) {
  const button = listSettings.value.subTableButtons[index];
  if (button) {
    expandedSubTableButtons.value.delete(button.id);
  }
  listSettings.value.subTableButtons.splice(index, 1);
}

// 当选择子表时，自动填充外键字段
function onSubTableSelect(button: any, tableName: string) {
  const subTable = props.subTables?.find((t) => t.tableName === tableName);
  if (subTable) {
    button.foreignKeyField = subTable.foreignKey;
    // 如果没有设置按钮文本，使用子表别名
    if (!button.buttonText) {
      button.buttonText = subTable.alias || tableName;
    }
  }
}

// 自定义按钮管理
// 按钮展开/折叠状态（默认全部折叠）
const expandedButtons = ref<Set<string>>(new Set());

function toggleButtonExpand(buttonId: string) {
  if (expandedButtons.value.has(buttonId)) {
    expandedButtons.value.delete(buttonId);
  } else {
    expandedButtons.value.add(buttonId);
  }
}

function addCustomButton() {
  const id = `custom_btn_${Date.now()}`;
  listSettings.value.customButtons.push({
    id,
    name: $t('form-manager.listDesign.defaultButtonName'),
    icon: 'lucide:mouse-pointer-click',
    type: 'primary',
    position: 'toolbar',
    actionType: 'link',
    actionConfig: {},
    sort: listSettings.value.customButtons.length,
  });
  // 新添加的按钮默认展开
  expandedButtons.value.add(id);
}

function addGenerateDocumentButton() {
  const id = `custom_btn_${Date.now()}`;
  listSettings.value.customButtons.push({
    id,
    name: $t('form-manager.generateDocument.buttonLabel'),
    icon: 'lucide:file-text',
    type: 'primary',
    position: 'row',
    actionType: 'generate_document',
    actionConfig: {},
    sort: listSettings.value.customButtons.length,
  });
  // 新添加的按钮默认展开
  expandedButtons.value.add(id);
}

function removeCustomButton(index: number) {
  const button = listSettings.value.customButtons[index];
  if (button) {
    expandedButtons.value.delete(button.id);
  }
  listSettings.value.customButtons.splice(index, 1);
}

// 根据表单组件类型映射查询组件类型
function mapQueryComponent(componentType: string): string {
  // 用户/部门/岗位/表单/表格选择器保持原组件
  if (
    [
      'department-selector',
      'dept-select',
      'dept-selector',
      'form-selector',
      'position-selector',
      'post-selector',
      'table-selector',
      'user-select',
      'user-selector',
    ].includes(componentType)
  ) {
    return componentType;
  }
  // 开关组件映射为 select（是/否下拉选择）
  if (componentType === 'switch') {
    return 'select';
  }
  // 带选项的组件映射为 select
  const selectTypes = [
    'select',
    'radio',
    'checkbox',
    'cascader',
    'tree-select',
  ];
  if (selectTypes.includes(componentType)) {
    return 'select';
  }
  // 日期类组件保持日期选择（包括 date-picker）
  if (['date', 'date-picker', 'time'].includes(componentType)) {
    return 'date';
  }
  // 其他组件默认使用输入框
  return 'input';
}

// 根据组件类型确定默认查询类型
function getDefaultQueryType(componentType: string): string {
  // 用户/部门/岗位/表单/表格选择器使用 in 查询（支持多选）
  if (
    [
      'department-selector',
      'dept-select',
      'dept-selector',
      'form-selector',
      'position-selector',
      'post-selector',
      'table-selector',
      'user-select',
      'user-selector',
    ].includes(componentType)
  ) {
    return 'in';
  }
  // 开关组件默认精确匹配
  if (componentType === 'switch') {
    return 'eq';
  }
  const selectTypes = [
    'select',
    'radio',
    'checkbox',
    'cascader',
    'tree-select',
  ];
  if (selectTypes.includes(componentType)) {
    return 'eq'; // 选择类组件默认精确匹配
  }
  // 日期类组件默认范围查询（包括 date-picker）
  if (['date', 'date-picker', 'time'].includes(componentType)) {
    return 'range'; // 日期时间默认范围查询
  }
  return 'like'; // 文本类默认模糊匹配
}

// 判断是否为选择器组件（查询类型和组件类型不可修改）
function isSelectorComponent(componentType: string): boolean {
  return [
    'department-selector',
    'dept-select',
    'dept-selector',
    'form-selector',
    'position-selector',
    'post-selector',
    'table-selector',
    'user-select',
    'user-selector',
  ].includes(componentType);
}

function addQueryField(field: any) {
  // 避免重复添加
  if (queryFields.value.find((f) => f.field === field.field)) return;

  const queryComponent = mapQueryComponent(field.component);
  const queryType = getDefaultQueryType(field.component);

  // 判断是否为 datetime 类型字段（需要显示时间选项）
  const isDatetimeField =
    field.dbType?.toLowerCase().includes('timestamp') ||
    field.dbType?.toLowerCase().includes('datetime') ||
    (field.component === 'date-picker' && field.props?.type?.includes('time'));

  // 开关组件自动生成是/否选项
  const switchOptions =
    field.component === 'switch'
      ? [
          { label: $t('common.yes'), value: true },
          { label: $t('common.no'), value: false },
        ]
      : undefined;

  queryFields.value.push({
    label: field.label,
    field: field.field,
    type: queryType,
    component: queryComponent,
    // 保存原始组件类型，用于渲染时判断
    originalComponent: field.component,
    // 保存选项数据（用于下拉框渲染）
    options: switchOptions || field.options,
    // 保存组件属性
    props: field.props,
    // 保存数据库类型
    dbType: field.dbType,
    width: 6,
    defaultValue: '',
    hidden: false,
    multiple: isSelectorComponent(field.component)
      ? true
      : field.props?.multiple || false,
    // 是否显示时间（仅 datetime 类型字段可用）
    showTime: isDatetimeField,
    // 大小写敏感（仅文本类查询有效，默认敏感）
    caseSensitive: true,
    // 表单选择器 / 表格选择器配置
    formCode: field.formCode || '',
    valueField: field.valueField || field.props?.valueField || 'id',
    labelField: field.labelField || field.props?.labelField || 'name',
    dataSourceType: field.dataSourceType || '',
    dictCode: field.dictCode || '',
    dataSourceCode: field.dataSourceCode || '',
    columns: field.columns,
    searchFields: field.searchFields,
  });
}

// 获取组件类型的显示标签
function getComponentLabel(component: string): string {
  const labels: Record<string, string> = {
    input: $t('form-manager.listDesign.compInput'),
    select: $t('form-manager.listDesign.compSelect'),
    date: $t('form-manager.listDesign.compDate'),
    time: $t('form-manager.listDesign.compTime'),
  };

  // 如果已有映射，直接返回
  if (labels[component]) {
    return labels[component];
  }

  // 处理带连字符的组件名称，将 -selector 后缀统一映射为 -select
  let normalizedComponent = component;
  if (component.endsWith('-selector')) {
    normalizedComponent = component.replace('-selector', '-select');
  }

  // 首字母大写
  const capitalizedComponent =
    normalizedComponent.charAt(0).toUpperCase() + normalizedComponent.slice(1);

  return $t(`form-manager.listDesign.comp${capitalizedComponent}`);
}

// 判断是否为带选项的组件类型
function isOptionComponent(componentType: string): boolean {
  return ['cascader', 'checkbox', 'radio', 'select', 'tree-select'].includes(
    componentType,
  );
}

// 判断是否为日期时间组件类型
function isDateComponent(componentType: string): boolean {
  return [
    'date',
    'date-picker',
    'datetime',
    'datetime-picker',
    'time',
    'time-picker',
  ].includes(componentType);
}

// 判断是否为关联组件（需要显示名称而非ID）
function isRelationComponent(componentType: string): boolean {
  return [
    'department-selector',
    'dept-select',
    'dept-selector',
    'org-selector',
    'position-selector',
    'post-selector',
    'region-selector',
    'role-selector',
    'user-select',
    'user-selector',
  ].includes(componentType);
}

// 判断是否为表单数据选择器组件
function isFormDataSelectorComponent(field: any): boolean {
  // select 或 table-selector 组件，且数据源类型为 formData
  // 或者 form-selector 组件（本身就是表单数据选择器）
  const componentType = field.component || field.originalComponent;

  // form-selector 组件本身就是表单数据选择器
  if (componentType === 'form-selector') {
    return true;
  }

  const isSelectType = ['select', 'tree-select', 'radio', 'checkbox', 'cascader', 'table-selector'].includes(componentType);
  const isFormDataSource =
    field.dataSourceType === 'formData' ||
    field.props?.dataSourceType === 'formData';
  return isSelectType && isFormDataSource;
}

// 判断是否为不支持排序和过滤的组件类型（文件、图片等）
function isNoSortFilterComponent(componentType: string): boolean {
  return [
    'editor',
    'file-selector',
    'file-upload',
    'image-selector',
    'image-upload',
    'rich-text',
    'signature',
  ].includes(componentType);
}

// 判断是否为需要弹窗选择器过滤的组件类型
function isDialogFilterComponent(componentType: string): boolean {
  return [
    'department-selector',
    'dept-select',
    'dept-selector',
    'position-selector',
    'post-selector',
    'user-select',
    'user-selector',
  ].includes(componentType);
}

// 判断是否为用户选择器组件（支持显示头像）
function isUserSelectorComponent(componentType: string): boolean {
  return ['user-select', 'user-selector'].includes(componentType);
}

// 自动生成 displayField 名称
function generateDisplayField(fieldName: string): string {
  // 如果字段名以 _id 结尾，替换为 _name
  if (fieldName.endsWith('_id')) {
    return fieldName.replace(/_id$/, '_name');
  }
  // 如果字段名以 Id 结尾（驼峰命名），替换为 Name
  if (fieldName.endsWith('Id')) {
    return fieldName.replace(/Id$/, 'Name');
  }
  // 否则直接添加 _name 后缀
  return `${fieldName}_name`;
}

// 根据组件类型确定默认过滤类型
function getDefaultFilterType(
  componentType: string,
): 'date-range' | 'dept-select' | 'input' | 'select' | 'user-select' {
  switch (componentType) {
    case 'date-picker': {
      return 'date-range';
    }
    case 'department-selector':
    case 'dept-select':
    case 'dept-selector': {
      return 'dept-select';
    }
    case 'user-select':
    case 'user-selector': {
      return 'user-select';
    }
    case 'switch': {
      return 'select';
    }
    default: {
      if (isOptionComponent(componentType)) {
        return 'select';
      }
    }
  }
  return 'input';
}

function addListColumn(field: any) {
  if (listColumns.value.find((f) => f.field === field.field)) return;

  const hasOptions = isOptionComponent(field.component);
  const isRelation = isRelationComponent(field.component);
  const isFormDataSelector = isFormDataSelectorComponent(field);

  // 深拷贝 options 并初始化 tagType 属性；开关组件自动生成是/否选项
  const isSwitch = field.component === 'switch';
  const clonedOptions = isSwitch
    ? [
        { label: $t('common.yes'), value: true, tagType: 'success' },
        { label: $t('common.no'), value: false, tagType: 'danger' },
      ]
    : field.options
      ? field.options.map((opt: any) => ({
          ...opt,
          tagType: opt.tagType || '',
        }))
      : undefined;

  // 使用传入的 isNumeric 属性（基于数据库字段类型判断）
  const isNumericField = field.isNumeric ?? false;

  // 根据组件类型确定默认过滤类型
  const defaultFilterType = getDefaultFilterType(field.component);

  // 判断是否为 datetime 类型字段
  const isDatetimeField =
    field.dbType?.toLowerCase().includes('timestamp') ||
    field.dbType?.toLowerCase().includes('datetime');

  listColumns.value.push({
    label: field.label,
    field: field.field,
    // 排序配置
    sortable: false,
    sortType: 'frontend' as 'backend' | 'frontend', // 排序类型：前端排序 | 后端排序
    // 过滤配置
    filterable: false,
    filterType: defaultFilterType as 'date-range' | 'input' | 'select', // 过滤类型
    filterQueryType: 'range' as 'eq' | 'range', // 过滤查询类型：精确匹配 | 范围查询（仅日期类型有效）
    filterShowTime: isDatetimeField, // 是否显示时间（仅日期类型有效）
    filterMultiple: true, // 是否多选过滤（仅 select 类型有效）
    // 列显示配置
    fixed: false,
    align: 'left',
    width: '',
    minWidth: '',
    resizable: true,
    showOverflowTooltip: true,
    ellipsis: true,
    formatter: 'none',
    formatPattern: '',
    prefix: '',
    suffix: '',
    // 保存原始组件类型和选项数据，用于 Tag 显示
    originalComponent: field.component,
    options: clonedOptions,
    // 是否使用 Tag 显示（带选项的组件和开关组件）
    showAsTag: hasOptions || isSwitch,
    // 关联组件配置
    isRelation,
    showDisplayName: isRelation, // 默认显示名称
    displayField: isRelation ? generateDisplayField(field.field) : '',
    // 用户选择器配置（显示头像）
    isUserSelector: isUserSelectorComponent(field.component),
    showAsAvatar: false, // 默认不显示头像
    // 表尾统计配置（基于数据库字段类型）
    dbType: field.dbType || '',
    isNumeric: isNumericField,
    summaryEnabled: false,
    // 表单数据选择器配置（用于显示关联表单的其他字段）
    isFormDataSelector,
    formCode: field.formCode || field.props?.formCode || '',
    valueField: field.valueField || field.props?.valueField || 'id',
    labelField: field.labelField || field.props?.labelField || 'name',
    dataSourceType: field.dataSourceType || field.props?.dataSourceType || '',
    dictCode: field.dictCode || field.props?.dictCode || '',
    dataSourceCode: field.dataSourceCode || field.props?.dataSourceCode || '',
    columns: field.columns || field.props?.columns,
    searchFields: field.searchFields || field.props?.searchFields,
    displayFieldName: '', // 选中的显示字段名（如 name, phone 等）
    displayFieldOptions: [] as Array<{ label: string; value: string }>, // 可选的显示字段列表
    displayFieldOptionsLoading: false, // 字段选项加载状态
    // 虚拟字段配置（值关联，不保存到数据库，由后端动态填充）
    isVirtualField: field.props?.isVirtualField ?? false,
    valueSourceField: field.props?.valueSourceField || '',
    valueDisplayField: field.props?.valueDisplayField || '',
    showVirtualValue: true, // 默认开启，显示关联值
  });
}

// 卡片字段配置相关
const selectedCardArea = ref<null | string>(null);

// 卡片可用字段列表：仅显示已选中的列表字段
const cardAvailableFields = computed(() => {
  const selectedKeys = new Set(listColumns.value.map((col: any) => col.field));
  return availableFields.value.filter((f: any) => selectedKeys.has(f.field));
});
const draggingField = ref<any>(null);
const dragOverArea = ref<null | string>(null);

// 获取卡片区域对应的字段配置（从 cardFields 中获取）
function getCardAreaField(area: string) {
  switch (area) {
    case 'description': {
      return listSettings.value.cardFields.description;
    }
    case 'footerLeft': {
      return listSettings.value.cardFields.footerLeft;
    }
    case 'footerRight': {
      return listSettings.value.cardFields.footerRight;
    }
    case 'icon': {
      return listSettings.value.cardFields.icon;
    }
    case 'subtitle': {
      return listSettings.value.cardFields.subtitle;
    }
    case 'title': {
      return listSettings.value.cardFields.title;
    }
    default: {
      return null;
    }
  }
}

// 从 listColumns 中查找字段配置
function findColumnConfig(fieldName: string) {
  return listColumns.value.find((col: any) => col.field === fieldName);
}

// 获取当前选中的卡片字段配置（从 listColumns 中读取）
const selectedCardField = computed(() => {
  if (!selectedCardArea.value) return null;

  const cardField = getCardAreaField(selectedCardArea.value);
  if (!cardField || !cardField.field) return null;

  // 从 listColumns 中查找对应的配置
  const columnConfig = findColumnConfig(cardField.field);
  if (columnConfig) {
    return columnConfig;
  }

  // 如果 listColumns 中没有，返回 cardField 本身（兼容旧数据）
  return cardField;
});

// 选择卡片区域
function selectCardArea(area: string) {
  selectedCardArea.value = area;
}

// 拖拽开始
function handleDragStart(event: DragEvent, field: any) {
  draggingField.value = field;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'copy';
    event.dataTransfer.setData('text/plain', field.field);
  }
}

// 拖拽结束
function handleDragEnd() {
  draggingField.value = null;
  dragOverArea.value = null;
}

// 拖拽进入区域
function handleDragEnter(area: string) {
  if (draggingField.value) {
    dragOverArea.value = area;
  }
}

// 拖拽离开区域
function handleDragLeave() {
  dragOverArea.value = null;
}

// 拖拽放置
function handleDrop(event: DragEvent, area: string) {
  event.preventDefault();
  if (!draggingField.value) return;

  // 添加字段到指定区域
  addFieldToArea(draggingField.value, area);
  draggingField.value = null;
  dragOverArea.value = null;
}

// 添加字段到指定区域
function addFieldToArea(field: any, area: string) {
  // 检查字段是否已在 listColumns 中
  let columnConfig = findColumnConfig(field.field);

  // 如果不在 listColumns 中，先添加到 listColumns
  if (!columnConfig) {
    addListColumn(field);
    columnConfig = findColumnConfig(field.field);
  }

  // 确保 listColumns 中的字段配置有 displayField（用于后端返回关联字段名称）
  if (columnConfig) {
    const isRelation = isRelationComponent(field.component);
    const isUserSelector = isUserSelectorComponent(field.component);

    if ((isRelation || isUserSelector) && !columnConfig.displayField) {
      columnConfig.displayField = `${field.field}_name`;
      columnConfig.showDisplayName = true;
    }

    // 如果是用户选择器且添加到图标区域，自动启用头像显示
    if (isUserSelector && area === 'icon') {
      columnConfig.showAsAvatar = true;
    }
  }

  // 卡片字段只保存基本信息，属性从 listColumns 中读取
  const fieldConfig = {
    field: field.field,
    label: field.label,
    component: field.component,
  };

  switch (area) {
    case 'description': {
      listSettings.value.cardFields.description = fieldConfig;
      break;
    }
    case 'footerLeft': {
      listSettings.value.cardFields.footerLeft = fieldConfig;
      break;
    }
    case 'footerRight': {
      listSettings.value.cardFields.footerRight = fieldConfig;
      break;
    }
    case 'icon': {
      listSettings.value.cardFields.icon = fieldConfig;
      break;
    }
    case 'subtitle': {
      listSettings.value.cardFields.subtitle = fieldConfig;
      break;
    }
    case 'tags': {
      if (listSettings.value.cardFields.tags.length < 3) {
        listSettings.value.cardFields.tags.push(fieldConfig);
      }
      break;
    }
    case 'title': {
      listSettings.value.cardFields.title = fieldConfig;
      break;
    }
  }
}

// 添加字段到选中的卡片区域（已废弃，保留用于向后兼容）
function addFieldToSelectedArea(field: any) {
  if (!selectedCardArea.value) {
    // 如果没有选中区域，默认添加到第一个空的区域
    if (!listSettings.value.cardFields.title) {
      selectedCardArea.value = 'title';
    } else if (!listSettings.value.cardFields.subtitle) {
      selectedCardArea.value = 'subtitle';
    } else if (!listSettings.value.cardFields.description) {
      selectedCardArea.value = 'description';
    } else if (listSettings.value.cardFields.tags.length < 3) {
      selectedCardArea.value = 'tags';
    } else if (!listSettings.value.cardFields.footerLeft) {
      selectedCardArea.value = 'footerLeft';
    } else if (!listSettings.value.cardFields.footerRight) {
      selectedCardArea.value = 'footerRight';
    } else if (listSettings.value.cardFields.icon) {
      return; // 所有区域都已填满
    } else {
      selectedCardArea.value = 'icon';
    }
  }

  addFieldToArea(field, selectedCardArea.value);

  // 清除选中状态
  selectedCardArea.value = null;
}

// 移除卡片标签字段
function removeCardTag(index: number) {
  listSettings.value.cardFields.tags.splice(index, 1);
}

// 清除卡片区域字段
function clearCardArea(area: string) {
  switch (area) {
    case 'description': {
      listSettings.value.cardFields.description = null;
      break;
    }
    case 'footerLeft': {
      listSettings.value.cardFields.footerLeft = null;
      break;
    }
    case 'footerRight': {
      listSettings.value.cardFields.footerRight = null;
      break;
    }
    case 'icon': {
      listSettings.value.cardFields.icon = null;
      break;
    }
    case 'subtitle': {
      listSettings.value.cardFields.subtitle = null;
      break;
    }
    case 'tags': {
      listSettings.value.cardFields.tags = [];
      break;
    }
    case 'title': {
      listSettings.value.cardFields.title = null;
      break;
    }
  }
}

// 加载表单数据选择器的可选字段
async function loadFormDataDisplayFieldOptions(column: any) {
  if (!column.formCode || column.displayFieldOptionsLoading) return;

  column.displayFieldOptionsLoading = true;
  try {
    const formMeta = await getFormByCodeApi(column.formCode);
    const formConfig = formMeta.form_config || {};
    const items = formConfig.items || [];

    // 提取所有可用字段
    const fields: Array<{ label: string; value: string }> = [];

    // 布局/展示类组件，这些组件不应该出现在字段选项中
    const layoutTypes = new Set([
      'alert',
      'collapse',
      'divider',
      'grid',
      'html',
      'spacer',
      'steps',
      'sub-table',
      'tabs',
      'text',
      'timeline',
      'title',
    ]);

    function extractFieldsFromItems(itemList: any[]) {
      for (const item of itemList) {
        const itemType = item.type || '';

        // 跳过布局/展示类组件，但需要递归处理其子组件
        if (layoutTypes.has(itemType)) {
          // 递归处理嵌套字段（如栅格、标签页等）
          if (item.columns) {
            item.columns.forEach((col: any) => {
              extractFieldsFromItems(col.children || []);
            });
          }
          if (item.items) {
            item.items.forEach((subItem: any) => {
              extractFieldsFromItems(subItem.children || []);
            });
          }
          if (item.children) {
            extractFieldsFromItems(item.children);
          }
          continue;
        }

        // 只添加有 field 属性的真实表单字段
        if (item.field && item.label) {
          fields.push({
            label: item.label,
            value: item.field,
          });
        }
      }
    }

    extractFieldsFromItems(items);
    column.displayFieldOptions = fields;

    // 如果没有选中的字段，默认选择 name 字段（如果存在）
    if (!column.displayFieldName && fields.length > 0) {
      const nameField = fields.find((f) => f.value === 'name');
      column.displayFieldName = nameField ? 'name' : fields[0]?.value || '';
    }
  } catch (error) {
    console.error('加载表单字段选项失败:', error);
    column.displayFieldOptions = [];
  } finally {
    column.displayFieldOptionsLoading = false;
  }
}

// 获取组件数据
function getData() {
  // 处理列配置，只有开启显示名称时才保留 displayField
  const processedColumns = listColumns.value.map((col) => {
    const {
      isRelation,
      showDisplayName,
      displayField,
      isUserSelector,
      isFormDataSelector,
      displayFieldOptions,
      displayFieldOptionsLoading,
      ...rest
    } = col;

    // 计算最终的 displayField
    let finalDisplayField: string | undefined;
    if (isRelation && showDisplayName) {
      // 关联组件（用户、部门等）
      finalDisplayField = displayField;
    } else if (isFormDataSelector && showDisplayName && rest.displayFieldName) {
      // 表单数据选择器：使用 field_displayFieldName 格式
      finalDisplayField = `${rest.field}_${rest.displayFieldName}`;
    }

    // 是否为需要保存选择器配置的组件（form-selector / table-selector）
    const isTableSelector = rest.originalComponent === 'table-selector';
    const needSelectorConfig = isFormDataSelector || isTableSelector;

    return {
      ...rest,
      displayField: finalDisplayField,
      // 只有用户选择器且开启显示头像时才保留 showAsAvatar
      showAsAvatar: isUserSelector && rest.showAsAvatar ? true : undefined,
      // 保存表单数据选择器的配置（用于后端识别和前端点击跳转）
      isFormDataSelector: isFormDataSelector || undefined,
      displayFieldName:
        isFormDataSelector && showDisplayName
          ? rest.displayFieldName
          : undefined,
      // 保存 formCode 用于点击跳转到关联表单详情
      formCode: needSelectorConfig ? rest.formCode : undefined,
      // 保存选择器的 valueField/labelField（用于查询和过滤时显示正确标签）
      valueField: needSelectorConfig ? rest.valueField || 'id' : undefined,
      labelField: needSelectorConfig ? rest.labelField || 'name' : undefined,
      // 保存 table-selector 额外配置
      dataSourceType: isTableSelector ? rest.dataSourceType : undefined,
      dictCode: isTableSelector ? rest.dictCode : undefined,
      dataSourceCode: isTableSelector ? rest.dataSourceCode : undefined,
      columns: isTableSelector ? rest.columns : undefined,
      searchFields: isTableSelector ? rest.searchFields : undefined,
    };
  });

  return {
    queryFields: queryFields.value,
    columns: processedColumns,
    listType: listSettings.value.listType,
    containerType: listSettings.value.containerType,
    table: listSettings.value.table,
    card: listSettings.value.card,
    cardFields: listSettings.value.cardFields,
    dialog: listSettings.value.dialog,
    drawer: listSettings.value.drawer,
    page: listSettings.value.page,
    layout: listSettings.value.layout,
    buttons: listSettings.value.buttons,
    showConfirmButton: listSettings.value.showConfirmButton,
    afterSaveAction: listSettings.value.afterSaveAction,
    enableStartWorkflowOnAdd: listSettings.value.enableStartWorkflowOnAdd,
    subTableButtons: listSettings.value.subTableButtons,
    customButtons: listSettings.value.customButtons,
    tree: listSettings.value.tree,
  };
}

// 设置组件数据
function setData(data: any) {
  // 重置查询字段，补全选择器配置（兼容旧数据）
  queryFields.value = (data?.queryFields || []).map((qf: any) => {
    const comp = qf.originalComponent || qf.component;
    if (
      (comp === 'form-selector' || comp === 'table-selector') &&
      !qf.formCode &&
      !qf.dictCode &&
      !qf.dataSourceCode
    ) {
      const sourceField = availableFields.value.find(
        (f: any) => f.field === qf.field,
      );
      if (sourceField) {
        return {
          ...qf,
          formCode: sourceField.formCode || '',
          valueField: sourceField.valueField || 'id',
          labelField: sourceField.labelField || 'name',
          dataSourceType: sourceField.dataSourceType || '',
          dictCode: sourceField.dictCode || '',
          dataSourceCode: sourceField.dataSourceCode || '',
          columns: sourceField.columns,
          searchFields: sourceField.searchFields,
        };
      }
    }
    return qf;
  });

  // 重置列表字段，确保 options 中的 tagType 属性存在，并恢复关联组件配置
  listColumns.value = (data?.columns || []).map((col: any) => {
    const isRelation = isRelationComponent(col.originalComponent);
    const isFormDataSelector = col.isFormDataSelector ?? false;
    const hasDisplayField = !!col.displayField;

    // 判断是否开启了显示名称
    const showDisplayName =
      (isRelation && hasDisplayField) ||
      (isFormDataSelector && hasDisplayField);

    return {
      ...col,
      options: col.options
        ? col.options.map((opt: any) => ({
            ...opt,
            tagType: opt.tagType || '',
          }))
        : undefined,
      // 恢复排序配置
      sortable: col.sortable ?? false,
      sortType: col.sortType || 'frontend',
      // 恢复过滤配置
      filterable: col.filterable ?? false,
      filterType: col.filterType || 'input',
      filterQueryType: col.filterQueryType || 'range',
      filterShowTime: col.filterShowTime ?? false,
      filterMultiple: col.filterMultiple ?? true,
      // 恢复关联组件配置
      isRelation,
      showDisplayName,
      displayField:
        col.displayField || (isRelation ? generateDisplayField(col.field) : ''),
      // 恢复用户选择器配置（显示头像）
      isUserSelector: isUserSelectorComponent(col.originalComponent),
      showAsAvatar: col.showAsAvatar ?? false,
      // 恢复统计配置（基于保存的 isNumeric 属性）
      dbType: col.dbType || '',
      isNumeric: col.isNumeric ?? false,
      summaryEnabled: col.summaryEnabled ?? false,
      // 恢复表单数据选择器配置
      isFormDataSelector,
      formCode: col.formCode || '',
      valueField: col.valueField || 'id',
      labelField: col.labelField || 'name',
      dataSourceType: col.dataSourceType || '',
      dictCode: col.dictCode || '',
      dataSourceCode: col.dataSourceCode || '',
      columns: col.columns,
      searchFields: col.searchFields,
      displayFieldName: col.displayFieldName || '',
      displayFieldOptions: [] as Array<{ label: string; value: string }>,
      displayFieldOptionsLoading: false,
      // 恢复虚拟字段配置
      isVirtualField: col.isVirtualField ?? false,
      valueSourceField: col.valueSourceField || '',
      valueDisplayField: col.valueDisplayField || '',
      showVirtualValue: col.showVirtualValue ?? true,
    };
  });

  // 设置列表类型（默认 table）
  listSettings.value.listType = data?.listType || 'table';

  // 合并 table 设置（使用默认值）
  listSettings.value.table = {
    showPagination: data?.table?.showPagination ?? true,
    pageSize: data?.table?.pageSize || 20,
    showIndex: data?.table?.showIndex ?? true,
    showSelection: data?.table?.showSelection ?? true,
    stripe: data?.table?.stripe ?? true,
    border: data?.table?.border ?? true,
    size: data?.table?.size || 'default',
    height: data?.table?.height || 'auto',
    defaultSort: Array.isArray(data?.table?.defaultSort)
      ? data.table.defaultSort
      : (data?.table?.defaultSort?.field
        ? [
            {
              field: data.table.defaultSort.field,
              order: data.table.defaultSort.order || 'desc',
            },
          ]
        : []),
    defaultFilters: Array.isArray(data?.table?.defaultFilters)
      ? data.table.defaultFilters
      : [],
    showSummary: data?.table?.showSummary ?? false,
    summaryType: data?.table?.summaryType || 'sum',
    summaryPrecision: data?.table?.summaryPrecision ?? 2,
  };

  // 合并 card 设置（使用默认值）
  listSettings.value.card = {
    columns: data?.card?.columns ?? 4,
    gap: data?.card?.gap ?? 16,
    shadow: data?.card?.shadow || 'hover',
    pageSize: data?.card?.pageSize ?? 12,
    showPagination: data?.card?.showPagination ?? true,
  };

  // 恢复卡片字段映射
  listSettings.value.cardFields = {
    icon: data?.cardFields?.icon || null,
    title: data?.cardFields?.title || null,
    subtitle: data?.cardFields?.subtitle || null,
    description: data?.cardFields?.description || null,
    tags: data?.cardFields?.tags || [],
    footerLeft: data?.cardFields?.footerLeft || null,
    footerRight: data?.cardFields?.footerRight || null,
  };

  // 设置容器类型（默认 drawer）
  listSettings.value.containerType = data?.containerType || 'drawer';

  // 合并 dialog 设置（使用默认值）
  listSettings.value.dialog = {
    width: data?.dialog?.width || '800px',
    fullscreen: data?.dialog?.fullscreen ?? false,
    draggable: data?.dialog?.draggable ?? true,
    closeOnClickModal: data?.dialog?.closeOnClickModal ?? false,
    closeOnPressEscape: data?.dialog?.closeOnPressEscape ?? true,
  };

  // 合并 drawer 设置（使用默认值）
  listSettings.value.drawer = {
    size: data?.drawer?.size || '800px',
    direction: data?.drawer?.direction || 'rtl',
    withHeader: data?.drawer?.withHeader ?? true,
    closeOnClickModal: data?.drawer?.closeOnClickModal ?? false,
    closeOnPressEscape: data?.drawer?.closeOnPressEscape ?? true,
  };

  // 合并 page 设置（使用默认值）
  listSettings.value.page = {
    showBackButton: data?.page?.showBackButton ?? true,
    openInNewTab: data?.page?.openInNewTab ?? true,
  };

  // 合并 layout 设置（使用默认值）
  listSettings.value.layout = {
    showBackButton: data?.layout?.showBackButton ?? true,
    renderMode: data?.layout?.renderMode || 'condition',
  };

  // 合并 buttons 设置（使用默认值）
  listSettings.value.buttons = {
    showAdd: data?.buttons?.showAdd ?? true,
    showEdit: data?.buttons?.showEdit ?? true,
    showDelete: data?.buttons?.showDelete ?? true,
    showView: data?.buttons?.showView ?? true,
    showExport: data?.buttons?.showExport ?? true,
    showImport: data?.buttons?.showImport ?? false,
    showBatchDelete: data?.buttons?.showBatchDelete ?? true,
  };

  // 恢复确认按钮显示配置（流程表单默认关闭，其他类型默认打开）
  const defaultShowConfirm = !isWorkflowForm.value;
  listSettings.value.showConfirmButton =
    data?.showConfirmButton ?? defaultShowConfirm;

  // 恢复保存后行为配置（兼容旧版 closeAfterSave 布尔值）
  if (data?.afterSaveAction) {
    listSettings.value.afterSaveAction = data.afterSaveAction;
  } else if (data?.closeAfterSave === false) {
    listSettings.value.afterSaveAction = 'editMode';
  } else {
    listSettings.value.afterSaveAction = 'close';
  }

  // 恢复新增时可发起流程配置（流程表单默认打开）
  const defaultEnableWorkflow = isWorkflowForm.value;
  listSettings.value.enableStartWorkflowOnAdd =
    data?.enableStartWorkflowOnAdd ?? defaultEnableWorkflow;

  // 恢复子表操作按钮
  listSettings.value.subTableButtons = data?.subTableButtons || [];

  // 恢复自定义按钮
  listSettings.value.customButtons = data?.customButtons || [];

  // 恢复树形表格配置
  listSettings.value.tree = {
    enabled: data?.tree?.enabled ?? false,
    parentField: data?.tree?.parentField || 'parent_id',
    lazy: data?.tree?.lazy ?? false,
    defaultExpandAll: data?.tree?.defaultExpandAll ?? false,
    indent: data?.tree?.indent ?? 16,
    checkStrictly: data?.tree?.checkStrictly ?? false,
  };
}

defineExpose({
  getData,
  setData,
});
</script>

<template>
  <div class="dark:bg-background-deep flex h-full w-full">
    <!-- 右侧属性配置区 -->
    <div class="bg-card ml-4 mt-4 flex w-[320px] flex-col rounded-[8px] border">
      <!-- Tabs 导航 -->
      <div class="px-3 py-4 pb-0">
        <ZqTabs v-model="activeTab" :items="tabItems" />
      </div>

      <!-- Tab 内容 -->
      <div class="flex-1 overflow-hidden">
        <!-- Tab 1: 查询字段 -->
        <div v-show="activeTab === 'query'" class="h-full">
          <ElScrollbar class="h-full">
            <div class="p-4">
              <div class="border-border mb-4 flex items-center justify-between">
                <span class="text-muted-foreground text-xs">{{
                  $t('form-manager.listDesign.querySelectionTip')
                }}</span>
                <ElCheckbox
                  v-if="availableFields.length > 0"
                  v-model="isQueryAllSelected"
                  :indeterminate="isQueryIndeterminate"
                  size="small"
                >
                  {{ $t('form-manager.listDesign.selectAll') }}
                </ElCheckbox>
              </div>
              <ElCheckboxGroup
                v-model="selectedQueryFieldKeys"
                class="flex flex-col gap-2"
              >
                <div
                  v-for="field in availableFields"
                  :key="field.field"
                  class="border-border bg-background hover:border-primary flex items-center rounded border p-3"
                >
                  <ElCheckbox :label="field.field" class="!mr-0 w-full">
                    <div class="flex flex-col">
                      <span class="text-foreground text-sm font-medium">{{
                        field.label
                      }}</span>
                      <span class="text-muted-foreground text-xs">{{
                        field.field
                      }}</span>
                    </div>
                  </ElCheckbox>
                </div>
              </ElCheckboxGroup>
              <div
                v-if="availableFields.length === 0"
                class="text-muted-foreground py-8 text-center"
              >
                {{ $t('form-manager.listDesign.noAvailableFields') }}
              </div>
            </div>
          </ElScrollbar>
        </div>

        <!-- Tab 2: 列表字段 -->
        <div v-show="activeTab === 'columns'" class="h-full">
          <ElScrollbar class="h-full">
            <div class="p-4">
              <div
                class="border-border mb-4 flex items-center justify-between border-b pb-2"
              >
                <span class="text-muted-foreground text-xs">{{
                  $t('form-manager.listDesign.listSelectionTip')
                }}</span>
                <ElCheckbox
                  v-if="availableFields.length > 0"
                  v-model="isListAllSelected"
                  :indeterminate="isListIndeterminate"
                  size="small"
                >
                  {{ $t('form-manager.listDesign.selectAll') }}
                </ElCheckbox>
              </div>
              <ElCheckboxGroup
                v-model="selectedListColumnKeys"
                class="flex flex-col gap-2"
              >
                <div
                  v-for="field in availableFields"
                  :key="field.field"
                  class="border-border bg-background hover:border-primary flex items-center rounded border p-3"
                >
                  <ElCheckbox :label="field.field" class="!mr-0 w-full">
                    <div class="flex flex-col">
                      <span class="text-foreground text-sm font-medium">{{
                        field.label
                      }}</span>
                      <span class="text-muted-foreground text-xs">{{
                        field.field
                      }}</span>
                    </div>
                  </ElCheckbox>
                </div>
              </ElCheckboxGroup>
              <div
                v-if="availableFields.length === 0"
                class="text-muted-foreground py-8 text-center"
              >
                {{ $t('form-manager.listDesign.noAvailableFields') }}
              </div>
            </div>
          </ElScrollbar>
        </div>

        <!-- Tab 3: 列表属性 -->
        <div v-show="activeTab === 'properties'" class="h-full">
          <ElScrollbar class="h-full">
            <div class="px-4 pb-4">
              <ElForm :model="listSettings" label-position="top" size="small">
                <!-- 列表类型切换 -->
                <div class="mb-4 mt-4">
                  <div class="text-muted-foreground mb-2 text-xs font-bold">
                    {{ $t('form-manager.listDesign.listType') }}
                  </div>
                  <ElRadioGroup
                    v-model="listSettings.listType"
                    class="list-type-radio w-full"
                  >
                    <ElRadio value="table" class="flex-1">
                      <div class="flex items-center gap-1">
                        <TableProperties class="h-4 w-4" />
                        <span>Table</span>
                      </div>
                    </ElRadio>
                    <ElRadio value="card" class="flex-1">
                      <div class="flex items-center gap-1">
                        <LayoutGrid class="h-4 w-4" />
                        <span>Card</span>
                      </div>
                    </ElRadio>
                  </ElRadioGroup>
                </div>

                <!-- Table 属性（仅 Table 模式显示） -->
                <template v-if="listSettings.listType === 'table'">
                  <div
                    class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                    @click="toggleSection('table')"
                  >
                    <span class="font-bold">{{
                      $t('form-manager.listDesign.tableProperties')
                    }}</span>
                    <ElIcon class="h-4 w-4">
                      <ArrowDown v-if="activeSections.includes('table')" />
                      <ArrowRight v-else />
                    </ElIcon>
                  </div>
                  <div v-show="activeSections.includes('table')">
                    <ElFormItem
                      :label="$t('form-manager.listDesign.showPagination')"
                    >
                      <ElSwitch v-model="listSettings.table.showPagination" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-manager.listDesign.pageSize')">
                      <ElSelect
                        v-model="listSettings.table.pageSize"
                        class="w-full"
                      >
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.itemsPerPage', {
                              count: 10,
                            })
                          "
                          :value="10"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.itemsPerPage', {
                              count: 20,
                            })
                          "
                          :value="20"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.itemsPerPage', {
                              count: 50,
                            })
                          "
                          :value="50"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.itemsPerPage', {
                              count: 100,
                            })
                          "
                          :value="100"
                        />
                      </ElSelect>
                    </ElFormItem>
                    <ElFormItem
                      :label="$t('form-manager.listDesign.showIndex')"
                    >
                      <ElSwitch v-model="listSettings.table.showIndex" />
                    </ElFormItem>
                    <ElFormItem
                      :label="$t('form-manager.listDesign.showSelection')"
                    >
                      <ElSwitch v-model="listSettings.table.showSelection" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-manager.listDesign.stripe')">
                      <ElSwitch v-model="listSettings.table.stripe" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-manager.listDesign.border')">
                      <ElSwitch v-model="listSettings.table.border" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-manager.listDesign.size')">
                      <ElRadioGroup v-model="listSettings.table.size">
                        <ElRadio value="large">
                          {{ $t('form-manager.listDesign.sizeLarge') }}
                        </ElRadio>
                        <ElRadio value="default">
                          {{ $t('form-manager.listDesign.sizeDefault') }}
                        </ElRadio>
                        <ElRadio value="small">
                          {{ $t('form-manager.listDesign.sizeSmall') }}
                        </ElRadio>
                      </ElRadioGroup>
                    </ElFormItem>
                    <ElFormItem
                      :label="$t('form-manager.listDesign.tableHeight')"
                    >
                      <ElSelect
                        v-model="listSettings.table.height"
                        class="w-full"
                      >
                        <ElOption
                          :label="$t('form-manager.listDesign.adaptive')"
                          value="auto"
                        />
                        <ElOption label="400px" value="400" />
                        <ElOption label="500px" value="500" />
                        <ElOption label="600px" value="600" />
                      </ElSelect>
                    </ElFormItem>
                  </div>

                  <!-- 表尾统计 -->
                  <div
                    class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                    @click="toggleSection('summary')"
                  >
                    <span class="font-bold">{{
                      $t('form-manager.listDesign.tableSummary')
                    }}</span>
                    <ElIcon class="h-4 w-4">
                      <ArrowDown v-if="activeSections.includes('summary')" />
                      <ArrowRight v-else />
                    </ElIcon>
                  </div>
                  <div v-show="activeSections.includes('summary')">
                    <ElFormItem
                      :label="$t('form-manager.listDesign.showSummary')"
                    >
                      <ElSwitch v-model="listSettings.table.showSummary" />
                    </ElFormItem>
                    <template v-if="listSettings.table.showSummary">
                      <ElFormItem
                        :label="$t('form-manager.listDesign.summaryType')"
                      >
                        <ElRadioGroup v-model="listSettings.table.summaryType">
                          <ElRadio value="sum">
                            {{ $t('form-manager.listDesign.summarySum') }}
                          </ElRadio>
                          <ElRadio value="avg">
                            {{ $t('form-manager.listDesign.summaryAvg') }}
                          </ElRadio>
                          <ElRadio value="count">
                            {{ $t('form-manager.listDesign.summaryCount') }}
                          </ElRadio>
                          <ElRadio value="max">
                            {{ $t('form-manager.listDesign.summaryMax') }}
                          </ElRadio>
                          <ElRadio value="min">
                            {{ $t('form-manager.listDesign.summaryMin') }}
                          </ElRadio>
                        </ElRadioGroup>
                      </ElFormItem>
                      <ElFormItem
                        :label="$t('form-manager.listDesign.summaryPrecision')"
                      >
                        <ElSelect
                          v-model="listSettings.table.summaryPrecision"
                          class="!w-24"
                        >
                          <ElOption label="0" :value="0" />
                          <ElOption label="1" :value="1" />
                          <ElOption label="2" :value="2" />
                          <ElOption label="3" :value="3" />
                          <ElOption label="4" :value="4" />
                        </ElSelect>
                      </ElFormItem>
                      <div class="text-muted-foreground mb-2 text-xs">
                        {{ $t('form-manager.listDesign.summaryColumnTip') }}
                      </div>
                    </template>
                  </div>

                  <!-- 树形表格配置 -->
                  <div
                    class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                    @click="toggleSection('tree')"
                  >
                    <span class="font-bold">{{
                      $t('form-manager.listDesign.treeConfig')
                    }}</span>
                    <ElIcon class="h-4 w-4">
                      <ArrowDown v-if="activeSections.includes('tree')" />
                      <ArrowRight v-else />
                    </ElIcon>
                  </div>
                  <div v-show="activeSections.includes('tree')">
                    <ElFormItem
                      :label="$t('form-manager.listDesign.enableTree')"
                    >
                      <ElSwitch v-model="listSettings.tree.enabled" />
                    </ElFormItem>
                    <template v-if="listSettings.tree.enabled">
                      <ElFormItem
                        :label="$t('form-manager.listDesign.parentField')"
                      >
                        <ElSelect
                          v-model="listSettings.tree.parentField"
                          class="w-full"
                          filterable
                        >
                          <ElOption
                            v-for="field in availableFields"
                            :key="field.field"
                            :label="`${field.label} (${field.field})`"
                            :value="field.field"
                          />
                        </ElSelect>
                      </ElFormItem>
                      <ElFormItem
                        :label="$t('form-manager.listDesign.lazyLoad')"
                      >
                        <ElSwitch v-model="listSettings.tree.lazy" />
                        <div class="text-muted-foreground ml-2 text-xs">
                          {{
                            listSettings.tree.lazy
                              ? $t('form-manager.listDesign.lazyLoadOnTip')
                              : $t('form-manager.listDesign.lazyLoadOffTip')
                          }}
                        </div>
                      </ElFormItem>
                      <ElFormItem
                        v-if="!listSettings.tree.lazy"
                        :label="$t('form-manager.listDesign.defaultExpandAll')"
                      >
                        <ElSwitch v-model="listSettings.tree.defaultExpandAll" />
                      </ElFormItem>
                      <ElFormItem
                        :label="$t('form-manager.listDesign.indent')"
                      >
                        <ElInputNumber
                          v-model="listSettings.tree.indent"
                          :min="8"
                          :max="64"
                          :step="8"
                          class="!w-24"
                        />
                        <span class="text-muted-foreground ml-2 text-xs">px</span>
                      </ElFormItem>
                      <ElFormItem
                        :label="$t('form-manager.listDesign.checkStrictly')"
                      >
                        <ElSwitch v-model="listSettings.tree.checkStrictly" />
                      </ElFormItem>
                    </template>
                  </div>
                </template>

                <!-- Card 属性（仅 Card 模式显示） -->
                <template v-if="listSettings.listType === 'card'">
                  <div
                    class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                    @click="toggleSection('card')"
                  >
                    <span class="font-bold">{{
                      $t('form-manager.listDesign.cardProperties')
                    }}</span>
                    <ElIcon class="h-4 w-4">
                      <ArrowDown v-if="activeSections.includes('card')" />
                      <ArrowRight v-else />
                    </ElIcon>
                  </div>
                  <div v-show="activeSections.includes('card')">
                    <ElFormItem
                      :label="$t('form-manager.listDesign.cardColumns')"
                    >
                      <ElSelect
                        v-model="listSettings.card.columns"
                        class="w-full"
                      >
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.cardColumnsOption', {
                              count: 1,
                            })
                          "
                          :value="1"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.cardColumnsOption', {
                              count: 2,
                            })
                          "
                          :value="2"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.cardColumnsOption', {
                              count: 3,
                            })
                          "
                          :value="3"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.cardColumnsOption', {
                              count: 4,
                            })
                          "
                          :value="4"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.cardColumnsOption', {
                              count: 5,
                            })
                          "
                          :value="5"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.cardColumnsOption', {
                              count: 6,
                            })
                          "
                          :value="6"
                        />
                      </ElSelect>
                    </ElFormItem>
                    <ElFormItem :label="$t('form-manager.listDesign.cardGap')">
                      <ElInputNumber
                        v-model="listSettings.card.gap"
                        :min="0"
                        :max="48"
                        :step="4"
                        class="w-full"
                      />
                    </ElFormItem>
                    <ElFormItem
                      :label="$t('form-manager.listDesign.cardShadow')"
                    >
                      <ElRadioGroup v-model="listSettings.card.shadow">
                        <ElRadio value="always">
                          {{ $t('form-manager.listDesign.shadowAlways') }}
                        </ElRadio>
                        <ElRadio value="hover">
                          {{ $t('form-manager.listDesign.shadowHover') }}
                        </ElRadio>
                        <ElRadio value="never">
                          {{ $t('form-manager.listDesign.shadowNever') }}
                        </ElRadio>
                      </ElRadioGroup>
                    </ElFormItem>
                    <ElFormItem
                      :label="$t('form-manager.listDesign.showPagination')"
                    >
                      <ElSwitch v-model="listSettings.card.showPagination" />
                    </ElFormItem>
                    <ElFormItem :label="$t('form-manager.listDesign.pageSize')">
                      <ElSelect
                        v-model="listSettings.card.pageSize"
                        class="w-full"
                      >
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.itemsPerPage', {
                              count: 8,
                            })
                          "
                          :value="8"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.itemsPerPage', {
                              count: 12,
                            })
                          "
                          :value="12"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.itemsPerPage', {
                              count: 16,
                            })
                          "
                          :value="16"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.itemsPerPage', {
                              count: 24,
                            })
                          "
                          :value="24"
                        />
                      </ElSelect>
                    </ElFormItem>
                  </div>
                </template>

                <!-- 默认排序与过滤条件（Table 和 Card 模式共用） -->
                <div class="mt-4">
                  <ElFormItem
                    :label="$t('form-manager.listDesign.defaultSortField')"
                  >
                    <div class="w-full space-y-2">
                      <draggable
                        v-model="listSettings.table.defaultSort"
                        item-key="field"
                        handle=".drag-handle"
                        class="space-y-2"
                      >
                        <template #item="{ element, index }">
                          <div
                            class="border-border bg-background flex items-center gap-2 rounded border p-2"
                          >
                            <div
                              class="drag-handle text-muted-foreground hover:text-foreground cursor-move"
                            >
                              <GripVertical class="h-4 w-4" />
                            </div>
                            <ElSelect
                              v-model="element.field"
                              size="small"
                              style="width: 140px"
                              :placeholder="
                                $t('form-manager.listDesign.selectSortField')
                              "
                            >
                              <ElOption
                                v-for="field in availableFields"
                                :key="field.field"
                                :label="`${field.label} (${field.field})`"
                                :value="field.field"
                              />
                            </ElSelect>
                            <ElSelect
                              v-model="element.order"
                              class="flex-1"
                              size="small"
                            >
                              <ElOption
                                :label="
                                  $t('form-manager.listDesign.ascending')
                                "
                                value="asc"
                              />
                              <ElOption
                                :label="
                                  $t('form-manager.listDesign.descending')
                                "
                                value="desc"
                              />
                            </ElSelect>
                            <ElButton
                              type="danger"
                              size="small"
                              :icon="Trash2"
                              circle
                              @click="removeSortField(index)"
                            />
                          </div>
                        </template>
                      </draggable>
                      <ElButton
                        type="primary"
                        size="small"
                        class="w-full"
                        @click="addSortField"
                      >
                        {{ $t('form-manager.listDesign.addSortField') }}
                      </ElButton>
                    </div>
                  </ElFormItem>

                  <ElFormItem
                    :label="$t('form-manager.listDesign.defaultFilterConditions')"
                  >
                    <div class="w-full space-y-2">
                      <div
                        v-for="(condition, index) in listSettings.table.defaultFilters"
                        :key="index"
                        class="border-border bg-background flex flex-wrap items-center gap-2 rounded border p-2"
                      >
                        <ElSelect
                          v-model="condition.field"
                          size="small"
                          style="width: 130px"
                          :placeholder="
                            $t('form-manager.listDesign.selectFilterField')
                          "
                        >
                          <ElOption
                            v-for="field in availableFields"
                            :key="field.field"
                            :label="`${field.label} (${field.field})`"
                            :value="field.field"
                          />
                        </ElSelect>
                        <ElSelect
                          v-model="condition.operator"
                          size="small"
                          style="width: 110px"
                        >
                          <ElOption
                            :label="$t('form-manager.listDesign.filterOperatorEq')"
                            value="eq"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.filterOperatorNe')"
                            value="ne"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.filterOperatorGt')"
                            value="gt"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.filterOperatorGte')"
                            value="gte"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.filterOperatorLt')"
                            value="lt"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.filterOperatorLte')"
                            value="lte"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.filterOperatorLike')"
                            value="like"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.filterOperatorIn')"
                            value="in"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.filterOperatorNull')"
                            value="null"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.filterOperatorNotNull')"
                            value="not_null"
                          />
                        </ElSelect>
                        <template
                          v-if="filterOperatorNeedsValue(condition.operator) && condition.field"
                        >
                          <ElSelect
                            v-if="getFilterValueType(condition.field) === 'boolean'"
                            v-model="condition.value"
                            size="small"
                            class="flex-1"
                            style="min-width: 80px"
                          >
                            <ElOption label="true" value="true" />
                            <ElOption label="false" value="false" />
                          </ElSelect>
                          <ElInputNumber
                            v-else-if="getFilterValueType(condition.field) === 'number'"
                            :model-value="condition.value ? Number(condition.value) : undefined"
                            size="small"
                            class="flex-1"
                            style="min-width: 100px"
                            controls-position="right"
                            @update:model-value="(val: any) => condition.value = val !== undefined && val !== null ? String(val) : ''"
                          />
                          <ElSelect
                            v-else-if="getFilterValueType(condition.field) === 'select'"
                            v-model="condition.value"
                            size="small"
                            class="flex-1"
                            style="min-width: 100px"
                            clearable
                            :placeholder="$t('form-manager.listDesign.filterValuePlaceholder')"
                          >
                            <ElOption
                              v-for="opt in getFilterFieldOptions(condition.field)"
                              :key="opt.value"
                              :label="opt.label"
                              :value="String(opt.value)"
                            />
                          </ElSelect>
                          <ElDatePicker
                            v-else-if="getFilterValueType(condition.field) === 'date'"
                            v-model="condition.value"
                            type="date"
                            size="small"
                            class="flex-1"
                            style="min-width: 140px"
                            value-format="YYYY-MM-DD"
                            :placeholder="$t('form-manager.listDesign.filterValuePlaceholder')"
                          />
                          <ElDatePicker
                            v-else-if="getFilterValueType(condition.field) === 'datetime'"
                            v-model="condition.value"
                            type="datetime"
                            size="small"
                            class="flex-1"
                            style="min-width: 180px"
                            value-format="YYYY-MM-DD HH:mm:ss"
                            :placeholder="$t('form-manager.listDesign.filterValuePlaceholder')"
                          />
                          <ElDatePicker
                            v-else-if="getFilterValueType(condition.field) === 'time'"
                            v-model="condition.value"
                            type="datetime"
                            size="small"
                            class="flex-1"
                            style="min-width: 140px"
                            value-format="HH:mm:ss"
                            :placeholder="$t('form-manager.listDesign.filterValuePlaceholder')"
                          />
                          <UserSelector
                            v-else-if="getFilterValueType(condition.field) === 'user'"
                            v-model="condition.value"
                            size="small"
                            class="flex-1"
                            style="min-width: 140px"
                          />
                          <DeptSelector
                            v-else-if="getFilterValueType(condition.field) === 'dept'"
                            v-model="condition.value"
                            size="small"
                            class="flex-1"
                            style="min-width: 140px"
                          />
                          <PostSelector
                            v-else-if="getFilterValueType(condition.field) === 'post'"
                            v-model="condition.value"
                            size="small"
                            class="flex-1"
                            style="min-width: 140px"
                          />
                          <RoleSelector
                            v-else-if="getFilterValueType(condition.field) === 'role'"
                            v-model="condition.value"
                            size="small"
                            class="flex-1"
                            style="min-width: 140px"
                          />
                          <FormSelector
                            v-else-if="getFilterValueType(condition.field) === 'form-selector'"
                            v-model="condition.value"
                            :form-code="getFilterFieldConfig(condition.field)?.formCode"
                            :value-field="getFilterFieldConfig(condition.field)?.valueField || 'id'"
                            :label-field="getFilterFieldConfig(condition.field)?.labelField || 'name'"
                            size="small"
                            class="flex-1"
                            style="min-width: 140px"
                          />
                          <ElInput
                            v-else
                            v-model="condition.value"
                            size="small"
                            class="flex-1"
                            style="min-width: 100px"
                            :placeholder="$t('form-manager.listDesign.filterValuePlaceholder')"
                          />
                        </template>
                        <ElInput
                          v-else-if="filterOperatorNeedsValue(condition.operator)"
                          v-model="condition.value"
                          size="small"
                          class="flex-1"
                          style="min-width: 100px"
                          :placeholder="
                            $t('form-manager.listDesign.filterValuePlaceholder')
                          "
                        />
                        <ElButton
                          type="danger"
                          size="small"
                          :icon="Trash2"
                          circle
                          @click="removeFilterCondition(index)"
                        />
                      </div>
                      <ElButton
                        type="primary"
                        size="small"
                        class="w-full"
                        @click="addFilterCondition"
                      >
                        {{ $t('form-manager.listDesign.addFilterCondition') }}
                      </ElButton>
                    </div>
                  </ElFormItem>
                </div>

                <!-- 容器类型选择 -->
                <div
                  class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                  @click="toggleSection('container')"
                >
                  <span class="font-bold">容器类型</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('container')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('container')">
                  <ElFormItem label="表单容器">
                    <ElRadioGroup v-model="listSettings.containerType">
                      <ElRadio value="drawer">Drawer（抽屉）</ElRadio>
                      <ElRadio value="dialog">Dialog（对话框）</ElRadio>
                      <ElRadio value="page">Page（独立页面）</ElRadio>
                      <ElRadio value="layout">Layout（系统布局）</ElRadio>
                    </ElRadioGroup>
                    <div
                      class="mt-1 text-xs text-[var(--el-text-color-secondary)]"
                    >
                      选择添加、编辑、查看表单时使用的容器类型
                    </div>
                  </ElFormItem>
                </div>

                <!-- Dialog 属性 -->
                <div
                  v-if="listSettings.containerType === 'dialog'"
                  class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                  @click="toggleSection('dialog')"
                >
                  <span class="font-bold">{{
                    $t('form-manager.listDesign.dialogProperties')
                  }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('dialog')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-if="listSettings.containerType === 'dialog'"
                  v-show="activeSections.includes('dialog')"
                >
                  <ElFormItem
                    :label="$t('form-manager.listDesign.dialogWidth')"
                  >
                    <ElSelect
                      v-model="listSettings.dialog.width"
                      class="w-full"
                    >
                      <ElOption
                        :label="$t('form-manager.listDesign.widthSmall')"
                        value="600px"
                      />
                      <ElOption
                        :label="$t('form-manager.listDesign.widthMedium')"
                        value="800px"
                      />
                      <ElOption
                        :label="$t('form-manager.listDesign.widthLarge')"
                        value="1000px"
                      />
                      <ElOption
                        :label="$t('form-manager.listDesign.widthExtraLarge')"
                        value="1200px"
                      />
                      <ElOption label="80%" value="80%" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem :label="$t('form-manager.listDesign.fullscreen')">
                    <ElSwitch v-model="listSettings.dialog.fullscreen" />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-manager.listDesign.draggable')">
                    <ElSwitch v-model="listSettings.dialog.draggable" />
                  </ElFormItem>
                  <ElFormItem
                    :label="$t('form-manager.listDesign.closeOnClickModal')"
                  >
                    <ElSwitch v-model="listSettings.dialog.closeOnClickModal" />
                  </ElFormItem>
                  <ElFormItem
                    :label="$t('form-manager.listDesign.closeOnPressEscape')"
                  >
                    <ElSwitch
                      v-model="listSettings.dialog.closeOnPressEscape"
                    />
                  </ElFormItem>
                </div>

                <!-- Drawer 属性 -->
                <div
                  v-if="listSettings.containerType === 'drawer'"
                  class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                  @click="toggleSection('drawer')"
                >
                  <span class="font-bold">Drawer 属性</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('drawer')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-if="listSettings.containerType === 'drawer'"
                  v-show="activeSections.includes('drawer')"
                >
                  <ElFormItem label="抽屉尺寸">
                    <ElSelect v-model="listSettings.drawer.size" class="w-full">
                      <ElOption label="600px" value="600px" />
                      <ElOption label="800px" value="800px" />
                      <ElOption label="1000px" value="1000px" />
                      <ElOption label="1200px" value="1200px" />
                      <ElOption label="50%" value="50%" />
                      <ElOption label="60%" value="60%" />
                      <ElOption label="80%" value="80%" />
                    </ElSelect>
                  </ElFormItem>
                  <ElFormItem label="打开方向">
                    <ElRadioGroup v-model="listSettings.drawer.direction">
                      <ElRadio value="rtl">从右往左</ElRadio>
                      <ElRadio value="ltr">从左往右</ElRadio>
                      <ElRadio value="ttb">从上往下</ElRadio>
                      <ElRadio value="btt">从下往上</ElRadio>
                    </ElRadioGroup>
                  </ElFormItem>
                  <ElFormItem label="显示标题栏">
                    <ElSwitch v-model="listSettings.drawer.withHeader" />
                  </ElFormItem>
                  <ElFormItem label="点击遮罩关闭">
                    <ElSwitch v-model="listSettings.drawer.closeOnClickModal" />
                  </ElFormItem>
                  <ElFormItem label="按 ESC 关闭">
                    <ElSwitch
                      v-model="listSettings.drawer.closeOnPressEscape"
                    />
                  </ElFormItem>
                </div>

                <!-- Page 属性 -->
                <div
                  v-if="listSettings.containerType === 'page'"
                  class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                  @click="toggleSection('page')"
                >
                  <span class="font-bold">{{
                    $t('form-manager.listDesign.pageProperties')
                  }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('page')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-if="listSettings.containerType === 'page'"
                  v-show="activeSections.includes('page')"
                >
                  <ElFormItem
                    :label="$t('form-manager.listDesign.showBackButton')"
                  >
                    <ElSwitch v-model="listSettings.page.showBackButton" />
                    <div
                      class="mt-1 text-xs text-[var(--el-text-color-secondary)]"
                    >
                      {{ $t('form-manager.listDesign.showBackButtonTip') }}
                    </div>
                  </ElFormItem>
                  <ElFormItem
                    :label="$t('form-manager.listDesign.openInNewTab')"
                  >
                    <ElSwitch v-model="listSettings.page.openInNewTab" />
                    <div
                      class="mt-1 text-xs text-[var(--el-text-color-secondary)]"
                    >
                      {{ $t('form-manager.listDesign.openInNewTabTip') }}
                    </div>
                  </ElFormItem>
                </div>

                <!-- Layout 属性 -->
                <div
                  v-if="listSettings.containerType === 'layout'"
                  class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                  @click="toggleSection('layout')"
                >
                  <span class="font-bold">Layout 属性</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('layout')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-if="listSettings.containerType === 'layout'"
                  v-show="activeSections.includes('layout')"
                >
                  <ElFormItem
                    :label="$t('form-manager.listDesign.layoutRenderMode')"
                  >
                    <ElRadioGroup v-model="listSettings.layout.renderMode">
                      <ElRadio value="condition">
                        {{ $t('form-manager.listDesign.conditionRender') }}
                      </ElRadio>
                      <ElRadio value="route">
                        {{ $t('form-manager.listDesign.routeRender') }}
                      </ElRadio>
                    </ElRadioGroup>
                    <div
                      class="mt-1 text-xs text-[var(--el-text-color-secondary)]"
                    >
                      {{
                        listSettings.layout.renderMode === 'condition'
                          ? $t('form-manager.listDesign.conditionRenderTip')
                          : $t('form-manager.listDesign.routeRenderTip')
                      }}
                    </div>
                  </ElFormItem>
                  <ElFormItem
                    :label="$t('form-manager.listDesign.showBackButton')"
                  >
                    <ElSwitch v-model="listSettings.layout.showBackButton" />
                    <div
                      class="mt-1 text-xs text-[var(--el-text-color-secondary)]"
                    >
                      {{ $t('form-manager.listDesign.showBackButtonTip') }}
                    </div>
                  </ElFormItem>
                </div>

                <!-- 按钮显示 -->
                <div
                  class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                  @click="toggleSection('buttons')"
                >
                  <span class="font-bold">{{
                    $t('form-manager.listDesign.buttonDisplay')
                  }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown v-if="activeSections.includes('buttons')" />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('buttons')">
                  <!-- 列表头部按钮 -->
                  <div class="mb-3 mt-2">
                    <div class="text-muted-foreground mb-2 text-xs font-medium">
                      {{ $t('form-manager.listDesign.toolbarButtons') }}
                    </div>
                    <div class="grid grid-cols-2 gap-x-4 gap-y-2">
                      <ElFormItem
                        :label="$t('form-manager.listDesign.addBtn')"
                        class="!mb-2"
                      >
                        <ElSwitch v-model="listSettings.buttons.showAdd" />
                      </ElFormItem>
                      <ElFormItem
                        :label="$t('form-manager.listDesign.batchDeleteBtn')"
                        class="!mb-2"
                      >
                        <ElSwitch
                          v-model="listSettings.buttons.showBatchDelete"
                        />
                      </ElFormItem>
                      <ElFormItem
                        :label="$t('form-manager.listDesign.exportBtn')"
                        class="!mb-2"
                      >
                        <ElSwitch v-model="listSettings.buttons.showExport" />
                      </ElFormItem>
                      <ElFormItem
                        :label="$t('form-manager.listDesign.importBtn')"
                        class="!mb-2"
                      >
                        <ElSwitch v-model="listSettings.buttons.showImport" />
                      </ElFormItem>
                    </div>
                  </div>

                  <!-- 列表项操作按钮 -->
                  <div class="mt-3">
                    <div class="text-muted-foreground mb-2 text-xs font-medium">
                      {{ $t('form-manager.listDesign.rowActionButtons') }}
                    </div>
                    <div class="grid grid-cols-2 gap-x-4 gap-y-2">
                      <ElFormItem
                        :label="$t('form-manager.listDesign.viewBtn')"
                        class="!mb-2"
                      >
                        <ElSwitch v-model="listSettings.buttons.showView" />
                      </ElFormItem>
                      <ElFormItem
                        :label="$t('form-manager.listDesign.editBtn')"
                        class="!mb-2"
                      >
                        <ElSwitch v-model="listSettings.buttons.showEdit" />
                      </ElFormItem>
                      <ElFormItem
                        :label="$t('form-manager.listDesign.deleteBtn')"
                        class="!mb-2"
                      >
                        <ElSwitch v-model="listSettings.buttons.showDelete" />
                      </ElFormItem>
                    </div>
                  </div>

                  <!-- 表单操作设置 -->
                  <div class="mt-3">
                    <div class="text-muted-foreground mb-2 text-xs font-medium">
                      {{ $t('form-manager.listDesign.formActionSettings') }}
                    </div>
                    <ElFormItem
                      :label="$t('form-manager.listDesign.showConfirmButton')"
                      class="!mb-2"
                    >
                      <ElSwitch v-model="listSettings.showConfirmButton" />
                    </ElFormItem>
                    <div class="text-muted-foreground mb-3 text-xs">
                      {{ $t('form-manager.listDesign.showConfirmButtonTip') }}
                    </div>
                    <ElFormItem
                      :label="$t('form-manager.listDesign.afterSaveAction')"
                      class="!mb-2"
                    >
                      <ElSelect
                        v-model="listSettings.afterSaveAction"
                        size="small"
                        class="w-full"
                      >
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.afterSaveClose')
                          "
                          value="close"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.afterSaveEditMode')
                          "
                          value="editMode"
                        />
                        <ElOption
                          :label="
                            $t('form-manager.listDesign.afterSaveContinueAdd')
                          "
                          value="continueAdd"
                        />
                      </ElSelect>
                    </ElFormItem>
                    <div class="text-muted-foreground mb-3 text-xs">
                      {{ $t('form-manager.listDesign.afterSaveActionTip') }}
                    </div>
                    <ElFormItem
                      v-if="isWorkflowForm"
                      :label="
                        $t('form-manager.listDesign.enableStartWorkflowOnAdd')
                      "
                      class="!mb-2"
                    >
                      <ElSwitch
                        v-model="listSettings.enableStartWorkflowOnAdd"
                      />
                    </ElFormItem>
                    <div
                      v-if="isWorkflowForm"
                      class="text-muted-foreground text-xs"
                    >
                      {{
                        $t(
                          'form-manager.listDesign.enableStartWorkflowOnAddTip',
                        )
                      }}
                    </div>
                  </div>
                </div>

                <!-- 子表操作按钮 -->
                <div
                  v-if="props.subTables && props.subTables.length > 0"
                  class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                  @click="toggleSection('subTableButtons')"
                >
                  <span class="font-bold">{{
                    $t('form-manager.listDesign.subTableButtons')
                  }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown
                      v-if="activeSections.includes('subTableButtons')"
                    />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div
                  v-if="props.subTables && props.subTables.length > 0"
                  v-show="activeSections.includes('subTableButtons')"
                >
                  <div class="text-muted-foreground mb-2 text-xs">
                    {{ $t('form-manager.listDesign.subTableButtonsTip') }}
                  </div>
                  <div class="mb-2">
                    <ElButton plain size="small" @click="addSubTableButton">
                      {{ $t('form-manager.listDesign.addSubTableButton') }}
                    </ElButton>
                  </div>

                  <div
                    v-if="listSettings.subTableButtons.length > 0"
                    class="flex flex-col gap-3"
                  >
                    <draggable
                      v-model="listSettings.subTableButtons"
                      item-key="id"
                      handle=".drag-handle"
                      animation="200"
                      class="flex flex-col gap-3"
                    >
                      <template #item="{ element, index }">
                        <div
                          class="border-border bg-background rounded-lg border p-3"
                        >
                          <!-- 按钮基础信息 -->
                          <div class="mb-3 flex items-center gap-2">
                            <div
                              class="drag-handle text-muted-foreground hover:text-foreground flex cursor-move items-center justify-center"
                            >
                              <GripVertical class="h-4 w-4" />
                            </div>
                            <ElInput
                              v-model="element.buttonText"
                              size="small"
                              :placeholder="
                                $t('form-manager.listDesign.subTableButtonText')
                              "
                              class="flex-1"
                            />
                            <ElButton
                              link
                              type="danger"
                              :icon="Trash2"
                              @click="removeSubTableButton(index)"
                            />
                            <ElButton
                              link
                              type="primary"
                              @click="toggleSubTableButtonExpand(element.id)"
                            >
                              <ElIcon>
                                <ArrowDown
                                  v-if="expandedSubTableButtons.has(element.id)"
                                />
                                <ArrowRight v-else />
                              </ElIcon>
                            </ElButton>
                          </div>

                          <!-- 按钮配置（可折叠） -->
                          <div
                            v-show="expandedSubTableButtons.has(element.id)"
                            class="flex flex-col gap-2"
                          >
                            <!-- 子表选择 -->
                            <ElFormItem
                              :label="
                                $t('form-manager.listDesign.selectSubTable')
                              "
                              class="!mb-0"
                            >
                              <ElSelect
                                v-model="element.subTableName"
                                size="small"
                                class="w-full"
                                :placeholder="
                                  $t(
                                    'form-manager.listDesign.selectSubTablePlaceholder',
                                  )
                                "
                                @change="
                                  (val) => onSubTableSelect(element, val)
                                "
                              >
                                <ElOption
                                  v-for="subTable in props.subTables"
                                  :key="subTable.tableName"
                                  :label="subTable.alias || subTable.tableName"
                                  :value="subTable.tableName"
                                />
                              </ElSelect>
                            </ElFormItem>

                            <!-- 子表单选择 -->
                            <ElFormItem
                              :label="
                                $t('form-manager.listDesign.selectSubForm')
                              "
                              class="!mb-0"
                            >
                              <ElSelect
                                v-model="element.subFormCode"
                                size="small"
                                class="w-full"
                                :placeholder="
                                  $t(
                                    'form-manager.listDesign.selectSubFormPlaceholder',
                                  )
                                "
                                :loading="formsLoading"
                                filterable
                                clearable
                              >
                                <ElOption
                                  v-for="form in publishedForms"
                                  :key="form.code"
                                  :label="form.name"
                                  :value="form.code"
                                >
                                  <div
                                    class="flex items-center justify-between"
                                  >
                                    <span>{{ form.name }}</span>
                                    <span class="ml-2 text-xs text-gray-400">{{
                                      form.code
                                    }}</span>
                                  </div>
                                </ElOption>
                              </ElSelect>
                            </ElFormItem>

                            <!-- 外键字段（只读） -->
                            <ElFormItem
                              :label="
                                $t('form-manager.listDesign.foreignKeyField')
                              "
                              class="!mb-0"
                            >
                              <ElInput
                                v-model="element.foreignKeyField"
                                size="small"
                                disabled
                                :placeholder="
                                  $t(
                                    'form-manager.listDesign.foreignKeyFieldPlaceholder',
                                  )
                                "
                              />
                            </ElFormItem>

                            <!-- 按钮样式 -->
                            <div class="border-border rounded border p-2">
                              <div
                                class="text-muted-foreground mb-2 text-xs font-medium"
                              >
                                {{ $t('form-manager.listDesign.buttonStyle') }}
                              </div>
                              <div class="grid grid-cols-2 gap-2">
                                <ElFormItem
                                  :label="
                                    $t('form-manager.listDesign.buttonType')
                                  "
                                  class="!mb-0"
                                >
                                  <ElSelect
                                    v-model="element.buttonType"
                                    size="small"
                                    class="w-full"
                                  >
                                    <ElOption label="Primary" value="primary" />
                                    <ElOption label="Success" value="success" />
                                    <ElOption label="Warning" value="warning" />
                                    <ElOption label="Danger" value="danger" />
                                    <ElOption label="Info" value="info" />
                                    <ElOption label="Default" value="default" />
                                  </ElSelect>
                                </ElFormItem>
                                <ElFormItem
                                  :label="
                                    $t('form-manager.listDesign.buttonIcon')
                                  "
                                  class="!mb-0"
                                >
                                  <ZqIconPicker
                                    v-model="element.buttonIcon"
                                    prefix="lucide"
                                    :auto-fetch-api="false"
                                    class="w-full"
                                  />
                                </ElFormItem>
                              </div>
                            </div>

                            <!-- 容器类型 -->
                            <ElFormItem
                              :label="
                                $t(
                                  'form-manager.listDesign.subFormContainerType',
                                )
                              "
                              class="!mb-0"
                            >
                              <ElRadioGroup
                                v-model="element.containerType"
                                size="small"
                              >
                                <ElRadio value="dialog">Dialog</ElRadio>
                                <ElRadio value="drawer">Drawer</ElRadio>
                                <ElRadio value="layout">Layout</ElRadio>
                              </ElRadioGroup>
                            </ElFormItem>

                            <!-- Dialog 配置 -->
                            <template v-if="element.containerType === 'dialog'">
                              <div class="grid grid-cols-2 gap-2">
                                <ElFormItem
                                  :label="
                                    $t('form-manager.listDesign.dialogWidth')
                                  "
                                  class="!mb-0"
                                >
                                  <ElSelect
                                    v-model="element.containerConfig.width"
                                    size="small"
                                    class="w-full"
                                  >
                                    <ElOption label="600px" value="600px" />
                                    <ElOption label="800px" value="800px" />
                                    <ElOption label="1000px" value="1000px" />
                                    <ElOption label="80%" value="80%" />
                                    <ElOption label="90%" value="90%" />
                                  </ElSelect>
                                </ElFormItem>
                                <ElFormItem
                                  :label="
                                    $t('form-manager.listDesign.fullscreen')
                                  "
                                  class="!mb-0"
                                >
                                  <ElSwitch
                                    v-model="element.containerConfig.fullscreen"
                                    size="small"
                                  />
                                </ElFormItem>
                              </div>
                            </template>

                            <!-- Drawer 配置 -->
                            <template v-if="element.containerType === 'drawer'">
                              <div class="grid grid-cols-2 gap-2">
                                <ElFormItem
                                  :label="
                                    $t('form-manager.listDesign.drawerSize')
                                  "
                                  class="!mb-0"
                                >
                                  <ElSelect
                                    v-model="element.containerConfig.size"
                                    size="small"
                                    class="w-full"
                                  >
                                    <ElOption label="50%" value="50%" />
                                    <ElOption label="60%" value="60%" />
                                    <ElOption label="70%" value="70%" />
                                    <ElOption label="80%" value="80%" />
                                  </ElSelect>
                                </ElFormItem>
                                <ElFormItem
                                  :label="
                                    $t(
                                      'form-manager.listDesign.drawerDirection',
                                    )
                                  "
                                  class="!mb-0"
                                >
                                  <ElSelect
                                    v-model="element.containerConfig.direction"
                                    size="small"
                                    class="w-full"
                                  >
                                    <ElOption label="从右往左" value="rtl" />
                                    <ElOption label="从左往右" value="ltr" />
                                    <ElOption label="从上往下" value="ttb" />
                                    <ElOption label="从下往上" value="btt" />
                                  </ElSelect>
                                </ElFormItem>
                              </div>
                            </template>

                            <!-- Layout 配置 -->
                            <!-- <template v-if="element.containerType === 'layout'">
                              <ElFormItem :label="$t('form-manager.listDesign.layoutRenderMode')" class="!mb-0">
                                <ElRadioGroup v-model="element.containerConfig.renderMode" size="small">
                                  <ElRadio value="condition">{{ $t('form-manager.listDesign.conditionRender') }}</ElRadio>
                                  <ElRadio value="route">{{ $t('form-manager.listDesign.routeRender') }}</ElRadio>
                                </ElRadioGroup>
                              </ElFormItem>
                            </template> -->
                          </div>
                        </div>
                      </template>
                    </draggable>
                  </div>

                  <div
                    v-else
                    class="text-muted-foreground py-4 text-center text-xs"
                  >
                    {{ $t('form-manager.listDesign.noSubTableButtons') }}
                  </div>
                </div>

                <!-- 自定义按钮 -->
                <div
                  class="group-title border-border text-muted-foreground hover:text-primary mb-2 mt-4 flex cursor-pointer select-none items-center justify-between border-b pb-2 text-xs"
                  @click="toggleSection('customButtons')"
                >
                  <span class="font-bold">{{
                    $t('form-manager.listDesign.customButtons')
                  }}</span>
                  <ElIcon class="h-4 w-4">
                    <ArrowDown
                      v-if="activeSections.includes('customButtons')"
                    />
                    <ArrowRight v-else />
                  </ElIcon>
                </div>
                <div v-show="activeSections.includes('customButtons')">
                  <div class="mb-2 flex gap-2">
                    <ElButton plain size="small" @click="addCustomButton">
                      {{ $t('form-manager.listDesign.addCustomButton') }}
                    </ElButton>
                    <ElButton
                      plain
                      size="small"
                      type="success"
                      @click="addGenerateDocumentButton"
                    >
                      {{ $t('form-manager.generateDocument.buttonLabel') }}
                    </ElButton>
                  </div>

                  <div
                    v-if="listSettings.customButtons.length > 0"
                    class="flex flex-col gap-3"
                  >
                    <draggable
                      v-model="listSettings.customButtons"
                      item-key="id"
                      handle=".drag-handle"
                      animation="200"
                      class="flex flex-col gap-3"
                    >
                      <template #item="{ element, index }">
                        <div
                          class="border-border bg-background rounded-lg border p-3"
                        >
                          <!-- 按钮基础信息 -->
                          <div class="mb-3 flex items-center gap-2">
                            <div
                              class="drag-handle text-muted-foreground hover:text-foreground flex cursor-move items-center justify-center"
                            >
                              <GripVertical class="h-4 w-4" />
                            </div>
                            <ElInput
                              v-model="element.name"
                              size="small"
                              :placeholder="
                                $t('form-manager.listDesign.buttonName')
                              "
                              class="flex-1"
                            />
                            <ElButton
                              link
                              type="danger"
                              :icon="Trash2"
                              @click="removeCustomButton(index)"
                            />
                            <ElButton
                              link
                              type="primary"
                              @click="toggleButtonExpand(element.id)"
                            >
                              <ElIcon>
                                <ArrowDown
                                  v-if="expandedButtons.has(element.id)"
                                />
                                <ArrowRight v-else />
                              </ElIcon>
                            </ElButton>
                          </div>

                          <!-- 按钮配置（可折叠） -->
                          <div
                            v-show="expandedButtons.has(element.id)"
                            class="flex flex-col gap-2"
                          >
                            <ElFormItem
                              :label="$t('form-manager.listDesign.buttonType')"
                              class="!mb-0"
                            >
                              <ElSelect
                                v-model="element.type"
                                size="small"
                                class="w-full"
                              >
                                <ElOption label="Primary" value="primary" />
                                <ElOption label="Success" value="success" />
                                <ElOption label="Warning" value="warning" />
                                <ElOption label="Danger" value="danger" />
                                <ElOption label="Info" value="info" />
                                <ElOption label="Default" value="default" />
                              </ElSelect>
                            </ElFormItem>

                            <ElFormItem
                              :label="
                                $t('form-manager.listDesign.buttonPosition')
                              "
                              class="!mb-0"
                            >
                              <ElRadioGroup
                                v-model="element.position"
                                size="small"
                              >
                                <ElRadio
                                  value="toolbar"
                                  :disabled="
                                    element.actionType === 'generate_document'
                                  "
                                >
                                  {{ $t('form-manager.listDesign.toolbar') }}
                                </ElRadio>
                                <ElRadio
                                  value="tools"
                                  :disabled="
                                    element.actionType === 'generate_document'
                                  "
                                >
                                  {{ $t('form-manager.listDesign.tools') }}
                                </ElRadio>
                                <ElRadio value="row">
                                  {{ $t('form-manager.listDesign.row') }}
                                </ElRadio>
                              </ElRadioGroup>
                              <div
                                v-if="
                                  element.actionType === 'generate_document'
                                "
                                class="text-muted-foreground mt-1 text-xs"
                              >
                                {{
                                  $t(
                                    'form-manager.generateDocument.positionHint',
                                  )
                                }}
                              </div>
                            </ElFormItem>

                            <!-- 图标和显示 -->
                            <div class="border-border rounded border p-2">
                              <div
                                class="text-muted-foreground mb-2 text-xs font-medium"
                              >
                                {{
                                  $t('form-manager.listDesign.iconAndDisplay')
                                }}
                              </div>
                              <ElFormItem
                                :label="
                                  $t('form-manager.listDesign.buttonIcon')
                                "
                                class="!mb-0"
                              >
                                <ZqIconPicker
                                  v-model="element.icon"
                                  prefix="lucide"
                                  :auto-fetch-api="false"
                                  class="w-full"
                                />
                              </ElFormItem>
                              <div class="mt-2 flex items-center gap-1">
                                <ElSwitch
                                  v-model="element.iconOnly"
                                  size="small"
                                />
                                <span class="text-xs">{{
                                  $t('form-manager.listDesign.iconOnly')
                                }}</span>
                              </div>
                            </div>

                            <!-- 样式属性 -->
                            <div class="border-border rounded border p-2">
                              <div
                                class="text-muted-foreground mb-2 text-xs font-medium"
                              >
                                {{ $t('form-manager.listDesign.styleOptions') }}
                              </div>
                              <div class="grid grid-cols-2 gap-2">
                                <div class="flex items-center gap-1">
                                  <ElSwitch
                                    v-model="element.plain"
                                    size="small"
                                  />
                                  <span class="text-xs">{{
                                    $t('form-manager.listDesign.plain')
                                  }}</span>
                                </div>
                                <div class="flex items-center gap-1">
                                  <ElSwitch
                                    v-model="element.round"
                                    size="small"
                                  />
                                  <span class="text-xs">{{
                                    $t('form-manager.listDesign.round')
                                  }}</span>
                                </div>
                                <div class="flex items-center gap-1">
                                  <ElSwitch
                                    v-model="element.circle"
                                    size="small"
                                  />
                                  <span class="text-xs">{{
                                    $t('form-manager.listDesign.circle')
                                  }}</span>
                                </div>
                                <div class="flex items-center gap-1">
                                  <ElSwitch
                                    v-model="element.text"
                                    size="small"
                                  />
                                  <span class="text-xs">{{
                                    $t('form-manager.listDesign.textBtn')
                                  }}</span>
                                </div>
                                <div class="flex items-center gap-1">
                                  <ElSwitch
                                    v-model="element.link"
                                    size="small"
                                  />
                                  <span class="text-xs">{{
                                    $t('form-manager.listDesign.linkBtn')
                                  }}</span>
                                </div>
                              </div>
                              <ElFormItem
                                :label="
                                  $t('form-manager.listDesign.buttonSize')
                                "
                                class="!mb-0 mt-2"
                              >
                                <ElSelect
                                  v-model="element.size"
                                  size="small"
                                  class="w-full"
                                >
                                  <ElOption
                                    :label="
                                      $t('form-manager.listDesign.sizeLarge')
                                    "
                                    value="large"
                                  />
                                  <ElOption
                                    :label="
                                      $t('form-manager.listDesign.sizeDefault')
                                    "
                                    value="default"
                                  />
                                  <ElOption
                                    :label="
                                      $t('form-manager.listDesign.sizeSmall')
                                    "
                                    value="small"
                                  />
                                </ElSelect>
                              </ElFormItem>
                            </div>

                            <!-- 状态控制 -->
                            <div class="border-border rounded border p-2">
                              <div
                                class="text-muted-foreground mb-2 text-xs font-medium"
                              >
                                {{ $t('form-manager.listDesign.stateControl') }}
                              </div>
                              <div class="mb-2 flex items-center gap-1">
                                <ElSwitch
                                  v-model="element.disabled"
                                  size="small"
                                />
                                <span class="text-xs">{{
                                  $t('form-manager.listDesign.disabled')
                                }}</span>
                              </div>
                              <ElFormItem
                                :label="
                                  $t(
                                    'form-manager.listDesign.disabledCondition',
                                  )
                                "
                                class="!mb-0"
                              >
                                <ElInput
                                  v-model="element.disabledCondition"
                                  size="small"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.disabledConditionPlaceholder',
                                    )
                                  "
                                />
                              </ElFormItem>
                            </div>

                            <!-- 提示和徽标 -->
                            <ElFormItem
                              :label="$t('form-manager.listDesign.tooltip')"
                              class="!mb-0"
                            >
                              <ElInput
                                v-model="element.tooltip"
                                size="small"
                                :placeholder="
                                  $t(
                                    'form-manager.listDesign.tooltipPlaceholder',
                                  )
                                "
                              />
                            </ElFormItem>

                            <div class="grid grid-cols-2 gap-2">
                              <ElFormItem
                                :label="$t('form-manager.listDesign.badge')"
                                class="!mb-0"
                              >
                                <ElInput
                                  v-model="element.badge"
                                  size="small"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.badgePlaceholder',
                                    )
                                  "
                                />
                              </ElFormItem>
                              <ElFormItem
                                :label="$t('form-manager.listDesign.badgeType')"
                                class="!mb-0"
                              >
                                <ElSelect
                                  v-model="element.badgeType"
                                  size="small"
                                  class="w-full"
                                >
                                  <ElOption label="Primary" value="primary" />
                                  <ElOption label="Success" value="success" />
                                  <ElOption label="Warning" value="warning" />
                                  <ElOption label="Danger" value="danger" />
                                  <ElOption label="Info" value="info" />
                                </ElSelect>
                              </ElFormItem>
                            </div>

                            <ElFormItem
                              :label="$t('form-manager.listDesign.actionType')"
                              class="!mb-0"
                            >
                              <ElSelect
                                v-model="element.actionType"
                                size="small"
                                class="w-full"
                              >
                                <ElOption
                                  :label="
                                    $t('form-manager.listDesign.actionLink')
                                  "
                                  value="link"
                                />
                                <ElOption
                                  :label="
                                    $t('form-manager.listDesign.actionApi')
                                  "
                                  value="api"
                                />
                                <ElOption
                                  :label="
                                    $t('form-manager.listDesign.actionEvent')
                                  "
                                  value="event"
                                />
                                <ElOption
                                  :label="
                                    $t('form-manager.listDesign.actionAgent')
                                  "
                                  value="agent"
                                />
                                <ElOption
                                  :label="
                                    $t('form-manager.listDesign.actionPage')
                                  "
                                  value="page"
                                />
                              </ElSelect>
                            </ElFormItem>

                            <!-- Link 类型配置 -->
                            <template v-if="element.actionType === 'link'">
                              <ElFormItem
                                :label="$t('form-manager.listDesign.linkUrl')"
                                class="!mb-0"
                              >
                                <ElInput
                                  v-model="element.actionConfig.url"
                                  size="small"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.linkUrlPlaceholder',
                                    )
                                  "
                                />
                              </ElFormItem>
                              <ElFormItem
                                :label="
                                  $t('form-manager.listDesign.openInNewTab')
                                "
                                class="!mb-0"
                              >
                                <ElSwitch
                                  v-model="element.actionConfig.openInNewTab"
                                  size="small"
                                />
                              </ElFormItem>
                            </template>

                            <!-- API 类型配置 -->
                            <template v-if="element.actionType === 'api'">
                              <ElFormItem
                                :label="$t('form-manager.listDesign.apiUrl')"
                                class="!mb-0"
                              >
                                <ElInput
                                  v-model="element.actionConfig.apiUrl"
                                  size="small"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.apiUrlPlaceholder',
                                    )
                                  "
                                />
                              </ElFormItem>
                              <ElFormItem
                                :label="$t('form-manager.listDesign.apiMethod')"
                                class="!mb-0"
                              >
                                <ElSelect
                                  v-model="element.actionConfig.apiMethod"
                                  size="small"
                                  class="w-full"
                                >
                                  <ElOption label="GET" value="GET" />
                                  <ElOption label="POST" value="POST" />
                                  <ElOption label="PUT" value="PUT" />
                                  <ElOption label="DELETE" value="DELETE" />
                                </ElSelect>
                              </ElFormItem>

                              <!-- 确认对话框配置 -->
                              <div class="border-border rounded border p-2">
                                <div
                                  class="text-muted-foreground mb-2 text-xs font-medium"
                                >
                                  {{
                                    $t('form-manager.listDesign.confirmDialog')
                                  }}
                                </div>
                                <ElFormItem
                                  :label="
                                    $t('form-manager.listDesign.confirmTitle')
                                  "
                                  class="!mb-2"
                                >
                                  <ElInput
                                    v-model="element.actionConfig.confirmTitle"
                                    size="small"
                                    :placeholder="
                                      $t(
                                        'form-manager.listDesign.confirmTitlePlaceholder',
                                      )
                                    "
                                  />
                                </ElFormItem>
                                <ElFormItem
                                  :label="
                                    $t('form-manager.listDesign.confirmMessage')
                                  "
                                  class="!mb-0"
                                >
                                  <ElInput
                                    v-model="
                                      element.actionConfig.confirmMessage
                                    "
                                    size="small"
                                    type="textarea"
                                    :rows="2"
                                    :placeholder="
                                      $t(
                                        'form-manager.listDesign.confirmMessagePlaceholder',
                                      )
                                    "
                                  />
                                </ElFormItem>
                              </div>

                              <!-- 提示消息配置 -->
                              <div class="border-border rounded border p-2">
                                <div
                                  class="text-muted-foreground mb-2 text-xs font-medium"
                                >
                                  {{
                                    $t('form-manager.listDesign.messageConfig')
                                  }}
                                </div>
                                <ElFormItem
                                  :label="
                                    $t('form-manager.listDesign.successMessage')
                                  "
                                  class="!mb-2"
                                >
                                  <ElInput
                                    v-model="
                                      element.actionConfig.successMessage
                                    "
                                    size="small"
                                    :placeholder="
                                      $t(
                                        'form-manager.listDesign.successMessagePlaceholder',
                                      )
                                    "
                                  />
                                </ElFormItem>
                                <ElFormItem
                                  :label="
                                    $t('form-manager.listDesign.errorMessage')
                                  "
                                  class="!mb-0"
                                >
                                  <ElInput
                                    v-model="element.actionConfig.errorMessage"
                                    size="small"
                                    :placeholder="
                                      $t(
                                        'form-manager.listDesign.errorMessagePlaceholder',
                                      )
                                    "
                                  />
                                </ElFormItem>
                              </div>

                              <div class="flex items-center gap-1">
                                <ElSwitch
                                  v-model="
                                    element.actionConfig.reloadAfterSuccess
                                  "
                                  size="small"
                                />
                                <span class="text-xs">{{
                                  $t(
                                    'form-manager.listDesign.reloadAfterSuccess',
                                  )
                                }}</span>
                              </div>
                            </template>

                            <!-- Event 类型配置 -->
                            <template v-if="element.actionType === 'event'">
                              <ElFormItem
                                :label="$t('form-manager.listDesign.eventName')"
                                class="!mb-0"
                              >
                                <ElInput
                                  v-model="element.actionConfig.eventName"
                                  size="small"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.eventNamePlaceholder',
                                    )
                                  "
                                />
                              </ElFormItem>
                            </template>

                            <!-- Agent 类型配置 -->
                            <template v-if="element.actionType === 'agent'">
                              <ElFormItem
                                :label="$t('form-manager.listDesign.agentId')"
                                class="!mb-0"
                              >
                                <ElSelect
                                  v-model="element.actionConfig.agentId"
                                  size="small"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.agentIdPlaceholder',
                                    )
                                  "
                                  :loading="agentsLoading"
                                  filterable
                                  clearable
                                  class="w-full"
                                  @change="
                                    (val) => {
                                      const agent = publishedAgents.find(
                                        (a) => a.id === val,
                                      );
                                      if (agent) {
                                        element.actionConfig.agentCode =
                                          agent.code;
                                      }
                                    }
                                  "
                                >
                                  <ElOption
                                    v-for="agent in publishedAgents"
                                    :key="agent.id"
                                    :label="`${agent.name} (${agent.code})`"
                                    :value="agent.id"
                                  >
                                    <div
                                      class="flex items-center justify-between"
                                    >
                                      <span>{{ agent.name }}</span>
                                      <span
                                        class="ml-2 text-xs text-gray-400"
                                        >{{ agent.code }}</span>
                                    </div>
                                  </ElOption>
                                </ElSelect>
                              </ElFormItem>
                              <ElFormItem
                                :label="$t('form-manager.listDesign.agentCode')"
                                class="!mb-0"
                              >
                                <ElInput
                                  v-model="element.actionConfig.agentCode"
                                  size="small"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.agentCodePlaceholder',
                                    )
                                  "
                                  disabled
                                />
                              </ElFormItem>
                              <ElFormItem
                                :label="
                                  $t('form-manager.listDesign.initialMessage')
                                "
                                class="!mb-0"
                              >
                                <ElInput
                                  v-model="element.actionConfig.initialMessage"
                                  size="small"
                                  type="textarea"
                                  :rows="3"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.initialMessagePlaceholder',
                                    )
                                  "
                                />
                              </ElFormItem>
                              <div class="flex items-center gap-1">
                                <ElSwitch
                                  v-model="element.actionConfig.autoSend"
                                  size="small"
                                />
                                <span class="text-xs">{{
                                  $t('form-manager.listDesign.autoSend')
                                }}</span>
                              </div>
                              <ElFormItem
                                :label="
                                  $t('form-manager.listDesign.dialogTitle')
                                "
                                class="!mb-0"
                              >
                                <ElInput
                                  v-model="element.actionConfig.dialogTitle"
                                  size="small"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.dialogTitlePlaceholder',
                                    )
                                  "
                                />
                              </ElFormItem>
                              <div class="grid grid-cols-2 gap-2">
                                <ElFormItem
                                  :label="
                                    $t(
                                      'form-manager.listDesign.pageDialogWidth',
                                    )
                                  "
                                  class="!mb-0"
                                >
                                  <ElInput
                                    v-model="element.actionConfig.dialogWidth"
                                    size="small"
                                    placeholder="80%"
                                  />
                                </ElFormItem>
                                <ElFormItem
                                  :label="
                                    $t(
                                      'form-manager.listDesign.pageDialogFullscreen',
                                    )
                                  "
                                  class="!mb-0"
                                >
                                  <ElSwitch
                                    v-model="
                                      element.actionConfig.dialogFullscreen
                                    "
                                    size="small"
                                  />
                                </ElFormItem>
                              </div>
                            </template>

                            <!-- Page 类型配置 -->
                            <template v-if="element.actionType === 'page'">
                              <ElFormItem
                                :label="$t('form-manager.listDesign.pageCode')"
                                class="!mb-0"
                              >
                                <ElSelect
                                  v-model="element.actionConfig.pageCode"
                                  size="small"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.pageCodePlaceholder',
                                    )
                                  "
                                  :loading="pagesLoading"
                                  filterable
                                  clearable
                                  class="w-full"
                                >
                                  <ElOption
                                    v-for="page in publishedPages"
                                    :key="page.code"
                                    :label="page.name"
                                    :value="page.code"
                                  >
                                    <div
                                      class="flex items-center justify-between"
                                    >
                                      <span>{{ page.name }}</span>
                                      <span
                                        class="ml-2 text-xs text-gray-400"
                                        >{{ page.code }}</span>
                                    </div>
                                  </ElOption>
                                </ElSelect>
                              </ElFormItem>
                              <ElFormItem
                                :label="
                                  $t('form-manager.listDesign.dialogTitle')
                                "
                                class="!mb-0"
                              >
                                <ElInput
                                  v-model="element.actionConfig.dialogTitle"
                                  size="small"
                                  :placeholder="
                                    $t(
                                      'form-manager.listDesign.dialogTitlePlaceholder',
                                    )
                                  "
                                />
                              </ElFormItem>
                              <div class="grid grid-cols-2 gap-2">
                                <ElFormItem
                                  :label="
                                    $t(
                                      'form-manager.listDesign.pageDialogWidth',
                                    )
                                  "
                                  class="!mb-0"
                                >
                                  <ElInput
                                    v-model="element.actionConfig.dialogWidth"
                                    size="small"
                                    placeholder="80%"
                                  />
                                </ElFormItem>
                                <ElFormItem
                                  :label="
                                    $t(
                                      'form-manager.listDesign.pageDialogFullscreen',
                                    )
                                  "
                                  class="!mb-0"
                                >
                                  <ElSwitch
                                    v-model="
                                      element.actionConfig.dialogFullscreen
                                    "
                                    size="small"
                                  />
                                </ElFormItem>
                              </div>
                            </template>

                            <ElFormItem
                              :label="
                                $t('form-manager.listDesign.showCondition')
                              "
                              class="!mb-0"
                            >
                              <ElInput
                                v-model="element.showCondition"
                                size="small"
                                :placeholder="
                                  $t(
                                    'form-manager.listDesign.showConditionPlaceholder',
                                  )
                                "
                              />
                            </ElFormItem>

                            <ElFormItem
                              :label="
                                $t('form-manager.listDesign.permissionCode')
                              "
                              class="!mb-0"
                            >
                              <ElInput
                                v-model="element.permissionCode"
                                size="small"
                                :placeholder="
                                  $t(
                                    'form-manager.listDesign.permissionCodePlaceholder',
                                  )
                                "
                              />
                            </ElFormItem>
                          </div>
                        </div>
                      </template>
                    </draggable>
                  </div>

                  <div
                    v-else
                    class="text-muted-foreground py-4 text-center text-xs"
                  >
                    {{ $t('form-manager.listDesign.noCustomButtons') }}
                  </div>
                </div>
              </ElForm>
            </div>
          </ElScrollbar>
        </div>
      </div>
    </div>
    <!-- 中间主要配置区 -->
    <div class="flex-1 overflow-hidden">
      <ElScrollbar class="h-full">
        <div class="p-4">
          <!-- 查询字段配置 -->
          <div
            class="border-border bg-card mb-4 min-h-[350px] rounded-lg border shadow-sm"
          >
            <div class="border-border border-b px-4 py-3">
              <h3 class="font-medium">
                {{ $t('form-manager.listDesign.queryConfigTitle') }}
              </h3>
            </div>
            <div class="p-4">
              <div v-if="queryFields.length > 0" class="flex flex-col gap-2">
                <!-- 表头 -->
                <div
                  class="text-muted-foreground flex items-center px-2 text-xs"
                >
                  <div class="w-8 text-center">
                    {{ $t('form-manager.listDesign.sort') }}
                  </div>
                  <div class="w-36 px-2">
                    {{ $t('form-manager.listDesign.displayName') }}
                  </div>
                  <div class="w-28 px-2">
                    {{ $t('form-manager.listDesign.fieldKey') }}
                  </div>
                  <div class="flex-1"></div>
                  <div class="w-28 px-2">
                    {{ $t('form-manager.listDesign.queryType') }}
                  </div>
                  <div class="w-24 px-2">
                    {{ $t('form-manager.listDesign.componentType') }}
                  </div>
                  <div class="w-24 px-2">
                    {{ $t('form-manager.listDesign.width') }}
                  </div>
                  <div class="w-28 px-2">
                    {{ $t('form-manager.listDesign.defaultValue') }}
                  </div>
                  <div class="w-14 px-1 text-center">
                    {{ $t('form-manager.listDesign.hidden') }}
                  </div>
                  <div class="w-14 px-1 text-center">
                    {{ $t('form-manager.listDesign.showTime') }}
                  </div>
                  <div class="w-14 px-1 text-center">
                    {{ $t('form-manager.listDesign.multiple') }}
                  </div>
                  <div class="w-20 px-1 text-center">
                    {{ $t('form-manager.listDesign.caseSensitive') }}
                  </div>
                  <div class="w-10 text-center">
                    {{ $t('form-manager.listDesign.actions') }}
                  </div>
                </div>

                <!-- 列表项 -->
                <draggable
                  v-model="queryFields"
                  item-key="field"
                  handle=".drag-handle"
                  animation="200"
                  class="flex flex-col gap-2"
                >
                  <template #item="{ element, index }">
                    <div
                      class="border-border bg-background hover:border-primary group flex items-center rounded-md border p-2 transition-colors hover:shadow-sm"
                    >
                      <!-- 拖拽手柄 -->
                      <div
                        class="drag-handle text-muted-foreground hover:text-foreground flex w-8 cursor-move items-center justify-center"
                      >
                        <GripVertical class="h-4 w-4" />
                      </div>

                      <!-- 显示名称 (可编辑) -->
                      <div class="w-36 px-2">
                        <ElInput v-model="element.label" size="small" />
                      </div>

                      <!-- 字段键值 (不可编辑) -->
                      <div class="w-28 px-2">
                        <span
                          class="text-muted-foreground truncate text-xs"
                          :title="element.field"
                          >{{ element.field }}</span
                        >
                      </div>

                      <!-- 占位符，把后面的推到右边 -->
                      <div class="flex-1"></div>

                      <!-- 查询类型 -->
                      <div class="w-28 px-2">
                        <ElSelect
                          v-model="element.type"
                          size="small"
                          class="w-full"
                          :disabled="
                            isSelectorComponent(element.originalComponent)
                          "
                        >
                          <!-- 日期组件不显示模糊匹配选项 -->
                          <ElOption
                            v-if="!isDateComponent(element.originalComponent)"
                            :label="$t('form-manager.listDesign.matchLike')"
                            value="like"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.matchEq')"
                            value="eq"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.matchRange')"
                            value="range"
                          />
                          <ElOption
                            v-if="
                              isSelectorComponent(element.originalComponent)
                            "
                            :label="$t('form-manager.listDesign.matchIn')"
                            value="in"
                          />
                          <!-- 文本输入组件显示空格模糊搜索选项 -->
                          <ElOption
                            v-if="!isDateComponent(element.originalComponent) && !isSelectorComponent(element.originalComponent)"
                            :label="$t('form-manager.listDesign.matchSpaceLikeAnd')"
                            value="space_like_and"
                          />
                          <ElOption
                            v-if="!isDateComponent(element.originalComponent) && !isSelectorComponent(element.originalComponent)"
                            :label="$t('form-manager.listDesign.matchSpaceLikeOr')"
                            value="space_like_or"
                          />
                          <!-- 文本输入组件显示空格精确搜索选项 -->
                          <ElOption
                            v-if="!isDateComponent(element.originalComponent) && !isSelectorComponent(element.originalComponent)"
                            :label="$t('form-manager.listDesign.matchSpaceEqAnd')"
                            value="space_eq_and"
                          />
                          <ElOption
                            v-if="!isDateComponent(element.originalComponent) && !isSelectorComponent(element.originalComponent)"
                            :label="$t('form-manager.listDesign.matchSpaceEqOr')"
                            value="space_eq_or"
                          />
                        </ElSelect>
                      </div>

                      <!-- 组件类型（只读显示，自动继承表单设计） -->
                      <div class="w-24 px-2">
                        <span
                          class="text-muted-foreground text-xs"
                          :title="
                            element.originalComponent || element.component
                          "
                        >
                          {{ getComponentLabel(element.component) }}
                        </span>
                      </div>

                      <!-- 宽度 -->
                      <div class="w-24 px-2">
                        <ElSelect
                          v-model="element.width"
                          size="small"
                          class="w-full"
                        >
                          <ElOption
                            :label="$t('form-manager.listDesign.width18')"
                            :value="3"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.width16')"
                            :value="4"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.width14')"
                            :value="6"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.width13')"
                            :value="8"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.width12')"
                            :value="12"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.widthFull')"
                            :value="24"
                          />
                        </ElSelect>
                      </div>

                      <!-- 默认值 -->
                      <div class="w-28 px-2">
                        <ElInput
                          v-model="element.defaultValue"
                          size="small"
                          :placeholder="$t('form-manager.listDesign.none')"
                        />
                      </div>

                      <!-- 是否隐藏 -->
                      <div class="flex w-14 items-center justify-center px-1">
                        <ElSwitch v-model="element.hidden" size="small" />
                      </div>

                      <!-- 显示时间 (仅日期时间类型字段可用) -->
                      <div class="flex w-14 items-center justify-center px-1">
                        <ElSwitch
                          v-model="element.showTime"
                          size="small"
                          :disabled="
                            !isDateComponent(element.originalComponent) ||
                            !element.dbType?.toLowerCase().includes('timestamp')
                          "
                        />
                      </div>

                      <!-- 是否多选 (下拉框可切换，选择器组件默认开启且不可修改) -->
                      <div class="flex w-14 items-center justify-center px-1">
                        <ElSwitch
                          v-model="element.multiple"
                          size="small"
                          :disabled="element.component !== 'select'"
                        />
                      </div>

                      <!-- 大小写敏感 (仅文本类查询类型有效，如 like/space_and/space_or) -->
                      <div class="flex w-20 items-center justify-center px-1">
                        <ElSwitch
                          v-model="element.caseSensitive"
                          size="small"
                        />
                      </div>

                      <!-- 操作 -->
                      <div class="flex w-10 items-center justify-center">
                        <ElButton
                          link
                          type="danger"
                          :icon="Trash2"
                          @click="removeQueryField(index)"
                        />
                      </div>
                    </div>
                  </template>
                </draggable>
              </div>

              <div
                v-else
                class="text-muted-foreground flex min-h-[270px] flex-col items-center justify-center py-8"
              >
                <div class="bg-muted mb-2 rounded-full p-4">
                  <Search class="h-8 w-8 opacity-50" />
                </div>
                <span class="text-sm">{{
                  $t('form-manager.listDesign.noQueryFields')
                }}</span>
                <span class="text-xs opacity-70">{{
                  $t('form-manager.listDesign.selectQueryTip')
                }}</span>
              </div>
            </div>
          </div>

          <!-- 列表字段配置（仅 Table 模式） -->
          <div
            v-if="listSettings.listType === 'table'"
            class="border-border bg-card min-h-[350px] rounded-lg border shadow-sm"
          >
            <div class="border-border border-b px-4 py-3">
              <h3 class="font-medium">
                {{ $t('form-manager.listDesign.listConfigTitle') }}
              </h3>
            </div>
            <div class="p-4">
              <div v-if="listColumns.length > 0" class="flex flex-col gap-3">
                <!-- 列表项 -->
                <draggable
                  v-model="listColumns"
                  item-key="field"
                  handle=".drag-handle"
                  animation="200"
                  class="flex flex-col gap-3"
                >
                  <template #item="{ element, index }">
                    <div
                      class="border-border bg-background hover:border-primary rounded-lg border transition-colors"
                    >
                      <!-- 第一行：基础信息 -->
                      <div
                        class="border-border flex items-center gap-2 border-b p-3"
                      >
                        <!-- 拖拽手柄 -->
                        <div
                          class="drag-handle text-muted-foreground hover:text-foreground flex cursor-move items-center justify-center"
                        >
                          <GripVertical class="h-4 w-4" />
                        </div>

                        <!-- 列名 -->
                        <div class="w-32">
                          <ElInput
                            v-model="element.label"
                            size="small"
                            :placeholder="
                              $t('form-manager.listDesign.columnName')
                            "
                            clearable
                          />
                        </div>

                        <!-- 字段 -->
                        <div
                          class="text-muted-foreground w-28 truncate text-xs"
                          :title="element.field"
                        >
                          {{ element.field }}
                        </div>

                        <div class="flex-1"></div>

                        <!-- 宽度 -->
                        <div class="flex items-center gap-1">
                          <span class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.width')
                          }}</span>
                          <ElInput
                            v-model="element.width"
                            size="small"
                            class="!w-16"
                            placeholder="auto"
                            clearable
                          />
                        </div>

                        <!-- 最小宽度 -->
                        <div class="flex items-center gap-1">
                          <span class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.min')
                          }}</span>
                          <ElInput
                            v-model="element.minWidth"
                            size="small"
                            class="!w-16"
                            placeholder="--"
                            clearable
                          />
                        </div>

                        <!-- 对齐 -->
                        <ElRadioGroup v-model="element.align" size="small">
                          <ElRadio label="left">
                            {{ $t('form-manager.listDesign.left') }}
                          </ElRadio>
                          <ElRadio label="center">
                            {{ $t('form-manager.listDesign.center') }}
                          </ElRadio>
                          <ElRadio label="right">
                            {{ $t('form-manager.listDesign.right') }}
                          </ElRadio>
                        </ElRadioGroup>

                        <!-- 冻结 -->
                        <ElSelect
                          v-model="element.fixed"
                          size="small"
                          class="!w-20"
                          clearable
                        >
                          <ElOption
                            :label="$t('form-manager.listDesign.noFixed')"
                            :value="false"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.fixedLeft')"
                            value="left"
                          />
                          <ElOption
                            :label="$t('form-manager.listDesign.fixedRight')"
                            value="right"
                          />
                        </ElSelect>

                        <!-- 删除 -->
                        <ElButton
                          link
                          type="danger"
                          :icon="Trash2"
                          @click="removeListColumn(index)"
                        />
                      </div>

                      <!-- 第二行：更多配置 -->
                      <div
                        class="flex flex-wrap items-center gap-x-4 gap-y-2 p-3"
                      >
                        <!-- 开关选项 -->
                        <div class="flex items-center gap-1">
                          <ElSwitch v-model="element.resizable" size="small" />
                          <span class="text-xs">{{
                            $t('form-manager.listDesign.resizable')
                          }}</span>
                        </div>
                        <div class="flex items-center gap-1">
                          <ElSwitch
                            v-model="element.showOverflowTooltip"
                            size="small"
                          />
                          <span class="text-xs">{{
                            $t('form-manager.listDesign.overflowTooltip')
                          }}</span>
                        </div>
                        <div class="flex items-center gap-1">
                          <ElSwitch v-model="element.ellipsis" size="small" />
                          <span class="text-xs">{{
                            $t('form-manager.listDesign.ellipsis')
                          }}</span>
                        </div>
                        <div
                          v-if="isOptionComponent(element.originalComponent)"
                          class="flex items-center gap-1"
                        >
                          <ElSwitch v-model="element.showAsTag" size="small" />
                          <span class="text-xs">{{
                            $t('form-manager.listDesign.showAsTag')
                          }}</span>
                        </div>

                        <!-- Tag 类型配置（仅在启用 Tag 显示时显示） -->
                        <template
                          v-if="element.showAsTag && element.options?.length"
                        >
                          <div class="bg-border mx-2 h-4 w-px"></div>
                          <div class="flex flex-wrap items-center gap-2">
                            <span class="text-muted-foreground text-xs">{{
                              $t('form-manager.listDesign.tagType')
                            }}</span>
                            <div
                              v-for="(opt, optIdx) in element.options"
                              :key="optIdx"
                              class="flex items-center gap-1"
                            >
                              <ElTag
                                :type="element.options[optIdx].tagType || ''"
                                size="small"
                                class="cursor-default"
                              >
                                {{ opt.label }}
                              </ElTag>
                              <ElSelect
                                v-model="element.options[optIdx].tagType"
                                size="small"
                                class="!w-20"
                                :placeholder="
                                  $t('form-manager.listDesign.tagDefault')
                                "
                                clearable
                              >
                                <ElOption
                                  :label="
                                    $t('form-manager.listDesign.tagDefault')
                                  "
                                  value=""
                                />
                                <ElOption
                                  :label="
                                    $t('form-manager.listDesign.tagSuccess')
                                  "
                                  value="success"
                                />
                                <ElOption
                                  :label="
                                    $t('form-manager.listDesign.tagWarning')
                                  "
                                  value="warning"
                                />
                                <ElOption
                                  :label="$t('form-manager.listDesign.tagInfo')"
                                  value="info"
                                />
                                <ElOption
                                  :label="
                                    $t('form-manager.listDesign.tagDanger')
                                  "
                                  value="danger"
                                />
                              </ElSelect>
                            </div>
                          </div>
                        </template>

                        <div class="bg-border mx-2 h-4 w-px"></div>

                        <!-- 关联字段显示名称开关 -->
                        <div
                          v-if="element.isRelation"
                          class="flex items-center gap-1"
                        >
                          <ElSwitch
                            v-model="element.showDisplayName"
                            size="small"
                          />
                          <span class="text-xs">{{
                            $t('form-manager.listDesign.showDisplayName')
                          }}</span>
                        </div>

                        <!-- 表单数据选择器显示关联字段 -->
                        <div
                          v-if="element.isFormDataSelector"
                          class="flex items-center gap-2"
                        >
                          <div class="flex items-center gap-1">
                            <ElSwitch
                              v-model="element.showDisplayName"
                              size="small"
                              @change="
                                (val: boolean) => {
                                  if (val && element.formCode)
                                    loadFormDataDisplayFieldOptions(element);
                                }
                              "
                            />
                            <span class="text-xs">{{
                              $t('form-manager.listDesign.showRelationField')
                            }}</span>
                          </div>
                          <ElSelect
                            v-if="element.showDisplayName"
                            v-model="element.displayFieldName"
                            size="small"
                            class="!w-32"
                            :placeholder="
                              $t(
                                'form-manager.listDesign.selectDisplayFieldPlaceholder',
                              )
                            "
                            :loading="element.displayFieldOptionsLoading"
                            @focus="loadFormDataDisplayFieldOptions(element)"
                          >
                            <ElOption
                              v-for="opt in element.displayFieldOptions"
                              :key="opt.value"
                              :label="opt.label"
                              :value="opt.value"
                            />
                          </ElSelect>
                        </div>

                        <!-- 用户选择器显示头像开关 -->
                        <div
                          v-if="element.isUserSelector"
                          class="flex items-center gap-1"
                        >
                          <ElSwitch
                            v-model="element.showAsAvatar"
                            size="small"
                          />
                          <span class="text-xs">{{
                            $t('form-manager.listDesign.showAvatar')
                          }}</span>
                        </div>

                        <!-- 虚拟字段显示关联值开关 -->
                        <div
                          v-if="element.isVirtualField"
                          class="flex items-center gap-1"
                        >
                          <ElSwitch
                            v-model="element.showVirtualValue"
                            size="small"
                          />
                          <span class="text-xs">{{
                            $t('form-manager.listDesign.showVirtualValue')
                          }}</span>
                        </div>

                        <div class="bg-border mx-2 h-4 w-px"></div>

                        <!-- 格式化 -->
                        <div class="flex items-center gap-1">
                          <span class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.formatter')
                          }}</span>
                          <ElSelect
                            v-model="element.formatter"
                            size="small"
                            class="!w-24"
                            clearable
                          >
                            <ElOption
                              :label="$t('form-manager.listDesign.none')"
                              value="none"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.formatDate')"
                              value="date"
                            />
                            <ElOption
                              :label="
                                $t('form-manager.listDesign.formatDateTime')
                              "
                              value="datetime"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.formatMoney')"
                              value="money"
                            />
                            <ElOption
                              :label="
                                $t('form-manager.listDesign.formatPercent')
                              "
                              value="percent"
                            />
                            <ElOption
                              :label="
                                $t('form-manager.listDesign.formatNumber')
                              "
                              value="number"
                            />
                          </ElSelect>
                        </div>

                        <!-- 格式模式（日期时显示） -->
                        <div
                          v-if="
                            element.formatter === 'date' ||
                            element.formatter === 'datetime'
                          "
                          class="flex items-center gap-1"
                        >
                          <span class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.formatPattern')
                          }}</span>
                          <ElInput
                            v-model="element.formatPattern"
                            size="small"
                            class="!w-28"
                            placeholder="YYYY-MM-DD"
                            clearable
                          />
                        </div>

                        <!-- 前缀 -->
                        <div class="flex items-center gap-1">
                          <span class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.prefix')
                          }}</span>
                          <ElSelect
                            v-model="element.prefix"
                            size="small"
                            class="!w-16"
                            :placeholder="$t('form-manager.listDesign.custom')"
                            clearable
                            filterable
                            allow-create
                            default-first-option
                          >
                            <ElOption label="￥" value="￥" />
                            <ElOption label="$" value="$" />
                            <ElOption label="€" value="€" />
                          </ElSelect>
                        </div>

                        <!-- 后缀 -->
                        <div class="flex items-center gap-1">
                          <span class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.suffix')
                          }}</span>
                          <ElSelect
                            v-model="element.suffix"
                            size="small"
                            class="!w-16"
                            :placeholder="$t('form-manager.listDesign.custom')"
                            clearable
                            filterable
                            allow-create
                            default-first-option
                          >
                            <ElOption label="%" value="%" />
                            <ElOption
                              :label="$t('form-manager.listDesign.unitYuan')"
                              value="元"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.unitGe')"
                              value="个"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.unitCi')"
                              value="次"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.unitDay')"
                              value="天"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.unitHour')"
                              value="小时"
                            />
                          </ElSelect>
                        </div>

                        <!-- 分隔线 -->
                        <div
                          v-if="
                            !isNoSortFilterComponent(element.originalComponent)
                          "
                          class="bg-border mx-2 h-4 w-px"
                        ></div>

                        <!-- 排序配置（文件、图片等组件不显示） -->
                        <template
                          v-if="
                            !isNoSortFilterComponent(element.originalComponent)
                          "
                        >
                          <div class="flex items-center gap-1">
                            <ElSwitch v-model="element.sortable" size="small" />
                            <span class="text-xs">{{
                              $t('form-manager.listDesign.sortable')
                            }}</span>
                          </div>
                          <template v-if="element.sortable">
                            <ElSelect
                              v-model="element.sortType"
                              size="small"
                              class="!w-20"
                            >
                              <ElOption
                                :label="
                                  $t('form-manager.listDesign.sortFrontend')
                                "
                                value="frontend"
                              />
                              <ElOption
                                :label="
                                  $t('form-manager.listDesign.sortBackend')
                                "
                                value="backend"
                              />
                            </ElSelect>
                          </template>

                          <!-- 过滤配置 -->
                          <div class="flex items-center gap-1">
                            <ElSwitch
                              v-model="element.filterable"
                              size="small"
                            />
                            <span class="text-xs">{{
                              $t('form-manager.listDesign.filterable')
                            }}</span>
                          </div>
                          <!-- 弹窗过滤类型提示 -->
                          <span
                            v-if="
                              element.filterable &&
                              isDialogFilterComponent(element.originalComponent)
                            "
                            class="text-muted-foreground text-xs"
                          >
                            ({{ $t('form-manager.listDesign.dialogFilter') }})
                          </span>
                          <!-- 日期过滤配置：查询类型和显示时间 -->
                          <template
                            v-if="
                              element.filterable &&
                              isDateComponent(element.originalComponent)
                            "
                          >
                            <ElSelect
                              v-model="element.filterQueryType"
                              size="small"
                              class="!w-20"
                            >
                              <ElOption
                                :label="$t('form-manager.listDesign.matchEq')"
                                value="eq"
                              />
                              <ElOption
                                :label="
                                  $t('form-manager.listDesign.matchRange')
                                "
                                value="range"
                              />
                            </ElSelect>
                            <div class="flex items-center gap-1">
                              <ElSwitch
                                v-model="element.filterShowTime"
                                size="small"
                                :disabled="
                                  !element.dbType
                                    ?.toLowerCase()
                                    .includes('timestamp')
                                "
                              />
                              <span class="text-xs">{{
                                $t('form-manager.listDesign.showTime')
                              }}</span>
                            </div>
                          </template>
                        </template>

                        <!-- 表尾统计配置（仅数值类型字段显示） -->
                        <template
                          v-if="
                            listSettings.table.showSummary && element.isNumeric
                          "
                        >
                          <div class="bg-border mx-2 h-4 w-px"></div>
                          <div class="flex items-center gap-1">
                            <ElSwitch
                              v-model="element.summaryEnabled"
                              size="small"
                            />
                            <span class="text-xs">{{
                              $t('form-manager.listDesign.enableSummary')
                            }}</span>
                          </div>
                        </template>
                      </div>
                    </div>
                  </template>
                </draggable>
              </div>

              <div
                v-else
                class="text-muted-foreground flex min-h-[270px] flex-col items-center justify-center py-8"
              >
                <div class="bg-muted mb-2 rounded-full p-4">
                  <TableProperties class="h-8 w-8 opacity-50" />
                </div>
                <span class="text-sm">{{
                  $t('form-manager.listDesign.noListFields')
                }}</span>
                <span class="text-xs opacity-70">{{
                  $t('form-manager.listDesign.selectListTip')
                }}</span>
              </div>
            </div>
          </div>

          <!-- 卡片字段配置（仅 Card 模式） -->
          <div
            v-if="listSettings.listType === 'card'"
            class="border-border bg-card min-h-[350px] rounded-lg border shadow-sm"
          >
            <div class="border-border border-b px-4 py-3">
              <h3 class="font-medium">
                {{ $t('form-manager.listDesign.cardFieldsConfig') }}
              </h3>
            </div>
            <div class="p-4">
              <div class="flex gap-6">
                <!-- 左侧：卡片预览 -->
                <div class="w-[420px] flex-shrink-0">
                  <div class="text-muted-foreground mb-2 text-xs">
                    {{ $t('form-manager.listDesign.cardPreview') }}
                  </div>
                  <div
                    class="border-border bg-background rounded-lg border p-5 shadow-sm"
                  >
                    <!-- 卡片头部 -->
                    <div class="mb-3 flex items-start gap-3">
                      <!-- 图标区域 -->
                      <div
                        class="card-drop-area group relative flex h-12 w-12 flex-shrink-0 cursor-pointer items-center justify-center rounded-lg border-2 border-dashed transition-colors"
                        :class="[
                          listSettings.cardFields.icon
                            ? 'border-primary bg-primary/10'
                            : 'border-border hover:border-primary',
                          selectedCardArea === 'icon' ? 'selected' : '',
                          dragOverArea === 'icon' ? 'drag-over' : '',
                        ]"
                        @click="selectCardArea('icon')"
                        @drop="handleDrop($event, 'icon')"
                        @dragover.prevent
                        @dragenter="handleDragEnter('icon')"
                        @dragleave="handleDragLeave"
                      >
                        <span
                          v-if="listSettings.cardFields.icon"
                          class="text-primary truncate px-1 text-xs font-medium"
                        >
                          {{ listSettings.cardFields.icon.label }}
                        </span>
                        <span v-else class="text-muted-foreground text-xs">{{
                          $t('form-manager.listDesign.cardAreaIcon')
                        }}</span>
                        <!-- 移除按钮 -->
                        <ElButton
                          v-if="listSettings.cardFields.icon"
                          link
                          type="danger"
                          size="small"
                          class="!absolute -right-1 -top-1 !h-4 !w-4 !min-w-0 !rounded-full !p-0 opacity-0 group-hover:opacity-100"
                          @click.stop="clearCardArea('icon')"
                        >
                          <Trash2 class="h-3 w-3" />
                        </ElButton>
                      </div>
                      <!-- 标题和副标题 -->
                      <div class="min-w-0 flex-1">
                        <div
                          class="card-drop-area group relative mb-1 cursor-pointer rounded border-2 border-dashed px-2 py-1 transition-colors"
                          :class="[
                            listSettings.cardFields.title
                              ? 'border-primary bg-primary/10'
                              : 'border-border hover:border-primary',
                            selectedCardArea === 'title' ? 'selected' : '',
                            dragOverArea === 'title' ? 'drag-over' : '',
                          ]"
                          @click="selectCardArea('title')"
                          @drop="handleDrop($event, 'title')"
                          @dragover.prevent
                          @dragenter="handleDragEnter('title')"
                          @dragleave="handleDragLeave"
                        >
                          <span
                            v-if="listSettings.cardFields.title"
                            class="text-primary text-sm font-medium"
                          >
                            {{ listSettings.cardFields.title.label }}
                          </span>
                          <span v-else class="text-muted-foreground text-xs">
                            {{ $t('form-manager.listDesign.cardAreaTitle') }}
                            <span class="text-danger">*</span>
                          </span>
                          <ElButton
                            v-if="listSettings.cardFields.title"
                            link
                            type="danger"
                            size="small"
                            class="!absolute -right-1 -top-1 !h-4 !w-4 !min-w-0 !rounded-full !p-0 opacity-0 group-hover:opacity-100"
                            @click.stop="clearCardArea('title')"
                          >
                            <Trash2 class="h-3 w-3" />
                          </ElButton>
                        </div>
                        <div
                          class="card-drop-area group relative cursor-pointer rounded border-2 border-dashed px-2 py-1 transition-colors"
                          :class="[
                            listSettings.cardFields.subtitle
                              ? 'border-primary bg-primary/10'
                              : 'border-border hover:border-primary',
                            selectedCardArea === 'subtitle' ? 'selected' : '',
                            dragOverArea === 'subtitle' ? 'drag-over' : '',
                          ]"
                          @click="selectCardArea('subtitle')"
                          @drop="handleDrop($event, 'subtitle')"
                          @dragover.prevent
                          @dragenter="handleDragEnter('subtitle')"
                          @dragleave="handleDragLeave"
                        >
                          <span
                            v-if="listSettings.cardFields.subtitle"
                            class="text-primary text-xs"
                          >
                            {{ listSettings.cardFields.subtitle.label }}
                          </span>
                          <span v-else class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.cardAreaSubtitle')
                          }}</span>
                          <ElButton
                            v-if="listSettings.cardFields.subtitle"
                            link
                            type="danger"
                            size="small"
                            class="!absolute -right-1 -top-1 !h-4 !w-4 !min-w-0 !rounded-full !p-0 opacity-0 group-hover:opacity-100"
                            @click.stop="clearCardArea('subtitle')"
                          >
                            <Trash2 class="h-3 w-3" />
                          </ElButton>
                        </div>
                      </div>
                    </div>

                    <!-- 描述区域 -->
                    <div
                      class="card-drop-area group relative mb-3 cursor-pointer rounded border-2 border-dashed px-2 py-2 transition-colors"
                      :class="[
                        listSettings.cardFields.description
                          ? 'border-primary bg-primary/10'
                          : 'border-border hover:border-primary',
                        selectedCardArea === 'description' ? 'selected' : '',
                        dragOverArea === 'description' ? 'drag-over' : '',
                      ]"
                      @click="selectCardArea('description')"
                      @drop="handleDrop($event, 'description')"
                      @dragover.prevent
                      @dragenter="handleDragEnter('description')"
                      @dragleave="handleDragLeave"
                    >
                      <span
                        v-if="listSettings.cardFields.description"
                        class="text-primary text-sm"
                      >
                        {{ listSettings.cardFields.description.label }}
                      </span>
                      <span v-else class="text-muted-foreground text-xs">{{
                        $t('form-manager.listDesign.cardAreaDescription')
                      }}</span>
                      <ElButton
                        v-if="listSettings.cardFields.description"
                        link
                        type="danger"
                        size="small"
                        class="!absolute -right-1 -top-1 !h-4 !w-4 !min-w-0 !rounded-full !p-0 opacity-0 group-hover:opacity-100"
                        @click.stop="clearCardArea('description')"
                      >
                        <Trash2 class="h-3 w-3" />
                      </ElButton>
                    </div>

                    <!-- 标签区域 -->
                    <div
                      class="card-drop-area mb-3 cursor-pointer rounded border-2 border-dashed px-2 py-2 transition-colors"
                      :class="[
                        listSettings.cardFields.tags.length > 0
                          ? 'border-primary bg-primary/10'
                          : 'border-border hover:border-primary',
                        selectedCardArea === 'tags' ? 'selected' : '',
                        dragOverArea === 'tags' ? 'drag-over' : '',
                      ]"
                      @click="selectCardArea('tags')"
                      @drop="handleDrop($event, 'tags')"
                      @dragover.prevent
                      @dragenter="handleDragEnter('tags')"
                      @dragleave="handleDragLeave"
                    >
                      <div
                        v-if="listSettings.cardFields.tags.length > 0"
                        class="flex flex-wrap gap-1"
                      >
                        <ElTag
                          v-for="(tag, idx) in listSettings.cardFields.tags"
                          :key="idx"
                          size="small"
                          closable
                          @close="removeCardTag(idx)"
                        >
                          {{ tag.label }}
                        </ElTag>
                      </div>
                      <span v-else class="text-muted-foreground text-xs">
                        {{ $t('form-manager.listDesign.cardAreaTags') }} ({{
                          $t('form-manager.listDesign.cardAreaMaxTags', {
                            count: 3,
                          })
                        }})
                      </span>
                    </div>

                    <!-- 底部区域 -->
                    <div class="flex items-center justify-between">
                      <div
                        class="card-drop-area group relative mr-2 flex-1 cursor-pointer rounded border-2 border-dashed px-2 py-1 transition-colors"
                        :class="[
                          listSettings.cardFields.footerLeft
                            ? 'border-primary bg-primary/10'
                            : 'border-border hover:border-primary',
                          selectedCardArea === 'footerLeft' ? 'selected' : '',
                          dragOverArea === 'footerLeft' ? 'drag-over' : '',
                        ]"
                        @click="selectCardArea('footerLeft')"
                        @drop="handleDrop($event, 'footerLeft')"
                        @dragover.prevent
                        @dragenter="handleDragEnter('footerLeft')"
                        @dragleave="handleDragLeave"
                      >
                        <span
                          v-if="listSettings.cardFields.footerLeft"
                          class="text-primary text-xs"
                        >
                          {{ listSettings.cardFields.footerLeft.label }}
                        </span>
                        <span v-else class="text-muted-foreground text-xs">{{
                          $t('form-manager.listDesign.cardAreaFooterLeft')
                        }}</span>
                        <ElButton
                          v-if="listSettings.cardFields.footerLeft"
                          link
                          type="danger"
                          size="small"
                          class="!absolute -right-1 -top-1 !h-4 !w-4 !min-w-0 !rounded-full !p-0 opacity-0 group-hover:opacity-100"
                          @click.stop="clearCardArea('footerLeft')"
                        >
                          <Trash2 class="h-3 w-3" />
                        </ElButton>
                      </div>
                      <div
                        class="card-drop-area group relative flex-1 cursor-pointer rounded border-2 border-dashed px-2 py-1 text-right transition-colors"
                        :class="[
                          listSettings.cardFields.footerRight
                            ? 'border-primary bg-primary/10'
                            : 'border-border hover:border-primary',
                          selectedCardArea === 'footerRight' ? 'selected' : '',
                          dragOverArea === 'footerRight' ? 'drag-over' : '',
                        ]"
                        @click="selectCardArea('footerRight')"
                        @drop="handleDrop($event, 'footerRight')"
                        @dragover.prevent
                        @dragenter="handleDragEnter('footerRight')"
                        @dragleave="handleDragLeave"
                      >
                        <span
                          v-if="listSettings.cardFields.footerRight"
                          class="text-primary text-xs"
                        >
                          {{ listSettings.cardFields.footerRight.label }}
                        </span>
                        <span v-else class="text-muted-foreground text-xs">{{
                          $t('form-manager.listDesign.cardAreaFooterRight')
                        }}</span>
                        <ElButton
                          v-if="listSettings.cardFields.footerRight"
                          link
                          type="danger"
                          size="small"
                          class="!absolute -right-1 -top-1 !h-4 !w-4 !min-w-0 !rounded-full !p-0 opacity-0 group-hover:opacity-100"
                          @click.stop="clearCardArea('footerRight')"
                        >
                          <Trash2 class="h-3 w-3" />
                        </ElButton>
                      </div>
                    </div>
                  </div>
                  <div class="text-muted-foreground mt-2 text-xs">
                    {{ $t('form-manager.listDesign.cardFieldsTip') }}
                  </div>
                </div>

                <!-- 右侧：字段属性配置 + 可用字段列表 -->
                <div class="flex flex-1 flex-col gap-4">
                  <!-- 字段属性配置（当选中区域有字段时显示） -->
                  <div v-if="selectedCardField">
                    <div
                      class="text-muted-foreground mb-2 flex items-center justify-between text-xs"
                    >
                      <span>{{
                        $t('form-manager.listDesign.fieldProperties')
                      }}</span>
                      <span class="text-primary">{{ selectedCardField.label }} ({{
                          selectedCardField.field
                        }})</span>
                    </div>
                    <div
                      class="border-border bg-background rounded-lg border p-3"
                    >
                      <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
                        <!-- 关联字段显示名称 -->
                        <div
                          v-if="selectedCardField.isRelation"
                          class="flex items-center gap-1"
                        >
                          <ElSwitch
                            v-model="selectedCardField.showDisplayName"
                            size="small"
                          />
                          <span class="text-xs">{{
                            $t('form-manager.listDesign.showDisplayName')
                          }}</span>
                        </div>

                        <!-- 表单数据选择器显示关联字段 -->
                        <div
                          v-if="selectedCardField.isFormDataSelector"
                          class="flex items-center gap-2"
                        >
                          <div class="flex items-center gap-1">
                            <ElSwitch
                              v-model="selectedCardField.showDisplayName"
                              size="small"
                              @change="
                                (val: boolean) => {
                                  if (val && selectedCardField.formCode)
                                    loadFormDataDisplayFieldOptions(
                                      selectedCardField,
                                    );
                                }
                              "
                            />
                            <span class="text-xs">{{
                              $t('form-manager.listDesign.showRelationField')
                            }}</span>
                          </div>
                          <ElSelect
                            v-if="selectedCardField.showDisplayName"
                            v-model="selectedCardField.displayFieldName"
                            size="small"
                            class="!w-32"
                            :placeholder="
                              $t(
                                'form-manager.listDesign.selectDisplayFieldPlaceholder',
                              )
                            "
                            :loading="
                              selectedCardField.displayFieldOptionsLoading
                            "
                            @focus="
                              loadFormDataDisplayFieldOptions(selectedCardField)
                            "
                          >
                            <ElOption
                              v-for="opt in selectedCardField.displayFieldOptions"
                              :key="opt.value"
                              :label="opt.label"
                              :value="opt.value"
                            />
                          </ElSelect>
                        </div>

                        <!-- 用户选择器显示头像 -->
                        <div
                          v-if="selectedCardField.isUserSelector"
                          class="flex items-center gap-1"
                        >
                          <ElSwitch
                            v-model="selectedCardField.showAsAvatar"
                            size="small"
                          />
                          <span class="text-xs">{{
                            $t('form-manager.listDesign.showAvatar')
                          }}</span>
                        </div>

                        <!-- 选项字段显示为 Tag -->
                        <div
                          v-if="isOptionComponent(selectedCardField.component)"
                          class="flex items-center gap-1"
                        >
                          <ElSwitch
                            v-model="selectedCardField.showAsTag"
                            size="small"
                          />
                          <span class="text-xs">{{
                            $t('form-manager.listDesign.showAsTag')
                          }}</span>
                        </div>

                        <div class="bg-border mx-2 h-4 w-px"></div>

                        <!-- 格式化 -->
                        <div class="flex items-center gap-1">
                          <span class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.formatter')
                          }}</span>
                          <ElSelect
                            v-model="selectedCardField.formatter"
                            size="small"
                            class="!w-24"
                            clearable
                          >
                            <ElOption
                              :label="$t('form-manager.listDesign.none')"
                              value="none"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.formatDate')"
                              value="date"
                            />
                            <ElOption
                              :label="
                                $t('form-manager.listDesign.formatDateTime')
                              "
                              value="datetime"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.formatMoney')"
                              value="money"
                            />
                            <ElOption
                              :label="
                                $t('form-manager.listDesign.formatPercent')
                              "
                              value="percent"
                            />
                            <ElOption
                              :label="
                                $t('form-manager.listDesign.formatNumber')
                              "
                              value="number"
                            />
                          </ElSelect>
                        </div>

                        <!-- 前缀 -->
                        <div class="flex items-center gap-1">
                          <span class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.prefix')
                          }}</span>
                          <ElSelect
                            v-model="selectedCardField.prefix"
                            size="small"
                            class="!w-16"
                            :placeholder="$t('form-manager.listDesign.custom')"
                            clearable
                            filterable
                            allow-create
                            default-first-option
                          >
                            <ElOption label="￥" value="￥" />
                            <ElOption label="$" value="$" />
                            <ElOption label="€" value="€" />
                          </ElSelect>
                        </div>

                        <!-- 后缀 -->
                        <div class="flex items-center gap-1">
                          <span class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.suffix')
                          }}</span>
                          <ElSelect
                            v-model="selectedCardField.suffix"
                            size="small"
                            class="!w-16"
                            :placeholder="$t('form-manager.listDesign.custom')"
                            clearable
                            filterable
                            allow-create
                            default-first-option
                          >
                            <ElOption label="%" value="%" />
                            <ElOption
                              :label="$t('form-manager.listDesign.unitYuan')"
                              value="元"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.unitGe')"
                              value="个"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.unitCi')"
                              value="次"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.unitDay')"
                              value="天"
                            />
                            <ElOption
                              :label="$t('form-manager.listDesign.unitHour')"
                              value="小时"
                            />
                          </ElSelect>
                        </div>
                      </div>

                      <!-- Tag 类型配置 -->
                      <div
                        v-if="
                          selectedCardField.showAsTag &&
                          selectedCardField.options?.length
                        "
                        class="border-border mt-3 border-t pt-3"
                      >
                        <div class="flex flex-wrap items-center gap-2">
                          <span class="text-muted-foreground text-xs">{{
                            $t('form-manager.listDesign.tagType')
                          }}</span>
                          <div
                            v-for="(opt, optIdx) in selectedCardField.options"
                            :key="optIdx"
                            class="flex items-center gap-1"
                          >
                            <ElTag
                              :type="
                                selectedCardField.options[optIdx].tagType || ''
                              "
                              size="small"
                            >
                              {{ opt.label }}
                            </ElTag>
                            <ElSelect
                              v-model="
                                selectedCardField.options[optIdx].tagType
                              "
                              size="small"
                              class="!w-20"
                              clearable
                            >
                              <ElOption
                                :label="
                                  $t('form-manager.listDesign.tagDefault')
                                "
                                value=""
                              />
                              <ElOption
                                :label="
                                  $t('form-manager.listDesign.tagSuccess')
                                "
                                value="success"
                              />
                              <ElOption
                                :label="
                                  $t('form-manager.listDesign.tagWarning')
                                "
                                value="warning"
                              />
                              <ElOption
                                :label="$t('form-manager.listDesign.tagInfo')"
                                value="info"
                              />
                              <ElOption
                                :label="$t('form-manager.listDesign.tagDanger')"
                                value="danger"
                              />
                            </ElSelect>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 可用字段列表 -->
                  <div class="min-h-0 flex-1">
                    <div class="text-muted-foreground mb-2 text-xs">
                      {{ $t('form-manager.listDesign.listTab') }}
                    </div>
                    <div
                      class="border-border rounded border"
                      :class="selectedCardField ? 'h-[220px]' : 'h-[400px]'"
                    >
                      <ElScrollbar class="h-full">
                        <div class="p-2">
                          <div
                            v-for="field in cardAvailableFields"
                            :key="field.field"
                            draggable="true"
                            class="border-border bg-background hover:border-primary mb-2 flex cursor-move items-center justify-between rounded border p-2 transition-colors"
                            @dragstart="handleDragStart($event, field)"
                            @dragend="handleDragEnd"
                          >
                            <div class="flex flex-col">
                              <span
                                class="text-foreground text-sm font-medium"
                                >{{ field.label }}</span>
                              <span class="text-muted-foreground text-xs">{{
                                field.field
                              }}</span>
                            </div>
                            <GripVertical
                              class="text-muted-foreground h-4 w-4"
                            />
                          </div>
                          <div
                            v-if="cardAvailableFields.length === 0"
                            class="text-muted-foreground py-4 text-center text-xs"
                          >
                            {{
                              $t('form-manager.listDesign.noAvailableFields')
                            }}
                          </div>
                        </div>
                      </ElScrollbar>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ElScrollbar>
    </div>
  </div>
</template>

<style scoped>
:deep(.el-tabs__content) {
  height: calc(100% - 40px);
  overflow: hidden;
}

:deep(.el-tabs__header) {
  margin-bottom: 0;
}

:deep(.el-tabs__nav-scroll) {
  display: flex;
  justify-content: center;
}

:deep(.el-tabs__nav) {
  float: none;
}

/* 列表类型切换样式 */
.list-type-radio {
  display: flex;
  gap: 8px;
}

.list-type-radio :deep(.el-radio) {
  flex: 1;
  margin-right: 0;
  padding: 16px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  min-height: 30px;
  transition: all 0.2s;
}

.list-type-radio :deep(.el-radio.is-checked) {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.list-type-radio :deep(.el-radio__input) {
  display: none;
}

.list-type-radio :deep(.el-radio__label) {
  padding-left: 0;
}

/* 卡片区域选中状态 */
.card-drop-area.selected {
  border-color: var(--el-color-primary) !important;
  background-color: var(--el-color-primary-light-9) !important;
}

/* 拖拽悬停高亮状态 */
.card-drop-area.drag-over {
  border-color: var(--el-color-success) !important;
  background-color: var(--el-color-success-light-9) !important;
  box-shadow: 0 0 0 2px var(--el-color-success-light-7) !important;
  transform: scale(1.02);
}

/* 拖拽时的样式 */
.card-drop-area {
  position: relative;
}

.card-drop-area:hover::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
}

/* 字段列表拖拽样式 */
[draggable='true'] {
  user-select: none;
}

[draggable='true']:active {
  opacity: 0.5;
  cursor: grabbing !important;
}
</style>
