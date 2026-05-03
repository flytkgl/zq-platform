<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import { Eye, RotateCw, Save } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
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
  visible: boolean;
  dbName: string;
  database: string;
  schema?: string;
  tableName: string;
  dbType: string;
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'success'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

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

// 数据权限所需的系统字段
const systemFieldNames = [
  'id',
  'sys_create_datetime',
  'sys_update_datetime',
  'sys_creator_id',
  'sys_modifier_id',
  'sys_dept_id',
];

// 表编辑数据
const loading = ref(false);
const saving = ref(false);
const editTableName = ref('');
const tableComment = ref('');
const fields = ref<FieldDefinition[]>([]);
const indexes = ref<IndexDefinition[]>([]);
const constraints = ref<ConstraintDefinition[]>([]);
const originalData = ref<any>(null);

// 是否有修改
const hasChanges = computed(() => {
  if (!originalData.value) return false;
  return (
    editTableName.value !== originalData.value.tableName ||
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
  if (!props.dbName || !props.tableName) {
    return;
  }

  loading.value = true;
  try {
    const data = await getTableStructureApi(
      props.dbName,
      props.tableName,
      props.database,
      props.schema,
    );

    // 转换为编辑格式
    editTableName.value = data.table_info.table_name;
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
      tableName: editTableName.value,
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
  if (originalData.value) {
    editTableName.value = originalData.value.tableName;
    tableComment.value = originalData.value.tableComment;
    fields.value = JSON.parse(JSON.stringify(originalData.value.fields));
    indexes.value = JSON.parse(JSON.stringify(originalData.value.indexes));
    constraints.value = JSON.parse(
      JSON.stringify(originalData.value.constraints),
    );
  }
}

// 生成ALTER TABLE SQL
function generateSQL(): string {
  if (!originalData.value) return '';

  const sqlStatements: string[] = [];
  const dbType = props.dbType?.toLowerCase();
  const schemaPrefix = props.schema
    ? dbType === 'postgresql'
      ? `"${props.schema}".`
      : `[${props.schema}].`
    : '';
  const quote = dbType === 'mysql' ? '`' : dbType === 'postgresql' ? '"' : '[';
  const endQuote =
    dbType === 'mysql' ? '`' : dbType === 'postgresql' ? '"' : ']';

  // 检查表名是否变化
  if (editTableName.value !== originalData.value.tableName) {
    switch (dbType) {
      case 'mysql': {
        sqlStatements.push(
          `RENAME TABLE ${quote}${originalData.value.tableName}${endQuote} TO ${quote}${editTableName.value}${endQuote};`,
        );

        break;
      }
      case 'postgresql': {
        sqlStatements.push(
          `ALTER TABLE ${schemaPrefix}${quote}${originalData.value.tableName}${endQuote} RENAME TO ${quote}${editTableName.value}${endQuote};`,
        );

        break;
      }
      case 'sqlserver': {
        sqlStatements.push(
          `EXEC sp_rename '${props.schema ? `${props.schema}.` : ''}${originalData.value.tableName}', '${editTableName.value}';`,
        );

        break;
      }
      // No default
    }
  }

  // 检查注释是否变化
  if (tableComment.value !== originalData.value.tableComment) {
    if (dbType === 'postgresql') {
      sqlStatements.push(
        `COMMENT ON TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} IS '${tableComment.value}';`,
      );
    } else if (dbType === 'mysql') {
      sqlStatements.push(
        `ALTER TABLE ${quote}${editTableName.value}${endQuote} COMMENT = '${tableComment.value}';`,
      );
    }
  }

  // 检查字段变化
  const originalFields = originalData.value.fields as FieldDefinition[];
  const currentFields = fields.value;

  // 找出删除的字段
  for (const origField of originalFields) {
    if (!currentFields.find((f) => f.name === origField.name)) {
      sqlStatements.push(
        `ALTER TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} DROP COLUMN ${quote}${origField.name}${endQuote};`,
      );
    }
  }

  // 找出新增的字段
  for (const field of currentFields) {
    if (!originalFields.find((f) => f.name === field.name)) {
      const columnDef = buildColumnDefinition(field, dbType);
      sqlStatements.push(
        `ALTER TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} ADD COLUMN ${columnDef};`,
      );
      // PostgreSQL 新增字段时需要单独添加注释
      if (dbType === 'postgresql' && field.comment) {
        sqlStatements.push(
          `COMMENT ON COLUMN ${schemaPrefix}${quote}${editTableName.value}${endQuote}.${quote}${field.name}${endQuote} IS '${field.comment}';`,
        );
      }
    }
  }

  // 找出修改的字段
  for (const field of currentFields) {
    const origField = originalFields.find((f) => f.name === field.name);
    if (origField && JSON.stringify(field) !== JSON.stringify(origField)) {
      // 字段有修改
      if (dbType === 'postgresql') {
        // PostgreSQL 需要分别修改各个属性
        // 检查类型或长度/精度是否变化
        const typeChanged = field.type !== origField.type;
        const lengthChanged = field.length !== origField.length;
        const precisionChanged =
          field.precision !== origField.precision ||
          field.scale !== origField.scale;

        if (typeChanged || lengthChanged || precisionChanged) {
          // 构建完整的类型定义（包含长度/精度）
          const typesWithLength = [
            'varchar',
            'char',
            'nvarchar',
            'nchar',
            'varbinary',
            'binary',
          ];
          // PostgreSQL: double precision 和 real 不支持精度参数，只有 decimal/numeric 支持
          const typesWithPrecision = ['decimal', 'numeric'];

          // 将通用类型转换为数据库特定类型
          let typeDef = mapToDbType(field.type, dbType);
          const lowerType = field.type.toLowerCase();

          if (
            typesWithLength.includes(lowerType) &&
            field.length > 0 &&
            field.length > 0
          ) {
            typeDef += `(${field.length})`;
          } else if (
            typesWithPrecision.includes(lowerType) &&
            field.precision
          ) {
            typeDef += field.scale
              ? `(${field.precision}, ${field.scale})`
              : `(${field.precision})`;
          }
          sqlStatements.push(
            `ALTER TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} ALTER COLUMN ${quote}${field.name}${endQuote} TYPE ${typeDef} USING ${quote}${field.name}${endQuote}::${typeDef};`,
          );
        }
        if (field.nullable !== origField.nullable) {
          sqlStatements.push(
            `ALTER TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} ALTER COLUMN ${quote}${field.name}${endQuote} ${field.nullable ? 'DROP NOT NULL' : 'SET NOT NULL'};`,
          );
        }
        if (field.default !== origField.default) {
          if (field.default) {
            sqlStatements.push(
              `ALTER TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} ALTER COLUMN ${quote}${field.name}${endQuote} SET DEFAULT ${field.default};`,
            );
          } else {
            sqlStatements.push(
              `ALTER TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} ALTER COLUMN ${quote}${field.name}${endQuote} DROP DEFAULT;`,
            );
          }
        }
        if (field.unique !== origField.unique) {
          if (field.unique) {
            // 添加唯一约束
            sqlStatements.push(
              `ALTER TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} ADD CONSTRAINT ${quote}${editTableName.value}_${field.name}_key${endQuote} UNIQUE (${quote}${field.name}${endQuote});`,
            );
          } else {
            // 删除唯一约束
            sqlStatements.push(
              `ALTER TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} DROP CONSTRAINT IF EXISTS ${quote}${editTableName.value}_${field.name}_key${endQuote};`,
            );
          }
        }
        if (field.primaryKey !== origField.primaryKey) {
          if (field.primaryKey) {
            // 添加主键约束
            sqlStatements.push(
              `ALTER TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} ADD PRIMARY KEY (${quote}${field.name}${endQuote});`,
            );
          } else {
            // 删除主键约束
            sqlStatements.push(
              `ALTER TABLE ${schemaPrefix}${quote}${editTableName.value}${endQuote} DROP CONSTRAINT IF EXISTS ${quote}${editTableName.value}_pkey${endQuote};`,
            );
          }
        }
        if (field.comment !== origField.comment) {
          sqlStatements.push(
            `COMMENT ON COLUMN ${schemaPrefix}${quote}${editTableName.value}${endQuote}.${quote}${field.name}${endQuote} IS '${field.comment || ''}';`,
          );
        }
      } else if (dbType === 'mysql') {
        const columnDef = buildColumnDefinition(field, dbType);
        sqlStatements.push(
          `ALTER TABLE ${quote}${editTableName.value}${endQuote} MODIFY COLUMN ${columnDef};`,
        );
        
        // MySQL 需要单独处理唯一约束和主键的变化
        if (field.unique !== origField.unique) {
          if (field.unique) {
            sqlStatements.push(
              `ALTER TABLE ${quote}${editTableName.value}${endQuote} ADD UNIQUE INDEX ${quote}${editTableName.value}_${field.name}_key${endQuote} (${quote}${field.name}${endQuote});`,
            );
          } else {
            sqlStatements.push(
              `ALTER TABLE ${quote}${editTableName.value}${endQuote} DROP INDEX IF EXISTS ${quote}${editTableName.value}_${field.name}_key${endQuote};`,
            );
          }
        }
        if (field.primaryKey !== origField.primaryKey) {
          if (field.primaryKey) {
            sqlStatements.push(
              `ALTER TABLE ${quote}${editTableName.value}${endQuote} ADD PRIMARY KEY (${quote}${field.name}${endQuote});`,
            );
          } else {
            sqlStatements.push(
              `ALTER TABLE ${quote}${editTableName.value}${endQuote} DROP PRIMARY KEY;`,
            );
          }
        }
      }
    }
  }

  return sqlStatements.join('\n\n');
}

// 构建字段定义
function buildColumnDefinition(field: FieldDefinition, dbType: string): string {
  const quote = dbType === 'mysql' ? '`' : dbType === 'postgresql' ? '"' : '[';
  const endQuote =
    dbType === 'mysql' ? '`' : dbType === 'postgresql' ? '"' : ']';

  // 将通用类型转换为数据库特定类型
  const dbFieldType = mapToDbType(field.type, dbType);
  let def = `${quote}${field.name}${endQuote} ${dbFieldType}`;

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
    def += `(${field.length})`;
  } else if (typesWithPrecision.includes(lowerType) && field.precision) {
    def += field.scale
      ? `(${field.precision}, ${field.scale})`
      : `(${field.precision})`;
  } else if (
    dbType === 'mysql' &&
    mysqlTypesWithPrecision.includes(lowerType) &&
    field.precision
  ) {
    def += field.scale
      ? `(${field.precision}, ${field.scale})`
      : `(${field.precision})`;
  }

  if (!field.nullable) {
    def += ' NOT NULL';
  }

  if (field.default) {
    def += ` DEFAULT ${field.default}`;
  }

  if (field.comment && dbType === 'mysql') {
    def += ` COMMENT '${field.comment}'`;
  }

  return def;
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

// 保存
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

    // 执行DDL
    const result = await executeDDLApi(props.dbName, {
      sql,
      database: props.database,
      schema_name: props.schema,
    });

    if (result.success) {
      ElMessage.success($t('database-manager.saveSuccess'));
      sqlPreviewVisible.value = false;
      emit('success');
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

// 关闭对话框
function handleClose() {
  if (hasChanges.value) {
    ElMessageBox.confirm(
      $t('database-manager.confirmClose'),
      $t('database-manager.confirmCloseTitle'),
      {
        confirmButtonText: $t('database-manager.confirm'),
        cancelButtonText: $t('database-manager.cancel'),
        type: 'warning',
      },
    )
      .then(() => {
        emit('update:visible', false);
      })
      .catch(() => {});
  } else {
    emit('update:visible', false);
  }
}

// 监听 visible 变化
watch(
  () => props.visible,
  (val) => {
    if (val) {
      loadTableStructure();
    }
  },
);
</script>

<template>
  <ElDialog
    :model-value="visible"
    :title="$t('database-manager.designTable', { tableName })"
    width="80%"
    :before-close="handleClose"
    @update:model-value="emit('update:visible', $event)"
    align-center
  >
    <div
      v-loading="loading"
      class="flex flex-col gap-4 pr-3"
      style="height: 750px"
    >
      <!-- 基本信息 -->
      <ElForm label-width="80px">
        <ElFormItem :label="$t('database-manager.databaseLabel')">
          <ElInput :model-value="database" disabled />
        </ElFormItem>
        <ElFormItem v-if="schema" :label="$t('database-manager.schemaLabel')">
          <ElInput :model-value="schema" disabled />
        </ElFormItem>
        <ElFormItem :label="$t('database-manager.tableNameLabel')">
          <ElInput
            v-model="editTableName"
            :placeholder="$t('database-manager.tableNamePlaceholder')"
            :disabled="loading"
          />
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

      <!-- 字段/索引/约束 -->
      <div class="border-border min-h-[300px] rounded border p-3">
        <ElTabs>
          <ElTabPane :label="$t('database-manager.fieldManagement')">
            <FieldEditor
              v-model:fields="fields"
              :disabled="loading"
              :db-type="dbType"
              :system-fields="systemFieldNames"
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
      </div>
    </div>
    <template #footer>
      <div class="flex w-full items-center justify-between">
        <div class="text-muted-foreground text-sm">
          <span v-if="hasChanges" class="text-orange-500"
            >● {{ $t('database-manager.unsavedChanges') }}</span
          >
          <span v-else class="text-green-500"
            >● {{ $t('database-manager.noChanges') }}</span
          >
        </div>
        <div class="flex gap-2">
          <ElButton @click="handleClose" :disabled="saving">
            {{ $t('database-manager.cancel') }}
          </ElButton>
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
    </template>

    <!-- SQL预览对话框 -->
    <ElDialog
      v-model="sqlPreviewVisible"
      :title="$t('database-manager.sqlPreview')"
      width="800px"
      append-to-body
    >
      <div class="sql-preview">
        <pre class="bg-muted max-h-96 overflow-auto rounded p-4 text-sm">{{
          generatedSQL
        }}</pre>
      </div>
      <template #footer>
        <ElButton @click="sqlPreviewVisible = false">
          {{ $t('database-manager.close') }}
        </ElButton>
        <ElButton type="primary" @click="handleSave" :loading="saving">
          {{ $t('database-manager.executeSql') }}
        </ElButton>
      </template>
    </ElDialog>
  </ElDialog>
</template>

<style scoped>
.sql-preview pre {
  font-family:
    Monaco, Menlo, 'Ubuntu Mono', Consolas, source-code-pro, monospace;
  line-height: 1.6;
}
</style>
