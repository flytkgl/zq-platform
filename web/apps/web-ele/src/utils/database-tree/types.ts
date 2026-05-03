/**
 * 数据库树节点类型定义
 */

// 节点类型
export type TreeNodeType =
  | 'connection'
  | 'database'
  | 'schema'
  | 'table'
  | 'tables-folder'
  | 'view'
  | 'views-folder';

// 节点元数据
export interface TreeNodeMeta {
  dbName?: string;
  dbType?: string;
  database?: string;
  schema?: string;
  table?: string;
  view?: string;
}

// 树节点
export interface TreeNode {
  id: string;
  label: string;
  type: TreeNodeType;
  isLeaf: boolean;
  meta?: TreeNodeMeta;
  children?: TreeNode[];
}

// 表字段信息
export interface TableField {
  name: string;
  type: string;
  comment: string;
  nullable: boolean;
  isPrimaryKey: boolean;
}

// 右键菜单项
export interface ContextMenuItem {
  label: string;
  icon: any;
  action: () => void;
  divided?: boolean;
  danger?: boolean;
  disabled?: boolean;
}
