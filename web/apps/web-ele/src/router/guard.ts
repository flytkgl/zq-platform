import type { Router } from 'vue-router';

import { LOGIN_PATH } from '@vben/constants';
import { preferences } from '@vben/preferences';
import { useAccessStore, useTabbarStore, useUserStore } from '@vben/stores';
import { startProgress, stopProgress } from '@vben/utils';

import { accessRoutes, coreRouteNames } from '#/router/routes';
import { useAuthStore } from '#/store';
import { useAppContextStore } from '#/store/app-context';

import { generateAccess } from './access';

/**
 * 通用守卫配置
 * @param router
 */
function setupCommonGuard(router: Router) {
  // 记录已经加载的页面
  const loadedPaths = new Set<string>();

  // 记录当前应用编码，用于检测应用切换
  let currentAppCode: null | string = null;

  // 为每个应用存储 tab 历史
  const tabHistoryByApp = new Map<string, any>();

  router.beforeEach((to) => {
    // 检测应用切换（支持 /app/ 和 /app-dev/ 两种模式）
    const devMatch = to.path.match(/^\/app-dev\/([^/]+)/);
    const appMatch = to.path.match(/^\/app\/([^/]+)/);
    const newAppCode =
      (devMatch && devMatch[1]) || (appMatch && appMatch[1]) || null;
    const isDevMode = !!(devMatch && devMatch[1]);
    const appKey = newAppCode
      ? (isDevMode
        ? `${newAppCode}-dev`
        : newAppCode)
      : 'main';

    // 如果应用切换了，保存当前应用的 tab 历史，加载新应用的 tab 历史
    if (newAppCode !== currentAppCode) {
      const tabbarStore = useTabbarStore();

      // 保存当前应用的 tab 历史到内存
      const currentAppKey = currentAppCode || 'main';
      tabHistoryByApp.set(currentAppKey, {
        tabs: [...tabbarStore.tabs],
        cachedTabs: new Set(tabbarStore.cachedTabs),
      });

      // 从 sessionStorage 加载新应用的 tab 历史
      const storageKey = `vben-admin-tabs-${appKey}`;
      const savedHistory = sessionStorage.getItem(storageKey);

      if (savedHistory) {
        try {
          const parsed = JSON.parse(savedHistory);
          tabbarStore.tabs = parsed.tabs || [];
          tabbarStore.cachedTabs = new Set(parsed.cachedTabs || []);
        } catch (error) {
          console.error('Failed to parse tab history:', error);
          tabbarStore.tabs = [];
          tabbarStore.cachedTabs = new Set();
        }
      } else {
        // 如果没有保存的历史，清空
        tabbarStore.tabs = [];
        tabbarStore.cachedTabs = new Set();
      }

      currentAppCode = newAppCode;
    }

    to.meta.loaded = loadedPaths.has(to.path);

    // 页面加载进度条
    if (!to.meta.loaded && preferences.transition.progress) {
      startProgress();
    }
    return true;
  });

  router.afterEach((to) => {
    // 记录页面是否加载,如果已经加载，后续的页面切换动画等效果不在重复执行
    loadedPaths.add(to.path);

    // 保存当前应用的 tab 历史到 sessionStorage（支持 /app/ 和 /app-dev/ 两种模式）
    const devMatch = to.path.match(/^\/app-dev\/([^/]+)/);
    const appMatch = to.path.match(/^\/app\/([^/]+)/);
    const appCode =
      (devMatch && devMatch[1]) || (appMatch && appMatch[1]) || null;
    const isDevMode = !!(devMatch && devMatch[1]);
    const appKey = appCode ? (isDevMode ? `${appCode}-dev` : appCode) : 'main';
    const storageKey = `vben-admin-tabs-${appKey}`;

    const tabbarStore = useTabbarStore();
    const tabHistory = {
      tabs: tabbarStore.tabs,
      cachedTabs: [...tabbarStore.cachedTabs],
    };
    sessionStorage.setItem(storageKey, JSON.stringify(tabHistory));

    // 关闭页面加载进度条
    if (preferences.transition.progress) {
      stopProgress();
    }
  });
}

/**
 * 权限访问守卫配置
 * @param router
 */
function setupAccessGuard(router: Router) {
  router.beforeEach(async (to, from) => {
    const accessStore = useAccessStore();
    const userStore = useUserStore();
    const authStore = useAuthStore();

    // 基本路由，这些路由不需要进入权限拦截
    if (coreRouteNames.includes(to.name as string)) {
      if (to.path === LOGIN_PATH && accessStore.accessToken) {
        return decodeURIComponent(
          (to.query?.redirect as string) ||
            userStore.userInfo?.homePath ||
            preferences.app.defaultHomePath,
        );
      }
      return true;
    }

    // accessToken 检查
    if (!accessStore.accessToken) {
      // 明确声明忽略权限访问权限，则可以访问
      if (to.meta.ignoreAccess) {
        return true;
      }

      // 没有访问权限，跳转登录页面
      if (to.fullPath !== LOGIN_PATH) {
        return {
          path: LOGIN_PATH,
          // 如不需要，直接删除 query
          query:
            to.fullPath === preferences.app.defaultHomePath
              ? {}
              : { redirect: encodeURIComponent(to.fullPath) },
          // 携带当前跳转的页面，登录后重新跳转该页面
          replace: true,
        };
      }
      return to;
    }

    // 是否已经生成过动态路由
    if (accessStore.isAccessChecked) {
      return true;
    }

    // 检查重定向路径或目标路径是否为子应用路径
    // 这是为了处理从子应用退出登录后再登录的情况
    const appContextStore = useAppContextStore();
    const redirectParam = from.query.redirect as string | undefined;
    const targetPath = redirectParam
      ? decodeURIComponent(redirectParam)
      : to.path;

    // 支持 /app-dev/ 和 /app/ 两种模式
    const devMatch = targetPath.match(/^\/app-dev\/([^/]+)/);
    const appMatch = targetPath.match(/^\/app\/([^/]+)/);
    const detectedAppCode =
      (devMatch && devMatch[1]) || (appMatch && appMatch[1]) || null;
    const detectedDevMode = !!(devMatch && devMatch[1]);

    if (detectedAppCode && !appContextStore.appCode) {
      // 从重定向路径中检测到子应用，初始化 appContextStore
      await appContextStore.setAppCode(detectedAppCode, detectedDevMode);
    }

    // 生成路由表
    // 当前登录用户拥有的角色标识列表
    const userInfo = userStore.userInfo || (await authStore.fetchUserInfo());
    const userRoles = userInfo.roles ?? [];

    // 生成菜单和路由
    const { accessibleMenus, accessibleRoutes } = await generateAccess({
      roles: userRoles,
      router,
      // 则会在菜单中显示，但是访问会被重定向到403
      routes: accessRoutes,
    });

    // 保存菜单信息和路由信息
    accessStore.setAccessMenus(accessibleMenus);
    accessStore.setAccessRoutes(accessibleRoutes);
    accessStore.setIsAccessChecked(true);

    // 子应用根路径重定向（/app/hr -> /app/hr/xxx 或 /app-dev/hr -> /app-dev/hr/xxx）
    if (appContextStore.isSubApp) {
      const pathPrefix = appContextStore.isDevMode ? '/app-dev' : '/app';
      const subAppRootPath = `${pathPrefix}/${appContextStore.appCode}`;

      if (to.path === subAppRootPath) {
        const defaultHome =
          preferences.app.defaultHomePath || '/page-render/main_home';
        // 确保路径包含子应用前缀
        const subAppTargetPath = defaultHome.startsWith(subAppRootPath)
          ? defaultHome
          : `${subAppRootPath}${defaultHome}`;
        return {
          path: subAppTargetPath,
          replace: true,
        };
      }
    }

    // 重定向逻辑
    const redirectPath = (from.query.redirect ??
      (to.path === preferences.app.defaultHomePath
        ? userInfo.homePath || preferences.app.defaultHomePath
        : to.fullPath)) as string;

    return {
      ...router.resolve(decodeURIComponent(redirectPath)),
      replace: true,
    };
  });
}

/**
 * 项目守卫配置
 * @param router
 */
function createRouterGuard(router: Router) {
  /** 通用 */
  setupCommonGuard(router);
  /** 权限访问 */
  setupAccessGuard(router);
}

export { createRouterGuard };
