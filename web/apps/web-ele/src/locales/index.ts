import type { Language } from 'element-plus/es/locale';

import type { App } from 'vue';

import type { LocaleSetupOptions, SupportedLanguagesType } from '@vben/locales';

import { ref } from 'vue';

import {
  $t,
  setupI18n as coreSetup,
  getSystemLanguage,
  loadLocalesMapFromDir,
} from '@vben/locales';
import { preferences } from '@vben/preferences';

import dayjs from 'dayjs';
import enLocale from 'element-plus/es/locale/lang/en';
import defaultLocale from 'element-plus/es/locale/lang/zh-cn';
import zhTwLocale from 'element-plus/es/locale/lang/zh-tw';

const elementLocale = ref<Language>(defaultLocale);

const modules = import.meta.glob('./langs/**/*.json');

const localesMap = loadLocalesMapFromDir(
  /\.\/langs\/([^/]+)\/(.*)\.json$/,
  modules,
);
/** zq-table 需要提升到根级的命名空间，以便 t('table.xxx') 等能正确解析 */
const ZQ_TABLE_ROOT_KEYS = [
  'common',
  'table',
  'toolbar',
  'filter',
  'field',
  'view',
  'kanban',
  'gantt',
  'calendar',
  'gallery',
  'form',
  'dashboard',
  'sidebar',
  'app',
  'theme',
  'language',
  'link',
  'cellRenderer',
  'permission',
  'summary',
  'formula',
  'validation',
  'comment',
  'mention',
  'document',
  'trash',
  'version',
  'template',
] as const;

/**
 * 加载应用特有的语言包
 * 这里也可以改造为从服务端获取翻译数据
 * @param lang
 */
async function loadMessages(lang: SupportedLanguagesType) {
  const [appLocaleMessages] = await Promise.all([
    localesMap[lang]?.(),
    loadThirdPartyMessage(lang),
  ]);
  const messages = appLocaleMessages?.default || {};
  // 将 zq-table / zq-smart-table 的 table/toolbar/filter 等命名空间提升到根级
  // 使用浅合并：zq-table 的子键补充到已有命名空间，app 级别的同名 key 优先保留
  const merged = { ...messages };
  for (const ns of ['zq-table', 'zq-smart-table'] as const) {
    const src = messages[ns];
    if (src && typeof src === 'object') {
      for (const key of ZQ_TABLE_ROOT_KEYS) {
        if (key in src && src[key] != null) {
          const existing = merged[key];
          if (
            existing &&
            typeof existing === 'object' &&
            typeof src[key] === 'object'
          ) {
            merged[key] = { ...src[key], ...existing };
          } else {
            merged[key] = src[key];
          }
        }
      }
    }
  }
  return merged;
}

/**
 * 加载第三方组件库的语言包
 * @param lang
 */
async function loadThirdPartyMessage(lang: SupportedLanguagesType) {
  await Promise.all([loadElementLocale(lang), loadDayjsLocale(lang)]);
}

/**
 * 加载dayjs的语言包
 * @param lang
 */
async function loadDayjsLocale(lang: SupportedLanguagesType) {
  let locale;
  switch (lang) {
    case 'en-US': {
      locale = await import('dayjs/locale/en');
      break;
    }
    case 'zh-CN': {
      locale = await import('dayjs/locale/zh-cn');
      break;
    }
    case 'zh-TW': {
      locale = await import('dayjs/locale/zh-tw');
      break;
    }
    // 默认使用英语
    default: {
      locale = await import('dayjs/locale/en');
    }
  }
  if (locale) {
    dayjs.locale(locale);
  } else {
    console.error(`Failed to load dayjs locale for ${lang}`);
  }
}

/**
 * 加载element-plus的语言包
 * @param lang
 */
async function loadElementLocale(lang: SupportedLanguagesType) {
  switch (lang) {
    case 'en-US': {
      elementLocale.value = enLocale;
      break;
    }
    case 'zh-CN': {
      elementLocale.value = defaultLocale;
      break;
    }
    case 'zh-TW': {
      elementLocale.value = zhTwLocale;
      break;
    }
  }
}

async function setupI18n(app: App, options: LocaleSetupOptions = {}) {
  // 如果是跟随系统，获取系统语言
  const locale = preferences.app.locale;
  const actualLocale = locale === 'auto' ? getSystemLanguage() : locale;

  await coreSetup(app, {
    defaultLocale: actualLocale,
    loadMessages,
    missingWarn: !import.meta.env.PROD,
    ...options,
  });
}

export { $t, elementLocale, setupI18n };
