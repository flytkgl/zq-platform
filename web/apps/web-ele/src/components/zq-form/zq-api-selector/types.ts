import type { SelectProps } from 'element-plus';

/** API 查询参数 */
export interface ApiSelectQueryParams {
  page: number;
  pageSize: number;
  keyword?: string;
}

/** API 查询结果 */
export interface ApiSelectQueryResult<T = any> {
  items: T[];
  total: number;
}

/** 选项数据结构 */
export interface ApiSelectOption {
  value: string;
  label: string;
  extra?: string;
  raw?: any;
}

export interface ZqApiSelectProps extends Partial<
  Omit<SelectProps, 'modelValue' | 'onChange'>
> {
  /** 选中值 */
  modelValue?: string | string[];

  /** 是否多选 */
  multiple?: boolean;

  /** 占位符 */
  placeholder?: string;

  /** 是否禁用 */
  disabled?: boolean;

  /** 是否可清空 */
  clearable?: boolean;

  /** 是否可搜索 */
  filterable?: boolean;

  // === 核心配置 ===

  /** 列表查询 API（必填） */
  api: (params: ApiSelectQueryParams) => Promise<ApiSelectQueryResult>;

  /** 根据 ID 查询 API（可选，用于回显） */
  apiByIds?: (ids: string[]) => Promise<any[]>;

  /** 值字段名，默认 'id' */
  valueField?: string;

  /** 标签字段名，默认 'name' */
  labelField?: string;

  /** 额外信息字段名（可选，显示在右侧） */
  extraField?: string;

  // === 弹窗配置 ===

  /** 弹窗标题 */
  dialogTitle?: string;

  /** 弹窗宽度，默认 '45%' */
  dialogWidth?: string;

  // === 分页配置 ===

  /** 每页数量，默认 20 */
  pageSize?: number;
}

export interface ZqApiSelectEmits {
  (e: 'update:modelValue', value: string | string[] | undefined): void;
  (e: 'change', value: string | string[] | undefined): void;
}
