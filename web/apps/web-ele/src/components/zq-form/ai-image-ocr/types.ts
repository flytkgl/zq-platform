export interface AiImageOcrProps {
  modelValue?: string | string[];
  multiple?: boolean;
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  maxSize?: number;
}

export interface AiImageOcrEmits {
  (e: 'update:modelValue', value: string | string[] | undefined): void;
  (e: 'change', value: string | string[] | undefined): void;
  (
    e: 'ocr-success',
    data: { extractedData: null | Record<string, any>; rawText: string },
  ): void;
  (e: 'fill-fields', data: Record<string, any>): void;
}
