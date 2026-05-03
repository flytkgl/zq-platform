export type QRCodeDataSource = 'field' | 'formula' | 'static';

export type QRCodeType =
  | 'email'
  | 'sms'
  | 'tel'
  | 'text'
  | 'url'
  | 'vcard'
  | 'wifi';

export type ErrorCorrectionLevel = 'H' | 'L' | 'M' | 'Q';

export interface QRCodeGeneratorProps {
  /** 二维码内容（静态模式） */
  modelValue?: null | string;
  /** 数据源类型 */
  dataSource?: QRCodeDataSource;
  /** 绑定字段（字段模式） */
  boundField?: string;
  /** 公式表达式（公式模式） */
  formula?: string;
  /** 表单数据（用于字段/公式模式） */
  formData?: Record<string, any>;
  /** 二维码类型 */
  qrcodeType?: QRCodeType;
  /** 尺寸（像素） */
  size?: number;
  /** 容错级别 */
  errorCorrectionLevel?: ErrorCorrectionLevel;
  /** 前景色 */
  foregroundColor?: string;
  /** 背景色 */
  backgroundColor?: string;
  /** Logo URL */
  logoUrl?: string;
  /** Logo 尺寸 */
  logoSize?: number;
  /** 边距 */
  margin?: number;
  /** 是否显示内容文本 */
  showContent?: boolean;
  /** 是否启用下载 */
  enableDownload?: boolean;
  /** 是否启用复制 */
  enableCopy?: boolean;
  /** 下载文件名 */
  downloadFilename?: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 只读模式 */
  readonly?: boolean;
  /** 占位提示 */
  placeholder?: string;
}

export interface QRCodeGeneratorEmits {
  (e: 'update:modelValue', value: null | string): void;
  (e: 'change', value: null | string): void;
  (e: 'generated', content: string): void;
  (e: 'downloaded'): void;
  (e: 'copied'): void;
}

/** vCard 联系人信息 */
export interface VCardInfo {
  firstName?: string;
  lastName?: string;
  organization?: string;
  title?: string;
  phone?: string;
  email?: string;
  address?: string;
  website?: string;
}

/** WiFi 配置信息 */
export interface WiFiInfo {
  ssid: string;
  password?: string;
  encryption?: 'nopass' | 'WEP' | 'WPA';
  hidden?: boolean;
}

/** 邮件信息 */
export interface EmailInfo {
  to: string;
  subject?: string;
  body?: string;
}

/** 短信信息 */
export interface SMSInfo {
  phone: string;
  message?: string;
}
