export interface SignaturePadProps {
  /** 签名文件ID */
  modelValue?: null | string;
  /** 画笔颜色 */
  penColor?: string;
  /** 画笔粗细 */
  penWidth?: number;
  /** 背景颜色 */
  backgroundColor?: string;
  /** 画布宽度 */
  width?: number | string;
  /** 画布高度 */
  height?: number;
  /** 是否禁用 */
  disabled?: boolean;
  /** 只读模式 */
  readonly?: boolean;
  /** 占位提示 */
  placeholder?: string;
  /** 文件上传来源标识 */
  source?: string;
}

export interface SignaturePadEmits {
  (e: 'update:modelValue', value: null | string): void;
  (e: 'change', value: null | string): void;
  (e: 'signed'): void;
  (e: 'cleared'): void;
}
