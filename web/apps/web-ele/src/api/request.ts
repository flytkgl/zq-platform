/**
 * 该文件可自行根据业务逻辑进行调整
 */
import type { RequestClientOptions } from '@vben/request';

import { useAppConfig } from '@vben/hooks';
import { $t } from '@vben/locales';
import { preferences } from '@vben/preferences';
import {
  authenticateResponseInterceptor,
  defaultResponseInterceptor,
  errorMessageResponseInterceptor,
  RequestClient,
} from '@vben/request';
import { useAccessStore } from '@vben/stores';

import { ElMessage } from 'element-plus';

import { useAuthStore } from '#/store';

import { refreshTokenApi } from './core';

const { apiURL } = useAppConfig(import.meta.env, import.meta.env.PROD);

function createRequestClient(baseURL: string, options?: RequestClientOptions) {
  const client = new RequestClient({
    ...options,
    baseURL,
    paramsSerializer: (params) => {
      const searchParams = new URLSearchParams();
      for (const key in params) {
        const value = params[key];
        if (value === undefined || value === null) {
          continue;
        }
        if (Array.isArray(value)) {
          value.forEach((v) => searchParams.append(key, v));
        } else {
          searchParams.append(key, value);
        }
      }
      return searchParams.toString();
    },
  });

  /**
   * 重新认证逻辑
   */
  async function doReAuthenticate() {
    console.warn(
      '[认证] Access token or refresh token is invalid or expired. ',
    );
    const accessStore = useAccessStore();
    const authStore = useAuthStore();

    // 检查是否有 token，如果没有说明是登录接口返回的 401（账号密码错误）
    // 这种情况不需要显示"登录已失效"的消息，也不需要跳转
    const hasToken = accessStore.accessToken || accessStore.refreshToken;

    accessStore.setAccessToken(null);
    accessStore.setRefreshToken(null);

    // 只有在有 token 的情况下才显示提示消息（说明是 token 失效）
    if (hasToken) {
      ElMessage.warning('登录已失效，请重新登录');

      if (
        preferences.app.loginExpiredMode === 'modal' &&
        accessStore.isAccessChecked
      ) {
        accessStore.setLoginExpired(true);
      } else {
        // 被强制登出时，不需要再调用后端 logout 接口（会 401）
        await authStore.logout(true, false);
      }
    }
  }

  /**
   * 刷新token逻辑
   */
  // 刷新Token的Promise缓存，用于请求去重
  let refreshPromise: null | Promise<string> = null;

  async function doRefreshToken() {
    // 如果已经有正在进行的刷新请求，直接返回该Promise
    // 这样多个并发请求会共享同一个刷新操作，避免重复刷新
    if (refreshPromise) {
      console.log('[Token刷新] 已有刷新请求进行中，等待...');
      return refreshPromise;
    }

    console.log('[Token刷新] 开始刷新token...');

    // 创建新的刷新Promise
    refreshPromise = (async () => {
      try {
        const accessStore = useAccessStore();

        console.log(
          '[Token刷新] 当前refreshToken:',
          accessStore.refreshToken ? '存在' : '不存在',
        );

        // 检查 refreshToken 是否存在
        if (!accessStore.refreshToken) {
          console.error('[Token刷新] Refresh token is missing');
          await doReAuthenticate();
          throw new Error($t('ui.fallback.http.unauthorized'));
        }

        // 传递 refreshToken 给 API
        const resp = await refreshTokenApi(accessStore.refreshToken);

        // 处理响应中的新 token
        // 后端支持两种格式：直接返回 token 字符串 或 { token, accessToken } 对象
        const newToken = resp.data?.accessToken || '';

        // 更新 access token
        accessStore.setAccessToken(newToken);

        // 如果响应中有新的 refresh token，也保存
        if (typeof resp.data === 'object' && resp.data?.refreshToken) {
          accessStore.setRefreshToken(resp.data.refreshToken);
        }

        return newToken;
      } finally {
        // 无论成功或失败，都清空Promise缓存，允许下次刷新
        refreshPromise = null;
      }
    })();

    return refreshPromise;
  }

  function formatToken(token: null | string) {
    return token ? `Bearer ${token}` : null;
  }

  // 请求头处理
  client.addRequestInterceptor({
    fulfilled: async (config) => {
      const accessStore = useAccessStore();

      config.headers.Authorization = formatToken(accessStore.accessToken);
      config.headers['Accept-Language'] = preferences.app.locale;
      return config;
    },
  });

  // 处理返回的响应数据格式
  client.addResponseInterceptor(
    defaultResponseInterceptor({
      codeField: 'code',
      dataField: 'data',
      successCode: 0,
    }),
  );

  // SSE 模块 401 时的 token 刷新
  client.refreshToken = async () => {
    try {
      return await doRefreshToken();
    } catch {
      await doReAuthenticate();
      throw new Error('Token refresh failed');
    }
  };

  // token过期的处理
  // 注意：enableRefreshToken 需要动态获取，因为 preferences 可能在运行时更新
  client.addResponseInterceptor(
    authenticateResponseInterceptor({
      client,
      doReAuthenticate,
      doRefreshToken,
      enableRefreshToken: true, // 始终启用 token 刷新
      formatToken,
    }),
  );

  // 通用的错误处理,如果没有进入上面的错误处理逻辑，就会进入这里
  client.addResponseInterceptor(
    errorMessageResponseInterceptor((msg: string, error) => {
      // 这里可以根据业务进行定制,你可以拿到 error 内的信息进行定制化处理，根据不同的 code 做不同的提示，而不是直接使用 message.error 提示 msg
      const responseData = error?.response?.data ?? {};
      const status = error?.response?.status;

      // 401 错误由 authenticateResponseInterceptor 处理，这里跳过
      // 避免在 token 刷新过程中显示错误消息
      if (status === 401) {
        return;
      }

      // 优先级顺序：后端自定义消息 > 传入的消息 > 状态码默认消息
      let errorMessage =
        responseData?.message ||
        responseData?.error ||
        responseData?.detail ||
        responseData?.msg ||
        msg;

      // 特殊处理429限流
      if (status === 429) {
        errorMessage =
          errorMessage || '请求过于频繁，请稍后再试（5分钟内不能重试）';
      }

      // 特殊处理403禁止访问
      if (status === 403) {
        errorMessage = errorMessage || '您没有权限访问此资源';
      }

      // 打印完整错误信息便于调试
      console.error('[API Error]', {
        status,
        message: errorMessage,
        data: responseData,
      });
      // 显示错误消息
      if (errorMessage) {
        ElMessage.error(errorMessage || msg);
      }
    }),
  );

  return client;
}

export const requestClient = createRequestClient(apiURL, {
  responseReturn: 'body',
});

export const baseRequestClient = new RequestClient({ baseURL: apiURL });
