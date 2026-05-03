export interface MultiDataViewProps<T = any> {
  /**
   * 静态数据源
   */
  data?: T[];
  /**
   * API 数据请求函数
   * (params: any) => Promise<{ items: T[]; total: number }>
   */
  api?: (params: any) => Promise<T[] | { items: T[]; total?: number }>;
  /**
   * API 请求的额外参数
   */
  params?: Record<string, any>;
  /**
   * 是否自动加载 API 数据
   * @default true
   */
  autoLoad?: boolean;
  /**
   * 标题
   */
  title?: string;
  /**
   * 显示模式
   * @default 'card'
   */
  mode?: 'card' | 'list';
  /**
   * 数据主键字段名
   * @default 'id'
   */
  rowKey?: string;
  /**
   * 是否显示工具栏
   * @default true
   */
  showToolbar?: boolean;
  /**
   * 是否开启多选
   * @default false
   */
  selection?: boolean;
  /**
   * 分页配置
   * boolean: 是否显示
   * object: ElPagination props
   * @default true
   */
  pagination?: boolean | PaginationProps;
  /**
   * 卡片网格配置 (参考 Element Plus Row/Col 或 Tailwind)
   * 如果不传，使用默认响应式配置
   */
  cardGrid?: {
    gutter?: number;
    lg?: number; // >=1200px span
    md?: number; // >=992px span
    sm?: number; // >=768px span
    xl?: number; // >=1920px span
    xs?: number; // <768px span
  };
  /**
   * 卡片模式下操作按钮位置
   * @default 'overlay'
   */
  cardActionPosition?: 'footer' | 'overlay';
}

export interface PaginationProps {
  currentPage?: number;
  pageSize?: number;
  total?: number;
  pageSizes?: number[];
  layout?: string;
}
