<script setup lang="ts">
import type { DataSourceConfig } from '../store/formDesignStore';

import { computed, nextTick, onMounted, ref, watch, watchEffect } from 'vue';

import { useDebounceFn } from '@vueuse/core';

import { CircleHelp } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  Bottom,
  Check,
  CopyDocument,
  Delete,
  Plus,
  Rank,
  Top,
} from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import {
  ElAlert,
  ElButton,
  ElCascader,
  ElCheckbox,
  ElCheckboxGroup,
  ElCol,
  ElCollapse,
  ElCollapseItem,
  ElColorPicker,
  ElDatePicker,
  ElDivider,
  ElFormItem,
  ElIcon,
  ElImage,
  ElImageViewer,
  ElInput,
  ElInputNumber,
  ElOption,
  ElPagination,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElRate,
  ElRow,
  ElSelect,
  ElSlider,
  ElStep,
  ElSteps,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTimeline,
  ElTimelineItem,
  ElTimePicker,
  ElTooltip,
  ElTreeSelect,
} from 'element-plus';
import draggable from 'vuedraggable';

import { checkFormDataUniqueApi } from '#/api/online-dev/form-data-api';
import { requestClient } from '#/api/request';
import { getFileUrl } from '#/composables/useFileUrl';
import FileListCell from '#/views/online-dev/form-render/components/FileListCell.vue';

import AiImageOcr from '../../zq-form/ai-image-ocr/ai-image-ocr.vue';
import CodeGenerator from '../../zq-form/code-generator/code-generator.vue';
import CronSelector from '../../zq-form/cron-selector/cron-selector.vue';
import CurrentDatetime from '../../zq-form/current-datetime/current-datetime.vue';
import CurrentUser from '../../zq-form/current-user/current-user.vue';
import DeptSelector from '../../zq-form/dept-selector/dept-selector.vue';
import FileSelector from '../../zq-form/file-selector/file-selector.vue';
import FormSelector from '../../zq-form/form-selector/form-selector.vue';
import FormulaInput from '../../zq-form/formula-input/formula-input.vue';
import ImageSelector from '../../zq-form/image-selector/image-selector.vue';
import LinkedField from '../../zq-form/linked-field/linked-field.vue';
import MoneyInput from '../../zq-form/money-input/money-input.vue';
import PostSelector from '../../zq-form/post-selector/post-selector.vue';
import QRCodeGenerator from '../../zq-form/qrcode-generator/qrcode-generator.vue';
import RegionSelector from '../../zq-form/region-selector/region-selector.vue';
import RichTextEditor from '../../zq-form/rich-text-editor/rich-text-editor.vue';
import RoleSelector from '../../zq-form/role-selector/role-selector.vue';
import SignaturePad from '../../zq-form/signature-pad/signature-pad.vue';
import TableSelector from '../../zq-form/table-selector/table-selector.vue';
import UserSelector from '../../zq-form/user-selector/user-selector.vue';

defineOptions({
  name: 'PreviewItem',
});

const props = defineProps<{
  /** 编辑时的记录ID（唯一性校验时排除自身） */
  editId?: string;
  /** 字段权限配置 */
  fieldPermissions?: Record<
    string,
    { mask_rule?: null | string; permission?: string; permission_type?: string }
  >;
  /** 表单编码（用于唯一性校验等后端调用） */
  formCode?: string;
  /** 是否为编辑模式 */
  isEdit?: boolean;
  isTable?: boolean;
  item: any;
  modelValue: any;
  /** 子表单中 ElFormItem 的 prop 前缀，如 "subTable.0." */
  propPrefix?: string;
  /** 子表数据数组引用（用于 expandMultipleToRows 功能） */
  subTableRows?: any[];
  /** 子表配置引用（用于 expandMultipleToRows 获取 children 初始化新行） */
  subTableItem?: any;
}>();

const fieldProp = computed(() => {
  return props.propPrefix
    ? `${props.propPrefix}${props.item.field}`
    : props.item.field;
});

// 动态选项数据
const dynamicOptions = ref<any[]>([]);
const isLoadingOptions = ref(false);

// 获取当前字段的权限
const fieldPermission = computed(() => {
  const fieldName = props.item.field;
  if (!fieldName || !props.fieldPermissions) {
    return null;
  }
  return props.fieldPermissions[fieldName] || null;
});

// 判断字段是否只读（read 权限或 masked 权限）
const isFieldReadonly = computed(() => {
  if (!fieldPermission.value) {
    return false;
  }
  // 兼容 permission_type 和 permission 两种key
  const permType =
    fieldPermission.value.permission_type || fieldPermission.value.permission;
  return permType === 'read' || permType === 'masked';
});

// 判断字段是否隐藏
const isFieldHidden = computed(() => {
  if (!fieldPermission.value) {
    return false;
  }
  // 兼容 permission_type 和 permission 两种key
  const permType =
    fieldPermission.value.permission_type || fieldPermission.value.permission;
  return permType === 'hidden';
});

// 需要特殊处理的选择器组件类型
const MASKED_SELECTOR_TYPES = new Set([
  'dept-selector',
  'post-selector',
  'region-selector',
  'role-selector',
  'user-selector',
]);

// 判断是否是脱敏的选择器组件（需要显示禁用的 input 而不是选择器）
const isMaskedSelector = computed(() => {
  if (!fieldPermission.value) {
    return false;
  }
  const permType =
    fieldPermission.value.permission_type || fieldPermission.value.permission;
  return permType === 'masked' && MASKED_SELECTOR_TYPES.has(props.item.type);
});

// 获取脱敏选择器的显示值（编辑时显示 name，新增时显示提示）
const maskedSelectorDisplayValue = computed(() => {
  if (!isMaskedSelector.value) return '';
  const fieldName = props.item.field;
  // 尝试获取关联的 _name 字段值
  const nameValue = props.modelValue[`${fieldName}_name`];
  if (nameValue) {
    return nameValue;
  }
  // 如果没有 _name 字段，尝试去掉 _id 后缀获取 name
  if (fieldName.endsWith('_id')) {
    const baseName = fieldName.slice(0, -3);
    const baseNameValue = props.modelValue[`${baseName}_name`];
    if (baseNameValue) {
      return baseNameValue;
    }
  }
  return '';
});

// 获取实际使用的选项（静态或动态）
const effectiveOptions = computed(() => {
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  if (!dataSource || dataSource.type === 'static') {
    return props.item.options || [];
  }
  return dynamicOptions.value;
});

// 转换接口返回数据为选项格式
function transformOptions(data: any[], config: DataSourceConfig): any[] {
  const labelField = config.labelField || 'label';
  const valueField = config.valueField || 'value';
  const descField = config.descField || '';
  const childrenField = config.childrenField || 'children';

  function transform(items: any[]): any[] {
    return items.map((item) => ({
      label: item[labelField],
      value: item[valueField],
      desc: descField ? (item[descField] ?? '') : '',
      children: item[childrenField]
        ? transform(item[childrenField])
        : undefined,
    }));
  }

  return transform(data);
}

// 加载字典数据
async function loadDictOptions(dictCode: string) {
  try {
    isLoadingOptions.value = true;
    const response = await requestClient.get(
      `/api/core/dict_item/by/dict_code/${dictCode}`,
    );
    const data = response || [];
    dynamicOptions.value = data.map((item: any) => ({
      label: item.label,
      value: item.value,
    }));
  } catch (error) {
    console.error($t('form-design.message.loadDictError'), error);
    dynamicOptions.value = [];
  } finally {
    isLoadingOptions.value = false;
  }
}

// 加载API数据
async function loadApiOptions(
  config: DataSourceConfig,
  params?: Record<string, any>,
) {
  if (!config.apiUrl) return;

  try {
    isLoadingOptions.value = true;
    const requestParams = { ...config.apiParams, ...params };

    let response;
    response = await (config.apiMethod === 'POST'
      ? requestClient.post(config.apiUrl, requestParams)
      : requestClient.get(config.apiUrl, { params: requestParams }));

    const data = Array.isArray(response)
      ? response
      : response?.list || response?.data || [];
    dynamicOptions.value = transformOptions(data, config);
  } catch (error) {
    console.error($t('form-design.message.loadApiError'), error);
    dynamicOptions.value = [];
  } finally {
    isLoadingOptions.value = false;
  }
}

// 构建数据源参数
function buildDataSourceParams(config: DataSourceConfig): Record<string, any> {
  const params: Record<string, any> = {};
  
  console.log('[buildDataSourceParams] config.dataSourceParams:', config.dataSourceParams);
  
  if (!config.dataSourceParams?.length) return params;
  
  for (const paramConfig of config.dataSourceParams) {
    let value: any;
    let useDefaultForEmpty = true; // 是否在值为空时使用默认值
    
    console.log('[buildDataSourceParams] Processing param:', paramConfig.name, {
      valueSource: paramConfig.valueSource,
      fixedValue: paramConfig.fixedValue,
      default: paramConfig.default,
    });
    
    switch (paramConfig.valueSource) {
      case 'fixed':
        // 优先使用用户设置的固定值，只有在用户未设置时才使用数据源默认值
        if (paramConfig.fixedValue !== undefined && paramConfig.fixedValue !== '') {
          value = paramConfig.fixedValue;
        } else if (paramConfig.default !== undefined) {
          value = paramConfig.default;
        }
        console.log('[buildDataSourceParams] Fixed value result:', value);
        break;
      case 'field':
        // 从表单字段获取值
        if (paramConfig.sourceField && props.modelValue) {
          value = props.modelValue[paramConfig.sourceField];
          console.log('[buildDataSourceParams] Field value:', {
            sourceField: paramConfig.sourceField,
            value,
            modelValue: props.modelValue,
          });
        }
        break;
      case 'search':
        // 搜索模式：从 searchKeyword 获取值，不使用默认值
        value = searchKeyword.value || undefined;
        useDefaultForEmpty = false; // 搜索模式不使用默认值，等待用户输入
        break;
    }
    
    // 只有有值时才添加参数（跳过 undefined 和空字符串）
    if (value !== undefined && value !== '') {
      params[paramConfig.name] = value;
    } else if (useDefaultForEmpty && paramConfig.required && paramConfig.default !== undefined) {
      // 必填参数使用默认值（搜索模式除外）
      params[paramConfig.name] = paramConfig.default;
    }
  }
  
  return params;
}

// 搜索关键词（用于 search 类型的参数）
const searchKeyword = ref('');

// 检查是否有 search 类型的参数（用于启用远程搜索）
const hasSearchParam = computed(() => {
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  if (dataSource?.type === 'dataSource' && dataSource.dataSourceParams?.length) {
    return dataSource.dataSourceParams.some(p => p.valueSource === 'search');
  }
  return false;
});

// 远程搜索处理函数
const handleRemoteSearch = useDebounceFn((query: string) => {
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  if (dataSource?.type === 'dataSource' && dataSource.dataSourceCode) {
    searchKeyword.value = query;
    loadDataSourceOptions(dataSource);
  }
}, 300);

// 加载数据源数据
async function loadDataSourceOptions(config: DataSourceConfig) {
  if (!config.dataSourceCode) return;

  // 检查是否有 search 类型的参数，如果有且搜索关键词为空，则不加载
  const hasSearchParam = config.dataSourceParams?.some(p => p.valueSource === 'search');
  if (hasSearchParam && !searchKeyword.value) {
    console.log('[DataSource] Skip loading: search param exists but keyword is empty');
    dynamicOptions.value = [];
    return;
  }

  try {
    isLoadingOptions.value = true;
    
    // 构建参数
    const params = buildDataSourceParams(config);
    
    // 调试日志
    console.log('[DataSource] Loading options with params:', {
      code: config.dataSourceCode,
      params,
      dataSourceParams: config.dataSourceParams,
    });
    
    const response = await requestClient.get(
      `/api/core/data-source/execute/${config.dataSourceCode}`,
      { params },
    );
    
    // 处理各种可能的返回格式
    let data: any[] = [];
    let rawObject: Record<string, any> | null = null;
    
    if (Array.isArray(response)) {
      data = response;
    } else if (response?.list && Array.isArray(response.list)) {
      data = response.list;
    } else if (response?.data && Array.isArray(response.data)) {
      data = response.data;
    } else if (response?.result && Array.isArray(response.result)) {
      data = response.result;
    } else if (response?.items && Array.isArray(response.items)) {
      data = response.items;
    } else if (config.objectToOptions && response && typeof response === 'object') {
      // 对象转选项模式：将对象属性转为选项
      // 按优先级从 data/result 等字段获取对象，否则使用整个 response
      if (response.data && typeof response.data === 'object' && !Array.isArray(response.data)) {
        rawObject = response.data;
      } else if (response.result && typeof response.result === 'object' && !Array.isArray(response.result)) {
        rawObject = response.result;
      } else {
        rawObject = response;
      }
    }

    console.log($t('form-design.message.loadDataSourceSuccess'), data, rawObject);

    // 对象转选项模式
    if (config.objectToOptions && rawObject) {
      const excludeFields = config.objectExcludeFields || [];
      const maxLength = config.objectLabelMaxLength;
      dynamicOptions.value = Object.entries(rawObject)
        .filter(([key]) => !excludeFields.includes(key))
        .filter(([, value]) => {
          // 过滤掉 null、undefined、对象和数组类型的值
          if (value === null || value === undefined) return false;
          if (typeof value === 'object') return false;
          return true;
        })
        .map(([key, value]) => {
          const strValue = String(value);
          const label = maxLength && strValue.length > maxLength
            ? strValue.slice(0, maxLength) + '...'
            : strValue;
          return {
            label,
            value: value,
            desc: key,
          };
        });
      console.log($t('form-design.message.transformedOptions'), dynamicOptions.value);
      return;
    }

    // 如果组件配置了字段映射，则使用组件的配置
    // 否则使用默认的 label/value 字段（数据源应该已经处理好字段映射）
    const labelField = config.labelField || 'label';
    const valueField = config.valueField || 'value';
    const childrenField = config.childrenField || 'children';

    // 检查数据是否已经是正确格式
    if (
      data.length > 0 &&
      data[0].label !== undefined &&
      data[0].value !== undefined
    ) {
      dynamicOptions.value = data;
    } else {
      // 需要转换字段
      dynamicOptions.value = transformOptions(data, {
        ...config,
        labelField,
        valueField,
        childrenField,
      });
    }

    console.log(
      $t('form-design.message.transformedOptions'),
      dynamicOptions.value,
    );
  } catch (error) {
    console.error($t('form-design.message.loadDataSourceError'), error);
    dynamicOptions.value = [];
  } finally {
    isLoadingOptions.value = false;
  }
}

// 表单数据搜索关键词
const formDataSearchKeyword = ref('');

// 检查是否启用表单数据远程搜索
const hasFormDataSearch = computed(() => {
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  return dataSource?.type === 'formData' && dataSource.formEnableSearch === true;
});

// 表单数据远程搜索处理函数
const handleFormDataRemoteSearch = useDebounceFn((query: string) => {
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  if (dataSource?.type === 'formData' && dataSource.formCode) {
    // 如果搜索关键词没有变化，不重复加载
    if (query === formDataSearchKeyword.value && dynamicOptions.value.length > 0) {
      return;
    }
    formDataSearchKeyword.value = query;
    loadFormDataOptions(dataSource);
  }
}, 300);

// 加载表单数据选项
async function loadFormDataOptions(config: DataSourceConfig) {
  if (!config.formCode || !config.formLabelField || !config.formValueField)
    return;
  // 级联/树形选择懒加载模式下不做全量加载（由 lazyLoad 函数按需加载）
  if (['cascader', 'tree-select'].includes(props.item.type) && config.formLazyLoad === true) return;


  try {
    isLoadingOptions.value = true;

    // 构建查询参数，使用配置的分页大小（默认100）
    const pageSize = config.formPageSize || 100;
    const params: Record<string, any> = { page: 1, pageSize };

    // 如果启用了搜索且有搜索关键词，添加搜索参数（支持 label 和描述字段混合搜索）
    if (config.formEnableSearch && formDataSearchKeyword.value) {
      // 构建搜索字段列表
      const searchFields = [config.formLabelField];
      if (config.formDescField) {
        searchFields.push(config.formDescField);
      }
      // 使用 search 参数进行多字段模糊搜索
      params.search = formDataSearchKeyword.value;
      params.search_fields = searchFields.join(',');
    }

    // 添加过滤条件
    if (config.formFilters && config.formFilters.length > 0) {
      for (const filter of config.formFilters) {
        if (filter.sourceField && filter.targetField) {
          const sourceValue = props.modelValue[filter.sourceField];

          // 为空/不为空操作符不需要源字段值
          if (filter.filterType === 'null') {
            params[`${filter.targetField}__null`] = 'true';
            continue;
          }
          if (filter.filterType === 'not_null') {
            params[`${filter.targetField}__not_null`] = 'true';
            continue;
          }

          // 其他操作符需要源字段有值
          if (
            sourceValue !== undefined &&
            sourceValue !== null &&
            sourceValue !== ''
          ) {
            // 根据过滤类型构建参数
            switch (filter.filterType) {
              case 'eq': {
                params[filter.targetField] = sourceValue;
                break;
              }
              case 'gt': {
                params[`${filter.targetField}__gt`] = sourceValue;
                break;
              }
              case 'gte': {
                params[`${filter.targetField}__gte`] = sourceValue;
                break;
              }
              case 'in': {
                // in 类型，值用逗号分隔
                const values = Array.isArray(sourceValue)
                  ? sourceValue.join(',')
                  : sourceValue;
                params[`filter_${filter.targetField}`] = values;
                break;
              }
              case 'like': {
                params[`${filter.targetField}__like`] = sourceValue;
                break;
              }
              case 'lt': {
                params[`${filter.targetField}__lt`] = sourceValue;
                break;
              }
              case 'lte': {
                params[`${filter.targetField}__lte`] = sourceValue;
                break;
              }
              case 'ne': {
                params[`${filter.targetField}__ne`] = sourceValue;
                break;
              }
            }
          }
        }
      }
    }

    // 调用表单数据列表接口
    const response = await requestClient.get(
      `/api/online_dev/form-data/${config.formCode}/list`,
      { params },
    );

    const items = response?.items || [];

    // 级联/树形选择 + 表单数据源 + 配置了父节点字段：构建树形结构
    if (['cascader', 'tree-select'].includes(props.item.type) && config.formCode && config.formParentField) {
      const parentField = config.formParentField;
      const valueField = config.formValueField!;
      const labelField = config.formLabelField!;

      function buildTree(flatItems: any[], parentId: any = null): any[] {
        return flatItems
          .filter((item: any) => {
            const pv = item[parentField];
            if (parentId === null) {
              return pv === null || pv === undefined || pv === '' || pv === 0;
            }
            return String(pv) === String(parentId);
          })
          .map((item: any) => {
            const children = buildTree(flatItems, item[valueField]);
            const node: any = {
              label: item[labelField] ?? '',
              value: item[valueField] ?? '',
              _raw: item,
            };
            if (children.length > 0) {
              node.children = children;
            }
            return node;
          })
          .filter((node: any) => node.value !== '' && node.value !== null && node.value !== undefined);
      }

      dynamicOptions.value = buildTree(items);
    } else {
      // 转换为选项格式（支持描述字段）
      // 保留原始数据对象 _raw，供值关联使用
      dynamicOptions.value = items
        .map((item: any) => ({
          label: item[config.formLabelField!] ?? '',
          value: item[config.formValueField!] ?? '',
          desc: config.formDescField ? (item[config.formDescField] ?? '') : '',
          _raw: item, // 保留完整的原始数据
        }))
        .filter(
          (opt: any) =>
            opt.value !== '' && opt.value !== null && opt.value !== undefined,
        );
    }
  } catch (error) {
    console.error('加载表单数据失败:', error);
    dynamicOptions.value = [];
  } finally {
    isLoadingOptions.value = false;
  }
}

// 级联组件懒加载函数
async function cascaderLazyLoadFn(node: any, resolve: (data: any[]) => void) {
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  if (!dataSource?.formCode || !dataSource.formLabelField || !dataSource.formValueField) {
    resolve([]);
    return;
  }

  const parentField = dataSource.formParentField || 'parent_id';
  const parentId = node.root ? undefined : node.value;
  const params: Record<string, any> = {
    parentField,
    ...(parentId !== undefined ? { parentId } : {}),
  };

  try {
    const items = await requestClient.get(
      `/api/online_dev/form-data/${dataSource.formCode}/tree/children`,
      { params },
    );
    const nodeList = (items || []).map((item: any) => ({
      label: item[dataSource.formLabelField!] ?? '',
      value: item[dataSource.formValueField!] ?? '',
      leaf: !item.has_children,
      _raw: item,
    })).filter((n: any) => n.value !== '' && n.value !== null && n.value !== undefined);
    resolve(nodeList);
  } catch {
    resolve([]);
  }
}

// 级联组件是否使用懒加载
const isCascaderLazy = computed(() => {
  if (props.item.type !== 'cascader') return false;
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  if (dataSource?.type !== 'formData' || !dataSource.formCode) return false;
  return dataSource.formLazyLoad === true;
});

// 级联组件的 CascaderProps（Element Plus 要求 lazy/lazyLoad 在 :props 对象里）
const cascaderElProps = computed(() => {
  if (props.item.type !== 'cascader') return undefined;
  const itemProps = props.item.props || {};
  // 收集 CascaderProps 相关属性
  const cascaderConfig: Record<string, any> = {};
  if (itemProps.expandTrigger) cascaderConfig.expandTrigger = itemProps.expandTrigger;
  if (itemProps.checkStrictly) cascaderConfig.checkStrictly = itemProps.checkStrictly;
  if (itemProps.emitPath !== undefined) cascaderConfig.emitPath = itemProps.emitPath;
  if (itemProps.multiple !== undefined) cascaderConfig.multiple = itemProps.multiple;
  // 懒加载配置
  if (isCascaderLazy.value) {
    cascaderConfig.lazy = true;
    cascaderConfig.lazyLoad = cascaderLazyLoadFn;
  }
  return Object.keys(cascaderConfig).length > 0 ? cascaderConfig : undefined;
});

// 树形选择是否使用懒加载
const isTreeSelectLazy = computed(() => {
  if (props.item.type !== 'tree-select') return false;
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  if (dataSource?.type !== 'formData' || !dataSource.formCode) return false;
  return dataSource.formLazyLoad === true;
});

// 树形选择懒加载函数（ElTreeSelect 的 load 回调签名：(node, resolve) => void）
async function treeSelectLoadFn(node: any, resolve: (data: any[]) => void) {
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  if (!dataSource?.formCode || !dataSource.formLabelField || !dataSource.formValueField) {
    resolve([]);
    return;
  }

  const parentField = dataSource.formParentField || 'parent_id';
  const parentId = node.level === 0 ? undefined : node.data?.value;
  const params: Record<string, any> = {
    parentField,
    ...(parentId !== undefined ? { parentId } : {}),
  };

  try {
    const items = await requestClient.get(
      `/api/online_dev/form-data/${dataSource.formCode}/tree/children`,
      { params },
    );
    const nodeList = (items || []).map((item: any) => ({
      label: item[dataSource.formLabelField!] ?? '',
      value: item[dataSource.formValueField!] ?? '',
      isLeaf: !item.has_children,
    })).filter((n: any) => n.value !== '' && n.value !== null && n.value !== undefined);
    resolve(nodeList);
  } catch {
    resolve([]);
  }
}

// 加载选项数据的通用函数
function loadOptionsData() {
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  if (!dataSource) return;

  if (dataSource.type === 'dict' && dataSource.dictCode) {
    loadDictOptions(dataSource.dictCode);
  } else if (dataSource.type === 'api' && dataSource.apiUrl) {
    loadApiOptions(dataSource);
  } else if (dataSource.type === 'dataSource' && dataSource.dataSourceCode) {
    loadDataSourceOptions(dataSource);
  } else if (dataSource.type === 'formData' && dataSource.formCode) {
    loadFormDataOptions(dataSource);
  }
}

// 懒加载模式下编辑回显：根据已选值查询对应的 label 预填充选项
const isPreloadingLabels = ref(false);

async function preloadLazySelectedLabels() {
  const itemType = props.item.type;
  if (!['cascader', 'tree-select'].includes(itemType)) return;
  const dataSource = props.item.dataSource as DataSourceConfig | undefined;
  if (!dataSource?.formCode || !dataSource.formLabelField || !dataSource.formValueField) return;
  if (dataSource.formLazyLoad !== true) return;

  const currentVal = props.modelValue?.[props.item.field];
  if (currentVal === null || currentVal === undefined || currentVal === '') return;

  const values = Array.isArray(currentVal) ? currentVal.flat() : [currentVal];
  const validValues = values.filter((v: any) => v !== null && v !== undefined && v !== '');
  if (validValues.length === 0) return;

  const valueField = dataSource.formValueField;
  const labelField = dataSource.formLabelField;

  isPreloadingLabels.value = true;
  try {
    const res = await requestClient.get(
      `/api/online_dev/form-data/${dataSource.formCode}/list`,
      { params: { page: 1, pageSize: validValues.length, [`filter_${valueField}`]: validValues.join(',') } },
    );
    const items = res?.items || [];
    if (items.length === 0) return;

    const preloadNodes = items.map((item: any) => ({
      label: item[labelField] ?? '',
      value: item[valueField] ?? '',
      leaf: true,
      isLeaf: true,
    })).filter((n: any) => n.value !== '' && n.value !== null);

    dynamicOptions.value = preloadNodes;
  } catch {
    // 静默失败
  } finally {
    isPreloadingLabels.value = false;
  }
}

// 初始化加载选项数据
onMounted(() => {
  nextTick(() => {
    loadOptionsData();
    preloadLazySelectedLabels();
    loadSubTableColumnOptions();
  });
});

// 监听数据源配置变化（设计器中切换数据源时触发）
watch(
  () => {
    const ds = props.item.dataSource as DataSourceConfig | undefined;
    return ds
      ? `${ds.type}-${ds.dictCode || ''}-${ds.dataSourceCode || ''}-${ds.apiUrl || ''}-${ds.formCode || ''}-${ds.formLabelField || ''}-${ds.formValueField || ''}-${ds.formDescField || ''}-${ds.labelField || ''}-${ds.valueField || ''}-${ds.descField || ''}`
      : '';
  },
  (newVal, oldVal) => {
    if (newVal && newVal !== oldVal) {
      loadOptionsData();
    }
  },
  { immediate: false },
);

// 监听依赖字段变化
watch(
  () => {
    const dataSource = props.item.dataSource as DataSourceConfig | undefined;
    if (dataSource?.type === 'dependent' && dataSource.dependField) {
      return props.modelValue[dataSource.dependField];
    }
    return undefined;
  },
  (newVal) => {
    const dataSource = props.item.dataSource as DataSourceConfig | undefined;
    if (
      dataSource?.type === 'dependent' &&
      dataSource.apiUrl &&
      newVal !== undefined
    ) {
      const paramName = dataSource.dependParamName || 'parentId';
      loadApiOptions(dataSource, { [paramName]: newVal });
      // 清空当前字段值，因为依赖字段变化了
      props.modelValue[props.item.field] = props.item.props.multiple
        ? []
        : null;
    }
  },
  { immediate: true },
);

// 监听表单数据过滤条件中的源字段变化
watch(
  () => {
    const dataSource = props.item.dataSource as DataSourceConfig | undefined;
    if (dataSource?.type === 'formData' && dataSource.formFilters?.length) {
      // 收集所有源字段的值，生成一个唯一的key
      return dataSource.formFilters
        .map((f) => `${f.sourceField}:${props.modelValue[f.sourceField] ?? ''}`)
        .join('|');
    }
    return undefined;
  },
  (newVal, oldVal) => {
    const dataSource = props.item.dataSource as DataSourceConfig | undefined;
    if (
      dataSource?.type === 'formData' &&
      dataSource.formCode &&
      newVal !== undefined &&
      newVal !== oldVal
    ) {
      loadFormDataOptions(dataSource);
      // 清空当前字段值，因为过滤条件变化了
      props.modelValue[props.item.field] = props.item.props?.multiple
        ? []
        : null;
    }
  },
  { immediate: false },
);

// 监听数据源参数中 field 类型参数对应的表单字段变化
watch(
  () => {
    const dataSource = props.item.dataSource as DataSourceConfig | undefined;
    if (dataSource?.type === 'dataSource' && dataSource.dataSourceParams?.length) {
      // 收集所有 field 类型参数对应的表单字段值
      const fieldParams = dataSource.dataSourceParams.filter(p => p.valueSource === 'field' && p.sourceField);
      if (fieldParams.length > 0) {
        return fieldParams
          .map((p) => `${p.sourceField}:${props.modelValue[p.sourceField!] ?? ''}`)
          .join('|');
      }
    }
    return undefined;
  },
  (newVal, oldVal) => {
    const dataSource = props.item.dataSource as DataSourceConfig | undefined;
    if (
      dataSource?.type === 'dataSource' &&
      dataSource.dataSourceCode &&
      newVal !== undefined
    ) {
      // 只有当值真正变化时才清空当前字段值（初始加载时不清空）
      if (oldVal !== undefined && newVal !== oldVal) {
        props.modelValue[props.item.field] = props.item.props?.multiple
          ? []
          : null;
      }
      // 当有 field 类型参数且对应字段有值时，重新加载数据源
      const fieldParams = dataSource.dataSourceParams?.filter(p => p.valueSource === 'field' && p.sourceField) || [];
      const hasFieldValue = fieldParams.some(p => {
        const val = props.modelValue[p.sourceField!];
        return val !== undefined && val !== null && val !== '';
      });
      if (hasFieldValue) {
        loadDataSourceOptions(dataSource);
      }
    }
  },
  { immediate: true },
);

// 值关联：仅在源字段值真正变化时（用户重新选择/更换），才自动填充关联值
// 编辑已有数据时不会触发，避免覆盖用户已修改的关联字段值
watch(
  () => {
    const itemProps = props.item.props;
    if (itemProps?.enableValueLink && itemProps?.valueSourceField) {
      return props.modelValue[itemProps.valueSourceField];
    }
    return undefined;
  },
  (newVal, oldVal) => {
    const itemProps = props.item.props;
    if (
      !itemProps?.enableValueLink ||
      !itemProps?.valueSourceField ||
      !itemProps?.valueDisplayField
    ) {
      return;
    }

    // 只在源字段值真正变化时才回填（跳过初始化赋值）
    if (oldVal === undefined && newVal !== undefined) {
      return;
    }

    if (!newVal) {
      return;
    }

    // 获取关联值
    let linkedValue: any = '';

    if (
      typeof newVal === 'object' &&
      newVal !== null &&
      !Array.isArray(newVal)
    ) {
      linkedValue = newVal[itemProps.valueDisplayField] ?? '';
    }

    if (Array.isArray(newVal) && newVal.length > 0) {
      const firstItem = newVal[0];
      if (typeof firstItem === 'object' && firstItem !== null) {
        linkedValue = firstItem[itemProps.valueDisplayField] ?? '';
      }
    }

    if (!linkedValue) {
      const selectedItemKey = `${itemProps.valueSourceField}_selectedItem`;
      const selectedItem = props.modelValue[selectedItemKey];
      if (selectedItem && typeof selectedItem === 'object') {
        linkedValue = selectedItem[itemProps.valueDisplayField] ?? '';
      }
    }

    if (!linkedValue) {
      const selectedItemsKey = `${itemProps.valueSourceField}_selectedItems`;
      const selectedItems = props.modelValue[selectedItemsKey];
      if (Array.isArray(selectedItems) && selectedItems.length > 0) {
        const firstItem = selectedItems[0];
        if (typeof firstItem === 'object' && firstItem !== null) {
          linkedValue = firstItem[itemProps.valueDisplayField] ?? '';
        }
      }
    }

    if (
      linkedValue !== '' &&
      linkedValue !== undefined &&
      linkedValue !== null
    ) {
      props.modelValue[props.item.field] = linkedValue;
    }
  },
);

// 公式计算：支持普通字段 {field} 和子表单聚合 SUM{subTable.field} 等
// 聚合函数：SUM, AVG, MAX, MIN, COUNT
// 日期函数：DATEDIFF{end, start} / DATEDIFF{end, start, unit}
const AGGREGATE_REGEX = /(?:(SUM|AVG|MAX|MIN|COUNT)\{([^}]+)\})/g;
const DATEDIFF_REGEX =
  /DATEDIFF\{\s*([^,}]+)\s*,\s*([^,}]+)\s*(?:,\s*(days|hours|minutes)\s*)?\}/g;
const SIMPLE_FIELD_REGEX = /\B\{([^}]+)\}/g;

// 计算子表单聚合值
const computeAggregate = (
  fn: string,
  subTableField: string,
  childField: string,
  data: Record<string, any>,
): null | number => {
  const rows = data[subTableField];
  if (!Array.isArray(rows) || rows.length === 0) {
    return fn === 'COUNT' ? 0 : null;
  }
  const values: number[] = [];
  for (const row of rows) {
    const v = row[childField];
    const num = typeof v === 'number' ? v : Number.parseFloat(v);
    if (!Number.isNaN(num)) {
      values.push(num);
    }
  }
  if (fn === 'COUNT') return values.length;
  if (values.length === 0) return null;
  switch (fn) {
    case 'AVG': {
      return values.reduce((a, b) => a + b, 0) / values.length;
    }
    case 'MAX': {
      return Math.max(...values);
    }
    case 'MIN': {
      return Math.min(...values);
    }
    case 'SUM': {
      return values.reduce((a, b) => a + b, 0);
    }
    default: {
      return null;
    }
  }
};

// 解析日期值为 Date 对象
const parseDateValue = (value: any): Date | null => {
  if (!value) return null;
  if (value instanceof Date) return value;
  if (typeof value === 'string' || typeof value === 'number') {
    const d = new Date(value);
    if (!Number.isNaN(d.getTime())) return d;
  }
  return null;
};

// 计算两个日期的差值
const computeDateDiff = (
  endField: string,
  startField: string,
  unit: string,
  data: Record<string, any>,
): null | number => {
  const endVal = parseDateValue(data[endField.trim()]);
  const startVal = parseDateValue(data[startField.trim()]);
  if (!endVal || !startVal) return null;
  const diffMs = endVal.getTime() - startVal.getTime();
  switch (unit) {
    case 'hours': {
      return diffMs / (1000 * 60 * 60);
    }
    case 'minutes': {
      return diffMs / (1000 * 60);
    }
    case 'days':
    default: {
      return diffMs / (1000 * 60 * 60 * 24);
    }
  }
};

const evaluateFormulaExpr = (
  formula: string,
  data: Record<string, any>,
): null | number => {
  if (!formula || !data) return null;
  try {
    let expression = formula;
    // 先替换 DATEDIFF{end, start, unit} -> 数值
    expression = expression.replaceAll(
      new RegExp(DATEDIFF_REGEX.source, 'g'),
      (_match, endField, startField, unit) => {
        const result = computeDateDiff(
          endField,
          startField,
          unit || 'days',
          data,
        );
        return result === null ? 'NaN' : result.toString();
      },
    );
    // 替换聚合函数 SUM{subTable.field} -> 数值
    expression = expression.replaceAll(
      new RegExp(AGGREGATE_REGEX.source, 'g'),
      (_match, fn, path) => {
        const dotIdx = path.indexOf('.');
        if (dotIdx === -1) return 'NaN';
        const subTableField = path.slice(0, dotIdx);
        const childField = path.slice(dotIdx + 1);
        const result = computeAggregate(fn, subTableField, childField, data);
        return result === null ? 'NaN' : result.toString();
      },
    );
    // 再替换普通字段 {field} -> 数值
    expression = expression.replaceAll(
      new RegExp(SIMPLE_FIELD_REGEX.source, 'g'),
      (_match, field) => {
        const value = data[field];
        const numValue =
          typeof value === 'number' ? value : Number.parseFloat(value);
        return Number.isNaN(numValue) ? 'NaN' : numValue.toString();
      },
    );
    // 如果包含 NaN，说明有字段值缺失
    if (expression.includes('NaN')) return null;
    // 清理非法字符，只保留数字和运算符
    expression = expression.replaceAll(/[^0-9+\-*/().]/g, '');
    if (!expression) return null;
    const result = new Function(`return ${expression}`)();
    if (
      typeof result === 'number' &&
      !Number.isNaN(result) &&
      Number.isFinite(result)
    ) {
      return result;
    }
    return null;
  } catch {
    return null;
  }
};

// 收集公式中引用的所有依赖（用于 watch）
const collectFormulaDeps = (
  formula: string,
  data: Record<string, any>,
): any[] => {
  const deps: any[] = [];
  // DATEDIFF 引用：监听日期字段
  let match;
  const dateDiffRe = new RegExp(DATEDIFF_REGEX.source, 'g');
  while ((match = dateDiffRe.exec(formula)) !== null) {
    const endField = (match[1] || '').trim();
    const startField = (match[2] || '').trim();
    deps.push(data[endField], data[startField]);
  }
  // 聚合引用：深度监听子表单数组
  const aggRe = new RegExp(AGGREGATE_REGEX.source, 'g');
  while ((match = aggRe.exec(formula)) !== null) {
    const path = match[2] || '';
    const dotIdx = path.indexOf('.');
    if (dotIdx !== -1) {
      const subTableField = path.slice(0, dotIdx);
      deps.push(JSON.stringify(data[subTableField]));
    }
  }
  // 普通字段引用
  const simpleRe = new RegExp(SIMPLE_FIELD_REGEX.source, 'g');
  while ((match = simpleRe.exec(formula)) !== null) {
    const fieldName = match[1] || '';
    deps.push(data[fieldName]);
  }
  return deps;
};

watch(
  () => {
    const itemProps = props.item.props;
    if (!itemProps?.enableFormula || !itemProps?.formula) return undefined;
    return collectFormulaDeps(itemProps.formula, props.modelValue);
  },
  () => {
    const itemProps = props.item.props;
    if (!itemProps?.enableFormula || !itemProps?.formula) return;
    const result = evaluateFormulaExpr(itemProps.formula, props.modelValue);
    if (result !== null) {
      const precision = itemProps.formulaPrecision ?? 2;
      props.modelValue[props.item.field] = Number(result.toFixed(precision));
    }
  },
  { immediate: true, deep: true },
);

// 分页逻辑
const currentPage = ref(1);
const pageSize = computed(() => props.item.props.pageSize || 10);
const hasPagination = computed(
  () => props.item.props.pagination && props.item.type === 'sub-table',
);

const displayData = computed({
  get: () => {
    ensureSubTableData();
    const list = props.modelValue[props.item.field] || [];
    if (!hasPagination.value) return list;
    const start = (currentPage.value - 1) * pageSize.value;
    return list.slice(start, start + pageSize.value);
  },
  set: (val) => {
    if (!hasPagination.value) {
      props.modelValue[props.item.field] = val;
      return;
    }
    const list = [...(props.modelValue[props.item.field] || [])];
    const start = (currentPage.value - 1) * pageSize.value;
    list.splice(start, pageSize.value, ...val);
    props.modelValue[props.item.field] = list;
  },
});

const handleCurrentChange = (val: number) => {
  currentPage.value = val;
};

const getRealIndex = (index: number) => {
  if (!hasPagination.value) return index;
  return (currentPage.value - 1) * pageSize.value + index;
};

// 监听数据变化，修正当前页
watchEffect(() => {
  if (!hasPagination.value) return;
  const total = (props.modelValue[props.item.field] || []).length;
  const maxPage = Math.ceil(total / pageSize.value) || 1;
  if (currentPage.value > maxPage) {
    currentPage.value = maxPage;
  }
});

// 确保子表单数据已初始化
const ensureSubTableData = () => {
  if (props.item.type === 'sub-table' && !props.modelValue[props.item.field]) {
    props.modelValue[props.item.field] = [];
  }
  // 新增模式下，如果子表单为空则自动添加一行
  if (
    props.item.type === 'sub-table' &&
    !props.isEdit &&
    props.modelValue[props.item.field] &&
    props.modelValue[props.item.field].length === 0
  ) {
    const newRow: any = {
      _id: `${Date.now()}_${Math.random()}`,
      _isEditing: true,
    };
    if (props.item.children) {
      props.item.children.forEach((col: any) => {
        newRow[col.field] = getColumnDefaultValue(col);
      });
    }
    props.modelValue[props.item.field].push(newRow);
  }
  return true;
};

// 处理AI图片识别的字段填充
const handleAiOcrFillFields = (data: Record<string, any>) => {
  if (!data || typeof data !== 'object') return;

  // 将识别结果填充到表单数据中
  Object.entries(data).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      props.modelValue[key] = value;
    }
  });
};

// 处理表格选择器选中项，存储完整数据供关联字段使用
const handleSelectItem = (
  field: string,
  item: Record<string, any> | Record<string, any>[] | undefined,
) => {
  // expandMultipleToRows：确认时一次性展开为多行
  if (
    Array.isArray(item) &&
    item.length > 0 &&
    props.item.props?.expandMultipleToRows &&
    props.subTableRows &&
    props.subTableItem
  ) {
    expandSelectedItemsToRows(field, item);
    return;
  }

  if (Array.isArray(item)) {
    props.modelValue[`${field}_selectedItems`] = item;
    props.modelValue[`${field}_selectedItem`] = item[0] || undefined;
  } else {
    props.modelValue[`${field}_selectedItem`] = item;
    props.modelValue[`${field}_selectedItems`] = item ? [item] : [];
  }
};

// 收集子表中所有行该字段的已有值（排除当前行），用于弹窗打开时自动勾选
function getExternalSelectedValues(field: string): string[] {
  if (!props.subTableRows) return [];
  const currentRow = props.modelValue;
  const values: string[] = [];
  for (const row of props.subTableRows) {
    if (row === currentRow) continue;
    if (row[field]) {
      values.push(String(row[field]));
    }
  }
  return values;
}

// 从选中项数据中提取值关联字段的值，填充到目标行
function fillLinkedFieldsFromItem(
  subItem: any,
  sourceField: string,
  selectedItem: Record<string, any>,
  targetRow: Record<string, any>,
) {
  if (!subItem.children) return;
  subItem.children.forEach((col: any) => {
    const colProps = col.props;
    if (
      colProps?.enableValueLink &&
      colProps?.valueSourceField === sourceField &&
      colProps?.valueDisplayField
    ) {
      const linkedValue = selectedItem[colProps.valueDisplayField];
      if (linkedValue !== undefined && linkedValue !== null) {
        targetRow[col.field] = linkedValue;
      }
    }
  });
}

// 多选展开为多行：点击确认后，仅新增不存在的选中项
function expandSelectedItemsToRows(
  field: string,
  selectedItems: Record<string, any>[],
) {
  const rows = props.subTableRows!;
  const subItem = props.subTableItem!;
  const valueField = props.item.formSelectorConfig?.valueField || 'id';
  const currentRow = props.modelValue;
  const currentIndex = rows.indexOf(currentRow);
  if (currentIndex === -1) return;

  // 收集子表中所有行已有的值（包括当前行）
  const existingValues = new Set<string>();
  for (const row of rows) {
    if (row[field]) existingValues.add(String(row[field]));
  }

  // 过滤出子表中尚不存在的新选中项
  const newItems = selectedItems.filter(
    (item) => !existingValues.has(String(item[valueField])),
  );

  if (newItems.length === 0) return;

  // 当前行还没有值时，第一个新项赋给当前行
  const currentHasValue = currentRow[field] && String(currentRow[field]).trim() !== '';
  let startIndex = 0;
  if (!currentHasValue) {
    const firstItem = newItems[0]!;
    currentRow[field] = String(firstItem[valueField]);
    currentRow[`${field}_selectedItem`] = firstItem;
    currentRow[`${field}_selectedItems`] = [firstItem];
    // 主动填充当前行的值关联字段
    fillLinkedFieldsFromItem(subItem, field, firstItem, currentRow);
    startIndex = 1;
  }

  // 剩余新项创建新行，插入到当前行之后
  const newRows: any[] = [];
  for (let i = startIndex; i < newItems.length; i++) {
    const selectedItem = newItems[i]!;
    const newRow: any = {
      _id: `${Date.now()}_${Math.random().toString(36).slice(2)}`,
      _isEditing: true,
    };
    if (subItem.children) {
      subItem.children.forEach((col: any) => {
        newRow[col.field] = getColumnDefaultValue(col);
      });
    }
    newRow[field] = String(selectedItem[valueField]);
    newRow[`${field}_selectedItem`] = selectedItem;
    newRow[`${field}_selectedItems`] = [selectedItem];
    // 主动填充值关联字段
    fillLinkedFieldsFromItem(subItem, field, selectedItem, newRow);
    newRows.push(newRow);
  }

  if (newRows.length > 0) {
    const insertIndex = rows.indexOf(currentRow) + 1;
    rows.splice(insertIndex, 0, ...newRows);
  }
}

// 处理 select 组件选择变化，存储完整选项对象供值关联使用
const handleSelectChange = (field: string, value: any) => {
  // 从 dynamicOptions 中查找选中的完整对象
  // 如果选项有 _raw 字段（表单数据源），则使用原始数据；否则使用选项本身
  if (Array.isArray(value)) {
    // 多选
    const selectedItems = value.map(v => {
      const opt = dynamicOptions.value.find(o => o.value === v);
      return opt?._raw || opt || { value: v, label: v };
    });
    props.modelValue[`${field}_selectedItems`] = selectedItems;
    props.modelValue[`${field}_selectedItem`] = selectedItems[0] || undefined;
  } else {
    // 单选
    const opt = dynamicOptions.value.find(o => o.value === value);
    const selectedItem = opt?._raw || opt || (value ? { value, label: value } : undefined);
    props.modelValue[`${field}_selectedItem`] = selectedItem;
    props.modelValue[`${field}_selectedItems`] = selectedItem ? [selectedItem] : [];
  }
};

// 子表合计方法：基于全量数据（非分页数据）计算，支持 sum/avg/min/max/count
const getSubTableSummaryMethod = (subItem: any) => {
  return (param: { columns: any[]; data: any[] }) => {
    const { columns } = param;
    // 使用全量数据而非分页后的 displayData
    const allData = props.modelValue[subItem.field] || [];

    return columns.map((column, index) => {
      // 序号列显示"合计"
      if (index === 0) {
        return $t('form-design.attribute.subTable.summaryLabel');
      }

      // 操作列留空
      if (column.label === $t('common.action')) {
        return '';
      }

      // 查找对应的子表列配置
      const col = subItem.children?.find(
        (c: any) => c.field === column.property,
      );
      if (!col || !col.props?.enableSummary) {
        return '';
      }

      const summaryType = col.props.summaryType || 'sum';
      const values = allData
        .map((row: any) => Number(row[col.field]))
        .filter((v: number) => !Number.isNaN(v));

      if (values.length === 0) {
        return summaryType === 'count' ? '0' : '';
      }

      let result: number;
      switch (summaryType) {
        case 'avg': {
          result = values.reduce((a: number, b: number) => a + b, 0) / values.length;
          break;
        }
        case 'min': {
          result = Math.min(...values);
          break;
        }
        case 'max': {
          result = Math.max(...values);
          break;
        }
        case 'count': {
          return String(allData.length);
        }
        default: {
          result = values.reduce((a: number, b: number) => a + b, 0);
          break;
        }
      }

      // 保留两位小数，去除多余的零
      return Number.isInteger(result)
        ? String(result)
        : result.toFixed(2).replace(/\.?0+$/, '');
    });
  };
};

// 计算操作列宽度
const getOperationColumnWidth = (item: any) => {
  let width = 100; // 基础宽度（编辑/保存）
  if (item.props.showSortButtons) width += 70;
  if (item.props.copyable) width += 50;
  if (item.props.deletable !== false) width += 50;
  return Math.max(width, 120);
};

// 开始编辑行
const startRowEdit = (row: any) => {
  // 保存原始数据用于取消时恢复
  row._originalData = JSON.parse(JSON.stringify(row));
  row._isEditing = true;
};

// 保存行编辑
const saveRowEdit = (row: any) => {
  row._isEditing = false;
  delete row._originalData;
};

// 全部保存：将所有编辑中的行退出编辑模式
const saveAllRows = (field: string) => {
  const rows = props.modelValue[field];
  if (!Array.isArray(rows)) return;
  for (const row of rows) {
    if (row._isEditing) {
      row._isEditing = false;
      delete row._originalData;
    }
  }
};

// 取消行编辑
const cancelRowEdit = (row: any, field: string, index: number) => {
  if (row._originalData) {
    // 恢复原始数据
    const list = props.modelValue[field];
    if (list && list[index]) {
      Object.keys(row._originalData).forEach((key) => {
        if (!key.startsWith('_')) {
          row[key] = row._originalData[key];
        }
      });
    }
    delete row._originalData;
  }
  row._isEditing = false;
};

// 选择器 label 缓存：key = "formCode:valueField:labelField:id", value = label
const selectorLabelCache = ref<Map<string, string>>(new Map());
const selectorLabelLoading = ref<Set<string>>(new Set());

// 异步加载选择器 label（form-selector / table-selector）
function loadSelectorLabels(col: any, ids: string[]) {
  const labelField =
    col.type === 'form-selector'
      ? col.formSelectorConfig?.labelField || 'name'
      : col.dataSource?.formLabelField || 'name';
  const valueField =
    col.type === 'form-selector'
      ? col.formSelectorConfig?.valueField || 'id'
      : col.dataSource?.formValueField || 'id';
  const formCode =
    col.type === 'form-selector'
      ? col.formSelectorConfig?.formCode
      : col.dataSource?.formCode;
  const dataSourceType = col.dataSource?.type;
  const dictCode = col.dataSource?.dictCode;
  const dataSourceCode = col.dataSource?.dataSourceCode;

  // 生成缓存 key 前缀
  const cachePrefix = `${col.type}:${formCode || dictCode || dataSourceCode || 'static'}:${valueField}:${labelField}`;

  // 过滤出未缓存且未在加载中的 id
  const missingIds = ids.filter((id) => {
    const cacheKey = `${cachePrefix}:${id}`;
    return (
      !selectorLabelCache.value.has(cacheKey) &&
      !selectorLabelLoading.value.has(cacheKey)
    );
  });
  if (missingIds.length === 0) return;

  // 标记为加载中
  missingIds.forEach((id) =>
    selectorLabelLoading.value.add(`${cachePrefix}:${id}`),
  );

  // 根据数据源类型加载
  const doLoad = async () => {
    try {
      let data: any[] = [];
      if (
        col.type === 'form-selector' ||
        (col.type === 'table-selector' && dataSourceType === 'formData')
      ) {
        if (!formCode) return;
        const idsStr = missingIds.join(',');
        const response = await requestClient.get(
          `/api/online_dev/form-data/${formCode}/list`,
          {
            params: {
              [`filter_${valueField}`]: idsStr,
              pageSize: missingIds.length,
            },
          },
        );
        data = response?.items || [];
      } else if (
        col.type === 'table-selector' &&
        dataSourceType === 'dict' &&
        dictCode
      ) {
        const response = await requestClient.get(
          `/api/core/dict_item/by/dict_code/${dictCode}`,
        );
        data = response || [];
      } else if (
        col.type === 'table-selector' &&
        dataSourceType === 'dataSource' &&
        dataSourceCode
      ) {
        const response = await requestClient.get(
          `/api/core/data-source/execute/${dataSourceCode}`,
        );
        data = Array.isArray(response)
          ? response
          : response?.list || response?.data || [];
      }
      for (const item of data) {
        const value = String(item[valueField] ?? '');
        const label = String(item[labelField] ?? '');
        if (value) {
          selectorLabelCache.value.set(`${cachePrefix}:${value}`, label);
        }
      }
    } catch (error) {
      console.error('加载选择器标签失败:', error);
    } finally {
      missingIds.forEach((id) =>
        selectorLabelLoading.value.delete(`${cachePrefix}:${id}`),
      );
    }
  };
  doLoad();
}

// 从缓存或 _selectedItems 中解析选择器显示值
function resolveSelectorLabel(val: any, col: any, row?: any): string {
  const labelField =
    col.type === 'form-selector'
      ? col.formSelectorConfig?.labelField || 'name'
      : col.dataSource?.formLabelField || 'name';
  const valueField =
    col.type === 'form-selector'
      ? col.formSelectorConfig?.valueField || 'id'
      : col.dataSource?.formValueField || 'id';
  const formCode =
    col.type === 'form-selector'
      ? col.formSelectorConfig?.formCode
      : col.dataSource?.formCode;
  const dataSourceType = col.dataSource?.type;
  const dictCode = col.dataSource?.dictCode;
  const dataSourceCode = col.dataSource?.dataSourceCode;

  const values = Array.isArray(val) ? val : [val];
  const labels: string[] = [];

  // 优先从行数据的 _selectedItems 中读取
  const selectedItems = row?.[`${col.field}_selectedItems`] || [];

  const cachePrefix = `${col.type}:${formCode || dictCode || dataSourceCode || 'static'}:${valueField}:${labelField}`;
  const uncachedIds: string[] = [];

  for (const v of values) {
    const strVal = String(v);
    // 1. 从 _selectedItems 查找
    const found = selectedItems.find(
      (item: any) => String(item[valueField]) === strVal,
    );
    if (found) {
      labels.push(String(found[labelField] ?? strVal));
      continue;
    }
    // 2. 从缓存查找
    const cached = selectorLabelCache.value.get(`${cachePrefix}:${strVal}`);
    if (cached !== undefined) {
      labels.push(cached);
      continue;
    }
    // 3. 未命中，标记需要加载
    uncachedIds.push(strVal);
  }

  // 触发异步加载未命中的 id
  if (uncachedIds.length > 0) {
    loadSelectorLabels(col, uncachedIds);
    return $t('common.loading');
  }

  return labels.join(', ');
}

// 子表图片列 URL 缓存
const subTableImageUrlCache = ref<Map<string, string>>(new Map());
const subTablePreviewImages = ref<string[]>([]);
const showSubTableImageViewer = ref(false);

function getFileIds(value: any): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value === 'string') return [value];
  return [];
}

function getImageUrl(fileId: string): string | undefined {
  if (!fileId) return undefined;
  const cached = subTableImageUrlCache.value.get(fileId);
  if (cached) return cached;
  getFileUrl(fileId).then((url) => {
    subTableImageUrlCache.value.set(fileId, url);
  });
  return undefined;
}

async function handleSubTableImagePreview(fileIds: string[]) {
  const urls = await Promise.all(
    fileIds.map(async (id) => {
      const cached = subTableImageUrlCache.value.get(id);
      if (cached) return cached;
      const url = await getFileUrl(id);
      subTableImageUrlCache.value.set(id, url);
      return url;
    }),
  );
  subTablePreviewImages.value = urls.filter(Boolean);
  showSubTableImageViewer.value = true;
}

// 判断是否为图片/文件类型列
function isImageColumn(col: any): boolean {
  return col.type === 'image-selector';
}

function isFileColumn(col: any): boolean {
  return col.type === 'file-selector';
}

// ========== 子表列动态选项缓存（用于只读单元格的 value→label 映射） ==========
const subTableColOptionsCache = ref<Map<string, any[]>>(new Map());

async function loadSubTableColumnOptions() {
  if (props.item.type !== 'sub-table' || !props.item.children) return;

  const selectLikeTypes = new Set([
    'select', 'radio', 'checkbox', 'cascader', 'tree-select',
  ]);

  for (const col of props.item.children) {
    if (!selectLikeTypes.has(col.type)) continue;
    const ds = col.dataSource as DataSourceConfig | undefined;
    if (!ds || ds.type === 'static') {
      if (col.options?.length) {
        subTableColOptionsCache.value.set(col.field, col.options);
      }
      continue;
    }

    try {
      let options: any[] = [];
      if (ds.type === 'dict' && ds.dictCode) {
        const resp = await requestClient.get(
          `/api/core/dict_item/by/dict_code/${ds.dictCode}`,
        );
        options = (resp || []).map((item: any) => ({
          label: item.label,
          value: item.value,
        }));
      } else if (ds.type === 'formData' && ds.formCode && ds.formLabelField && ds.formValueField) {
        const pageSize = ds.formPageSize || 100;
        const resp = await requestClient.get(
          `/api/online_dev/form-data/${ds.formCode}/list`,
          { params: { page: 1, pageSize } },
        );
        const items = resp?.items || [];
        options = items.map((item: any) => ({
          label: item[ds.formLabelField!] ?? '',
          value: item[ds.formValueField!] ?? '',
        }));
      } else if (ds.type === 'api' && ds.apiUrl) {
        const resp = await (ds.apiMethod === 'POST'
          ? requestClient.post(ds.apiUrl, ds.apiParams || {})
          : requestClient.get(ds.apiUrl, { params: ds.apiParams || {} }));
        const data = Array.isArray(resp)
          ? resp
          : resp?.list || resp?.data || [];
        options = transformOptions(data, ds);
      } else if (ds.type === 'dataSource' && ds.dataSourceCode) {
        const resp = await requestClient.get(
          `/api/core/data-source/${ds.dataSourceCode}/execute`,
        );
        const data = Array.isArray(resp)
          ? resp
          : resp?.list || resp?.data || [];
        options = transformOptions(data, ds);
      }
      if (options.length > 0) {
        subTableColOptionsCache.value.set(col.field, options);
      }
    } catch (error) {
      console.error(`加载子表列 ${col.field} 的动态选项失败:`, error);
    }
  }
}

function getSubTableColOptions(col: any): any[] {
  return subTableColOptionsCache.value.get(col.field) || col.options || [];
}

function findOptionLabel(options: any[], val: any): string | null {
  for (const opt of options) {
    if (opt.value === val) return opt.label;
    if (opt.children?.length) {
      const found = findOptionLabel(opt.children, val);
      if (found) return found;
    }
  }
  return null;
}

function findOptionPath(options: any[], val: any, path: string[] = []): string[] | null {
  for (const opt of options) {
    const currentPath = [...path, opt.label];
    if (opt.value === val) return currentPath;
    if (opt.children?.length) {
      const found = findOptionPath(opt.children, val, currentPath);
      if (found) return found;
    }
  }
  return null;
}

// 格式化单元格内容
const formatCellContent = (val: any, col: any, row?: any) => {
  if (val === null || val === undefined || val === '') return '-';

  // 日期格式化
  if (col.type === 'date') {
    return dayjs(val).format(col.props?.format || 'YYYY-MM-DD');
  }

  // 选择类组件 (Select/Radio/Checkbox)
  if (['radio', 'select', 'checkbox'].includes(col.type)) {
    const options = getSubTableColOptions(col);
    if (Array.isArray(val)) {
      return val
        .map((v) => findOptionLabel(options, v) ?? v)
        .join(', ');
    }
    return findOptionLabel(options, val) ?? val;
  }

  // 级联 / 树形选择
  if (['cascader', 'tree-select'].includes(col.type)) {
    const options = getSubTableColOptions(col);
    if (Array.isArray(val)) {
      if (col.props?.emitPath) {
        const path = val.map((v) => findOptionLabel(options, v) ?? v);
        return path.join(' / ');
      }
      return val
        .map((v) => {
          const p = findOptionPath(options, v);
          return p ? p.join(' / ') : v;
        })
        .join(', ');
    }
    const path = findOptionPath(options, val);
    return path ? path.join(' / ') : val;
  }

  // 开关
  if (col.type === 'switch') {
    return val ? $t('common.yes') : $t('common.no');
  }

  // 表单选择器 / 表格选择器
  if (['form-selector', 'table-selector'].includes(col.type)) {
    return resolveSelectorLabel(val, col, row);
  }

  return val;
};

// 子表单数据（用于卡片模式和行内模式的 draggable）
const subTableData = computed(() => {
  ensureSubTableData();
  return props.modelValue[props.item.field] || [];
});

// 获取子表列的默认值
function getColumnDefaultValue(col: any): any {
  if (col.defaultValue !== undefined && col.defaultValue !== null && col.defaultValue !== '') {
    return JSON.parse(JSON.stringify(col.defaultValue));
  }
  // 多选类型默认空数组
  if (col.props?.multiple) return [];
  return null;
}

// 子表单操作
const addRow = (item: any) => {
  if (!props.modelValue[item.field]) {
    props.modelValue[item.field] = [];
  }
  const newRow: any = {
    _id: `${Date.now()}_${Math.random()}`,
    _isEditing: true,
  };
  if (item.children) {
    item.children.forEach((col: any) => {
      newRow[col.field] = getColumnDefaultValue(col);
    });
  }
  props.modelValue[item.field].push(newRow);
};

const removeRow = (field: string, index: number) => {
  if (props.modelValue[field]) {
    props.modelValue[field].splice(index, 1);
  }
};

const copyRow = (item: any, index: number) => {
  const list = props.modelValue[item.field];
  if (list && list[index]) {
    const clone = JSON.parse(JSON.stringify(list[index]));
    clone._id = `${Date.now()}_${Math.random()}`; // 确保唯一键
    list.splice(index + 1, 0, clone);
  }
};

const moveRow = (field: string, index: number, step: number) => {
  const list = props.modelValue[field];
  if (!list) return;

  const targetIndex = index + step;
  if (targetIndex >= 0 && targetIndex < list.length) {
    const temp = list[index];
    list[index] = list[targetIndex];
    list[targetIndex] = temp;
  }
};

// 状态管理
const activeCollapse = ref<any>([]);
const activeTab = ref<string>('');
const activeStep = ref<number>(0);

watchEffect(() => {
  if (props.item.type === 'collapse' && props.item.items?.length) {
    activeCollapse.value = props.item.props.accordion
      ? props.item.items[0].name
      : props.item.items.map((i: any) => i.name);
  } else if (props.item.type === 'tabs' && props.item.items?.length) {
    activeTab.value = props.item.items[0].name;
  }
});

const visible = computed(() => {
  // 直接隐藏开关优先
  if (props.item.isHidden) return false;
  // 隐藏条件：如果 hideCondition 为真，则隐藏
  if (props.item.hideCondition) {
    try {
      const hideFunc = new Function('model', `return ${props.item.hideCondition}`);
      if (hideFunc(props.modelValue)) return false;
    } catch (error) {
      console.warn(`Hide condition error for field ${props.item.field}:`, error);
    }
  }
  // 显示条件
  if (!props.item.showCondition) return true;
  try {
    const func = new Function('model', `return ${props.item.showCondition}`);
    return func(props.modelValue);
  } catch (error) {
    console.warn(`Show condition error for field ${props.item.field}:`, error);
    return true;
  }
});

// 组件映射
const COMPONENT_MAP: Record<string, any> = {
  input: ElInput,
  textarea: ElInput,
  select: ElSelect,
  radio: ElRadioGroup,
  checkbox: ElCheckboxGroup,
  date: ElDatePicker,
  'input-number': ElInputNumber,
  time: ElTimePicker,
  switch: ElSwitch,
  slider: ElSlider,
  rate: ElRate,
  color: ElColorPicker,
  cascader: ElCascader,
  'tree-select': ElTreeSelect,
  'dept-selector': DeptSelector,
  'user-selector': UserSelector,
  'role-selector': RoleSelector,
  'post-selector': PostSelector,
  'cron-selector': CronSelector,
  'image-selector': ImageSelector,
  'file-selector': FileSelector,
  'rich-text': RichTextEditor,
  'current-user': CurrentUser,
  'current-datetime': CurrentDatetime,
  'code-generator': CodeGenerator,
  'money-input': MoneyInput,
  'formula-input': FormulaInput,
  'linked-field': LinkedField,
  'region-selector': RegionSelector,
  'ai-image-ocr': AiImageOcr,
  'table-selector': TableSelector,
  'form-selector': FormSelector,
  'signature-pad': SignaturePad,
  'qrcode-generator': QRCodeGenerator,
};

function getComponentMap(type: string) {
  return COMPONENT_MAP[type] || ElInput;
}

// 日期关联：根据配置动态生成 disabledDate 函数
const dateDisabledDate = computed(() => {
  if (props.item.type !== 'date') return undefined;
  const linkedField = props.item.props?.dateLinkedField;
  const linkedRule = props.item.props?.dateLinkedRule;
  if (!linkedField || !linkedRule) return undefined;

  return (date: Date) => {
    const linkedValue = props.modelValue?.[linkedField];
    if (!linkedValue) return false;
    const linkedDate = dayjs(linkedValue);
    if (!linkedDate.isValid()) return false;
    const d = dayjs(date);
    switch (linkedRule) {
      case 'gt': {
        // 晚于关联字段 → 禁用关联字段当天及之前
        return !d.isAfter(linkedDate, 'day');
      }
      case 'gte': {
        // 不早于关联字段 → 禁用关联字段之前
        return d.isBefore(linkedDate, 'day');
      }
      case 'lt': {
        // 早于关联字段 → 禁用关联字段当天及之后
        return !d.isBefore(linkedDate, 'day');
      }
      case 'lte': {
        // 不晚于关联字段 → 禁用关联字段之后
        return d.isAfter(linkedDate, 'day');
      }
      default: {
        return false;
      }
    }
  };
});

function getRules(item: any) {
  const itemRules: any[] = [];

  // 必填校验
  if (item.props.required) {
    // 输入类组件使用 blur 触发，选择类组件同时使用 change 和 blur 触发
    const inputTypes = ['input', 'input-number', 'textarea', 'money-input'];
    const trigger = inputTypes.includes(item.type)
      ? 'blur'
      : ['change', 'blur'];
    itemRules.push({
      required: true,
      message: `${item.label}${$t('form-design.attribute.requiredTip')}`,
      trigger,
    });
  }

  // 正则校验
  if (item.regList && item.regList.length > 0) {
    item.regList.forEach((reg: any) => {
      if (reg.pattern && reg.message) {
        try {
          // 解析正则字符串，例如 "/^...$/"
          const match = reg.pattern.match(/^\/(.+)\/([gim]*)$/);
          let regex;
          if (match) {
            regex = new RegExp(match[1], match[2]);
          } else {
            // 尝试直接创建（兼容不带斜杠的情况）
            regex = new RegExp(reg.pattern);
          }

          itemRules.push({
            pattern: regex,
            message: reg.message,
            trigger: 'blur',
          });
        } catch {
          console.error('Invalid regex:', reg.pattern);
        }
      }
    });
  }

  // 跨字段校验
  if (item.props.crossValidations && item.props.crossValidations.length > 0) {
    const dateTypes = new Set(['current-datetime', 'date']);
    const isDate = dateTypes.has(item.type);

    item.props.crossValidations.forEach((cv: any) => {
      if (!cv.targetField || !cv.operator) return;
      itemRules.push({
        validator: (_rule: any, value: any, callback: any) => {
          if (value === null || value === undefined || value === '') {
            callback();
            return;
          }
          const targetValue = props.modelValue?.[cv.targetField];
          if (
            targetValue === null ||
            targetValue === undefined ||
            targetValue === ''
          ) {
            callback();
            return;
          }

          let current: number;
          let target: number;

          if (isDate) {
            current = dayjs(value).valueOf();
            target = dayjs(targetValue).valueOf();
            if (Number.isNaN(current) || Number.isNaN(target)) {
              callback();
              return;
            }
          } else {
            current = Number(value);
            target = Number(targetValue);
            if (Number.isNaN(current) || Number.isNaN(target)) {
              callback();
              return;
            }
          }

          let pass = true;
          switch (cv.operator) {
            case 'eq': {
              pass = current === target;
              break;
            }
            case 'gt': {
              pass = current > target;
              break;
            }
            case 'gte': {
              pass = current >= target;
              break;
            }
            case 'lt': {
              pass = current < target;
              break;
            }
            case 'lte': {
              pass = current <= target;
              break;
            }
            case 'ne': {
              pass = current !== target;
              break;
            }
          }

          if (pass) {
            callback();
          } else {
            callback(
              new Error(
                cv.message ||
                  $t('form-design.attribute.crossValidation.defaultError'),
              ),
            );
          }
        },
        trigger: 'change',
      });
    });
  }

  // 唯一性校验（异步，调用后端 API）
  if (item.props.uniqueCheck && props.formCode) {
    let uniqueCheckTimer: null | ReturnType<typeof setTimeout> = null;
    itemRules.push({
      validator: (_rule: any, value: any, callback: any) => {
        if (value === null || value === undefined || value === '') {
          callback();
          return;
        }
        // 防抖：避免每次按键都请求
        if (uniqueCheckTimer) clearTimeout(uniqueCheckTimer);
        uniqueCheckTimer = setTimeout(async () => {
          try {
            const res = await checkFormDataUniqueApi(props.formCode!, {
              field: item.field,
              value: String(value),
              excludeId: props.editId,
            });
            if (res.unique) {
              callback();
            } else {
              callback(
                new Error(
                  item.props.uniqueCheckMessage ||
                    $t('form-design.attribute.uniqueCheck.defaultMessage'),
                ),
              );
            }
          } catch {
            // 接口异常时不阻塞提交
            callback();
          }
        }, 500);
      },
      trigger: 'blur',
    });
  }

  return itemRules;
}
</script>

<template>
  <!-- 栅格布局渲染 -->
  <ElRow v-if="item.type === 'grid' && visible" :gutter="item.props.gutter">
    <ElCol v-for="(col, index) in item.columns" :key="index" :span="col.span">
      <PreviewItem
        v-for="child in col.children"
        :key="child.id"
        :item="child"
        :model-value="modelValue"
        :is-edit="isEdit"
        :field-permissions="fieldPermissions"
        :form-code="formCode"
        :edit-id="editId"
      />
    </ElCol>
  </ElRow>

  <!-- 间距占位 -->
  <div
    v-else-if="item.type === 'spacer' && visible"
    :style="{ height: `${item.props?.height || 24}px` }"
  ></div>

  <!-- 标题组件 -->
  <div
    v-else-if="item.type === 'title' && visible"
    class="mb-3 flex items-center gap-2 rounded-[8px] py-2.5"
    :style="{
      backgroundColor: `var(--el-color-${item.props?.theme || 'primary'}-light-9)`,
      borderBottom: item.props?.showBorder
        ? `1px solid var(--el-color-${item.props?.theme || 'primary'}-light-5)`
        : 'none',
    }"
  >
    <div
      v-if="item.props?.showBar"
      class="h-4 w-1 rounded-sm"
      :style="{
        backgroundColor: `var(--el-color-${item.props?.theme || 'primary'})`,
      }"
    ></div>
    <span
      class="font-bold"
      :style="{
        fontSize: `${item.props?.fontSize || 15}px`,
        color: `var(--el-color-${item.props?.theme || 'primary'})`,
      }"
      >{{ item.props?.text || item.label }}</span>
  </div>

  <!-- 分割线 -->
  <div v-else-if="item.type === 'divider' && visible" class="py-2">
    <ElDivider v-bind="item.props">
      {{
        item.label !== $t('form-design.material.components.divider')
          ? item.label
          : ''
      }}
    </ElDivider>
  </div>

  <!-- 折叠面板 -->
  <div v-else-if="item.type === 'collapse' && visible" class="mb-4">
    <ElCollapse v-bind="item.props" v-model="activeCollapse">
      <ElCollapseItem
        v-for="(subItem, index) in item.items"
        :key="index"
        :title="subItem.title"
        :name="subItem.name"
      >
        <PreviewItem
          v-for="child in subItem.children"
          :key="child.id"
          :item="child"
          :model-value="modelValue"
          :is-edit="isEdit"
          :field-permissions="fieldPermissions"
        />
      </ElCollapseItem>
    </ElCollapse>
  </div>

  <!-- 标签页 -->
  <div v-else-if="item.type === 'tabs' && visible" class="mb-4">
    <ElTabs v-bind="item.props" v-model="activeTab">
      <ElTabPane
        v-for="(subItem, index) in item.items"
        :key="index"
        :label="subItem.label"
        :name="subItem.name"
      >
        <PreviewItem
          v-for="child in subItem.children"
          :key="child.id"
          :item="child"
          :model-value="modelValue"
          :is-edit="isEdit"
          :field-permissions="fieldPermissions"
        />
      </ElTabPane>
    </ElTabs>
  </div>

  <!-- 步骤组件 -->
  <div v-else-if="item.type === 'steps' && visible" class="mb-4">
    <ElSteps
      :active="activeStep"
      :direction="item.props?.direction || 'horizontal'"
      :align-center="item.props?.alignCenter"
      :simple="item.props?.simple"
      :finish-status="item.props?.finishStatus || 'success'"
      :process-status="item.props?.processStatus || 'process'"
      class="mb-4"
    >
      <ElStep
        v-for="(subItem, index) in item.items"
        :key="index"
        :title="subItem.title"
        :description="subItem.description"
      />
    </ElSteps>
    <div
      v-for="(subItem, index) in item.items"
      :key="subItem.name"
      v-show="activeStep === index"
    >
      <PreviewItem
        v-for="child in subItem.children"
        :key="child.id"
        :item="child"
        :model-value="modelValue"
        :is-edit="isEdit"
        :field-permissions="fieldPermissions"
        :form-code="formCode"
        :edit-id="editId"
      />
    </div>
    <div class="mt-4 flex justify-end gap-2">
      <ElButton v-if="activeStep > 0" @click="activeStep--">
        {{ $t('form-design.attribute.layout.prevStep') }}
      </ElButton>
      <ElButton
        v-if="item.items && activeStep < item.items.length - 1"
        type="primary"
        @click="activeStep++"
      >
        {{ $t('form-design.attribute.layout.nextStep') }}
      </ElButton>
    </div>
  </div>

  <!-- 警告提示 -->
  <div v-else-if="item.type === 'alert' && visible" class="mb-4">
    <ElAlert v-bind="item.props" />
  </div>

  <!-- 时间线 -->
  <div v-else-if="item.type === 'timeline' && visible" class="mb-4">
    <ElTimeline v-bind="item.props">
      <ElTimelineItem
        v-for="(subItem, index) in item.items"
        :key="index"
        :timestamp="subItem.timestamp"
        :type="subItem.type"
        :icon="subItem.icon"
        :color="subItem.color"
      >
        {{ subItem.content }}
      </ElTimelineItem>
    </ElTimeline>
  </div>

  <!-- 子表单 -->
  <div v-else-if="item.type === 'sub-table' && visible" class="mb-4">
    <div
      class="mb-2 flex items-center justify-between text-sm font-bold text-gray-700"
    >
      <span>{{ item.label }}</span>
      <span v-if="item.props.maxRows" class="text-xs font-normal text-gray-400">
        ({{ $t('form-design.attribute.maxRows') }}: {{ item.props.maxRows }})
      </span>
    </div>

    <!-- 表格模式 -->
    <template
      v-if="!item.props.displayMode || item.props.displayMode === 'table'"
    >
      <ElTable
        :data="displayData"
        border
        :stripe="item.props.stripe !== false"
        :style="{ width: '100%' }"
        :show-summary="item.props.summary"
        :summary-method="item.props.summary ? getSubTableSummaryMethod(item) : undefined"
      >
        <ElTableColumn
          type="index"
          width="50"
          v-if="item.props.showIndex"
          align="center"
          fixed="left"
        >
          <template #default="scope">
            {{ getRealIndex(scope.$index) + 1 }}
          </template>
        </ElTableColumn>

        <ElTableColumn
          v-for="col in item.children"
          :key="col.field"
          :prop="col.field"
          :label="col.label"
          :width="col.props.columnWidth"
          :min-width="150"
          :align="col.props.columnAlign || 'left'"
          :fixed="col.props.columnFixed"
        >
          <template #default="scope">
            <!-- 编辑模式：显示组件 -->
            <PreviewItem
              v-if="scope.row._isEditing"
              :item="col"
              :model-value="scope.row"
              :is-table="true"
              :prop-prefix="`${item.field}.${getRealIndex(scope.$index)}.`"
              :sub-table-rows="modelValue[item.field]"
              :sub-table-item="item"
            />
            <!-- 查看模式：图片类型 -->
            <template v-else-if="isImageColumn(col)">
              <div
                v-if="getFileIds(scope.row[col.field]).length > 0"
                class="flex items-center gap-1"
              >
                <template
                  v-for="fileId in getFileIds(scope.row[col.field]).slice(0, 1)"
                  :key="fileId"
                >
                  <ElImage
                    v-if="getImageUrl(fileId)"
                    :src="getImageUrl(fileId)"
                    fit="cover"
                    :style="{
                      width: '32px',
                      height: '32px',
                      cursor: 'pointer',
                      borderRadius: '4px',
                    }"
                    :preview-src-list="[]"
                    @click="
                      handleSubTableImagePreview(
                        getFileIds(scope.row[col.field]),
                      )
                    "
                  />
                  <div
                    v-else
                    class="flex items-center justify-center"
                    :style="{
                      width: '32px',
                      height: '32px',
                      borderRadius: '4px',
                      backgroundColor: 'var(--el-fill-color-light)',
                      animation: 'el-skeleton-loading 1.4s ease infinite',
                    }"
                  />
                </template>
                <ElTooltip
                  v-if="getFileIds(scope.row[col.field]).length > 1"
                  :content="`共 ${getFileIds(scope.row[col.field]).length} 张图片`"
                  placement="top"
                >
                  <span class="text-xs text-gray-400">
                    +{{ getFileIds(scope.row[col.field]).length - 1 }}
                  </span>
                </ElTooltip>
              </div>
              <span v-else>-</span>
            </template>
            <!-- 查看模式：文件类型 -->
            <template v-else-if="isFileColumn(col)">
              <FileListCell
                v-if="getFileIds(scope.row[col.field]).length > 0"
                :file-ids="getFileIds(scope.row[col.field])"
              />
              <span v-else>-</span>
            </template>
            <!-- 查看模式：显示格式化后的值 -->
            <span
              v-else
              class="block truncate"
              :title="formatCellContent(scope.row[col.field], col, scope.row)"
            >
              {{ formatCellContent(scope.row[col.field], col, scope.row) }}
            </span>
          </template>
        </ElTableColumn>

        <ElTableColumn
          :label="$t('common.action')"
          :width="getOperationColumnWidth(item)"
          fixed="right"
          align="center"
        >
          <template #default="scope">
            <div class="flex items-center justify-center gap-1">
              <!-- 编辑模式下显示保存和取消 -->
              <template v-if="scope.row._isEditing">
                <ElButton
                  type="success"
                  link
                  size="small"
                  @click="saveRowEdit(scope.row)"
                >
                  {{ $t('common.save') }}
                </ElButton>
                <ElButton
                  type="info"
                  link
                  size="small"
                  @click="
                    cancelRowEdit(
                      scope.row,
                      item.field,
                      getRealIndex(scope.$index),
                    )
                  "
                >
                  {{ $t('common.cancel') }}
                </ElButton>
              </template>

              <!-- 查看模式下显示编辑和其他操作 -->
              <template v-else>
                <ElButton
                  type="primary"
                  link
                  size="small"
                  @click="startRowEdit(scope.row)"
                >
                  {{ $t('common.edit') }}
                </ElButton>

                <template v-if="item.props.showSortButtons">
                  <ElButton
                    circle
                    size="small"
                    :disabled="getRealIndex(scope.$index) === 0"
                    @click="moveRow(item.field, getRealIndex(scope.$index), -1)"
                  >
                    <ElIcon><Top /></ElIcon>
                  </ElButton>
                  <ElButton
                    circle
                    size="small"
                    :disabled="
                      getRealIndex(scope.$index) ===
                      (modelValue[item.field] || []).length - 1
                    "
                    @click="moveRow(item.field, getRealIndex(scope.$index), 1)"
                  >
                    <ElIcon><Bottom /></ElIcon>
                  </ElButton>
                </template>

                <ElButton
                  v-if="item.props.copyable"
                  type="primary"
                  link
                  size="small"
                  @click="copyRow(item, getRealIndex(scope.$index))"
                >
                  {{ $t('common.copy') }}
                </ElButton>

                <ElButton
                  type="danger"
                  link
                  size="small"
                  v-if="item.props.deletable !== false"
                  :disabled="
                    (modelValue[item.field] || []).length <=
                    (item.props.minRows || 0)
                  "
                  @click="removeRow(item.field, getRealIndex(scope.$index))"
                >
                  {{ $t('common.delete') }}
                </ElButton>
              </template>
            </div>
          </template>
        </ElTableColumn>
      </ElTable>
    </template>

    <!-- 卡片模式 -->
    <template v-else-if="item.props.displayMode === 'card'">
      <div class="flex flex-col gap-4">
        <draggable
          :list="subTableData"
          item-key="_id"
          handle=".drag-handle"
          :disabled="!item.props.sortable"
          :animation="200"
        >
          <template #item="{ element: row, index }">
            <div
              class="group relative mb-4 rounded-lg border bg-gray-50 p-4 transition-shadow hover:shadow-sm"
            >
              <div class="mb-4 flex items-center justify-between border-b pb-2">
                <div class="flex items-center gap-2">
                  <ElIcon
                    v-if="item.props.sortable"
                    class="drag-handle cursor-move text-gray-400 hover:text-blue-500"
                  >
                    <Rank />
                  </ElIcon>
                  <span class="font-bold text-gray-600"
                    >#{{ getRealIndex(index) + 1 }}</span
                  >
                </div>
                <div class="flex gap-2">
                  <!-- 编辑模式下显示保存和取消 -->
                  <template v-if="row._isEditing">
                    <ElButton
                      type="success"
                      link
                      size="small"
                      @click="saveRowEdit(row)"
                    >
                      {{ $t('common.save') }}
                    </ElButton>
                    <ElButton
                      type="info"
                      link
                      size="small"
                      @click="
                        cancelRowEdit(row, item.field, getRealIndex(index))
                      "
                    >
                      {{ $t('common.cancel') }}
                    </ElButton>
                  </template>

                  <!-- 查看模式下显示编辑和其他操作 -->
                  <template v-else>
                    <ElButton
                      type="primary"
                      link
                      size="small"
                      @click="startRowEdit(row)"
                    >
                      {{ $t('common.edit') }}
                    </ElButton>

                    <ElButton
                      type="primary"
                      link
                      size="small"
                      v-if="item.props.copyable"
                      @click="copyRow(item, getRealIndex(index))"
                    >
                      {{ $t('common.copy') }}
                    </ElButton>
                    <ElButton
                      type="danger"
                      link
                      size="small"
                      v-if="item.props.deletable !== false"
                      :disabled="
                        (modelValue[item.field] || []).length <=
                        (item.props.minRows || 0)
                      "
                      @click="removeRow(item.field, getRealIndex(index))"
                    >
                      {{ $t('common.delete') }}
                    </ElButton>
                  </template>
                </div>
              </div>

              <ElRow :gutter="20">
                <ElCol
                  v-for="col in item.children"
                  :key="col.field"
                  :span="24"
                  class="mb-4 last:mb-0"
                >
                  <div class="flex flex-col">
                    <span class="mb-1 text-sm text-gray-500">{{
                      col.label
                    }}</span>
                    <!-- 编辑模式 -->
                    <PreviewItem
                      v-if="row._isEditing"
                      :item="{ ...col, label: '' }"
                      :model-value="row"
                      :prop-prefix="`${item.field}.${getRealIndex(index)}.`"
                      :sub-table-rows="modelValue[item.field]"
                      :sub-table-item="item"
                    />
                    <!-- 查看模式：图片类型 -->
                    <div
                      v-else-if="isImageColumn(col)"
                      class="min-h-[32px] rounded border border-gray-100 bg-gray-50 p-2 text-sm"
                    >
                      <template
                        v-if="getFileIds(row[col.field]).length > 0"
                      >
                        <div class="flex items-center gap-1">
                          <template
                            v-for="fileId in getFileIds(row[col.field]).slice(0, 1)"
                            :key="fileId"
                          >
                            <ElImage
                              v-if="getImageUrl(fileId)"
                              :src="getImageUrl(fileId)"
                              fit="cover"
                              :style="{
                                width: '32px',
                                height: '32px',
                                cursor: 'pointer',
                                borderRadius: '4px',
                              }"
                              :preview-src-list="[]"
                              @click="handleSubTableImagePreview(getFileIds(row[col.field]))"
                            />
                            <div
                              v-else
                              :style="{
                                width: '32px',
                                height: '32px',
                                borderRadius: '4px',
                                backgroundColor: 'var(--el-fill-color-light)',
                                animation: 'el-skeleton-loading 1.4s ease infinite',
                              }"
                            />
                          </template>
                          <span
                            v-if="getFileIds(row[col.field]).length > 1"
                            class="text-xs text-gray-400"
                          >
                            +{{ getFileIds(row[col.field]).length - 1 }}
                          </span>
                        </div>
                      </template>
                      <span v-else>-</span>
                    </div>
                    <!-- 查看模式：文件类型 -->
                    <div
                      v-else-if="isFileColumn(col)"
                      class="min-h-[32px] rounded border border-gray-100 bg-gray-50 p-2 text-sm"
                    >
                      <FileListCell
                        v-if="getFileIds(row[col.field]).length > 0"
                        :file-ids="getFileIds(row[col.field])"
                      />
                      <span v-else>-</span>
                    </div>
                    <!-- 查看模式 -->
                    <div
                      v-else
                      class="min-h-[32px] rounded border border-gray-100 bg-gray-50 p-2 text-sm"
                    >
                      {{ formatCellContent(row[col.field], col, row) }}
                    </div>
                  </div>
                </ElCol>
              </ElRow>
            </div>
          </template>
        </draggable>
      </div>
    </template>

    <!-- 行内模式 -->
    <template v-else-if="item.props.displayMode === 'inline'">
      <div class="flex flex-col gap-4">
        <draggable
          :list="subTableData"
          item-key="_id"
          handle=".drag-handle"
          :disabled="!item.props.sortable"
          :animation="200"
        >
          <template #item="{ element: row, index }">
            <div
              class="mb-4 flex items-center gap-4 rounded-lg border bg-white p-4 transition-shadow last:mb-0 hover:shadow-sm"
            >
              <div
                v-if="item.props.sortable"
                class="drag-handle flex-shrink-0 cursor-move text-gray-400 hover:text-blue-500"
              >
                <ElIcon size="16"><Rank /></ElIcon>
              </div>
              <span
                v-if="item.props.showIndex"
                class="flex h-6 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 text-center text-xs font-medium text-gray-500"
                >{{ getRealIndex(index) + 1 }}</span
              >

              <div class="flex-1 overflow-x-auto">
                <div
                  class="grid items-center gap-4"
                  :style="{
                    gridTemplateColumns: `repeat(${item.children.length}, auto)`,
                    minWidth: `${Math.max(item.children.length * 180, 100)}px`,
                  }"
                >
                  <div
                    v-for="col in item.children"
                    :key="col.field"
                    class="min-w-[160px]"
                  >
                    <div
                      class="mb-1 truncate text-xs text-gray-500"
                      :title="col.label"
                    >
                      {{ col.label }}
                    </div>
                    <PreviewItem
                      :item="{ ...col, label: '' }"
                      :model-value="row"
                      :prop-prefix="`${item.field}.${getRealIndex(index)}.`"
                      :sub-table-rows="modelValue[item.field]"
                      :sub-table-item="item"
                    />
                  </div>
                </div>
              </div>

              <div
                class="ml-2 flex flex-shrink-0 gap-2"
                v-if="item.props.deletable !== false || item.props.copyable"
              >
                <ElButton
                  circle
                  size="small"
                  v-if="item.props.copyable"
                  @click="copyRow(item, getRealIndex(index))"
                  :title="$t('common.copy')"
                >
                  <ElIcon><CopyDocument /></ElIcon>
                </ElButton>
                <ElButton
                  type="danger"
                  circle
                  size="small"
                  v-if="item.props.deletable !== false"
                  :disabled="
                    (modelValue[item.field] || []).length <=
                    (item.props.minRows || 0)
                  "
                  @click="removeRow(item.field, getRealIndex(index))"
                  :title="$t('common.delete')"
                >
                  <ElIcon><Delete /></ElIcon>
                </ElButton>
              </div>
            </div>
          </template>
        </draggable>
      </div>
    </template>

    <div
      class="mt-2 flex items-center justify-between"
      v-if="item.props.addable !== false || hasPagination"
    >
      <div class="flex gap-2">
        <ElButton
          v-if="
            item.props.addable !== false &&
            (!item.props.maxRows ||
              (modelValue[item.field] || []).length < item.props.maxRows)
          "
          type="primary"
          plain
          size="small"
          @click="addRow(item)"
        >
          <ElIcon class="mr-1"><Plus /></ElIcon>
          {{
            item.props.addButtonText || $t('form-design.attribute.addOption')
          }}
        </ElButton>
        <ElButton
          v-if="(modelValue[item.field] || []).some((r: any) => r._isEditing)"
          type="success"
          plain
          size="small"
          @click="saveAllRows(item.field)"
        >
          <ElIcon class="mr-1"><Check /></ElIcon>
          {{ $t('form-design.attribute.saveAll') }}
        </ElButton>
      </div>

      <!-- 分页组件 -->
      <ElPagination
        v-if="hasPagination"
        v-model:current-page="currentPage"
        v-model:page-size="item.props.pageSize"
        :page-sizes="[5, 10, 20, 50]"
        :total="(modelValue[item.field] || []).length"
        layout="total, sizes, prev, pager, next, jumper"
        background
        small
        @current-change="handleCurrentChange"
      />
    </div>
  </div>

  <!-- 脱敏选择器组件：显示禁用的 input -->
  <ElFormItem
    v-else-if="visible && !isFieldHidden && isMaskedSelector"
    :label="item.hideLabel ? undefined : item.label"
    :label-width="item.hideLabel ? '0px' : undefined"
    :prop="fieldProp"
    :class="{ '!mb-0': isTable }"
  >
    <ElInput
      :model-value="maskedSelectorDisplayValue || undefined"
      disabled
      :placeholder="maskedSelectorDisplayValue ? '' : '脱敏字段禁止编辑'"
      :style="{ width: item.props?.width || '100%' }"
      class="w-full"
    />
  </ElFormItem>

  <!-- 普通组件渲染 -->
  <ElFormItem
    v-else-if="visible && !isFieldHidden"
    :label="
      item.props?.showHelp &&
      item.props?.helpDisplayMode === 'icon' &&
      item.props?.helpText
        ? undefined
        : item.hideLabel
          ? undefined
          : item.label
    "
    :label-width="item.hideLabel ? '0px' : undefined"
    :label-position="item.labelPosition || undefined"
    :prop="fieldProp"
    :rules="getRules(item)"
    :class="{ '!mb-0': isTable }"
  >
    <template
      v-if="
        item.props?.showHelp &&
        item.props?.helpDisplayMode === 'icon' &&
        item.props?.helpText &&
        !item.hideLabel
      "
      #label
    >
      <span class="inline-flex items-center">
        {{ item.label }}
        <ElTooltip
          :content="item.props.helpText"
          placement="top"
          :show-after="200"
        >
          <CircleHelp
            class="ml-1 cursor-help text-[var(--el-text-color-placeholder)]"
            :size="14"
          />
        </ElTooltip>
      </span>
    </template>
    <component
      :is="getComponentMap(item.type)"
      :model-value="
        item.type === 'qrcode-generator' && item.props?.dataSource === 'static'
          ? modelValue[item.field] || item.defaultValue
          : modelValue[item.field]
      "
      @update:model-value="
        (val: any) => {
          // expandMultipleToRows 模式：拦截数组赋值，由 select-item 事件展开为多行
          if (
            item.type === 'form-selector' &&
            item.props?.expandMultipleToRows &&
            Array.isArray(val)
          ) {
            return;
          }
          let finalVal = val;
          if (item.type === 'input' && typeof val === 'string') {
            if (item.props?.autoUppercase) {
              finalVal = val.toUpperCase();
            } else if (item.props?.autoLowercase) {
              finalVal = val.toLowerCase();
            }
          }
          modelValue[item.field] = finalVal;
          if (item.type === 'select') {
            handleSelectChange(item.field, val);
          }
        }
      "
      v-bind="item.props"
      :options="
        ['cascader'].includes(item.type)
          ? effectiveOptions
          : item.type === 'table-selector'
            ? item.options
            : undefined
      "
      :props="item.type === 'cascader' && cascaderElProps ? cascaderElProps : undefined"
      :data="item.type === 'tree-select' ? effectiveOptions : undefined"
      :lazy="item.type === 'tree-select' && isTreeSelectLazy ? true : undefined"
      :load="item.type === 'tree-select' && isTreeSelectLazy ? treeSelectLoadFn : undefined"
      :node-key="item.type === 'tree-select' ? 'value' : undefined"
      :loading="isLoadingOptions || isPreloadingLabels"
      :filterable="item.type === 'select' ? ((hasSearchParam || hasFormDataSearch) ? true : item.props?.filterable) : item.props?.filterable"
      :remote="item.type === 'select' && (hasSearchParam || hasFormDataSearch) ? true : undefined"
      :remote-method="item.type === 'select' ? (hasSearchParam ? handleRemoteSearch : (hasFormDataSearch ? handleFormDataRemoteSearch : undefined)) : undefined"
      :is-edit="item.type === 'code-generator' ? isEdit : undefined"
      :disabled="item.props?.disabled || isFieldReadonly"
      :style="{ width: item.props?.width || '100%' }"
      :ai-ocr-config="
        item.type === 'ai-image-ocr' ? item.aiOcrConfig : undefined
      "
      :form-data="
        [
          'ai-image-ocr',
          'formula-input',
          'linked-field',
          'qrcode-generator',
        ].includes(item.type)
          ? modelValue
          : undefined
      "
      :formula="item.type === 'formula-input' ? item.props?.formula : undefined"
      :source-field="
        item.type === 'linked-field' ? item.props?.sourceField : undefined
      "
      :display-field="
        item.type === 'linked-field' ? item.props?.displayField : undefined
      "
      :auto-current-user="
        item.type === 'user-selector' ? item.props?.autoCurrentUser : undefined
      "
      :disabled-date="item.type === 'date' ? dateDisabledDate : undefined"
      :data-source-type="
        item.type === 'table-selector' ? item.dataSource?.type : undefined
      "
      :dict-code="
        item.type === 'table-selector' ? item.dataSource?.dictCode : undefined
      "
      :data-source-code="
        item.type === 'table-selector'
          ? item.dataSource?.dataSourceCode
          : undefined
      "
      :form-code="
        item.type === 'table-selector'
          ? item.dataSource?.formCode
          : item.type === 'form-selector'
            ? item.formSelectorConfig?.formCode
            : undefined
      "
      :label-field="
        item.type === 'table-selector'
          ? item.dataSource?.formLabelField
          : item.type === 'form-selector'
            ? item.formSelectorConfig?.labelField
            : undefined
      "
      :value-field="
        item.type === 'table-selector'
          ? item.dataSource?.formValueField
          : item.type === 'form-selector'
            ? item.formSelectorConfig?.valueField
            : undefined
      "
      :dialog-title="
        item.type === 'table-selector'
          ? item.tableSelectorConfig?.dialogTitle
          : item.type === 'form-selector'
            ? item.props?.dialogTitle
            : undefined
      "
      :dialog-width="
        item.type === 'table-selector'
          ? item.tableSelectorConfig?.dialogWidth
          : item.type === 'form-selector'
            ? item.props?.dialogWidth
            : undefined
      "
      :columns="
        item.type === 'table-selector'
          ? item.tableSelectorConfig?.columns
          : item.type === 'form-selector'
            ? item.formSelectorConfig?.columns
            : undefined
      "
      :search-fields="
        item.type === 'table-selector'
          ? item.tableSelectorConfig?.searchFields
          : item.type === 'form-selector'
            ? item.formSelectorConfig?.searchFields
            : undefined
      "
      :collapse-tags="
        item.type === 'table-selector'
          ? item.tableSelectorConfig?.collapseTags
          : undefined
      "
      :expand-multiple-to-rows="
        item.type === 'form-selector' && !!item.props?.expandMultipleToRows
      "
      :external-selected-values="
        item.type === 'form-selector' && item.props?.expandMultipleToRows && subTableRows
          ? getExternalSelectedValues(item.field)
          : undefined
      "
      class="w-full"
      @fill-fields="
        item.type === 'ai-image-ocr' ? handleAiOcrFillFields($event) : undefined
      "
      @select-item="
        ['table-selector', 'form-selector'].includes(item.type)
          ? handleSelectItem(item.field, $event)
          : undefined
      "
    >
      <!-- 前缀后缀 (input 类型使用 prepend/append) -->
      <template
        v-if="
          item.type === 'input' &&
          item.props?.showAddon &&
          item.props?.addonBefore
        "
        #prepend
      >
        {{ item.props.addonBefore }}
      </template>
      <template
        v-if="
          item.type === 'input' &&
          item.props?.showAddon &&
          item.props?.addonAfter
        "
        #append
      >
        {{ item.props.addonAfter }}
      </template>
      <!-- 前缀后缀 (input-number 类型使用 prefix/suffix) -->
      <template
        v-if="
          item.type === 'input-number' &&
          item.props?.showAddon &&
          item.props?.addonBefore
        "
        #prefix
      >
        {{ item.props.addonBefore }}
      </template>
      <template
        v-if="
          item.type === 'input-number' &&
          item.props?.showAddon &&
          item.props?.addonAfter
        "
        #suffix
      >
        {{ item.props.addonAfter }}
      </template>
      <!-- 特殊处理选项 -->
      <template v-if="['select', 'radio', 'checkbox'].includes(item.type)">
        <template v-if="item.type === 'select'">
          <ElOption
            v-for="opt in effectiveOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          >
            <div class="flex w-full items-center justify-between">
              <span>{{ opt.label }}</span>
              <span
                v-if="opt.desc"
                class="ml-2 text-xs text-[var(--el-text-color-secondary)]"
                >{{ opt.desc }}</span
              >
            </div>
          </ElOption>
        </template>

        <template v-else-if="item.type === 'radio'">
          <template v-if="item.props?.buttonStyle">
            <ElRadioButton
              v-for="opt in effectiveOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </ElRadioButton>
          </template>
          <template v-else>
            <ElRadio
              v-for="opt in effectiveOptions"
              :key="opt.value"
              :label="opt.value"
            >
              {{ opt.label }}
            </ElRadio>
          </template>
        </template>

        <template v-else-if="item.type === 'checkbox'">
          <ElCheckbox
            v-for="opt in effectiveOptions"
            :key="opt.value"
            :label="opt.value"
          >
            {{ opt.label }}
          </ElCheckbox>
        </template>
      </template>
    </component>
    <div
      v-if="
        item.props?.showHelp &&
        item.props?.helpText &&
        (!item.props?.helpDisplayMode || item.props?.helpDisplayMode === 'text')
      "
      class="mt-1 text-xs leading-normal text-[var(--el-text-color-placeholder)]"
    >
      {{ item.props.helpText }}
    </div>
  </ElFormItem>

  <!-- 子表图片预览 -->
  <Teleport to="body">
    <ElImageViewer
      v-if="showSubTableImageViewer"
      :url-list="subTablePreviewImages"
      @close="showSubTableImageViewer = false"
    />
  </Teleport>
</template>
