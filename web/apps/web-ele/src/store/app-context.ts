import type { Application } from '#/api/core/application';

import { computed, ref } from 'vue';

import { defineStore } from 'pinia';

import { getApplicationByCodeApi } from '#/api/core/application';

/**
 * 应用上下文 Store
 * 用于管理当前应用的状态，支持多应用架构
 */
export const useAppContextStore = defineStore('app-context', () => {
  // 当前应用编码（从 URL 参数中获取）
  const appCode = ref<null | string>(null);

  // 当前应用详情
  const currentApp = ref<Application | null>(null);

  // 是否为开发模式（/app-dev/{code}/）
  const isDevMode = ref<boolean>(false);

  // 是否为子应用模式
  const isSubApp = computed(() => !!appCode.value);

  // 是否为主应用模式
  const isMainApp = computed(() => !appCode.value);

  /**
   * 从 URL 路径中初始化应用上下文
   * URL 格式：
   * - /app/:appCode/... （正常模式）
   * - /app-dev/:appCode/... （开发模式）
   */
  async function initFromUrl() {
    const path = window.location.pathname;

    // 先尝试匹配开发模式 /app-dev/{code}/
    const devMatch = path.match(/^\/app-dev\/([^/]+)/);
    if (devMatch && devMatch[1]) {
      appCode.value = devMatch[1];
      isDevMode.value = true;
      await loadCurrentApp();
      return;
    }

    // 再尝试匹配正常模式 /app/{code}/
    const appMatch = path.match(/^\/app\/([^/]+)/);
    if (appMatch && appMatch[1]) {
      appCode.value = appMatch[1];
      isDevMode.value = false;
      await loadCurrentApp();
      return;
    }

    // 主应用模式
    appCode.value = null;
    isDevMode.value = false;
    currentApp.value = null;
  }

  /**
   * 加载当前应用详情
   */
  async function loadCurrentApp() {
    if (!appCode.value) {
      currentApp.value = null;
      return;
    }

    try {
      const app = await getApplicationByCodeApi(appCode.value);
      currentApp.value = app;
    } catch (error) {
      console.error('Failed to load application:', error);
      currentApp.value = null;
    }
  }

  /**
   * 设置当前应用
   * @param code 应用编码
   * @param devMode 是否为开发模式
   */
  async function setAppCode(code: null | string, devMode: boolean = false) {
    appCode.value = code;
    isDevMode.value = devMode;
    if (code) {
      await loadCurrentApp();
    } else {
      currentApp.value = null;
    }
  }

  /**
   * 清除应用上下文
   */
  function clear() {
    appCode.value = null;
    isDevMode.value = false;
    currentApp.value = null;
  }

  /**
   * 获取子应用 URL
   * @param code 应用编码
   * @param devMode 是否为开发模式
   */
  function getSubAppUrl(code: string, devMode: boolean = false): string {
    const baseUrl = window.location.origin;
    const prefix = devMode ? 'app-dev' : 'app';
    return `${baseUrl}/${prefix}/${code}`;
  }

  /**
   * 获取当前上下文的路由路径
   * 在子应用模式下会自动添加 /app/{code} 或 /app-dev/{code} 前缀
   * @param path 原始路由路径（如 /ai-platform/workflow/editor/123）
   */
  function getContextPath(path: string): string {
    if (!appCode.value) {
      return path;
    }
    const prefix = isDevMode.value ? 'app-dev' : 'app';
    return `/${prefix}/${appCode.value}${path}`;
  }

  /**
   * 重置 store 状态
   */
  function $reset() {
    appCode.value = null;
    isDevMode.value = false;
    currentApp.value = null;
  }

  return {
    appCode,
    currentApp,
    isDevMode,
    isSubApp,
    isMainApp,
    initFromUrl,
    loadCurrentApp,
    setAppCode,
    clear,
    getSubAppUrl,
    getContextPath,
    $reset,
  };
});
