<script setup lang="ts">
import { computed } from 'vue';

import { Plus, Trash } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElInput,
  ElMessage,
  ElOption,
  ElSelect,
  ElTable,
  ElTableColumn,
} from 'element-plus';

interface ConstraintDefinition {
  name: string;
  type: string;
  definition: string;
  columns?: string[];
  referencedTable?: string;
  referencedColumns?: string[];
}

interface FieldDefinition {
  name: string;
}

interface Props {
  constraints: ConstraintDefinition[];
  fields: FieldDefinition[];
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
});
const emit = defineEmits<{
  'update:constraints': [constraints: ConstraintDefinition[]];
}>();

// 约束类型选项
const constraintTypes = [
  { label: $t('database-manager.primaryKey'), value: 'primary' },
  { label: $t('database-manager.foreignKey'), value: 'foreign' },
  { label: $t('database-manager.unique'), value: 'unique' },
  { label: $t('database-manager.check'), value: 'check' },
];

const localConstraints = computed({
  get: () => props.constraints,
  set: (value) => emit('update:constraints', value),
});

// 添加约束
function addConstraint() {
  const newConstraint: ConstraintDefinition = {
    name: '',
    type: 'check',
    definition: '',
    columns: [],
  };
  localConstraints.value = [...localConstraints.value, newConstraint];
}

// 删除约束
function deleteConstraint(index: number) {
  localConstraints.value = localConstraints.value.filter((_, i) => i !== index);
  ElMessage.success($t('database-manager.constraintDeleted'));
}
</script>

<template>
  <div class="constraint-editor">
    <div class="mb-3 flex items-center justify-between">
      <div class="text-sm font-semibold">
        {{ $t('database-manager.constraintList') }}
      </div>
      <ElButton
        type="primary"
        size="small"
        @click="addConstraint"
        :disabled="disabled"
      >
        <Plus :size="14" />
        <span class="ml-1">{{ $t('database-manager.addConstraint') }}</span>
      </ElButton>
    </div>

    <ElTable :data="localConstraints" border stripe max-height="400">
      <ElTableColumn
        :label="$t('database-manager.serialNumber')"
        width="60"
        align="center"
      >
        <template #default="{ $index }">
          {{ $index + 1 }}
        </template>
      </ElTableColumn>

      <ElTableColumn :label="$t('database-manager.constraintName')" width="180">
        <template #default="{ row }">
          <ElInput
            v-model="row.name"
            :placeholder="$t('database-manager.constraintName')"
            size="small"
          />
        </template>
      </ElTableColumn>

      <ElTableColumn :label="$t('database-manager.constraintType')" width="150">
        <template #default="{ row }">
          <ElSelect
            v-model="row.type"
            :placeholder="$t('database-manager.constraintType')"
            size="small"
          >
            <ElOption
              v-for="type in constraintTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </ElSelect>
        </template>
      </ElTableColumn>

      <ElTableColumn :label="$t('database-manager.field')" width="180">
        <template #default="{ row }">
          <ElSelect
            v-model="row.columns"
            multiple
            :placeholder="$t('database-manager.selectField')"
            size="small"
            style="width: 100%"
          >
            <ElOption
              v-for="field in fields"
              :key="field.name"
              :label="field.name"
              :value="field.name"
            />
          </ElSelect>
        </template>
      </ElTableColumn>

      <ElTableColumn :label="$t('database-manager.definition')" min-width="200">
        <template #default="{ row }">
          <ElInput
            v-model="row.definition"
            :placeholder="$t('database-manager.constraintDefinition')"
            size="small"
          />
        </template>
      </ElTableColumn>

      <ElTableColumn
        :label="$t('database-manager.referencedTable')"
        width="150"
        v-if="false"
      >
        <template #default="{ row }">
          <ElInput
            v-if="row.type === 'foreign'"
            v-model="row.referencedTable"
            :placeholder="$t('database-manager.referencedTable')"
            size="small"
          />
          <span v-else class="text-xs text-gray-400">-</span>
        </template>
      </ElTableColumn>

      <ElTableColumn
        :label="$t('database-manager.operation')"
        width="80"
        fixed="right"
        align="center"
      >
        <template #default="{ $index }">
          <ElButton
            size="small"
            type="danger"
            @click="deleteConstraint($index)"
          >
            <Trash :size="14" />
          </ElButton>
        </template>
      </ElTableColumn>
    </ElTable>

    <div
      v-if="localConstraints.length === 0"
      class="py-8 text-center text-gray-400"
    >
      {{ $t('database-manager.noConstraints') }}
    </div>
  </div>
</template>
