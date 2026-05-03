export enum FieldType {
  Text = 'text',
  Number = 'number',
  SingleSelect = 'singleSelect',
  MultiSelect = 'multiSelect',
  Date = 'date',
  Checkbox = 'checkbox',
  Person = 'person',
  Attachment = 'attachment',
  URL = 'url',
  Email = 'email',
  Phone = 'phone',
  Rating = 'rating',
  Progress = 'progress',
  Currency = 'currency',
  AutoNumber = 'autoNumber',
  Location = 'location',
  CreatedTime = 'createdTime',
  ModifiedTime = 'modifiedTime',
  CreatedBy = 'createdBy',
  ModifiedBy = 'modifiedBy',
  Formula = 'formula',
  RichText = 'richText',
  User = 'user',
  Department = 'department',
  Region = 'region',
  Image = 'image',
  Link = 'link',
  Lookup = 'lookup',
  Rollup = 'rollup',
}

export type NumberFormat = 'number' | 'currency' | 'percent' | 'yuan'
export type CurrencySymbol = '¥' | '$' | '€' | '£' | '₩'

export interface SelectOption {
  id: string
  label: string
  color: string
}

export interface AttachmentItem {
  id: string
  name: string
  size: number
  type: string
  url: string
  thumbnailUrl?: string
}

export type RollupAggregation = 'COUNT' | 'COUNTA' | 'SUM' | 'AVG' | 'MIN' | 'MAX'

export interface FieldValidation {
  min?: number | null
  max?: number | null
  minLength?: number | null
  maxLength?: number | null
  pattern?: string | null
  unique?: boolean
  message?: string
}

export interface LinkedRecordItem {
  id: string
  title: string
}

export interface FieldConfig {
  id: string
  name: string
  type: FieldType
  width: number
  visible: boolean
  required: boolean
  description?: string
  options?: SelectOption[]
  precision?: number
  numberFormat?: NumberFormat
  dateFormat?: string
  includeTime?: boolean
  maxRating?: number
  currencySymbol?: CurrencySymbol
  formula?: string
  formulaResultType?: 'text' | 'number' | 'date' | 'boolean'
  multiple?: boolean
  regionLevel?: 'province' | 'city' | 'district'
  maxImageCount?: number
  linkedTableId?: string
  symmetricFieldId?: string
  linkFieldId?: string
  lookupFieldId?: string
  rollupFieldId?: string
  aggregation?: RollupAggregation
  validation?: FieldValidation
}

export const FIELD_TYPE_LABELS: Record<FieldType, string> = {
  [FieldType.Text]: 'field.text',
  [FieldType.Number]: 'field.number',
  [FieldType.SingleSelect]: 'field.singleSelect',
  [FieldType.MultiSelect]: 'field.multiSelect',
  [FieldType.Date]: 'field.date',
  [FieldType.Checkbox]: 'field.checkbox',
  [FieldType.Person]: 'field.person',
  [FieldType.Attachment]: 'field.attachment',
  [FieldType.URL]: 'field.url',
  [FieldType.Email]: 'field.email',
  [FieldType.Phone]: 'field.phone',
  [FieldType.Rating]: 'field.rating',
  [FieldType.Progress]: 'field.progress',
  [FieldType.Currency]: 'field.currency',
  [FieldType.AutoNumber]: 'field.autoNumber',
  [FieldType.Location]: 'field.location',
  [FieldType.CreatedTime]: 'field.createdTime',
  [FieldType.ModifiedTime]: 'field.modifiedTime',
  [FieldType.CreatedBy]: 'field.createdBy',
  [FieldType.ModifiedBy]: 'field.modifiedBy',
  [FieldType.Formula]: 'field.formula',
  [FieldType.RichText]: 'field.richText',
  [FieldType.User]: 'field.user',
  [FieldType.Department]: 'field.department',
  [FieldType.Region]: 'field.region',
  [FieldType.Image]: 'field.image',
  [FieldType.Link]: 'field.link',
  [FieldType.Lookup]: 'field.lookup',
  [FieldType.Rollup]: 'field.rollup',
}

export const SELECT_COLORS = [
  '#4e83fd', '#36b37e', '#ff991f', '#f54a45',
  '#8777d9', '#00b8d9', '#ff6b6b', '#36b37e',
  '#ffc400', '#6554c0', '#00c7e6', '#ff8f73',
]
