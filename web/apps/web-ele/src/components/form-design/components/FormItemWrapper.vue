<script setup lang="ts">
import type {
  DataSourceConfig,
  FormItemSchema,
} from '../store/formDesignStore';

import { $t } from '@vben/locales';
import { CircleHelp } from '@vben/icons';
import { computed, nextTick, ref, watch, watchEffect } from 'vue';
import { useDebounceFn } from '@vueuse/core';

import {
  Bottom,
  CopyDocument,
  Delete,
  DocumentCopy,
  ScaleToOriginal,
  Top,
} from '@element-plus/icons-vue';
import {
  ElAlert,
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
  ElInput,
  ElInputNumber,
  ElOption,
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
  ElTabPane,
  ElTabs,
  ElTimeline,
  ElTimelineItem,
  ElTimePicker,
  ElTooltip,
  ElTreeSelect,
} from 'element-plus';
import draggable from 'vuedraggable';

import { requestClient } from '#/api/request';

import AiImageOcr from '../../zq-form/ai-image-ocr/ai-image-ocr.vue';
import CodeGenerator from '../../zq-form/code-generator/code-generator.vue';
import CronSelector from '../../zq-form/cron-selector/cron-selector.vue';
import CurrentDatetime from '../../zq-form/current-datetime/current-datetime.vue';
import CurrentUser from '../../zq-form/current-user/current-user.vue';
import DeptSelector from '../../zq-form/dept-selector/dept-selector.vue';
import FileSelector from '../../zq-form/file-selector/file-selector.vue';
import FormulaInput from '../../zq-form/formula-input/formula-input.vue';
import ImageSelector from '../../zq-form/image-selector/image-selector.vue';
import LinkedField from '../../zq-form/linked-field/linked-field.vue';
import MoneyInput from '../../zq-form/money-input/money-input.vue';
import PostSelector from '../../zq-form/post-selector/post-selector.vue';
import RegionSelector from '../../zq-form/region-selector/region-selector.vue';
import RichTextEditor from '../../zq-form/rich-text-editor/rich-text-editor.vue';
import RoleSelector from '../../zq-form/role-selector/role-selector.vue';
import UserSelector from '../../zq-form/user-selector/user-selector.vue';
import TableSelector from '../../zq-form/table-selector/table-selector.vue';
import FormSelector from '../../zq-form/form-selector/form-selector.vue';
import SignaturePad from '../../zq-form/signature-pad/signature-pad.vue';
import QRCodeGenerator from '../../zq-form/qrcode-generator/qrcode-generator.vue';
import { useFormDesignStore } from '../store/formDesignStore';

defineOptions({
  name: 'FormItemWrapper',
});

// 移动端不支持的组件类型
const MOBILE_UNSUPPORTED_TYPES = ['timeline', 'current-datetime', 'money-input', 'ai-image-ocr', 'cron-selector', 'color'];

const props = withDefaults(
  defineProps<{
    active: boolean;
    interactive?: boolean;
    previewMode?: 'mobile' | 'pc';
    schema: FormItemSchema;
  }>(),
  {
    interactive: true,
    previewMode: 'pc',
  },
);

const isMobileUnsupported = computed(() => {
  return props.previewMode === 'mobile' && MOBILE_UNSUPPORTED_TYPES.includes(props.schema.type);
});

const emit = defineEmits(['delete']);
const store = useFormDesignStore();
const dummyValue = ref(null); // 仅用于展示，不需要真实绑定数据

// 动态选项数据
const dynamicOptions = ref<any[]>([]);

// 获取实际使用的选项（静态或动态）
const effectiveOptions = computed(() => {
  const dataSource = props.schema.dataSource as DataSourceConfig | undefined;
  if (!dataSource || dataSource.type === 'static') {
    return props.schema.options || [];
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
  }
}

// 加载API数据
async function loadApiOptions(config: DataSourceConfig) {
  if (!config.apiUrl) return;

  try {
    let response;
    response = await (config.apiMethod === 'POST'
      ? requestClient.post(config.apiUrl, config.apiParams || {})
      : requestClient.get(config.apiUrl, { params: config.apiParams || {} }));

    const data = Array.isArray(response)
      ? response
      : response?.list || response?.data || [];
    dynamicOptions.value = transformOptions(data, config);
  } catch (error) {
    console.error($t('form-design.message.loadApiError'), error);
    dynamicOptions.value = [];
  }
}

// 搜索关键词（用于 search 类型的参数）
const searchKeyword = ref('');

// 构建数据源参数
function buildDataSourceParams(config: DataSourceConfig): Record<string, any> {
  const params: Record<string, any> = {};
  
  if (!config.dataSourceParams?.length) return params;
  
  for (const paramConfig of config.dataSourceParams) {
    let value: any;
    
    switch (paramConfig.valueSource) {
      case 'fixed':
        // 优先使用用户设置的固定值，只有在用户未设置时才使用数据源默认值
        if (paramConfig.fixedValue !== undefined && paramConfig.fixedValue !== '') {
          value = paramConfig.fixedValue;
        } else if (paramConfig.default !== undefined) {
          value = paramConfig.default;
        }
        break;
      case 'field':
        // 设计器预览模式下，字段值不可用，使用默认值
        if (paramConfig.default !== undefined) {
          value = paramConfig.default;
        }
        break;
      case 'search':
        // 搜索模式：从 searchKeyword 获取值，不使用默认值
        value = searchKeyword.value || undefined;
        break;
    }
    
    // 只有有值时才添加参数
    if (value !== undefined && value !== '') {
      params[paramConfig.name] = value;
    } else if (paramConfig.valueSource !== 'search' && paramConfig.required && paramConfig.default !== undefined) {
      // 搜索模式不使用默认值
      params[paramConfig.name] = paramConfig.default;
    }
  }
  
  return params;
}

// 检查是否有 search 类型的参数（用于启用远程搜索）
const hasSearchParam = computed(() => {
  const dataSource = props.schema.dataSource as DataSourceConfig | undefined;
  if (dataSource?.type === 'dataSource' && dataSource.dataSourceParams?.length) {
    return dataSource.dataSourceParams.some(p => p.valueSource === 'search');
  }
  return false;
});

// 远程搜索处理函数
const handleRemoteSearch = useDebounceFn((query: string) => {
  const dataSource = props.schema.dataSource as DataSourceConfig | undefined;
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
    dynamicOptions.value = [];
    return;
  }

  try {
    // 构建参数
    const params = buildDataSourceParams(config);
    
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
      return;
    }

    // 如果组件配置了字段映射，则使用组件的配置
    // 否则使用默认的 label/value 字段（数据源应该已经处理好字段映射）
    const labelField = config.labelField || 'label';
    const valueField = config.valueField || 'value';

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
      });
    }
  } catch (error) {
    console.error($t('form-design.message.loadDataSourceError'), error);
    dynamicOptions.value = [];
  }
}

// 表单数据搜索关键词
const formDataSearchKeyword = ref('');

// 检查是否启用表单数据远程搜索
const hasFormDataSearch = computed(() => {
  const dataSource = props.schema.dataSource as DataSourceConfig | undefined;
  return dataSource?.type === 'formData' && dataSource.formEnableSearch === true;
});

// 表单数据远程搜索处理函数
const handleFormDataRemoteSearch = useDebounceFn((query: string) => {
  const dataSource = props.schema.dataSource as DataSourceConfig | undefined;
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
  if (!config.formCode || !config.formLabelField || !config.formValueField) return;
  // 级联/树形选择懒加载模式下不做全量加载
  if (['cascader', 'tree-select'].includes(props.schema.type) && config.formLazyLoad === true) return;


  try {
    // 构建查询参数，使用配置的分页大小（默认100）
    const pageSize = config.formPageSize || 100;
    const params: Record<string, any> = { page: 1, pageSize };

    // 如果启用了搜索且有搜索关键词，添加搜索参数（支持 label 和描述字段混合搜索）
    if (config.formEnableSearch && formDataSearchKeyword.value) {
      const searchFields = [config.formLabelField];
      if (config.formDescField) {
        searchFields.push(config.formDescField);
      }
      params.search = formDataSearchKeyword.value;
      params.search_fields = searchFields.join(',');
    }

    const response = await requestClient.get(
      `/api/online_dev/form-data/${config.formCode}/list`,
      { params }
    );

    const items = response?.items || [];

    // 级联/树形选择 + 表单数据源 + 配置了父节点字段：构建树形结构
    if (['cascader', 'tree-select'].includes(props.schema.type) && config.formCode && config.formParentField) {
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
      dynamicOptions.value = items.map((item: any) => ({
        label: item[config.formLabelField!] ?? '',
        value: item[config.formValueField!] ?? '',
        desc: config.formDescField ? (item[config.formDescField] ?? '') : '',
        _raw: item, // 保留完整的原始数据
      })).filter((opt: any) => opt.value !== '' && opt.value !== null && opt.value !== undefined);
    }

  } catch (error) {
    console.error('加载表单数据失败:', error);
    dynamicOptions.value = [];
  }
}

// 监听 dataSource 变化，自动加载数据
watch(
  () => props.schema.dataSource,
  (dataSource) => {
    if (!dataSource) {
      dynamicOptions.value = [];
      return;
    }

    if (dataSource.type === 'dict' && dataSource.dictCode) {
      loadDictOptions(dataSource.dictCode);
    } else if (dataSource.type === 'api') {
      loadApiOptions(dataSource);
    } else if (dataSource.type === 'dataSource' && dataSource.dataSourceCode) {
      loadDataSourceOptions(dataSource);
    } else if (dataSource.type === 'formData' && dataSource.formCode) {
      loadFormDataOptions(dataSource);
    }
  },
  { immediate: true, deep: true },
);

// 双击编辑状态
const isEditing = ref(false);
const editingLabel = ref('');
const labelInputRef = ref<HTMLInputElement | null>(null);

// 右键菜单状态
const contextMenuVisible = ref(false);
const contextMenuPosition = ref({ x: 0, y: 0 });

// 多选状态
const isMultiSelected = computed(() => {
  return store.isSelected(props.schema.id) && !props.active;
});

// 布局组件状态管理
const activeCollapse = ref<any>([]);
const activeTab = ref<string>('');
const activeStep = ref<number>(0);

watchEffect(() => {
  const items = props.schema.items || [];
  if (props.schema.type === 'collapse' && items.length > 0) {
    // 设计模式下，默认展开所有，方便拖拽
    // 如果是手风琴模式，则只能展开一个，默认第一个
    if (props.schema.props.accordion) {
      // 如果当前没选中，或者选中的不在 items 里，重置为第一个
      const current = activeCollapse.value;
      const firstItem = items[0];
      if (firstItem) {
        const first = firstItem.name;
        if (!current || (Array.isArray(current) && current.length === 0)) {
          activeCollapse.value = first;
        }
      }
    } else {
      // 非手风琴模式，全展开
      activeCollapse.value = items.map((i: any) => i.name);
    }
  } else if (
    props.schema.type === 'tabs' &&
    items.length > 0 && // 如果没有选中的标签，默认选中第一个
    (!activeTab.value || !items.find((i: any) => i.name === activeTab.value))
  ) {
    const firstItem = items[0];
    if (firstItem) {
      activeTab.value = firstItem.name || '';
    }
  }
});

const handleSelect = (event: MouseEvent) => {
  const multiSelect = event.ctrlKey || event.metaKey;
  const rangeSelect = event.shiftKey;
  store.setActive(props.schema.id, multiSelect, rangeSelect);
};

// 双击编辑标签
const handleDoubleClick = () => {
  // 布局组件不支持双击编辑
  if (['collapse', 'divider', 'grid', 'tabs'].includes(props.schema.type)) {
    return;
  }
  isEditing.value = true;
  editingLabel.value = props.schema.label;
  nextTick(() => {
    labelInputRef.value?.focus();
    labelInputRef.value?.select();
  });
};

const handleLabelBlur = () => {
  if (editingLabel.value.trim()) {
    store.updateItemLabel(props.schema.id, editingLabel.value.trim());
  }
  isEditing.value = false;
};

const handleLabelKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    handleLabelBlur();
  } else if (event.key === 'Escape') {
    isEditing.value = false;
  }
};

// 右键菜单
const handleContextMenu = (event: MouseEvent) => {
  event.preventDefault();
  store.setActive(props.schema.id);
  contextMenuPosition.value = { x: event.clientX, y: event.clientY };
  contextMenuVisible.value = true;

  // 点击其他地方关闭菜单
  const closeMenu = () => {
    contextMenuVisible.value = false;
    document.removeEventListener('click', closeMenu);
  };
  setTimeout(() => {
    document.addEventListener('click', closeMenu);
  }, 0);
};

const handleMenuCommand = (command: string) => {
  contextMenuVisible.value = false;
  switch (command) {
    case 'copy': {
      store.copyToClipboard([props.schema.id]);
      break;
    }
    case 'delete': {
      store.deleteItem(props.schema.id);
      break;
    }
    case 'duplicate': {
      store.copyItem(props.schema.id);
      break;
    }
    case 'moveDown': {
      store.moveItem(props.schema.id, 'down');
      break;
    }
    case 'moveUp': {
      store.moveItem(props.schema.id, 'up');
      break;
    }
    case 'paste': {
      store.pasteFromClipboard();
      break;
    }
  }
};

const handleCopy = () => {
  store.copyItem(props.schema.id);
};

const handleDeleteSelf = () => {
  // 调用 store 的递归删除
  store.deleteItem(props.schema.id);
};

const handleDelete = (id: string) => {
  store.deleteItem(id);
};

const handleAdd = (_evt: any) => {
  // 可以在这里处理新增组件的选中逻辑
  // 这里的 evt.item 是 DOM 元素，evt.newIndex 是索引
  // 我们需要获取对应的数据对象来 setActive
  // 由于 draggable v-model 绑定的是 col.children
  // 我们可以尝试获取刚刚添加的 item
  // 但在这里比较难直接获取到数据对象，除非去 col.children[newIndex] 找
  // 暂时忽略，用户手动点击选中即可
};

// 组件映射表
const COMPONENT_MAP: Record<string, any> = {
  input: ElInput,
  textarea: ElInput, // Element Plus 中 input type="textarea"
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
  'region-selector': RegionSelector,
  'ai-image-ocr': AiImageOcr,
  'rich-text': RichTextEditor,
  'current-user': CurrentUser,
  'current-datetime': CurrentDatetime,
  'code-generator': CodeGenerator,
  'money-input': MoneyInput,
  'formula-input': FormulaInput,
  'linked-field': LinkedField,
  'table-selector': TableSelector,
  'form-selector': FormSelector,
  'signature-pad': SignaturePad,
  'qrcode-generator': QRCodeGenerator,
};

function getComponentMap(type: string) {
  return COMPONENT_MAP[type] || ElInput;
}
</script>

<template>
  <div
    class="form-item-wrapper group relative mb-2 cursor-move border border-dashed border-[var(--el-border-color)] p-2 hover:border-[var(--el-color-primary)] hover:bg-[var(--el-color-primary-light-9)]"
    :class="{
      'is-active bg-[var(--el-color-primary-light-9)] ring-2 ring-[var(--el-color-primary)]':
        active,
      'is-selected bg-[var(--el-color-primary-light-9)] ring-1 ring-[var(--el-color-primary)]':
        isMultiSelected && !active,
    }"
    @click.stop="handleSelect"
    @dblclick.stop="handleDoubleClick"
    @contextmenu.prevent="handleContextMenu"
  >
    <!-- 移动端不支持的组件占位提示 -->
    <div
      v-if="isMobileUnsupported"
      class="flex items-center gap-2 rounded border border-dashed border-[var(--el-color-warning)] bg-[var(--el-color-warning-light-9)] px-3 py-2 text-sm text-[var(--el-color-warning)]"
    >
      <ElIcon :size="14"><ScaleToOriginal /></ElIcon>
      <span>{{ schema.label || schema.type }} · {{ $t('form-design.mobileUnsupported') }}</span>
    </div>

    <!-- 栅格布局渲染 -->
    <div v-else-if="schema.type === 'grid'" class="grid-layout">
      <ElRow :gutter="schema.props.gutter" class="h-full min-h-[60px]">
        <ElCol
          v-for="(col, index) in schema.columns"
          :key="index"
          :span="col.span"
          class="min-h-[60px] border border-dashed border-[var(--el-border-color)] p-2"
        >
          <draggable
            v-model="col.children"
            group="form-design"
            item-key="id"
            class="h-full min-h-[50px]"
            ghost-class="ghost"
            :animation="200"
            @add="handleAdd"
          >
            <template #item="{ element }">
              <FormItemWrapper
                :schema="element"
                :active="store.activeId === element.id"
                @delete="handleDelete"
              />
            </template>
          </draggable>
        </ElCol>
      </ElRow>
    </div>

    <!-- 间距占位 -->
    <div
      v-else-if="schema.type === 'spacer'"
      :style="{ height: `${schema.props?.height || 24}px` }"
      class="flex items-center justify-center border border-dashed border-[var(--el-border-color-lighter)]"
    >
      <span class="text-xs text-[var(--el-text-color-placeholder)]">{{ schema.props?.height || 24 }}px</span>
    </div>

    <!-- 标题组件 -->
    <div
      v-else-if="schema.type === 'title'"
      class="flex items-center gap-2 py-2.5 rounded-[8px] mb-3"
      :style="{
        backgroundColor: `var(--el-color-${schema.props?.theme || 'primary'}-light-9)`,
        borderBottom: schema.props?.showBorder ? `1px solid var(--el-color-${schema.props?.theme || 'primary'}-light-5)` : 'none',
      }"
    >
      <div
        v-if="schema.props?.showBar"
        class="h-4 w-1 rounded-sm"
        :style="{ backgroundColor: `var(--el-color-${schema.props?.theme || 'primary'})` }"
      />
      <span
        class="font-bold"
        :style="{
          fontSize: `${schema.props?.fontSize || 15}px`,
          color: `var(--el-color-${schema.props?.theme || 'primary'})`,
        }"
      >{{ schema.props?.text || schema.label }}</span>
    </div>

    <!-- 分割线 -->
    <div v-else-if="schema.type === 'divider'" class="py-2">
      <ElDivider v-bind="schema.props">
        {{ schema.label !== $t('form-design.material.components.divider') ? schema.label : '' }}
      </ElDivider>
    </div>

    <!-- 折叠面板 -->
    <div v-else-if="schema.type === 'collapse'" class="mb-2">
      <ElCollapse
        v-bind="schema.props"
        v-model="activeCollapse"
        class="border border-dashed border-[var(--el-border-color)] p-1"
      >
        <ElCollapseItem
          v-for="(item, index) in schema.items"
          :key="index"
          :title="item.title"
          :name="item.name"
        >
          <div class="min-h-[50px] p-2">
            <draggable
              v-model="item.children"
              group="form-design"
              item-key="id"
              class="min-h-[50px]"
              ghost-class="ghost"
              :animation="200"
              @add="handleAdd"
            >
              <template #item="{ element }">
                <FormItemWrapper
                  :schema="element"
                  :active="store.activeId === element.id"
                  @delete="handleDelete"
                />
              </template>
            </draggable>
          </div>
        </ElCollapseItem>
      </ElCollapse>
    </div>

    <!-- 标签页 -->
    <div v-else-if="schema.type === 'tabs'" class="mb-2">
      <ElTabs
        v-bind="schema.props"
        v-model="activeTab"
        class="border border-dashed border-[var(--el-border-color)] p-1"
      >
        <ElTabPane
          v-for="(item, index) in schema.items"
          :key="index"
          :label="item.label"
          :name="item.name"
        >
          <div class="min-h-[50px] p-2">
            <draggable
              v-model="item.children"
              group="form-design"
              item-key="id"
              class="min-h-[50px]"
              ghost-class="ghost"
              :animation="200"
              @add="handleAdd"
            >
              <template #item="{ element }">
                <FormItemWrapper
                  :schema="element"
                  :active="store.activeId === element.id"
                  @delete="handleDelete"
                />
              </template>
            </draggable>
          </div>
        </ElTabPane>
      </ElTabs>
    </div>

    <!-- 步骤组件 -->
    <div v-else-if="schema.type === 'steps'" class="mb-2">
      <div class="border border-dashed border-[var(--el-border-color)] p-3">
        <ElSteps
          :active="activeStep"
          :direction="schema.props?.direction || 'horizontal'"
          :align-center="schema.props?.alignCenter"
          :simple="schema.props?.simple"
          :finish-status="schema.props?.finishStatus || 'success'"
          :process-status="schema.props?.processStatus || 'process'"
          class="mb-4"
        >
          <ElStep
            v-for="(item, index) in schema.items"
            :key="index"
            :title="item.title"
            :description="item.description"
            class="cursor-pointer"
            @click.native="activeStep = index as number"
          />
        </ElSteps>
        <div
          v-for="(item, index) in schema.items"
          :key="item.name"
          v-show="activeStep === index"
          class="min-h-[50px] rounded border border-dashed border-[var(--el-border-color-lighter)] p-2"
        >
          <draggable
            v-model="item.children"
            group="form-design"
            item-key="id"
            class="min-h-[50px]"
            ghost-class="ghost"
            :animation="200"
            @add="handleAdd"
          >
            <template #item="{ element }">
              <FormItemWrapper
                :schema="element"
                :active="store.activeId === element.id"
                @delete="handleDelete"
              />
            </template>
          </draggable>
        </div>
      </div>
    </div>

    <!-- 警告提示 -->
    <div v-else-if="schema.type === 'alert'" class="py-2">
      <ElAlert v-bind="schema.props as any" />
    </div>

    <!-- 时间线 -->
    <div v-else-if="schema.type === 'timeline'" class="p-2">
      <ElTimeline v-bind="schema.props">
        <ElTimelineItem
          v-for="(item, index) in schema.items"
          :key="index"
          :timestamp="item.timestamp"
          :type="item.type as any"
          :icon="item.icon"
          :color="item.color"
        >
          {{ item.content }}
        </ElTimelineItem>
      </ElTimeline>
    </div>

    <!-- 子表单 -->
    <div v-else-if="schema.type === 'sub-table'" class="mb-2">
      <div
        class="rounded border border-dashed border-[var(--el-border-color)] bg-[var(--el-fill-color-light)] p-2"
      >
        <div
          class="mb-2 flex justify-between text-sm font-bold text-[var(--el-text-color-primary)]"
        >
          <span>{{ $t('form-design.material.components.subTable') }}: {{ schema.label }}</span>
          <span
            class="text-xs font-normal text-[var(--el-text-color-placeholder)]"
            >{{ $t('form-design.attribute.addSubTableFirstTip') }}</span>
        </div>

        <!-- 水平拖拽区域，模拟列 -->
        <draggable
          v-model="schema.children"
          :group="{
            name: 'sub-table-fields',
            pull: false,
            put: ['form-design', 'sub-table-fields'],
          }"
          item-key="id"
          class="flex min-h-[100px] flex-row items-start gap-2 overflow-x-auto rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] p-2"
          ghost-class="ghost"
          :animation="200"
          @add="handleAdd"
        >
          <template #item="{ element }">
            <div
              class="min-w-[180px] rounded border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-light)]"
            >
              <FormItemWrapper
                :schema="element"
                :active="store.activeId === element.id"
                @delete="handleDelete"
              />
            </div>
          </template>
        </draggable>
      </div>
    </div>

    <!-- 普通组件渲染 -->
    <ElFormItem
      v-else
      :label="(schema.props?.showHelp && schema.props?.helpDisplayMode === 'icon' && schema.props?.helpText) ? undefined : (schema.hideLabel ? undefined : schema.label)"
      :label-width="schema.hideLabel ? '0px' : undefined"
      :label-position="schema.labelPosition || undefined"
      :required="schema.props.required"
      :prop="schema.field"
      :class="{ 'pointer-events-none': !interactive }"
    >
      <template v-if="schema.props?.showHelp && schema.props?.helpDisplayMode === 'icon' && schema.props?.helpText && !schema.hideLabel" #label>
        <span class="inline-flex items-center">
          {{ schema.label }}
          <ElTooltip :content="schema.props.helpText" placement="top" :show-after="200">
            <CircleHelp class="ml-1 cursor-help text-[var(--el-text-color-placeholder)]" :size="14" />
          </ElTooltip>
        </span>
      </template>
      <!-- 动态组件渲染 -->
      <component
        :is="getComponentMap(schema.type)"
        v-bind="schema.props"
        :model-value="schema.type === 'qrcode-generator' && schema.props?.dataSource === 'static' ? schema.defaultValue : dummyValue"
        :options="
          ['cascader'].includes(schema.type) ? effectiveOptions : (schema.type === 'table-selector' ? schema.options : undefined)
        "
        :data="
          ['tree-select'].includes(schema.type) ? effectiveOptions : undefined
        "
        :node-key="schema.type === 'tree-select' ? 'value' : undefined"
        :render-after-expand="schema.type === 'tree-select' ? false : undefined"
        :ai-ocr-config="schema.type === 'ai-image-ocr' ? schema.aiOcrConfig : undefined"
        :formula="schema.type === 'formula-input' ? schema.props?.formula : undefined"
        :source-field="schema.type === 'linked-field' ? schema.props?.sourceField : undefined"
        :display-field="schema.type === 'linked-field' ? schema.props?.displayField : undefined"
        :data-source-type="schema.type === 'table-selector' ? schema.dataSource?.type : undefined"
        :dict-code="schema.type === 'table-selector' ? schema.dataSource?.dictCode : undefined"
        :data-source-code="schema.type === 'table-selector' ? schema.dataSource?.dataSourceCode : undefined"
        :form-code="schema.type === 'table-selector' ? schema.dataSource?.formCode : (schema.type === 'form-selector' ? schema.formSelectorConfig?.formCode : undefined)"
        :label-field="schema.type === 'table-selector' ? schema.dataSource?.formLabelField : (schema.type === 'form-selector' ? schema.formSelectorConfig?.labelField : undefined)"
        :value-field="schema.type === 'table-selector' ? schema.dataSource?.formValueField : (schema.type === 'form-selector' ? schema.formSelectorConfig?.valueField : undefined)"
        :dialog-title="schema.type === 'table-selector' ? schema.tableSelectorConfig?.dialogTitle : (schema.type === 'form-selector' ? schema.props?.dialogTitle : undefined)"
        :dialog-width="schema.type === 'table-selector' ? schema.tableSelectorConfig?.dialogWidth : (schema.type === 'form-selector' ? schema.props?.dialogWidth : undefined)"
        :columns="schema.type === 'table-selector' ? schema.tableSelectorConfig?.columns : undefined"
        :search-fields="schema.type === 'table-selector' ? schema.tableSelectorConfig?.searchFields : undefined"
        :collapse-tags="schema.type === 'table-selector' ? schema.tableSelectorConfig?.collapseTags : undefined"
        :filterable="schema.type === 'select' ? ((hasSearchParam || hasFormDataSearch) ? true : schema.props?.filterable) : schema.props?.filterable"
        :remote="schema.type === 'select' && (hasSearchParam || hasFormDataSearch) ? true : undefined"
        :remote-method="schema.type === 'select' ? (hasSearchParam ? handleRemoteSearch : (hasFormDataSearch ? handleFormDataRemoteSearch : undefined)) : undefined"
        :style="{
          width:
            schema.type !== 'switch' && schema.props.width
              ? schema.props.width
              : undefined,
        }"
      >
        <!-- 前缀后缀 (input 类型使用 prepend/append) -->
        <template v-if="schema.type === 'input' && schema.props?.showAddon && schema.props?.addonBefore" #prepend>
          {{ schema.props.addonBefore }}
        </template>
        <template v-if="schema.type === 'input' && schema.props?.showAddon && schema.props?.addonAfter" #append>
          {{ schema.props.addonAfter }}
        </template>
        <!-- 前缀后缀 (input-number 类型使用 prefix/suffix) -->
        <template v-if="schema.type === 'input-number' && schema.props?.showAddon && schema.props?.addonBefore" #prefix>
          {{ schema.props.addonBefore }}
        </template>
        <template v-if="schema.type === 'input-number' && schema.props?.showAddon && schema.props?.addonAfter" #suffix>
          {{ schema.props.addonAfter }}
        </template>
        <!-- 特殊处理 Select/Radio/Checkbox 的选项 -->
        <template v-if="['select', 'radio', 'checkbox'].includes(schema.type)">
          <template v-if="schema.type === 'select'">
            <ElOption
              v-for="opt in effectiveOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            >
              <div class="flex w-full items-center justify-between">
                <span>{{ opt.label }}</span>
                <span v-if="opt.desc" class="ml-2 text-xs text-[var(--el-text-color-secondary)]">{{ opt.desc }}</span>
              </div>
            </ElOption>
          </template>

          <template v-else-if="schema.type === 'radio'">
            <template v-if="schema.props?.buttonStyle">
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

          <template v-else-if="schema.type === 'checkbox'">
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
        v-if="schema.props?.showHelp && schema.props?.helpText && (!schema.props?.helpDisplayMode || schema.props?.helpDisplayMode === 'text')"
        class="mt-1 text-xs leading-normal text-[var(--el-text-color-placeholder)]"
      >
        {{ schema.props.helpText }}
      </div>
    </ElFormItem>

    <!-- 双击编辑标签输入框 -->
    <div
      v-if="isEditing"
      class="absolute inset-0 z-30 flex items-center justify-center bg-[var(--el-bg-color)] bg-opacity-90"
      @click.stop
    >
      <input
        ref="labelInputRef"
        v-model="editingLabel"
        class="w-3/4 rounded border border-[var(--el-color-primary)] px-2 py-1 text-sm outline-none focus:ring-2 focus:ring-[var(--el-color-primary)]"
        @blur="handleLabelBlur"
        @keydown="handleLabelKeydown"
      />
    </div>

    <!-- 操作按钮（选中或悬停时显示） -->
    <div
      class="action-bar translate-y-1/1 absolute bottom-0 right-0 z-20 items-center rounded bg-[var(--el-color-primary-light-9)] shadow-sm backdrop-blur-sm"
      :class="active ? 'flex' : 'hidden group-hover:flex'"
    >
      <div
        class="flex cursor-pointer items-center justify-center rounded p-1 text-[var(--el-text-color-regular)] transition-all hover:bg-[var(--el-color-primary-light-8)] hover:text-[var(--el-color-primary)]"
        :title="$t('form-design.attribute.moveUp')"
        @click.stop="handleMenuCommand('moveUp')"
      >
        <ElIcon :size="14"><Top /></ElIcon>
      </div>
      <div
        class="flex cursor-pointer items-center justify-center rounded p-1 text-[var(--el-text-color-regular)] transition-all hover:bg-[var(--el-color-primary)]-light-8)] hover:text-[var(--el-color-primary)]"
        :title="$t('form-design.attribute.moveDown')"
        @click.stop="handleMenuCommand('moveDown')"
      >
        <ElIcon :size="14"><Bottom /></ElIcon>
      </div>
      <div
        class="flex cursor-pointer items-center justify-center rounded p-1 text-[var(--el-color-primary)] transition-all hover:bg-[var(--el-color-primary-light-8)] hover:text-[var(--el-color-primary-dark-2)]"
        :title="$t('form-design.copy')"
        @click.stop="handleCopy"
      >
        <ElIcon :size="14"><CopyDocument /></ElIcon>
      </div>
      <div
        class="flex cursor-pointer items-center justify-center rounded p-1 text-[var(--el-color-danger)] transition-all hover:bg-[var(--el-color-danger-light-8)] hover:text-[var(--el-color-danger-dark-2)]"
        :title="$t('form-design.delete')"
        @click.stop="handleDeleteSelf"
      >
        <ElIcon :size="14"><Delete /></ElIcon>
      </div>
    </div>

    <!-- 右键菜单 -->
    <Teleport to="body">
    <div
      v-if="contextMenuVisible"
      class="fixed z-[9999] min-w-[120px] rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)] py-1 shadow-lg"
      :style="{
        left: `${contextMenuPosition.x}px`,
        top: `${contextMenuPosition.y}px`,
      }"
    >
      <div
        class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--el-fill-color-light)]"
        @click="handleMenuCommand('moveUp')"
      >
        <ElIcon :size="14"><Top /></ElIcon>
        <span>{{ $t('form-design.attribute.moveUp') }}</span>
      </div>
      <div
        class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--el-fill-color-light)]"
        @click="handleMenuCommand('moveDown')"
      >
        <ElIcon :size="14"><Bottom /></ElIcon>
        <span>{{ $t('form-design.attribute.moveDown') }}</span>
      </div>
      <div class="my-1 border-t border-[var(--el-border-color)]"></div>
      <div
        class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--el-fill-color-light)]"
        @click="handleMenuCommand('copy')"
      >
        <ElIcon :size="14"><DocumentCopy /></ElIcon>
        <span>{{ $t('form-design.copy') }}</span>
      </div>
      <div
        class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--el-fill-color-light)]"
        @click="handleMenuCommand('paste')"
      >
        <ElIcon :size="14"><ScaleToOriginal /></ElIcon>
        <span>{{ $t('form-design.paste') }}</span>
      </div>
      <div
        class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm hover:bg-[var(--el-fill-color-light)]"
        @click="handleMenuCommand('duplicate')"
      >
        <ElIcon :size="14"><CopyDocument /></ElIcon>
        <span>{{ $t('form-design.attribute.duplicate') }}</span>
      </div>
      <div class="my-1 border-t border-[var(--el-border-color)]"></div>
      <div
        class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm text-[var(--el-color-danger)] hover:bg-[var(--el-fill-color-light)]"
        @click="handleMenuCommand('delete')"
      >
        <ElIcon :size="14"><Delete /></ElIcon>
        <span>{{ $t('form-design.delete') }}</span>
      </div>
    </div>
  </Teleport>
</div>
</template>

<style scoped>
/* 让所有表单组件不可交互，只做展示 */
.pointer-events-none :deep(*) {
  pointer-events: none !important;
}

.ghost {
  position: relative;
  height: 4px;
  overflow: hidden;
  background: var(--el-color-primary-light-9);
  border-top: 2px solid var(--el-color-primary);
}

.ghost::after {
  display: block;
  content: '';
  background: var(--el-bg-color);
}
</style>
