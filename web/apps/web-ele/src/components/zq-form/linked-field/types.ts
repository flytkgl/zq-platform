export interface LinkedFieldProps {
  modelValue?: number | string;
  // 源字段（选择组件的字段名）
  sourceField?: string;
  // 要显示的字段名（从选中项中取哪个字段的值）
  displayField?: string;
  // 表单数据
  formData?: Record<string, any>;
  // 占位符
  placeholder?: string;
  // 是否禁用
  disabled?: boolean;
}

export interface LinkedFieldEmits {
  (e: 'update:modelValue', value: number | string | undefined): void;
  (e: 'change', value: number | string | undefined): void;
}
