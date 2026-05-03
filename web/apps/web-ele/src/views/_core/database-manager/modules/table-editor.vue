<script setup lang="ts">
import type { TreeNode } from '../index.vue';

import { computed, ref, watch } from 'vue';

import { Eye, RotateCw, Save } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElTabPane,
  ElTabs,
} from 'element-plus';

import {
  executeDDLApi,
  getTableStructureApi,
} from '#/api/core/database-manager';
import { mapToDbType, normalizeDbType } from '#/utils/database-types';

import ConstraintEditor from './constraint-editor.vue';
import FieldEditor from './field-editor.vue';
import IndexEditor from './index-editor.vue';

interface Props {
  node: TreeNode;
}

const props = defineProps<Props>();

// 字段定义
interface FieldDefinition {
  name: string;
  type: string;
  length?: number;
  precision?: number;
  scale?: number;
  nullable: boolean;
  default?: string;
  primaryKey: boolean;
  unique: boolean;
  comment?: string;
}

interface IndexDefinition {
  name: string;
  type: string;
  columns: string[];
  unique: boolean;
}

interface ConstraintDefinition {
  name: string;
  type: string;
  definition: string;
  columns?: string[];
  referencedTable?: string;
  referencedColumns?: string[];
}

// 表编辑数据
const loading = ref(false);
const saving = ref(false);
const tableName = ref('');
const tableComment = ref('');
const fields = ref<FieldDefinition[]>([]);
const indexes = ref<IndexDefinition[]>([]);
const constraints = ref<ConstraintDefinition[]>([]);
const originalData = ref<any>(null);

// 是否有修改
const hasChanges = computed(() => {
  if (!originalData.value) return false;
  return (
    tableName.value !== originalData.value.tableName ||
    tableComment.value !== originalData.value.tableComment ||
    JSON.stringify(fields.value) !==
      JSON.stringify(originalData.value.fields) ||
    JSON.stringify(indexes.value) !==
      JSON.stringify(originalData.value.indexes) ||
    JSON.stringify(constraints.value) !==
      JSON.stringify(originalData.value.constraints)
  );
});

// SQL预览
const sqlPreviewVisible = ref(false);
const generatedSQL = ref('');

// 使用统一的 normalizeDbType 函数替代本地实现
const normalizeTypeName = normalizeDbType;

// 加载表结构
async function loadTableStructure() {
  if (!props.node.meta?.dbName || !props.node.meta?.table) {
    return;
  }

  loading.value = true;
  try {
    const data = await getTableStructureApi(
      props.node.meta.dbName,
      props.node.meta.table,
      props.node.meta.database,
      props.node.meta.schema,
    );

    // 转换为编辑格式
    tableName.value = data.table_info.table_name;
    tableComment.value = data.table_info.description || '';

    fields.value = data.columns.map((col) => ({
      name: col.column_name,
      type: normalizeTypeName(col.data_type),
      length: col.character_maximum_length,
      precision: col.numeric_precision,
      scale: col.numeric_scale,
      nullable: col.is_nullable,
      default: col.column_default,
      primaryKey: col.is_primary_key,
      unique: col.is_unique,
      comment: col.description,
    }));

    // 转换索引
    indexes.value = data.indexes.map((idx) => ({
      name: idx.index_name,
      type: idx.index_type?.toLowerCase() || 'btree',
      columns: idx.columns?.split(', ') || [],
      unique: idx.is_unique,
    }));

    // 转换约束
    constraints.value = data.constraints.map((con) => ({
      name: con.constraint_name,
      type: con.constraint_type?.toLowerCase() || 'check',
      definition: con.definition || '',
      columns: con.columns?.split(', ') || [],
    }));

    // 保存原始数据用于比较
    originalData.value = {
      tableName: tableName.value,
      tableComment: tableComment.value,
      fields: JSON.parse(JSON.stringify(fields.value)),
      indexes: JSON.parse(JSON.stringify(indexes.value)),
      constraints: JSON.parse(JSON.stringify(constraints.value)),
    };
  } catch (error) {
    console.error('Failed to load table structure:', error);
    ElMessage.error($t('database-manager.loadTableStructureFailed'));
  } finally {
    loading.value = false;
  }
}

// 重置
function handleReset() {
  if (!originalData.value) return;

  ElMessageBox.confirm(
    $t('database-manager.confirmReset'),
    $t('database-manager.confirmResetTitle'),
    {
      confirmButtonText: $t('database-manager.confirm'),
      cancelButtonText: $t('database-manager.cancel'),
      type: 'warning',
    },
  )
    .then(() => {
      tableName.value = originalData.value.tableName;
      tableComment.value = originalData.value.tableComment;
      fields.value = JSON.parse(JSON.stringify(originalData.value.fields));
      indexes.value = JSON.parse(JSON.stringify(originalData.value.indexes));
      constraints.value = JSON.parse(
        JSON.stringify(originalData.value.constraints),
      );
      ElMessage.success($t('database-manager.resetSuccess'));
    })
    .catch(() => {
      // 取消
    });
}

// 获取数据库类型
function getDbType(): string {
  return props.node.meta?.dbType?.toLowerCase() || 'postgresql';
}

// 引用标识符（根据数据库类型）
function quoteIdentifier(name: string): string {
  const dbType = getDbType();
  if (dbType === 'mysql') {
    return `\`${name}\``;
  } else if (dbType === 'sqlserver') {
    return `[${name}]`;
  }
  // PostgreSQL 使用双引号
  return `"${name}"`;
}

// 生成类型定义
function buildTypeDef(field: FieldDefinition): string {
  const dbType = getDbType();
  // 将通用类型转换为数据库特定类型
  let typeDef = mapToDbType(field.type, dbType);

  const typesWithLength = [
    'varchar',
    'char',
    'nvarchar',
    'nchar',
    'varbinary',
    'binary',
  ];
  // PostgreSQL: double precision 和 real 不支持精度参数
  const typesWithPrecision = ['decimal', 'numeric'];
  // MySQL: float 支持精度参数
  const mysqlTypesWithPrecision = ['float'];

  const lowerType = field.type.toLowerCase();

  if (
    typesWithLength.includes(lowerType) &&
    field.length > 0 &&
    field.length > 0
  ) {
    typeDef += `(${field.length})`;
  } else if (typesWithPrecision.includes(lowerType) && field.precision) {
    typeDef += `(${field.precision}${field.scale ? `,${field.scale}` : ''})`;
  } else if (
    dbType === 'mysql' &&
    mysqlTypesWithPrecision.includes(lowerType) &&
    field.precision
  ) {
    typeDef += `(${field.precision}${field.scale ? `,${field.scale}` : ''})`;
  }

  return typeDef;
}

// 生成SQL
function generateSQL() {
  const sqlStatements: string[] = [];
  const dbType = getDbType();
  const tbl = quoteIdentifier(tableName.value);
  const originalTbl = quoteIdentifier(originalData.value.tableName);

  // 表名修改
  if (tableName.value !== originalData.value.tableName) {
    if (dbType === 'mysql') {
      sqlStatements.push(`RENAME TABLE ${originalTbl} TO ${tbl};`);
    } else if (dbType === 'sqlserver') {
      sqlStatements.push(
        `EXEC sp_rename '${originalData.value.tableName}', '${tableName.value}';`,
      );
    } else {
      // PostgreSQL
      sqlStatements.push(`ALTER TABLE ${originalTbl} RENAME TO ${tbl};`);
    }
  }

  // 表注释修改
  if (tableComment.value !== originalData.value.tableComment) {
    if (dbType === 'mysql') {
      sqlStatements.push(
        `ALTER TABLE ${tbl} COMMENT = '${tableComment.value}';`,
      );
    } else if (dbType === 'sqlserver') {
      // SQL Server 使用扩展属性
      sqlStatements.push(
        `EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'${tableComment.value}', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'${tableName.value}';`,
      );
    } else {
      // PostgreSQL
      sqlStatements.push(`COMMENT ON TABLE ${tbl} IS '${tableComment.value}';`);
    }
  }

  // 字段修改
  const originalFields = originalData.value.fields;
  const currentFields = fields.value;

  // 新增字段
  currentFields.forEach((field: FieldDefinition) => {
    const originalField = originalFields.find(
      (f: FieldDefinition) => f.name === field.name,
    );
    const col = quoteIdentifier(field.name);

    if (originalField) {
      // 检查字段是否有修改
      const typeDef = buildTypeDef(field);
      const originalTypeDef = buildTypeDef(originalField);

      // 类型修改
      if (typeDef !== originalTypeDef) {
        if (dbType === 'mysql') {
          let modifyDef = `${col} ${typeDef}`;
          if (!field.nullable) modifyDef += ' NOT NULL';
          if (field.default) modifyDef += ` DEFAULT ${field.default}`;
          if (field.comment) modifyDef += ` COMMENT '${field.comment}'`;
          sqlStatements.push(`ALTER TABLE ${tbl} MODIFY COLUMN ${modifyDef};`);
        } else if (dbType === 'sqlserver') {
          let alterDef = `${col} ${typeDef}`;
          alterDef += field.nullable ? ' NULL' : ' NOT NULL';
          sqlStatements.push(`ALTER TABLE ${tbl} ALTER COLUMN ${alterDef};`);
        } else {
          // PostgreSQL - 添加USING子句以支持类型转换
          sqlStatements.push(
            `ALTER TABLE ${tbl} ALTER COLUMN ${col} TYPE ${typeDef} USING ${col}::${typeDef};`,
          );
        }
      }

      // 可空性修改（仅当类型未修改时单独处理）
      if (
        typeDef === originalTypeDef &&
        field.nullable !== originalField.nullable
      ) {
        if (dbType === 'mysql') {
          let modifyDef = `${col} ${typeDef}`;
          if (!field.nullable) modifyDef += ' NOT NULL';
          if (field.default) modifyDef += ` DEFAULT ${field.default}`;
          if (field.comment) modifyDef += ` COMMENT '${field.comment}'`;
          sqlStatements.push(`ALTER TABLE ${tbl} MODIFY COLUMN ${modifyDef};`);
        } else if (dbType === 'sqlserver') {
          let alterDef = `${col} ${typeDef}`;
          alterDef += field.nullable ? ' NULL' : ' NOT NULL';
          sqlStatements.push(`ALTER TABLE ${tbl} ALTER COLUMN ${alterDef};`);
        } else {
          // PostgreSQL
          if (field.nullable) {
            sqlStatements.push(
              `ALTER TABLE ${tbl} ALTER COLUMN ${col} DROP NOT NULL;`,
            );
          } else {
            sqlStatements.push(
              `ALTER TABLE ${tbl} ALTER COLUMN ${col} SET NOT NULL;`,
            );
          }
        }
      }

      // 默认值修改
      if (field.default !== originalField.default) {
        if (dbType === 'mysql') {
          if (field.default) {
            sqlStatements.push(
              `ALTER TABLE ${tbl} ALTER COLUMN ${col} SET DEFAULT ${field.default};`,
            );
          } else {
            sqlStatements.push(
              `ALTER TABLE ${tbl} ALTER COLUMN ${col} DROP DEFAULT;`,
            );
          }
        } else if (dbType === 'sqlserver') {
          // SQL Server 需要先删除旧约束再添加新约束（简化处理）
          if (field.default) {
            sqlStatements.push(
              `ALTER TABLE ${tbl} ADD DEFAULT ${field.default} FOR ${col};`,
            );
          }
        } else {
          // PostgreSQL
          if (field.default) {
            sqlStatements.push(
              `ALTER TABLE ${tbl} ALTER COLUMN ${col} SET DEFAULT ${field.default};`,
            );
          } else {
            sqlStatements.push(
              `ALTER TABLE ${tbl} ALTER COLUMN ${col} DROP DEFAULT;`,
            );
          }
        }
      }

      // 注释修改
      if (field.comment !== originalField.comment) {
        if (dbType === 'mysql') {
          // MySQL 需要 MODIFY COLUMN 来修改注释
          let modifyDef = `${col} ${typeDef}`;
          if (!field.nullable) modifyDef += ' NOT NULL';
          if (field.default) modifyDef += ` DEFAULT ${field.default}`;
          modifyDef += ` COMMENT '${field.comment || ''}'`;
          sqlStatements.push(`ALTER TABLE ${tbl} MODIFY COLUMN ${modifyDef};`);
        } else if (dbType === 'sqlserver') {
          // SQL Server 使用扩展属性
          sqlStatements.push(
            `EXEC sp_updateextendedproperty @name=N'MS_Description', @value=N'${field.comment || ''}', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'${tableName.value}', @level2type=N'COLUMN', @level2name=N'${field.name}';`,
          );
        } else {
          // PostgreSQL
          sqlStatements.push(
            `COMMENT ON COLUMN ${tbl}.${col} IS '${field.comment || ''}';`,
          );
        }
      }
    } else {
      // 新增字段
      const typeDef = buildTypeDef(field);
      let fieldDef = `${col} ${typeDef}`;
      if (!field.nullable) fieldDef += ' NOT NULL';
      if (field.default) fieldDef += ` DEFAULT ${field.default}`;

      if (dbType === 'mysql') {
        // MySQL 支持在 ADD COLUMN 中直接添加注释
        if (field.comment) fieldDef += ` COMMENT '${field.comment}'`;
        sqlStatements.push(`ALTER TABLE ${tbl} ADD COLUMN ${fieldDef};`);
      } else if (dbType === 'sqlserver') {
        // SQL Server
        sqlStatements.push(`ALTER TABLE ${tbl} ADD ${fieldDef};`);
        // SQL Server 使用扩展属性添加注释
        if (field.comment) {
          sqlStatements.push(
            `EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'${field.comment}', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'${tableName.value}', @level2type=N'COLUMN', @level2name=N'${field.name}';`,
          );
        }
      } else {
        // PostgreSQL
        sqlStatements.push(`ALTER TABLE ${tbl} ADD COLUMN ${fieldDef};`);
        if (field.comment) {
          sqlStatements.push(
            `COMMENT ON COLUMN ${tbl}.${col} IS '${field.comment}';`,
          );
        }
      }
    }
  });

  // 删除字段
  originalFields.forEach((field: FieldDefinition) => {
    const exists = currentFields.find((f) => f.name === field.name);
    if (!exists) {
      const col = quoteIdentifier(field.name);
      sqlStatements.push(`ALTER TABLE ${tbl} DROP COLUMN ${col};`);
    }
  });

  return sqlStatements.join('\n\n');
}

// 预览SQL
function handlePreviewSQL() {
  generatedSQL.value = generateSQL();
  if (!generatedSQL.value) {
    ElMessage.info($t('database-manager.noChangesDetected'));
    return;
  }
  sqlPreviewVisible.value = true;
}

// 保存更改
async function handleSave() {
  if (!hasChanges.value) {
    ElMessage.info($t('database-manager.noChangesDetected'));
    return;
  }

  try {
    await ElMessageBox.confirm(
      $t('database-manager.confirmSave'),
      $t('database-manager.confirmSaveTitle'),
      {
        confirmButtonText: $t('database-manager.confirm'),
        cancelButtonText: $t('database-manager.cancel'),
        type: 'warning',
      },
    );

    saving.value = true;

    // 生成SQL
    const sql = generateSQL();
    if (!sql) {
      ElMessage.warning($t('database-manager.noSQLGenerated'));
      return;
    }

    // 检查必要的meta信息
    if (!props.node.meta?.dbName) {
      ElMessage.error($t('database-manager.missingDatabaseConfig'));
      return;
    }

    // 执行DDL
    const result = await executeDDLApi(props.node.meta.dbName, {
      sql,
      database: props.node.meta.database,
      schema_name: props.node.meta.schema,
    });

    if (result.success) {
      ElMessage.success($t('database-manager.saveSuccess'));
      // 重新加载表结构
      await loadTableStructure();
    } else {
      ElMessage.error(result.message || $t('database-manager.saveFailed'));
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('保存失败:', error);
      ElMessage.error(error.message || $t('database-manager.saveFailed'));
    }
  } finally {
    saving.value = false;
  }
}

// 监听节点变化
watch(
  () => props.node,
  () => {
    loadTableStructure();
  },
  { immediate: true },
);
</script>

<template>
  <div class="flex h-full flex-col gap-3">
    <!-- 基本信息 -->
    <ElCard shadow="never" v-loading="loading">
      <template #header>
        <div class="font-semibold">{{ $t('database-manager.basicInfo') }}</div>
      </template>
      <ElForm label-width="80px">
        <ElFormItem :label="$t('database-manager.tableNameLabel')">
          <ElInput
            v-model="tableName"
            :placeholder="$t('database-manager.tableNamePlaceholder')"
            :disabled="loading"
          />
        </ElFormItem>
        <ElFormItem :label="$t('database-manager.schemaLabel')">
          <ElInput :model-value="node.meta?.schema" disabled />
        </ElFormItem>
        <ElFormItem :label="$t('database-manager.commentLabel')">
          <ElInput
            v-model="tableComment"
            type="textarea"
            :rows="2"
            :placeholder="$t('database-manager.tableCommentPlaceholder')"
            :disabled="loading"
          />
        </ElFormItem>
      </ElForm>
    </ElCard>

    <!-- 字段/索引/约束 -->
    <ElCard
      shadow="never"
      class="flex-1"
      :body-style="{ padding: '12px', height: '100%' }"
      v-loading="loading"
    >
      <ElTabs>
        <ElTabPane :label="$t('database-manager.fieldManagement')">
          <FieldEditor
            v-model:fields="fields"
            :disabled="loading"
            :db-type="node.meta?.dbType"
          />
        </ElTabPane>
        <ElTabPane :label="$t('database-manager.indexManagement')">
          <IndexEditor
            v-model:indexes="indexes"
            :fields="fields"
            :disabled="loading"
          />
        </ElTabPane>
        <ElTabPane :label="$t('database-manager.constraintManagement')">
          <ConstraintEditor
            v-model:constraints="constraints"
            :fields="fields"
            :disabled="loading"
          />
        </ElTabPane>
      </ElTabs>
    </ElCard>

    <!-- 操作按钮 -->
    <div class="flex items-center justify-between">
      <div class="text-sm text-gray-500">
        <span v-if="hasChanges" class="text-orange-500"
          >● {{ $t('database-manager.unsavedChanges') }}</span
        >
        <span v-else class="text-green-500"
          >● {{ $t('database-manager.noChanges') }}</span
        >
      </div>
      <div class="flex gap-2">
        <ElButton @click="handleReset" :disabled="!hasChanges || saving">
          <RotateCw :size="14" />
          <span class="ml-1">{{ $t('database-manager.reset') }}</span>
        </ElButton>
        <ElButton @click="handlePreviewSQL" :disabled="!hasChanges || saving">
          <Eye :size="14" />
          <span class="ml-1">{{ $t('database-manager.previewSQL') }}</span>
        </ElButton>
        <ElButton
          type="primary"
          @click="handleSave"
          :disabled="!hasChanges || saving"
          :loading="saving"
        >
          <Save :size="14" />
          <span class="ml-1">{{ $t('database-manager.saveChanges') }}</span>
        </ElButton>
      </div>
    </div>

    <!-- SQL预览对话框 -->
    <ElDialog
      v-model="sqlPreviewVisible"
      :title="$t('database-manager.sqlPreview')"
      width="800px"
    >
      <div class="sql-preview">
        <pre class="max-h-96 overflow-auto rounded bg-gray-50 p-4 text-sm">{{
          generatedSQL
        }}</pre>
      </div>
      <template #footer>
        <ElButton @click="sqlPreviewVisible = false">
          {{ $t('database-manager.close') }}
        </ElButton>
        <ElButton type="primary" @click="handleSave">
          {{ $t('database-manager.executeSql') }}
        </ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.sql-preview pre {
  font-family:
    Monaco, Menlo, 'Ubuntu Mono', Consolas, source-code-pro, monospace;
  line-height: 1.6;
}
</style>
