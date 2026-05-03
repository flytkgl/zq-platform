export interface MoneyInputProps {
  modelValue?: number | string;
  precision?: number;
  currencySymbol?: string;
  showCurrency?: boolean;
  showThousandSeparator?: boolean;
  showCapital?: boolean;
  min?: number;
  max?: number;
  disabled?: boolean;
  readonly?: boolean;
  placeholder?: string;
}

export interface MoneyInputEmits {
  (e: 'update:modelValue', value: number | string): void;
  (e: 'change', value: number | string): void;
}
