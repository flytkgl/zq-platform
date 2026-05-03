import { requestClient } from '#/api/request';

/**
 * Demo相关类型定义
 */
export interface Demo {
  id: string;
  title: string;
  content?: string;
  status: number;
  priority: number;
  is_active: boolean;
  sort?: number;
  is_deleted?: boolean;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
  sys_creator_id?: string;
  sys_dept_id?: string;
}

export interface DemoCreateInput {
  title: string;
  content?: string;
  status?: number;
  priority?: number;
  is_active?: boolean;
}

export interface DemoUpdateInput extends Partial<DemoCreateInput> {}

export interface DemoListParams {
  page?: number;
  pageSize?: number;
  title?: string;
  status?: number;
  priority?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  pageSize?: number;
}

// ============ Demo API ============

/**
 * 创建Demo
 */
export async function createDemoApi(data: DemoCreateInput) {
  return requestClient.post<Demo>('/api/zq_demo/demos', data);
}

/**
 * 获取Demo列表（分页）
 */
export async function getDemoListApi(params?: DemoListParams) {
  return requestClient.get<PaginatedResponse<Demo>>('/api/zq_demo/demos', {
    params,
  });
}

/**
 * 获取Demo详情
 */
export async function getDemoDetailApi(demoId: string) {
  return requestClient.get<Demo>(`/api/zq_demo/demos/${demoId}`);
}

/**
 * 更新Demo
 */
export async function updateDemoApi(demoId: string, data: DemoUpdateInput) {
  return requestClient.put<Demo>(`/api/zq_demo/demos/${demoId}`, data);
}

/**
 * 删除Demo
 */
export async function deleteDemoApi(demoId: string, hard: boolean = false) {
  return requestClient.delete(`/api/zq_demo/demos/${demoId}`, {
    params: { hard },
  });
}

/**
 * 检查字段唯一性
 */
export async function checkDemoUniqueApi(
  field: string,
  value: string,
  excludeId?: string,
) {
  return requestClient.get<{ unique: boolean }>(
    '/api/zq_demo/demos/check/unique',
    {
      params: {
        field,
        value,
        excludeId,
      },
    },
  );
}

/**
 * 导出Excel
 */
export async function exportDemoExcelApi() {
  return requestClient.get('/api/zq_demo/demos/export/excel', {
    responseType: 'blob',
  });
}

/**
 * 下载导入模板
 */
export async function downloadDemoTemplateApi() {
  return requestClient.get('/api/zq_demo/demos/import/template', {
    responseType: 'blob',
  });
}

/**
 * 导入Excel
 */
export async function importDemoExcelApi(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return requestClient.post('/api/zq_demo/demos/import/excel', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}
