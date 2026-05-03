export type GenerateMode =
  | 'custom' // 自定义模板
  | 'date_seq' // 日期+序号: PREFIX20241222-0001
  | 'datetime' // 日期时间: PREFIX20241222103000
  | 'random' // 随机字符: PREFIX-X7K9M2
  | 'snowflake' // 雪花ID: PREFIX1234567890123456
  | 'uuid'; // UUID片段: PREFIX-a1b2c3d4

export type SeqResetRule = 'daily' | 'monthly' | 'never' | 'yearly';

export interface CodeGeneratorProps {
  modelValue?: string;
  prefix?: string;
  separator?: string;
  generateMode?: GenerateMode;
  dateFormat?: string;
  seqLength?: number;
  seqResetRule?: SeqResetRule;
  randomLength?: number;
  customTemplate?: string;
  businessType?: string;
  disabled?: boolean;
  readonly?: boolean;
  placeholder?: string;
  generateOnMount?: boolean;
  /** 是否为编辑模式，编辑模式下不自动生成编码 */
  isEdit?: boolean;
}

export interface CodeGeneratorEmits {
  (e: 'update:modelValue', value: string): void;
  (e: 'change', value: string): void;
}
