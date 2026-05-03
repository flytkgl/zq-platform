<script lang="ts" setup>
import type {
  FieldPermissions,
  FormPermissions,
} from '#/api/online-dev/form-data-api';
import type { FormMeta } from '#/api/online-dev/form-manager';

import { computed, h, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import {
  ArrowLeft,
  Download,
  Edit,
  Eye,
  IconifyIcon,
  Link,
  MoreVertical,
  Plus,
  Save,
  Trash2,
  Upload,
} from '@vben/icons';
import { $t } from '@vben/locales';

import dayjs from 'dayjs';
import {
  ElAvatar,
  ElBadge,
  ElButton,
  ElCard,
  ElCheckbox,
  ElDatePicker,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElImage,
  ElImageViewer,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElPagination,
  ElRadio,
  ElSelect,
  ElTag,
  ElTooltip,
} from 'element-plus';

import {
  batchDeleteFormDataApi,
  createFormDataApi,
  deleteFormDataApi,
  downloadBlob,
  getFieldPermissionsApi,
  getFieldValuesApi,
  getFormDataDetailApi,
  getFormDataListApi,
  getFormPermissionsApi,
  getImportTemplateApi,
  getTreeChildrenApi,
  updateFormDataApi,
} from '#/api/online-dev/form-data-api';
import { getFormByCodeApi } from '#/api/online-dev/form-manager';
import { requestClient } from '#/api/request';
import PreviewItem from '#/components/form-design/components/PreviewItem.vue';
import UserAvatar from '#/components/user-avatar/index.vue';
import { ZqDialog } from '#/components/zq-dialog';
import { DeptSelector } from '#/components/zq-form/dept-selector';
import { FormSelector } from '#/components/zq-form/form-selector';
import { PostSelector } from '#/components/zq-form/post-selector';
import { TableSelector } from '#/components/zq-form/table-selector';
import { UserSelector } from '#/components/zq-form/user-selector';
import { useZqTable } from '#/components/zq-table';
import { getFileUrl } from '#/composables/useFileUrl';
import { useFormData } from '#/views/online-dev/form-manager/composables/useFormData';

import ExportConfigDialog from './ExportConfigDialog.vue';
import ExportProgressDialog from './ExportProgressDialog.vue';
import FileListCell from './FileListCell.vue';
import FormDataDialog from './FormDataDialog.vue';
import ImportDialog from './ImportDialog.vue';
import PageViewDialog from './PageViewDialog.vue';
import SubTableFormContainer from './SubTableFormContainer.vue';

const props = withDefaults(
  defineProps<{
    // 新增时的默认数据（用于子表单自动填充外键）
    defaultFormData?: Record<string, any>;
    formCode: string;
    //
    heightOffset?: number;
    // 初始过滤条件（用于子表单过滤）
    initialFilters?: Record<string, any>;
    // 自定义操作处理（用于 page 模式跳转）
    onAdd?: () => void;
    onEdit?: (row: any) => void;
    onView?: (row: any) => void;
    // 选择模式下已选中的值（用于高亮显示）
    selectedValues?: Set<string>;
    // 选择模式：用于表单选择器组件
    selectionMode?: boolean;
    // 选择模式下是否多选
    selectionMultiple?: boolean;
    // 选择模式下的值字段
    selectionValueField?: string;
    // 外边距
    showMargin?: boolean;
    // 是否显示工具栏
    showToolbar?: boolean;
    // 是否使用导出配置对话框
    useExportConfig?: boolean;
  }>(),
  {
    showToolbar: true,
    useExportConfig: false,
    showMargin: true,
    selectionMode: false,
    selectionMultiple: false,
    selectionValueField: 'id',
  } as const,
);

const emit = defineEmits<{
  (e: 'loaded', formMeta: FormMeta): void;
  (e: 'row-select', row: any): void;
  (e: 'select-all', rows: any[]): void;
}>();

// 表单元数据
const formMeta = ref<FormMeta | null>(null);
const loading = ref(false);

// 查询字段动态选项（字典 / 表单数据源）：key 为 field name
const queryFieldDynamicOptions = ref<Record<string, any[]>>({});

// 列表配置
const listConfig = computed(() => {
  const config = formMeta.value?.list_config || {};
  return {
    listType: config.listType || 'table',
    containerType: config.containerType || 'drawer',
    card: {
      columns: config.card?.columns ?? 4,
      gap: config.card?.gap ?? 16,
      shadow: config.card?.shadow || 'hover',
      pageSize: config.card?.pageSize ?? 12,
      showPagination: config.card?.showPagination ?? true,
    },
    cardFields: config.cardFields || {
      icon: null,
      title: null,
      subtitle: null,
      description: null,
      tags: [],
      footerLeft: null,
      footerRight: null,
    },
    table: {
      showPagination: config.table?.showPagination ?? true,
      pageSize: config.table?.pageSize || 20,
      showIndex: config.table?.showIndex ?? true,
      showSelection: config.table?.showSelection ?? true,
      stripe: config.table?.stripe ?? true,
      border: config.table?.border ?? true,
      size: config.table?.size || 'default',
      height: config.table?.height || 'auto',
      defaultSort: Array.isArray(config.table?.defaultSort)
        ? config.table.defaultSort
        : config.table?.defaultSort?.field
          ? [
              {
                field: config.table.defaultSort.field,
                order: config.table.defaultSort.order || 'desc',
              },
            ]
          : [],
      defaultFilters: Array.isArray(config.table?.defaultFilters)
        ? config.table.defaultFilters
        : [],
      showSummary: config.table?.showSummary ?? false,
      summaryType: config.table?.summaryType || 'sum',
      summaryPrecision: config.table?.summaryPrecision ?? 2,
    },
    dialog: {
      width: config.dialog?.width || '800px',
      fullscreen: config.dialog?.fullscreen ?? false,
      draggable: config.dialog?.draggable ?? true,
      closeOnClickModal: config.dialog?.closeOnClickModal ?? false,
      closeOnPressEscape: config.dialog?.closeOnPressEscape ?? true,
    },
    drawer: {
      size: config.drawer?.size || '800px',
      direction: config.drawer?.direction || 'rtl',
      withHeader: config.drawer?.withHeader ?? true,
      closeOnClickModal: config.drawer?.closeOnClickModal ?? false,
      closeOnPressEscape: config.drawer?.closeOnPressEscape ?? true,
    },
    buttons: {
      showAdd: config.buttons?.showAdd ?? false,
      showEdit: config.buttons?.showEdit ?? false,
      showDelete: config.buttons?.showDelete ?? false,
      showView: config.buttons?.showView ?? false,
      showExport: config.buttons?.showExport ?? false,
      showImport: config.buttons?.showImport ?? false,
      showBatchDelete: config.buttons?.showBatchDelete ?? false,
    },
    // 新增/编辑时显示确认按钮
    showConfirmButton: config.showConfirmButton ?? true,
    // 保存后行为（兼容旧版 closeAfterSave）
    afterSaveAction:
      config.afterSaveAction ||
      (config.closeAfterSave === false ? 'editMode' : 'close'),
    // 新增时可发起流程（仅流程表单有效）
    enableStartWorkflowOnAdd: config.enableStartWorkflowOnAdd ?? false,
    // 子表操作按钮
    subTableButtons: config.subTableButtons || [],
    customButtons: config.customButtons || [],
    // 树形表格配置
    tree: {
      enabled: config.tree?.enabled ?? false,
      parentField: config.tree?.parentField || 'parent_id',
      lazy: config.tree?.lazy ?? false,
      defaultExpandAll: config.tree?.defaultExpandAll ?? false,
      indent: config.tree?.indent ?? 16,
      checkStrictly: config.tree?.checkStrictly ?? false,
    },
  };
});

const cardGridStyle = computed(() => ({
  display: 'grid',
  gridTemplateColumns: `repeat(${listConfig.value.card.columns}, minmax(0, 1fr))`,
  gap: `${listConfig.value.card.gap}px`,
}));

// 弹窗状态
const showFormDialog = ref(false);
const dialogMode = ref<'add' | 'edit' | 'view'>('add');
const editingId = ref<null | string>(null);

// 选中的行
const selectedRows = ref<any[]>([]);

// 当前排序状态（用于后端排序）
const currentSort = ref<{
  field: string;
  order: 'ascending' | 'descending' | null;
}>({
  field: '',
  order: null,
});

// 当前过滤状态（用于后端过滤）
const currentFilters = ref<Record<string, any[]>>({});

// 导出配置对话框
const showExportDialog = ref(false);

// 导出进度对话框
const showExportProgressDialog = ref(false);
const exportProgressConfig = ref<null | {
  includeSubTables: boolean;
  queryParams: Record<string, any>;
  selectedFields: string[];
}>(null);

// 用户权限
const userPermissions = ref<FormPermissions>({
  view: false,
  add: false,
  edit: false,
  delete: false,
  export: false,
  import: false,
});

// 字段权限
const fieldPermissions = ref<FieldPermissions>({});

// 计算最终按钮显示状态（表单配置 AND 用户权限）
const effectiveButtons = computed(() => ({
  showAdd: listConfig.value.buttons.showAdd && userPermissions.value.add,
  showEdit: listConfig.value.buttons.showEdit && userPermissions.value.edit,
  showDelete:
    listConfig.value.buttons.showDelete && userPermissions.value.delete,
  showView: listConfig.value.buttons.showView && userPermissions.value.view,
  showExport:
    listConfig.value.buttons.showExport && userPermissions.value.export,
  showImport:
    listConfig.value.buttons.showImport && userPermissions.value.import,
  showBatchDelete:
    listConfig.value.buttons.showBatchDelete && userPermissions.value.delete,
}));

// ============ 子表操作按钮相关 ============
const showSubTableContainer = ref(false);
const currentSubTableButton = ref<any>(null);
const currentMainRecordId = ref<string>('');

// ============ 生成单据弹窗相关 ============
const showGenerateDocumentDialog = ref(false);
const currentGenerateDocumentRow = ref<any>(null);

const router = useRouter();
const route = useRoute();

// ============ 子表 Layout 条件渲染模式相关 ============
const subTableLayoutMode = ref<'add' | 'edit' | 'list' | 'none' | 'view'>(
  'none',
);
const subTableLayoutEditId = ref<null | string>(null);
const subTableLayoutLoading = ref(false);
const subTableLayoutSaving = ref(false);
const subTableLayoutFormRef = ref();
const subTableLayoutFormData = reactive<Record<string, any>>({});
const subTableLayoutFieldPermissions = ref<Record<string, any>>({});
const subTableFormMeta = ref<FormMeta | null>(null);
const subTableFormDataListRef = ref();

const {
  initFormData: initSubTableFormData,
  extractMainData: extractSubTableMainData,
  extractSubTables: extractSubTableSubTables,
  resetFormData: resetSubTableFormData,
} = useFormData(subTableLayoutFormData);

// 子表 Layout 模式页面标题
const subTableLayoutPageTitle = computed(() => {
  const baseName =
    currentSubTableButton.value?.buttonText ||
    $t('form-manager.formRender.subTableData');
  const titles = {
    none: '',
    list: baseName,
    add: `${$t('common.add')}${baseName}`,
    edit: `${$t('common.edit')}${baseName}`,
    view: `${$t('common.view')}${baseName}`,
  };
  return titles[subTableLayoutMode.value];
});

// 子表 Layout 模式是否只读
const subTableLayoutIsReadonly = computed(
  () => subTableLayoutMode.value === 'view',
);

// 子表表单配置
const subTableFormConf = computed(() => {
  return (
    subTableFormMeta.value?.form_config || {
      items: [],
      labelWidth: 100,
      labelPosition: 'right',
      size: 'default',
    }
  );
});

// ============ 关联表单详情弹窗相关 ============
const showRelatedFormDialog = ref(false);
const relatedFormLoading = ref(false);
const relatedFormMeta = ref<FormMeta | null>(null);
const relatedFormData = reactive<Record<string, any>>({});
const relatedFormFieldPermissions = ref<Record<string, any>>({});

// 关联表单配置
const relatedFormConf = computed(() => {
  return (
    relatedFormMeta.value?.form_config || {
      items: [],
      labelWidth: 100,
      labelPosition: 'right',
      size: 'default',
    }
  );
});

// 关联表单弹窗标题
const relatedFormDialogTitle = computed(() => {
  return relatedFormMeta.value?.name || $t('common.view');
});

// 子表初始过滤条件
const subTableInitialFilters = computed(() => {
  if (
    !currentSubTableButton.value?.foreignKeyField ||
    !currentMainRecordId.value
  ) {
    return {};
  }
  return {
    [currentSubTableButton.value.foreignKeyField]: {
      type: 'eq',
      value: currentMainRecordId.value,
    },
  };
});

// 子表新增时的默认数据
const subTableDefaultFormData = computed(() => {
  if (
    !currentSubTableButton.value?.foreignKeyField ||
    !currentMainRecordId.value
  ) {
    return {};
  }
  return {
    [currentSubTableButton.value.foreignKeyField]: currentMainRecordId.value,
  };
});

// 构建子表路由路径
function buildSubTablePath(action: string, id?: string) {
  const subFormCode = currentSubTableButton.value?.subFormCode;
  if (!subFormCode) return '';

  const match = route.path.match(/^\/app\/([^/]+)/);
  const devMatch = route.path.match(/^\/app-dev\/([^/]+)/);

  let basePath: string;
  if (match && match[1]) {
    basePath = `/app/${match[1]}/form-layout/${subFormCode}`;
  } else if (devMatch && devMatch[1]) {
    basePath = `/app-dev/${devMatch[1]}/form-layout/${subFormCode}`;
  } else {
    basePath = `/form-layout/${subFormCode}`;
  }
  return id ? `${basePath}/${action}/${id}` : `${basePath}/${action}`;
}

// 加载子表单元数据
async function loadSubTableFormMeta() {
  if (!currentSubTableButton.value?.subFormCode) return;

  subTableLayoutLoading.value = true;
  try {
    subTableFormMeta.value = await getFormByCodeApi(
      currentSubTableButton.value.subFormCode,
    );
  } catch (error) {
    console.error('加载子表单失败:', error);
    ElMessage.error($t('form-manager.formRender.loadSubFormFailed'));
  } finally {
    subTableLayoutLoading.value = false;
  }
}

// 加载子表 Layout 模式字段权限
async function loadSubTableLayoutFieldPermissions() {
  if (!currentSubTableButton.value?.subFormCode) return;
  try {
    subTableLayoutFieldPermissions.value = await getFieldPermissionsApi(
      currentSubTableButton.value.subFormCode,
    );
  } catch (error) {
    console.error('加载字段权限失败:', error);
    subTableLayoutFieldPermissions.value = {};
  }
}

// 加载子表 Layout 模式编辑数据
async function loadSubTableLayoutEditData() {
  if (!subTableLayoutEditId.value) return;

  subTableLayoutLoading.value = true;
  try {
    await loadSubTableLayoutFieldPermissions();

    if (subTableFormMeta.value?.form_config?.items) {
      initSubTableFormData(subTableFormMeta.value.form_config.items);
    }

    const detail = await getFormDataDetailApi(
      currentSubTableButton.value.subFormCode,
      subTableLayoutEditId.value,
    );

    let mainData = detail.main;
    if (!mainData && !detail.main && typeof detail === 'object') {
      const { sub_tables, ...rest } = detail;
      mainData = rest;
    }

    if (mainData) {
      const trimmedData: Record<string, any> = {};
      Object.keys(mainData).forEach((key) => {
        const value = mainData[key];
        trimmedData[key] = typeof value === 'string' ? value.trim() : value;
      });
      Object.assign(subTableLayoutFormData, trimmedData);
    }

    const subTables = detail.sub_tables;
    if (subTables) {
      Object.keys(subTables).forEach((key) => {
        if (Array.isArray(subTables[key])) {
          subTableLayoutFormData[key] = subTables[key].map((row: any) => ({
            ...row,
            _id: row.id || `${Date.now()}_${Math.random()}`,
            _isEditing: false,
          }));
        }
      });
    }
  } catch (error: any) {
    console.error('Failed to load form data:', error);
    ElMessage.error(
      error?.message || $t('form-manager.formRender.loadDataFailed'),
    );
  } finally {
    subTableLayoutLoading.value = false;
  }
}

// 子表 Layout 模式保存表单
async function handleSubTableLayoutSave() {
  if (!subTableLayoutFormRef.value) return;

  try {
    await subTableLayoutFormRef.value.validate();
  } catch {
    ElMessage.warning($t('form-manager.formRender.validateFailed'));
    return;
  }

  subTableLayoutSaving.value = true;
  try {
    const mainData = extractSubTableMainData(
      subTableFormMeta.value!.form_config.items,
    );
    const subTables = extractSubTableSubTables(
      subTableFormMeta.value!.form_config.items,
    );

    // 确保外键字段被填充
    if (
      currentSubTableButton.value?.foreignKeyField &&
      currentMainRecordId.value
    ) {
      mainData[currentSubTableButton.value.foreignKeyField] =
        currentMainRecordId.value;
    }

    const payload = {
      main: mainData,
      sub_tables: subTables,
    };

    const action = listConfig.value.afterSaveAction || 'close';

    if (subTableLayoutMode.value === 'add') {
      const result = await createFormDataApi(
        currentSubTableButton.value.subFormCode,
        payload,
      );
      ElMessage.success($t('common.createSuccess'));

      if (action === 'editMode' && result?.id) {
        subTableLayoutEditId.value = result.id;
        subTableLayoutMode.value = 'edit';
        return;
      } else if (action === 'continueAdd') {
        resetSubTableFormData();
        if (subTableFormMeta.value?.form_config?.items) {
          initSubTableFormData(subTableFormMeta.value.form_config.items);
        }
        if (
          currentSubTableButton.value?.foreignKeyField &&
          currentMainRecordId.value
        ) {
          subTableLayoutFormData[currentSubTableButton.value.foreignKeyField] =
            currentMainRecordId.value;
        }
        return;
      }
    } else if (subTableLayoutMode.value === 'edit') {
      await updateFormDataApi(
        currentSubTableButton.value.subFormCode,
        subTableLayoutEditId.value!,
        payload,
      );
      ElMessage.success($t('common.updateSuccess'));
      if (action !== 'close') {
        return;
      }
    }

    handleSubTableLayoutBack();
  } catch (error: any) {
    console.error('Failed to save form data:', error);
    ElMessage.error(error?.message || $t('common.saveFailed'));
  } finally {
    subTableLayoutSaving.value = false;
  }
}

// 子表 Layout 模式返回列表
function handleSubTableLayoutBack() {
  subTableLayoutMode.value = 'list';
  subTableLayoutEditId.value = null;
  resetSubTableFormData();
  // 刷新子表列表数据
  subTableFormDataListRef.value?.reload();
}

// 子表 Layout 模式返回主表
function handleSubTableLayoutClose() {
  subTableLayoutMode.value = 'none';
  subTableLayoutEditId.value = null;
  resetSubTableFormData();
  currentSubTableButton.value = null;
  currentMainRecordId.value = '';
  subTableFormMeta.value = null;
}

// 子表 Layout 条件渲染模式 - 新增
function handleSubTableLayoutAdd() {
  resetSubTableFormData();
  loadSubTableLayoutFieldPermissions().then(() => {
    if (subTableFormMeta.value?.form_config?.items) {
      initSubTableFormData(subTableFormMeta.value.form_config.items);
    }
    // 填充外键默认值
    if (
      currentSubTableButton.value?.foreignKeyField &&
      currentMainRecordId.value
    ) {
      subTableLayoutFormData[currentSubTableButton.value.foreignKeyField] =
        currentMainRecordId.value;
    }
  });
  subTableLayoutMode.value = 'add';
}

// 子表 Layout 条件渲染模式 - 编辑
function handleSubTableLayoutEdit(row: any) {
  subTableLayoutEditId.value = row.id;
  subTableLayoutMode.value = 'edit';
  loadSubTableLayoutEditData();
}

// 子表 Layout 条件渲染模式 - 查看
function handleSubTableLayoutView(row: any) {
  subTableLayoutEditId.value = row.id;
  subTableLayoutMode.value = 'view';
  loadSubTableLayoutEditData();
}

// 打开子表单
function handleOpenSubTable(row: any, buttonConfig: any) {
  currentMainRecordId.value = row.id;
  currentSubTableButton.value = buttonConfig;

  const containerType = buttonConfig?.containerType;
  const renderMode = buttonConfig?.containerConfig?.renderMode || 'condition';

  if (containerType === 'layout') {
    if (renderMode === 'route') {
      // Layout 路由渲染模式：跳转到子表单的 form-render 路由
      const subFormCode = buttonConfig.subFormCode;
      const foreignKeyField = buttonConfig.foreignKeyField;
      const match = route.path.match(/^\/app\/([^/]+)/);
      const devMatch = route.path.match(/^\/app-dev\/([^/]+)/);

      let basePath: string;
      if (match && match[1]) {
        basePath = `/app/${match[1]}/form-render/${subFormCode}`;
      } else if (devMatch && devMatch[1]) {
        basePath = `/app-dev/${devMatch[1]}/form-render/${subFormCode}`;
      } else {
        basePath = `/form-render/${subFormCode}`;
      }
      // 带上外键过滤参数
      router.push({
        path: basePath,
        query: {
          [`filter_${foreignKeyField}`]: row.id,
          [`default_${foreignKeyField}`]: row.id,
        },
      });
    } else {
      // Layout 条件渲染模式：在当前页面内切换视图
      subTableLayoutMode.value = 'list';
      loadSubTableFormMeta();
    }
  } else {
    // Dialog/Drawer/Page 模式：使用 SubTableFormContainer
    showSubTableContainer.value = true;
  }
}

// 关闭子表单
function handleSubTableClosed() {
  showSubTableContainer.value = false;
  currentSubTableButton.value = null;
  currentMainRecordId.value = '';
}

// ============ 卡片模式相关 ============
const cardSearchKeyword = ref('');
const cardDataList = ref<any[]>([]);
const cardPagination = ref({
  current: 1,
  pageSize: 12,
  total: 0,
});
const cardQueryForm = ref<Record<string, any>>({});

// 卡片模式的查询字段（最多3个）
const cardQueryFields = computed(() => {
  const queryFields = formMeta.value?.list_config?.queryFields || [];
  return queryFields.slice(0, 3).map((field: any) => {
    if (field.originalComponent === 'switch' && field.component !== 'select') {
      return {
        ...field,
        component: 'select',
        type: 'eq',
        options: field.options?.length
          ? field.options
          : [
              { label: $t('common.yes'), value: true },
              { label: $t('common.no'), value: false },
            ],
      };
    }
    // 优先使用动态加载的选项（字典 / 表单数据源）
    const dynamicOpts = queryFieldDynamicOptions.value[field.field];
    if (dynamicOpts && dynamicOpts.length > 0) {
      return { ...field, options: dynamicOpts };
    }
    return field;
  });
});

// 加载卡片数据
async function loadCardData() {
  if (!props.formCode || listConfig.value.listType !== 'card') return;

  try {
    loading.value = true;
    const params: any = {
      page: cardPagination.value.current,
      pageSize: cardPagination.value.pageSize,
    };

    // 处理初始过滤条件（用于子表单过滤）
    if (props.initialFilters) {
      Object.entries(props.initialFilters).forEach(([field, config]) => {
        if (
          config &&
          typeof config === 'object' &&
          'type' in config &&
          'value' in config
        ) {
          const { type, value } = config as { type: string; value: any };
          if (value !== undefined && value !== null && value !== '') {
            switch (type) {
              case 'eq': {
                params[`${field}__eq`] = value;

                break;
              }
              case 'in': {
                params[`filter_${field}`] = Array.isArray(value)
                  ? value.join(',')
                  : value;

                break;
              }
              case 'like': {
                params[`${field}__like`] = value;

                break;
              }
              default: {
                params[`${field}__${type}`] = value;
              }
            }
          }
        }
      });
    }

    // 处理默认过滤条件（列表设计时配置的固定过滤）
    const defaultFilters = listConfig.value.table.defaultFilters;
    if (Array.isArray(defaultFilters) && defaultFilters.length > 0) {
      defaultFilters.forEach((condition: any) => {
        if (!condition.field || !condition.operator) return;
        const { field, operator, value } = condition;
        switch (operator) {
          case 'in': {
            params[`filter_${field}`] = value;

            break;
          }
          case 'like': {
            params[`${field}__like`] = value;

            break;
          }
          case 'not_null': {
            params[`${field}__not_null`] = '1';

            break;
          }
          case 'null': {
            params[`${field}__null`] = '1';

            break;
          }
          default: {
            params[`${field}__${operator}`] = value;
          }
        }
      });
    }

    // 处理查询表单参数（复用表格模式的查询逻辑）
    if (cardQueryForm.value) {
      Object.entries(cardQueryForm.value).forEach(([key, value]) => {
        if (value === undefined || value === null || value === '') return;

        // 获取该字段的查询配置
        const fieldConfig = getQueryFieldConfig(key);
        const queryType = fieldConfig?.type || 'like';

        // 范围查询（日期范围等）
        if (
          queryType === 'range' &&
          Array.isArray(value) &&
          value.length === 2
        ) {
          if (value[0]) params[`${key}__gte`] = value[0];
          if (value[1]) params[`${key}__lte`] = value[1];
        } else if (
          queryType === 'in' ||
          (Array.isArray(value) && value.length > 0)
        ) {
          // IN 查询或多选选择器
          params[`filter_${key}`] = Array.isArray(value)
            ? value.join(',')
            : value;
        } else
          switch (queryType) {
            case 'eq': {
              // 精确匹配
              params[`${key}__eq`] = value;
              if (fieldConfig?.caseSensitive === false) {
                params[`${key}__case_sensitive`] = 'false';
              }

              break;
            }
            case 'like': {
              // 模糊匹配
              params[`${key}__like`] = value;
              if (fieldConfig?.caseSensitive === false) {
                params[`${key}__case_sensitive`] = 'false';
              }

              break;
            }
            case 'space_eq_and': {
              params[`${key}__space_eq_and`] = value;
              if (fieldConfig?.caseSensitive === false) {
                params[`${key}__case_sensitive`] = 'false';
              }

              break;
            }
            case 'space_eq_or': {
              params[`${key}__space_eq_or`] = value;
              if (fieldConfig?.caseSensitive === false) {
                params[`${key}__case_sensitive`] = 'false';
              }

              break;
            }
            case 'space_like_and': {
              params[`${key}__space_like_and`] = value;
              if (fieldConfig?.caseSensitive === false) {
                params[`${key}__case_sensitive`] = 'false';
              }

              break;
            }
            case 'space_like_or': {
              params[`${key}__space_like_or`] = value;
              if (fieldConfig?.caseSensitive === false) {
                params[`${key}__case_sensitive`] = 'false';
              }

              break;
            }
            default: {
              params[key] = value;
            }
          }
      });
    }

    // 处理默认排序（卡片模式也支持排序）
    const defaultSort = listConfig.value.table.defaultSort;
    if (Array.isArray(defaultSort) && defaultSort.length > 0) {
      const validSorts = defaultSort.filter((s: any) => s.field);
      if (validSorts.length > 0) {
        params.sortFields = validSorts.map((s: any) => s.field).join(',');
        params.sortOrders = validSorts.map((s: any) => s.order).join(',');
      }
    }

    const res = await getFormDataListApi(props.formCode, params);
    cardDataList.value = res.items || [];
    cardPagination.value.total = res.total || 0;
  } catch (error) {
    console.error('加载卡片数据失败:', error);
    cardDataList.value = [];
  } finally {
    loading.value = false;
  }
}

// 卡片搜索
function handleCardSearch() {
  cardPagination.value.current = 1;
  loadCardData();
}

// 重置卡片查询
function handleCardReset() {
  cardQueryForm.value = {};
  cardPagination.value.current = 1;
  loadCardData();
}

// 卡片分页变化
function handleCardPageChange(page: number) {
  cardPagination.value.current = page;
  loadCardData();
}

function handleCardSizeChange(size: number) {
  cardPagination.value.pageSize = size;
  cardPagination.value.current = 1;
  loadCardData();
}

// 卡片点击（查看详情或选择）
function handleCardClick(item: any) {
  // 选择模式下，点击卡片触发选择
  if (props.selectionMode) {
    emit('row-select', item);
    return;
  }
  if (effectiveButtons.value.showView) {
    handleView(item);
  }
}

// 从 columns 中获取字段的完整配置
function getFieldConfigFromColumns(fieldName: string): any {
  const columns = formMeta.value?.list_config?.columns || [];
  return columns.find((col: any) => col.field === fieldName);
}

// 合并卡片字段配置和 columns 配置
function getMergedCardFieldConfig(cardFieldConfig: any): any {
  if (!cardFieldConfig || !cardFieldConfig.field) return cardFieldConfig;

  // 从 columns 中获取完整配置
  const columnConfig = getFieldConfigFromColumns(cardFieldConfig.field);
  if (columnConfig) {
    // 合并配置，columns 中的配置优先
    return { ...cardFieldConfig, ...columnConfig };
  }

  return cardFieldConfig;
}

// 判断是否是用户选择器组件
function isUserSelectorComponent(componentType: string): boolean {
  return ['user-selector', 'UserSelector'].includes(componentType);
}

// 获取卡片图标区域的合并配置（用于模板中判断 showAsAvatar 等属性）
const mergedIconConfig = computed(() => {
  const iconField = listConfig.value.cardFields?.icon;
  if (!iconField) return null;

  const merged = { ...getMergedCardFieldConfig(iconField) };

  // 如果没有 isUserSelector 属性，通过组件类型判断
  if (merged.isUserSelector === undefined) {
    const component =
      merged.component || merged.originalComponent || iconField.component;
    merged.isUserSelector = isUserSelectorComponent(component);
  }

  // 如果是用户选择器且在图标区域，默认启用头像显示
  if (merged.isUserSelector && merged.showAsAvatar === undefined) {
    merged.showAsAvatar = true;
  }

  return merged;
});

// 获取卡片字段值
function getCardFieldValue(item: any, fieldConfig: any): any {
  if (!fieldConfig || !fieldConfig.field) return null;

  // 获取合并后的配置
  const mergedConfig = getMergedCardFieldConfig(fieldConfig);

  let value = item[mergedConfig.field];

  // 优先使用 displayField 配置的字段（与 zq-table 保持一致）
  if (
    mergedConfig.displayField &&
    item[mergedConfig.displayField] !== undefined
  ) {
    value = item[mergedConfig.displayField];
  }
  // 检查是否有 _name 后缀的显示字段（省市区、关联字段等）
  else {
    const nameField = `${mergedConfig.field}_name`;
    if (item[nameField] !== undefined) {
      value = item[nameField];
    }
    // 关联字段显示名称
    else if (mergedConfig.showDisplayName && item[nameField] !== undefined) {
      value = item[nameField];
    }
  }

  // 如果值是数组，尝试转换为字符串
  if (Array.isArray(value)) {
    value = value.join(', ');
  }

  // 格式化处理
  if (
    mergedConfig.formatter &&
    mergedConfig.formatter !== 'none' &&
    value != null
  ) {
    value = formatCardValue(value, mergedConfig.formatter);
  }

  // 前缀后缀
  if (value != null && value !== '') {
    if (mergedConfig.prefix) value = `${mergedConfig.prefix}${value}`;
    if (mergedConfig.suffix) value = `${value}${mergedConfig.suffix}`;
  }

  return value;
}

// 格式化卡片字段值
function formatCardValue(value: any, formatter: string): string {
  if (value == null) return '';

  switch (formatter) {
    case 'date': {
      if (value) {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          return date.toLocaleDateString('zh-CN');
        }
      }
      return String(value);
    }
    case 'datetime': {
      if (value) {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          return date.toLocaleString('zh-CN');
        }
      }
      return String(value);
    }
    case 'money': {
      const num = Number(value);
      if (!isNaN(num)) {
        return `¥${num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      }
      return String(value);
    }
    case 'number': {
      const n = Number(value);
      if (!isNaN(n)) {
        return n.toLocaleString('zh-CN');
      }
      return String(value);
    }
    case 'percent': {
      const pct = Number(value);
      if (!isNaN(pct)) {
        return `${(pct * 100).toFixed(2)}%`;
      }
      return String(value);
    }
    default: {
      return String(value);
    }
  }
}

// 获取卡片字段显示值（用于带选项的字段）
function getCardFieldDisplayValue(item: any, fieldConfig: any): string {
  if (!fieldConfig || !fieldConfig.field) return '';

  // 获取合并后的配置
  const mergedConfig = getMergedCardFieldConfig(fieldConfig);

  const value = item[mergedConfig.field];

  // 优先使用 displayField 配置的字段（与 zq-table 保持一致）
  if (
    mergedConfig.displayField &&
    item[mergedConfig.displayField] !== undefined
  ) {
    return String(item[mergedConfig.displayField] ?? '');
  }

  // 检查是否有 _name 后缀的显示字段（省市区、关联字段等）
  const nameField = `${mergedConfig.field}_name`;
  if (item[nameField] !== undefined) {
    return String(item[nameField] ?? '');
  }

  // 关联字段显示名称（后端返回 {field}_name）
  if (mergedConfig.showDisplayName && item[nameField] !== undefined) {
    return String(item[nameField] ?? '');
  }

  // 如果有选项配置，查找对应的 label
  if (mergedConfig.options && Array.isArray(mergedConfig.options)) {
    const option = mergedConfig.options.find((opt: any) => opt.value === value);
    if (option) return option.label;
  }

  // 如果值是数组，转换为字符串
  if (Array.isArray(value)) {
    return value.join(', ');
  }

  // 格式化处理
  if (
    mergedConfig.formatter &&
    mergedConfig.formatter !== 'none' &&
    value != null
  ) {
    return formatCardValue(value, mergedConfig.formatter);
  }

  return String(value ?? '');
}

// 获取卡片标签类型
function getCardTagType(
  item: any,
  fieldConfig: any,
): 'danger' | 'info' | 'primary' | 'success' | 'warning' | undefined {
  if (!fieldConfig || !fieldConfig.field) return undefined;

  // 获取合并后的配置
  const mergedConfig = getMergedCardFieldConfig(fieldConfig);

  if (!mergedConfig.options) return undefined;
  const value = item[mergedConfig.field];
  const option = mergedConfig.options.find((opt: any) => opt.value === value);
  const tagType = option?.tagType;
  // 确保返回有效的 tag 类型或 undefined
  if (
    tagType &&
    ['danger', 'info', 'primary', 'success', 'warning'].includes(tagType)
  ) {
    return tagType as 'danger' | 'info' | 'primary' | 'success' | 'warning';
  }
  return undefined;
}

// 获取卡片头像 URL
function getCardAvatarUrl(item: any, fieldConfig: any): string {
  if (!fieldConfig || !fieldConfig.field) return '';

  // 获取合并后的配置
  const mergedConfig = getMergedCardFieldConfig(fieldConfig);

  // 尝试获取头像字段
  const avatarField = `${mergedConfig.field}_avatar`;
  if (item[avatarField]) {
    return item[avatarField];
  }

  // 如果字段值本身是 URL
  const value = item[mergedConfig.field];
  if (
    typeof value === 'string' &&
    (value.startsWith('http') || value.startsWith('/'))
  ) {
    return value;
  }

  return '';
}

// 判断卡片字段是否是 form-selector 类型
function isCardFieldFormSelector(fieldConfig: any): boolean {
  if (!fieldConfig || !fieldConfig.field) return false;
  const mergedConfig = getMergedCardFieldConfig(fieldConfig);
  return (
    mergedConfig.originalComponent === 'form-selector' &&
    !!mergedConfig.formCode
  );
}

// 获取卡片字段的 formCode
function getCardFieldFormCode(fieldConfig: any): string {
  if (!fieldConfig || !fieldConfig.field) return '';
  const mergedConfig = getMergedCardFieldConfig(fieldConfig);
  return mergedConfig.formCode || '';
}

// 处理卡片中 form-selector 字段的点击
function handleCardFormSelectorClick(e: Event, item: any, fieldConfig: any) {
  e.stopPropagation();
  const formCode = getCardFieldFormCode(fieldConfig);
  const recordId = item[fieldConfig.field];
  if (formCode && recordId) {
    handleFormSelectorClick(formCode, recordId);
  }
}

// 加载用户权限
async function loadUserPermissions() {
  if (!props.formCode) return;
  try {
    userPermissions.value = await getFormPermissionsApi(props.formCode);
  } catch (error) {
    console.error('加载权限失败:', error);
    // 权限加载失败时，默认无权限
    userPermissions.value = {
      view: false,
      add: false,
      edit: false,
      delete: false,
      export: false,
      import: false,
    };
  }
}

// 加载字段权限
async function loadFieldPermissions() {
  if (!props.formCode) return;
  try {
    fieldPermissions.value = await getFieldPermissionsApi(props.formCode);
  } catch (error) {
    console.error('加载字段权限失败:', error);
    fieldPermissions.value = {};
  }
}

// 加载表单配置（不在这里关闭 loading，由数据加载完成后关闭）
async function loadFormMeta() {
  if (!props.formCode) return;

  loading.value = true;
  try {
    formMeta.value = await getFormByCodeApi(props.formCode);
    emit('loaded', formMeta.value);
  } catch (error: any) {
    ElMessage.error(error?.message || '加载表单配置失败');
    loading.value = false; // 只在出错时关闭 loading
  }
  // 成功时不关闭 loading，等待数据加载完成
}

// 从 form_config.items 中递归提取字段名 -> { dataSource, componentType } 的映射
function extractFieldDataSourceMap(
  items: any[],
): Record<string, { componentType: string; dataSource: any }> {
  const map: Record<string, { componentType: string; dataSource: any }> = {};
  const layoutTypes = new Set([
    'alert',
    'collapse',
    'divider',
    'grid',
    'html',
    'spacer',
    'sub-table',
    'tabs',
    'text',
    'timeline',
    'title',
  ]);
  for (const item of items) {
    if (layoutTypes.has(item.type)) {
      if (item.columns) {
        for (const col of item.columns) {
          Object.assign(map, extractFieldDataSourceMap(col.children || []));
        }
      }
      if (item.items) {
        for (const sub of item.items) {
          Object.assign(map, extractFieldDataSourceMap(sub.children || []));
        }
      }
      if (item.children) {
        Object.assign(map, extractFieldDataSourceMap(item.children));
      }
      continue;
    }
    if (item.field && item.dataSource) {
      map[item.field] = {
        dataSource: item.dataSource,
        componentType: item.type || '',
      };
    }
  }
  return map;
}

// 根据 dictCode 加载字典选项到 queryFieldDynamicOptions
function pushDictTask(
  tasks: Promise<void>[],
  fieldName: string,
  dictCode: string,
) {
  if (queryFieldDynamicOptions.value[fieldName]) return;
  tasks.push(
    requestClient
      .get(`/api/core/dict_item/by/dict_code/${dictCode}`)
      .then((res: any) => {
        const data = res || [];
        queryFieldDynamicOptions.value[fieldName] = data.map((item: any) => ({
          label: item.label,
          value: item.value,
        }));
      })
      .catch(() => {}),
  );
}

// 根据 formCode 加载表单数据选项到 queryFieldDynamicOptions（扁平列表）
function pushFormDataTask(
  tasks: Promise<void>[],
  fieldName: string,
  formCode: string,
  valueField: string,
  labelField: string,
) {
  if (queryFieldDynamicOptions.value[fieldName]) return;
  tasks.push(
    requestClient
      .get(`/api/online_dev/form-data/${formCode}/list`, {
        params: { page: 1, pageSize: 9999 },
      })
      .then((res: any) => {
        const items = res?.items || [];
        queryFieldDynamicOptions.value[fieldName] = items.map((item: any) => ({
          label: item[labelField] ?? item.name ?? '',
          value: item[valueField] ?? item.id ?? '',
        }));
      })
      .catch(() => {}),
  );
}

// 将扁平数据构建为树形结构（用于级联组件）
function buildTreeOptions(
  flatItems: any[],
  valueField: string,
  labelField: string,
  parentField: string,
): any[] {
  function build(parentId: any): any[] {
    return flatItems
      .filter((item: any) => {
        const pv = item[parentField];
        if (parentId === null) {
          return pv === null || pv === undefined || pv === '' || pv === 0;
        }
        return String(pv) === String(parentId);
      })
      .map((item: any) => {
        const children = build(item[valueField]);
        const node: any = {
          label: item[labelField] ?? '',
          value: item[valueField] ?? '',
        };
        if (children.length > 0) {
          node.children = children;
        }
        return node;
      })
      .filter(
        (node: any) =>
          node.value !== '' && node.value !== null && node.value !== undefined,
      );
  }
  return build(null);
}

// 根据 formCode 加载级联树形选项到 queryFieldDynamicOptions
function pushCascaderFormDataTask(
  tasks: Promise<void>[],
  fieldName: string,
  formCode: string,
  valueField: string,
  labelField: string,
  parentField: string,
) {
  if (queryFieldDynamicOptions.value[fieldName]) return;
  tasks.push(
    requestClient
      .get(`/api/online_dev/form-data/${formCode}/list`, {
        params: { page: 1, pageSize: 9999 },
      })
      .then((res: any) => {
        const items = res?.items || [];
        queryFieldDynamicOptions.value[fieldName] = buildTreeOptions(
          items,
          valueField,
          labelField,
          parentField,
        );
      })
      .catch(() => {}),
  );
}

// 从 form_config.items 中获取指定字段的 dataSource 配置
function getFieldDataSource(fieldName: string): any {
  const formItems = formMeta.value?.form_config?.items || [];
  if (formItems.length === 0) return null;
  const fieldDsMap = extractFieldDataSourceMap(formItems);
  return fieldDsMap[fieldName]?.dataSource || null;
}

// 加载查询字段和列过滤中配置了字典 / 表单数据源的动态选项
async function loadQueryFieldOptions() {
  const queryFields = formMeta.value?.list_config?.queryFields || [];
  const tasks: Promise<void>[] = [];
  const selectLikeTypes = new Set([
    'cascader',
    'checkbox',
    'radio',
    'select',
    'tree-select',
  ]);
  const scheduled = new Set<string>();

  // 1. 查询字段
  for (const field of queryFields) {
    const comp = field.originalComponent || field.component;
    if (!selectLikeTypes.has(comp)) continue;

    if (field.dictCode) {
      pushDictTask(tasks, field.field, field.dictCode);
      scheduled.add(field.field);
    } else if (field.dataSourceType === 'formData' && field.formCode) {
      if (['cascader', 'tree-select'].includes(comp)) {
        const ds = getFieldDataSource(field.field);
        const parentField = ds?.formParentField || 'parent_id';
        pushCascaderFormDataTask(
          tasks,
          field.field,
          field.formCode,
          field.valueField || 'id',
          field.labelField || 'name',
          parentField,
        );
      } else {
        pushFormDataTask(
          tasks,
          field.field,
          field.formCode,
          field.valueField || 'id',
          field.labelField || 'name',
        );
      }
      scheduled.add(field.field);
    }
  }

  // 2. 列过滤：从 form_config 中获取组件的 dataSource 配置
  const columns = formMeta.value?.list_config?.columns || [];
  const formItems = formMeta.value?.form_config?.items || [];
  const fieldDsMap =
    formItems.length > 0 ? extractFieldDataSourceMap(formItems) : {};

  for (const col of columns) {
    if (!col.filterable || scheduled.has(col.field)) continue;
    const entry = fieldDsMap[col.field];
    if (!entry) continue;
    const ds = entry.dataSource;
    const compType = entry.componentType;

    if (ds.type === 'dict' && ds.dictCode) {
      pushDictTask(tasks, col.field, ds.dictCode);
      scheduled.add(col.field);
    } else if (ds.type === 'formData' && ds.formCode) {
      if (['cascader', 'tree-select'].includes(compType)) {
        const parentField = ds.formParentField || 'parent_id';
        pushCascaderFormDataTask(
          tasks,
          col.field,
          ds.formCode,
          ds.formValueField || 'id',
          ds.formLabelField || 'name',
          parentField,
        );
      } else {
        const valueField = ds.formValueField || ds.valueField || 'id';
        const labelField = ds.formLabelField || ds.labelField || 'name';
        pushFormDataTask(tasks, col.field, ds.formCode, valueField, labelField);
      }
      scheduled.add(col.field);
    }
  }

  if (tasks.length > 0) {
    await Promise.all(tasks);
  }
}

// 格式化值
function formatValue(value: any, col: any) {
  if (value === null || value === undefined || value === '') return '-';

  let formatted = value;

  switch (col.formatter) {
    case 'date': {
      formatted = dayjs(value).format(col.formatPattern || 'YYYY-MM-DD');
      break;
    }
    case 'datetime': {
      formatted = dayjs(value).format(
        col.formatPattern || 'YYYY-MM-DD HH:mm:ss',
      );
      break;
    }
    case 'money': {
      formatted = Number(value).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      break;
    }
    case 'number': {
      formatted = Number(value).toLocaleString();
      break;
    }
    case 'percent': {
      formatted = `${Number(value).toFixed(2)}%`;
      break;
    }
  }

  if (col.prefix) formatted = `${col.prefix}${formatted}`;
  if (col.suffix) formatted = `${formatted}${col.suffix}`;

  return formatted;
}

function parseWidth(width: any) {
  if (!width || width === 'auto') return undefined;
  const num = Number(width);
  return isNaN(num) ? undefined : num;
}

function getOptionDisplay(
  value: any,
  options: any[],
  isMultiple = false,
): { label: string; type: string | undefined }[] {
  if (!options || options.length === 0) return [];

  const values = isMultiple && Array.isArray(value) ? value : [value];

  return values.map((val) => {
    const trimmedVal = typeof val === 'string' ? val.trim() : val;
    const option = options.find((opt: any) => {
      const optValue =
        typeof opt.value === 'string' ? opt.value.trim() : opt.value;
      return optValue === trimmedVal;
    });

    if (!option) {
      return { label: String(trimmedVal), type: undefined };
    }
    return {
      label: option.label as string,
      type: option.tagType || undefined,
    };
  });
}

// 图片预览状态
const previewImages = ref<string[]>([]);
const showImageViewer = ref(false);
const imageUrlCache = ref<Map<string, string>>(new Map());

// 获取文件ID数组
function getFileIds(value: any): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value === 'string') return [value];
  return [];
}

// 渲染图片单元格
function renderImageCell(value: any, col: any) {
  const fileIds = getFileIds(value);
  if (fileIds.length === 0) return '-';

  const align = col?.align || 'left';
  const justifyMap: Record<string, string> = {
    left: 'flex-start',
    center: 'center',
    right: 'flex-end',
  };
  const justify = justifyMap[align] || 'flex-start';

  const firstId = fileIds[0];
  const cachedUrl = imageUrlCache.value.get(firstId!);

  // 如果没有缓存，异步加载
  if (!cachedUrl && firstId) {
    getFileUrl(firstId).then((url) => {
      imageUrlCache.value.set(firstId, url);
    });
  }

  const handlePreview = async () => {
    // 加载所有图片URL
    const urls = await Promise.all(
      fileIds.map(async (id) => {
        const cached = imageUrlCache.value.get(id);
        if (cached) return cached;
        const url = await getFileUrl(id);
        imageUrlCache.value.set(id, url);
        return url;
      }),
    );
    previewImages.value = urls.filter(Boolean);
    showImageViewer.value = true;
  };

  // URL 未加载时显示 loading 占位，避免 ElImage 收到空 src 显示加载失败
  const imageNode = cachedUrl
    ? h(ElImage, {
        src: cachedUrl,
        fit: 'cover',
        style: {
          width: '32px',
          height: '32px',
          cursor: 'pointer',
          borderRadius: '4px',
        },
        previewSrcList: [],
        onClick: handlePreview,
      })
    : h('div', {
        class: 'flex items-center justify-center',
        style: {
          width: '32px',
          height: '32px',
          borderRadius: '4px',
          backgroundColor: 'var(--el-fill-color-light)',
          animation: 'el-skeleton-loading 1.4s ease infinite',
        },
      });

  return h(
    'div',
    {
      class: 'flex items-center gap-1',
      style: { justifyContent: justify },
    },
    [
      imageNode,
      fileIds.length > 1
        ? h(
            ElTooltip,
            { content: `共 ${fileIds.length} 张图片`, placement: 'top' },
            () =>
              h(
                'span',
                { class: 'text-xs text-gray-400' },
                `+${fileIds.length - 1}`,
              ),
          )
        : null,
    ].filter(Boolean),
  );
}

// 渲染文件单元格
function renderFileCell(value: any, _col: any) {
  const fileIds = getFileIds(value);
  if (fileIds.length === 0) return '-';

  return h(FileListCell, { fileIds });
}

// 根据 list_config 生成表格列（根据字段权限过滤隐藏的列）
const tableColumns = computed(() => {
  if (!formMeta.value?.list_config?.columns) return [];

  // 过滤掉隐藏的字段
  const visibleColumns = formMeta.value.list_config.columns.filter(
    (col: any) => {
      const perm = fieldPermissions.value[col.field];
      // 如果字段权限为 hidden，则不显示该列（兼容 permission_type 和 permission 两种key）
      const permType = perm?.permission_type || perm?.permission;
      if (permType === 'hidden') {
        return false;
      }
      return true;
    },
  );

  const columns = visibleColumns.map((col: any) => {
    const width = parseWidth(col.width);
    const minWidth = parseWidth(col.minWidth);

    // 处理排序配置：后端排序使用 'custom'，前端排序使用 true
    const sortableValue = col.sortable
      ? col.sortType === 'backend'
        ? 'custom'
        : true
      : false;

    return {
      key: col.field,
      dataKey: col.field,
      title: col.label,
      prop: col.field,
      width,
      minWidth: minWidth || (width ? undefined : 120),
      sortable: sortableValue,
      // 自定义过滤配置
      filterable: col.filterable ?? false,
      filterMultiple: col.filterMultiple ?? true,
      filterQueryType: col.filterQueryType || 'range', // 日期过滤查询类型
      filterShowTime: col.filterShowTime ?? false, // 日期过滤是否显示时间
      options: queryFieldDynamicOptions.value[col.field] || col.options, // 动态选项优先，回退到静态选项
      originalComponent: col.originalComponent, // 传递原始组件类型用于过滤弹窗判断
      // 级联过滤配置
      cascaderProps: ['cascader', 'tree-select'].includes(col.originalComponent)
        ? {
            emitPath: col.props?.emitPath ?? false,
            checkStrictly: col.props?.checkStrictly ?? true,
            multiple: col.props?.multiple ?? false,
          }
        : undefined,
      formCode: col.formCode, // 表单/表格选择器的 formCode
      formSelectorValueField: col.valueField || 'id', // 选择器值字段
      formSelectorLabelField: col.labelField || 'name', // 选择器显示字段
      // table-selector 额外配置
      tableSelectorDataSourceType: col.dataSourceType,
      tableSelectorDictCode: col.dictCode,
      tableSelectorDataSourceCode: col.dataSourceCode,
      tableSelectorColumns: col.columns,
      tableSelectorSearchFields: col.searchFields,
      fixed: col.fixed,
      align: col.align || 'left',
      headerAlign: col.align || 'left',
      resizable: col.resizable ?? true,
      cellRenderer: ({ cellData, rowData }: any) => {
        let displayValue = cellData;
        if (col.displayField && rowData[col.displayField] !== undefined) {
          displayValue = rowData[col.displayField];
        }

        // 处理用户选择器显示头像
        if (
          col.showAsAvatar &&
          (col.originalComponent === 'user-select' ||
            col.originalComponent === 'user-selector') &&
          cellData
        ) {
          // 支持单选和多选
          const userIds = Array.isArray(cellData) ? cellData : [cellData];
          const userNames = displayValue
            ? Array.isArray(displayValue)
              ? displayValue
              : [displayValue]
            : [];

          if (userIds.length === 0) {
            return '-';
          }

          return h(
            'div',
            { class: 'flex flex-wrap items-center gap-2' },
            userIds.map((userId: string, idx: number) =>
              h('div', { key: userId, class: 'flex items-center gap-1' }, [
                h(UserAvatar, {
                  userId,
                  name: userNames[idx] || undefined,
                  size: 24,
                  fontSize: 10,
                  shadow: false,
                  showPopover: true,
                  autoLoad: true, // 始终自动加载以获取头像
                }),
                userNames[idx]
                  ? h('span', { class: 'text-sm' }, userNames[idx])
                  : null,
              ]),
            ),
          );
        }

        // 处理图片字段
        if (col.originalComponent === 'image-selector' && displayValue) {
          return renderImageCell(displayValue, col);
        }

        // 处理文件字段
        if (col.originalComponent === 'file-selector' && displayValue) {
          return renderFileCell(displayValue, col);
        }

        // 处理表单选择器字段（form-selector）- 点击可跳转到关联表单详情
        if (
          col.originalComponent === 'form-selector' &&
          col.formCode &&
          cellData
        ) {
          return h(
            'span',
            {
              class:
                'inline-flex items-center gap-1 px-2 py-1 text-xs rounded-md bg-primary/10 text-primary hover:bg-primary/20 cursor-pointer transition-colors',
              onClick: (e: Event) => {
                e.stopPropagation();
                handleFormSelectorClick(col.formCode, cellData);
              },
            },
            [
              h(Link, { class: 'w-3 h-3 flex-shrink-0' }),
              displayValue || cellData,
            ],
          );
        }

        const effectiveOptions =
          queryFieldDynamicOptions.value[col.field] || col.options;
        if (
          col.showAsTag &&
          effectiveOptions &&
          displayValue !== null &&
          displayValue !== undefined &&
          displayValue !== ''
        ) {
          const isMultiple = Array.isArray(displayValue);
          const displays = getOptionDisplay(
            displayValue,
            effectiveOptions,
            isMultiple,
          );

          if (displays.length === 0) {
            return '-';
          }

          if (displays.length > 1) {
            return h(
              'div',
              { class: 'flex flex-wrap gap-1' },
              displays.map((item, idx) =>
                h(
                  ElTag,
                  { key: idx, type: item.type as any, size: 'small' },
                  () => item.label,
                ),
              ),
            );
          }

          const firstDisplay = displays[0]!;
          return h(
            ElTag,
            { type: firstDisplay.type as any, size: 'small' },
            () => firstDisplay.label,
          );
        }

        const content = formatValue(displayValue, col);

        if (col.showOverflowTooltip || col.ellipsis) {
          return h(
            'div',
            {
              class: `truncate ${col.ellipsis ? 'w-full' : ''}`,
              title: col.showOverflowTooltip ? content : undefined,
            },
            content,
          );
        }
        return content;
      },
    };
  });

  // 选择模式下添加选择列和序号列
  if (props.selectionMode) {
    const valueField = props.selectionValueField || 'id';

    // 添加序号列（在选择列之后）
    columns.unshift({
      key: '_index',
      dataKey: '_index',
      title: '#',
      width: 60,
      fixed: 'left',
      align: 'center',
      cellRenderer: ({ rowIndex }: any) => {
        return h('span', {}, rowIndex + 1);
      },
    });

    // 添加选择列（在最前面）
    columns.unshift({
      key: '_selection',
      dataKey: '_selection',
      title: '',
      width: 50,
      fixed: 'left',
      align: 'center',
      // 多选模式下添加表头全选 checkbox
      headerCellRenderer: props.selectionMultiple
        ? () => {
            const allData = gridApi.tableData.value || [];
            const allSelected =
              allData.length > 0 &&
              allData.every((row: any) =>
                props.selectedValues?.has(String(row[valueField])),
              );
            const someSelected =
              allData.some((row: any) =>
                props.selectedValues?.has(String(row[valueField])),
              ) && !allSelected;

            return h(ElCheckbox, {
              modelValue: allSelected,
              indeterminate: someSelected,
              onChange: () => emit('select-all', allData),
            });
          }
        : undefined,
      cellRenderer: ({ rowData }: any) => {
        const value = String(rowData[valueField]);
        const isSelected = props.selectedValues?.has(value) ?? false;

        if (props.selectionMultiple) {
          // 多选模式：显示 checkbox
          return h(ElCheckbox, {
            modelValue: isSelected,
            onChange: () => emit('row-select', rowData),
          });
        } else {
          // 单选模式：显示 radio
          return h(ElRadio, {
            modelValue: isSelected,
            value: true,
            onChange: () => emit('row-select', rowData),
          });
        }
      },
    });
  }

  const showActions =
    effectiveButtons.value.showView ||
    effectiveButtons.value.showEdit ||
    effectiveButtons.value.showDelete;
  // 选择模式下不显示操作列
  if (showActions && !props.selectionMode) {
    // 动态计算操作列宽度：基础按钮（查看/编辑/删除）+ 子表按钮 + 自定义行按钮
    let actionBtnCount = 0;
    if (effectiveButtons.value.showView) actionBtnCount++;
    if (effectiveButtons.value.showEdit) actionBtnCount++;
    if (effectiveButtons.value.showDelete) actionBtnCount++;
    actionBtnCount += listConfig.value.subTableButtons?.length || 0;
    actionBtnCount +=
      listConfig.value.customButtons?.filter(
        (btn: any) => btn.position === 'row',
      )?.length || 0;
    // 每个按钮约 70px，最小 120px
    const actionWidth = Math.max(120, actionBtnCount * 70 + 16);
    columns.push({
      key: 'actions',
      dataKey: 'actions',
      title: $t('common.operation'),
      width: actionWidth,
      minWidth: actionWidth,
      fixed: 'right',
      align: 'center',
    });
  }

  return columns;
});

const QUERY_WIDTH_CLASS_MAP: Record<number, string> = {
  3: 'col-span-1',
  4: 'col-span-2',
  6: 'col-span-3',
  8: 'col-span-4',
  12: 'col-span-6',
  24: 'col-span-12',
};

function getQueryFieldClass(width?: number) {
  if (!width) return QUERY_WIDTH_CLASS_MAP[6]!;
  return QUERY_WIDTH_CLASS_MAP[width] || QUERY_WIDTH_CLASS_MAP[6]!;
}

// 根据 list_config 生成查询表单配置
const formSchema = computed(() => {
  if (!formMeta.value?.list_config?.queryFields) return [];

  return formMeta.value.list_config.queryFields.map((rawField: any) => {
    // 兼容旧数据：开关组件强制映射为 select
    const field =
      rawField.originalComponent === 'switch' && rawField.component !== 'select'
        ? {
            ...rawField,
            component: 'select',
            type: 'eq',
            options: rawField.options?.length
              ? rawField.options
              : [
                  { label: $t('common.yes'), value: true },
                  { label: $t('common.no'), value: false },
                ],
          }
        : rawField;
    // 优先使用 originalComponent（如果存在），否则使用 component
    const sourceComponent = field.originalComponent || field.component;
    const componentType = mapComponent(sourceComponent);
    const componentProps = buildComponentProps(field, componentType);

    return {
      fieldName: field.field,
      label: field.label,
      component: componentType,
      componentProps,
      defaultValue: field.defaultValue,
      formItemClass: getQueryFieldClass(field.width),
    };
  });
});

function mapComponent(type: string) {
  const map: Record<string, string> = {
    input: 'Input',
    select: 'Select',
    radio: 'Select',
    checkbox: 'Select',
    cascader: 'Cascader',
    'tree-select': 'TreeSelect',
    switch: 'Select',
    date: 'DatePicker',
    'date-picker': 'DatePicker',
    time: 'TimePicker',
    'time-picker': 'TimePicker',
    'user-select': 'UserSelector',
    'user-selector': 'UserSelector',
    'dept-select': 'DeptSelector',
    'dept-selector': 'DeptSelector',
    'department-selector': 'DeptSelector',
    'post-select': 'PostSelector',
    'post-selector': 'PostSelector',
    'position-selector': 'PostSelector',
    'form-selector': 'FormSelector',
    'table-selector': 'TableSelector',
  };
  return map[type] || 'Input';
}

function buildComponentProps(
  field: any,
  componentType: string,
): Record<string, any> {
  const componentProps: Record<string, any> = {
    clearable: true,
  };

  // 选择器组件的 placeholder
  componentProps.placeholder = [
    'Cascader',
    'DeptSelector',
    'FormSelector',
    'PostSelector',
    'Select',
    'TableSelector',
    'TreeSelect',
    'UserSelector',
  ].includes(componentType)
    ? `请选择${field.label}`
    : `请输入${field.label}`;

  if (componentType === 'Select') {
    const sourceComp = field.originalComponent || field.component;
    const itemProps = field.props || {};
    // 优先使用动态加载的选项（字典 / 表单数据源）
    const dynamicOpts = queryFieldDynamicOptions.value[field.field];
    if (sourceComp === 'switch') {
      componentProps.options = field.options?.length
        ? field.options.map((opt: any) => ({
            label: opt.label,
            value: opt.value,
          }))
        : [
            { label: $t('common.yes'), value: true },
            { label: $t('common.no'), value: false },
          ];
    } else if (dynamicOpts && dynamicOpts.length > 0) {
      componentProps.options = dynamicOpts;
    } else if (field.options) {
      componentProps.options = field.options.map((opt: any) => ({
        label: opt.label,
        value: opt.value,
      }));
    }
    // 从原始组件 props 中读取 filterable（与表单 PreviewItem 保持一致）
    if (itemProps.filterable) {
      componentProps.filterable = true;
    }
    if (field.multiple || itemProps.multiple) {
      componentProps.multiple = true;
      componentProps.collapseTags = true;
      componentProps.collapseTagsTooltip = true;
    }
  }

  if (componentType === 'Cascader') {
    const dynamicOpts = queryFieldDynamicOptions.value[field.field];
    if (dynamicOpts && dynamicOpts.length > 0) {
      componentProps.options = dynamicOpts;
    } else if (field.options) {
      componentProps.options = field.options;
    }
    componentProps.filterable = true;
    componentProps.clearable = true;

    // 从原始组件 props 中读取级联配置（与表单 PreviewItem 中 cascaderElProps 保持一致）
    const itemProps = field.props || {};
    const cascaderConfig: Record<string, any> = {};
    if (itemProps.expandTrigger)
      cascaderConfig.expandTrigger = itemProps.expandTrigger;
    if (itemProps.checkStrictly)
      cascaderConfig.checkStrictly = itemProps.checkStrictly;
    if (itemProps.multiple !== undefined)
      cascaderConfig.multiple = itemProps.multiple;
    // emitPath 默认 false（只取最后一级值），与表单设计 MaterialPanel 默认值一致
    cascaderConfig.emitPath = itemProps.emitPath ?? false;
    componentProps.props = cascaderConfig;

    if (field.multiple || itemProps.multiple) {
      componentProps.collapseTags = true;
      componentProps.collapseTagsTooltip = true;
    }
  }

  if (componentType === 'TreeSelect') {
    const dynamicOpts = queryFieldDynamicOptions.value[field.field];
    if (dynamicOpts && dynamicOpts.length > 0) {
      componentProps.data = dynamicOpts;
    } else if (field.options) {
      componentProps.data = field.options;
    }
    componentProps.nodeKey = 'value';
    componentProps.clearable = true;
    componentProps.renderAfterExpand = false;

    const itemProps = field.props || {};
    if (itemProps.filterable) componentProps.filterable = true;
    if (itemProps.checkStrictly) componentProps.checkStrictly = true;
    if (itemProps.checkOnClickNode) componentProps.checkOnClickNode = true;
    if (field.multiple || itemProps.multiple) {
      componentProps.multiple = true;
      componentProps.showCheckbox = true;
      componentProps.collapseTags = true;
      componentProps.collapseTagsTooltip = true;
    }
  }

  if (componentType === 'DatePicker') {
    // 检查是否显示时间（从查询字段配置中获取 showTime 属性）
    const showTime = field.showTime === true;
    // 查询类型（eq: 精确匹配, range: 范围查询）
    const queryType = field.type;

    // 根据查询类型和是否显示时间决定日期选择器类型
    if (queryType === 'range' && showTime) {
      // 范围查询 + 显示时间：使用 datetimerange
      componentProps.type = 'datetimerange';
      componentProps.format = 'YYYY-MM-DD HH:mm:ss';
      componentProps.valueFormat = 'YYYY-MM-DD HH:mm:ss';
    } else if (queryType === 'range') {
      // 范围查询：使用 daterange
      componentProps.type = 'daterange';
      componentProps.format = 'YYYY-MM-DD';
      componentProps.valueFormat = 'YYYY-MM-DD';
    } else if (queryType === 'eq' && showTime) {
      // 精确匹配 + 显示时间：使用 datetime
      componentProps.type = 'datetime';
      componentProps.format = 'YYYY-MM-DD HH:mm:ss';
      componentProps.valueFormat = 'YYYY-MM-DD HH:mm:ss';
    } else if (queryType === 'eq') {
      // 精确匹配：使用 date
      componentProps.type = 'date';
      componentProps.format = 'YYYY-MM-DD';
      componentProps.valueFormat = 'YYYY-MM-DD';
    } else {
      // 默认：使用 daterange（兼容旧配置）
      componentProps.type = 'daterange';
      componentProps.format = 'YYYY-MM-DD';
      componentProps.valueFormat = 'YYYY-MM-DD';
    }

    // 范围选择器的占位符
    if (
      componentProps.type === 'daterange' ||
      componentProps.type === 'datetimerange'
    ) {
      componentProps.startPlaceholder = '开始日期';
      componentProps.endPlaceholder = '结束日期';
      componentProps.rangeSeparator = '-';
    }
  }

  if (componentType === 'TimePicker') {
    componentProps.format = field.props?.format || 'HH:mm:ss';
    componentProps.valueFormat = field.props?.valueFormat || 'HH:mm:ss';
  }

  // 用户/部门/岗位选择器组件
  if (
    ['DeptSelector', 'PostSelector', 'UserSelector'].includes(componentType)
  ) {
    componentProps.multiple = true;
  }

  // 表单选择器组件
  if (componentType === 'FormSelector') {
    componentProps.formCode = field.formCode || '';
    componentProps.valueField = field.valueField || 'id';
    componentProps.labelField = field.labelField || 'name';
    componentProps.multiple = true;
  }

  // 表格选择器组件
  if (componentType === 'TableSelector') {
    componentProps.dataSourceType = field.dataSourceType || 'static';
    componentProps.formCode = field.formCode || '';
    componentProps.dictCode = field.dictCode || '';
    componentProps.dataSourceCode = field.dataSourceCode || '';
    componentProps.valueField = field.valueField || 'id';
    componentProps.labelField = field.labelField || 'name';
    componentProps.columns = field.columns;
    componentProps.searchFields = field.searchFields;
    componentProps.multiple = true;
  }

  return componentProps;
}

// 获取查询字段的配置
function getQueryFieldConfig(fieldName: string) {
  const queryFields = formMeta.value?.list_config?.queryFields || [];
  return queryFields.find((f: any) => f.field === fieldName);
}

/**
 * 构建过滤/排序/搜索查询参数（供数据查询和导出共用）
 * @param formValues 表单查询字段的值
 */
function buildFilterQueryParams(
  formValues?: Record<string, any>,
): Record<string, any> {
  const queryParams: any = {};

  // 处理初始过滤条件（用于子表单过滤）
  if (props.initialFilters) {
    Object.entries(props.initialFilters).forEach(([field, config]) => {
      if (
        config &&
        typeof config === 'object' &&
        'type' in config &&
        'value' in config
      ) {
        const { type, value } = config as { type: string; value: any };
        if (value !== undefined && value !== null && value !== '') {
          switch (type) {
            case 'eq': {
              queryParams[`${field}__eq`] = value;
              break;
            }
            case 'in': {
              queryParams[`filter_${field}`] = Array.isArray(value)
                ? value.join(',')
                : value;
              break;
            }
            case 'like': {
              queryParams[`${field}__like`] = value;
              break;
            }
            default: {
              queryParams[`${field}__${type}`] = value;
            }
          }
        }
      }
    });
  }

  // 处理默认过滤条件（列表设计时配置的固定过滤）
  const defaultFilters = listConfig.value.table.defaultFilters;
  if (Array.isArray(defaultFilters) && defaultFilters.length > 0) {
    defaultFilters.forEach((condition: any) => {
      if (!condition.field || !condition.operator) return;
      const { field, operator, value } = condition;
      switch (operator) {
        case 'in': {
          queryParams[`filter_${field}`] = value;

          break;
        }
        case 'like': {
          queryParams[`${field}__like`] = value;

          break;
        }
        case 'not_null': {
          queryParams[`${field}__not_null`] = '1';

          break;
        }
        case 'null': {
          queryParams[`${field}__null`] = '1';

          break;
        }
        default: {
          queryParams[`${field}__${operator}`] = value;
        }
      }
    });
  }

  // 处理表单查询参数
  if (formValues) {
    Object.entries(formValues).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') return;

      const fieldConfig = getQueryFieldConfig(key);
      const queryType = fieldConfig?.type || 'like';

      if (queryType === 'range' && Array.isArray(value) && value.length === 2) {
        if (value[0]) queryParams[`${key}__gte`] = value[0];
        if (value[1]) queryParams[`${key}__lte`] = value[1];
      } else if (
        queryType === 'in' ||
        (Array.isArray(value) && value.length > 0)
      ) {
        queryParams[`filter_${key}`] = Array.isArray(value)
          ? value.join(',')
          : value;
      } else
        switch (queryType) {
          case 'eq': {
            queryParams[`${key}__eq`] = value;
            if (fieldConfig?.caseSensitive === false) {
              queryParams[`${key}__case_sensitive`] = 'false';
            }

            break;
          }
          case 'like': {
            queryParams[`${key}__like`] = value;
            // 大小写敏感标志（默认敏感，仅当明确设为 false 时传递）
            if (fieldConfig?.caseSensitive === false) {
              queryParams[`${key}__case_sensitive`] = 'false';
            }

            break;
          }
          case 'space_eq_and': {
            queryParams[`${key}__space_eq_and`] = value;
            if (fieldConfig?.caseSensitive === false) {
              queryParams[`${key}__case_sensitive`] = 'false';
            }

            break;
          }
          case 'space_eq_or': {
            queryParams[`${key}__space_eq_or`] = value;
            if (fieldConfig?.caseSensitive === false) {
              queryParams[`${key}__case_sensitive`] = 'false';
            }

            break;
          }
          case 'space_like_and': {
            queryParams[`${key}__space_like_and`] = value;
            if (fieldConfig?.caseSensitive === false) {
              queryParams[`${key}__case_sensitive`] = 'false';
            }

            break;
          }
          case 'space_like_or': {
            queryParams[`${key}__space_like_or`] = value;
            if (fieldConfig?.caseSensitive === false) {
              queryParams[`${key}__case_sensitive`] = 'false';
            }

            break;
          }
          default: {
            queryParams[key] = value;
          }
        }
    });
  }

  // 优先使用用户点击列头触发的排序
  if (currentSort.value.field && currentSort.value.order) {
    queryParams.sortFields = currentSort.value.field;
    queryParams.sortOrders =
      currentSort.value.order === 'ascending' ? 'asc' : 'desc';
  } else {
    const defaultSort = listConfig.value.table.defaultSort;
    if (Array.isArray(defaultSort) && defaultSort.length > 0) {
      const validSorts = defaultSort.filter((s: any) => s.field);
      if (validSorts.length > 0) {
        queryParams.sortFields = validSorts.map((s: any) => s.field).join(',');
        queryParams.sortOrders = validSorts.map((s: any) => s.order).join(',');
      }
    }
  }

  // 处理过滤参数（来自列头过滤）
  const filterEntries = Object.entries(currentFilters.value);
  if (filterEntries.length > 0) {
    filterEntries.forEach(([field, values]) => {
      if (!values) return;

      const colConfig = formMeta.value?.list_config?.columns?.find(
        (c: any) => c.field === field,
      );
      const isDateComponent =
        colConfig?.originalComponent &&
        [
          'date',
          'date-picker',
          'datetime',
          'datetime-picker',
          'time',
          'time-picker',
        ].includes(colConfig.originalComponent);

      if (typeof values === 'string') {
        if (isDateComponent) {
          queryParams[`${field}__eq`] = values;
        } else {
          queryParams[`filter_${field}`] = values;
        }
        return;
      }

      if (Array.isArray(values) && values.length > 0) {
        const allValuesAreDateStrings =
          values.length === 2 &&
          values.every(
            (v: any) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}/.test(v),
          );

        const isDateRange = isDateComponent || allValuesAreDateStrings;

        if (isDateRange && values.length === 2) {
          queryParams[`${field}__gte`] = values[0];
          queryParams[`${field}__lte`] = values[1];
        } else {
          queryParams[`filter_${field}`] = values.join(',');
        }
      }
    });
  }

  return queryParams;
}

// 数据查询函数
async function queryData(params: { form: any; page: any }) {
  if (!props.formCode) return { items: [], total: 0 };

  // 树形表格懒加载模式：使用专门的 API 获取根节点
  if (listConfig.value.tree.enabled && listConfig.value.tree.lazy) {
    const rootNodes = await getTreeChildrenApi(props.formCode, {
      parentId: undefined, // 获取根节点
      parentField: listConfig.value.tree.parentField,
    });
    return {
      items: rootNodes || [],
      total: rootNodes?.length || 0,
    };
  }

  // 构建查询参数（树形和普通模式都需要）
  const queryParams: any = {
    page: params.page.currentPage,
    pageSize: params.page.pageSize,
    ...buildFilterQueryParams(params.form),
  };

  // 树形表格非懒加载模式：需要获取全部数据来构建树
  if (listConfig.value.tree.enabled && !listConfig.value.tree.lazy) {
    queryParams.page = 1;
    queryParams.pageSize = 9999;
  }

  const res = await getFormDataListApi(props.formCode, queryParams);

  // 树形表格非懒加载模式：构建树形结构
  if (listConfig.value.tree.enabled && !listConfig.value.tree.lazy) {
    const treeData = buildTreeData(
      res.items || [],
      listConfig.value.tree.parentField,
    );
    console.log('[TreeTable] 树形数据构建完成:', {
      flatCount: res.items?.length,
      rootCount: treeData.length,
      parentField: listConfig.value.tree.parentField,
      searchParams: queryParams,
      firstRoot: treeData[0],
    });
    return {
      items: treeData,
      total: treeData.length, // 返回根节点数量
    };
  }

  return {
    items: res.items,
    total: res.total,
  };
}

// 构建树形数据（非懒加载模式）
function buildTreeData(flatData: any[], parentField: string): any[] {
  if (!flatData || flatData.length === 0) return [];

  const map = new Map<string, any>();
  const roots: any[] = [];

  // 第一遍：创建所有节点的映射
  flatData.forEach((item) => {
    map.set(item.id, { ...item, children: [] });
  });

  // 第二遍：构建父子关系
  flatData.forEach((item) => {
    const node = map.get(item.id);
    const parentId = item[parentField];

    if (parentId && map.has(parentId)) {
      // 有父节点，添加到父节点的 children
      const parent = map.get(parentId);
      parent.children.push(node);
    } else {
      // 没有父节点或父节点不存在，作为根节点
      roots.push(node);
    }
  });

  // 清理空的 children 数组（Element Plus 需要）
  const cleanChildren = (nodes: any[]) => {
    nodes.forEach((node) => {
      if (node.children && node.children.length === 0) {
        delete node.children;
      } else if (node.children) {
        cleanChildren(node.children);
      }
    });
  };
  cleanChildren(roots);

  return roots;
}

// 处理排序变更（后端排序）
function handleSortChange(data: {
  column: any;
  order: 'ascending' | 'descending' | null;
  prop: string;
}) {
  // 检查该列是否配置为后端排序
  const colConfig = formMeta.value?.list_config?.columns?.find(
    (c: any) => c.field === data.prop,
  );
  if (colConfig?.sortType === 'backend') {
    currentSort.value = {
      field: data.prop || '',
      order: data.order,
    };
    // 重新加载数据
    gridApi.reload();
  }
}

// 处理过滤变更
function handleFilterChange(filters: Record<string, any[]>) {
  // 更新过滤状态
  currentFilters.value = filters;
  // 重新加载数据
  gridApi.reload();
}

// 过滤 API 函数（供 zq-table 调用）
async function filterApi(params: {
  field: string;
  page: number;
  pageSize: number;
  search?: string;
}) {
  if (!props.formCode) {
    return { items: [], total: 0, hasMore: false };
  }
  return await getFieldValuesApi(props.formCode, params.field, {
    page: params.page,
    pageSize: params.pageSize,
    search: params.search,
  });
}

// 使用 ZqTable
const [Grid, gridApi] = useZqTable({
  gridOptions: {
    columns: [],
    border: true,
    stripe: true,
    size: 'default',
    showSelection: true,
    showIndex: true,
    filterApi, // 传递过滤 API 函数
    proxyConfig: {
      enabled: true,
      autoLoad: false,
      ajax: {
        query: queryData,
      },
    },
    pagerConfig: {
      enabled: true,
      pageSize: 20,
    },
    toolbarConfig: {
      search: true,
      refresh: true,
      zoom: true,
      custom: true,
    },
  },
  formOptions: {
    schema: [],
    showCollapseButton: true,
    submitOnChange: false, // 初始化时禁用，避免重复请求
  },
});

// 树形表格懒加载函数
async function loadTreeChildren(
  row: any,
  _treeNode: any,
  resolve: (data: any[]) => void,
) {
  if (!props.formCode || !listConfig.value.tree.enabled) {
    resolve([]);
    return;
  }

  try {
    const children = await getTreeChildrenApi(props.formCode, {
      parentId: row.id,
      parentField: listConfig.value.tree.parentField,
    });
    resolve(children || []);
  } catch (error) {
    console.error('加载子节点失败:', error);
    resolve([]);
  }
}

// 处理选择变更
function handleSelectionChange(rows: any[]) {
  selectedRows.value = rows;
}

// 处理单元格点击（用于选择模式）
function handleCellClick({ row }: { row: any }) {
  if (props.selectionMode) {
    emit('row-select', row);
  }
}

// 选择模式下的行样式（高亮已选中的行）
function getSelectionRowClassName({ row }: { row: any }) {
  if (!props.selectionMode || !props.selectedValues) return '';
  const valueField = props.selectionValueField || 'id';
  const value = String(row[valueField]);
  return props.selectedValues.has(value)
    ? 'selection-row-selected'
    : 'selection-row-hover';
}

// CRUD 操作
function handleAdd() {
  if (props.onAdd) {
    props.onAdd();
    return;
  }
  dialogMode.value = 'add';
  editingId.value = null;
  showFormDialog.value = true;
}

function handleView(row: any) {
  if (props.onView) {
    props.onView(row);
    return;
  }
  dialogMode.value = 'view';
  editingId.value = row.id;
  showFormDialog.value = true;
}

function handleEdit(row: any) {
  if (props.onEdit) {
    props.onEdit(row);
    return;
  }
  dialogMode.value = 'edit';
  editingId.value = row.id;
  showFormDialog.value = true;
}

// 处理表单选择器字段点击，弹窗显示关联表单详情
async function handleFormSelectorClick(formCode: string, recordId: string) {
  if (!formCode || !recordId) return;

  showRelatedFormDialog.value = true;
  relatedFormLoading.value = true;

  try {
    // 加载关联表单元数据
    relatedFormMeta.value = await getFormByCodeApi(formCode);

    // 加载字段权限
    try {
      relatedFormFieldPermissions.value =
        await getFieldPermissionsApi(formCode);
    } catch {
      relatedFormFieldPermissions.value = {};
    }

    // 加载表单数据
    const detail = await getFormDataDetailApi(formCode, recordId);
    let mainData = detail.main;
    if (!mainData && !detail.main && typeof detail === 'object') {
      const { sub_tables, ...rest } = detail;
      mainData = rest;
    }

    // 清空并填充数据
    Object.keys(relatedFormData).forEach((key) => delete relatedFormData[key]);
    Object.assign(relatedFormData, mainData || {});

    // 处理子表数据
    const subTables = detail.sub_tables;
    if (subTables) {
      Object.keys(subTables).forEach((key) => {
        if (Array.isArray(subTables[key])) {
          relatedFormData[key] = subTables[key].map((row: any) => ({
            ...row,
            _id: row.id || `${Date.now()}_${Math.random()}`,
            _isEditing: false,
          }));
        }
      });
    }
  } catch (error: any) {
    console.error('加载关联表单数据失败:', error);
    ElMessage.error(error?.message || '加载关联表单数据失败');
    showRelatedFormDialog.value = false;
  } finally {
    relatedFormLoading.value = false;
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确定要删除这条数据吗？', '删除确认', {
      type: 'warning',
    });
    await deleteFormDataApi(props.formCode, row.id);
    ElMessage.success('删除成功');
    if (listConfig.value.listType === 'card') {
      loadCardData();
    } else {
      gridApi.reload();
    }
  } catch {
    // 用户取消
  }
}

const batchDeleting = ref(false);

async function handleBatchDelete() {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要删除的数据');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 条数据吗？`,
      '批量删除确认',
      { type: 'warning' },
    );
    batchDeleting.value = true;
    const ids = selectedRows.value.map((row) => row.id);
    await batchDeleteFormDataApi(props.formCode, ids);
    ElMessage.success('删除成功');
    selectedRows.value = [];
    gridApi.reload();
  } catch {
    // 用户取消
  } finally {
    batchDeleting.value = false;
  }
}

function handleFormSaved() {
  if (listConfig.value.listType === 'card') {
    loadCardData();
  } else {
    gridApi.reload();
  }
}

// 导出
function handleExport() {
  showExportDialog.value = true;
}

async function handleConfirmExport(config: {
  includeSubTables: boolean;
  selectedFields: string[];
}) {
  // 获取当前表单查询条件
  let formValues: Record<string, any> = {};
  if (listConfig.value.listType === 'card') {
    formValues = cardQueryForm.value || {};
  } else {
    try {
      formValues =
        gridApi.formApi && typeof gridApi.formApi.getValues === 'function'
          ? await gridApi.formApi.getValues()
          : {};
    } catch {
      formValues = {};
    }
  }

  const filterParams = buildFilterQueryParams(formValues);

  // 设置进度对话框配置并打开
  exportProgressConfig.value = {
    selectedFields: config.selectedFields,
    includeSubTables: config.includeSubTables,
    queryParams: filterParams,
  };
  showExportProgressDialog.value = true;
}

// 下载导入模板
async function handleDownloadTemplate() {
  try {
    const blob = await getImportTemplateApi(props.formCode);
    downloadBlob(blob, `${props.formCode}_template.xlsx`);
    ElMessage.success('模板下载成功');
  } catch (error) {
    ElMessage.error('模板下载失败');
    console.error('模板下载失败:', error);
  }
}

// 导入数据
const importDialogRef = ref<InstanceType<typeof ImportDialog> | null>(null);

const importFormFields = computed(() => {
  const columns = formMeta.value?.list_config?.columns || [];
  return columns
    .filter((col: any) => col.field && col.label && col.field !== 'id')
    .map((col: any) => ({ field: col.field, label: col.label }));
});

function handleImport() {
  importDialogRef.value?.open();
}

function handleImportSuccess() {
  gridApi.reload();
}

// Agent 对话相关
const agentChatVisible = ref(false);
const currentAgentId = ref<string>('');
const currentAgentCode = ref<string>('');
const agentInitialMessage = ref<string>('');
const agentDialogTitle = ref<string>('');
const agentDialogWidth = ref<string>('80%');
const agentDialogFullscreen = ref(false);

function handleAgentChat(button: any, row?: any) {
  const config = button.actionConfig || {};

  // 设置 Agent ID 或 Code
  currentAgentId.value = config.agentId || '';
  currentAgentCode.value = config.agentCode || '';

  // 准备初始消息
  if (config.initialMessage) {
    const message = replaceVariables(config.initialMessage, row || {});
    agentInitialMessage.value = message;
  } else {
    agentInitialMessage.value = '';
  }

  // 设置 dialog 属性
  agentDialogTitle.value = config.dialogTitle
    ? replaceVariables(config.dialogTitle, row || {})
    : $t('form-manager.listDesign.actionAgent');
  agentDialogWidth.value = config.dialogWidth || '80%';
  agentDialogFullscreen.value = config.dialogFullscreen || false;

  // 打开对话窗口
  agentChatVisible.value = true;
}

function handleAgentChatClose() {
  agentChatVisible.value = false;
  currentAgentId.value = '';
  currentAgentCode.value = '';
  agentInitialMessage.value = '';
  agentDialogTitle.value = '';
  agentDialogWidth.value = '80%';
  agentDialogFullscreen.value = false;
}

// 页面查看相关
const pageViewVisible = ref(false);
const currentPageCode = ref<string>('');
const currentPageTitle = ref<string>('');
const currentPageWidth = ref<string>('80%');
const currentPageFullscreen = ref(false);
const currentPageRowData = ref<Record<string, any>>({});

function handlePageView(button: any, row?: any) {
  const config = button.actionConfig || {};

  if (!config.pageCode) {
    ElMessage.warning($t('form-manager.listDesign.pageCodeRequired'));
    return;
  }

  currentPageCode.value = config.pageCode;
  currentPageTitle.value = config.dialogTitle
    ? replaceVariables(config.dialogTitle, row || {})
    : '';
  currentPageWidth.value = config.dialogWidth || '80%';
  currentPageFullscreen.value = config.dialogFullscreen || false;
  currentPageRowData.value = row || {};

  pageViewVisible.value = true;
}

// 发起流程相关
const boundWorkflows = ref<WorkflowListItem[]>([]);

// 加载绑定的工作流
async function loadBoundWorkflows() {
  if (!props.formCode || formMeta.value?.form_type !== 'workflow') return;
  try {
    boundWorkflows.value = await getWorkflowsByFormApi(props.formCode);
  } catch (error) {
    console.error('加载绑定工作流失败:', error);
    boundWorkflows.value = [];
  }
}

// 自定义按钮处理
function evaluateCondition(condition: string, row: any): boolean {
  if (!condition) return true;
  try {
    const func = new Function('row', `return ${condition}`);
    return func(row);
  } catch (error) {
    console.error('条件表达式执行错误:', error);
    return false;
  }
}

function replaceVariables(template: string, row: any): string {
  if (!template) return '';
  return template.replaceAll(/\{(\w+)\}/g, (match, key) => {
    return row[key] === undefined ? match : String(row[key]);
  });
}

async function handleCustomButtonClick(button: any, row?: any) {
  // 检查显示条件
  if (
    row &&
    button.showCondition &&
    !evaluateCondition(button.showCondition, row)
  ) {
    return;
  }

  switch (button.actionType) {
    case 'agent': {
      // 打开 Agent 对话窗口
      handleAgentChat(button, row);
      break;
    }
    case 'api': {
      try {
        // 显示确认对话框
        if (button.actionConfig.confirmMessage) {
          const confirmTitle = button.actionConfig.confirmTitle || '确认操作';
          await ElMessageBox.confirm(
            replaceVariables(button.actionConfig.confirmMessage, row || {}),
            replaceVariables(confirmTitle, row || {}),
            { type: 'warning' },
          );
        }

        const apiUrl = replaceVariables(
          button.actionConfig.apiUrl || '',
          row || {},
        );
        const method = button.actionConfig.apiMethod || 'POST';

        switch (method) {
          case 'DELETE': {
            await requestClient.delete(apiUrl);

            break;
          }
          case 'GET': {
            await requestClient.get(apiUrl);

            break;
          }
          case 'POST': {
            await requestClient.post(apiUrl, row);

            break;
          }
          case 'PUT': {
            await requestClient.put(apiUrl, row);

            break;
          }
          // No default
        }

        // 显示成功消息
        const successMsg = button.actionConfig.successMessage || '操作成功';
        ElMessage.success(replaceVariables(successMsg, row || {}));

        // 根据配置决定是否刷新列表
        if (button.actionConfig.reloadAfterSuccess !== false) {
          gridApi.reload();
        }
      } catch (error: any) {
        if (error !== 'cancel') {
          const errorMsg =
            button.actionConfig.errorMessage || error?.message || '操作失败';
          ElMessage.error(replaceVariables(errorMsg, row || {}));
        }
      }
      break;
    }
    case 'event': {
      // 触发自定义事件，可以在外部监听
      const eventName = button.actionConfig.eventName;
      if (eventName) {
        window.dispatchEvent(
          new CustomEvent(eventName, { detail: { button, row } }),
        );
      }
      break;
    }
    case 'generate_document': {
      // 打开生成单据弹窗
      if (row?.id) {
        currentGenerateDocumentRow.value = row;
        showGenerateDocumentDialog.value = true;
      }
      break;
    }
    case 'link': {
      const url = replaceVariables(button.actionConfig.url || '', row || {});
      if (url) {
        if (button.actionConfig.openInNewTab) {
          window.open(url, '_blank');
        } else {
          window.location.href = url;
        }
      }
      break;
    }
    case 'page': {
      // 打开页面查看弹窗
      handlePageView(button, row);
      break;
    }
  }
}

// 过滤自定义按钮（根据位置和权限）
const toolbarCustomButtons = computed(() => {
  return listConfig.value.customButtons.filter(
    (btn: any) => btn.position === 'toolbar',
  );
});

const toolsCustomButtons = computed(() => {
  return listConfig.value.customButtons.filter(
    (btn: any) => btn.position === 'tools',
  );
});

const rowCustomButtons = computed(() => {
  return listConfig.value.customButtons.filter(
    (btn: any) => btn.position === 'row',
  );
});

// 获取行操作按钮的可见列表（根据条件过滤）
function getVisibleRowButtons(row: any) {
  return rowCustomButtons.value.filter((btn: any) => {
    if (!btn.showCondition) return true;
    return evaluateCondition(btn.showCondition, row);
  });
}

// 计算所有可见的行操作项（包括内置按钮、子表按钮、自定义按钮）
function getRowActionItems(row: any) {
  const items: Array<{
    data: any;
    key: string;
    type: 'builtin' | 'custom' | 'subtable';
  }> = [];

  // 内置按钮
  if (effectiveButtons.value.showView) {
    items.push({ type: 'builtin', key: 'view', data: null });
  }
  if (effectiveButtons.value.showEdit) {
    items.push({ type: 'builtin', key: 'edit', data: null });
  }
  if (effectiveButtons.value.showDelete) {
    items.push({ type: 'builtin', key: 'delete', data: null });
  }

  // 子表按钮
  for (const subBtn of listConfig.value.subTableButtons || []) {
    items.push({ type: 'subtable', key: subBtn.id, data: subBtn });
  }

  // 自定义按钮（已过滤可见性）
  const visibleCustomButtons = getVisibleRowButtons(row);
  for (const btn of visibleCustomButtons) {
    items.push({ type: 'custom', key: btn.id, data: btn });
  }

  return items;
}

// 获取直接显示的按钮（前2个）
function getDirectRowActions(row: any) {
  return getRowActionItems(row).slice(0, 2);
}

// 获取更多菜单中的按钮（第3个及之后）
function getMoreRowActions(row: any) {
  return getRowActionItems(row).slice(2);
}

// 是否显示更多菜单
function hasMoreRowActions(row: any) {
  return getRowActionItems(row).length > 2;
}

// 从列配置中提取统计列配置
const summaryColumns = computed(() => {
  if (!formMeta.value?.list_config?.columns) return [];

  return formMeta.value.list_config.columns
    .filter((col: any) => col.summaryEnabled)
    .map((col: any) => ({
      field: col.field,
      enabled: col.summaryEnabled,
    }));
});

// 监听 formCode 变化
watch(
  () => props.formCode,
  async (newCode) => {
    if (newCode) {
      await loadFieldPermissions();
      await loadFormMeta();
      await loadQueryFieldOptions();
      await loadUserPermissions();
      await loadBoundWorkflows();
      gridApi.setState({
        gridOptions: {
          columns: tableColumns.value,
          // 选择模式下隐藏复选框列和序号列（由 tableColumns 手动添加）
          showSelection: props.selectionMode
            ? false
            : effectiveButtons.value.showBatchDelete,
          showIndex: props.selectionMode
            ? false
            : listConfig.value.table.showIndex,
          stripe: props.selectionMode ? false : listConfig.value.table.stripe,
          border: listConfig.value.table.border,
          showSummary: listConfig.value.table.showSummary,
          summaryType: listConfig.value.table.summaryType,
          summaryPrecision: listConfig.value.table.summaryPrecision,
          summaryColumns: summaryColumns.value,
          // 选择模式下添加行样式
          rowClassName: props.selectionMode
            ? getSelectionRowClassName
            : undefined,
          highlightCurrentRow: props.selectionMode,
          // 树形表格配置
          ...(listConfig.value.tree.enabled
            ? {
                rowKey: 'id',
                treeProps: {
                  children: 'children',
                  hasChildren: 'has_children',
                },
                lazy: listConfig.value.tree.lazy,
                load: listConfig.value.tree.lazy ? loadTreeChildren : undefined,
                defaultExpandAll: listConfig.value.tree.defaultExpandAll,
                indent: listConfig.value.tree.indent,
              }
            : {}),
          // 树形表格模式下禁用分页（数据已是完整树结构）
          pagerConfig: {
            enabled: listConfig.value.tree.enabled
              ? false
              : listConfig.value.table.showPagination,
            pageSize: listConfig.value.table.pageSize,
          },
          toolbarConfig: {
            search: props.showToolbar,
            refresh: props.showToolbar,
            zoom: props.showToolbar,
            custom: props.showToolbar,
          },
        },
        formOptions: {
          schema: formSchema.value,
          submitOnChange: false, // 初始化时禁用，避免重复请求
          wrapperClass: 'grid-cols-12',
        },
      });

      // 表格模式：手动触发数据加载
      if (listConfig.value.listType === 'table') {
        console.log('[FormDataList] tableColumns:', tableColumns.value);
        console.log(
          '[FormDataList] list_config.columns:',
          formMeta.value?.list_config?.columns,
        );
        await gridApi.reload();
        loading.value = false;
        gridApi.setState({
          formOptions: {
            submitOnChange: true,
          },
        });
      }
    }

    // 卡片模式：初始化分页大小并加载数据
    if (listConfig.value.listType === 'card') {
      cardPagination.value.pageSize = listConfig.value.card.pageSize;
      loadCardData();
    }
  },
  { immediate: true },
);

// onMounted 不再需要，watch immediate: true 已经处理了初始化逻辑

// 暴露方法供外部调用
defineExpose({
  reload: () => {
    if (listConfig.value.listType === 'card') {
      loadCardData();
    } else {
      gridApi.reload();
    }
  },
  getFormMeta: () => formMeta.value,
});
</script>

<template>
  <div class="form-data-list h-full">
    <!-- 子表 Layout 条件渲染模式：表单视图 -->
    <Page
      v-if="subTableLayoutMode !== 'none' && subTableLayoutMode !== 'list'"
      :title="subTableLayoutPageTitle"
      auto-content-height
      :height-offset="35"
    >
      <template #title>
        <div class="header-back flex items-center gap-2">
          <ElButton :icon="ArrowLeft" text @click="handleSubTableLayoutBack">
            {{ $t('common.back') }}
          </ElButton>
          <h1 class="header-title text-lg font-medium">
            {{ subTableLayoutPageTitle }}
          </h1>
        </div>
      </template>
      <template #extra>
        <div class="flex items-center gap-2">
          <ElButton
            v-if="!subTableLayoutIsReadonly"
            type="primary"
            :icon="Save"
            :loading="subTableLayoutSaving"
            @click="handleSubTableLayoutSave"
          >
            {{ $t('common.save') }}
          </ElButton>
        </div>
      </template>

      <div v-loading="subTableLayoutLoading" class="h-full">
        <div
          v-if="!subTableLayoutLoading && subTableFormMeta"
          class="form-container"
          :style="{
            width: subTableFormConf.formWidth || '100%',
            maxWidth: subTableFormConf.formMaxWidth || '100%',
            padding: `${subTableFormConf.formPaddingTop ?? subTableFormConf.formPadding ?? 24}px ${subTableFormConf.formPaddingRight ?? subTableFormConf.formPadding ?? 24}px ${subTableFormConf.formPaddingBottom ?? subTableFormConf.formPadding ?? 24}px ${subTableFormConf.formPaddingLeft ?? subTableFormConf.formPadding ?? 24}px`,
            margin: `${subTableFormConf.formMarginTop ?? subTableFormConf.formMargin ?? 0}px ${subTableFormConf.formMarginRight ?? subTableFormConf.formMargin ?? 0}px ${subTableFormConf.formMarginBottom ?? subTableFormConf.formMargin ?? 0}px ${subTableFormConf.formMarginLeft ?? subTableFormConf.formMargin ?? 0}px`,
            backgroundColor:
              subTableFormConf.formBackground || 'var(--el-bg-color)',
            border: subTableFormConf.formBorder
              ? '1px solid var(--el-border-color)'
              : 'none',
            borderRadius: subTableFormConf.formBorder
              ? `${subTableFormConf.formBorderRadius || 8}px`
              : '8px',
            boxShadow: subTableFormConf.formShadow
              ? '0 2px 12px 0 rgba(0, 0, 0, 0.1)'
              : 'none',
          }"
        >
          <ElForm
            ref="subTableLayoutFormRef"
            :model="subTableLayoutFormData"
            :label-width="`${subTableFormConf.labelWidth || 100}px`"
            :label-position="subTableFormConf.labelPosition || 'right'"
            :size="subTableFormConf.size || 'default'"
            :disabled="subTableLayoutIsReadonly"
            :style="{
              '--el-form-item-margin-bottom': `${subTableFormConf.itemSpacing || 18}px`,
            }"
          >
            <PreviewItem
              v-for="item in subTableFormConf.items"
              :key="item.id"
              :item="item"
              :model-value="subTableLayoutFormData"
              :is-edit="subTableLayoutMode !== 'add'"
              :field-permissions="subTableLayoutFieldPermissions"
              :form-code="currentSubTableButton?.subFormCode"
              :edit-id="subTableLayoutEditId ?? undefined"
            />
          </ElForm>
        </div>
      </div>
    </Page>

    <!-- 子表 Layout 条件渲染模式：列表视图 -->
    <Page
      v-else-if="subTableLayoutMode === 'list'"
      :title="subTableLayoutPageTitle"
      auto-content-height
      :height-offset="35"
    >
      <template #title>
        <div class="header-back flex items-center gap-2">
          <ElButton :icon="ArrowLeft" text @click="handleSubTableLayoutClose">
            {{ $t('common.back') }}
          </ElButton>
          <h1 class="header-title text-lg font-medium">
            {{ subTableLayoutPageTitle }}
          </h1>
        </div>
      </template>

      <div v-loading="subTableLayoutLoading" class="h-full">
        <FormDataList
          v-if="subTableFormMeta"
          ref="subTableFormDataListRef"
          :form-code="currentSubTableButton?.subFormCode"
          :initial-filters="subTableInitialFilters"
          :default-form-data="subTableDefaultFormData"
          :on-add="handleSubTableLayoutAdd"
          :on-edit="handleSubTableLayoutEdit"
          :on-view="handleSubTableLayoutView"
          :show-margin="false"
        />
      </div>
    </Page>

    <!-- 主表视图 -->
    <template v-else>
      <!-- <Page
        auto-content-height
        v-if="!formMeta"
        v-loading="loading"
        :show-margin="showMargin"
        :height-offset="selectionMode ? heightOffset : 26"
      /> -->
      <Page
        auto-content-height
        v-if="formMeta && listConfig.listType === 'table'"
        class="pb-3"
        :height-offset="selectionMode ? heightOffset : 26"
        :show-margin="showMargin"
      >
        <!-- Table 模式 -->
        <Grid
          @selection-change="handleSelectionChange"
          @sort-change="handleSortChange"
          @filter-change="handleFilterChange"
          @cell-click="handleCellClick"
        >
          <template #toolbar-actions>
            <ElButton
              v-if="effectiveButtons.showAdd && !selectionMode"
              type="primary"
              :icon="Plus"
              @click="handleAdd"
            >
              {{ $t('common.add') }}
            </ElButton>
            <ElButton
              v-if="effectiveButtons.showBatchDelete && !selectionMode"
              :disabled="selectedRows.length === 0"
              :loading="batchDeleting"
              type="danger"
              plain
              :icon="Trash2"
              @click="handleBatchDelete"
            >
              {{
                selectedRows.length > 0
                  ? `${$t('common.batchDelete')} (${selectedRows.length})`
                  : $t('common.batchDelete')
              }}
            </ElButton>
            <ElButton
              v-if="effectiveButtons.showExport"
              type="success"
              plain
              :icon="Download"
              @click="handleExport"
            >
              {{ $t('common.export') }}
            </ElButton>
            <ElButton
              v-if="effectiveButtons.showImport"
              type="warning"
              plain
              :icon="Upload"
              @click="handleDownloadTemplate"
            >
              {{ $t('common.downloadTemplate') }}
            </ElButton>
            <ElButton
              v-if="effectiveButtons.showImport"
              type="primary"
              plain
              :icon="Upload"
              @click="handleImport"
            >
              {{ $t('common.import') }}
            </ElButton>

            <!-- 自定义工具栏按钮 -->
            <ElTooltip
              v-for="button in toolbarCustomButtons"
              :key="button.id"
              :content="button.tooltip"
              :disabled="!button.tooltip"
            >
              <ElButton
                :type="button.type"
                :plain="button.plain"
                :round="button.round"
                :circle="button.circle"
                :text="button.text"
                :link="button.link"
                :size="button.size || 'default'"
                :disabled="
                  button.disabled ||
                  (button.disabledCondition &&
                    evaluateCondition(button.disabledCondition, {}))
                "
                :loading="button.loading"
                @click="handleCustomButtonClick(button)"
              >
                <template v-if="button.badge">
                  <ElBadge
                    :value="button.badge"
                    :type="button.badgeType || 'primary'"
                  >
                    <IconifyIcon
                      v-if="button.icon"
                      :icon="button.icon"
                      class="mr-1"
                    />
                    <span v-if="!button.iconOnly">{{ button.name }}</span>
                  </ElBadge>
                </template>
                <template v-else>
                  <IconifyIcon
                    v-if="button.icon"
                    :icon="button.icon"
                    :class="{ 'mr-1': !button.iconOnly }"
                  />
                  <span v-if="!button.iconOnly">{{ button.name }}</span>
                </template>
              </ElButton>
            </ElTooltip>
          </template>

          <template #toolbar-tools>
            <!-- 自定义工具栏右侧按钮 -->
            <ElTooltip
              v-for="button in toolsCustomButtons"
              :key="button.id"
              :content="button.tooltip"
              :disabled="!button.tooltip"
            >
              <ElButton
                :type="button.type"
                :plain="button.plain"
                :round="button.round"
                :circle="button.circle"
                :text="button.text"
                :link="button.link"
                :size="button.size || 'default'"
                :disabled="
                  button.disabled ||
                  (button.disabledCondition &&
                    evaluateCondition(button.disabledCondition, {}))
                "
                :loading="button.loading"
                @click="handleCustomButtonClick(button)"
              >
                <template v-if="button.badge">
                  <ElBadge
                    :value="button.badge"
                    :type="button.badgeType || 'primary'"
                  >
                    <IconifyIcon
                      v-if="button.icon"
                      :icon="button.icon"
                      class="mr-1"
                    />
                    <span v-if="!button.iconOnly">{{ button.name }}</span>
                  </ElBadge>
                </template>
                <template v-else>
                  <IconifyIcon
                    v-if="button.icon"
                    :icon="button.icon"
                    :class="{ 'mr-1': !button.iconOnly }"
                  />
                  <span v-if="!button.iconOnly">{{ button.name }}</span>
                </template>
              </ElButton>
            </ElTooltip>
          </template>

          <template #cell-actions="{ row }">
            <div class="row-actions">
              <!-- 直接显示的按钮（前2个） -->
              <template
                v-for="action in getDirectRowActions(row)"
                :key="action.key"
              >
                <!-- 内置按钮 -->
                <ElButton
                  v-if="action.type === 'builtin' && action.key === 'view'"
                  link
                  type="primary"
                  :icon="Eye"
                  @click="handleView(row)"
                >
                  {{ $t('common.view') }}
                </ElButton>
                <ElButton
                  v-else-if="action.type === 'builtin' && action.key === 'edit'"
                  link
                  type="primary"
                  :icon="Edit"
                  @click="handleEdit(row)"
                >
                  {{ $t('common.edit') }}
                </ElButton>
                <ElButton
                  v-else-if="
                    action.type === 'builtin' && action.key === 'delete'
                  "
                  link
                  type="danger"
                  :icon="Trash2"
                  @click="handleDelete(row)"
                >
                  {{ $t('common.delete') }}
                </ElButton>
                <!-- 子表按钮 -->
                <ElButton
                  v-else-if="action.type === 'subtable'"
                  link
                  :type="action.data.buttonType || 'primary'"
                  @click="handleOpenSubTable(row, action.data)"
                >
                  <IconifyIcon
                    v-if="action.data.buttonIcon"
                    :icon="action.data.buttonIcon"
                    class="mr-1"
                  />
                  {{ action.data.buttonText }}
                </ElButton>
                <!-- 自定义按钮 -->
                <ElTooltip
                  v-else-if="action.type === 'custom'"
                  :content="replaceVariables(action.data.tooltip || '', row)"
                  :disabled="!action.data.tooltip"
                >
                  <ElButton
                    :type="action.data.type"
                    :plain="action.data.plain"
                    :round="action.data.round"
                    :circle="action.data.circle"
                    :text="action.data.text"
                    :link="action.data.link !== false"
                    :size="action.data.size || 'default'"
                    :disabled="
                      action.data.disabled ||
                      (action.data.disabledCondition &&
                        evaluateCondition(action.data.disabledCondition, row))
                    "
                    :loading="action.data.loading"
                    @click="handleCustomButtonClick(action.data, row)"
                  >
                    <template v-if="action.data.badge">
                      <ElBadge
                        :value="
                          replaceVariables(String(action.data.badge), row)
                        "
                        :type="action.data.badgeType || 'primary'"
                      >
                        <IconifyIcon
                          v-if="action.data.icon"
                          :icon="action.data.icon"
                          class="mr-1"
                        />
                        <span v-if="!action.data.iconOnly">{{
                          action.data.name
                        }}</span>
                      </ElBadge>
                    </template>
                    <template v-else>
                      <IconifyIcon
                        v-if="action.data.icon"
                        :icon="action.data.icon"
                        :class="{ 'mr-1': !action.data.iconOnly }"
                      />
                      <span v-if="!action.data.iconOnly">{{
                        action.data.name
                      }}</span>
                    </template>
                  </ElButton>
                </ElTooltip>
              </template>

              <!-- 更多菜单（第3个及之后的按钮） -->
              <ElDropdown v-if="hasMoreRowActions(row)" trigger="click">
                <ElButton link type="primary" :icon="MoreVertical">
                  {{ $t('common.more') }}
                </ElButton>
                <template #dropdown>
                  <ElDropdownMenu>
                    <template
                      v-for="action in getMoreRowActions(row)"
                      :key="action.key"
                    >
                      <!-- 内置按钮 -->
                      <ElDropdownItem
                        v-if="
                          action.type === 'builtin' && action.key === 'view'
                        "
                        @click="handleView(row)"
                      >
                        <Eye class="mr-2 h-4 w-4" />
                        {{ $t('common.view') }}
                      </ElDropdownItem>
                      <ElDropdownItem
                        v-else-if="
                          action.type === 'builtin' && action.key === 'edit'
                        "
                        @click="handleEdit(row)"
                      >
                        <Edit class="mr-2 h-4 w-4" />
                        {{ $t('common.edit') }}
                      </ElDropdownItem>
                      <ElDropdownItem
                        v-else-if="
                          action.type === 'builtin' && action.key === 'delete'
                        "
                        @click="handleDelete(row)"
                      >
                        <Trash2 class="mr-2 h-4 w-4 text-red-500" />
                        <span class="text-red-500">{{
                          $t('common.delete')
                        }}</span>
                      </ElDropdownItem>
                      <!-- 子表按钮 -->
                      <ElDropdownItem
                        v-else-if="action.type === 'subtable'"
                        @click="handleOpenSubTable(row, action.data)"
                      >
                        <IconifyIcon
                          v-if="action.data.buttonIcon"
                          :icon="action.data.buttonIcon"
                          class="mr-2 h-4 w-4"
                        />
                        {{ action.data.buttonText }}
                      </ElDropdownItem>
                      <!-- 自定义按钮 -->
                      <ElDropdownItem
                        v-else-if="action.type === 'custom'"
                        :disabled="
                          action.data.disabled ||
                          (action.data.disabledCondition &&
                            evaluateCondition(
                              action.data.disabledCondition,
                              row,
                            ))
                        "
                        @click="handleCustomButtonClick(action.data, row)"
                      >
                        <IconifyIcon
                          v-if="action.data.icon"
                          :icon="action.data.icon"
                          class="mr-2 h-4 w-4"
                        />
                        {{ action.data.name }}
                      </ElDropdownItem>
                    </template>
                  </ElDropdownMenu>
                </template>
              </ElDropdown>
            </div>
          </template>
        </Grid>
      </Page>

      <!-- Card 模式 -->
      <Page
        v-if="formMeta && listConfig.listType === 'card'"
        :height-offset="selectionMode ? heightOffset : 24"
        auto-content-height
        v-loading="loading"
        :show-margin="showMargin"
      >
        <template #title>
          <div class="flex items-center justify-between">
            <!-- 查询字段 -->
            <div class="flex items-center gap-3">
              <template v-for="field in cardQueryFields" :key="field.field">
                <!-- 输入框 -->
                <ElInput
                  v-if="!field.component || field.component === 'input'"
                  v-model="cardQueryForm[field.field]"
                  :placeholder="field.label"
                  clearable
                  class="w-40"
                  @keyup.enter="handleCardSearch"
                  @clear="handleCardSearch"
                />
                <!-- 选择器 -->
                <ElSelect
                  v-else-if="field.component === 'select'"
                  v-model="cardQueryForm[field.field]"
                  :placeholder="field.label"
                  clearable
                  :multiple="field.multiple"
                  collapse-tags
                  collapse-tags-tooltip
                  class="min-w-56"
                  @change="handleCardSearch"
                  @clear="handleCardSearch"
                >
                  <ElOption
                    v-for="opt in field.options"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </ElSelect>
                <!-- 日期选择器 -->
                <ElDatePicker
                  v-else-if="
                    field.component === 'date' ||
                    field.component === 'date-picker'
                  "
                  v-model="cardQueryForm[field.field]"
                  :type="
                    field.type === 'range'
                      ? field.showTime
                        ? 'datetimerange'
                        : 'daterange'
                      : field.showTime
                        ? 'datetime'
                        : 'date'
                  "
                  :placeholder="field.label"
                  :start-placeholder="$t('common.startDate')"
                  :end-placeholder="$t('common.endDate')"
                  :format="
                    field.showTime ? 'YYYY-MM-DD HH:mm:ss' : 'YYYY-MM-DD'
                  "
                  :value-format="
                    field.showTime ? 'YYYY-MM-DD HH:mm:ss' : 'YYYY-MM-DD'
                  "
                  clearable
                  class="min-w-56"
                  @change="handleCardSearch"
                  @clear="handleCardSearch"
                />
                <!-- 用户选择器 -->
                <UserSelector
                  v-else-if="
                    field.component === 'user-selector' ||
                    field.component === 'user-select'
                  "
                  v-model="cardQueryForm[field.field]"
                  :placeholder="field.label"
                  multiple
                  clearable
                  collapse-tags
                  collapse-tags-tooltip
                  class="min-w-56"
                  @change="handleCardSearch"
                />
                <!-- 部门选择器 -->
                <DeptSelector
                  v-else-if="
                    field.component === 'dept-selector' ||
                    field.component === 'dept-select' ||
                    field.component === 'department-selector'
                  "
                  v-model="cardQueryForm[field.field]"
                  :placeholder="field.label"
                  multiple
                  clearable
                  collapse-tags
                  collapse-tags-tooltip
                  class="w-48"
                  @change="handleCardSearch"
                />
                <!-- 岗位选择器 -->
                <PostSelector
                  v-else-if="
                    field.component === 'post-selector' ||
                    field.component === 'post-select' ||
                    field.component === 'position-selector'
                  "
                  v-model="cardQueryForm[field.field]"
                  :placeholder="field.label"
                  multiple
                  clearable
                  collapse-tags
                  collapse-tags-tooltip
                  class="w-48"
                  @change="handleCardSearch"
                />
                <!-- 表单选择器 -->
                <FormSelector
                  v-else-if="
                    field.component === 'form-selector' ||
                    field.originalComponent === 'form-selector'
                  "
                  v-model="cardQueryForm[field.field]"
                  :form-code="field.formCode"
                  :value-field="field.valueField || 'id'"
                  :label-field="field.labelField || 'name'"
                  :placeholder="field.label"
                  multiple
                  clearable
                  class="min-w-56"
                  @change="handleCardSearch"
                />
                <!-- 表格选择器 -->
                <TableSelector
                  v-else-if="
                    field.component === 'table-selector' ||
                    field.originalComponent === 'table-selector'
                  "
                  v-model="cardQueryForm[field.field]"
                  :data-source-type="field.dataSourceType || 'static'"
                  :form-code="field.formCode"
                  :dict-code="field.dictCode"
                  :data-source-code="field.dataSourceCode"
                  :value-field="field.valueField || 'id'"
                  :label-field="field.labelField || 'name'"
                  :columns="field.columns"
                  :search-fields="field.searchFields"
                  :placeholder="field.label"
                  multiple
                  clearable
                  class="min-w-56"
                  @change="handleCardSearch"
                />
                <!-- 其他组件默认使用输入框 -->
                <ElInput
                  v-else
                  v-model="cardQueryForm[field.field]"
                  :placeholder="field.label"
                  clearable
                  class="w-40"
                  @keyup.enter="handleCardSearch"
                  @clear="handleCardSearch"
                />
              </template>
              <ElButton type="primary" @click="handleCardSearch">
                {{ $t('common.search') }}
              </ElButton>
              <ElButton @click="handleCardReset">
                {{ $t('common.reset') }}
              </ElButton>
            </div>
            <!-- 操作按钮（选择模式下隐藏） -->
            <div v-if="!selectionMode" class="flex items-center gap-2">
              <ElButton
                v-if="effectiveButtons.showAdd"
                type="primary"
                :icon="Plus"
                @click="handleAdd"
              >
                {{ $t('common.add') }}
              </ElButton>
              <ElButton
                v-if="effectiveButtons.showExport"
                type="success"
                plain
                :icon="Download"
                @click="handleExport"
              >
                {{ $t('common.export') }}
              </ElButton>
            </div>
          </div>
        </template>

        <!-- 卡片网格 -->
        <div v-if="cardDataList.length > 0" :style="cardGridStyle">
          <ElCard
            v-for="item in cardDataList"
            :key="item.id"
            class="card-item h-full cursor-pointer transition-shadow hover:shadow-lg"
            :class="{
              'card-item-selected':
                selectionMode &&
                selectedValues?.has(String(item[selectionValueField || 'id'])),
            }"
            :shadow="listConfig.card.shadow"
            style="border: none"
            @click="handleCardClick(item)"
          >
            <template #header>
              <div class="flex items-start gap-3">
                <!-- 图标/头像 -->
                <template v-if="listConfig.cardFields.icon">
                  <!-- 用户头像（使用 UserAvatar 组件） -->
                  <UserAvatar
                    v-if="
                      mergedIconConfig?.showAsAvatar &&
                      mergedIconConfig?.isUserSelector
                    "
                    :user-id="item[listConfig.cardFields.icon.field]"
                    :size="40"
                    :font-size="16"
                    :shadow="false"
                    :show-popover="true"
                    auto-load
                    class="flex-shrink-0"
                  />
                  <!-- 普通头像 -->
                  <ElAvatar
                    v-else-if="mergedIconConfig?.showAsAvatar"
                    :size="40"
                    :src="getCardAvatarUrl(item, listConfig.cardFields.icon)"
                    class="flex-shrink-0"
                  >
                    {{
                      String(
                        getCardFieldValue(item, listConfig.cardFields.icon) ||
                          '-',
                      ).charAt(0)
                    }}
                  </ElAvatar>
                  <!-- 显示文字 -->
                  <div
                    v-else
                    class="bg-primary/10 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg"
                  >
                    <span class="text-primary text-sm font-medium">
                      {{
                        getCardFieldValue(item, listConfig.cardFields.icon) ||
                        '-'
                      }}
                    </span>
                  </div>
                </template>
                <!-- 标题、副标题、操作按钮 -->
                <div class="min-w-0 flex-1">
                  <!-- 第一行：标题 + 操作按钮 -->
                  <div class="flex items-center justify-between">
                    <div class="min-w-0 flex-1 truncate font-medium">
                      <span
                        v-if="
                          listConfig.cardFields.title &&
                          isCardFieldFormSelector(
                            listConfig.cardFields.title,
                          ) &&
                          getCardFieldValue(item, listConfig.cardFields.title)
                        "
                        class="text-primary inline-flex cursor-pointer items-center gap-1"
                        @click="
                          handleCardFormSelectorClick(
                            $event,
                            item,
                            listConfig.cardFields.title,
                          )
                        "
                      >
                        <Link class="h-3 w-3 flex-shrink-0" />
                        {{
                          getCardFieldValue(item, listConfig.cardFields.title)
                        }}
                      </span>
                      <template v-else>
                        {{
                          listConfig.cardFields.title
                            ? getCardFieldValue(
                                item,
                                listConfig.cardFields.title,
                              )
                            : item.id
                        }}
                      </template>
                    </div>
                    <!-- 选择模式下显示 checkbox/radio -->
                    <div
                      v-if="selectionMode"
                      class="ml-2 flex-shrink-0"
                      @click.stop="emit('row-select', item)"
                    >
                      <ElCheckbox
                        v-if="selectionMultiple"
                        :model-value="
                          selectedValues?.has(
                            String(item[selectionValueField || 'id']),
                          )
                        "
                      />
                      <ElRadio
                        v-else
                        :model-value="
                          selectedValues?.has(
                            String(item[selectionValueField || 'id']),
                          )
                        "
                        :value="true"
                      />
                    </div>
                    <!-- 操作按钮（选择模式下隐藏） -->
                    <div
                      v-else
                      @click.stop
                      class="ml-2 flex flex-shrink-0 items-center"
                    >
                      <ElTooltip
                        v-if="effectiveButtons.showEdit"
                        :content="$t('common.edit')"
                        placement="top"
                      >
                        <ElButton link size="small" @click="handleEdit(item)">
                          <Edit class="h-4 w-4" />
                        </ElButton>
                      </ElTooltip>
                      <ElTooltip
                        v-if="effectiveButtons.showDelete"
                        :content="$t('common.delete')"
                        placement="top"
                      >
                        <ElButton
                          link
                          size="small"
                          type="danger"
                          @click="handleDelete(item)"
                        >
                          <Trash2 class="h-4 w-4" />
                        </ElButton>
                      </ElTooltip>
                      <!-- 子表操作按钮 -->
                      <ElTooltip
                        v-for="subBtn in listConfig.subTableButtons"
                        :key="subBtn.id"
                        :content="subBtn.buttonText"
                        placement="top"
                      >
                        <ElButton
                          link
                          size="small"
                          :type="subBtn.buttonType || 'primary'"
                          @click="handleOpenSubTable(item, subBtn)"
                        >
                          <IconifyIcon
                            v-if="subBtn.buttonIcon"
                            :icon="subBtn.buttonIcon"
                            class="h-4 w-4"
                          />
                          <span v-else>{{ subBtn.buttonText }}</span>
                        </ElButton>
                      </ElTooltip>
                    </div>
                  </div>
                  <!-- 第二行：副标题 -->
                  <div
                    v-if="listConfig.cardFields.subtitle"
                    class="text-muted-foreground mt-1 truncate text-xs"
                  >
                    <span
                      v-if="
                        isCardFieldFormSelector(
                          listConfig.cardFields.subtitle,
                        ) &&
                        getCardFieldValue(item, listConfig.cardFields.subtitle)
                      "
                      class="text-primary inline-flex cursor-pointer items-center gap-1"
                      @click="
                        handleCardFormSelectorClick(
                          $event,
                          item,
                          listConfig.cardFields.subtitle,
                        )
                      "
                    >
                      <Link class="h-3 w-3 flex-shrink-0" />
                      {{
                        getCardFieldValue(item, listConfig.cardFields.subtitle)
                      }}
                    </span>
                    <template v-else>
                      {{
                        getCardFieldValue(item, listConfig.cardFields.subtitle)
                      }}
                    </template>
                  </div>
                </div>
              </div>
            </template>

            <!-- 描述 -->
            <div class="space-y-3">
              <p
                v-if="listConfig.cardFields.description"
                class="text-muted-foreground line-clamp-2 min-h-[40px] text-[12px] text-sm"
              >
                <span
                  v-if="
                    isCardFieldFormSelector(
                      listConfig.cardFields.description,
                    ) &&
                    getCardFieldValue(item, listConfig.cardFields.description)
                  "
                  class="text-primary inline-flex cursor-pointer items-center gap-1 hover:underline"
                  @click="
                    handleCardFormSelectorClick(
                      $event,
                      item,
                      listConfig.cardFields.description,
                    )
                  "
                >
                  <Link class="h-3 w-3 flex-shrink-0" />
                  {{
                    getCardFieldValue(item, listConfig.cardFields.description)
                  }}
                </span>
                <template v-else>
                  {{
                    getCardFieldValue(
                      item,
                      listConfig.cardFields.description,
                    ) || $t('common.noDescription')
                  }}
                </template>
              </p>

              <!-- 标签 -->
              <div
                v-if="
                  listConfig.cardFields.tags &&
                  listConfig.cardFields.tags.length > 0
                "
                class="flex flex-wrap gap-1"
              >
                <template
                  v-for="(tagField, idx) in listConfig.cardFields.tags"
                  :key="idx"
                >
                  <!-- form-selector 类型字段使用可点击的标签样式 -->
                  <span
                    v-if="
                      isCardFieldFormSelector(tagField) &&
                      getCardFieldValue(item, tagField)
                    "
                    class="bg-primary/10 text-primary hover:bg-primary/20 inline-flex cursor-pointer items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors"
                    @click="handleCardFormSelectorClick($event, item, tagField)"
                  >
                    <Link class="h-3 w-3 flex-shrink-0" />
                    {{ getCardFieldDisplayValue(item, tagField) }}
                  </span>
                  <!-- 普通标签 -->
                  <ElTag
                    v-else-if="getCardFieldValue(item, tagField)"
                    size="small"
                    :type="getCardTagType(item, tagField)"
                  >
                    {{ getCardFieldDisplayValue(item, tagField) }}
                  </ElTag>
                </template>
              </div>

              <!-- 底部 -->
              <div
                class="text-muted-foreground flex items-center justify-between text-xs"
              >
                <span v-if="listConfig.cardFields.footerLeft">
                  <span
                    v-if="
                      isCardFieldFormSelector(
                        listConfig.cardFields.footerLeft,
                      ) &&
                      getCardFieldValue(item, listConfig.cardFields.footerLeft)
                    "
                    class="text-primary inline-flex cursor-pointer items-center gap-1 hover:underline"
                    @click="
                      handleCardFormSelectorClick(
                        $event,
                        item,
                        listConfig.cardFields.footerLeft,
                      )
                    "
                  >
                    <Link class="h-3 w-3 flex-shrink-0" />
                    {{
                      getCardFieldValue(item, listConfig.cardFields.footerLeft)
                    }}
                  </span>
                  <template v-else>
                    {{
                      getCardFieldValue(item, listConfig.cardFields.footerLeft)
                    }}
                  </template>
                </span>
                <span v-else></span>
                <span v-if="listConfig.cardFields.footerRight">
                  <span
                    v-if="
                      isCardFieldFormSelector(
                        listConfig.cardFields.footerRight,
                      ) &&
                      getCardFieldValue(item, listConfig.cardFields.footerRight)
                    "
                    class="text-primary inline-flex cursor-pointer items-center gap-1 hover:underline"
                    @click="
                      handleCardFormSelectorClick(
                        $event,
                        item,
                        listConfig.cardFields.footerRight,
                      )
                    "
                  >
                    <Link class="h-3 w-3 flex-shrink-0" />
                    {{
                      getCardFieldValue(item, listConfig.cardFields.footerRight)
                    }}
                  </span>
                  <template v-else>
                    {{
                      getCardFieldValue(item, listConfig.cardFields.footerRight)
                    }}
                  </template>
                </span>
              </div>
            </div>
          </ElCard>
        </div>

        <!-- 空状态 -->
        <ElEmpty v-else :description="$t('common.noData')" />

        <!-- 分页 -->
        <template #footer>
          <div
            v-if="listConfig.card.showPagination"
            class="flex w-full items-center justify-end"
          >
            <ElPagination
              v-model:current-page="cardPagination.current"
              v-model:page-size="cardPagination.pageSize"
              :total="cardPagination.total"
              :page-sizes="[12, 24, 36, 48]"
              :pager-count="7"
              layout="total, sizes, prev, pager, next, jumper"
              background
              size="small"
              @current-change="handleCardPageChange"
              @size-change="handleCardSizeChange"
            />
          </div>
        </template>
      </Page>
    </template>

    <FormDataDialog
      v-if="formMeta"
      v-model="showFormDialog"
      :mode="dialogMode"
      :form-code="formCode"
      :form-config="formMeta.form_config"
      :edit-id="editingId"
      :container-type="listConfig.containerType"
      :dialog-config="listConfig.dialog"
      :drawer-config="listConfig.drawer"
      :show-confirm-button="listConfig.showConfirmButton"
      :after-save-action="listConfig.afterSaveAction"
      :form-type="formMeta.form_type"
      :enable-start-workflow-on-add="listConfig.enableStartWorkflowOnAdd"
      :bound-workflows="boundWorkflows"
      :default-form-data="props.defaultFormData"
      @saved="handleFormSaved"
    />

    <ExportConfigDialog
      v-if="formMeta && formMeta.list_config"
      v-model="showExportDialog"
      :columns="formMeta.list_config.columns || []"
      :has-sub-tables="formMeta.sub_tables && formMeta.sub_tables.length > 0"
      @confirm="handleConfirmExport"
    />

    <!-- 导出进度对话框 -->
    <ExportProgressDialog
      v-model="showExportProgressDialog"
      :form-code="formCode"
      :export-config="exportProgressConfig"
    />

    <!-- 导入对话框 -->
    <ImportDialog
      ref="importDialogRef"
      :form-code="formCode"
      :form-fields="importFormFields"
      @success="handleImportSuccess"
    />

    <!-- 图片预览 -->
    <ElImageViewer
      v-if="showImageViewer"
      :url-list="previewImages"
      :initial-index="0"
      @close="showImageViewer = false"
    />

    <!-- Agent 对话窗口 -->
    <ZqDialog
      v-model="agentChatVisible"
      :title="agentDialogTitle"
      :width="agentDialogWidth"
      :show-footer="false"
      :fullscreen="agentDialogFullscreen"
      :close-on-click-modal="false"
      destroy-on-close
      @close="handleAgentChatClose"
    >
      <div
        :class="
          agentDialogFullscreen ? 'agent-chat-fullscreen' : 'agent-chat-normal'
        "
      >
        <AiChatPanel
          v-if="agentChatVisible && (currentAgentId || currentAgentCode)"
          mode="agent-chat"
          :agent-id="currentAgentId || undefined"
          :initial-inputs="{ form_code: formCode }"
          layout="fullscreen"
          :show-header="false"
          :show-close-button="false"
          @close="agentChatVisible = false"
        />
        <div v-else class="py-8 text-center text-gray-500">
          {{ $t('form-manager.listDesign.agentIdPlaceholder') }}
        </div>
      </div>
    </ZqDialog>

    <!-- 页面查看弹窗 -->
    <PageViewDialog
      v-model="pageViewVisible"
      :page-code="currentPageCode"
      :title="currentPageTitle"
      :width="currentPageWidth"
      :fullscreen="currentPageFullscreen"
      :row-data="currentPageRowData"
    />

    <!-- 子表单容器 -->
    <SubTableFormContainer
      v-if="
        currentSubTableButton &&
        currentSubTableButton.containerType !== 'layout'
      "
      v-model="showSubTableContainer"
      :button-config="currentSubTableButton"
      :main-record-id="currentMainRecordId"
      @closed="handleSubTableClosed"
    />

    <!-- 生成单据弹窗 -->
    <GenerateDocumentDialog
      v-model="showGenerateDocumentDialog"
      :form-code="formMeta?.code || ''"
      :form-data-id="currentGenerateDocumentRow?.id || ''"
    />

    <!-- 关联表单详情弹窗 -->
    <ZqDialog
      v-model="showRelatedFormDialog"
      :title="relatedFormDialogTitle"
      width="1200px"
      :show-footer="false"
      destroy-on-close
      class="h-[90%]"
    >
      <div v-loading="relatedFormLoading" class="600px">
        <ElForm
          v-if="relatedFormMeta && !relatedFormLoading"
          :model="relatedFormData"
          :label-width="`${relatedFormConf.labelWidth || 100}px`"
          :label-position="relatedFormConf.labelPosition || 'right'"
          :size="relatedFormConf.size || 'default'"
          disabled
        >
          <PreviewItem
            v-for="item in relatedFormConf.items"
            :key="item.id"
            :item="item"
            :model-value="relatedFormData"
            :is-edit="true"
            :field-permissions="relatedFormFieldPermissions"
          />
        </ElForm>
      </div>
    </ZqDialog>
  </div>
</template>

<style scoped>
.form-data-list {
  display: flex;
  flex-direction: column;
}

.agent-chat-fullscreen {
  height: calc(100vh - 120px);
  overflow: auto;
}

.agent-chat-normal {
  height: calc(100vh - 200px);
  min-height: 400px;
  overflow: auto;
}

/* 行操作按钮容器 */
.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: nowrap;
}

/* 修复更多按钮下拉菜单的对齐问题 */
.row-actions .el-dropdown {
  display: inline-flex;
  align-items: center;
}

/* 选择模式下的行样式 */
.selection-row-hover {
  cursor: pointer;
}

.selection-row-hover:hover {
  background-color: var(--el-fill-color-light) !important;
}

.selection-row-selected {
  cursor: pointer;
  background-color: var(--el-color-primary-light-9) !important;
}

.selection-row-selected:hover {
  background-color: var(--el-color-primary-light-8) !important;
}

/* 卡片选择模式下的样式 */
.card-item-selected {
  border: 2px solid var(--el-color-primary) !important;
  background-color: var(--el-color-primary-light-9);
}

.card-item-selected:hover {
  background-color: var(--el-color-primary-light-8);
}
</style>
