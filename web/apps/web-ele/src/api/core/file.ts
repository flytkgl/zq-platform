/**
 * -*- coding: utf-8 -*-
 * time: 2024/12/19
 * author: 臧成龙
 * QQ: 939589097
 */
import { requestClient } from '#/api/request';

export namespace SystemFileManagerApi {
  export interface FileItem {
    [key: string]: any;
    id?: string;
    name: string;
    path: string;
    file_type: 'file' | 'folder'; // 后端返回 file_type
    file_size?: number; // 后端返回 file_size
    file_ext?: string;
    parent_id?: string;
    updated_time?: string; // 后端返回 updated_time
    has_children?: boolean;
  }

  export interface FolderTree {
    id: string;
    name: string;
    path: string;
    parent_id?: string;
    children?: FolderTree[];
  }

  export interface FileListParams {
    path?: string;
    parent_id?: null | string;
    type?: 'file' | 'folder';
    page?: number;
    pageSize?: number;
  }

  export interface FileListResult {
    items: FileItem[];
    total: number;
  }

  export interface StorageConfig {
    [key: string]: any;
    storage_type?: string;
    max_file_size?: number;
    allowed_extensions?: string[];
  }

  export interface MoveParams {
    source_ids: string[];
    target_parent_id: string;
  }

  export interface RenameParams {
    name: string;
  }

  export interface BatchDeleteParams {
    ids: string[];
  }

  export interface FolderCreateParams {
    name: string;
    parent_id?: string;
    path?: string;
  }

  export interface CreateAccessTokenParams {
    fileId: string;
    expiresIn?: number;
  }

  export interface AccessTokenResponse {
    token: string;
    expiresAt: string;
    fileId: string;
  }

  export interface AccessTokenUrlResponse {
    url: string;
    token: string;
    expiresAt: string;
  }
}

/**
 * 获取文件列表
 * @param params 查询参数
 */
async function getFileList(params?: SystemFileManagerApi.FileListParams) {
  return requestClient.get<SystemFileManagerApi.FileListResult>(
    '/api/core/file_manager',
    { params },
  );
}

/**
 * 获取最近上传的图片
 * @param limit 数量，默认20
 */
async function getRecentImages(limit: number = 20) {
  return requestClient.get<SystemFileManagerApi.FileItem[]>(
    '/api/core/file_manager/recent/images',
    { params: { limit } },
  );
}

/**
 * 获取最近上传的文件（所有类型）
 * @param limit 数量，默认20
 */
async function getRecentFiles(limit: number = 20) {
  return requestClient.get<SystemFileManagerApi.FileItem[]>(
    '/api/core/file_manager/recent/files',
    { params: { limit } },
  );
}

/**
 * 上传文件
 * @param file 文件对象
 * @param options 上传选项
 * @param options.parentId 父文件夹ID
 * @param options.isPublic 是否公开（公开文件无需认证即可访问）
 * @param options.onProgress 上传进度回调
 */
async function uploadFile(
  file: File,
  options?: {
    isPublic?: boolean;
    onProgress?: (progressEvent: {
      loaded: number;
      percentage: number;
      total: number;
    }) => void;
    parentId?: string;
    source?: string;
  },
) {
  const { parentId, isPublic = false, source, onProgress } = options || {};
  return requestClient.upload(
    '/api/core/file_manager/upload',
    {
      file,
      parent_id: parentId || undefined,
      is_public: isPublic,
      source: source || undefined,
    },
    {
      onUploadProgress: (progressEvent: any) => {
        if (onProgress && progressEvent.total) {
          const percentage = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          onProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            percentage,
          });
        }
      },
    },
  );
}

/**
 * 创建文件夹
 * @param data 文件夹数据
 */
async function createFolder(data: SystemFileManagerApi.FolderCreateParams) {
  return requestClient.post('/api/core/file_manager/folder', data);
}

/**
 * 获取文件夹树
 */
async function getFolderTree() {
  return requestClient.get<Array<SystemFileManagerApi.FolderTree>>(
    '/api/core/file_manager/tree',
  );
}

/**
 * 重命名文件/文件夹
 * @param id 文件/文件夹ID
 * @param data 重命名数据
 */
async function renameItem(id: string, data: SystemFileManagerApi.RenameParams) {
  return requestClient.put(`/api/core/file_manager/${id}/rename`, data);
}

/**
 * 移动文件/文件夹
 * @param data 移动参数
 */
async function moveItems(data: SystemFileManagerApi.MoveParams) {
  return requestClient.put('/api/core/file_manager/move', data);
}

/**
 * 删除文件/文件夹
 * @param id 文件/文件夹ID
 */
async function deleteItem(id: string) {
  return requestClient.delete(`/api/core/file_manager/${id}`);
}

/**
 * 批量删除文件/文件夹
 * @param data 批量删除参数
 */
async function batchDelete(data: SystemFileManagerApi.BatchDeleteParams) {
  return requestClient.post('/api/core/file_manager/batch/delete', data);
}

/**
 * 获取下载链接
 * @param path 文件路径
 */
function getDownloadUrl(path: string): string {
  return `/basic-api/api/core/file_manager/file/download?path=${encodeURIComponent(path)}`;
}

/**
 * 获取存储配置
 */
async function getStorageConfig() {
  return requestClient.get<SystemFileManagerApi.StorageConfig>(
    '/api/core/file_manager/storage_config',
  );
}

/**
 * 更新存储配置
 * @param data 存储配置数据
 */
async function updateStorageConfig(data: SystemFileManagerApi.StorageConfig) {
  return requestClient.put('/api/core/file_manager/storage_config', data);
}

/**
 * 通过文件ID获取文件访问URL
 * @param fileId 文件ID
 */
async function getFileUrlById(fileId: string) {
  return requestClient.get<{ url: string }>(
    `/api/core/file_manager/url/${fileId}`,
  );
}

/**
 * 批量获取文件访问URL
 * @param fileIds 文件ID数组
 */
async function getBatchFileUrls(fileIds: string[]) {
  const ids = fileIds.join(',');
  return requestClient.get<{ data: Record<string, string> }>(
    `/api/core/file_manager/batch/urls`,
    {
      params: { ids },
    },
  );
}

/**
 * 创建临时访问令牌
 * @param params 创建参数
 */
async function createAccessToken(
  params: SystemFileManagerApi.CreateAccessTokenParams,
) {
  return requestClient.post<SystemFileManagerApi.AccessTokenResponse>(
    '/api/core/file_manager/access-token',
    params,
  );
}

/**
 * 获取带临时令牌的文件URL
 * @param fileId 文件ID
 * @param expiresIn 过期时间（秒），默认1小时
 */
async function getFileUrlWithToken(fileId: string, expiresIn: number = 3600) {
  return requestClient.get<SystemFileManagerApi.AccessTokenUrlResponse>(
    `/api/core/file_manager/access-token/url/${fileId}`,
    {
      params: { expiresIn },
    },
  );
}

/**
 * 撤销临时访问令牌
 * @param token 令牌
 */
async function revokeAccessToken(token: string) {
  return requestClient.delete(`/api/core/file_manager/access-token/${token}`);
}

/**
 * 获取文件流式传输URL（用于img src等直接访问）
 * 注意：此方法已废弃，建议使用 getFileUrlWithToken 获取带临时令牌的URL
 * @param fileId 文件ID
 * @deprecated 使用 getFileUrlWithToken 替代
 */
function getFileStreamUrl(fileId: string): string {
  return `/basic-api/api/core/file_manager/stream/${fileId}`;
}

/**
 * 获取文件流式传输URL（带临时令牌）
 * @param fileId 文件ID
 * @param token 临时访问令牌
 */
function getFileStreamUrlWithToken(fileId: string, token: string): string {
  return `/basic-api/api/core/file_manager/stream/${fileId}?token=${token}`;
}

/**
 * 获取文件代理访问URL（用于img src等直接访问）
 * @param fileId 文件ID
 * @param download 是否下载
 */
function getFileProxyUrl(fileId: string, download = false): string {
  const params = download ? '?download=true' : '';
  return `/api/core/file_manager/proxy/${fileId}${params}`;
}

/**
 * 通过API客户端获取文件流（返回blob数据）
 * @param fileId 文件ID
 */
async function getFileStream(fileId: string) {
  return requestClient.get(`/api/core/file_manager/stream/${fileId}`, {
    responseType: 'blob',
  });
}

/**
 * 通过id获取文件信息
 * @param fileId 文件ID
 */
async function getFileInfo(fileId: string) {
  return requestClient.get(`/api/core/file_manager/file_info/${fileId}`);
}

/**
 * 通过多个文件ID批量获取文件信息
 * @param fileIds 文件ID数组
 * @returns 所有文件信息的数组
 */
async function getFilesInfo(fileIds: string[]) {
  if (!fileIds || fileIds.length === 0) {
    return [];
  }

  // 使用Promise.all并行请求所有文件信息
  const promises = fileIds.map((fileId) => getFileInfo(fileId));

  try {
    return await Promise.all(promises);
  } catch (error) {
    console.error('批量获取文件信息失败:', error);
    throw error; // 可以根据需要处理错误，这里选择抛出以便上层处理
  }
}

/**
 * 通过API客户端获取文件代理数据（返回blob数据）
 * @param fileId 文件ID
 * @param download 是否下载
 */
async function getFileProxy(fileId: string, download = false) {
  return requestClient.get(`/api/core/file_manager/proxy/${fileId}`, {
    params: download ? { download: true } : undefined,
    responseType: 'blob',
  });
}

/**
 * 获取公开文件的URL（无需认证）
 * 公开文件可以直接通过URL访问，不需要临时令牌
 * @param fileId 文件ID
 */
function getPublicFileUrl(fileId: string): string {
  return `/basic-api/api/core/file_manager/stream/${fileId}`;
}

/**
 * 设置文件的公开状态
 * @param fileId 文件ID
 * @param isPublic 是否公开
 */
async function setFilePublic(fileId: string, isPublic: boolean): Promise<any> {
  return requestClient.put(`/api/core/file_manager/${fileId}/public`, null, {
    params: { isPublic },
  });
}

// ==================== 签名令牌相关 API ====================

export interface SignatureTokenResponse {
  token: string;
  callback_key: string;
  expired_at: string;
}

export interface SignatureStatusResponse {
  status: 'completed' | 'expired' | 'not_found' | 'pending';
  message: string;
  file_id?: string;
}

/**
 * 创建签名令牌（用于手机扫码签名）
 */
export async function createSignatureToken(
  source: string = 'form',
  expireMinutes: number = 30,
): Promise<SignatureTokenResponse> {
  const formData = new FormData();
  formData.append('source', source);
  formData.append('expire_minutes', String(expireMinutes));
  return requestClient.post('/api/core/file_manager/signature/token', formData);
}

/**
 * 检查签名状态（用于前端轮询）
 */
export async function checkSignatureStatus(
  callbackKey: string,
): Promise<SignatureStatusResponse> {
  return requestClient.get(
    `/api/core/file_manager/signature/status/${callbackKey}`,
  );
}

/**
 * 获取签名令牌信息（移动端使用，无需登录）
 */
export async function getSignatureTokenInfo(token: string): Promise<{
  expired_at: string;
  source: string;
  token: string;
}> {
  return requestClient.get(`/api/core/file_manager/signature/info/${token}`);
}

/**
 * 上传签名图片并完成签名（移动端使用，无需登录）
 */
export async function uploadSignatureImage(
  token: string,
  file: File,
): Promise<{ file_id: string; message: string; success: boolean }> {
  return requestClient.upload(
    `/api/core/file_manager/signature/upload/${token}`,
    { file },
  );
}

/**
 * 完成签名（移动端使用）
 */
export async function completeSignature(
  token: string,
  signatureFileId: string,
): Promise<{ file_id: string; message: string; success: boolean }> {
  const formData = new FormData();
  formData.append('signature_file_id', signatureFileId);
  return requestClient.post(
    `/api/core/file_manager/signature/complete/${token}`,
    formData,
  );
}

export {
  batchDelete,
  createAccessToken,
  createFolder,
  deleteItem,
  getBatchFileUrls,
  getDownloadUrl,
  getFileInfo,
  getFileList,
  getFileProxy,
  getFileProxyUrl,
  getFilesInfo,
  getFileStream,
  getFileStreamUrl,
  getFileStreamUrlWithToken,
  getFileUrlById,
  getFileUrlWithToken,
  getFolderTree,
  getPublicFileUrl,
  getRecentFiles,
  getRecentImages,
  getStorageConfig,
  moveItems,
  renameItem,
  revokeAccessToken,
  setFilePublic,
  updateStorageConfig,
  uploadFile,
};
