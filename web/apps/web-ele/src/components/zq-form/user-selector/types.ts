import type { SelectProps } from 'element-plus';

export interface UserSelectorUser {
  id: string;
  username: string;
  name: string;
  avatar?: string;
}

export interface UserSelectorDept {
  id: string;
  name: string;
  children?: UserSelectorDept[];
}

// 继承 ElSelect 的所有属性，但排除我们自定义处理的属性
export interface UserSelectorProps extends Partial<
  Omit<SelectProps, 'modelValue' | 'onChange'>
> {
  modelValue?: string | string[];
  multiple?: boolean;
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  filterable?: boolean;
  displayMode?: 'button' | 'select'; // 显示方式：select 或 button
  onConfirm?: (userIds: string | string[]) => Promise<void> | void; // 确认回调（button 模式下使用）
  autoCurrentUser?: boolean; // 自动获取当前用户作为默认值
  readonly?: boolean; // 只读模式（显示值但不可修改）
}

export interface UserSelectorEmits {
  (e: 'update:modelValue', value: string | string[] | undefined): void;
  (e: 'change', value: string | string[] | undefined): void;
}
