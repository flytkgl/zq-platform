export interface TableSelectorColumn {
  field: string;
  label: string;
  width?: number;
}

export interface TableSelectorProps {
  modelValue?: string | string[];
  multiple?: boolean;
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  dialogTitle?: string;
  dialogWidth?: string;
  columns?: TableSelectorColumn[];
  labelField?: string;
  valueField?: string;
}

export interface TableSelectorEmits {
  (e: 'update:modelValue', value: string | string[] | undefined): void;
  (e: 'change', value: string | string[] | undefined): void;
  (e: 'blur'): void;
  (
    e: 'select-item',
    item: Record<string, any> | Record<string, any>[] | undefined,
  ): void;
}
