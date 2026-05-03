<script lang="ts" setup>
import type { ExtendedZqTableApi, ZqTableProps } from './types';

import {
  computed,
  defineComponent,
  nextTick,
  onMounted,
  onUnmounted,
  ref,
  toRaw,
  useSlots,
  watch,
} from 'vue';

import { VbenHelpTooltip } from '@vben/common-ui';
import { usePriorityValues } from '@vben/hooks';
import {
  EmptyIcon,
  ListFilter,
  GripVertical as LucideGripVertical,
  Pin as LucidePin,
  RotateCcw as LucideRotateCcw,
} from '@vben/icons';
import { $t } from '@vben/locales';
import { usePreferences } from '@vben/preferences';
import { cn, isBoolean, isEqual, mergeWithArrayOverride } from '@vben/utils';

import {
  Filter,
  FullScreen,
  Refresh,
  Search,
  Setting,
} from '@element-plus/icons-vue';
import { useResizeObserver } from '@vueuse/core';
import {
  ElButton,
  ElCascader,
  ElCheckbox,
  ElDatePicker,
  ElDivider,
  ElIcon,
  ElInput,
  ElPagination,
  ElPopover,
  ElScrollbar,
  ElSkeletonItem,
  ElTable,
  ElTableColumn,
  ElTooltip,
} from 'element-plus';
import draggable from 'vuedraggable';

import { DeptSelector } from '../zq-form/dept-selector';
import { FormSelector } from '../zq-form/form-selector';
import { PostSelector } from '../zq-form/post-selector';
import { TableSelector } from '../zq-form/table-selector';
import { UserSelector } from '../zq-form/user-selector';
import { useTableForm } from './init';

import './style.css';

interface Props extends ZqTableProps {
  api: ExtendedZqTableApi;
}

interface ColumnState {
  key: string;
  title: string;
  visible: boolean;
  fixed: 'left' | 'right' | false;
  originalIndex: number;
}

const props = withDefaults(defineProps<Props>(), {});
const emit = defineEmits([
  'selection-change',
  'sort-change',
  'filter-change',
  'row-click',
  'row-dblclick',
]);
const rootRef = ref<HTMLElement>();
const tableContainerRef = ref<HTMLElement>();
const tableWidth = ref(0);
const tableHeight = ref(0);
const tableRef = ref();

const isFullscreen = ref(false);
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value;
}

useResizeObserver(tableContainerRef, (entries) => {
  const entry = entries[0];
  if (!entry) return;
  const { width, height } = entry.contentRect;
  tableWidth.value = width;
  tableHeight.value = height;
});

const FORM_SLOT_PREFIX = 'form-';
const CELL_SLOT_PREFIX = 'cell-';
const TOOLBAR_ACTIONS = 'toolbar-actions';
const TOOLBAR_TOOLS = 'toolbar-tools';
const TABLE_TITLE = 'table-title';

const state = props.api?.useStore?.();

const {
  gridOptions,
  class: className,
  gridClass,
  formOptions,
  tableTitle,
  tableTitleHelp,
  showSearchForm,
  separator,
} = usePriorityValues(props, state);

const { isMobile } = usePreferences();
const isSeparator = computed(() => {
  if (
    !formOptions.value ||
    showSearchForm.value === false ||
    separator.value === false
  ) {
    return false;
  }
  if (separator.value === true || separator.value === undefined) {
    return true;
  }
  return separator.value.show !== false;
});

const separatorBg = computed(() => {
  return !separator.value ||
    isBoolean(separator.value) ||
    !separator.value.backgroundColor
    ? undefined
    : separator.value.backgroundColor;
});

const slots = useSlots();
// 防抖定时器
let debounceTimer: null | ReturnType<typeof setTimeout> = null;

// 触发搜索
const triggerSearch = async () => {
  const formValues = await formApi.getValues();
  formApi.setLatestSubmissionValues(toRaw(formValues));
  props.api.reload(formValues);
};

// 防抖搜索
const debouncedSearch = () => {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  debounceTimer = setTimeout(() => {
    triggerSearch();
  }, 300);
};

// Initialize Form
const [Form, formApi] = useTableForm({
  compact: true,
  handleSubmit: async () => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    await triggerSearch();
  },
  handleReset: async () => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    const prevValues = await formApi.getValues();
    await formApi.resetForm();
    const formValues = await formApi.getValues();
    formApi.setLatestSubmissionValues(formValues);
    if (isEqual(prevValues, formValues) || !formOptions.value?.submitOnChange) {
      props.api.reload(formValues);
    }
  },
  commonConfig: {
    componentProps: {
      class: 'w-full',
      clearable: true,
    },
  },
  showCollapseButton: true,
  collapseTriggerResize: true, // 自动检测是否需要折叠
  collapsed: true, // 默认折叠状态
  submitOnChange: true, // 默认启用输入时触发搜索
  submitButtonOptions: {
    content: computed(() => $t('common.search')),
  },
  resetButtonOptions: {
    content: computed(() => $t('common.reset')),
    type: undefined, // 覆盖默认的 type="button"，避免 ElButton 警告
  },
  wrapperClass: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
});

// 监听表单值变化，自动触发搜索
watch(
  () => formApi.form?.values,
  (newValues, oldValues) => {
    // 只有当 submitOnChange 为 true 时才自动搜索
    if (
      formOptions.value?.submitOnChange &&
      newValues &&
      oldValues && // 检查值是否真的变化了
      !isEqual(newValues, oldValues)
    ) {
      debouncedSearch();
    }
  },
  { deep: true },
);

// Toolbar logic
const showTableTitle = computed(() => {
  return !!slots[TABLE_TITLE] || tableTitle.value;
});

const showToolbar = computed(() => {
  return (
    !!slots[TOOLBAR_ACTIONS] ||
    !!slots[TOOLBAR_TOOLS] ||
    showTableTitle.value ||
    !!gridOptions.value?.toolbarConfig
  );
});

const delegatedSlots = computed(() => {
  const resultSlots: string[] = [];
  for (const key of Object.keys(slots)) {
    if (
      !['empty', 'form', 'loading', TOOLBAR_ACTIONS, TOOLBAR_TOOLS].includes(
        key,
      )
    ) {
      resultSlots.push(key);
    }
  }
  return resultSlots;
});

const delegatedFormSlots = computed(() => {
  const resultSlots: string[] = [];
  for (const key of Object.keys(slots)) {
    if (key.startsWith(FORM_SLOT_PREFIX)) {
      resultSlots.push(key);
    }
  }
  return resultSlots.map((key) => key.replace(FORM_SLOT_PREFIX, ''));
});

// Data & Pagination binding
const tableData = props.api.tableData;
const total = props.api.total;
const loading = props.api.loading;
const pagination = props.api.pagination;

function onPageChange(currentPage: number) {
  props.api.handlePageChange(currentPage, pagination.pageSize);
}

function onPageSizeChange(pageSize: number) {
  props.api.handlePageChange(pagination.currentPage, pageSize);
}

function onSearchBtnClick() {
  props.api.toggleSearchForm();
}

function onRefreshBtnClick() {
  props.api.reload();
}

// Init logic
async function init() {
  await nextTick();
  const defaultGridOptions = mergeWithArrayOverride(
    {},
    toRaw(gridOptions.value),
  );

  const autoLoad = defaultGridOptions.proxyConfig?.autoLoad;
  if (autoLoad) {
    props.api.reload();
  }
}

// Column Setting State
const columnState = ref<ColumnState[]>([]);

function initColumnState() {
  const cols = gridOptions.value?.columns;
  if (cols) {
    columnState.value = cols.map((col: any, index: number) => ({
      key: col.key || col.dataKey,
      title: col.title || col.label || col.key || col.dataKey, // el-table uses label
      visible: col.hidden !== true,
      fixed: col.fixed === true ? 'left' : col.fixed || false,
      originalIndex: index,
    }));
  }
}

watch(
  () => gridOptions.value?.columns,
  () => {
    initColumnState();
  },
  { immediate: true, deep: true },
);

function handleResetColumn() {
  initColumnState();
}

function handleToggleFixed(col: ColumnState, type: 'left' | 'right') {
  col.fixed = col.fixed === type ? false : type;
}

watch(
  formOptions,
  () => {
    formApi.setState((prev) => {
      const finalFormOptions = mergeWithArrayOverride(
        {},
        formOptions.value,
        prev,
      );
      return {
        ...finalFormOptions,
        // 自动检测是否需要折叠按钮
        collapseTriggerResize: finalFormOptions.showCollapseButton ?? true,
        // 默认启用输入时触发搜索，除非明确设置为 false
        submitOnChange: finalFormOptions.submitOnChange ?? true,
      };
    });
  },
  { immediate: true },
);

const isCompactForm = computed(() => {
  return formApi.getState()?.compact;
});

onMounted(() => {
  props.api.mount(formApi);
  init();
});

onUnmounted(() => {
  props.api.unmount();
});

// 获取单元格插槽名称列表
const cellSlotNames = computed(() => {
  const result: Record<string, string> = {};
  for (const key of Object.keys(slots)) {
    if (key.startsWith(CELL_SLOT_PREFIX)) {
      const colKey = key.replace(CELL_SLOT_PREFIX, '');
      result[colKey] = key;
    }
  }
  return result;
});

// Renderer Component for VNode
const VNodeRenderer = defineComponent({
  props: {
    renderer: { type: Function, required: true },
    params: { type: Object, required: true },
  },
  setup(props) {
    return () => props.renderer(props.params);
  },
});

// 设置弹性列（最后一个非固定、非特殊列），移除其 width 让它自动填充剩余空间
function setFlexColumn(cols: any[]) {
  // 从后往前找第一个非固定、非 type（selection/index）、非 actions 的列
  for (let i = cols.length - 1; i >= 0; i--) {
    const col = cols[i];
    if (
      !col.type &&
      !col.fixed &&
      col.prop !== 'actions' &&
      col.key !== 'actions'
    ) {
      // 移除 width，保留 minWidth
      delete col.width;
      if (!col.minWidth) {
        col.minWidth = 100;
      }
      break;
    }
  }
  return cols;
}

// Table Columns
const columns = computed(() => {
  const cols = (gridOptions.value?.columns || []) as any[];

  const processCol = (col: any) => {
    const colKey = col.key || col.dataKey || col.prop;
    const slotName = cellSlotNames.value[colKey];

    return {
      ...col,
      prop: colKey, // el-table uses prop
      label: col.title || col.label, // el-table uses label
      slotName: slotName && slots[slotName] ? slotName : undefined,
      resizable: col.resizable ?? true,
      showOverflowTooltip: col.showOverflowTooltip ?? true, // 默认开启溢出提示
    };
  };

  // 如果没有初始化 columnState，直接返回所有列
  if (columnState.value.length === 0) {
    const processedCols = cols.map(processCol);

    // 处理 Selection 和 Index
    const prefixCols: any[] = [];
    if (gridOptions.value?.showSelection) {
      prefixCols.push({
        type: 'selection',
        width: 50,
        fixed: 'left',
        align: 'center',
      });
    }
    if (gridOptions.value?.showIndex) {
      prefixCols.push({
        type: 'index',
        width: 60,
        label: '#',
        fixed: 'left',
        align: 'center',
      });
    }

    const final = [...prefixCols, ...processedCols];

    // 强制 actions 列在最后且固定右侧
    const actionIndex = final.findIndex(
      (c: any) => c.prop === 'actions' || c.key === 'actions',
    );
    if (actionIndex !== -1) {
      const actionCol = final.splice(actionIndex, 1)[0];
      actionCol.fixed = 'right';
      final.push(actionCol);
    }
    return setFlexColumn(final);
  }

  const finalCols: any[] = [];

  // 处理 Selection 和 Index
  if (gridOptions.value?.showSelection) {
    finalCols.push({
      type: 'selection',
      width: 50,
      fixed: 'left',
      align: 'center',
    });
  }
  if (gridOptions.value?.showIndex) {
    finalCols.push({
      type: 'index',
      width: 60,
      label: '#',
      fixed: 'left',
      align: 'center',
    });
  }

  columnState.value.forEach((state) => {
    if (!state.visible) return;

    const originalCol = cols.find(
      (c) => (c.key || c.dataKey || c.prop) === state.key,
    );
    if (originalCol) {
      const processedCol = processCol(originalCol);
      finalCols.push({
        ...processedCol,
        fixed: state.fixed,
      });
    }
  });

  // 强制 actions 列在最后且固定右侧
  const actionIndex = finalCols.findIndex(
    (c: any) => c.prop === 'actions' || c.key === 'actions',
  );
  if (actionIndex !== -1) {
    const actionCol = finalCols.splice(actionIndex, 1)[0];
    actionCol.fixed = 'right';
    finalCols.push(actionCol);
  }

  return setFlexColumn(finalCols);
});

function handleSelectionChange(val: any[]) {
  emit('selection-change', val);
}

function handleSortChange(data: any) {
  emit('sort-change', data);
}

function handleFilterChange(filters: any) {
  emit('filter-change', filters);
}

// ========== 自定义 Excel 风格过滤功能（支持后端分页加载） ==========
// 当前过滤状态：{ 字段名: 选中的值数组或单个值（日期精确匹配） }
const columnFilters = ref<Record<string, any[] | string>>({});
// 每个列的弹窗显示状态
const filterPopoverVisible = ref<Record<string, boolean>>({});
// 过滤图标的 ref（用于 virtual-triggering）
const filterIconRefs = ref<Record<string, any>>({});
function setFilterIconRef(prop: string, el: any) {
  if (el) {
    filterIconRefs.value[prop] = el.$el || el;
  }
}
// 当前打开的过滤弹窗对应的列
const activeFilterColumn = ref<null | string>(null);
// 当前过滤列的组件类型
const activeFilterComponentType = ref<null | string>(null);
// 当前过滤列的查询类型（日期过滤用）
const activeFilterQueryType = ref<'eq' | 'range'>('range');
// 当前过滤列是否显示时间（日期过滤用）
const activeFilterShowTime = ref(false);
// 临时选中的过滤值（在确认前）
const tempFilterValues = ref<any[]>([]);

// 过滤选项状态
const filterOptions = ref<{ count?: number; label: string; value: any }[]>([]);
const filterLoading = ref(false);
const filterHasMore = ref(false);
const filterPage = ref(1);
const filterSearch = ref('');
const filterSearchDebounceTimer = ref<null | ReturnType<typeof setTimeout>>(
  null,
);

// 日期范围过滤状态
const tempDateRangeFilter = ref<[string, string] | null>(null);
// 日期精确匹配过滤状态
const tempDateFilter = ref<null | string>(null);
// 级联过滤临时值
const tempCascaderFilter = ref<any>(null);

// 日期快捷选项
const dateShortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
      return [start, end];
    },
  },
  {
    text: '最近一个月',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
      return [start, end];
    },
  },
  {
    text: '最近三个月',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
      return [start, end];
    },
  },
];

// 判断是否为弹窗选择器过滤的组件类型
function isDialogFilterComponent(componentType: string): boolean {
  return [
    'department-selector',
    'dept-select',
    'dept-selector',
    'form-selector',
    'position-selector',
    'post-select',
    'post-selector',
    'table-selector',
    'user-select',
    'user-selector',
  ].includes(componentType);
}

// 判断是否为日期时间组件类型
function isDateTimeComponent(componentType: string): boolean {
  return [
    'date',
    'date-picker',
    'datetime',
    'datetime-picker',
    'time',
    'time-picker',
  ].includes(componentType);
}

// 判断是否为级联组件
function isCascaderComponent(componentType: string): boolean {
  return ['cascader', 'tree-select'].includes(componentType);
}

// 判断是否为特殊过滤组件（不需要加载选项列表）
function isSpecialFilterComponent(componentType: string): boolean {
  return (
    isDialogFilterComponent(componentType) ||
    isDateTimeComponent(componentType) ||
    isCascaderComponent(componentType)
  );
}

// 获取过滤 API 函数（从 gridOptions 中获取）
function getFilterApi() {
  return gridOptions.value?.filterApi;
}

// 加载过滤选项（从后端或本地）
async function loadFilterOptions(
  prop: string,
  page: number = 1,
  search: string = '',
) {
  const filterApi = getFilterApi();
  const col = columns.value.find((c: any) => c.prop === prop);

  // 列配置中有 options 时优先使用（如开关、下拉等已知选项的组件）
  if (col?.options && col.options.length > 0) {
    let options = col.options.map((opt: any) => ({
      value: opt.value,
      label: opt.label || String(opt.value),
    }));
    if (search) {
      const searchLower = search.toLowerCase();
      options = options.filter((opt: any) =>
        opt.label.toLowerCase().includes(searchLower),
      );
    }
    filterOptions.value = options;
    filterHasMore.value = false;
    filterLoading.value = false;
    return;
  }

  if (filterApi) {
    // 使用后端 API 加载
    filterLoading.value = true;
    try {
      const result = await filterApi({
        field: prop,
        page,
        pageSize: 20,
        search,
      });
      filterOptions.value =
        page === 1 ? result.items : [...filterOptions.value, ...result.items];
      filterHasMore.value = result.hasMore;
      filterPage.value = page;
    } catch (error) {
      console.error('加载过滤选项失败:', error);
    } finally {
      filterLoading.value = false;
    }
  } else {
    // 从当前数据中提取
    const data = tableData.value || [];
    const uniqueMap = new Map<any, string>();

    for (const row of data) {
      const value = row[prop];
      if (value !== null && value !== undefined && value !== '') {
        uniqueMap.set(value, String(value));
      }
    }

    let options = [...uniqueMap.entries()]
      .map(([value, label]) => ({ value, label }))
      .sort((a, b) => a.label.localeCompare(b.label));

    // 本地搜索过滤
    if (search) {
      const searchLower = search.toLowerCase();
      options = options.filter((opt) =>
        opt.label.toLowerCase().includes(searchLower),
      );
    }

    filterOptions.value = options;
    filterHasMore.value = false;
  }
}

// 加载更多过滤选项
async function loadMoreFilterOptions() {
  if (!activeFilterColumn.value || filterLoading.value || !filterHasMore.value)
    return;
  await loadFilterOptions(
    activeFilterColumn.value,
    filterPage.value + 1,
    filterSearch.value,
  );
}

// 搜索过滤选项（防抖）
function onFilterSearchInput(value: string) {
  filterSearch.value = value;

  if (filterSearchDebounceTimer.value) {
    clearTimeout(filterSearchDebounceTimer.value);
  }

  filterSearchDebounceTimer.value = setTimeout(() => {
    if (activeFilterColumn.value) {
      loadFilterOptions(activeFilterColumn.value, 1, value);
    }
  }, 300);
}

// 处理过滤图标点击
async function handleFilterIconClick(prop: string, col?: any) {
  // 关闭其他已打开的弹窗
  Object.keys(filterPopoverVisible.value).forEach((key) => {
    if (key !== prop) {
      filterPopoverVisible.value[key] = false;
    }
  });

  // 先清空数据和设置加载状态
  activeFilterColumn.value = prop;
  activeFilterComponentType.value = col?.originalComponent || null;
  // 读取日期过滤配置
  activeFilterQueryType.value = col?.filterQueryType || 'range';
  activeFilterShowTime.value = col?.filterShowTime ?? false;
  filterSearch.value = '';
  filterPage.value = 1;
  filterOptions.value = [];
  filterHasMore.value = false;
  tempFilterValues.value = [...(columnFilters.value[prop] || [])];

  // 检查是否为特殊过滤组件（选择器或日期时间）
  const componentType = col?.originalComponent;

  // 初始化日期过滤值
  if (componentType && isDateTimeComponent(componentType)) {
    const existingFilter = columnFilters.value[prop];
    if (activeFilterQueryType.value === 'eq') {
      tempDateFilter.value =
        typeof existingFilter === 'string' ? existingFilter : null;
      tempDateRangeFilter.value = null;
    } else {
      tempDateRangeFilter.value =
        Array.isArray(existingFilter) && existingFilter.length === 2
          ? (existingFilter as [string, string])
          : null;
      tempDateFilter.value = null;
    }
  }

  // 初始化级联过滤值
  if (componentType && isCascaderComponent(componentType)) {
    const existingFilter = columnFilters.value[prop];
    tempCascaderFilter.value = existingFilter ?? null;
  }

  if (componentType && isSpecialFilterComponent(componentType)) {
    // 对于特殊组件，直接打开弹窗，不需要加载选项
    filterLoading.value = false;
  } else {
    // 普通组件需要加载选项
    filterLoading.value = true;
  }

  // 打开弹窗
  filterPopoverVisible.value[prop] = true;

  // 非特殊组件才加载数据
  if (!componentType || !isSpecialFilterComponent(componentType)) {
    await loadFilterOptions(prop, 1, '');
  }
}

// 关闭过滤弹窗
function closeFilterPopover() {
  if (activeFilterColumn.value) {
    filterPopoverVisible.value[activeFilterColumn.value] = false;
  }
  activeFilterColumn.value = null;
  tempFilterValues.value = [];
}

// 切换过滤值选中状态
function toggleFilterValue(value: any) {
  const index = tempFilterValues.value.indexOf(value);
  if (index === -1) {
    tempFilterValues.value.push(value);
  } else {
    tempFilterValues.value.splice(index, 1);
  }
}

// 全选/取消全选（使用当前加载的选项）
function toggleSelectAll(_prop: string) {
  const allValues = filterOptions.value.map((item) => item.value);
  tempFilterValues.value =
    tempFilterValues.value.length === allValues.length ? [] : [...allValues];
}

// 确认过滤
function confirmFilter() {
  if (!activeFilterColumn.value) return;

  const prop = activeFilterColumn.value;
  if (tempFilterValues.value.length === 0) {
    // 清除该列的过滤
    delete columnFilters.value[prop];
  } else {
    columnFilters.value[prop] = [...tempFilterValues.value];
  }

  // 触发过滤变更事件
  emit('filter-change', { ...columnFilters.value });
  closeFilterPopover();
}

// 确认日期过滤
function confirmDateFilter() {
  if (!activeFilterColumn.value) return;

  const prop = activeFilterColumn.value;

  if (activeFilterQueryType.value === 'eq') {
    // 精确匹配
    if (tempDateFilter.value) {
      columnFilters.value[prop] = String(tempDateFilter.value);
    } else {
      delete columnFilters.value[prop];
    }
  } else {
    // 范围查询
    if (!tempDateRangeFilter.value || tempDateRangeFilter.value.length !== 2) {
      delete columnFilters.value[prop];
    } else {
      const [start, end] = tempDateRangeFilter.value;
      columnFilters.value[prop] = [String(start), String(end)];
    }
  }

  // 触发过滤变更事件
  emit('filter-change', { ...columnFilters.value });
  closeFilterPopover();
  tempDateRangeFilter.value = null;
  tempDateFilter.value = null;
}

// 确认级联过滤
function confirmCascaderFilter() {
  if (!activeFilterColumn.value) return;

  const prop = activeFilterColumn.value;
  const val = tempCascaderFilter.value;

  if (val === null || val === undefined || (Array.isArray(val) && val.length === 0)) {
    delete columnFilters.value[prop];
  } else {
    // 级联值可能是单个值或数组（emitPath=true 时为路径数组），统一存为数组便于后端查询
    columnFilters.value[prop] = Array.isArray(val) ? [...val] : [val];
  }

  emit('filter-change', { ...columnFilters.value });
  closeFilterPopover();
  tempCascaderFilter.value = null;
}

// 清除该列过滤
function clearColumnFilter(prop: string) {
  delete columnFilters.value[prop];
  tempFilterValues.value = [];
  tempDateRangeFilter.value = null;
  tempDateFilter.value = null;
  tempCascaderFilter.value = null;
  emit('filter-change', { ...columnFilters.value });
  filterPopoverVisible.value[prop] = false;
  activeFilterColumn.value = null;
}

// 处理选择器过滤值变化
function handleSelectorFilterChange(value: any) {
  // 将选择器返回的值转换为数组
  if (Array.isArray(value)) {
    tempFilterValues.value = [...value];
  } else if (value) {
    tempFilterValues.value = [value];
  } else {
    tempFilterValues.value = [];
  }
}

// 检查列是否有激活的过滤
function hasActiveFilter(prop: string): boolean {
  return !!(columnFilters.value[prop] && columnFilters.value[prop].length > 0);
}

// 统计类型国际化标签映射
const summaryTypeLabels: Record<string, string> = {
  sum: '合计',
  avg: '平均',
  count: '计数',
  max: '最大',
  min: '最小',
};

// 表尾统计方法
function getSummaryMethod(param: { columns: any[]; data: any[] }) {
  const { columns: tableCols, data } = param;
  const sums: string[] = [];
  const summaryColumns = gridOptions.value?.summaryColumns || [];
  const summaryType = gridOptions.value?.summaryType || 'sum';
  const precision = gridOptions.value?.summaryPrecision ?? 2;

  tableCols.forEach((column, index) => {
    // 第一列显示统计类型名称
    if (index === 0) {
      sums[index] = summaryTypeLabels[summaryType] || summaryType;
      return;
    }

    // 查找该列的统计配置
    const summaryConfig = summaryColumns.find(
      (sc: any) => sc.field === column.property,
    );

    if (!summaryConfig || !summaryConfig.enabled) {
      sums[index] = '';
      return;
    }

    // 获取该列的所有数值
    const values = data.map((item) => Number(item[column.property]));
    const validValues = values.filter((value) => !Number.isNaN(value));

    if (validValues.length === 0) {
      sums[index] = '-';
      return;
    }

    let result: number;
    switch (summaryType) {
      case 'avg': {
        result =
          validValues.reduce((acc, val) => acc + val, 0) / validValues.length;
        break;
      }
      case 'count': {
        result = validValues.length;
        break;
      }
      case 'max': {
        result = Math.max(...validValues);
        break;
      }
      case 'min': {
        result = Math.min(...validValues);
        break;
      }
      case 'sum': {
        result = validValues.reduce((acc, val) => acc + val, 0);
        break;
      }
      default: {
        result = validValues.reduce((acc, val) => acc + val, 0);
      }
    }

    sums[index] = result.toFixed(precision);
  });

  return sums;
}
</script>

<template>
  <div
    :class="
      cn('bg-card flex h-full flex-col rounded-md', className, {
        'zq-table-fullscreen': isFullscreen,
      })
    "
    ref="rootRef"
  >
    <!-- Form -->
    <div
      v-if="formOptions"
      v-show="showSearchForm !== false"
      :class="
        cn(
          'relative rounded p-4',
          isCompactForm
            ? isSeparator
              ? 'pb-8'
              : 'pb-4'
            : isSeparator
              ? 'pb-4'
              : 'pb-0',
        )
      "
    >
      <slot name="form">
        <Form>
          <template
            v-for="slotName in delegatedFormSlots"
            :key="slotName"
            #[slotName]="slotProps"
          >
            <slot
              :name="`${FORM_SLOT_PREFIX}${slotName}`"
              v-bind="slotProps"
            ></slot>
          </template>
        </Form>
      </slot>
      <div
        v-if="isSeparator"
        :style="{
          ...(separatorBg ? { backgroundColor: separatorBg } : undefined),
        }"
        class="bg-background-deep z-100 absolute -left-2 bottom-1 h-2 w-[calc(100%+8px)] overflow-hidden md:bottom-2 md:h-3"
      ></div>
    </div>

    <!-- Toolbar -->
    <div
      v-if="showToolbar"
      class="flex items-center justify-between px-4 pb-4 pt-2"
    >
      <!-- Left: Title / Actions -->
      <div class="flex items-center">
        <slot v-if="showTableTitle" name="table-title">
          <div class="mr-1 pl-1 text-[1rem] font-medium">
            {{ tableTitle }}
            <VbenHelpTooltip v-if="tableTitleHelp" trigger-class="pb-1">
              {{ tableTitleHelp }}
            </VbenHelpTooltip>
          </div>
        </slot>
        <slot name="toolbar-actions"></slot>
      </div>

      <!-- Right: Tools -->
      <div class="flex items-center">
        <slot name="toolbar-tools"></slot>

        <!-- Default Tools -->
        <ElButton
          v-if="gridOptions?.toolbarConfig?.search && !!formOptions"
          circle
          :type="showSearchForm ? 'primary' : ''"
          :icon="Search"
          @click="onSearchBtnClick"
          :title="$t('common.search')"
        />
        <ElButton
          v-if="gridOptions?.toolbarConfig?.refresh !== false"
          circle
          @click="onRefreshBtnClick"
          :title="$t('common.refresh')"
        >
          <ElIcon :class="{ 'zq-spin': loading }">
            <Refresh />
          </ElIcon>
        </ElButton>
        <ElButton
          v-if="gridOptions?.toolbarConfig?.zoom !== false"
          circle
          :type="isFullscreen ? 'primary' : ''"
          :icon="FullScreen"
          @click="toggleFullscreen"
          :title="
            isFullscreen ? $t('common.exitFullscreen') : $t('common.fullscreen')
          "
        />
        <ElPopover
          v-if="gridOptions?.toolbarConfig?.custom !== false"
          placement="bottom-end"
          :width="280"
          trigger="click"
        >
          <template #reference>
            <ElButton circle :icon="Setting" :title="$t('common.setting')" />
          </template>
          <div class="p-2">
            <div class="mb-2 flex items-center justify-between">
              <span class="font-bold">{{ $t('common.columnSetting') }}</span>
              <ElButton
                link
                size="small"
                @click="handleResetColumn"
                :icon="LucideRotateCcw"
              >
                {{ $t('common.reset') }}
              </ElButton>
            </div>
            <ElDivider class="!my-2" />
            <ElScrollbar max-height="300px">
              <draggable
                v-model="columnState"
                item-key="key"
                handle=".drag-handle"
                :animation="200"
              >
                <template #item="{ element }">
                  <div
                    class="hover:bg-accent/50 group mb-1 flex items-center rounded p-1"
                  >
                    <LucideGripVertical
                      class="text-muted-foreground drag-handle mr-2 h-4 w-4 cursor-move opacity-0 group-hover:opacity-100"
                    />
                    <ElCheckbox
                      v-model="element.visible"
                      class="mr-2 !h-6 flex-1 truncate"
                      :label="element.title"
                      :title="element.title"
                    />

                    <div
                      class="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100"
                    >
                      <ElTooltip content="固定到左侧" placement="top">
                        <LucidePin
                          class="h-3.5 w-3.5 cursor-pointer"
                          :class="
                            element.fixed === 'left'
                              ? 'text-primary rotate-[-45deg]'
                              : 'text-muted-foreground hover:text-foreground'
                          "
                          @click="handleToggleFixed(element, 'left')"
                        />
                      </ElTooltip>
                      <ElTooltip content="固定到右侧" placement="top">
                        <LucidePin
                          class="h-3.5 w-3.5 scale-x-[-1] cursor-pointer"
                          :class="
                            element.fixed === 'right'
                              ? 'text-primary rotate-[-45deg]'
                              : 'text-muted-foreground hover:text-foreground'
                          "
                          @click="handleToggleFixed(element, 'right')"
                        />
                      </ElTooltip>
                    </div>
                  </div>
                </template>
              </draggable>
            </ElScrollbar>
          </div>
        </ElPopover>
      </div>
    </div>

    <!-- Table Body -->
    <div
      class="relative flex-1 overflow-hidden px-3"
      :class="gridClass"
      v-loading="loading"
    >
      <div class="h-full w-full" ref="tableContainerRef">
        <ElTable
          ref="tableRef"
          v-bind="gridOptions"
          :data="tableData"
          :height="tableHeight"
          :style="{ width: '100%' }"
          header-row-class-name="zq-table-header"
          :show-summary="gridOptions?.showSummary"
          :summary-method="
            gridOptions?.showSummary ? getSummaryMethod : undefined
          "
          @selection-change="handleSelectionChange"
          @sort-change="handleSortChange"
        >
          <ElTableColumn
            v-for="col in columns"
            :key="col.prop || col.key || col.type"
            v-bind="col"
          >
            <!-- 自定义表头：显示过滤图标 -->
            <template v-if="!col.type && col.filterable" #header>
              <div class="zq-table-header-cell" @click.stop>
                <span class="zq-table-header-label">{{ col.label }}</span>
                <ElIcon
                  :ref="(el: any) => setFilterIconRef(col.prop, el)"
                  class="zq-filter-icon"
                  :class="{ 'text-primary': hasActiveFilter(col.prop) }"
                  @click.stop="handleFilterIconClick(col.prop, col)"
                >
                  <ListFilter v-if="hasActiveFilter(col.prop)" />
                  <Filter v-else />
                </ElIcon>
                <ElPopover
                  :visible="filterPopoverVisible[col.prop]"
                  placement="bottom"
                  :width="280"
                  trigger="click"
                  virtual-triggering
                  :virtual-ref="filterIconRefs[col.prop]"
                  :teleported="true"
                  popper-class="zq-filter-popover-wrapper"
                >
                  <div class="zq-filter-popover">
                    <!-- 选择器组件过滤 -->
                    <template
                      v-if="
                        activeFilterComponentType &&
                        isDialogFilterComponent(activeFilterComponentType)
                      "
                    >
                      <div class="mb-2">
                        <UserSelector
                          v-if="
                            activeFilterComponentType === 'user-select' ||
                            activeFilterComponentType === 'user-selector'
                          "
                          :model-value="tempFilterValues"
                          multiple
                          :placeholder="$t('common.select')"
                          @change="handleSelectorFilterChange"
                        />
                        <DeptSelector
                          v-else-if="
                            activeFilterComponentType === 'dept-select' ||
                            activeFilterComponentType === 'dept-selector' ||
                            activeFilterComponentType === 'department-selector'
                          "
                          :model-value="tempFilterValues"
                          multiple
                          :placeholder="$t('common.select')"
                          @change="handleSelectorFilterChange"
                        />
                        <PostSelector
                          v-else-if="
                            activeFilterComponentType === 'post-select' ||
                            activeFilterComponentType === 'post-selector' ||
                            activeFilterComponentType === 'position-selector'
                          "
                          :model-value="tempFilterValues"
                          multiple
                          :placeholder="$t('common.select')"
                          @change="handleSelectorFilterChange"
                        />
                        <FormSelector
                          v-else-if="
                            activeFilterComponentType === 'form-selector'
                          "
                          :model-value="tempFilterValues"
                          :form-code="col.formCode"
                          :value-field="col.formSelectorValueField || 'id'"
                          :label-field="col.formSelectorLabelField || 'name'"
                          multiple
                          :placeholder="$t('common.select')"
                          @change="handleSelectorFilterChange"
                        />
                        <TableSelector
                          v-else-if="
                            activeFilterComponentType === 'table-selector'
                          "
                          :model-value="tempFilterValues"
                          :data-source-type="col.tableSelectorDataSourceType"
                          :form-code="col.formCode"
                          :dict-code="col.tableSelectorDictCode"
                          :data-source-code="col.tableSelectorDataSourceCode"
                          :value-field="col.formSelectorValueField || 'id'"
                          :label-field="col.formSelectorLabelField || 'name'"
                          :columns="col.tableSelectorColumns"
                          :search-fields="col.tableSelectorSearchFields"
                          multiple
                          :placeholder="$t('common.select')"
                          @change="handleSelectorFilterChange"
                        />
                      </div>
                      <!-- 操作按钮 -->
                      <div class="mt-2 flex justify-end gap-2">
                        <ElButton
                          size="small"
                          @click="clearColumnFilter(col.prop)"
                        >
                          {{ $t('common.reset') }}
                        </ElButton>
                        <ElButton size="small" @click="closeFilterPopover">
                          {{ $t('common.cancel') }}
                        </ElButton>
                        <ElButton
                          type="primary"
                          size="small"
                          @click="confirmFilter"
                        >
                          {{ $t('common.confirm') }}
                        </ElButton>
                      </div>
                    </template>
                    <!-- 日期时间组件过滤 -->
                    <template
                      v-else-if="
                        activeFilterComponentType &&
                        isDateTimeComponent(activeFilterComponentType)
                      "
                    >
                      <div class="mb-2">
                        <!-- 范围查询 -->
                        <template v-if="activeFilterQueryType === 'range'">
                          <ElDatePicker
                            v-model="tempDateRangeFilter"
                            :type="
                              activeFilterShowTime
                                ? 'datetimerange'
                                : 'daterange'
                            "
                            :start-placeholder="$t('common.startDate')"
                            :end-placeholder="$t('common.endDate')"
                            :format="
                              activeFilterShowTime
                                ? 'YYYY-MM-DD HH:mm:ss'
                                : 'YYYY-MM-DD'
                            "
                            :value-format="
                              activeFilterShowTime
                                ? 'YYYY-MM-DD HH:mm:ss'
                                : 'YYYY-MM-DD'
                            "
                            size="small"
                            style="width: 100%"
                            :shortcuts="dateShortcuts"
                          />
                        </template>
                        <!-- 精确匹配 -->
                        <template v-else>
                          <ElDatePicker
                            v-model="tempDateFilter"
                            :type="activeFilterShowTime ? 'datetime' : 'date'"
                            :placeholder="$t('common.selectDate')"
                            :format="
                              activeFilterShowTime
                                ? 'YYYY-MM-DD HH:mm:ss'
                                : 'YYYY-MM-DD'
                            "
                            :value-format="
                              activeFilterShowTime
                                ? 'YYYY-MM-DD HH:mm:ss'
                                : 'YYYY-MM-DD'
                            "
                            size="small"
                            style="width: 100%"
                          />
                        </template>
                      </div>
                      <!-- 操作按钮 -->
                      <div class="mt-2 flex justify-end gap-2">
                        <ElButton
                          size="small"
                          @click="clearColumnFilter(col.prop)"
                        >
                          {{ $t('common.reset') }}
                        </ElButton>
                        <ElButton size="small" @click="closeFilterPopover">
                          {{ $t('common.cancel') }}
                        </ElButton>
                        <ElButton
                          type="primary"
                          size="small"
                          @click="confirmDateFilter"
                        >
                          {{ $t('common.confirm') }}
                        </ElButton>
                      </div>
                    </template>
                    <!-- 级联组件过滤 -->
                    <template
                      v-else-if="
                        activeFilterComponentType &&
                        isCascaderComponent(activeFilterComponentType)
                      "
                    >
                      <div class="mb-2">
                        <ElCascader
                          v-model="tempCascaderFilter"
                          :options="col.options || []"
                          :props="{
                            expandTrigger: 'hover',
                            checkStrictly: col.cascaderProps?.checkStrictly ?? true,
                            emitPath: col.cascaderProps?.emitPath ?? false,
                            multiple: col.cascaderProps?.multiple ?? false,
                            value: 'value',
                            label: 'label',
                            children: 'children',
                          }"
                          filterable
                          clearable
                          :placeholder="$t('common.select')"
                          size="small"
                          style="width: 100%"
                          :collapse-tags="col.cascaderProps?.multiple"
                          :collapse-tags-tooltip="col.cascaderProps?.multiple"
                        />
                      </div>
                      <!-- 操作按钮 -->
                      <div class="mt-2 flex justify-end gap-2">
                        <ElButton
                          size="small"
                          @click="clearColumnFilter(col.prop)"
                        >
                          {{ $t('common.reset') }}
                        </ElButton>
                        <ElButton size="small" @click="closeFilterPopover">
                          {{ $t('common.cancel') }}
                        </ElButton>
                        <ElButton
                          type="primary"
                          size="small"
                          @click="confirmCascaderFilter"
                        >
                          {{ $t('common.confirm') }}
                        </ElButton>
                      </div>
                    </template>
                    <!-- 普通过滤选项 -->
                    <template v-else>
                      <!-- 搜索框 -->
                      <div class="mb-2">
                        <ElInput
                          v-model="filterSearch"
                          :placeholder="$t('common.search')"
                          size="small"
                          clearable
                          :prefix-icon="Search"
                          @input="onFilterSearchInput"
                        />
                      </div>
                      <!-- 全选和重置 -->
                      <div class="mb-2 flex items-center justify-between">
                        <ElCheckbox
                          :model-value="
                            tempFilterValues.length === filterOptions.length &&
                            tempFilterValues.length > 0
                          "
                          :indeterminate="
                            tempFilterValues.length > 0 &&
                            tempFilterValues.length < filterOptions.length
                          "
                          :disabled="filterLoading"
                          @change="toggleSelectAll(col.prop)"
                        >
                          {{ $t('common.selectAll') }}
                        </ElCheckbox>
                        <ElButton
                          link
                          type="primary"
                          size="small"
                          @click="clearColumnFilter(col.prop)"
                        >
                          {{ $t('common.reset') }}
                        </ElButton>
                      </div>
                      <!-- 选项列表 -->
                      <ElScrollbar height="200px">
                        <div class="min-h-[200px]">
                          <!-- 骨架屏加载状态 -->
                          <template
                            v-if="filterLoading && filterOptions.length === 0"
                          >
                            <div
                              v-for="i in 5"
                              :key="i"
                              class="flex items-center py-1"
                            >
                              <ElSkeletonItem
                                variant="text"
                                style="
                                  width: 16px;
                                  height: 16px;
                                  margin-right: 8px;
                                "
                              />
                              <ElSkeletonItem
                                variant="text"
                                style="width: 80%"
                              />
                            </div>
                          </template>
                          <!-- 选项列表 -->
                          <template v-else>
                            <div
                              v-for="item in filterOptions"
                              :key="item.value"
                              class="flex items-center py-0.5"
                            >
                              <ElCheckbox
                                :model-value="
                                  tempFilterValues.includes(item.value)
                                "
                                @change="toggleFilterValue(item.value)"
                              >
                                <span class="truncate">{{ item.label }}</span>
                                <span
                                  v-if="item.count"
                                  class="text-muted-foreground ml-1 text-xs"
                                  >({{ item.count }})</span
                                >
                              </ElCheckbox>
                            </div>
                            <!-- 加载更多 -->
                            <div v-if="filterHasMore" class="py-2 text-center">
                              <ElButton
                                v-if="!filterLoading"
                                link
                                type="primary"
                                size="small"
                                @click="loadMoreFilterOptions"
                              >
                                {{ $t('common.loadMore') }}
                              </ElButton>
                              <span v-else class="text-muted-foreground text-xs"
                                >{{ $t('common.loading') }}...</span
                              >
                            </div>
                            <!-- 无数据 -->
                            <div
                              v-if="
                                !filterLoading && filterOptions.length === 0
                              "
                              class="text-muted-foreground py-4 text-center text-sm"
                            >
                              {{ $t('common.noData') }}
                            </div>
                          </template>
                        </div>
                      </ElScrollbar>
                      <!-- 操作按钮 -->
                      <div class="mt-2 flex justify-end gap-2">
                        <ElButton size="small" @click="closeFilterPopover">
                          {{ $t('common.cancel') }}
                        </ElButton>
                        <ElButton
                          type="primary"
                          size="small"
                          @click="confirmFilter"
                        >
                          {{ $t('common.confirm') }}
                        </ElButton>
                      </div>
                    </template>
                  </div>
                </ElPopover>
              </div>
            </template>
            <!-- 对于 selection 和 index 类型的列，不使用自定义插槽 -->
            <template v-if="!col.type" #default="scope">
              <!-- 优先使用插槽 -->
              <slot
                v-if="col.slotName"
                :name="col.slotName"
                v-bind="{ row: scope.row, $index: scope.$index }"
              ></slot>
              <!-- 其次使用 cellRenderer (函数渲染 VNode) -->
              <VNodeRenderer
                v-else-if="col.cellRenderer"
                :renderer="col.cellRenderer"
                :params="{
                  cellData: scope.row[col.prop],
                  rowData: scope.row,
                  rowIndex: scope.$index,
                  column: col,
                }"
              />
              <!-- 默认显示 -->
              <span v-else>{{ scope.row[col.prop] }}</span>
            </template>
          </ElTableColumn>

          <template #empty>
            <slot name="empty">
              <div
                class="text-muted-foreground flex h-full flex-col items-center justify-center"
              >
                <EmptyIcon class="mx-auto" />
                <div class="mt-2">{{ $t('common.noData') }}</div>
              </div>
            </slot>
          </template>
        </ElTable>
      </div>
    </div>

    <!-- Pagination -->
    <div
      v-if="gridOptions?.pagerConfig?.enabled !== false"
      class="flex justify-end p-4"
    >
      <ElPagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :total="total"
        :page-sizes="gridOptions?.pagerConfig?.pageSizes || [10, 20, 50, 100]"
        :layout="
          gridOptions?.pagerConfig?.layout ||
          'total, sizes, prev, pager, next, jumper'
        "
        :background="gridOptions?.pagerConfig?.background !== false"
        size="small"
        @current-change="onPageChange"
        @size-change="onPageSizeChange"
      />
    </div>
  </div>
</template>

<style>
/*
 * 树形表格修复：自定义插槽可能渲染 block 元素导致与展开图标分行。
 * 匹配包含展开图标或占位符的 .cell（覆盖所有树形行，含 level-0）。
 */
.el-table .cell:has(> .el-table__expand-icon),
.el-table .cell:has(> .el-table__placeholder) {
  display: flex !important;
  align-items: center;
  flex-wrap: nowrap;
}

.el-table .cell > .el-table__indent,
.el-table .cell > .el-table__expand-icon,
.el-table .cell > .el-table__placeholder {
  flex-shrink: 0;
}

.el-table .cell:has(> .el-table__expand-icon) > :last-child,
.el-table .cell:has(> .el-table__placeholder) > :last-child {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
