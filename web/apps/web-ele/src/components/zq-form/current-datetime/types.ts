export interface CurrentDatetimeProps {
  modelValue?: string;
  type?: 'date' | 'datetime' | 'time';
  format?: string;
  valueFormat?: string;
  disabled?: boolean;
  placeholder?: string;
  autoUpdate?: boolean;
  /** 填充模式: onCreate-仅创建时填充, onUpdate-每次更新时填充, always-始终填充 */
  fillMode?: 'always' | 'onCreate' | 'onUpdate';
}

export interface CurrentDatetimeEmits {
  (e: 'update:modelValue', value: string): void;
  (e: 'change', value: string): void;
}
