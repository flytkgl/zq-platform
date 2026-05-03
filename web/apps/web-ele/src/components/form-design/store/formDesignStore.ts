import { computed, nextTick, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { defineStore } from 'pinia';
import { v4 as uuidv4 } from 'uuid';

// 数据来源类型
export type DataSourceType =
  | 'api'
  | 'dataSource'
  | 'dependent'
  | 'dict'
  | 'formData'
  | 'static';

// 表单数据过滤条件
export interface FormDataFilter {
  targetField: string; // 目标表单的过滤字段（如 customer_id）
  sourceField: string; // 当前表单的依赖字段（如 customer）
  filterType:
    | 'eq'
    | 'gt'
    | 'gte'
    | 'in'
    | 'like'
    | 'lt'
    | 'lte'
    | 'ne'
    | 'not_null' // 过滤类型
    | 'null';
}

// 数据源参数配置（用于配置数据源参数的值来源）
export interface DataSourceParamConfig {
  name: string; // 参数名
  label?: string; // 参数显示名
  type?: 'boolean' | 'float' | 'integer' | 'string'; // 参数类型
  required?: boolean; // 是否必填
  default?: any; // 默认值
  // 值来源配置
  valueSource: 'fixed' | 'field' | 'search'; // fixed=固定值, field=表单字段, search=搜索输入
  fixedValue?: any; // 固定值（valueSource=fixed时使用）
  sourceField?: string; // 来源字段名（valueSource=field时使用）
}

// 数据来源配置
export interface DataSourceConfig {
  type: DataSourceType;
  // 字典模式
  dictCode?: string;
  // API模式
  apiUrl?: string;
  apiMethod?: 'GET' | 'POST';
  labelField?: string; // 显示字段映射
  valueField?: string; // 值字段映射
  descField?: string; // 描述字段映射
  childrenField?: string; // 子节点字段映射（级联/树形）
  apiParams?: Record<string, any>; // 额外参数
  // 依赖字段模式
  dependField?: string; // 依赖的字段名
  dependParamName?: string; // 传递给接口的参数名
  // 数据源模式（使用系统配置的数据源）
  dataSourceCode?: string; // 数据源编码
  dataSourceParams?: DataSourceParamConfig[]; // 数据源参数配置
  // 表单数据模式
  formCode?: string; // 表单编码
  formLabelField?: string; // 显示字段
  formValueField?: string; // 值字段
  formDescField?: string; // 描述字段
  formFilters?: FormDataFilter[]; // 过滤条件列表
  formPageSize?: number; // 分页大小（默认100）
  formEnableSearch?: boolean; // 是否启用远程搜索
  formParentField?: string; // 父节点字段（级联组件使用，默认 parent_id）
  formLazyLoad?: boolean; // 是否懒加载（级联组件使用，默认 true）
  // 对象转选项模式（当API返回单个对象时，将对象属性转为选项）
  objectToOptions?: boolean; // 是否启用对象转选项
  objectExcludeFields?: string[]; // 排除的字段列表
  objectLabelMaxLength?: number; // 标签最大长度（超出截断显示）
}

// 表格选择器列配置
export interface TableSelectorColumn {
  field: string;
  label: string;
  width?: number;
}

// 表格选择器配置
export interface TableSelectorConfig {
  dialogTitle?: string; // 弹窗标题
  dialogWidth?: string; // 弹窗宽度
  columns?: TableSelectorColumn[]; // 显示列配置
  searchFields?: string[]; // 搜索字段列表
  collapseTags?: boolean; // 多选时是否折叠标签
}

// AI OCR 字段映射配置
export interface OcrFieldMapping {
  source: string; // Function返回的字段名
  target: string; // 表单字段名
  transform?: string; // 转换规则
}

// AI OCR 结构化输出字段定义（与LLM节点SchemaField一致）
export interface OcrSchemaField {
  name: string;
  type: string;
  description: string;
  required: boolean;
  items?: OcrSchemaField; // array 类型的元素定义
  properties?: OcrSchemaField[]; // object 类型的子属性
  enum?: string[]; // 枚举值（仅 string 类型）
  default?: any; // 默认值
}

// AI 文件识别支持的文件类型
export type AiFileType = 'all' | 'excel' | 'image' | 'pdf' | 'text' | 'word';

// AI OCR 预设模板类型
export type OcrTemplateType =
  | 'business_license'
  | 'contract'
  | 'custom'
  | 'id_card'
  | 'invoice'
  | 'receipt';

// AI OCR 配置
export interface AiOcrConfig {
  enabled: boolean; // 是否启用
  templateType: OcrTemplateType; // 预设模板类型
  acceptFileTypes: AiFileType[]; // 接受的文件类型
  outputSchema: OcrSchemaField[]; // 结构化输出字段定义
  fieldMapping: OcrFieldMapping[]; // 字段映射
  confirmMode: 'auto' | 'manual'; // 填充模式：自动/手动确认
  customPrompt?: string; // 自定义提示词
}

export interface FormItemSchema {
  id: string;
  type: string;
  field: string;
  label: string;
  icon?: string;
  props: Record<string, any>;
  rules?: any[];
  // 新增正则校验列表
  regList?: { message: string; pattern: string }[];
  // 显隐控制表达式，例如: model.field_abc === '1'
  showCondition?: string;
  // 隐藏条件表达式，例如: model.field_abc === '1'
  hideCondition?: string;
  // 是否隐藏（直接隐藏开关）
  isHidden?: boolean;
  // 是否隐藏Label
  hideLabel?: boolean;
  // 单组件 Label 对齐方式（覆盖表单全局设置）
  labelPosition?: '' | 'left' | 'right' | 'top';
  // 默认值
  defaultValue?: any;
  // 静态选项数据
  options?: { children?: any[]; label: string; value: any }[];
  // 数据来源配置
  dataSource?: DataSourceConfig;
  // AI OCR 配置（用于 ai-image-ocr 组件）
  aiOcrConfig?: AiOcrConfig;
  // 表格选择器配置（用于 table-selector 组件）
  tableSelectorConfig?: TableSelectorConfig;
  // 表单选择器配置（用于 form-selector 组件）
  formSelectorConfig?: {
    columns?: any[];
    formCode?: string;
    labelField?: string;
    searchFields?: any[];
    valueField?: string;
  };
  // 直接子项，用于 sub-table 等容器组件
  children?: FormItemSchema[];
  columns?: { children: FormItemSchema[]; span: number }[];
  // 折叠面板/标签页的子项配置
  items?: {
    children?: FormItemSchema[];
    color?: string;
    content?: string;
    description?: string;
    icon?: string;
    label?: string;
    name?: string;
    timestamp?: string;
    title?: string;
    type?: string;
  }[];
}

// 表字段定义
export interface TableField {
  name: string;
  type: string;
  comment: string;
  nullable: boolean;
  isPrimaryKey: boolean;
  maxLength?: number; // 最大长度 (varchar/char)
  precision?: number; // 数值精度
  scale?: number; // 小数位数
}

// 表配置定义
export interface TableConfig {
  id: string;
  type: 'main' | 'sub';
  tableName: string;
  alias: string;
  foreignKey?: string;
  relatedField?: string;
  relationType?: 'one-to-many' | 'one-to-one';
  fields: TableField[];
}

export const useFormDesignStore = defineStore('form-design', () => {
  const activeId = ref<null | string>(null);
  // 多选支持
  const selectedIds = ref<Set<string>>(new Set());
  // 剪贴板
  const clipboard = ref<FormItemSchema[]>([]);
  // 预览模式：pc | mobile
  const previewMode = ref<'mobile' | 'pc'>('pc');
  const togglePreviewMode = () => {
    previewMode.value = previewMode.value === 'pc' ? 'mobile' : 'pc';
  };

  // 数据源配置（从第一步传入）
  const dataSource = ref<{
    mainTable: null | TableConfig;
    subTables: TableConfig[];
  }>({
    mainTable: null,
    subTables: [],
  });

  const formConf = ref({
    labelWidth: 100,
    labelPosition: 'top' as 'left' | 'right' | 'top',
    size: 'default' as 'default' | 'large' | 'small',
    // 表单容器样式
    formPadding: 20, // 表单内边距（兼容旧数据）
    formPaddingTop: 20,
    formPaddingRight: 20,
    formPaddingBottom: 20,
    formPaddingLeft: 20,
    formPaddingLinked: true, // 上下联动、左右联动
    formMargin: 0, // 表单外边距（兼容旧数据）
    formMarginTop: 0,
    formMarginRight: 0,
    formMarginBottom: 0,
    formMarginLeft: 0,
    formMarginLinked: true, // 上下联动、左右联动
    formWidth: '100%', // 表单宽度
    formMaxWidth: '', // 表单最大宽度
    // 表单项间距
    itemSpacing: 18, // 表单项之间的间距
    // 表单背景
    formBackground: '', // 表单背景色
    formBorder: false, // 是否显示边框
    formBorderRadius: 4, // 边框圆角
    formShadow: false, // 是否显示阴影
    // 禁用状态
    disabled: false, // 全局禁用
    items: [] as FormItemSchema[],
  });

  // 历史记录相关
  const history = ref<string[]>([]);
  const historyIndex = ref(-1);
  const isTimeTravel = ref(false); // 防止 undo/redo 触发 watcher

  // 拖拽状态
  const isDragging = ref(false);
  const setDragging = (val: boolean) => {
    isDragging.value = val;
  };

  // 记录快照
  const recordSnapshot = () => {
    if (isTimeTravel.value) return;

    // 如果当前不在历史记录末尾，先删除后面的记录
    if (historyIndex.value < history.value.length - 1) {
      history.value.splice(historyIndex.value + 1);
    }

    history.value.push(JSON.stringify(formConf.value));
    historyIndex.value = history.value.length - 1;

    // 限制历史记录长度，例如最多 20 步
    if (history.value.length > 20) {
      history.value.shift();
      historyIndex.value--;
    }
  };

  // 初始化记录
  // recordSnapshot(); // 不要在定义时立即调用，因为 formConf 还是初始值，可以在 mounted 或首次变化时触发

  // 监听 formConf 变化
  watch(
    formConf,
    () => {
      recordSnapshot();
    },
    { deep: true },
  );

  const canUndo = computed(() => historyIndex.value > 0);
  const canRedo = computed(() => historyIndex.value < history.value.length - 1);

  const undo = () => {
    if (!canUndo.value) return;

    isTimeTravel.value = true;
    historyIndex.value--;
    const snapshot = history.value[historyIndex.value];
    if (snapshot) {
      formConf.value = JSON.parse(snapshot);
    }

    // 恢复选中状态 (简单处理：如果当前选中的组件在 undo 后不存在了，则取消选中)
    if (activeId.value) {
      // TODO: 检查 activeId 是否存在于新的 formConf 中
    }

    nextTick(() => {
      isTimeTravel.value = false;
    });
  };

  const redo = () => {
    if (!canRedo.value) return;

    isTimeTravel.value = true;
    historyIndex.value++;
    const snapshot = history.value[historyIndex.value];
    if (snapshot) {
      formConf.value = JSON.parse(snapshot);
    }

    nextTick(() => {
      isTimeTravel.value = false;
    });
  };

  function setActive(
    id: null | string,
    multiSelect = false,
    rangeSelect = false,
  ) {
    if (!id) {
      activeId.value = null;
      selectedIds.value.clear();
      return;
    }

    if (multiSelect) {
      // Ctrl+点击：切换选中状态
      if (selectedIds.value.has(id)) {
        selectedIds.value.delete(id);
        if (activeId.value === id) {
          activeId.value =
            selectedIds.value.size > 0
              ? ([...selectedIds.value][0] ?? null)
              : null;
        }
      } else {
        selectedIds.value.add(id);
        activeId.value = id;
      }
    } else if (rangeSelect) {
      // Shift+点击：范围选择（仅支持顶层 items）
      if (activeId.value) {
        const ids = formConf.value.items.map((item) => item.id);
        const startIdx = ids.indexOf(activeId.value);
        const endIdx = ids.indexOf(id);
        if (startIdx !== -1 && endIdx !== -1) {
          const [from, to] =
            startIdx < endIdx ? [startIdx, endIdx] : [endIdx, startIdx];
          for (let i = from; i <= to; i++) {
            selectedIds.value.add(ids[i]!);
          }
        }
      }
      activeId.value = id;
    } else {
      // 普通点击：单选
      activeId.value = id;
      selectedIds.value.clear();
      selectedIds.value.add(id);
    }
  }

  function clearSelection() {
    selectedIds.value.clear();
    activeId.value = null;
  }

  function isSelected(id: string) {
    return selectedIds.value.has(id);
  }

  // 递归查找组件及其所在列表
  function findItemAndList(
    id: string,
    items: FormItemSchema[] = formConf.value.items,
  ): null | { index: number; item: FormItemSchema; list: FormItemSchema[] } {
    const index = items.findIndex((item) => item.id === id);
    if (index !== -1) {
      return { item: items[index]!, list: items, index };
    }

    for (const item of items) {
      if (item.columns) {
        for (const col of item.columns) {
          const found = findItemAndList(id, col.children);
          if (found) return found;
        }
      }
      if (item.items) {
        for (const subItem of item.items) {
          if (subItem.children) {
            const found = findItemAndList(id, subItem.children);
            if (found) return found;
          }
        }
      }
      if (item.children) {
        const found = findItemAndList(id, item.children);
        if (found) return found;
      }
    }
    return null;
  }

  // 移动组件（上移/下移）
  function moveItem(id: string, direction: 'down' | 'up') {
    const found = findItemAndList(id);
    if (!found) return;

    const { list, index } = found;
    const newIndex = direction === 'up' ? index - 1 : index + 1;

    if (newIndex < 0 || newIndex >= list.length) return;

    // 交换位置
    const temp = list[index]!;
    list[index] = list[newIndex]!;
    list[newIndex] = temp;
  }

  // 复制到剪贴板
  function copyToClipboard(ids?: string[]) {
    const targetIds = ids || [...selectedIds.value];
    if (targetIds.length === 0 && activeId.value) {
      targetIds.push(activeId.value);
    }

    clipboard.value = targetIds
      .map((id) => findItemAndList(id)?.item)
      .filter((item): item is FormItemSchema => !!item)
      .map((item) => cloneComponent(item));
  }

  // 从剪贴板粘贴
  function pasteFromClipboard() {
    if (clipboard.value.length === 0) return;

    // 粘贴到当前选中组件之后，或者画布末尾
    const newItems = clipboard.value.map((item) => cloneComponent(item));

    if (activeId.value) {
      const found = findItemAndList(activeId.value);
      if (found) {
        found.list.splice(found.index + 1, 0, ...newItems);
        activeId.value = newItems[0]?.id ?? null;
        return;
      }
    }

    // 默认添加到画布末尾
    formConf.value.items.push(...newItems);
    if (newItems.length > 0) {
      activeId.value = newItems[0]?.id ?? null;
    }
  }

  // 批量删除
  function deleteSelected() {
    const idsToDelete = [...selectedIds.value];
    if (idsToDelete.length === 0 && activeId.value) {
      idsToDelete.push(activeId.value);
    }

    for (const id of idsToDelete) {
      deleteItemFromList(formConf.value.items, id);
    }

    selectedIds.value.clear();
    activeId.value = null;
  }

  // 更新组件标签
  function updateItemLabel(id: string, label: string) {
    const found = findItemAndList(id);
    if (found) {
      found.item.label = label;
    }
  }

  // 递归查找并删除
  function deleteItemFromList(items: FormItemSchema[], id: string): boolean {
    const index = items.findIndex((item) => item.id === id);
    if (index !== -1) {
      items.splice(index, 1);
      return true;
    }

    for (const item of items) {
      if (item.columns) {
        for (const col of item.columns) {
          if (deleteItemFromList(col.children, id)) {
            return true;
          }
        }
      }
      if (item.items) {
        for (const subItem of item.items) {
          if (subItem.children && deleteItemFromList(subItem.children, id)) {
            return true;
          }
        }
      }
      if (item.children && deleteItemFromList(item.children, id)) {
        return true;
      }
    }
    return false;
  }

  function deleteItem(id: string) {
    if (deleteItemFromList(formConf.value.items, id) && activeId.value === id) {
      activeId.value = null;
    }
  }

  function cloneComponent(origin: any) {
    const clone = JSON.parse(JSON.stringify(origin));

    function generateIds(item: any) {
      const id = uuidv4().replaceAll('-', '');
      item.id = id;
      // 只有当 field 不存在或为空时才生成默认值，保留已设置的字段名
      if (!item.field) {
        item.field = `field_${id.slice(0, 8)}`;
      }

      if (item.columns) {
        item.columns.forEach((col: any) => {
          col.children = col.children.map((child: any) => generateIds(child));
        });
      }
      if (item.items) {
        item.items.forEach((subItem: any) => {
          if (subItem.children) {
            subItem.children = subItem.children.map((child: any) =>
              generateIds(child),
            );
          }
        });
      }
      if (item.children) {
        item.children = item.children.map((child: any) => generateIds(child));
      }
      return item;
    }

    return generateIds(clone);
  }

  // 添加组件到画布末尾
  function addComponent(component: any) {
    const newItem = cloneComponent(component);
    formConf.value.items.push(newItem);
    activeId.value = newItem.id;
  }

  function copyItem(id: string) {
    function findAndCopy(items: FormItemSchema[]): boolean {
      const index = items.findIndex((item) => item.id === id);
      if (index !== -1) {
        const original = items[index];
        const clone = cloneComponent(original);
        items.splice(index + 1, 0, clone);
        activeId.value = clone.id;
        return true;
      }

      for (const item of items) {
        if (item.columns) {
          for (const col of item.columns) {
            if (findAndCopy(col.children)) return true;
          }
        }
        if (item.items) {
          for (const subItem of item.items) {
            if (subItem.children && findAndCopy(subItem.children)) return true;
          }
        }
        if (item.children && findAndCopy(item.children)) return true;
      }
      return false;
    }

    findAndCopy(formConf.value.items);
  }

  const defaultTemplates = [
    {
      title: $t('form-design.template.login'),
      icon: 'User',
      items: [
        {
          type: 'input',
          label: $t('form-design.material.components.input'),
          props: {
            placeholder: $t('form-design.attribute.placeholder'),
            width: '100%',
          },
          field: 'username',
          id: 'tpl_login_1',
        },
        {
          type: 'input',
          label: $t('form-design.attribute.password'),
          props: {
            placeholder: $t('form-design.attribute.placeholder'),
            type: 'password',
            showPassword: true,
            width: '100%',
          },
          field: 'password',
          id: 'tpl_login_2',
        },
      ],
    },
    {
      title: $t('form-design.template.register'),
      icon: 'Edit',
      items: [
        {
          type: 'input',
          label: $t('form-design.material.components.input'),
          props: {
            placeholder: $t('form-design.attribute.placeholder'),
            width: '100%',
          },
          field: 'username',
          id: 'tpl_reg_1',
        },
        {
          type: 'input',
          label: $t('form-design.attribute.password'),
          props: {
            placeholder: $t('form-design.attribute.placeholder'),
            type: 'password',
            showPassword: true,
            width: '100%',
          },
          field: 'password',
          id: 'tpl_reg_2',
        },
        {
          type: 'input',
          label: $t('form-design.attribute.password'), // Should probably be confirm password but using existing keys for now
          props: {
            placeholder: $t('form-design.attribute.placeholder'),
            type: 'password',
            showPassword: true,
            width: '100%',
          },
          field: 'confirm_password',
          id: 'tpl_reg_3',
        },
        {
          type: 'input',
          label: $t('form-design.attribute.mobile'),
          props: {
            placeholder: $t('form-design.attribute.placeholder'),
            width: '100%',
          },
          field: 'mobile',
          id: 'tpl_reg_4',
        },
      ],
    },
    {
      title: $t('form-design.template.userInfo'),
      icon: 'Document',
      items: [
        {
          type: 'input',
          label: $t('form-design.attribute.nodeLabel'),
          props: {
            placeholder: $t('form-design.attribute.placeholder'),
            width: '100%',
          },
          field: 'name',
          id: 'tpl_user_1',
        },
        {
          type: 'radio',
          label: $t('form-design.material.components.radio'),
          props: { border: true },
          options: [
            { label: $t('common.male'), value: 1 },
            { label: $t('common.female'), value: 2 },
          ],
          field: 'gender',
          id: 'tpl_user_2',
        },
        {
          type: 'textarea',
          label: $t('form-design.material.components.textarea'),
          props: {
            placeholder: $t('form-design.attribute.placeholder'),
            rows: 3,
            width: '100%',
          },
          field: 'bio',
          id: 'tpl_user_3',
        },
      ],
    },
  ];

  const templates = ref(defaultTemplates);

  const addTemplate = (template: any) => {
    templates.value.push(template);
  };

  const setDataSource = (configs: TableConfig[]) => {
    dataSource.value = {
      mainTable: configs.find((t) => t.type === 'main') || null,
      subTables: configs.filter((t) => t.type === 'sub'),
    };
  };

  return {
    activeId,
    selectedIds,
    formConf,
    dataSource,
    setDataSource,
    setActive,
    clearSelection,
    isSelected,
    deleteItem,
    deleteSelected,
    cloneComponent,
    addComponent,
    copyItem,
    moveItem,
    copyToClipboard,
    pasteFromClipboard,
    updateItemLabel,
    undo,
    redo,
    canUndo,
    canRedo,
    isDragging,
    setDragging,
    templates,
    addTemplate,
    previewMode,
    togglePreviewMode,
  };
});
