/** 导入结果 */
export interface ImportResult {
  success: number;
  failed: number;
  errors: ImportError[];
  warnings?: string[];
}

/** 导入错误详情 */
export interface ImportError {
  row: number;
  field: null | string;
  error: string;
  type: 'header' | 'option' | 'required' | 'system' | 'type';
}

/** 导出选项 */
export interface ExportOptions {
  ids?: string[];
  includeSubTables?: boolean;
  filename?: string;
}

/** 任务状态 */
export type TaskStatus =
  | 'cancelled'
  | 'failed'
  | 'pending'
  | 'running'
  | 'success';

/** 任务记录 */
export interface TaskRecord {
  id: string;
  type: 'export' | 'import';
  filename: string;
  status: TaskStatus;
  startTime: Date;
  endTime?: Date;
  progress?: number;
  totalCount?: number; // 总条数
  processedCount?: number; // 已处理条数
  result?: ImportResult | { count: number };
  error?: string;
  expiresAt?: string; // 任务过期时间
  options?: ExportOptions; // 导出选项，用于重试
}

/** 组件 Props */
export interface ImportExportManagerProps {
  /** 表单编码 */
  formCode: string;
  /** 表单名称 */
  formName?: string;
  /** 是否显示导入功能 */
  showImport?: boolean;
  /** 是否显示导出功能 */
  showExport?: boolean;
  /** 是否显示下载模板 */
  showTemplate?: boolean;
}

/** 组件 Emits */
export interface ImportExportManagerEmits {
  (e: 'import-success', result: ImportResult): void;
  (e: 'export-success'): void;
}
