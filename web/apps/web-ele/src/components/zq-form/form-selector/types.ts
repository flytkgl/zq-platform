export interface FormSelectorProps {
  modelValue?: null | string | string[];
  formCode?: string;
  /** 值字段，默认 id */
  valueField?: string;
  /** 显示字段，默认 name */
  labelField?: string;
  /** 是否多选 */
  multiple?: boolean;
  /** 多选时是否折叠标签 */
  collapseTags?: boolean;
  /** 多选时折叠标签的最大显示数量 */
  maxCollapseTags?: number;
  /** 占位符 */
  placeholder?: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否可清空 */
  clearable?: boolean;
  /** 弹窗标题 */
  dialogTitle?: string;
  /** 弹窗宽度 */
  dialogWidth?: string;
  /** 多选展开为多行模式：输入框不实时显示弹窗内的选中项 */
  expandMultipleToRows?: boolean;
  /** 外部预设的已选中值（用于 expandMultipleToRows 模式下同步子表已有行） */
  externalSelectedValues?: string[];
}

export interface FormSelectorEmits {
  (e: 'update:modelValue', value: null | string | string[]): void;
  (e: 'change', value: null | string | string[]): void;
  (e: 'select-item', item: any): void;
}
