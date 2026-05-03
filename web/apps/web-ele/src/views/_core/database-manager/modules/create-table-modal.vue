<script setup lang="ts">
import { computed, ref } from 'vue';

import { Eye, Save } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElTabPane,
  ElTabs,
} from 'element-plus';

import { executeDDLApi } from '#/api/core/database-manager';
import { mapToDbType } from '#/utils/database-types';

import ConstraintEditor from './constraint-editor.vue';
import FieldEditor from './field-editor.vue';
import IndexEditor from './index-editor.vue';

interface Props {
  visible: boolean;
  dbName: string;
  database: string;
  schema?: string;
  dbType: string;
}

interface Emits {
  (e: 'update:visible', value: boolean): void;
  (e: 'success', tableName: string): void;
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
  autoIncrement?: boolean;
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

// 表单数据
const tableName = ref('');
const tableComment = ref('');
// 系统字段名称列表（不可修改和删除）
const systemFieldNames = [
  'id',
  'sys_create_datetime',
  'sys_update_datetime',
  'sys_creator_id',
  'sys_modifier_id',
  'sys_dept_id',
  'sort',
];

const fields = ref<FieldDefinition[]>([
  {
    name: 'id',
    type: 'varchar',
    length: 36,
    nullable: false,
    primaryKey: true,
    unique: false,
    autoIncrement: false,
    comment: '主键ID',
  },
  {
    name: 'sys_create_datetime',
    type: 'datetime',
    nullable: true,
    primaryKey: false,
    unique: false,
    autoIncrement: false,
    comment: '创建时间',
  },
  {
    name: 'sys_update_datetime',
    type: 'datetime',
    nullable: true,
    primaryKey: false,
    unique: false,
    autoIncrement: false,
    comment: '更新时间',
  },
  {
    name: 'sys_creator_id',
    type: 'varchar',
    length: 36,
    nullable: true,
    primaryKey: false,
    unique: false,
    autoIncrement: false,
    comment: '创建人ID',
  },
  {
    name: 'sys_modifier_id',
    type: 'varchar',
    length: 36,
    nullable: true,
    primaryKey: false,
    unique: false,
    autoIncrement: false,
    comment: '修改人ID',
  },
  {
    name: 'sys_dept_id',
    type: 'varchar',
    length: 36,
    nullable: true,
    primaryKey: false,
    unique: false,
    autoIncrement: false,
    comment: '部门ID',
  },
  {
    name: 'sort',
    type: 'int',
    nullable: true,
    primaryKey: false,
    unique: false,
    autoIncrement: false,
    default: '0',
    comment: '排序',
  },
]);
const indexes = ref<IndexDefinition[]>([]);
const constraints = ref<ConstraintDefinition[]>([]);

// SQL预览
const sqlPreviewVisible = ref(false);
const generatedSQL = ref('');

// Loading状态
const loading = ref(false);

// 表单验证
const formValid = computed(() => {
  return tableName.value.trim() !== '' && fields.value.length > 0;
});

// 生成CREATE TABLE SQL
function generateCreateTableSQL(): string {
  const sqlLines: string[] = [];
  const { dbType } = props;

  // CREATE TABLE语句开始
  const fullTableName = props.schema
    ? `"${props.schema}"."${tableName.value}"`
    : `"${tableName.value}"`;

  sqlLines.push(`CREATE TABLE ${fullTableName} (`);

  // 字段定义
  const fieldDefs: string[] = [];
  const primaryKeys: string[] = [];

  fields.value.forEach((field) => {
    // 将通用类型转换为数据库特定类型
    const dbFieldType = mapToDbType(field.type, dbType);
    let fieldDef = `  "${field.name}" ${dbFieldType}`;

    // 需要长度的类型
    const typesNeedLength = [
      'varchar',
      'char',
      'nvarchar',
      'nchar',
      'binary',
      'varbinary',
    ];
    // 需要精度的类型（PostgreSQL: double precision 和 real 不支持精度参数）
    const typesNeedPrecision = ['numeric', 'decimal'];
    // MySQL: float 支持精度参数
    const mysqlTypesNeedPrecision = ['float'];

    // 长度/精度（注意：某些类型如 TINYINT(1), NVARCHAR(MAX) 已经包含长度，不需要再添加）
    const lowerFieldType = field.type.toLowerCase();
    if (
      field.length > 0 &&
      field.length > 0 &&
      typesNeedLength.includes(lowerFieldType)
    ) {
      fieldDef += `(${field.length})`;
    } else if (field.precision && typesNeedPrecision.includes(lowerFieldType)) {
      fieldDef += `(${field.precision}${field.scale ? `,${field.scale}` : ''})`;
    } else if (
      field.precision &&
      dbType.toLowerCase() === 'mysql' &&
      mysqlTypesNeedPrecision.includes(lowerFieldType)
    ) {
      fieldDef += `(${field.precision}${field.scale ? `,${field.scale}` : ''})`;
    }

    // 自增（根据数据库类型）
    if (field.autoIncrement) {
      switch (dbType.toLowerCase()) {
        case 'mysql': {
          fieldDef += ' AUTO_INCREMENT';

          break;
        }
        case 'postgresql': {
          fieldDef = `  "${field.name}" SERIAL`;

          break;
        }
        case 'sqlserver':
        case 'sql server': {
          fieldDef += ' IDENTITY(1,1)';

          break;
        }
        // No default
      }
    }

    // NOT NULL
    if (!field.nullable) {
      fieldDef += ' NOT NULL';
    }

    // DEFAULT
    if (field.default) {
      fieldDef += ` DEFAULT ${field.default}`;
    }

    // UNIQUE
    if (field.unique && !field.primaryKey) {
      fieldDef += ' UNIQUE';
    }

    // 注释（MySQL支持）
    if (field.comment && dbType.toLowerCase() === 'mysql') {
      fieldDef += ` COMMENT '${field.comment}'`;
    }

    fieldDefs.push(fieldDef);

    // 收集主键
    if (field.primaryKey) {
      primaryKeys.push(`"${field.name}"`);
    }
  });

  // 添加字段定义
  sqlLines.push(
    ...fieldDefs.map((def, idx) =>
      idx < fieldDefs.length - 1 ||
      primaryKeys.length > 0 ||
      constraints.value.length > 0
        ? `${def},`
        : def,
    ),
  );

  // 主键约束
  if (primaryKeys.length > 0) {
    const pkConstraint = `  PRIMARY KEY (${primaryKeys.join(', ')})`;
    sqlLines.push(
      constraints.value.length > 0 ? `${pkConstraint},` : pkConstraint,
    );
  }

  // 其他约束
  constraints.value.forEach((constraint, idx) => {
    let constraintDef = `  CONSTRAINT "${constraint.name}"`;

    switch (constraint.type) {
      case 'check': {
        constraintDef += ` CHECK (${constraint.definition})`;

        break;
      }
      case 'foreign key': {
        constraintDef += ` FOREIGN KEY (${constraint.columns?.map((c) => `"${c}"`).join(', ')})`;
        constraintDef += ` REFERENCES "${constraint.referencedTable}" (${constraint.referencedColumns?.map((c) => `"${c}"`).join(', ')})`;

        break;
      }
      case 'unique': {
        constraintDef += ` UNIQUE (${constraint.columns?.map((c) => `"${c}"`).join(', ')})`;

        break;
      }
      // No default
    }

    if (idx < constraints.value.length - 1) {
      constraintDef += ',';
    }

    sqlLines.push(constraintDef);
  });

  sqlLines.push(');');

  // 表注释（PostgreSQL）
  if (tableComment.value && dbType.toLowerCase() === 'postgresql') {
    sqlLines.push(
      '',
      `COMMENT ON TABLE ${fullTableName} IS '${tableComment.value}';`,
    );
  }

  // 列注释（PostgreSQL）
  if (dbType.toLowerCase() === 'postgresql') {
    fields.value.forEach((field) => {
      if (field.comment) {
        sqlLines.push(
          `COMMENT ON COLUMN ${fullTableName}."${field.name}" IS '${field.comment}';`,
        );
      }
    });
  }

  // 索引
  indexes.value.forEach((index) => {
    sqlLines.push('');
    const indexType = index.unique ? 'UNIQUE INDEX' : 'INDEX';
    const indexMethod = index.type.toUpperCase();
    sqlLines.push(
      `CREATE ${indexType} "${index.name}" ON ${fullTableName} USING ${indexMethod} (${index.columns.map((c) => `"${c}"`).join(', ')});`,
    );
  });

  return sqlLines.join('\n');
}

// 预览SQL
function handlePreviewSQL() {
  if (!formValid.value) {
    ElMessage.warning($t('database-manager.fillTableNameAndFields'));
    return;
  }

  generatedSQL.value = generateCreateTableSQL();
  sqlPreviewVisible.value = true;
}

// 创建表
async function handleCreate() {
  if (!formValid.value) {
    ElMessage.warning($t('database-manager.fillTableNameAndFields'));
    return;
  }

  try {
    loading.value = true;

    // 生成SQL
    const sql = generateCreateTableSQL();

    // 调用API执行DDL
    const result = await executeDDLApi(props.dbName, {
      sql,
      database: props.database,
      schema_name: props.schema,
    });

    if (result.success) {
      ElMessage.success($t('database-manager.createTableSuccess'));
      emit('update:visible', false);
      emit('success', tableName.value);
    } else {
      ElMessage.error(
        result.message || $t('database-manager.createTableFailed'),
      );
    }
  } catch (error: any) {
    console.error('创建表失败:', error);
    ElMessage.error(error.message || $t('database-manager.createTableFailed'));
  } finally {
    loading.value = false;
  }
}

// 重置表单
function resetForm() {
  tableName.value = '';
  tableComment.value = '';
  fields.value = [
    {
      name: 'id',
      type: 'varchar',
      length: 36,
      nullable: false,
      primaryKey: true,
      unique: false,
      autoIncrement: false,
      comment: '主键ID',
    },
    {
      name: 'sys_create_datetime',
      type: 'datetime',
      nullable: true,
      primaryKey: false,
      unique: false,
      autoIncrement: false,
      comment: '创建时间',
    },
    {
      name: 'sys_update_datetime',
      type: 'datetime',
      nullable: true,
      primaryKey: false,
      unique: false,
      autoIncrement: false,
      comment: '更新时间',
    },
    {
      name: 'sys_creator_id',
      type: 'varchar',
      length: 36,
      nullable: true,
      primaryKey: false,
      unique: false,
      autoIncrement: false,
      comment: '创建人ID',
    },
    {
      name: 'sys_modifier_id',
      type: 'varchar',
      length: 36,
      nullable: true,
      primaryKey: false,
      unique: false,
      autoIncrement: false,
      comment: '修改人ID',
    },
    {
      name: 'sys_dept_id',
      type: 'varchar',
      length: 36,
      nullable: true,
      primaryKey: false,
      unique: false,
      autoIncrement: false,
      comment: '部门ID',
    },
  ];
  indexes.value = [];
  constraints.value = [];
}

// 关闭对话框
function handleClose() {
  emit('update:visible', false);
  // 延迟重置，避免关闭动画时看到数据变化
  setTimeout(resetForm, 300);
}
</script>

<template>
  <ElDialog
    :model-value="visible"
    :title="$t('database-manager.createNewTable')"
    width="80%"
    :before-close="handleClose"
    @update:model-value="emit('update:visible', $event)"
    align-center
  >
    <div class="flex flex-col gap-4" style="height: 750px">
      <!-- 基本信息 -->
      <ElForm label-width="80px">
        <ElFormItem :label="$t('database-manager.database')" required>
          <ElInput :model-value="database" disabled />
        </ElFormItem>
        <ElFormItem v-if="schema" :label="$t('database-manager.schema')">
          <ElInput :model-value="schema" disabled />
        </ElFormItem>
        <ElFormItem :label="$t('database-manager.tableName')" required>
          <ElInput
            v-model="tableName"
            :placeholder="$t('database-manager.enterTableName')"
            clearable
          />
        </ElFormItem>
        <ElFormItem :label="$t('database-manager.tableComment')">
          <ElInput
            v-model="tableComment"
            type="textarea"
            :rows="2"
            :placeholder="$t('database-manager.enterTableComment')"
          />
        </ElFormItem>
      </ElForm>

      <!-- 字段/索引/约束 -->
      <div class="min-h-[300px] flex-1 rounded border p-3">
        <ElTabs>
          <ElTabPane :label="$t('database-manager.fieldManagement')">
            <FieldEditor
              v-model:fields="fields"
              :db-type="dbType"
              :system-fields="systemFieldNames"
            />
          </ElTabPane>
          <ElTabPane :label="$t('database-manager.indexManagement')">
            <IndexEditor v-model:indexes="indexes" :fields="fields" />
          </ElTabPane>
          <ElTabPane :label="$t('database-manager.constraintManagement')">
            <ConstraintEditor
              v-model:constraints="constraints"
              :fields="fields"
            />
          </ElTabPane>
        </ElTabs>
      </div>
    </div>

    <template #footer>
      <div class="flex w-full items-center justify-between">
        <div class="text-sm text-gray-500">
          {{ $t('database-manager.databaseType') }}: {{ dbType }}
        </div>
        <div class="flex gap-2">
          <ElButton @click="handleClose" :disabled="loading">
            {{ $t('database-manager.cancel') }}
          </ElButton>
          <ElButton @click="handlePreviewSQL" :disabled="loading">
            <Eye :size="14" />
            <span class="ml-1">{{ $t('database-manager.previewSQL') }}</span>
          </ElButton>
          <ElButton
            type="primary"
            @click="handleCreate"
            :disabled="!formValid || loading"
            :loading="loading"
          >
            <Save :size="14" />
            <span class="ml-1">{{ $t('database-manager.createTable') }}</span>
          </ElButton>
        </div>
      </div>
    </template>

    <!-- SQL预览对话框 -->
    <ElDialog
      v-model="sqlPreviewVisible"
      :title="$t('database-manager.createTableSQLPreview')"
      width="800px"
      append-to-body
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
        <ElButton type="primary" @click="handleCreate">
          {{ $t('database-manager.executeCreate') }}
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
