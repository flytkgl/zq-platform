export interface FormulaInputProps {
  modelValue?: number | string;
  formula?: string;
  formData?: Record<string, any>;
  precision?: number;
  disabled?: boolean;
  placeholder?: string;
  showFormula?: boolean;
}

export interface FormulaInputEmits {
  (e: 'update:modelValue', value: number | string): void;
  (e: 'change', value: number | string): void;
}
