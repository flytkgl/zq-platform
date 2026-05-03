import type { SelectProps } from 'element-plus';

export interface FileSelectorFile {
  id: string;
  name: string;
  path: string;
  type: 'file' | 'folder';
  size?: number;
  file_ext?: string;
  mime_type?: string;
  url?: string;
  sys_create_datetime?: string;
}

// 继承 ElSelect 的所有属性，但排除我们自定义处理的属性
export interface FileSelectorProps extends Partial<
  Omit<SelectProps, 'modelValue' | 'onChange'>
> {
  modelValue?: string | string[];
  multiple?: boolean;
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  /** 允许的文件类型，如 ['image/*', '.pdf', '.doc'] */
  accept?: string[];
  /** 最大文件大小（MB） */
  maxSize?: number;
  /** 是否显示文件大小 */
  showSize?: boolean;
  /** 是否显示文件类型图标 */
  showIcon?: boolean;
  /** 已选文件显示方式：'popover' - 悬停显示 | 'list' - 选择框下方列表显示 */
  displayMode?: 'list' | 'popover';
  /** 触发方式：'default' - 显示触发器UI | 'button' - 不渲染触发器，通过 openModal() 外部控制 */
  trigger?: 'button' | 'default';
  /** 上传文件的来源标识，用于文件自动归类，默认 'form' */
  source?: string;
}

export interface FileSelectorEmits {
  (e: 'update:modelValue', value: string | string[] | undefined): void;
  (e: 'change', value: string | string[] | undefined): void;
}
