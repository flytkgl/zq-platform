/**
 * 省市区街道村庄选择器类型定义
 */

// 区域数据项
export interface RegionItem {
  code: string;
  name: string;
  children?: RegionItem[];
}

// 数据源类型
export type DataSourceType = 'api' | 'static';

// 级别类型：1-省 2-市 3-区 4-街道 5-村庄
export type RegionLevel = 1 | 2 | 3 | 4 | 5;

// 组件 Props
export interface RegionSelectorProps {
  modelValue?: string | string[];
  level?: RegionLevel;
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  multiple?: boolean;
  showAllLevels?: boolean;
  separator?: string;
  dataSource?: DataSourceType;
  apiUrl?: string;
  lazy?: boolean; // 是否懒加载
  checkStrictly?: boolean; // 是否严格的选择任意一级
  expandTrigger?: 'click' | 'hover'; // 展开触发方式
}

// 组件 Emits
export interface RegionSelectorEmits {
  (e: 'update:modelValue', value: string | string[] | undefined): void;
  (
    e: 'change',
    value: string | string[] | undefined,
    selectedOptions: RegionItem[],
  ): void;
}
