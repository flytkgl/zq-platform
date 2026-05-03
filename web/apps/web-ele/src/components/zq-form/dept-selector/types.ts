import type { SelectProps } from 'element-plus';

export interface DeptSelectorDept {
  id: string;
  name: string;
  children?: DeptSelectorDept[];
  parent_id?: null | string;
  status?: number;
  child_count?: number;
}

// 继承 ElSelect 的所有属性，但排除我们自定义处理的属性
export interface DeptSelectorProps extends Partial<
  Omit<SelectProps, 'modelValue' | 'onChange'>
> {
  modelValue?: string | string[];
  multiple?: boolean;
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  filterable?: boolean;
}

export interface DeptSelectorEmits {
  (e: 'update:modelValue', value: string | string[] | undefined): void;
  (e: 'change', value: string | string[] | undefined): void;
}
