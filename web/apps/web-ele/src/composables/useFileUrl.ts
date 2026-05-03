/**
 * 文件URL管理 Composable
 * 用于管理文件的临时访问URL，支持缓存和自动刷新
 *
 * 支持两种访问模式：
 * - 私有文件：需要临时访问令牌，URL会自动缓存和刷新
 * - 公开文件：直接返回URL，无需认证
 */
import { ref, watch } from 'vue';

import { getFileUrlWithToken, getPublicFileUrl } from '#/api/core/file';

// 全局URL缓存（临时令牌URL）
const urlCache = new Map<string, { expiresAt: number; url: string }>();

// 全局 Blob ObjectURL 缓存（图片等二进制内容，长期有效）
const blobCache = new Map<string, string>();

// 正在进行的请求去重（避免同一 fileId 并发重复请求）
const pendingRequests = new Map<string, Promise<string>>();

// Blob 缓存最大条目数，防止内存无限增长
const BLOB_CACHE_MAX_SIZE = 500;

// 默认过期时间（秒）
const DEFAULT_EXPIRES_IN = 3600;

// 提前刷新时间（秒）- 在过期前5分钟刷新
const REFRESH_BEFORE = 300;

/**
 * 清理过期的缓存
 */
function cleanupExpiredCache() {
  const now = Date.now();
  for (const [key, value] of urlCache.entries()) {
    if (value.expiresAt < now) {
      urlCache.delete(key);
    }
  }
}

/**
 * 获取公开文件的URL（无需认证，同步返回）
 * @param fileId 文件ID
 * @returns string 文件访问URL
 */
export function getFileUrlPublic(fileId: string): string {
  if (!fileId) return '';
  return getPublicFileUrl(fileId);
}

/**
 * 获取临时令牌URL（内部方法，不含 Blob 缓存）
 */
async function getTokenUrl(
  fileId: string,
  expiresIn: number = DEFAULT_EXPIRES_IN,
): Promise<string> {
  const now = Date.now();
  const cached = urlCache.get(fileId);

  if (cached && cached.expiresAt - REFRESH_BEFORE * 1000 > now) {
    return cached.url;
  }

  const result = await getFileUrlWithToken(fileId, expiresIn);
  const expiresAt = new Date(result.expiresAt).getTime();
  const url = `/basic-api${result.url}`;
  urlCache.set(fileId, { url, expiresAt });
  return url;
}

/**
 * 获取文件的访问URL（带 Blob 缓存 + 令牌URL缓存）
 *
 * 缓存策略：
 * 1. 如果 Blob 缓存命中（ObjectURL），直接返回，零网络请求
 * 2. 否则获取临时令牌URL，fetch 下载为 Blob，生成 ObjectURL 缓存
 * 3. 如果 fetch 失败，降级返回临时令牌URL
 * 4. 并发请求同一 fileId 会自动去重
 *
 * @param fileId 文件ID
 * @param expiresIn 过期时间（秒）
 * @returns Promise<string> 文件访问URL
 */
export async function getFileUrl(
  fileId: string,
  expiresIn: number = DEFAULT_EXPIRES_IN,
): Promise<string> {
  if (!fileId) return '';

  // 1. Blob 缓存命中，直接返回
  const blobUrl = blobCache.get(fileId);
  if (blobUrl) {
    return blobUrl;
  }

  // 2. 去重：如果已有相同 fileId 的请求在进行中，等待它完成
  const pending = pendingRequests.get(fileId);
  if (pending) {
    return pending;
  }

  // 3. 发起新请求
  const request = (async () => {
    try {
      const tokenUrl = await getTokenUrl(fileId, expiresIn);

      // 尝试 fetch 并缓存为 Blob ObjectURL
      try {
        const response = await fetch(tokenUrl);
        if (response.ok) {
          const blob = await response.blob();
          // 限制缓存大小：超出时清理最早的条目
          if (blobCache.size >= BLOB_CACHE_MAX_SIZE) {
            const firstKey = blobCache.keys().next().value;
            if (firstKey) {
              const oldUrl = blobCache.get(firstKey);
              if (oldUrl) URL.revokeObjectURL(oldUrl);
              blobCache.delete(firstKey);
            }
          }
          const objectUrl = URL.createObjectURL(blob);
          blobCache.set(fileId, objectUrl);
          return objectUrl;
        }
      } catch {
        // fetch 失败，降级返回令牌URL
      }

      return tokenUrl;
    } catch (error) {
      console.error('获取文件URL失败:', error);
      const cached = urlCache.get(fileId);
      if (cached) return cached.url;
      return '';
    } finally {
      pendingRequests.delete(fileId);
    }
  })();

  pendingRequests.set(fileId, request);
  return request;
}

/**
 * 批量获取文件URL
 * @param fileIds 文件ID数组
 * @param expiresIn 过期时间（秒）
 * @returns Promise<Map<string, string>> 文件ID到URL的映射
 */
export async function getFileUrls(
  fileIds: string[],
  expiresIn: number = DEFAULT_EXPIRES_IN,
): Promise<Map<string, string>> {
  const result = new Map<string, string>();
  const promises = fileIds.map(async (fileId) => {
    const url = await getFileUrl(fileId, expiresIn);
    result.set(fileId, url);
  });

  await Promise.all(promises);
  return result;
}

/**
 * 清除文件URL缓存
 * @param fileId 可选，指定文件ID；不传则清除所有缓存
 */
export function clearFileUrlCache(fileId?: string) {
  if (fileId) {
    urlCache.delete(fileId);
    const blobUrl = blobCache.get(fileId);
    if (blobUrl) {
      URL.revokeObjectURL(blobUrl);
      blobCache.delete(fileId);
    }
  } else {
    urlCache.clear();
    for (const url of blobCache.values()) {
      URL.revokeObjectURL(url);
    }
    blobCache.clear();
  }
}

/**
 * useFileUrl Composable
 * 用于在组件中响应式地获取文件URL
 *
 * @example
 * ```vue
 * <script setup>
 * const { url, loading, refresh } = useFileUrl(fileId);
 * </script>
 * <template>
 *   <img v-if="!loading" :src="url" />
 * </template>
 * ```
 */
export function useFileUrl(
  fileId: (() => string | undefined) | string | undefined,
  options: {
    expiresIn?: number;
    immediate?: boolean;
  } = {},
) {
  const { expiresIn = DEFAULT_EXPIRES_IN, immediate = true } = options;

  const url = ref('');
  const loading = ref(false);
  const error = ref<Error | null>(null);

  const getFileIdValue = () => {
    if (typeof fileId === 'function') {
      return fileId();
    }
    return fileId;
  };

  async function refresh() {
    const id = getFileIdValue();
    if (!id) {
      url.value = '';
      return;
    }

    loading.value = true;
    error.value = null;

    try {
      // 清除缓存以强制刷新
      clearFileUrlCache(id);
      url.value = await getFileUrl(id, expiresIn);
    } catch (error_) {
      error.value = error_ as Error;
      console.error('获取文件URL失败:', error_);
    } finally {
      loading.value = false;
    }
  }

  async function load() {
    const id = getFileIdValue();
    if (!id) {
      url.value = '';
      return;
    }

    loading.value = true;
    error.value = null;

    try {
      url.value = await getFileUrl(id, expiresIn);
    } catch (error_) {
      error.value = error_ as Error;
      console.error('获取文件URL失败:', error_);
    } finally {
      loading.value = false;
    }
  }

  // 监听fileId变化
  if (typeof fileId === 'function') {
    watch(fileId, (newId) => {
      if (newId) {
        load();
      } else {
        url.value = '';
      }
    });
  }

  // 立即加载
  if (immediate) {
    load();
  }

  return {
    url,
    loading,
    error,
    refresh,
    load,
  };
}

/**
 * useFileUrls Composable
 * 用于批量获取多个文件的URL
 */
export function useFileUrls(
  fileIds: (() => string[]) | string[],
  options: {
    expiresIn?: number;
    immediate?: boolean;
  } = {},
) {
  const { expiresIn = DEFAULT_EXPIRES_IN, immediate = true } = options;

  const urls = ref<Map<string, string>>(new Map());
  const loading = ref(false);
  const error = ref<Error | null>(null);

  const getFileIdsValue = () => {
    if (typeof fileIds === 'function') {
      return fileIds();
    }
    return fileIds;
  };

  async function load() {
    const ids = getFileIdsValue();
    if (!ids || ids.length === 0) {
      urls.value = new Map();
      return;
    }

    loading.value = true;
    error.value = null;

    try {
      urls.value = await getFileUrls(ids, expiresIn);
    } catch (error_) {
      error.value = error_ as Error;
      console.error('批量获取文件URL失败:', error_);
    } finally {
      loading.value = false;
    }
  }

  async function refresh() {
    const ids = getFileIdsValue();
    ids.forEach((id) => clearFileUrlCache(id));
    await load();
  }

  // 监听fileIds变化
  if (typeof fileIds === 'function') {
    watch(fileIds, () => {
      load();
    });
  }

  // 立即加载
  if (immediate) {
    load();
  }

  /**
   * 获取单个文件的URL
   */
  function getUrl(fileId: string): string {
    return urls.value.get(fileId) || '';
  }

  return {
    urls,
    loading,
    error,
    refresh,
    load,
    getUrl,
  };
}

// 定期清理过期缓存（每5分钟）
setInterval(cleanupExpiredCache, 5 * 60 * 1000);

export default useFileUrl;
