import { preferences } from '@vben/preferences';
import { useAccessStore } from '@vben/stores';

import { ElMessage } from 'element-plus';

import { useAuthStore } from '#/store';

import { refreshTokenApi } from './core';

/**
 * 流式请求配置
 */
interface StreamRequestOptions {
  /** 请求方法 */
  method?: 'DELETE' | 'GET' | 'PATCH' | 'POST' | 'PUT';
  /** 请求头 */
  headers?: Record<string, string>;
  /** 请求体 */
  body?: any;
  /** 超时时间（毫秒） */
  timeout?: number;
  /** 是否自动处理JSON */
  json?: boolean;
}

/**
 * 流式请求事件处理器
 */
export interface StreamEventHandler<T> {
  /** 处理数据事件 */
  onData?: (data: T) => void;
  /** 处理错误事件 */
  onError?: (error: Error) => void;
  /** 处理完成事件 */
  onComplete?: () => void;
}

// 是否正在刷新 token
let isRefreshing = false;
// 等待刷新 token 的请求队列
let refreshSubscribers: Array<(token: string) => void> = [];

/**
 * 添加到刷新队列
 */
function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

/**
 * 通知所有等待的请求
 */
function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
}

/**
 * 重新认证逻辑
 */
async function doReAuthenticate() {
  console.warn('Access token or refresh token is invalid or expired.');
  const accessStore = useAccessStore();
  const authStore = useAuthStore();
  accessStore.setAccessToken(null);
  if (
    preferences.app.loginExpiredMode === 'modal' &&
    accessStore.isAccessChecked
  ) {
    accessStore.setLoginExpired(true);
  } else {
    await authStore.logout();
  }
}

/**
 * 刷新 token 逻辑
 */
async function doRefreshToken(): Promise<string> {
  const accessStore = useAccessStore();

  // 检查 refreshToken 是否存在
  if (!accessStore.refreshToken) {
    console.error('Refresh token is missing');
    await doReAuthenticate();
    throw new Error('Refresh token is missing');
  }

  // 传递 refreshToken 给 API
  const resp = await refreshTokenApi(accessStore.refreshToken);

  // 处理响应中的新 token
  const newToken = resp.data?.accessToken || '';

  // 更新 access token
  accessStore.setAccessToken(newToken);

  // 如果响应中有新的 refresh token，也保存
  if (typeof resp.data === 'object' && resp.data?.refreshToken) {
    accessStore.setRefreshToken(resp.data.refreshToken);
  }

  return newToken;
}

/**
 * 执行流式请求（内部实现）
 */
function doStreamRequest<T = any>(
  url: string,
  options: StreamRequestOptions = {},
  eventHandler: StreamEventHandler<T> = {},
  token?: string,
): () => void {
  const {
    method = 'GET',
    headers = {},
    body,
    timeout = 30_000,
    json = true,
  } = options;

  const controller = new AbortController();
  const signal = controller.signal;
  let isAborted = false;

  // 设置请求头
  const requestHeaders = new Headers({
    'Content-Type': 'application/json',
    ...headers,
  });

  // 添加认证头
  const accessStore = useAccessStore();
  const accessToken = token || accessStore.accessToken;
  if (accessToken) {
    requestHeaders.set('Authorization', `Bearer ${accessToken}`);
  }

  // 添加语言头
  requestHeaders.set('Accept-Language', preferences.app.locale);

  // 准备请求体
  let requestBody: BodyInit | null = null;
  if (body) {
    requestBody = json ? JSON.stringify(body) : body;
  }

  // 发起请求
  const requestPromise = fetch(url, {
    method,
    headers: requestHeaders,
    body: requestBody,
    signal,
  });

  // 设置超时
  const timeoutId = setTimeout(() => {
    if (!isAborted) {
      controller.abort();
      const error = new Error('请求超时');
      eventHandler.onError?.(error);
    }
  }, timeout);

  // 处理响应
  requestPromise
    .then(async (response) => {
      clearTimeout(timeoutId);

      // 处理 401 错误 - 尝试刷新 token
      if (response.status === 401 && preferences.app.enableRefreshToken) {
        // 如果正在刷新 token，等待刷新完成后重试
        if (isRefreshing) {
          return new Promise<void>((resolve) => {
            subscribeTokenRefresh((newToken) => {
              // 使用新 token 重试请求
              const cancel = doStreamRequest(
                url,
                options,
                eventHandler,
                newToken,
              );
              // 如果原请求被取消，也取消重试的请求
              if (isAborted) {
                cancel();
              }
              resolve();
            });
          });
        }

        // 开始刷新 token
        isRefreshing = true;
        try {
          const newToken = await doRefreshToken();
          isRefreshing = false;
          onTokenRefreshed(newToken);

          // 使用新 token 重试请求
          const cancel = doStreamRequest(url, options, eventHandler, newToken);
          // 如果原请求被取消，也取消重试的请求
          if (isAborted) {
            cancel();
          }
          return;
        } catch {
          isRefreshing = false;
          refreshSubscribers = [];
          await doReAuthenticate();
          const error = new Error('认证失败，请重新登录');
          (error as any).status = 401;
          eventHandler.onError?.(error);
          return;
        }
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(
          errorData.message ||
            errorData.detail ||
            `请求失败: ${response.statusText}`,
        );
        (error as any).status = response.status;
        (error as any).data = errorData;
        throw error;
      }

      if (!response.body) {
        throw new Error('响应体为空');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const processStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              eventHandler.onComplete?.();
              return;
            }

            buffer += decoder.decode(value, { stream: true });

            // 处理可能的多条消息
            let newlineIndex;
            while ((newlineIndex = buffer.indexOf('\n')) >= 0) {
              const line = buffer.slice(0, newlineIndex).trim();
              buffer = buffer.slice(newlineIndex + 1);

              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                  eventHandler.onComplete?.();
                  return;
                }

                try {
                  const parsed = JSON.parse(data);
                  eventHandler.onData?.(parsed);
                } catch (error) {
                  console.error('解析流数据失败:', error, '原始数据:', data);
                }
              }
            }
          }
        } catch (error) {
          if (!isAborted) {
            console.error('处理流数据时出错:', error);
            eventHandler.onError?.(error as Error);
          }
        }
      };

      await processStream();
    })
    .catch((error) => {
      clearTimeout(timeoutId);
      if (!isAborted) {
        console.error('请求失败:', error);

        // 处理取消的请求
        if (error.name === 'AbortError') {
          return;
        }

        // 处理HTTP错误
        if (error.status) {
          let errorMessage = error.message;

          // 根据状态码显示更友好的错误信息
          switch (error.status) {
            case 401: {
              errorMessage = '认证失败，请重新登录';
              break;
            }
            case 403: {
              errorMessage = '没有权限访问此资源';
              break;
            }
            case 429: {
              errorMessage = '请求过于频繁，请稍后再试';
              break;
            }
            default: {
              if (error.status >= 500) {
                errorMessage = '服务器内部错误，请稍后再试';
              }
            }
          }

          ElMessage.error(errorMessage);
        }

        eventHandler.onError?.(error);
      }
    });

  // 返回取消函数
  return () => {
    isAborted = true;
    controller.abort();
    clearTimeout(timeoutId);
  };
}

/**
 * 执行流式请求
 * @param url 请求URL
 * @param options 请求选项
 * @param eventHandler 事件处理器
 * @returns 取消函数
 */
export function streamRequest<T = any>(
  url: string,
  options: StreamRequestOptions = {},
  eventHandler: StreamEventHandler<T> = {},
): () => void {
  return doStreamRequest(url, options, eventHandler);
}

/**
 * 创建流式请求的取消令牌
 */
export class StreamRequestToken {
  /**
   * 检查是否已取消
   */
  get isCancelled() {
    return this.controller?.signal.aborted ?? false;
  }

  private controller: AbortController | null = null;

  /**
   * 取消请求
   */
  cancel() {
    if (this.controller) {
      this.controller.abort();
      this.controller = null;
    }
  }

  /**
   * 创建一个新的取消令牌
   */
  create() {
    this.controller = new AbortController();
    return this.controller.signal;
  }
}

/**
 * 使用流式请求配置创建请求函数
 */
export function createStreamRequest(
  baseURL: string = '',
  options: StreamRequestOptions = {},
) {
  return <T>(url: string, data?: any, eventHandler?: StreamEventHandler<T>) => {
    const fullUrl = `${baseURL}${url}`;

    return streamRequest<T>(
      fullUrl,
      {
        ...options,
        method: data ? 'POST' : 'GET',
        body: data,
      },
      eventHandler,
    );
  };
}

// 创建默认的流式请求客户端
export const streamRequestClient = createStreamRequest(
  import.meta.env.VITE_GLOB_API_URL,
);
