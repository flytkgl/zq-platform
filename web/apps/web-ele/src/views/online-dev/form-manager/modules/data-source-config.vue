<script lang="ts" setup>
import type { ColumnInfo } from '#/api/core/database-manager';

import { computed, onMounted, ref } from 'vue';

import {
  Copy,
  Database,
  Edit,
  Eye,
  FilePlus,
  Link2,
  Plus,
  RefreshCw,
  Trash2,
} from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElAlert,
  ElButton,
  ElCheckbox,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElPopconfirm,
  ElScrollbar,
  ElSelect,
  ElTag,
  ElTooltip,
  ElTree,
} from 'element-plus';

import {
  executeDDLApi,
  getDatabaseConfigsApi,
  getSchemasApi,
  getTableColumnsApi,
  getTablesApi,
} from '#/api/core/database-manager';
import { getNodeIcon, getNodeIconClass } from '#/utils/database-tree';
import {
  getDataTypesByDbType,
  normalizeDbType,
  typeHasLength as typeHasLengthUtil,
  typeHasPrecision as typeHasPrecisionUtil,
} from '#/utils/database-types';

import CreateTableModal from '../../../_core/database-manager/modules/create-table-modal.vue';
import TableEditorModal from '../../../_core/database-manager/modules/table-editor-modal.vue';

// 树节点类型
interface TreeNode {
  id: string;
  label: string;
  type: 'connection' | 'database' | 'schema' | 'table';
  isLeaf: boolean;
  meta?: {
    database?: string;
    dbName?: string;
    dbType?: string;
    schema?: string;
    table?: string;
  };
  children?: TreeNode[];
}

// 表配置类型
export interface TableConfig {
  id: string;
  type: 'main' | 'sub'; // 主表 / 从表
  tableName: string; // 表名
  alias: string; // 别名
  foreignKey?: string; // 外键字段（从表需要）
  relatedField?: string; // 关联主表字段（从表需要）
  relationType?: 'one-to-many' | 'one-to-one'; // 关联类型
  fields: TableField[]; // 表字段列表
  meta?: {
    // 数据库元信息
    database?: string;
    dbName?: string;
    dbType?: string;
    schema?: string;
  };
}

export interface TableField {
  name: string; // 字段名
  type: string; // 字段类型
  comment: string; // 字段注释
  nullable: boolean; // 是否可空
  isPrimaryKey: boolean; // 是否主键
  maxLength?: number; // 最大长度 (varchar/char)
  precision?: number; // 数值精度
  scale?: number; // 小数位数
  uniqueCheck?: boolean; // 唯一性检查
}

// 右键菜单项类型
interface ContextMenuItem {
  label: string;
  icon: any;
  action: () => void;
  divided?: boolean;
}

// Props
interface Props {
  modelValue: TableConfig[];
  workflowMode?: boolean; // 工作流模式：隐藏左侧数据库树，主表/从表可编辑
}

const props = withDefaults(defineProps<Props>(), {
  workflowMode: false,
});

const emit = defineEmits<{
  'update:modelValue': [value: TableConfig[]];
}>();

// 内部数据
const tables = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

// 树相关
const treeRef = ref();
const treeData = ref<TreeNode[]>([]);
const loading = ref(false);
const defaultExpandedKeys = ref<string[]>([]);

// 树配置
const treeProps = {
  label: 'label',
  children: 'children',
  isLeaf: 'isLeaf',
};

// 当前选中的表节点（用于显示字段预览）
const selectedTableNode = ref<null | TreeNode>(null);
const previewFields = ref<TableField[]>([]);
const previewLoading = ref(false);

// 右键菜单
const contextMenuVisible = ref(false);
const contextMenuStyle = ref({ left: '0px', top: '0px' });
const contextMenuNode = ref<null | TreeNode>(null);

// 创建表Modal
const createTableModalVisible = ref(false);
const createTableData = ref({
  dbName: '',
  database: '',
  schema: '',
  dbType: '',
});

// 编辑表Modal
const tableEditorModalVisible = ref(false);
const tableEditorData = ref({
  dbName: '',
  database: '',
  schema: '',
  tableName: '',
  dbType: '',
});

// 获取主表
const mainTable = computed(() => tables.value.find((t) => t.type === 'main'));

// 获取从表列表
const subTables = computed(() => tables.value.filter((t) => t.type === 'sub'));

// 主表字段列表（用于从表关联选择）
const mainTableFields = computed(() => {
  if (!mainTable.value) return [];
  return mainTable.value.fields.map((f) => f.name);
});

// 过滤后的主表字段列表（工作流模式下过滤系统字段）
const filteredMainTableFields = computed(() => {
  if (!mainTable.value) return [];
  if (props.workflowMode) {
    // 工作流模式下过滤掉系统字段
    return mainTable.value.fields.filter(
      (f) => !SYSTEM_FIELDS.includes(f.name),
    );
  }
  return mainTable.value.fields;
});

// 过滤从表字段（工作流模式下过滤系统字段）
function getFilteredSubTableFields(subTable: TableConfig): TableField[] {
  if (props.workflowMode) {
    return subTable.fields.filter((f) => !SYSTEM_FIELDS.includes(f.name));
  }
  return subTable.fields;
}

// 根据数据库类型获取数据类型列表
const fieldTypes = computed(() => {
  // 工作流模式下默认使用 PostgreSQL 类型
  const dbType = mainTable.value?.meta?.dbType?.toLowerCase() || 'postgresql';
  return getDataTypesByDbType(dbType);
});

// 判断字段类型是否需要长度
function typeHasLength(type: string): boolean {
  return typeHasLengthUtil(fieldTypes.value, type);
}

// 判断字段类型是否需要精度（小数位）
function typeHasPrecision(type: string): boolean {
  return typeHasPrecisionUtil(fieldTypes.value, type);
}

// 添加字段（工作流模式）
function addField(table: TableConfig) {
  table.fields.push({
    name: '',
    type: 'varchar',
    comment: '',
    nullable: true,
    isPrimaryKey: false,
    maxLength: 255,
  });
}

// 删除字段（工作流模式）
function removeField(table: TableConfig, index: number) {
  table.fields.splice(index, 1);
}

// 加载数据库配置（根节点）
async function loadDatabaseConfigs() {
  loading.value = true;
  try {
    const configs = await getDatabaseConfigsApi();
    // 只取第一个配置（默认数据库）
    const defaultConfig = configs[0];
    if (defaultConfig) {
      // 直接显示数据库节点，不显示连接层级
      const dbNodeId = `db-${defaultConfig.db_name}-${defaultConfig.database}`;
      treeData.value = [
        {
          id: dbNodeId,
          label: defaultConfig.database,
          type: 'database' as const,
          isLeaf: false,
          meta: {
            dbName: defaultConfig.db_name,
            dbType: defaultConfig.db_type,
            database: defaultConfig.database,
          },
        },
      ];

      // 设置默认展开的节点
      defaultExpandedKeys.value = [dbNodeId];
    } else {
      treeData.value = [];
    }
  } catch (error) {
    console.error('Failed to load database configs:', error);
    ElMessage.error($t('form-manager.dataSource.loadConfigFailed'));
  } finally {
    loading.value = false;
  }
}

// 加载Schema列表
async function loadSchemas(dbName: string, database: string, dbType?: string) {
  try {
    const schemas = await getSchemasApi(dbName, database);
    return schemas.map((schema) => ({
      id: `schema-${dbName}-${database}-${schema.name}`,
      label: schema.name,
      type: 'schema' as const,
      isLeaf: false,
      meta: {
        dbName,
        dbType, // 直接使用传入的 dbType
        database,
        schema: schema.name,
      },
    }));
  } catch (error) {
    console.error('Failed to load schemas:', error);
    ElMessage.error($t('form-manager.dataSource.loadSchemaFailed'));
    return [];
  }
}

// 加载表列表
async function loadTables(
  dbName: string,
  database: string,
  schema?: string,
  dbType?: string,
) {
  try {
    const tableList = await getTablesApi(dbName, database, schema);

    return tableList.map((table) => ({
      id: `table-${dbName}-${database}-${schema || ''}-${table.table_name}`,
      label: table.table_name,
      type: 'table' as const,
      isLeaf: true,
      meta: {
        dbName,
        dbType,
        database,
        schema: schema || table.schema_name,
        table: table.table_name,
      },
    }));
  } catch (error) {
    console.error('Failed to load tables:', error);
    ElMessage.error($t('form-manager.dataSource.loadTableFailed'));
    return [];
  }
}

// 懒加载子节点
async function loadNode(node: any, resolve: any) {
  if (node.level === 0) {
    resolve(treeData.value);
    return;
  }

  const nodeData = node.data as TreeNode;
  const { type, meta } = nodeData;

  if (!meta) {
    resolve([]);
    return;
  }

  try {
    // 数据库节点：加载 Schema 或直接加载表
    if (type === 'database' && meta.dbName && meta.database) {
      const dbType = meta.dbType?.toLowerCase();
      if (dbType === 'postgresql' || dbType === 'sqlserver') {
        // PostgreSQL 和 SQL Server 支持 Schema，先加载 Schema
        const nodes = await loadSchemas(
          meta.dbName,
          meta.database,
          meta.dbType,
        );
        resolve(nodes);
      } else {
        // MySQL 等直接加载表
        const nodes = await loadTables(
          meta.dbName,
          meta.database,
          undefined,
          meta.dbType,
        );
        resolve(nodes);
      }
      return;
    }

    // Schema 节点：加载表
    if (type === 'schema' && meta.dbName && meta.database) {
      const nodes = await loadTables(
        meta.dbName,
        meta.database,
        meta.schema,
        meta.dbType,
      );
      resolve(nodes);
      return;
    }

    resolve([]);
  } catch (error) {
    console.error('Failed to load node:', error);
    ElMessage.error($t('form-manager.dataSource.loadNodeFailed'));
    resolve([]);
  }
}

// 节点点击 - 预览表字段
async function handleNodeClick(data: TreeNode) {
  if (data.type === 'table' && data.meta) {
    selectedTableNode.value = data;
    previewLoading.value = true;

    try {
      const columns = await getTableColumnsApi(
        data.meta.dbName!,
        data.meta.table!,
        data.meta.database,
        data.meta.schema,
      );
      previewFields.value = columns.map((col: ColumnInfo) => ({
        name: col.column_name,
        type: normalizeDbType(col.data_type),
        comment: col.description || '',
        nullable: col.is_nullable,
        isPrimaryKey: col.is_primary_key,
        uniqueCheck: col.is_unique,
      }));
    } catch (error) {
      console.error('Failed to load columns:', error);
      previewFields.value = [];
    } finally {
      previewLoading.value = false;
    }
  }
}

// 生成唯一ID
function generateId() {
  return `table_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

// 数据权限所需的系统字段
const SYSTEM_FIELDS = [
  'sys_create_datetime',
  'sys_update_datetime',
  'sys_creator_id',
  'sys_modifier_id',
  'sys_dept_id',
  'sort',
];

// 检查表是否缺少系统字段
function checkMissingSystemFields(fields: TableField[]): string[] {
  const fieldNames = new Set(fields.map((f) => f.name));
  return SYSTEM_FIELDS.filter((sf) => !fieldNames.has(sf));
}

// 系统字段注释映射
const SYSTEM_FIELD_COMMENTS: Record<string, string> = {
  sys_create_datetime: '创建时间',
  sys_update_datetime: '更新时间',
  sys_creator_id: '创建人ID',
  sys_modifier_id: '修改人ID',
  sys_dept_id: '部门ID',
  sort: '排序',
};

// 生成添加系统字段的 SQL
function generateAddSystemFieldsSQL(
  tableName: string,
  missingFields: string[],
  dbType: string,
  database?: string,
  schema?: string,
): string {
  const sqlStatements: string[] = [];
  const fullTableName = schema
    ? `"${schema}"."${tableName}"`
    : `"${tableName}"`;
  const dbTypeLower = dbType.toLowerCase();

  missingFields.forEach((fieldName) => {
    let fieldDef = '';
    if (
      fieldName === 'sys_create_datetime' ||
      fieldName === 'sys_update_datetime'
    ) {
      fieldDef = `"${fieldName}" TIMESTAMP`;
    } else if (fieldName === 'sort') {
      fieldDef = `"${fieldName}" INTEGER DEFAULT 0`;
    } else {
      fieldDef = `"${fieldName}" VARCHAR(36)`;
    }
    sqlStatements.push(`ALTER TABLE ${fullTableName} ADD COLUMN ${fieldDef};`);

    // PostgreSQL 添加字段注释
    if (dbTypeLower === 'postgresql') {
      const comment = SYSTEM_FIELD_COMMENTS[fieldName] || fieldName;
      sqlStatements.push(
        `COMMENT ON COLUMN ${fullTableName}."${fieldName}" IS '${comment}';`,
      );
    }
  });

  return sqlStatements.join('\n');
}

// 添加主表
async function addMainTable(node: TreeNode) {
  if (node.type !== 'table' || !node.meta) return;

  // 获取字段
  let fields: TableField[] = [];
  try {
    const columns = await getTableColumnsApi(
      node.meta.dbName!,
      node.meta.table!,
      node.meta.database,
      node.meta.schema,
    );
    fields = columns.map((col: ColumnInfo) => ({
      name: col.column_name,
      type: normalizeDbType(col.data_type),
      comment: col.description || '',
      nullable: col.is_nullable,
      isPrimaryKey: col.is_primary_key,
      uniqueCheck: col.is_unique,
      maxLength: col.character_maximum_length,
      precision: col.numeric_precision,
      scale: col.numeric_scale,
    }));
  } catch (error) {
    console.error('Failed to load columns:', error);
  }

  // 检查是否缺少系统字段
  const missingFields = checkMissingSystemFields(fields);
  if (missingFields.length > 0) {
    try {
      await ElMessageBox.confirm(
        $t('form-manager.dataSource.missingSystemFieldsMessage', {
          fields: missingFields.join(', '),
        }),
        $t('form-manager.dataSource.missingSystemFieldsTitle'),
        {
          confirmButtonText: $t('form-manager.dataSource.autoAddFields'),
          cancelButtonText: $t('form-manager.dataSource.ignoreAndContinue'),
          type: 'warning',
          dangerouslyUseHTMLString: true,
        },
      );

      // 用户点击确认，自动添加缺少的字段
      const sql = generateAddSystemFieldsSQL(
        node.meta.table!,
        missingFields,
        node.meta.dbType || 'postgresql',
        node.meta.database,
        node.meta.schema,
      );

      try {
        const result = await executeDDLApi(node.meta.dbName!, {
          sql,
          database: node.meta.database,
          schema_name: node.meta.schema,
        });

        if (result.success) {
          ElMessage.success(
            $t('form-manager.dataSource.addSystemFieldsSuccess'),
          );
          // 重新获取字段
          const columns = await getTableColumnsApi(
            node.meta.dbName!,
            node.meta.table!,
            node.meta.database,
            node.meta.schema,
          );
          fields = columns.map((col: ColumnInfo) => ({
            name: col.column_name,
            type: normalizeDbType(col.data_type),
            comment: col.description || '',
            nullable: col.is_nullable,
            isPrimaryKey: col.is_primary_key,
            uniqueCheck: col.is_unique,
            maxLength: col.character_maximum_length,
            precision: col.numeric_precision,
            scale: col.numeric_scale,
          }));
        } else {
          ElMessage.error(
            result.message ||
              $t('form-manager.dataSource.addSystemFieldsFailed'),
          );
        }
      } catch (error: any) {
        ElMessage.error(
          error.message || $t('form-manager.dataSource.addSystemFieldsFailed'),
        );
      }
    } catch {
      // 用户点击取消，忽略继续
    }
  }

  // 如果已有主表，先移除
  const existingMainIndex = tables.value.findIndex((t) => t.type === 'main');
  if (existingMainIndex !== -1) {
    tables.value.splice(existingMainIndex, 1);
  }

  tables.value.unshift({
    id: generateId(),
    type: 'main',
    tableName: node.meta.table!,
    alias: node.meta.table!,
    fields,
    meta: {
      dbName: node.meta.dbName,
      dbType: node.meta.dbType,
      database: node.meta.database,
      schema: node.meta.schema,
    },
  });

  ElMessage.success(
    $t('form-manager.dataSource.setMainSuccess', { name: node.meta.table }),
  );
}

// 添加从表
async function addSubTable(node: TreeNode) {
  if (node.type !== 'table' || !node.meta) return;

  // 检查是否已添加
  if (tables.value.find((t) => t.tableName === node.meta?.table)) {
    ElMessage.warning($t('form-manager.dataSource.tableAlreadyAdded'));
    return;
  }

  // 获取字段
  let fields: TableField[] = [];
  try {
    const columns = await getTableColumnsApi(
      node.meta.dbName!,
      node.meta.table!,
      node.meta.database,
      node.meta.schema,
    );
    fields = columns.map((col: ColumnInfo) => ({
      name: col.column_name,
      type: normalizeDbType(col.data_type),
      comment: col.description || '',
      nullable: col.is_nullable,
      isPrimaryKey: col.is_primary_key,
      uniqueCheck: col.is_unique,
      maxLength: col.character_maximum_length,
      precision: col.numeric_precision,
      scale: col.numeric_scale,
    }));
  } catch (error) {
    console.error('Failed to load columns:', error);
  }

  // 检查是否缺少系统字段
  const missingFields = checkMissingSystemFields(fields);
  if (missingFields.length > 0) {
    try {
      await ElMessageBox.confirm(
        $t('form-manager.dataSource.missingSystemFieldsMessage', {
          fields: missingFields.join(', '),
        }),
        $t('form-manager.dataSource.missingSystemFieldsTitle'),
        {
          confirmButtonText: $t('form-manager.dataSource.autoAddFields'),
          cancelButtonText: $t('form-manager.dataSource.ignoreAndContinue'),
          type: 'warning',
          dangerouslyUseHTMLString: true,
        },
      );

      // 用户点击确认，自动添加缺少的字段
      const sql = generateAddSystemFieldsSQL(
        node.meta.table!,
        missingFields,
        node.meta.dbType || 'postgresql',
        node.meta.database,
        node.meta.schema,
      );

      try {
        const result = await executeDDLApi(node.meta.dbName!, {
          sql,
          database: node.meta.database,
          schema_name: node.meta.schema,
        });

        if (result.success) {
          ElMessage.success(
            $t('form-manager.dataSource.addSystemFieldsSuccess'),
          );
          // 重新获取字段
          const columns = await getTableColumnsApi(
            node.meta.dbName!,
            node.meta.table!,
            node.meta.database,
            node.meta.schema,
          );
          fields = columns.map((col: ColumnInfo) => ({
            name: col.column_name,
            type: normalizeDbType(col.data_type),
            comment: col.description || '',
            nullable: col.is_nullable,
            isPrimaryKey: col.is_primary_key,
            uniqueCheck: col.is_unique,
            maxLength: col.character_maximum_length,
            precision: col.numeric_precision,
            scale: col.numeric_scale,
          }));
        } else {
          ElMessage.error(
            result.message ||
              $t('form-manager.dataSource.addSystemFieldsFailed'),
          );
        }
      } catch (error: any) {
        ElMessage.error(
          error.message || $t('form-manager.dataSource.addSystemFieldsFailed'),
        );
      }
    } catch {
      // 用户点击取消，忽略继续
    }
  }

  tables.value.push({
    id: generateId(),
    type: 'sub',
    tableName: node.meta.table!,
    alias: node.meta.table!,
    foreignKey: '',
    relatedField: 'id',
    relationType: 'one-to-many',
    fields,
    meta: {
      dbName: node.meta.dbName,
      dbType: node.meta.dbType,
      database: node.meta.database,
      schema: node.meta.schema,
    },
  });

  ElMessage.success(
    $t('form-manager.dataSource.addSubSuccess', { name: node.meta.table }),
  );
}

// 移除表
function removeTable(id: string) {
  const index = tables.value.findIndex((t) => t.id === id);
  if (index !== -1) {
    tables.value.splice(index, 1);
  }
}

// 判断表是否已添加
function isTableAdded(tableName: string) {
  return tables.value.some((t) => t.tableName === tableName);
}

// 刷新树
async function refreshTree() {
  await loadDatabaseConfigs();
  ElMessage.success($t('form-manager.dataSource.refreshSuccess'));
}

// 右键菜单 - 显示
function handleContextMenu(event: Event, data: TreeNode) {
  const mouseEvent = event as MouseEvent;
  mouseEvent.preventDefault();
  contextMenuNode.value = data;
  contextMenuStyle.value = {
    left: `${mouseEvent.clientX}px`,
    top: `${mouseEvent.clientY}px`,
  };
  contextMenuVisible.value = true;
}

// 右键菜单 - 关闭
function closeContextMenu() {
  contextMenuVisible.value = false;
}

// 右键菜单 - 刷新节点
async function handleRefreshNode() {
  if (!contextMenuNode.value || !treeRef.value) {
    closeContextMenu();
    return;
  }

  const node = contextMenuNode.value;
  const treeInstance = treeRef.value;

  try {
    const treeNode = treeInstance.getNode(node.id);
    if (!treeNode) {
      ElMessage.warning($t('form-manager.dataSource.nodeNotFound'));
      closeContextMenu();
      return;
    }

    if (treeNode.expanded) {
      treeNode.loaded = false;
      treeNode.childNodes = [];
      treeNode.collapse();
      await new Promise((resolve) => setTimeout(resolve, 100));
      treeNode.expand();
      ElMessage.success($t('form-manager.dataSource.refreshSuccess'));
    } else {
      treeNode.loaded = false;
      treeNode.childNodes = [];
      ElMessage.success($t('form-manager.dataSource.refreshNodeSuccess'));
    }
  } catch (error) {
    console.error('刷新节点失败:', error);
    ElMessage.error($t('form-manager.dataSource.refreshNodeFailed'));
  }

  closeContextMenu();
}

// 右键菜单 - 复制名称
function handleCopyName() {
  if (contextMenuNode.value) {
    navigator.clipboard.writeText(contextMenuNode.value.label);
    ElMessage.success($t('form-manager.dataSource.copyToClipboard'));
  }
  closeContextMenu();
}

// 右键菜单 - 查看字段
function handleViewFields() {
  if (contextMenuNode.value) {
    handleNodeClick(contextMenuNode.value);
  }
  closeContextMenu();
}

// 右键菜单 - 设为主表
function handleSetMainTable() {
  if (contextMenuNode.value) {
    addMainTable(contextMenuNode.value);
  }
  closeContextMenu();
}

// 右键菜单 - 添加为从表
function handleAddSubTable() {
  if (contextMenuNode.value) {
    addSubTable(contextMenuNode.value);
  }
  closeContextMenu();
}

// 右键菜单 - 创建数据库
function handleCreateDatabase() {
  if (contextMenuNode.value) {
    const { meta } = contextMenuNode.value;
    const dbType = meta?.dbType?.toLowerCase();

    ElMessageBox.prompt(
      $t('form-manager.dataSource.inputDatabaseName'),
      $t('form-manager.dataSource.addDatabase'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        inputPattern: /^[a-z_]\w*$/i,
        inputErrorMessage: $t('form-manager.dataSource.databaseNameRule'),
      },
    )
      .then(async ({ value: dbName }) => {
        try {
          let sql = '';
          switch (dbType) {
            case 'mysql': {
              sql = `CREATE DATABASE \`${dbName}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`;

              break;
            }
            case 'postgresql': {
              sql = `CREATE DATABASE "${dbName}";`;

              break;
            }
            case 'sqlserver': {
              sql = `CREATE DATABASE [${dbName}];`;

              break;
            }
            // No default
          }

          const result = await executeDDLApi(meta?.dbName || '', {
            sql,
            database: undefined,
            schema_name: undefined,
          });

          if (result.success) {
            ElMessage.success(
              $t('form-manager.dataSource.databaseCreateSuccess', {
                name: dbName,
              }),
            );
            await handleRefreshNode();
          } else {
            ElMessage.error(
              result.message ||
                $t('form-manager.dataSource.databaseCreateFailed'),
            );
          }
        } catch (error: any) {
          console.error('创建数据库失败:', error);
          ElMessage.error(
            error.message || $t('form-manager.dataSource.databaseCreateFailed'),
          );
        }
      })
      .catch(() => {});
  }
  closeContextMenu();
}

// 右键菜单 - 编辑数据库（重命名）
function handleEditDatabase() {
  if (contextMenuNode.value) {
    const { label } = contextMenuNode.value;

    ElMessageBox.prompt(
      $t('form-manager.dataSource.inputNewDatabaseName'),
      $t('form-manager.dataSource.editDatabase'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        inputValue: label,
        inputPattern: /^[a-z_]\w*$/i,
        inputErrorMessage: $t('form-manager.dataSource.databaseNameRule'),
      },
    )
      .then(async ({ value: newName }) => {
        if (newName === label) {
          ElMessage.info($t('form-manager.dataSource.nameNotChanged'));
          return;
        }
        // 注意：大多数数据库不支持直接重命名数据库，这里只是提示
        ElMessage.warning($t('form-manager.dataSource.renameNotSupported'));
      })
      .catch(() => {});
  }
  closeContextMenu();
}

// 右键菜单 - 创建Schema
function handleCreateSchema() {
  if (contextMenuNode.value) {
    const { meta } = contextMenuNode.value;
    const dbType = meta?.dbType?.toLowerCase();

    ElMessageBox.prompt(
      $t('form-manager.dataSource.inputSchemaName'),
      $t('form-manager.dataSource.createSchema'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        inputPattern: /^[a-z_]\w*$/i,
        inputErrorMessage: $t('form-manager.dataSource.schemaNameRule'),
      },
    )
      .then(async ({ value: schemaName }) => {
        try {
          let sql = '';
          if (dbType === 'postgresql') {
            sql = `CREATE SCHEMA "${schemaName}";`;
          } else if (dbType === 'sqlserver') {
            sql = `CREATE SCHEMA [${schemaName}];`;
          }

          const result = await executeDDLApi(meta?.dbName || '', {
            sql,
            database: meta?.database,
            schema_name: undefined,
          });

          if (result.success) {
            ElMessage.success(
              $t('form-manager.dataSource.schemaCreateSuccess', {
                name: schemaName,
              }),
            );
            await handleRefreshNode();
          } else {
            ElMessage.error(
              result.message ||
                $t('form-manager.dataSource.schemaCreateFailed'),
            );
          }
        } catch (error: any) {
          console.error('创建Schema失败:', error);
          ElMessage.error(
            error.message || $t('form-manager.dataSource.schemaCreateFailed'),
          );
        }
      })
      .catch(() => {});
  }
  closeContextMenu();
}

// 右键菜单 - 编辑Schema（重命名）
function handleEditSchema() {
  if (contextMenuNode.value) {
    const { meta, label } = contextMenuNode.value;
    const dbType = meta?.dbType?.toLowerCase();

    ElMessageBox.prompt(
      $t('form-manager.dataSource.inputNewSchemaName'),
      $t('form-manager.dataSource.editSchema'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        inputValue: label,
        inputPattern: /^[a-z_]\w*$/i,
        inputErrorMessage: $t('form-manager.dataSource.schemaNameRule'),
      },
    )
      .then(async ({ value: newName }) => {
        if (newName === label) {
          ElMessage.info($t('form-manager.dataSource.nameNotChanged'));
          return;
        }
        try {
          let sql = '';
          if (dbType === 'postgresql') {
            sql = `ALTER SCHEMA "${label}" RENAME TO "${newName}";`;
          } else if (dbType === 'sqlserver') {
            // SQL Server 不支持直接重命名 Schema
            ElMessage.warning(
              $t('form-manager.dataSource.sqlServerRenameSchemaNotSupported'),
            );
            return;
          }

          const result = await executeDDLApi(meta?.dbName || '', {
            sql,
            database: meta?.database,
            schema_name: undefined,
          });

          if (result.success) {
            ElMessage.success(
              $t('form-manager.dataSource.schemaRenameSuccess', {
                name: newName,
              }),
            );
            await handleRefreshNode();
          } else {
            ElMessage.error(
              result.message ||
                $t('form-manager.dataSource.schemaRenameFailed'),
            );
          }
        } catch (error: any) {
          console.error('重命名Schema失败:', error);
          ElMessage.error(
            error.message || $t('form-manager.dataSource.schemaRenameFailed'),
          );
        }
      })
      .catch(() => {});
  }
  closeContextMenu();
}

// 右键菜单 - 创建表
function handleCreateTable() {
  if (contextMenuNode.value) {
    const { meta } = contextMenuNode.value;

    createTableData.value = {
      dbName: meta?.dbName || '',
      database: meta?.database || '',
      schema: meta?.schema || '',
      dbType: meta?.dbType || '',
    };

    createTableModalVisible.value = true;
  }
  closeContextMenu();
}

// 创建表成功回调
async function handleCreateTableSuccess() {
  // 刷新当前节点
  if (contextMenuNode.value && treeRef.value) {
    const treeNode = treeRef.value.getNode(contextMenuNode.value.id);
    if (treeNode) {
      treeNode.loaded = false;
      treeNode.childNodes = [];
      if (treeNode.expanded) {
        treeNode.collapse();
        await new Promise((resolve) => setTimeout(resolve, 100));
        treeNode.expand();
      }
    }
  }
}

// 右键菜单 - 设计表
function handleEditTable() {
  if (contextMenuNode.value) {
    const { meta } = contextMenuNode.value;

    tableEditorData.value = {
      dbName: meta?.dbName || '',
      database: meta?.database || '',
      schema: meta?.schema || '',
      tableName: meta?.table || '',
      dbType: meta?.dbType || '',
    };

    tableEditorModalVisible.value = true;
  }
  closeContextMenu();
}

// 刷新已选择表的字段信息
async function refreshSelectedTableFields(tableName: string, meta: any) {
  try {
    const columns = await getTableColumnsApi(
      meta.dbName!,
      tableName,
      meta.database,
      meta.schema,
    );
    const fields = columns.map((col: ColumnInfo) => ({
      name: col.column_name,
      type: normalizeDbType(col.data_type),
      comment: col.description || '',
      nullable: col.is_nullable,
      isPrimaryKey: col.is_primary_key,
      uniqueCheck: col.is_unique,
      maxLength: col.character_maximum_length,
      precision: col.numeric_precision,
      scale: col.numeric_scale,
    }));
    return fields;
  } catch (error) {
    console.error('Failed to refresh table fields:', error);
    return null;
  }
}

// 表设计器保存成功回调
async function handleTableEditorSuccess() {
  // 刷新当前节点的父节点（schema 或 database）
  if (treeRef.value && contextMenuNode.value) {
    const parentNode = treeRef.value.getNode(contextMenuNode.value.id)?.parent;
    if (parentNode && parentNode.data) {
      parentNode.loaded = false;
      parentNode.childNodes = [];
      if (parentNode.expanded) {
        parentNode.collapse();
        await new Promise((resolve) => setTimeout(resolve, 100));
        parentNode.expand();
      }
    }
  }

  // 自动刷新已选择的表的字段信息
  if (contextMenuNode.value?.meta) {
    const editedTableName = contextMenuNode.value.meta.table;
    const meta = contextMenuNode.value.meta;

    // 查找并更新已选择的表
    for (const table of tables.value) {
      if (
        table.tableName === editedTableName &&
        table.meta?.dbName === meta.dbName &&
        table.meta?.database === meta.database &&
        table.meta?.schema === meta.schema
      ) {
        // 刷新字段信息
        const newFields = await refreshSelectedTableFields(
          editedTableName,
          meta,
        );
        if (newFields) {
          table.fields = newFields;
          ElMessage.success(
            $t('form-manager.dataSource.tableFieldsRefreshed', {
              name: editedTableName,
            }),
          );
        }
        break;
      }
    }
  }
}

// 获取右键菜单项
function getContextMenuItems(): ContextMenuItem[] {
  if (!contextMenuNode.value) return [];

  const { type, meta } = contextMenuNode.value;
  const tableName = meta?.table;
  const dbType = meta?.dbType?.toLowerCase();
  const supportsSchema = dbType === 'postgresql' || dbType === 'sqlserver';

  // 数据库节点菜单
  if (type === 'database') {
    const items: ContextMenuItem[] = [];

    // 如果支持Schema，添加创建Schema选项
    if (supportsSchema) {
      items.push({
        label: $t('form-manager.dataSource.addSchema'),
        icon: FilePlus,
        action: handleCreateSchema,
      });
    }
    items.push(
      {
        label: $t('form-manager.dataSource.addTable'),
        icon: FilePlus,
        action: handleCreateTable,
      },
      {
        label: $t('form-manager.dataSource.refreshDatabase'),
        icon: RefreshCw,
        action: handleRefreshNode,
        divided: true,
      },
    );

    return items;
  }

  // Schema节点菜单
  if (type === 'schema') {
    return [
      {
        label: $t('form-manager.dataSource.addTable'),
        icon: FilePlus,
        action: handleCreateTable,
      },
      {
        label: $t('form-manager.dataSource.editSchema'),
        icon: Edit,
        action: handleEditSchema,
        divided: true,
      },
      {
        label: $t('form-manager.dataSource.refreshSchema'),
        icon: RefreshCw,
        action: handleRefreshNode,
      },
      {
        label: $t('form-manager.dataSource.copySchemaName'),
        icon: Copy,
        action: handleCopyName,
      },
    ];
  }

  // 表节点菜单
  if (type === 'table') {
    const items: ContextMenuItem[] = [
      {
        label: $t('form-manager.dataSource.viewFields'),
        icon: Eye,
        action: handleViewFields,
      },
      {
        label: $t('form-manager.dataSource.designTable'),
        icon: Edit,
        action: handleEditTable,
        divided: true,
      },
    ];

    // 如果没有主表，显示"设为主表"
    if (!mainTable.value) {
      items.push({
        label: $t('form-manager.dataSource.setMainTable'),
        icon: Plus,
        action: handleSetMainTable,
      });
    } else if (!isTableAdded(tableName || '')) {
      // 如果有主表但该表未添加，显示"添加为从表"
      items.push({
        label: $t('form-manager.dataSource.addSubTable'),
        icon: Plus,
        action: handleAddSubTable,
      });
    }

    items.push(
      {
        label: $t('form-manager.dataSource.copyTableName'),
        icon: Copy,
        action: handleCopyName,
        divided: true,
      },
      {
        label: $t('form-manager.dataSource.refresh'),
        icon: RefreshCw,
        action: handleRefreshNode,
      },
    );

    return items;
  }

  return [];
}

// 初始化
onMounted(() => {
  // 非工作流模式才加载数据库配置
  if (!props.workflowMode) {
    loadDatabaseConfigs();
  }
});
</script>

<template>
  <div class="flex h-full gap-3">
    <!-- 左侧：数据库树形结构（工作流模式下隐藏） -->
    <div
      v-if="!workflowMode"
      class="border-border bg-card flex h-full w-[300px] flex-col rounded-lg border"
    >
      <div
        class="border-border flex items-center justify-between border-b px-4 py-3"
      >
        <div class="flex items-center gap-2">
          <ElIcon><Database /></ElIcon>
          <span class="font-medium">{{
            $t('form-manager.dataSource.database')
          }}</span>
        </div>
        <ElTooltip :content="$t('form-manager.dataSource.refresh')">
          <ElButton :icon="RefreshCw" link @click="refreshTree" />
        </ElTooltip>
      </div>

      <!-- 树形结构 -->
      <ElScrollbar class="flex-1">
        <div v-if="loading" class="flex h-32 items-center justify-center">
          <span class="text-muted-foreground text-sm">{{
            $t('form-manager.dataSource.loading')
          }}</span>
        </div>
        <ElTree
          v-else
          ref="treeRef"
          :data="treeData"
          :props="treeProps"
          :load="loadNode"
          :default-expanded-keys="defaultExpandedKeys"
          node-key="id"
          lazy
          highlight-current
          class="p-2"
          @node-click="handleNodeClick"
          @node-contextmenu="handleContextMenu"
        >
          <template #default="{ data }">
            <div class="group flex w-full items-center justify-between pr-2">
              <div class="flex items-center gap-2">
                <component
                  :is="getNodeIcon(data.type)"
                  class="h-4 w-4"
                  :class="getNodeIconClass(data.type)"
                />
                <span class="text-sm">{{ data.label }}</span>
              </div>
              <!-- 表节点显示操作按钮 -->
              <div
                v-if="data.type === 'table'"
                class="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100"
              >
                <ElTooltip
                  v-if="!mainTable"
                  :content="$t('form-manager.dataSource.setMainTable')"
                >
                  <ElButton
                    link
                    size="small"
                    type="primary"
                    @click.stop="addMainTable(data)"
                  >
                    {{ $t('form-manager.dataSource.mainTable') }}
                  </ElButton>
                </ElTooltip>
                <ElTooltip
                  v-else-if="!isTableAdded(data.meta?.table)"
                  :content="$t('form-manager.dataSource.addSubTable')"
                >
                  <ElButton link size="small" @click.stop="addSubTable(data)">
                    <Plus class="h-4 w-4" />
                  </ElButton>
                </ElTooltip>
                <ElTag
                  v-if="isTableAdded(data.meta?.table)"
                  size="small"
                  type="success"
                >
                  {{ $t('form-manager.dataSource.added') }}
                </ElTag>
              </div>
            </div>
          </template>
        </ElTree>
      </ElScrollbar>

      <!-- 字段预览 -->
      <div v-if="selectedTableNode" class="border-border border-t">
        <div class="bg-muted/50 flex items-center justify-between px-4 py-2">
          <span class="text-muted-foreground text-xs font-medium">
            {{ selectedTableNode.label }}
            {{ $t('form-manager.dataSource.fieldPreview') }}
          </span>
        </div>
        <ElScrollbar height="180px">
          <div
            v-if="previewLoading"
            class="flex h-20 items-center justify-center"
          >
            <span class="text-muted-foreground text-xs">{{
              $t('form-manager.dataSource.loading')
            }}</span>
          </div>
          <div v-else class="p-2">
            <div
              v-for="field in previewFields"
              :key="field.name"
              class="border-border/50 flex items-center justify-between border-b px-2 py-1.5 text-xs last:border-b-0"
            >
              <div class="flex items-center gap-2">
                <span
                  class="font-mono font-medium"
                  :class="{ 'text-primary': field.isPrimaryKey }"
                >
                  {{ field.name }}
                </span>
                <ElTag v-if="field.isPrimaryKey" size="small" type="warning">
                  PK
                </ElTag>
              </div>
              <span class="text-muted-foreground">{{ field.type }}</span>
            </div>
            <div
              v-if="previewFields.length === 0"
              class="text-muted-foreground py-4 text-center text-xs"
            >
              {{ $t('form-manager.dataSource.noFields') }}
            </div>
          </div>
        </ElScrollbar>
      </div>
    </div>

    <!-- 右侧：已配置的表 -->
    <div class="border-border bg-card flex flex-1 flex-col rounded-lg border">
      <div class="border-border flex items-center gap-2 border-b px-4 py-3">
        <ElIcon><Link2 /></ElIcon>
        <span class="font-medium">{{
          $t('form-manager.dataSource.relationConfig')
        }}</span>
      </div>

      <ElScrollbar class="flex-1">
        <div class="p-4">
          <!-- 提示信息 -->
          <ElAlert
            v-if="!mainTable"
            :title="$t('form-manager.dataSource.selectMainTip')"
            :description="$t('form-manager.dataSource.selectMainDesc')"
            type="info"
            :closable="false"
            show-icon
            class="mb-4"
          />

          <!-- 主表配置 -->
          <div v-if="mainTable" class="mb-6">
            <div class="mb-3 flex items-center gap-2">
              <ElTag type="primary" effect="dark" size="small">
                {{ $t('form-manager.dataSource.mainTable') }}
              </ElTag>
              <span class="text-sm font-medium">{{ mainTable.tableName }}</span>
              <span
                v-if="mainTable.meta?.dbName || mainTable.meta?.database"
                class="text-muted-foreground text-xs"
              >
                ({{ mainTable.meta.dbName || mainTable.meta.database
                }}{{
                  mainTable.meta.schema ? `.${mainTable.meta.schema}` : ''
                }})
              </span>
            </div>

            <div class="border-primary/30 bg-primary/5 rounded-lg border p-4">
              <div class="mb-4 grid grid-cols-3 gap-4">
                <!-- Schema名（工作流模式） -->
                <div v-if="workflowMode">
                  <label class="text-muted-foreground mb-1.5 block text-xs">{{
                    $t('form-manager.dataSource.schemaName')
                  }}</label>
                  <ElInput
                    v-model="mainTable.meta!.schema"
                    size="small"
                    :placeholder="
                      $t('form-manager.dataSource.schemaNamePlaceholder')
                    "
                  />
                </div>
                <div>
                  <label class="text-muted-foreground mb-1.5 block text-xs">{{
                    $t('form-manager.dataSource.tableName')
                  }}</label>
                  <ElInput
                    v-model="mainTable.tableName"
                    size="small"
                    :disabled="!workflowMode"
                    :placeholder="
                      workflowMode
                        ? $t('form-manager.dataSource.tableNamePlaceholder')
                        : ''
                    "
                  />
                </div>
                <div>
                  <label class="text-muted-foreground mb-1.5 block text-xs">{{
                    $t('form-manager.dataSource.alias')
                  }}</label>
                  <ElInput
                    v-model="mainTable.alias"
                    size="small"
                    :placeholder="
                      $t('form-manager.dataSource.aliasPlaceholder')
                    "
                  />
                </div>
              </div>

              <!-- 主表字段列表 -->
              <div>
                <div class="mb-2 flex items-center justify-between">
                  <span class="text-muted-foreground text-xs font-medium">
                    {{
                      $t('form-manager.dataSource.fieldList', {
                        count: filteredMainTableFields.length,
                      })
                    }}
                  </span>
                  <ElButton
                    v-if="workflowMode"
                    type="primary"
                    link
                    size="small"
                    :icon="Plus"
                    @click="addField(mainTable)"
                  >
                    {{ $t('form-manager.dataSource.addField') }}
                  </ElButton>
                </div>
                <div
                  class="border-border bg-background max-h-[300px] overflow-auto rounded border"
                >
                  <table class="w-full text-xs">
                    <thead class="bg-muted/50 sticky top-0">
                      <tr>
                        <th class="px-2 py-2 text-left font-medium">
                          {{ $t('form-manager.dataSource.fieldName') }}
                        </th>
                        <th class="px-2 py-2 text-left font-medium">
                          {{ $t('form-manager.dataSource.fieldType') }}
                        </th>
                        <th
                          v-if="workflowMode"
                          class="w-16 px-2 py-2 text-left font-medium"
                        >
                          {{ $t('form-manager.dataSource.fieldLength') }}
                        </th>
                        <th
                          v-if="workflowMode"
                          class="w-16 px-2 py-2 text-left font-medium"
                        >
                          {{ $t('form-manager.dataSource.fieldScale') }}
                        </th>
                        <th class="px-2 py-2 text-left font-medium">
                          {{ $t('form-manager.dataSource.fieldComment') }}
                        </th>
                        <th class="w-14 px-2 py-2 text-center font-medium">
                          {{ $t('form-manager.dataSource.nullable') }}
                        </th>
                        <th class="w-14 px-2 py-2 text-center font-medium">
                          {{ $t('form-manager.dataSource.isPrimaryKey') }}
                        </th>
                        <th class="w-14 px-2 py-2 text-center font-medium">
                          {{ $t('form-manager.dataSource.uniqueCheck') }}
                        </th>
                        <th
                          v-if="workflowMode"
                          class="w-14 px-2 py-2 text-center font-medium"
                        >
                          {{ $t('common.operation') }}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="(field, index) in filteredMainTableFields"
                        :key="index"
                        class="border-border/50 border-t"
                      >
                        <!-- 字段名 -->
                        <td class="px-2 py-1">
                          <ElInput
                            v-if="workflowMode"
                            v-model="field.name"
                            size="small"
                            class="font-mono"
                            :placeholder="
                              $t('form-manager.dataSource.fieldNamePlaceholder')
                            "
                          />
                          <span v-else class="font-mono">{{ field.name }}</span>
                        </td>
                        <!-- 字段类型 -->
                        <td class="px-2 py-1">
                          <ElSelect
                            v-if="workflowMode"
                            v-model="field.type"
                            size="small"
                            class="w-full"
                            filterable
                            allow-create
                          >
                            <ElOption
                              v-for="t in fieldTypes"
                              :key="t.value"
                              :label="`${t.label} - ${t.desc}`"
                              :value="t.value"
                            />
                          </ElSelect>
                          <span v-else class="text-muted-foreground">{{
                            field.type
                          }}</span>
                        </td>
                        <!-- 长度（工作流模式，根据类型显示） -->
                        <td v-if="workflowMode" class="px-2 py-1">
                          <ElInputNumber
                            v-if="typeHasLength(field.type)"
                            v-model="field.maxLength"
                            size="small"
                            :min="0"
                            :max="65535"
                            controls-position="right"
                            class="w-full"
                          />
                          <span v-else class="text-muted-foreground">-</span>
                        </td>
                        <!-- 小数位（工作流模式，根据类型显示） -->
                        <td v-if="workflowMode" class="px-2 py-1">
                          <ElInputNumber
                            v-if="typeHasPrecision(field.type)"
                            v-model="field.scale"
                            size="small"
                            :min="0"
                            :max="30"
                            controls-position="right"
                            class="w-full"
                          />
                          <span v-else class="text-muted-foreground">-</span>
                        </td>
                        <!-- 注释 -->
                        <td class="px-2 py-1">
                          <ElInput
                            v-if="workflowMode"
                            v-model="field.comment"
                            size="small"
                            :placeholder="
                              $t(
                                'form-manager.dataSource.fieldCommentPlaceholder',
                              )
                            "
                          />
                          <span v-else>{{ field.comment }}</span>
                        </td>
                        <!-- 是否可空 -->
                        <td class="px-2 py-1 text-center">
                          <ElCheckbox
                            v-if="workflowMode"
                            v-model="field.nullable"
                          />
                          <ElTag
                            v-else-if="field.nullable"
                            size="small"
                            type="info"
                          >
                            NULL
                          </ElTag>
                        </td>
                        <!-- 主键 -->
                        <td class="px-2 py-1 text-center">
                          <ElCheckbox
                            v-if="workflowMode"
                            v-model="field.isPrimaryKey"
                          />
                          <ElTag
                            v-else-if="field.isPrimaryKey"
                            size="small"
                            type="warning"
                          >
                            PK
                          </ElTag>
                        </td>
                        <!-- 唯一性检查 -->
                        <td class="px-2 py-1 text-center">
                          <ElTag
                            v-if="field.uniqueCheck"
                            size="small"
                            type="success"
                          >
                            UQ
                          </ElTag>
                        </td>
                        <!-- 操作（工作流模式） -->
                        <td v-if="workflowMode" class="px-2 py-1 text-center">
                          <ElButton
                            type="danger"
                            link
                            size="small"
                            :icon="Trash2"
                            @click="removeField(mainTable, index)"
                          />
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div class="mt-3 flex justify-end">
                <ElPopconfirm
                  :title="$t('form-manager.dataSource.removeMainConfirm')"
                  @confirm="removeTable(mainTable.id)"
                >
                  <template #reference>
                    <ElButton type="danger" link size="small" :icon="Trash2">
                      {{ $t('form-manager.dataSource.removeMain') }}
                    </ElButton>
                  </template>
                </ElPopconfirm>
              </div>
            </div>
          </div>

          <!-- 从表配置 -->
          <div v-if="mainTable && subTables.length > 0">
            <div class="mb-3 flex items-center gap-2">
              <ElTag type="success" effect="dark" size="small">
                {{ $t('form-manager.dataSource.subTable') }}
              </ElTag>
              <span class="text-muted-foreground text-sm">{{
                $t('form-manager.dataSource.subTableCount', {
                  count: subTables.length,
                })
              }}</span>
            </div>

            <div class="space-y-4">
              <div
                v-for="subTable in subTables"
                :key="subTable.id"
                class="border-border bg-background rounded-lg border p-4"
              >
                <div class="mb-4 flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="font-medium">{{ subTable.tableName }}</span>
                    <span
                      v-if="subTable.meta?.database"
                      class="text-muted-foreground text-xs"
                    >
                      ({{ subTable.meta.database
                      }}{{
                        subTable.meta.schema ? `.${subTable.meta.schema}` : ''
                      }})
                    </span>
                  </div>
                  <ElPopconfirm
                    :title="$t('form-manager.dataSource.removeSubConfirm')"
                    @confirm="removeTable(subTable.id)"
                  >
                    <template #reference>
                      <ElButton
                        type="danger"
                        link
                        size="small"
                        :icon="Trash2"
                      />
                    </template>
                  </ElPopconfirm>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="text-muted-foreground mb-1.5 block text-xs">{{
                      $t('form-manager.dataSource.alias')
                    }}</label>
                    <ElInput
                      v-model="subTable.alias"
                      size="small"
                      :placeholder="
                        $t('form-manager.dataSource.aliasPlaceholder')
                      "
                    />
                  </div>
                  <div>
                    <label class="text-muted-foreground mb-1.5 block text-xs">{{
                      $t('form-manager.dataSource.relationType')
                    }}</label>
                    <ElSelect
                      v-model="subTable.relationType"
                      size="small"
                      class="w-full"
                    >
                      <ElOption
                        :label="$t('form-manager.dataSource.oneToMany')"
                        value="one-to-many"
                      />
                      <ElOption
                        :label="$t('form-manager.dataSource.oneToOne')"
                        value="one-to-one"
                      />
                    </ElSelect>
                  </div>
                  <div>
                    <label class="text-muted-foreground mb-1.5 block text-xs">{{
                      $t('form-manager.dataSource.foreignKeyField')
                    }}</label>
                    <ElSelect
                      v-model="subTable.foreignKey"
                      size="small"
                      class="w-full"
                      :placeholder="
                        $t('form-manager.dataSource.selectForeignKey')
                      "
                    >
                      <ElOption
                        v-for="field in getFilteredSubTableFields(subTable)"
                        :key="field.name"
                        :label="`${field.name} (${field.comment || field.type})`"
                        :value="field.name"
                      />
                    </ElSelect>
                  </div>
                  <div>
                    <label class="text-muted-foreground mb-1.5 block text-xs">{{
                      $t('form-manager.dataSource.relatedFieldMain')
                    }}</label>
                    <ElSelect
                      v-model="subTable.relatedField"
                      size="small"
                      class="w-full"
                      :placeholder="
                        $t('form-manager.dataSource.selectRelatedField')
                      "
                    >
                      <ElOption
                        v-for="fieldName in mainTableFields"
                        :key="fieldName"
                        :label="fieldName"
                        :value="fieldName"
                      />
                    </ElSelect>
                  </div>
                </div>

                <!-- 从表字段列表（可折叠） -->
                <details class="mt-4">
                  <summary
                    class="text-muted-foreground hover:text-foreground cursor-pointer text-xs"
                  >
                    {{
                      $t('form-manager.dataSource.viewFieldList', {
                        count: getFilteredSubTableFields(subTable).length,
                      })
                    }}
                  </summary>
                  <div
                    class="border-border mt-2 max-h-[150px] overflow-auto rounded border"
                  >
                    <table class="w-full text-xs">
                      <thead class="bg-muted/50 sticky top-0">
                        <tr>
                          <th class="px-3 py-2 text-left font-medium">
                            {{ $t('form-manager.dataSource.fieldName') }}
                          </th>
                          <th class="px-3 py-2 text-left font-medium">
                            {{ $t('form-manager.dataSource.fieldType') }}
                          </th>
                          <th class="px-3 py-2 text-left font-medium">
                            {{ $t('form-manager.dataSource.fieldComment') }}
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="field in getFilteredSubTableFields(subTable)"
                          :key="field.name"
                          class="border-border/50 border-t"
                        >
                          <td class="px-3 py-2 font-mono">{{ field.name }}</td>
                          <td class="text-muted-foreground px-3 py-2">
                            {{ field.type }}
                          </td>
                          <td class="px-3 py-2">{{ field.comment }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </details>
              </div>
            </div>
          </div>

          <!-- 无从表提示 -->
          <div
            v-if="mainTable && subTables.length === 0"
            class="border-border rounded-lg border border-dashed p-8 text-center"
          >
            <div class="text-muted-foreground mb-2">
              <Link2 class="mx-auto h-10 w-10 opacity-50" />
            </div>
            <p class="text-muted-foreground text-sm">
              {{ $t('form-manager.dataSource.noSubTables') }}
            </p>
            <p class="text-muted-foreground/70 text-xs">
              {{ $t('form-manager.dataSource.addSubTip') }}
            </p>
          </div>
        </div>
      </ElScrollbar>
    </div>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <div
        v-if="contextMenuVisible"
        class="border-border bg-card fixed z-[9999] min-w-[160px] rounded-lg border shadow-lg"
        :style="contextMenuStyle"
        @click.stop
      >
        <div class="py-1">
          <template v-for="(item, index) in getContextMenuItems()" :key="index">
            <div v-if="item.divided" class="bg-border my-1 h-px"></div>
            <div
              class="hover:bg-muted flex cursor-pointer items-center gap-2 px-3 py-2 text-sm transition-colors"
              @click="item.action"
            >
              <component :is="item.icon" class="h-4 w-4" />
              <span>{{ item.label }}</span>
            </div>
          </template>
        </div>
      </div>
    </Teleport>

    <!-- 点击遮罩关闭菜单 -->
    <Teleport to="body">
      <div
        v-if="contextMenuVisible"
        class="fixed inset-0 z-[9998]"
        @click="closeContextMenu"
        @contextmenu.prevent="closeContextMenu"
      ></div>
    </Teleport>

    <!-- 创建表Modal -->
    <CreateTableModal
      v-model:visible="createTableModalVisible"
      :db-name="createTableData.dbName"
      :database="createTableData.database"
      :schema="createTableData.schema"
      :db-type="createTableData.dbType"
      @success="handleCreateTableSuccess"
    />

    <!-- 设计表Modal -->
    <TableEditorModal
      v-model:visible="tableEditorModalVisible"
      :db-name="tableEditorData.dbName"
      :database="tableEditorData.database"
      :schema="tableEditorData.schema"
      :table-name="tableEditorData.tableName"
      :db-type="tableEditorData.dbType"
      @success="handleTableEditorSuccess"
    />
  </div>
</template>

<style scoped>
/* 调整树节点高度 */
:deep(.el-tree-node__content) {
  height: 32px;
  line-height: 32px;
  border-radius: 4px;
}

/* 选中节点的背景色 */
:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: var(--el-color-primary-light-9);
}

/* 悬停效果 */
:deep(.el-tree-node__content:hover) {
  background-color: var(--el-fill-color-light);
}
</style>
