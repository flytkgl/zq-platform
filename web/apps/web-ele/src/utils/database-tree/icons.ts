import type { TreeNodeType } from './types';

/**
 * 数据库树节点图标配置
 */
import {
  Database,
  Eye,
  Layers,
  Server,
  Table,
  TableProperties,
} from '@vben/icons';

// 节点图标映射
const iconMap: Record<TreeNodeType, any> = {
  connection: Server,
  database: Database,
  schema: Layers,
  'tables-folder': TableProperties,
  'views-folder': Eye,
  table: Table,
  view: Eye,
};

// 节点图标样式映射
const iconClassMap: Record<TreeNodeType, string> = {
  connection: 'text-blue-500',
  database: 'text-green-500',
  schema: 'text-purple-500',
  'tables-folder': 'text-orange-500',
  'views-folder': 'text-cyan-500',
  table: 'text-muted-foreground',
  view: 'text-muted-foreground',
};

/**
 * 获取节点图标组件
 */
export function getNodeIcon(type: string | TreeNodeType): any {
  return iconMap[type as TreeNodeType] || Database;
}

/**
 * 获取节点图标样式类
 */
export function getNodeIconClass(type: string | TreeNodeType): string {
  return iconClassMap[type as TreeNodeType] || 'text-muted-foreground';
}
