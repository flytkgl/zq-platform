<script setup lang="ts">
import type { TreeNode } from '../index.vue';

import { onMounted, ref } from 'vue';

import {
  Copy,
  Database,
  Eye,
  FilePlus,
  FileText,
  Layers,
  Play,
  RefreshCw,
  RotateCw,
  Search,
  Server,
  Table,
  TableProperties,
} from '@vben/icons';
import { $t } from '@vben/locales';

import { ElMessage, ElMessageBox, ElTree } from 'element-plus';

import {
  executeDDLApi,
  getDatabaseConfigsApi,
  getDatabasesApi,
  getSchemasApi,
  getTablesApi,
  getViewsApi,
} from '#/api/core/database-manager';

import CreateTableModal from './create-table-modal.vue';

interface Props {
  selectedNode: null | TreeNode;
  searchKeyword?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  select: [node: TreeNode];
  'switch-tab': [tabName: string];
}>();

// 树数据
const treeData = ref<TreeNode[]>([]);
const treeRef = ref();
const loading = ref(false);

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

// 树配置
const treeProps = {
  label: 'label',
  children: 'children',
  isLeaf: 'isLeaf',
};

// 加载数据库配置（根节点）
async function loadDatabaseConfigs() {
  console.log('[loadDatabaseConfigs] 开始加载数据库配置');
  loading.value = true;
  try {
    const configs = await getDatabaseConfigsApi();
    treeData.value = configs.map((config) => ({
      id: `conn-${config.db_name}`,
      label: config.name,
      type: 'connection' as const,
      isLeaf: false,
      meta: {
        dbName: config.db_name,
        dbType: config.db_type,
      },
    }));
  } catch (error) {
    console.error('Failed to load database configs:', error);
    ElMessage.error($t('database-manager.loadDatabaseConfigsFailed'));
  } finally {
    loading.value = false;
  }
}

// 加载数据库列表
async function loadDatabases(dbName: string) {
  try {
    const databases = await getDatabasesApi(dbName);
    return databases.map((db) => ({
      id: `db-${dbName}-${db.name}`,
      label: db.name,
      type: 'database' as const,
      isLeaf: false,
      meta: {
        dbName,
        dbType: treeData.value.find((n) => n.meta?.dbName === dbName)?.meta
          ?.dbType,
        database: db.name,
      },
    }));
  } catch (error) {
    console.error('Failed to load databases:', error);
    ElMessage.error(
      `${$t('database-manager.loadDatabaseListFailed')}: ${error}`,
    );
    return [];
  }
}

// 加载Schema列表（PostgreSQL/SQL Server）
async function loadSchemas(dbName: string, database: string) {
  try {
    console.log('[loadSchemas] dbName:', dbName, 'database:', database);
    const schemas = await getSchemasApi(dbName, database);
    return schemas.map((schema) => ({
      id: `schema-${dbName}-${database}-${schema.name}`,
      label: schema.name,
      type: 'schema' as const,
      isLeaf: false,
      meta: {
        dbName,
        dbType: treeData.value.find((n) => n.meta?.dbName === dbName)?.meta
          ?.dbType,
        database,
        schema: schema.name,
      },
    }));
  } catch (error) {
    console.error('Failed to load schemas:', error);
    ElMessage.error(`${$t('database-manager.loadSchemaListFailed')}: ${error}`);
    return [];
  }
}

// 创建Tables和Views文件夹节点
function createFolders(dbName: string, database: string, schema?: string) {
  const dbType = treeData.value.find((n) => n.meta?.dbName === dbName)?.meta
    ?.dbType;

  return [
    // Tables文件夹
    {
      id: `tables-folder-${dbName}-${database}-${schema || ''}`,
      label: 'Tables',
      type: 'tables-folder' as const,
      isLeaf: false,
      meta: {
        dbName,
        dbType,
        database,
        schema,
      },
    },
    // Views文件夹
    {
      id: `views-folder-${dbName}-${database}-${schema || ''}`,
      label: 'Views',
      type: 'views-folder' as const,
      isLeaf: false,
      meta: {
        dbName,
        dbType,
        database,
        schema,
      },
    },
  ];
}

// 加载表列表
async function loadTables(dbName: string, database: string, schema?: string) {
  try {
    console.log(
      '[loadTables] dbName:',
      dbName,
      'database:',
      database,
      'schema:',
      schema,
    );
    const tables = await getTablesApi(dbName, database, schema);
    const dbType = treeData.value.find((n) => n.meta?.dbName === dbName)?.meta
      ?.dbType;

    return tables.map((table) => ({
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
    ElMessage.error(`${$t('database-manager.loadTableListFailed')}: ${error}`);
    return [];
  }
}

// 加载视图列表
async function loadViews(dbName: string, database: string, schema?: string) {
  try {
    console.log(
      '[loadViews] dbName:',
      dbName,
      'database:',
      database,
      'schema:',
      schema,
    );
    const views = await getViewsApi(dbName, database, schema);
    const dbType = treeData.value.find((n) => n.meta?.dbName === dbName)?.meta
      ?.dbType;

    return views.map((view) => ({
      id: `view-${dbName}-${database}-${schema || ''}-${view.view_name}`,
      label: view.view_name,
      type: 'view' as const,
      isLeaf: true,
      meta: {
        dbName,
        dbType,
        database,
        schema: schema || view.schema_name,
        view: view.view_name,
      },
    }));
  } catch (error) {
    console.error('Failed to load views:', error);
    ElMessage.error(`${$t('database-manager.loadViewListFailed')}: ${error}`);
    return [];
  }
}

// 懒加载子节点
async function loadNode(node: any, resolve: any) {
  // 根节点：返回已加载的treeData
  if (node.level === 0) {
    resolve(treeData.value);
    return;
  }

  const nodeData = node.data as TreeNode;
  const { type, meta } = nodeData;

  // 检查meta是否存在
  if (!meta) {
    resolve([]);
    return;
  }

  try {
    // 连接节点：加载数据库列表
    if (type === 'connection' && meta.dbName) {
      const nodes = await loadDatabases(meta.dbName);
      resolve(nodes);
      return;
    }

    // 数据库节点：根据数据库类型决定加载Schema还是文件夹
    if (type === 'database' && meta.dbName && meta.database) {
      console.log('[loadNode] database node meta:', meta);
      const dbType = meta.dbType?.toLowerCase();
      if (dbType === 'postgresql' || dbType === 'sqlserver') {
        // PostgreSQL/SQL Server：加载Schema列表
        const nodes = await loadSchemas(meta.dbName, meta.database);
        resolve(nodes);
      } else {
        // MySQL：直接加载Tables和Views文件夹
        const nodes = createFolders(meta.dbName, meta.database);
        resolve(nodes);
      }
      return;
    }

    // Schema节点：加载Tables和Views文件夹
    if (type === 'schema' && meta.dbName && meta.database) {
      const nodes = createFolders(meta.dbName, meta.database, meta.schema);
      resolve(nodes);
      return;
    }

    // Tables文件夹节点：加载表列表
    if (type === 'tables-folder' && meta.dbName && meta.database) {
      console.log('[loadNode] tables-folder meta:', meta);
      const nodes = await loadTables(meta.dbName, meta.database, meta.schema);
      resolve(nodes);
      return;
    }

    // Views文件夹节点：加载视图列表
    if (type === 'views-folder' && meta.dbName && meta.database) {
      console.log('[loadNode] views-folder meta:', meta);
      const nodes = await loadViews(meta.dbName, meta.database, meta.schema);
      resolve(nodes);
      return;
    }

    // 表节点是叶子节点，不应该走到这里
    resolve([]);
  } catch (error) {
    console.error('Failed to load node:', error);
    resolve([]);
  }
}

// 节点点击
function handleNodeClick(data: TreeNode) {
  emit('select', data);
}

// 右键菜单
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

// 关闭右键菜单
function closeContextMenu() {
  contextMenuVisible.value = false;
}

// 刷新节点
async function handleRefreshNode() {
  if (!contextMenuNode.value || !treeRef.value) {
    closeContextMenu();
    return;
  }

  const node = contextMenuNode.value;
  const treeInstance = treeRef.value;

  try {
    // 获取当前节点在ElTree中的Node对象
    const treeNode = treeInstance.getNode(node.id);

    if (!treeNode) {
      ElMessage.warning($t('database-manager.cannotFindNode'));
      closeContextMenu();
      return;
    }

    // 如果节点已展开，先折叠再展开以触发重新加载
    if (treeNode.expanded) {
      // 清除该节点的子节点缓存
      treeNode.loaded = false;
      treeNode.childNodes = [];

      // 折叠节点
      treeNode.collapse();

      // 等待一小段时间后重新展开
      await new Promise((resolve) => setTimeout(resolve, 100));

      // 重新展开，触发懒加载
      treeNode.expand();

      ElMessage.success($t('database-manager.refreshSuccess'));
    } else {
      // 如果节点未展开，清除加载状态即可
      treeNode.loaded = false;
      treeNode.childNodes = [];
      ElMessage.success($t('database-manager.expandNodeToViewLatestData'));
    }
  } catch (error) {
    console.error('刷新节点失败:', error);
    ElMessage.error($t('database-manager.refreshFailed'));
  }

  closeContextMenu();
}

// 查看信息
function handleViewInfo() {
  if (contextMenuNode.value) {
    emit('select', contextMenuNode.value);
  }
  closeContextMenu();
}

// 复制名称
function handleCopyName() {
  if (contextMenuNode.value) {
    navigator.clipboard.writeText(contextMenuNode.value.label);
    ElMessage.success($t('database-manager.copiedToClipboard'));
  }
  closeContextMenu();
}

// 执行SQL
function handleExecuteSQL() {
  if (contextMenuNode.value) {
    emit('select', contextMenuNode.value);
    // 通知父组件切换到SQL执行Tab
    emit('switch-tab', 'sql');
  }
  closeContextMenu();
}

// 导出数据
function handleExport() {
  ElMessage.info('导出功能开发中...');
  closeContextMenu();
}

// 导入数据
function handleImport() {
  ElMessage.info('导入功能开发中...');
  closeContextMenu();
}

// 创建Schema
function handleCreateSchema() {
  if (contextMenuNode.value) {
    const { meta } = contextMenuNode.value;
    const dbType = meta?.dbType?.toLowerCase();

    ElMessageBox.prompt(
      $t('database-manager.enterSchemaName'),
      $t('database-manager.createSchema'),
      {
        confirmButtonText: $t('database-manager.confirm'),
        cancelButtonText: $t('database-manager.cancel'),
        inputPattern: /^[a-z_]\w*$/i,
        inputErrorMessage: $t('database-manager.schemaNamePattern'),
      },
    )
      .then(async ({ value: schemaName }) => {
        try {
          // 生成CREATE SCHEMA SQL
          let sql = '';
          if (dbType === 'postgresql') {
            sql = `CREATE SCHEMA "${schemaName}";`;
          } else if (dbType === 'sqlserver') {
            sql = `CREATE SCHEMA [${schemaName}];`;
          }

          // 执行DDL
          const result = await executeDDLApi(meta?.dbName || '', {
            sql,
            database: meta?.database,
            schema_name: undefined,
          });

          if (result.success) {
            ElMessage.success(
              $t('database-manager.schemaCreatedSuccess', { schemaName }),
            );
            // 刷新数据库节点
            await handleRefreshNode();
          } else {
            ElMessage.error(
              result.message || $t('database-manager.createSchemaFailed'),
            );
          }
        } catch (error: any) {
          console.error('创建Schema失败:', error);
          ElMessage.error(
            error.message || $t('database-manager.createSchemaFailed'),
          );
        }
      })
      .catch(() => {
        // 用户取消
      });
  }
  closeContextMenu();
}

// 创建表
function handleCreateTable() {
  if (contextMenuNode.value) {
    const { meta } = contextMenuNode.value;

    // 设置创建表的上下文信息
    createTableData.value = {
      dbName: meta?.dbName || '',
      database: meta?.database || '',
      schema: meta?.schema || '',
      dbType: meta?.dbType || '',
    };

    // 打开Modal
    createTableModalVisible.value = true;
  }
  closeContextMenu();
}

// 创建表成功回调
async function handleCreateTableSuccess(tableName?: string) {
  // 不显示消息，create-table-modal已经显示了

  // 刷新Tables文件夹节点
  if (contextMenuNode.value && treeRef.value) {
    const { type, meta } = contextMenuNode.value;

    // 找到tables-folder节点
    let tablesFolderNode = null;

    if (type === 'tables-folder') {
      tablesFolderNode = treeRef.value.getNode(contextMenuNode.value.id);
    } else if (type === 'schema' || type === 'database') {
      // 需要找到该schema/database下的tables-folder
      const parentNode = treeRef.value.getNode(contextMenuNode.value.id);
      if (parentNode && parentNode.childNodes) {
        tablesFolderNode = parentNode.childNodes.find(
          (child: any) => child.data?.type === 'tables-folder',
        );
      }
    }

    // 刷新tables-folder节点
    if (tablesFolderNode) {
      tablesFolderNode.loaded = false;
      tablesFolderNode.childNodes = [];

      // 如果节点已展开，重新加载
      if (tablesFolderNode.expanded) {
        tablesFolderNode.collapse();
        await new Promise((resolve) => setTimeout(resolve, 100));
        await tablesFolderNode.expand();

        // 等待节点加载完成后，选中新创建的表
        if (tableName) {
          await new Promise((resolve) => setTimeout(resolve, 200));

          // 查找新创建的表节点
          const tableNode = tablesFolderNode.childNodes?.find(
            (child: any) =>
              child.data?.label === tableName || child.data?.name === tableName,
          );

          if (tableNode) {
            // 选中该节点
            treeRef.value.setCurrentKey(tableNode.data.id);
            // 触发选择事件
            handleNodeClick(tableNode.data);
          }
        }
      } else {
        // 如果未展开，先展开
        await tablesFolderNode.expand();

        // 等待加载后选中
        if (tableName) {
          await new Promise((resolve) => setTimeout(resolve, 200));
          const tableNode = tablesFolderNode.childNodes?.find(
            (child: any) =>
              child.data?.label === tableName || child.data?.name === tableName,
          );

          if (tableNode) {
            treeRef.value.setCurrentKey(tableNode.data.id);
            handleNodeClick(tableNode.data);
          }
        }
      }
    }
  }
}

// 编辑
function handleEdit() {
  ElMessage.info('编辑功能开发中...');
  closeContextMenu();
}

// 删除
function handleDelete() {
  ElMessage.info('删除功能开发中...');
  closeContextMenu();
}

// 查询数据
function handleQueryData() {
  if (contextMenuNode.value) {
    emit('select', contextMenuNode.value);
    // 通知父组件切换到数据Tab
    emit('switch-tab', 'data');
  }
  closeContextMenu();
}

// 生成DDL
function handleGenerateDDL() {
  if (contextMenuNode.value) {
    const { meta } = contextMenuNode.value;
    if (meta?.dbName && meta?.table) {
      // 通知父组件显示DDL
      emit('generate-ddl', {
        dbName: meta.dbName,
        database: meta.database,
        schema: meta.schema,
        table: meta.table,
      });
    }
  }
  closeContextMenu();
}

// 清空表数据
function handleTruncateTable() {
  if (contextMenuNode.value) {
    ElMessageBox.confirm(
      `确定要清空表 "${contextMenuNode.value.label}" 的所有数据吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
      .then(() => {
        ElMessage.info('清空表功能开发中...');
      })
      .catch(() => {
        // 用户取消
      });
  }
  closeContextMenu();
}

// 查看视图定义
function handleViewDefinition() {
  if (contextMenuNode.value) {
    emit('select', contextMenuNode.value);
    // 通知父组件切换到视图定义Tab
    emit('switch-tab', 'definition');
  }
  closeContextMenu();
}

// 刷新物化视图（仅物化视图）
function handleRefreshMaterializedView() {
  if (contextMenuNode.value) {
    const { meta } = contextMenuNode.value;
    // 检查是否是物化视图
    if (meta?.view) {
      ElMessageBox.confirm(
        `确定要刷新物化视图 "${contextMenuNode.value.label}" 吗？`,
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info',
        },
      )
        .then(() => {
          ElMessage.info('刷新物化视图功能开发中...');
        })
        .catch(() => {
          // 用户取消
        });
    } else {
      ElMessage.warning('只有物化视图才需要手动刷新');
    }
  }
  closeContextMenu();
}

// 创建新视图
function handleCreateView() {
  ElMessage.info('创建视图功能开发中...');
  closeContextMenu();
}

// 导出所有表
function handleExportAllTables() {
  if (contextMenuNode.value) {
    ElMessageBox.confirm(
      '确定要导出当前Schema/Database下的所有表吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      },
    )
      .then(() => {
        ElMessage.info('导出所有表功能开发中...');
      })
      .catch(() => {
        // 用户取消
      });
  }
  closeContextMenu();
}

// 导出所有视图
function handleExportAllViews() {
  if (contextMenuNode.value) {
    ElMessageBox.confirm(
      '确定要导出当前Schema/Database下的所有视图吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      },
    )
      .then(() => {
        ElMessage.info('导出所有视图功能开发中...');
      })
      .catch(() => {
        // 用户取消
      });
  }
  closeContextMenu();
}

// 查看表统计
function handleViewTableStats() {
  if (contextMenuNode.value) {
    emit('select', contextMenuNode.value);
    // 通知父组件切换到统计Tab
    emit('switch-tab', 'stats');
  }
  closeContextMenu();
}

// 刷新所有物化视图
function handleRefreshAllMaterializedViews() {
  if (contextMenuNode.value) {
    ElMessageBox.confirm(
      '确定要刷新当前Schema/Database下的所有物化视图吗？这可能需要一些时间。',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
      .then(() => {
        ElMessage.info('刷新所有物化视图功能开发中...');
      })
      .catch(() => {
        // 用户取消
      });
  }
  closeContextMenu();
}

// 获取右键菜单项
function getContextMenuItems() {
  if (!contextMenuNode.value) return [];

  const { type } = contextMenuNode.value;

  // 连接节点菜单
  if (type === 'connection') {
    return [
      {
        label: $t('database-manager.refreshConnection'),
        icon: RefreshCw,
        action: handleRefreshNode,
      },
      {
        label: $t('database-manager.viewInfo'),
        icon: Eye,
        action: handleViewInfo,
      },
      {
        label: $t('database-manager.copyConnectionName'),
        icon: Copy,
        action: handleCopyName,
        divided: true,
      },
    ];
  }

  // 数据库节点菜单
  if (type === 'database') {
    const { meta } = contextMenuNode.value;
    const dbType = meta?.dbType?.toLowerCase();

    // 检查数据库是否支持Schema（PostgreSQL和SQL Server）
    const supportsSchema = dbType === 'postgresql' || dbType === 'sqlserver';

    const menuItems = [
      {
        label: $t('database-manager.refreshDatabase'),
        icon: RefreshCw,
        action: handleRefreshNode,
      },
      {
        label: $t('database-manager.viewInfo'),
        icon: Eye,
        action: handleViewInfo,
      },
    ];

    // 如果支持Schema，添加"创建Schema"选项
    if (supportsSchema) {
      menuItems.push({
        label: $t('database-manager.createSchema'),
        icon: FilePlus,
        action: handleCreateSchema,
        divided: true,
      });
    }

    menuItems.push(
      {
        label: $t('database-manager.createNewTable'),
        icon: FilePlus,
        action: handleCreateTable,
        divided: !supportsSchema,
      },
      {
        label: $t('database-manager.executeSql'),
        icon: Play,
        action: handleExecuteSQL,
      },
      // { label: '导出数据库', icon: Download, action: handleExport, divided: true },
      // { label: '导入数据', icon: Upload, action: handleImport },
      {
        label: $t('database-manager.copyDatabaseName'),
        icon: Copy,
        action: handleCopyName,
        divided: true,
      },
    );

    return menuItems;
  }

  // Schema节点菜单
  if (type === 'schema') {
    return [
      {
        label: $t('database-manager.refreshSchema'),
        icon: RefreshCw,
        action: handleRefreshNode,
      },
      {
        label: $t('database-manager.viewInfo'),
        icon: Eye,
        action: handleViewInfo,
      },
      {
        label: $t('database-manager.createNewTable'),
        icon: FilePlus,
        action: handleCreateTable,
        divided: true,
      },
      // { label: '导出Schema', icon: Download, action: handleExport },
      {
        label: $t('database-manager.copySchemaName'),
        icon: Copy,
        action: handleCopyName,
        divided: true,
      },
    ];
  }

  // Tables文件夹菜单
  if (type === 'tables-folder') {
    return [
      {
        label: $t('database-manager.refreshTableList'),
        icon: RefreshCw,
        action: handleRefreshNode,
      },
      {
        label: $t('database-manager.createNewTable'),
        icon: FilePlus,
        action: handleCreateTable,
        divided: true,
      },
      // { label: '导出所有表', icon: Download, action: handleExportAllTables },
      {
        label: $t('database-manager.viewStatistics'),
        icon: Eye,
        action: handleViewTableStats,
        divided: true,
      },
    ];
  }

  // Views文件夹菜单
  if (type === 'views-folder') {
    return [
      {
        label: $t('database-manager.refreshViewList'),
        icon: RefreshCw,
        action: handleRefreshNode,
      },
      {
        label: $t('database-manager.createNewView'),
        icon: FilePlus,
        action: handleCreateView,
        divided: true,
      },
      // { label: '导出所有视图', icon: Download, action: handleExportAllViews },
      {
        label: $t('database-manager.refreshAllMaterializedViews'),
        icon: RotateCw,
        action: handleRefreshAllMaterializedViews,
        divided: true,
      },
    ];
  }

  // 表节点菜单
  if (type === 'table') {
    return [
      {
        label: $t('database-manager.viewTableStructure'),
        icon: Eye,
        action: handleViewInfo,
      },
      {
        label: $t('database-manager.queryData'),
        icon: Search,
        action: handleQueryData,
        divided: true,
      },
      // { label: '生成DDL', icon: FileText, action: handleGenerateDDL },
      {
        label: $t('database-manager.executeSql'),
        icon: Play,
        action: handleExecuteSQL,
        divided: true,
      },
      // { label: '导出表数据', icon: Download, action: handleExport },
      // { label: '导入数据', icon: Upload, action: handleImport },
      // { label: '清空表数据', icon: Trash, action: handleTruncateTable, danger: true, divided: true },
      {
        label: $t('database-manager.copyTableName'),
        icon: Copy,
        action: handleCopyName,
        divided: true,
      },
      {
        label: $t('database-manager.refresh'),
        icon: RefreshCw,
        action: handleRefreshNode,
      },
    ];
  }

  // 视图节点菜单
  if (type === 'view') {
    return [
      {
        label: $t('database-manager.viewViewStructure'),
        icon: Eye,
        action: handleViewInfo,
      },
      {
        label: $t('database-manager.queryData'),
        icon: Search,
        action: handleQueryData,
        divided: true,
      },
      {
        label: $t('database-manager.viewDefinitionSQL'),
        icon: FileText,
        action: handleViewDefinition,
      },
      {
        label: $t('database-manager.executeSql'),
        icon: Play,
        action: handleExecuteSQL,
        divided: true,
      },
      // { label: '导出视图数据', icon: Download, action: handleExport },
      {
        label: $t('database-manager.refreshView'),
        icon: RefreshCw,
        action: handleRefreshMaterializedView,
        divided: true,
      },
      {
        label: $t('database-manager.copyViewName'),
        icon: Copy,
        action: handleCopyName,
        divided: true,
      },
    ];
  }

  return [];
}

// 搜索节点
function filterNode(value: string, data: any) {
  if (!value) return true;
  return data.label?.toLowerCase().includes(value.toLowerCase()) || false;
}

// 处理搜索 - 暴露给父组件调用
function handleSearch(keyword: string) {
  if (treeRef.value) {
    treeRef.value.filter(keyword);
  }
}

// 刷新数据 - 暴露给父组件调用
async function handleRefresh() {
  try {
    await loadDatabaseConfigs();
    ElMessage.success('刷新成功');
  } catch {
    ElMessage.error('刷新失败');
  }
}

// 暴露方法给父组件
defineExpose({
  handleSearch,
  handleRefresh,
});

// 获取节点图标
function getNodeIcon(type: string) {
  const iconMap: Record<string, any> = {
    connection: Server,
    database: Database,
    schema: Layers,
    'tables-folder': TableProperties,
    'views-folder': Eye,
    table: Table,
    view: Eye,
  };
  return iconMap[type] || Database;
}

// 获取节点图标样式
function getNodeIconClass(type: string) {
  const classMap: Record<string, string> = {
    connection: 'text-blue-500',
    database: 'text-green-500',
    schema: 'text-purple-500',
    'tables-folder': 'text-orange-500',
    'views-folder': 'text-cyan-500',
    table: 'text-gray-600',
    view: 'text-gray-600',
  };
  return classMap[type] || 'text-gray-500';
}

// 页面加载时初始化根节点
onMounted(() => {
  loadDatabaseConfigs();
});
</script>

<template>
  <div class="h-full">
    <!-- 树形结构 -->
    <div class="h-full">
      <div v-if="loading" class="flex h-64 items-center justify-center">
        <span class="text-gray-400">{{ $t('database-manager.loading') }}</span>
      </div>

      <ElTree
        v-else
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        :load="loadNode"
        :filter-node-method="filterNode"
        node-key="id"
        lazy
        highlight-current
        @node-click="handleNodeClick"
        @node-contextmenu="handleContextMenu"
      >
        <template #default="{ node, data }">
          <div class="flex items-center gap-2">
            <!-- 图标 -->
            <component
              :is="getNodeIcon(data.type)"
              :size="16"
              :class="getNodeIconClass(data.type)"
            />
            <!-- 标签 -->
            <span class="text-sm">{{ node.label }}</span>
          </div>
        </template>
      </ElTree>
    </div>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <div
        v-if="contextMenuVisible"
        class="fixed z-[9999] min-w-[160px] rounded-lg border bg-white shadow-lg"
        :style="contextMenuStyle"
        @click.stop
      >
        <div class="py-1">
          <template v-for="(item, index) in getContextMenuItems()" :key="index">
            <div v-if="item.divided" class="my-1 h-px bg-gray-200"></div>
            <div
              class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm transition-colors hover:bg-gray-100"
              :class="{ 'text-red-600 hover:bg-red-50': item.danger }"
              @click="item.action"
            >
              <component :is="item.icon" :size="14" />
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
  </div>
</template>

<style scoped>
/* 调整树节点高度 */
:deep(.el-tree-node__content) {
  height: 34px;
  margin-bottom: 4px;
  line-height: 34px;
  border-radius: 6px;
}

/* 调整展开/收起图标的对齐 */
:deep(.el-tree-node__expand-icon) {
  padding: 6px;
}

/* 选中节点的背景色 - 使用primary色 */
:deep(.el-tree-node.is-current > .el-tree-node__content) {
  color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

/* 悬停效果 */
:deep(.el-tree-node__content:hover) {
  background-color: var(--el-fill-color-light);
}

/* 选中节点悬停时保持primary色 */
:deep(.el-tree-node.is-current > .el-tree-node__content:hover) {
  background-color: var(--el-color-primary-light-8);
}
</style>
