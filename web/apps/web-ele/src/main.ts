import { initPreferences } from '@vben/preferences';
import { merge, unmountGlobalLoading } from '@vben/utils';

import { overridesPreferences } from './preferences';

/**
 * 从 URL 路径中解析 appCode 和模式
 * URL 格式：
 * - /app/:appCode/... （正常模式）
 * - /app-dev/:appCode/... （开发模式）
 */
function getAppInfoFromUrl(): { appCode: null | string; isDevMode: boolean } {
  const path = window.location.pathname;

  // 先尝试匹配开发模式 /app-dev/{code}/
  const devMatch = path.match(/^\/app-dev\/([^/]+)/);
  if (devMatch?.[1]) {
    return { appCode: devMatch[1], isDevMode: true };
  }

  // 再尝试匹配正常模式 /app/{code}/
  const appMatch = path.match(/^\/app\/([^/]+)/);
  if (appMatch?.[1]) {
    return { appCode: appMatch[1], isDevMode: false };
  }

  return { appCode: null, isDevMode: false };
}

/**
 * 根据 appCode 获取应用详情
 */
async function getApplicationByCode(
  appCode: string,
): Promise<null | { id: string }> {
  try {
    const apiURL = import.meta.env.VITE_GLOB_API_URL || '';
    const response = await fetch(
      `${apiURL}/api/core/applications/code/${appCode}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      },
    );

    if (response.ok) {
      const result = await response.json();
      // 后端直接返回应用数据，不包装 code/data
      if (result && result.id) {
        return result;
      }
    }
  } catch (error) {
    console.warn('[应用加载] 获取应用详情失败', error);
  }
  return null;
}

/**
 * 从后端加载UI配置
 * 如果加载失败则返回空对象，使用前端默认配置
 * @param applicationId 应用ID，不传则获取主应用配置
 */
async function loadBackendPreferences(
  applicationId?: string,
): Promise<Record<string, any>> {
  try {
    const apiURL = import.meta.env.VITE_GLOB_API_URL || '';
    const url = applicationId
      ? `${apiURL}/api/core/ui_config/preferences?applicationId=${applicationId}`
      : `${apiURL}/api/core/ui_config/preferences`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      const result = await response.json();
      // 后端直接返回配置数据，不包装 code/data
      if (result && typeof result === 'object') {
        console.log(
          '[配置加载] 成功从后端加载UI配置',
          applicationId ? `(应用: ${applicationId})` : '(主应用)',
        );
        return result;
      }
    }
  } catch (error) {
    console.warn('[配置加载] 后端UI配置加载失败，使用前端默认配置', error);
  }
  return {};
}

/**
 * 应用初始化完成之后再进行页面加载渲染
 */
async function initApplication() {
  // name用于指定项目唯一标识
  // 用于区分不同项目的偏好设置以及存储数据的key前缀以及其他一些需要隔离的数据
  const env = import.meta.env.PROD ? 'prod' : 'dev';
  const appVersion = import.meta.env.VITE_APP_VERSION;
  const baseNamespace = `${import.meta.env.VITE_APP_NAMESPACE}-${appVersion}-${env}`;

  // 1. 检查是否为子应用模式，获取 appCode 和 applicationId
  const { appCode, isDevMode } = getAppInfoFromUrl();
  let applicationId: string | undefined;

  if (appCode) {
    const appInfo = await getApplicationByCode(appCode);
    applicationId = appInfo?.id;
    const modeLabel = isDevMode ? '开发模式' : '正常模式';
    console.log(`[应用初始化] 子应用${modeLabel}`, {
      appCode,
      applicationId,
      isDevMode,
    });
  } else {
    console.log('[应用初始化] 主应用模式');
  }

  // 2. 根据应用模式生成不同的 namespace，确保主应用和子应用的 localStorage 隔离
  // 主应用: vben-admin-1.0.0-dev
  // 子应用正常模式: vben-admin-1.0.0-dev-crm
  // 子应用开发模式: vben-admin-1.0.0-dev-crm-dev
  let namespace = baseNamespace;
  if (appCode) {
    namespace = isDevMode
      ? `${baseNamespace}-${appCode}-dev`
      : `${baseNamespace}-${appCode}`;
  }

  // 3. 从后端加载UI配置（传递 applicationId 获取对应应用的配置）
  const backendPreferences = await loadBackendPreferences(applicationId);
  console.log('[配置加载] 后端配置:', backendPreferences);
  console.log('[配置加载] 前端默认配置:', overridesPreferences);

  // 4. 合并配置：后端配置优先级高于前端配置
  // defu/merge 的特点是第一个参数优先，所以后端配置放前面
  const finalPreferences = merge({}, backendPreferences, overridesPreferences);
  console.log('[配置加载] 合并后配置:', finalPreferences);

  // 5. app偏好设置初始化
  await initPreferences({
    namespace,
    overrides: finalPreferences,
  });

  // 启动应用并挂载
  // vue应用主要逻辑及视图
  const { bootstrap } = await import('./bootstrap');
  await bootstrap(namespace);

  // 移除并销毁loading
  unmountGlobalLoading();
}

initApplication();
