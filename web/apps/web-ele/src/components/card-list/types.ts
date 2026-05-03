/**
 * 卡片列表项配置接口
 */
export interface CardListItem {
  id: string;
  [key: string]: any;
}

/**
 * 卡片列表搜索字段配置
 */
export interface SearchField {
  field: string;
  /** 如果为true，则进行模糊搜索 */
  fuzzy?: boolean;
}

/**
 * 卡片列表显示模式
 */
export type CardListDisplayMode = 'center' | 'default';

/**
 * 卡片列表配置选项
 */
export interface CardListOptions<T extends CardListItem = CardListItem> {
  /** 搜索关键词字段，支持多字段搜索 */
  searchFields: SearchField[];
  /** 标题字段，必需 */
  titleField: keyof T;
  /** 是否显示骨架屏加载 */
  showSkeleton?: boolean;
  /** 加载时的骨架屏数量 */
  skeletonCount?: number;
  /** 项目渲染函数 */
  renderItem?: (item: T, hovered: boolean) => any;
  /** 显示模式：'default' - 两行显示（标题+详情），'center' - 一行居中显示 */
  displayMode?: CardListDisplayMode;
}

/**
 * 卡片列表事件
 */
export interface CardListEmits {
  select: [id: string | undefined];
  edit: [item: CardListItem, event: Event];
  delete: [item: CardListItem, event: Event];
  add: [];
  'form-success': [];
}
