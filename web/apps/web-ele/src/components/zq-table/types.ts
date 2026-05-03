import type { Column } from 'element-plus';

import type { Ref } from 'vue';

import type { BaseFormComponentType, VbenFormProps } from '@vben/common-ui';
import type { ClassType, DeepPartial } from '@vben/types';

import type { ZqTableApi } from './api';

import { useVbenForm } from '@vben/common-ui';

export interface ZqPaginationInfo {
  currentPage: number;
  pageSize: number;
  total: number;
}

export interface ZqProxyConfig {
  enabled?: boolean;
  autoLoad?: boolean;
  ajax?: {
    query?: (params: {
      form: any;
      page: ZqPaginationInfo;
      sort: any;
    }) => Promise<any>;
    queryAll?: (params: { form: any; sort: any }) => Promise<any>;
  };
}

export interface ZqPagerConfig {
  enabled?: boolean;
  pageSize?: number;
  pageSizes?: number[];
  currentPage?: number;
  total?: number;
  layout?: string;
  background?: boolean;
}

export interface ZqToolbarConfig {
  title?: string;
  search?: boolean; // 是否显示搜索切换按钮
  refresh?: boolean; // 是否显示刷新按钮
  zoom?: boolean; // 是否显示全屏按钮
  custom?: boolean; // 是否显示列设置
  tools?: any[]; // 自定义工具栏按钮
}

export interface ZqTableGridOptions<T = any> {
  /** 列配置 */
  columns?: Column<T>[];
  /** 数据 */
  data?: T[];
  /** 代理配置 */
  proxyConfig?: ZqProxyConfig;
  /** 分页配置 */
  pagerConfig?: ZqPagerConfig;
  /** 工具栏配置 */
  toolbarConfig?: ZqToolbarConfig;
  /** 高度 */
  height?: number | string;
  /** 其他 Element Plus Table V2 props */
  [key: string]: any;
}

export interface ZqTableProps<
  T extends Record<string, any> = any,
  D extends BaseFormComponentType = BaseFormComponentType,
> {
  /**
   * 标题
   */
  tableTitle?: string;
  /**
   * 标题帮助
   */
  tableTitleHelp?: string;
  /**
   * 组件class
   */
  class?: ClassType;
  /**
   * zq-table class
   */
  gridClass?: ClassType;
  /**
   * grid 配置
   */
  gridOptions?: DeepPartial<ZqTableGridOptions<T>>;
  /**
   * grid 事件
   */
  gridEvents?: Record<string, (...args: any[]) => any>;
  /**
   * 表单配置
   */
  formOptions?: VbenFormProps<D>;
  /**
   * 显示搜索表单
   */
  showSearchForm?: boolean;
  /**
   * 搜索表单与表格主体之间的分隔条
   */
  separator?: boolean | { backgroundColor?: string; show?: boolean };
}

export type ExtendedZqTableApi<
  D extends Record<string, any> = any,
  F extends BaseFormComponentType = BaseFormComponentType,
> = ZqTableApi<D> & {
  useStore: <T = NoInfer<ZqTableProps<D, F>>>(
    selector?: (state: NoInfer<ZqTableProps<any, any>>) => T,
  ) => Readonly<Ref<T>>;
};

export interface SetupZqTable {
  useVbenForm: typeof useVbenForm;
}
