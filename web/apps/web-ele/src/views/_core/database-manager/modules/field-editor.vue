<script setup lang="ts">
import { computed } from 'vue';

import { Plus, Trash } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCheckbox,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElSelect,
  ElTable,
  ElTableColumn,
} from 'element-plus';

import { getDataTypesByDbType } from '#/utils/database-types';

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

interface Props {
  fields: FieldDefinition[];
  disabled?: boolean;
  dbType?: string;
  systemFields?: string[];
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  dbType: 'postgresql',
  systemFields: () => [],
});

const emit = defineEmits<{
  'update:fields': [fields: FieldDefinition[]];
}>();
// 判断是否为系统字段（不可编辑和删除）
function isSystemField(fieldName: string): boolean {
  return props.systemFields.includes(fieldName);
}
// 根据数据库类型获取数据类型列表
const dataTypes = computed(() => getDataTypesByDbType(props.dbType));

const localFields = computed({
  get: () => props.fields,
  set: (value) => emit('update:fields', value),
});

// 触发字段更新（用于属性变化时通知父组件）
function triggerUpdate() {
  emit('update:fields', [...props.fields]);
}

// 校验字段名
function validateFieldName(fieldName: string): {
  message?: string;
  valid: boolean;
} {
  if (!fieldName) {
    return {
      valid: false,
      message: $t('database-manager.fieldNameRequired') || '字段名不能为空',
    };
  }

  // 检查是否包含空格
  if (/\s/.test(fieldName)) {
    return {
      valid: false,
      message: $t('database-manager.fieldNameNoSpace') || '字段名不能包含空格',
    };
  }

  // 检查是否以数字开头
  if (/^\d/.test(fieldName)) {
    return {
      valid: false,
      message:
        $t('database-manager.fieldNameNoNumberStart') || '字段名不能以数字开头',
    };
  }

  return { valid: true };
}

// 处理字段名变化
function handleFieldNameChange(field: FieldDefinition) {
  const validation = validateFieldName(field.name);
  if (!validation.valid) {
    ElMessage.warning(validation.message!);
    // 清除无效字符
    field.name = field.name.replaceAll(/\s/g, '').replace(/^\d+/, '');
  }
  triggerUpdate();
}

// 处理类型变化
function handleTypeChange(field: FieldDefinition) {
  // 为 NUMERIC 类型设置默认精度和小数位
  if (field.type === 'numeric') {
    if (!field.precision) {
      field.precision = 10;
    }
    if (field.scale === undefined) {
      field.scale = 2;
    }
  }
  triggerUpdate();
}

// 添加字段（在系统字段之后插入，id 永远在第一个）
function addField() {
  const newField: FieldDefinition = {
    name: '',
    type: 'varchar',
    length: 255,
    nullable: true,
    primaryKey: false,
    unique: false,
    default: undefined,
    comment: '',
  };

  // 找到最后一个系统字段的位置（遍历所有字段）
  let lastSystemFieldIndex = -1;
  for (let i = 0; i < localFields.value.length; i++) {
    if (isSystemField(localFields.value[i]?.name || '')) {
      lastSystemFieldIndex = i;
    }
  }

  // 在最后一个系统字段之后插入新字段
  const insertIndex = lastSystemFieldIndex + 1;
  const newFields = [...localFields.value];
  newFields.splice(insertIndex, 0, newField);
  localFields.value = newFields;
}

// 删除字段
function deleteField(index: number) {
  localFields.value = localFields.value.filter((_, i) => i !== index);
  ElMessage.success($t('database-manager.fieldDeleted'));
}

// 上移字段
function moveUp(index: number) {
  if (index === 0) return;
  const newFields = [...localFields.value];
  const temp = newFields[index - 1];
  newFields[index - 1] = newFields[index];
  newFields[index] = temp;
  localFields.value = newFields;
}

// 下移字段
function moveDown(index: number) {
  if (index === localFields.value.length - 1) return;
  const newFields = [...localFields.value];
  const temp = newFields[index];
  newFields[index] = newFields[index + 1];
  newFields[index + 1] = temp;
  localFields.value = newFields;
}

// 检查类型是否需要长度
function needsLength(type: string) {
  const typeInfo = dataTypes.value.find((t) => t.value === type);
  return typeInfo?.hasLength || false;
}

// 检查类型是否需要精度
function needsPrecision(type: string) {
  const typeInfo = dataTypes.value.find((t) => t.value === type);
  return typeInfo?.hasPrecision || false;
}
</script>

<template>
  <div class="field-editor">
    <div class="mb-3 flex items-center justify-between">
      <div class="text-sm font-semibold">
        {{ $t('database-manager.fieldList') }}
      </div>
      <ElButton
        type="primary"
        size="small"
        @click="addField"
        :disabled="disabled"
      >
        <Plus :size="14" />
        <span class="ml-1">{{ $t('database-manager.addField') }}</span>
      </ElButton>
    </div>

    <ElTable :data="localFields" border stripe height="400">
      <ElTableColumn
        :label="$t('database-manager.serialNumber')"
        width="60"
        align="center"
      >
        <template #default="{ $index }">
          {{ $index + 1 }}
        </template>
      </ElTableColumn>

      <ElTableColumn :label="$t('database-manager.fieldName')" width="160">
        <template #default="{ row }">
          <ElInput
            v-model="row.name"
            :placeholder="$t('database-manager.fieldNamePlaceholder')"
            size="small"
            :disabled="isSystemField(row.name)"
            @blur="() => handleFieldNameChange(row)"
            @change="triggerUpdate"
          />
        </template>
      </ElTableColumn>

      <ElTableColumn :label="$t('database-manager.dataType')" width="150">
        <template #default="{ row }">
          <ElSelect
            v-model="row.type"
            :placeholder="$t('database-manager.type')"
            size="small"
            :disabled="isSystemField(row.name)"
            @change="() => handleTypeChange(row)"
          >
            <ElOption
              v-for="type in dataTypes"
              :key="type.value"
              :label="`${type.label} - ${type.desc}`"
              :value="type.value"
            >
              <div class="flex items-center justify-between">
                <span class="font-medium">{{ type.label }}</span>
                <span class="ml-2 text-xs text-gray-500">{{ type.desc }}</span>
              </div>
            </ElOption>
          </ElSelect>
        </template>
      </ElTableColumn>

      <ElTableColumn
        :label="$t('database-manager.lengthPrecision')"
        width="130"
      >
        <template #default="{ row }">
          <ElInputNumber
            v-if="needsLength(row.type)"
            v-model="row.length"
            :min="1"
            :max="65535"
            size="small"
            controls-position="right"
            style="width: 70px"
            :disabled="isSystemField(row.name)"
            @change="triggerUpdate"
          />
          <ElInputNumber
            v-else-if="needsPrecision(row.type)"
            v-model="row.precision"
            :min="1"
            :max="65"
            size="small"
            style="width: 70px"
            controls-position="right"
            :disabled="isSystemField(row.name)"
            @change="triggerUpdate"
          />
          <span v-else class="text-xs text-gray-400">-</span>
        </template>
      </ElTableColumn>

      <ElTableColumn :label="$t('database-manager.decimalPlaces')" width="100">
        <template #default="{ row }">
          <ElInputNumber
            v-if="needsPrecision(row.type)"
            v-model="row.scale"
            :min="0"
            :max="30"
            size="small"
            style="width: 70px"
            controls-position="right"
            :disabled="isSystemField(row.name)"
            @change="triggerUpdate"
          />
          <span v-else class="text-xs text-gray-400">-</span>
        </template>
      </ElTableColumn>

      <ElTableColumn
        :label="$t('database-manager.nullable')"
        width="60"
        align="center"
      >
        <template #default="{ row }">
          <ElCheckbox
            v-model="row.nullable"
            :disabled="isSystemField(row.name)"
            @change="triggerUpdate"
          />
        </template>
      </ElTableColumn>

      <ElTableColumn :label="$t('database-manager.defaultValue')" width="120">
        <template #default="{ row }">
          <ElInput
            v-model="row.default"
            :placeholder="$t('database-manager.defaultValuePlaceholder')"
            size="small"
            :disabled="isSystemField(row.name)"
            @change="triggerUpdate"
          />
        </template>
      </ElTableColumn>

      <ElTableColumn
        :label="$t('database-manager.primaryKey')"
        width="60"
        align="center"
      >
        <template #default="{ row }">
          <ElCheckbox
            v-model="row.primaryKey"
            :disabled="isSystemField(row.name)"
            @change="triggerUpdate"
          />
        </template>
      </ElTableColumn>

      <ElTableColumn
        :label="$t('database-manager.unique')"
        width="60"
        align="center"
      >
        <template #default="{ row }">
          <ElCheckbox
            v-model="row.unique"
            :disabled="isSystemField(row.name)"
            @change="triggerUpdate"
          />
        </template>
      </ElTableColumn>

      <ElTableColumn :label="$t('database-manager.comment')" min-width="150">
        <template #default="{ row }">
          <ElInput
            v-model="row.comment"
            :placeholder="$t('database-manager.fieldCommentPlaceholder')"
            size="small"
            @change="triggerUpdate"
          />
        </template>
      </ElTableColumn>

      <ElTableColumn
        :label="$t('database-manager.operation')"
        width="140"
        fixed="right"
        align="center"
      >
        <template #default="{ row, $index }">
          <div class="flex justify-center gap-1">
            <ElButton
              size="small"
              type="danger"
              :disabled="isSystemField(row.name)"
              @click="deleteField($index)"
            >
              <Trash :size="14" />
            </ElButton>
          </div>
        </template>
      </ElTableColumn>
    </ElTable>

    <div v-if="localFields.length === 0" class="py-8 text-center text-gray-400">
      {{ $t('database-manager.noFields') }}
    </div>
  </div>
</template>

<style scoped>
.field-editor :deep(.el-input__inner),
.field-editor :deep(.el-input-number__inner) {
  text-align: left;
}
</style>
