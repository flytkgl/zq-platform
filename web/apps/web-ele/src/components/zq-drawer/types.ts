import type { DrawerProps } from 'element-plus';

export interface ZqDrawerProps extends Partial<DrawerProps> {
  /** v-model 控制显隐 */
  modelValue?: boolean;

  /** 标题 */
  title?: string;

  /** 宽度，默认 '30%' */
  size?: number | string;

  /** 方向，默认 'rtl' */
  direction?: 'btt' | 'ltr' | 'rtl' | 'ttb';

  /** 内容区固定高度 */
  contentHeight?: number | string;

  /** 内容区最大高度（超出滚动） */
  maxHeight?: number | string;

  /** 内容区 loading 遮罩 */
  loading?: boolean;

  /** 确认按钮 loading */
  confirmLoading?: boolean;

  /** 是否显示底部，默认 true */
  showFooter?: boolean;

  /** 显示确认按钮，默认 true */
  showConfirmButton?: boolean;

  /** 显示取消按钮，默认 true */
  showCancelButton?: boolean;

  /** 确认按钮文字，默认 '确定' */
  confirmText?: string;

  /** 取消按钮文字，默认 '取消' */
  cancelText?: string;

  /** 确认按钮类型，默认 'primary' */
  confirmButtonType?:
    | 'danger'
    | 'default'
    | 'info'
    | 'primary'
    | 'success'
    | 'warning';

  /** 显示全屏按钮，默认 true */
  showFullscreenButton?: boolean;

  /** 默认全屏，默认 false */
  defaultFullscreen?: boolean;

  /** 显示关闭按钮，默认 true */
  showCloseButton?: boolean;

  /** 关闭销毁，默认 true */
  destroyOnClose?: boolean;

  /** 点击遮罩关闭，默认 false */
  closeOnClickModal?: boolean;

  /** 插入 body，默认 true */
  appendToBody?: boolean;
}

export interface ZqDrawerEmits {
  (e: 'update:modelValue', value: boolean): void;
  (e: 'confirm'): void;
  (e: 'cancel'): void;
  (e: 'open'): void;
  (e: 'opened'): void;
  (e: 'close'): void;
  (e: 'closed'): void;
}

export interface ZqDrawerExpose {
  /** 打开抽屉 */
  open: () => void;
  /** 关闭抽屉 */
  close: () => void;
  /** 设置内容区 loading */
  setLoading: (val: boolean) => void;
  /** 设置确认按钮 loading */
  setConfirmLoading: (val: boolean) => void;
}
