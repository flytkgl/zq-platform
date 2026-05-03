import { requestClient } from '#/api/request';

/**
 * 表单数据操作 API
 * 动态操作表单数据，支持主表和子表的 CRUD、导入导出
 */

// ============ 类型定义 ============

/** 表单数据创建请求 */
export interface FormDataCreateInput {
  main: Record<string, any>;
  sub_tables?: Record<string, Record<string, any>[]>;
}

/** 表单数据更新请求 */
export interface FormDataUpdateInput {
  main: Record<string, any>;
  sub_tables?: Record<string, Record<string, any>[]>;
}

/** 表单数据列表响应 */
export interface FormDataListResponse {
  items: Record<string, any>[];
  total: number;
  page: number;
  page_size: number;
}

/** 表单数据详情（含子表） */
export interface FormDataDetail {
  main: Record<string, any>;
  sub_tables: Record<string, Record<string, any>[]>;
}

/** 列表查询参数 */
export interface FormDataListParams {
  page?: number;
  pageSize?: number;
  sortField?: string;
  sortOrder?: 'asc' | 'desc';
  [key: string]: any; // 动态过滤条件
}

/** 导入错误详情 */
export interface ImportError {
  row: number;
  field: null | string;
  error: string;
  type: 'header' | 'option' | 'required' | 'system' | 'type';
}

/** 导入结果 */
export interface ImportResult {
  success: number;
  fail: number;
  message: string;
  errors: Array<{ row: number; error: string }>;
  validated?: boolean;
  will_insert?: number;
  will_update?: number;
  action?: string;
}

/** 导出任务状态 */
export type ExportTaskStatus =
  | 'cancelled'
  | 'completed'
  | 'expired'
  | 'failed'
  | 'pending'
  | 'processing';

/** 创建导出任务响应 */
export interface CreateExportTaskResponse {
  task_id: string;
  status: ExportTaskStatus;
  message: string;
}

/** 导出任务状态响应 */
export interface ExportTaskStatusResponse {
  task_id: string;
  status: ExportTaskStatus;
  progress: number;
  total_count: number;
  processed_count: number;
  file_size: null | number;
  error_message: null | string;
  created_at: null | string;
  started_at: null | string;
  completed_at: null | string;
  expires_at: null | string;
}

// ============ 权限 API ============

/** 表单操作权限 */
export interface FormPermissions {
  view: boolean;
  add: boolean;
  edit: boolean;
  delete: boolean;
  export: boolean;
  import: boolean;
}

/** 字段权限配置 */
export interface FieldPermission {
  permission_type?: 'hidden' | 'masked' | 'read' | 'write';
  permission?: 'hidden' | 'masked' | 'read' | 'write';
  mask_rule?: 'email' | 'id_card' | 'name' | 'phone' | null;
}

/** 字段权限映射 */
export type FieldPermissions = Record<string, FieldPermission>;

/**
 * 获取当前用户对表单的操作权限
 */
export async function getFormPermissionsApi(
  formCode: string,
): Promise<FormPermissions> {
  return requestClient.get<FormPermissions>(
    `/api/online_dev/form-data/${formCode}/permissions`,
  );
}

/**
 * 获取当前用户对表单的字段权限
 */
export async function getFieldPermissionsApi(
  formCode: string,
): Promise<FieldPermissions> {
  return requestClient.get<FieldPermissions>(
    `/api/online_dev/form-data/${formCode}/field-permissions`,
  );
}

// ============ 表单数据 CRUD API ============

/**
 * 查询表单数据列表
 */
export async function getFormDataListApi(
  formCode: string,
  params?: FormDataListParams,
) {
  return requestClient.get<FormDataListResponse>(
    `/api/online_dev/form-data/${formCode}/list`,
    { params },
  );
}

/** 树形子节点查询参数 */
export interface TreeChildrenParams {
  parentId?: string;
  parentField?: string;
}

/** 树形节点数据 */
export interface TreeNodeData extends Record<string, any> {
  id: string;
  has_children: boolean;
}

/**
 * 获取树形数据子节点（懒加载）
 * @param formCode 表单编码
 * @param params 查询参数
 * @returns 子节点列表
 */
export async function getTreeChildrenApi(
  formCode: string,
  params?: TreeChildrenParams,
) {
  return requestClient.get<TreeNodeData[]>(
    `/api/online_dev/form-data/${formCode}/tree/children`,
    { params },
  );
}

/**
 * 获取表单数据详情（含子表）
 */
export async function getFormDataDetailApi(formCode: string, pk: string) {
  return requestClient.get<FormDataDetail>(
    `/api/online_dev/form-data/${formCode}/detail/${pk}`,
  );
}

/** 字段唯一值响应 */
export interface FieldValuesResponse {
  items: { count: number; label: string; value: any }[];
  total: number;
  hasMore: boolean;
}

/** 字段唯一值查询参数 */
export interface FieldValuesParams {
  page?: number;
  pageSize?: number;
  search?: string;
}

/**
 * 获取字段唯一值列表（用于过滤选项）
 */
export async function getFieldValuesApi(
  formCode: string,
  fieldName: string,
  params?: FieldValuesParams,
) {
  return requestClient.get<FieldValuesResponse>(
    `/api/online_dev/form-data/${formCode}/field-values/${fieldName}`,
    { params },
  );
}

/** 唯一性检查参数 */
export interface CheckUniqueParams {
  field: string;
  value: string;
  excludeId?: string;
}

/** 唯一性检查响应 */
export interface CheckUniqueResponse {
  unique: boolean;
}

/**
 * 检查字段值唯一性
 */
export async function checkFormDataUniqueApi(
  formCode: string,
  params: CheckUniqueParams,
) {
  return requestClient.get<CheckUniqueResponse>(
    `/api/online_dev/form-data/${formCode}/check-unique`,
    { params },
  );
}

/**
 * 新增表单数据
 */
export async function createFormDataApi(
  formCode: string,
  data: FormDataCreateInput,
) {
  return requestClient.post<Record<string, any>>(
    `/api/online_dev/form-data/${formCode}`,
    data,
  );
}

/**
 * 更新表单数据
 */
export async function updateFormDataApi(
  formCode: string,
  pk: string,
  data: FormDataUpdateInput,
) {
  return requestClient.put<Record<string, any>>(
    `/api/online_dev/form-data/${formCode}/${pk}`,
    data,
  );
}

/**
 * 删除表单数据
 */
export async function deleteFormDataApi(formCode: string, pk: string) {
  return requestClient.delete<{ success: boolean }>(
    `/api/online_dev/form-data/${formCode}/${pk}`,
  );
}

/**
 * 批量删除表单数据
 */
export async function batchDeleteFormDataApi(formCode: string, ids: string[]) {
  return requestClient.delete<{ count: number }>(
    `/api/online_dev/form-data/${formCode}/batch/delete`,
    { params: { ids } },
  );
}

// ============ 导入导出 API ============

/**
 * 导出表单数据为 Excel
 */
export async function exportFormDataExcelApi(
  formCode: string,
  options?: {
    ids?: string[];
    includeSubTables?: boolean;
  },
) {
  return requestClient.download<Blob>(
    `/api/online_dev/form-data/${formCode}/export/excel`,
    { params: options },
  );
}

/**
 * 获取导入模板
 */
export async function getImportTemplateApi(formCode: string) {
  return requestClient.download<Blob>(
    `/api/online_dev/form-data/${formCode}/import/template`,
  );
}

/** 导入选项 */
export interface ImportOptions {
  mode?: 'append' | 'overwrite'; // 导入模式：追加或覆盖
  dataHandling?: 'insert_only' | 'update_only' | 'upsert'; // 数据处理方式
  matchField?: string; // 更新模式下的匹配字段
  validateOnly?: boolean; // 是否仅验证数据
}

/**
 * 从 Excel 导入表单数据
 */
export async function importFormDataExcelApi(
  formCode: string,
  file: File,
  options?: ImportOptions,
) {
  const formData = new FormData();
  formData.append('file', file);
  if (options?.mode) {
    formData.append('mode', options.mode);
  }
  if (options?.dataHandling) {
    formData.append('data_handling', options.dataHandling);
  }
  if (options?.matchField) {
    formData.append('match_field', options.matchField);
  }
  if (options?.validateOnly !== undefined) {
    formData.append('validate_only', String(options.validateOnly));
  }

  return requestClient.post<ImportResult>(
    `/api/online_dev/form-data/${formCode}/import/excel`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
  );
}

/** 导入进度回调参数 */
export interface ImportProgressData {
  processed: number;
  total: number;
  percent: number;
  stage: 'importing' | 'parsing';
  success: number;
  fail: number;
}

/** SSE 导入完成回调参数 */
export interface ImportCompletedData {
  success: number;
  fail: number;
  errors: Array<{ row: number; error: string }>;
  message: string;
}

/** 验证进度回调参数 */
export interface ValidateProgressData {
  processed: number;
  total: number;
  percent: number;
  stage: string;
}

/** SSE 验证完成回调参数 */
export interface ValidateCompletedData {
  success: number;
  fail: number;
  errors: Array<{ row: number; error: string }>;
  message: string;
  validated: boolean;
  will_insert: number;
  will_update: number;
  action: string;
}

/**
 * SSE 方式验证导入数据（带实时进度）
 * 返回 abort 函数用于中断请求
 */
export function validateFormDataSSE(
  formCode: string,
  file: File,
  options: Omit<ImportOptions, 'validateOnly'>,
  callbacks: {
    onProgress?: (data: ValidateProgressData) => void;
    onCompleted?: (data: ValidateCompletedData) => void;
    onError?: (message: string) => void;
  },
): { abort: () => void; promise: Promise<void> } {
  const controller = new AbortController();

  const formData = new FormData();
  formData.append('file', file);
  if (options.mode) formData.append('mode', options.mode);
  if (options.dataHandling) formData.append('data_handling', options.dataHandling);
  if (options.matchField) formData.append('match_field', options.matchField);

  let sseBuffer = '';
  let pendingEvent = '';
  let pendingData = '';

  function handleSSEEvent(event: string, dataStr: string) {
    try {
      const parsed = JSON.parse(dataStr);
      switch (event) {
        case 'progress': {
          callbacks.onProgress?.(parsed);
          break;
        }
        case 'completed': {
          callbacks.onCompleted?.(parsed);
          break;
        }
        case 'error': {
          callbacks.onError?.(parsed.message || 'Validate failed');
          break;
        }
      }
    } catch {
      // ignore parse errors
    }
  }

  function flushPending() {
    if (pendingEvent && pendingData) {
      handleSSEEvent(pendingEvent, pendingData);
    }
    pendingEvent = '';
    pendingData = '';
  }

  function parseSseLines(text: string) {
    const lines = text.split('\n');
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        if (pendingEvent && pendingData) flushPending();
        pendingEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        pendingData = line.slice(6);
      } else if (line.trim() === '') {
        flushPending();
      }
    }
  }

  const promise = requestClient.postSSE(
    `/api/online_dev/form-data/${formCode}/import/validate/sse`,
    formData,
    {
      signal: controller.signal,
      onMessage(content: string) {
        sseBuffer += content;
        const lastDoubleNewline = sseBuffer.lastIndexOf('\n\n');
        if (lastDoubleNewline !== -1) {
          const completePart = sseBuffer.slice(0, lastDoubleNewline + 2);
          sseBuffer = sseBuffer.slice(lastDoubleNewline + 2);
          parseSseLines(completePart);
        }
      },
      onEnd() {
        if (sseBuffer.trim()) {
          parseSseLines(sseBuffer);
          flushPending();
        }
        sseBuffer = '';
      },
    },
  );

  return { abort: () => controller.abort(), promise };
}

/**
 * SSE 方式导入表单数据（带实时进度）
 * 返回 abort 函数用于中断请求
 */
export function importFormDataSSE(
  formCode: string,
  file: File,
  options: Omit<ImportOptions, 'validateOnly'>,
  callbacks: {
    onProgress?: (data: ImportProgressData) => void;
    onCompleted?: (data: ImportCompletedData) => void;
    onError?: (message: string) => void;
  },
): { abort: () => void; promise: Promise<void> } {
  const controller = new AbortController();

  const formData = new FormData();
  formData.append('file', file);
  if (options.mode) formData.append('mode', options.mode);
  if (options.dataHandling) formData.append('data_handling', options.dataHandling);
  if (options.matchField) formData.append('match_field', options.matchField);

  let sseBuffer = '';
  let pendingEvent = '';
  let pendingData = '';

  function handleSSEEvent(event: string, dataStr: string) {
    try {
      const parsed = JSON.parse(dataStr);
      switch (event) {
        case 'progress': {
          callbacks.onProgress?.(parsed);
          break;
        }
        case 'completed': {
          callbacks.onCompleted?.(parsed);
          break;
        }
        case 'error': {
          callbacks.onError?.(parsed.message || 'Import failed');
          break;
        }
      }
    } catch {
      // ignore parse errors
    }
  }

  function flushPending() {
    if (pendingEvent && pendingData) {
      handleSSEEvent(pendingEvent, pendingData);
    }
    pendingEvent = '';
    pendingData = '';
  }

  function parseSseLines(text: string) {
    const lines = text.split('\n');
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        if (pendingEvent && pendingData) flushPending();
        pendingEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        pendingData = line.slice(6);
      } else if (line.trim() === '') {
        flushPending();
      }
    }
  }

  const promise = requestClient.postSSE(
    `/api/online_dev/form-data/${formCode}/import/sse`,
    formData,
    {
      signal: controller.signal,
      onMessage(content: string) {
        sseBuffer += content;
        const lastDoubleNewline = sseBuffer.lastIndexOf('\n\n');
        if (lastDoubleNewline !== -1) {
          const completePart = sseBuffer.slice(0, lastDoubleNewline + 2);
          sseBuffer = sseBuffer.slice(lastDoubleNewline + 2);
          parseSseLines(completePart);
        }
      },
      onEnd() {
        if (sseBuffer.trim()) {
          parseSseLines(sseBuffer);
          flushPending();
        }
        sseBuffer = '';
      },
    },
  );

  return { abort: () => controller.abort(), promise };
}

// ============ 配置 ============

export interface ImportExportConfig {
  maxRows: number;
  serverMemoryGB: number;
}

/**
 * 获取导入导出配置（最大行数等）
 */
export function getImportExportConfigApi(): Promise<ImportExportConfig> {
  return requestClient.get('/api/online_dev/form-data/import-export/config');
}

// ============ 辅助函数 ============

/**
 * 下载 Blob 文件
 */
export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

/**
 * 导出并下载表单数据
 */
export async function downloadFormDataExcel(
  formCode: string,
  options?: {
    filename?: string;
    ids?: string[];
    includeSubTables?: boolean;
  },
) {
  const blob = await exportFormDataExcelApi(formCode, {
    ids: options?.ids,
    includeSubTables: options?.includeSubTables,
  });
  downloadBlob(blob, options?.filename || `${formCode}_data.xlsx`);
}

/**
 * 下载导入模板
 */
export async function downloadImportTemplate(
  formCode: string,
  filename?: string,
) {
  const blob = await getImportTemplateApi(formCode);
  downloadBlob(blob, filename || `${formCode}_import_template.xlsx`);
}

// ============ 异步导出任务 API ============

/**
 * 创建异步导出任务
 */
export async function createExportTaskApi(
  formCode: string,
  options?: {
    ids?: string[];
    includeSubTables?: boolean;
  },
) {
  return requestClient.post<CreateExportTaskResponse>(
    `/api/online_dev/form-data/${formCode}/export/task`,
    null,
    { params: options },
  );
}

/**
 * 获取导出任务状态
 */
export async function getExportTaskStatusApi(formCode: string, taskId: string) {
  return requestClient.get<ExportTaskStatusResponse>(
    `/api/online_dev/form-data/${formCode}/export/task/${taskId}/status`,
  );
}

/**
 * 下载导出任务文件
 */
export async function downloadExportTaskFileApi(
  formCode: string,
  taskId: string,
) {
  return requestClient.download<Blob>(
    `/api/online_dev/form-data/${formCode}/export/task/${taskId}/download`,
  );
}

/**
 * 取消导出任务
 */
export async function cancelExportTaskApi(formCode: string, taskId: string) {
  return requestClient.post<{ message: string; success: boolean }>(
    `/api/online_dev/form-data/${formCode}/export/task/${taskId}/cancel`,
  );
}

/**
 * 轮询导出任务状态直到完成或失败
 * 支持页面离开时自动停止轮询
 */
export function pollExportTask(
  formCode: string,
  taskId: string,
  options?: {
    filename?: string;
    onProgress?: (
      progress: number,
      status: ExportTaskStatus,
      details?: ExportTaskStatusResponse,
    ) => void;
    pollInterval?: number;
  },
): { promise: Promise<void>; stop: () => void } {
  const { onProgress, pollInterval = 3000 } = options || {}; // 默认3秒

  let stopped = false;
  let timeoutId: null | ReturnType<typeof setTimeout> = null;

  const stop = () => {
    stopped = true;
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  const promise = new Promise<void>((resolve, reject) => {
    const poll = async () => {
      if (stopped) {
        return; // 已停止，不再轮询
      }

      try {
        console.log(`[轮询] 查询任务状态: ${taskId}`);
        const status = await getExportTaskStatusApi(formCode, taskId);
        console.log(`[轮询] 任务状态:`, status);

        if (stopped) return; // 请求期间可能被停止

        onProgress?.(status.progress, status.status, status);

        switch (status.status) {
          case 'cancelled': {
            reject(new Error('导出任务已取消'));

            break;
          }
          case 'completed': {
            // 下载文件
            const blob = await downloadExportTaskFileApi(formCode, taskId);
            downloadBlob(blob, options?.filename || `${formCode}_data.xlsx`);
            resolve();

            break;
          }
          case 'expired': {
            reject(new Error('导出任务已过期'));

            break;
          }
          case 'failed': {
            reject(new Error(status.error_message || '导出失败'));

            break;
          }
          default: {
            if (!stopped) {
              // 继续轮询
              timeoutId = setTimeout(poll, pollInterval);
            }
          }
        }
      } catch (error) {
        if (!stopped) {
          reject(error);
        }
      }
    };

    poll();
  });

  return { promise, stop };
}

/**
 * 异步导出并下载（带轮询）
 */
export async function asyncExportFormData(
  formCode: string,
  options?: {
    filename?: string;
    ids?: string[];
    includeSubTables?: boolean;
    onProgress?: (
      progress: number,
      status: ExportTaskStatus,
      details?: ExportTaskStatusResponse,
    ) => void;
    pollInterval?: number;
  },
): Promise<{ stop: () => void }> {
  // 1. 创建任务
  const { task_id } = await createExportTaskApi(formCode, {
    ids: options?.ids,
    includeSubTables: options?.includeSubTables,
  });

  // 2. 轮询状态
  const { promise, stop } = pollExportTask(formCode, task_id, options);
  await promise;
  return { stop };
}
