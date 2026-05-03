import type { FieldConfig, AttachmentItem } from './field'

export type CellValue = string | number | boolean | string[] | AttachmentItem[] | null | undefined

export type DependencyType = 'FS' | 'FF' | 'SS' | 'SF'

export interface GanttDependency {
  id: string
  fromRecordId: string
  toRecordId: string
  type: DependencyType
}

export interface Record {
  id: string
  values: { [fieldId: string]: CellValue }
  createdTime: string
  modifiedTime: string
  createdBy?: string
  modifiedBy?: string
}

export enum ViewType {
  Grid = 'grid',
  Kanban = 'kanban',
  Gallery = 'gallery',
  Form = 'form',
  Calendar = 'calendar',
  Gantt = 'gantt',
}

export interface SortRule {
  fieldId: string
  direction: 'asc' | 'desc'
}

export interface FilterRule {
  fieldId: string
  operator: FilterOperator
  value: CellValue
}

export enum FilterOperator {
  Equals = 'equals',
  NotEquals = 'notEquals',
  Contains = 'contains',
  NotContains = 'notContains',
  IsEmpty = 'isEmpty',
  IsNotEmpty = 'isNotEmpty',
  GreaterThan = 'greaterThan',
  LessThan = 'lessThan',
}

export interface GroupRule {
  fieldId: string
}

export type RowHeight = 'short' | 'medium' | 'tall' | 'extraTall'

export interface ConditionalFormatRule {
  id: string
  fieldId: string
  operator: FilterOperator
  value: CellValue
  bgColor: string
  textColor: string
  applyToRow: boolean
}

export type SummaryAggregation =
  | 'SUM' | 'AVG' | 'MIN' | 'MAX'
  | 'COUNT' | 'COUNTA' | 'COUNT_EMPTY'
  | 'PERCENT_EMPTY' | 'PERCENT_FILLED'

export interface ViewConfig {
  id: string
  name: string
  type: ViewType
  filters: FilterRule[]
  filterLogic: 'and' | 'or'
  sorts: SortRule[]
  groups: GroupRule[]
  visibleFieldIds: string[]
  conditionalFormats?: ConditionalFormatRule[]
  kanbanFieldId?: string
  ganttStartFieldId?: string
  ganttEndFieldId?: string
  ganttDependencies?: GanttDependency[]
  ganttMilestoneFieldId?: string
  calendarDateFieldId?: string
  calendarEndDateFieldId?: string
  calendarMode?: 'month' | 'week' | 'day'
  rowHeight?: RowHeight
  zebra?: boolean
  frozenFieldId?: string
  summaryConfig?: Record<string, SummaryAggregation>
}

export enum SmartItemType {
  Table = 'table',
  Document = 'document',
}

export interface Table {
  id: string
  name: string
  icon: string
  type: SmartItemType
  parentId?: string | null
  wikiSpaceId?: string | null
  content?: any
  cover?: string | null
  emoji?: string | null
  fields: FieldConfig[]
  records: Record[]
  views: ViewConfig[]
  activeViewId: string
  children?: Table[]
  createdAt?: string
  updatedAt?: string
  creatorId?: string
  creatorName?: string
  creatorAvatar?: string
}

export interface WikiSpace {
  id: string
  name: string
  icon: string
  avatar?: string | null
  description?: string
  cover?: string | null
  category: string
  visibility: string
  documentCount?: number
  createdAt?: string
  updatedAt?: string
  creatorId?: string
  creatorName?: string
}
