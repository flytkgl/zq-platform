import type { Extension } from '@codemirror/state';

import type { CodeLanguage } from './types';

// 语言扩展懒加载映射
const languageLoaders: Record<CodeLanguage, () => Promise<Extension>> = {
  javascript: async () => {
    const { javascript } = await import('@codemirror/lang-javascript');
    return javascript();
  },
  typescript: async () => {
    const { javascript } = await import('@codemirror/lang-javascript');
    return javascript({ typescript: true });
  },
  python: async () => {
    const { python } = await import('@codemirror/lang-python');
    return python();
  },
  sql: async () => {
    const { sql } = await import('@codemirror/lang-sql');
    return sql();
  },
  json: async () => {
    const { json } = await import('@codemirror/lang-json');
    return json();
  },
  html: async () => {
    const { html } = await import('@codemirror/lang-html');
    return html();
  },
  css: async () => {
    const { css } = await import('@codemirror/lang-css');
    return css();
  },
  markdown: async () => {
    const { markdown } = await import('@codemirror/lang-markdown');
    return markdown();
  },
  xml: async () => {
    const { xml } = await import('@codemirror/lang-xml');
    return xml();
  },
  yaml: async () => {
    const { yaml } = await import('@codemirror/lang-yaml');
    return yaml();
  },
};

/**
 * 获取语言扩展
 * @param language 语言类型
 * @returns 语言扩展
 */
export async function getLanguageExtension(
  language: CodeLanguage | string,
): Promise<Extension | null> {
  const loader = languageLoaders[language as CodeLanguage];
  if (loader) {
    return await loader();
  }
  return null;
}

/**
 * 支持的语言列表
 */
export const supportedLanguages: CodeLanguage[] = [
  'javascript',
  'typescript',
  'python',
  'sql',
  'json',
  'html',
  'css',
  'markdown',
  'xml',
  'yaml',
];
