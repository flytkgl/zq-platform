import type { Editor } from '@tiptap/vue-3';

export interface RichTextEditorProps {
  /** 编辑器内容 (HTML 格式) */
  modelValue?: string;
  /** 占位符 */
  placeholder?: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否只读 */
  readonly?: boolean;
  /** 最小高度 */
  minHeight?: number | string;
  /** 最大高度 */
  maxHeight?: number | string;
  /** 是否显示工具栏 */
  showToolbar?: boolean;
  /** 是否显示字数统计 */
  showWordCount?: boolean;
  /** 最大字符数 */
  maxLength?: number;
  /** 自定义工具栏配置 */
  toolbarConfig?: ToolbarConfig;
}

export interface RichTextEditorEmits {
  (e: 'update:modelValue', value: string): void;
  (e: 'change', value: string): void;
  (e: 'focus', event: FocusEvent): void;
  (e: 'blur', event: FocusEvent): void;
  (e: 'ready', editor: Editor): void;
}

export interface ToolbarConfig {
  /** 显示的工具组 */
  groups?: ToolbarGroup[];
  /** 插入功能细分控制 */
  insert?: {
    attachment?: boolean;
    image?: boolean;
    link?: boolean;
    table?: boolean;
    video?: boolean;
  };
}

export type ToolbarGroup =
  | 'align' // 对齐方式
  | 'blockquote' // 引用
  | 'clear' // 清除格式
  | 'code' // 代码
  | 'color' // 文字颜色/背景色
  | 'divider' // 分割线
  | 'format' // 加粗/斜体/下划线/删除线
  | 'heading' // 标题
  | 'history' // 撤销/重做
  | 'indent' // 缩进
  | 'insert' // 插入链接/图片/表格/附件/视频
  | 'list'; // 列表

export const defaultToolbarGroups: ToolbarGroup[] = [
  'history',
  'heading',
  'format',
  'color',
  'align',
  'list',
  'insert',
  'blockquote',
  'code',
  'divider',
  'clear',
];

/** 默认插入功能配置 - 基础功能默认开启 */
export const defaultInsertConfig = {
  link: true,
  image: true,
  table: true,
  attachment: false, // 附件默认关闭
  video: false, // 视频默认关闭
};
