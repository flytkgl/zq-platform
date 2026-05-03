export interface CurrentUserProps {
  modelValue?: string;
  displayField?: 'name' | 'nickname' | 'username';
  valueField?: 'id' | 'realName' | 'username';
  showAvatar?: boolean;
  disabled?: boolean;
  placeholder?: string;
  /** 填充模式: onCreate-仅创建时填充, always-始终填充 */
  fillMode?: 'always' | 'onCreate';
}

export interface CurrentUserEmits {
  (e: 'update:modelValue', value: string): void;
  (e: 'change', value: string): void;
}
