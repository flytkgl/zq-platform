import type { EditorView } from '@codemirror/view';

export type CodeLanguage =
  | 'css'
  | 'html'
  | 'javascript'
  | 'json'
  | 'markdown'
  | 'python'
  | 'sql'
  | 'typescript'
  | 'xml'
  | 'yaml';

export interface CodeEditorProps {
  /** 代码内容 */
  modelValue?: string;
  /** 语言类型 */
  language?: CodeLanguage | string;
  /** 主题: light/dark/auto(跟随系统) */
  theme?: 'auto' | 'dark' | 'light';
  /** 是否只读 */
  readonly?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 高度 */
  height?: number | string;
  /** 最小高度 */
  minHeight?: number | string;
  /** 最大高度 */
  maxHeight?: number | string;
  /** 占位符 */
  placeholder?: string;
  /** Tab 大小 */
  tabSize?: number;
  /** 是否显示行号 */
  lineNumbers?: boolean;
  /** 是否自动换行 */
  lineWrapping?: boolean;
  /** 是否显示代码折叠 */
  foldGutter?: boolean;
  /** 是否高亮当前行 */
  highlightActiveLine?: boolean;
  /** 是否显示括号匹配 */
  bracketMatching?: boolean;
  /** 是否启用自动补全 */
  autocompletion?: boolean;
  /** 是否显示缩进指南 */
  indentGuide?: boolean;
}

export interface CodeEditorEmits {
  (e: 'update:modelValue', value: string): void;
  (e: 'change', value: string): void;
  (e: 'focus'): void;
  (e: 'blur'): void;
  (e: 'ready', view: EditorView): void;
}

export interface CodeEditorExpose {
  /** 获取 EditorView 实例 */
  getView: () => EditorView | null;
  /** 聚焦编辑器 */
  focus: () => void;
  /** 获取代码内容 */
  getValue: () => string;
  /** 设置代码内容 */
  setValue: (value: string) => void;
  /** 格式化代码(仅支持 JSON) */
  format: () => void;
}
