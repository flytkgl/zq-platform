import type { SelectProps } from 'element-plus';

export interface ImageSelectorFile {
  id: string;
  name: string;
  path: string;
  url?: string;
  size?: number;
  mime_type?: string;
  sys_create_datetime?: string;
  // 图片特有属性
  width?: number;
  height?: number;
  previewUrl?: string; // 本地预览URL
}

// 继承 ElSelect 的所有属性，但排除我们自定义处理的属性
export interface ImageSelectorProps extends Partial<
  Omit<SelectProps, 'modelValue' | 'onChange' | 'size'>
> {
  modelValue?: string | string[];
  multiple?: boolean;
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  /** 最大文件大小（MB） */
  maxSize?: number;
  /** 最大图片宽度（像素），0表示不限制 */
  maxWidth?: number;
  /** 最大图片高度（像素），0表示不限制 */
  maxHeight?: number;
  /** 最小图片宽度（像素），0表示不限制 */
  minWidth?: number;
  /** 最小图片高度（像素），0表示不限制 */
  minHeight?: number;
  /** 允许的图片格式 */
  accept?: string[];
  /** 网格列数 */
  gridColumns?: number;
  /** 是否显示图片信息 */
  showImageInfo?: boolean;
  /** 是否支持拖拽排序（仅多选时有效） */
  sortable?: boolean;
  /** 是否启用裁剪功能 */
  enableCrop?: boolean;
  /** 裁剪宽高比，例如 16/9, 4/3, 1 (正方形), undefined (自由裁剪) */
  cropAspectRatio?: number;
  /** 裁剪形状：'rect' - 矩形 | 'circle' - 圆形 */
  cropShape?: 'circle' | 'rect';
  /** 触发器大小（像素），用于控制图片预览和上传按钮的尺寸（正方形） */
  size?: number;
  /** 触发器宽度（像素），优先级高于 size */
  width?: number;
  /** 触发器高度（像素），优先级高于 size */
  height?: number;
  /** 上传文件的来源标识，用于文件自动归类，默认 'form' */
  source?: string;
}

export interface ImageSelectorEmits {
  (e: 'update:modelValue', value: string | string[] | null | undefined): void;
  (e: 'change', value: string | string[] | null | undefined): void;
}
