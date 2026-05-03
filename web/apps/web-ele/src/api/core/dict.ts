import { requestClient } from '#/api/request';

/**
 * 字典相关类型定义
 */
export interface Dict {
  id: string;
  application_id?: string;
  application_name?: string;
  is_global?: boolean;
  name: string;
  code: string;
  status: boolean;
  remark?: string;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface DictCreateInput {
  application_id?: string;
  is_global?: boolean;
  name: string;
  code: string;
  status?: boolean;
  remark?: string;
}

export interface DictUpdateInput extends Partial<DictCreateInput> {}

export interface DictListParams {
  page?: number;
  pageSize?: number;
  applicationId?: string;
  name?: string;
  code?: string;
  status?: boolean;
}

/**
 * 字典项相关类型定义
 */
export interface DictItem {
  id: string;
  dict_id: string;
  label?: string;
  value?: string;
  icon?: string;
  sort?: number;
  status: boolean;
  remark?: string;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface DictItemCreateInput {
  dict_id: string;
  label?: string;
  value?: string;
  icon?: string;
  sort?: number;
  status?: boolean;
  remark?: string;
}

export interface DictItemUpdateInput extends Partial<DictItemCreateInput> {}

export interface DictItemListParams {
  page?: number;
  pageSize?: number;
  dict_id?: string;
  label?: string;
  value?: string;
  status?: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

// ============ 字典API ============

/**
 * 创建字典
 */
export async function createDictApi(data: DictCreateInput) {
  return requestClient.post<Dict>('/api/core/dict', data);
}

/**
 * 获取字典列表（分页）
 */
export async function getDictListApi(params?: DictListParams) {
  return requestClient.get<PaginatedResponse<Dict>>('/api/core/dict', {
    params,
  });
}

/**
 * 获取所有字典（不分页）
 */
export async function getAllDictApi(applicationId?: string) {
  return requestClient.get<Dict[]>('/api/core/dict/all', {
    params: { applicationId },
  });
}

/**
 * 获取字典详情
 */
export async function getDictDetailApi(dictId: string) {
  return requestClient.get<Dict>(`/api/core/dict/${dictId}`);
}

/**
 * 更新字典
 */
export async function updateDictApi(dictId: string, data: DictUpdateInput) {
  return requestClient.put<Dict>(`/api/core/dict/${dictId}`, data);
}

/**
 * 删除字典
 */
export async function deleteDictApi(dictId: string) {
  return requestClient.delete<Dict>(`/api/core/dict/${dictId}`);
}

// ============ 字典项API ============

/**
 * 创建字典项
 */
export async function createDictItemApi(data: DictItemCreateInput) {
  return requestClient.post<DictItem>('/api/core/dict_item', data);
}

/**
 * 获取字典项列表（分页）
 */
export async function getDictItemListApi(params?: DictItemListParams) {
  return requestClient.get<PaginatedResponse<DictItem>>('/api/core/dict_item', {
    params,
  });
}

/**
 * 获取所有字典项（不分页）
 */
export async function getAllDictItemApi() {
  return requestClient.get<DictItem[]>('/api/core/dict_item/get/all');
}

/**
 * 根据字典编码获取字典项
 */
export async function getDictItemByCodeApi(code: string) {
  return requestClient.get<DictItem[]>(
    `/api/core/dict_item/by/dict_code/${code}`,
  );
}

/**
 * 获取字典项详情
 */
export async function getDictItemDetailApi(dictItemId: string) {
  return requestClient.get<DictItem>(`/api/core/dict_item/${dictItemId}`);
}

/**
 * 更新字典项
 */
export async function updateDictItemApi(
  dictItemId: string,
  data: DictItemUpdateInput,
) {
  return requestClient.put<DictItem>(`/api/core/dict_item/${dictItemId}`, data);
}

/**
 * 删除字典项
 */
export async function deleteDictItemApi(dictItemId: string) {
  return requestClient.delete<DictItem>(`/api/core/dict_item/${dictItemId}`);
}
