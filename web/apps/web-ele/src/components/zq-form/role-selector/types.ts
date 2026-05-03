import type { SelectProps } from 'element-plus';

export interface RoleSelectorRole {
  id: string;
  name: string;
  code?: string;
  status?: number;
  sort?: number;
}

// 继承 ElSelect 的所有属性，但排除我们自定义处理的属性
export interface RoleSelectorProps extends Partial<
  Omit<SelectProps, 'modelValue' | 'onChange'>
> {
  modelValue?: string | string[];
  multiple?: boolean;
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  filterable?: boolean;
}

export interface RoleSelectorEmits {
  (e: 'update:modelValue', value: string | string[] | undefined): void;
  (e: 'change', value: string | string[] | undefined): void;
}
