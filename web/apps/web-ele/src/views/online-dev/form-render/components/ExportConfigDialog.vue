<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import { ElAlert, ElCheckbox, ElCheckboxGroup, ElMessage } from 'element-plus';

import { ZqDialog } from '#/components/zq-dialog';

interface Column {
  field: string;
  label: string;
}

interface Props {
  modelValue: boolean;
  columns: Column[];
  hasSubTables?: boolean;
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void;
  (
    e: 'confirm',
    config: { includeSubTables: boolean; selectedFields: string[] },
  ): void;
}

const props = withDefaults(defineProps<Props>(), {
  hasSubTables: false,
});

const emit = defineEmits<Emits>();

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const loading = ref(false);
const selectedFields = ref<string[]>([]);
const includeSubTables = ref(false);

// 可用的列（排除内部字段，保留系统字段）
const availableColumns = computed(() => {
  return props.columns.filter((col) => {
    // 只排除内部字段，不排除系统字段
    const internalFields = ['is_deleted', 'sort'];
    return !internalFields.includes(col.field);
  });
});

// 全选状态
const selectAll = computed({
  get: () => {
    const availableCount = availableColumns.value.length;
    const selectedCount = selectedFields.value.length;
    return availableCount > 0 && selectedCount === availableCount;
  },
  set: () => {},
});

// 半选状态
const indeterminate = computed(() => {
  const len = selectedFields.value.length;
  return len > 0 && len < availableColumns.value.length;
});

// 全选/取消全选
function handleSelectAll(checked: boolean) {
  selectedFields.value = checked
    ? availableColumns.value.map((col) => col.field)
    : [];
}

// 初始化时默认全选（包括子表）
watch(visible, (newVal) => {
  if (newVal) {
    selectedFields.value = availableColumns.value.map((col) => col.field);
    // 如果有子表，默认勾选导出子表
    includeSubTables.value = props.hasSubTables;
  }
});

// 确认导出
function handleConfirm() {
  if (selectedFields.value.length === 0) {
    ElMessage.warning('请至少选择一个字段');
    return;
  }

  emit('confirm', {
    selectedFields: selectedFields.value,
    includeSubTables: includeSubTables.value,
  });
  visible.value = false;
}
</script>

<template>
  <ZqDialog
    v-model="visible"
    title="导出配置"
    width="600px"
    :confirm-loading="loading"
    @confirm="handleConfirm"
  >
    <div class="export-config">
      <!-- 字段选择 -->
      <div class="config-section">
        <div class="section-header">
          <span class="section-title">选择导出字段</span>
          <ElCheckbox
            v-model="selectAll"
            :indeterminate="indeterminate"
            @change="handleSelectAll"
          >
            全选
          </ElCheckbox>
        </div>
        <ElCheckboxGroup v-model="selectedFields" class="field-list">
          <ElCheckbox
            v-for="column in availableColumns"
            :key="column.field"
            :label="column.field"
          >
            {{ column.label }}
          </ElCheckbox>
        </ElCheckboxGroup>
      </div>

      <!-- 子表选项 -->
      <div v-if="hasSubTables" class="config-section">
        <div class="section-header">
          <span class="section-title">子表选项</span>
        </div>
        <ElCheckbox v-model="includeSubTables"> 导出子表数据 </ElCheckbox>
        <div v-if="includeSubTables" class="sub-table-tip">
          <ElAlert type="info" :closable="false" show-icon>
            <template #title>
              导出子表时，主表必须包含 ID 字段用于关联
            </template>
          </ElAlert>
        </div>
      </div>
    </div>
  </ZqDialog>
</template>

<style scoped lang="scss">
.export-config {
  .config-section {
    margin-bottom: 24px;

    &:last-child {
      margin-bottom: 0;
    }

    .section-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;

      .section-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--el-text-color-primary);
      }
    }

    .field-list {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      max-height: 300px;
      overflow-y: auto;
      padding: 12px;
      background: var(--el-fill-color-lighter);
      border-radius: 4px;

      :deep(.el-checkbox) {
        margin-right: 0;
      }
    }

    .export-tip {
      margin-top: 12px;
    }

    .sub-table-tip {
      margin-top: 12px;
    }
  }
}
</style>
