import { requestClient } from '#/api/request';

/**
 * 表单管理 API
 * 表单元数据的 CRUD、发布、复制、导入导出
 */

// ============ 类型定义 ============

/** 子表配置 */
export interface FormSubTable {
  id?: string;
  table_name: string;
  table_schema?: string;
  table_database?: string;
  alias?: string;
  foreign_key: string;
  related_field?: string;
  relation_type?: string;
  sort?: number;
}

/** 表单类型 */
export type FormType = 'normal' | 'workflow';

/** 表单元数据 */
export interface FormMeta {
  id: string;
  application_id?: string;
  name: string;
  code: string;
  form_type: FormType;
  description: string;
  status: string;
  version: number;
  db_config: string;
  main_table: string;
  main_table_schema: string;
  main_table_database: string;
  form_config: Record<string, any>;
  list_config: Record<string, any>;
  sort: number;
  show_in_mobile: boolean;
  icon: string;
  icon_bg_color: string;
  sys_create_datetime: string;
  sys_update_datetime: string;
  sub_tables?: FormSubTable[];
}

/** 表单列表项 */
export interface FormMetaListItem {
  id: string;
  application_id?: string;
  application_name: string;
  application_code?: string;
  name: string;
  code: string;
  form_type: FormType;
  description: string;
  status: string;
  version: number;
  main_table: string;
  sort: number;
  sys_create_datetime: string;
  sys_update_datetime: string;
}

/** 创建表单请求 */
export interface FormMetaCreateInput {
  application_id?: string;
  name: string;
  code: string;
  form_type?: FormType;
  description?: string;
  sort?: number;
  db_config: string;
  main_table: string;
  main_table_schema?: string;
  main_table_database?: string;
  form_config?: Record<string, any>;
  list_config?: Record<string, any>;
  sub_tables?: FormSubTable[];
}

/** 更新表单请求 */
export interface FormMetaUpdateInput {
  name?: string;
  form_type?: FormType;
  description?: string;
  sort?: number;
  show_in_mobile?: boolean;
  icon?: string;
  icon_bg_color?: string;
  form_config?: Record<string, any>;
  list_config?: Record<string, any>;
  sub_tables?: FormSubTable[];
}

/** 导入表单请求 */
export interface FormImportInput {
  name: string;
  code: string;
  form_type?: FormType;
  description?: string;
  db_config: string;
  main_table: string;
  main_table_schema?: string;
  main_table_database?: string;
  form_config?: Record<string, any>;
  list_config?: Record<string, any>;
  sub_tables?: FormSubTable[];
}

/** 列表查询参数 */
export interface FormListParams {
  page?: number;
  pageSize?: number;
  applicationId?: string;
  name?: string;
  code?: string;
  form_type?: FormType;
  status?: string;
}

/** 发布配置 */
export interface FormPublishInput {
  /** 菜单名称 */
  menu_name: string;
  /** 上级菜单ID */
  menu_parent_id?: string;
  /** 菜单图标 */
  menu_icon?: string;
  /** 菜单排序 */
  menu_order?: number;
}

/** 分页响应 */
interface FormPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

// ============ 表单元数据 API ============

/**
 * 获取表单列表（分页）
 */
export async function getFormListApi(params?: FormListParams) {
  return requestClient.get<FormPaginatedResponse<FormMetaListItem>>(
    '/api/online_dev/form/list',
    { params },
  );
}

/**
 * 获取分类列表
 */
export async function getFormCategoriesApi() {
  return requestClient.get<string[]>('/api/online_dev/form/categories');
}

/**
 * 获取表单详情
 */
export async function getFormDetailApi(formId: string) {
  return requestClient.get<FormMeta>(`/api/online_dev/form/${formId}`);
}

/**
 * 根据编码获取表单
 */
export async function getFormByCodeApi(code: string) {
  return requestClient.get<FormMeta>(`/api/online_dev/form/code/${code}`);
}

/**
 * 创建表单
 */
export async function createFormApi(data: FormMetaCreateInput) {
  return requestClient.post<FormMeta>('/api/online_dev/form', data);
}

/**
 * 更新表单
 */
export async function updateFormApi(formId: string, data: FormMetaUpdateInput) {
  return requestClient.put<FormMeta>(`/api/online_dev/form/${formId}`, data);
}

/**
 * 删除表单
 */
export async function deleteFormApi(formId: string) {
  return requestClient.delete<FormMeta>(`/api/online_dev/form/${formId}`);
}

/**
 * 批量删除表单
 */
export async function batchDeleteFormApi(ids: string[]) {
  return requestClient.delete<{ count: number }>(
    '/api/online_dev/form/batch/delete',
    {
      params: { ids },
    },
  );
}

/**
 * 发布表单
 */
export async function publishFormApi(formId: string, data: FormPublishInput) {
  return requestClient.post<FormMeta>(
    `/api/online_dev/form/${formId}/publish`,
    data,
  );
}

/**
 * 取消发布表单
 */
export async function unpublishFormApi(formId: string) {
  return requestClient.post<FormMeta>(
    `/api/online_dev/form/${formId}/unpublish`,
  );
}

/**
 * 复制表单
 */
export async function copyFormApi(
  formId: string,
  newCode: string,
  newName?: string,
) {
  return requestClient.post<FormMeta>(
    `/api/online_dev/form/${formId}/copy`,
    null,
    {
      params: { new_code: newCode, new_name: newName },
    },
  );
}

/**
 * 导出表单配置（返回 JSON 文件）
 */
export async function exportFormConfigApi(formId: string) {
  return requestClient.get<Blob>(`/api/online_dev/form/${formId}/export`, {
    responseType: 'blob',
  });
}

/**
 * 导入表单配置
 */
export async function importFormConfigApi(data: FormImportInput) {
  return requestClient.post<FormMeta>('/api/online_dev/form/import', data);
}

/** 已发布表单简单信息 */
export interface PublishedFormSimple {
  code: string;
  name: string;
  mainTable: string;
  fields: Array<{
    field: string;
    label: string;
    type: string;
  }>;
}

/**
 * 获取已发布表单简单列表（用于下拉选择）
 */
export async function getPublishedFormsSimpleApi(applicationId?: string) {
  return requestClient.get<PublishedFormSimple[]>(
    '/api/online_dev/form/published/simple',
    { params: { applicationId } },
  );
}
