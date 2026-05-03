<script lang="ts" setup>
/**
 * 任务位置参数编辑器
 * 可视化的数组编辑组件，替代 JSON 文本输入
 */
import { ref, watch } from 'vue';

import { Plus, Trash2 } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElInput, ElOption, ElSelect } from 'element-plus';

interface ArgItem {
  value: string;
  type: 'boolean' | 'number' | 'string';
}

const props = defineProps<{
  modelValue?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const items = ref<ArgItem[]>([]);

// 类型选项
const typeOptions = [
  { label: $t('scheduler.paramType.string'), value: 'string' },
  { label: $t('scheduler.paramType.number'), value: 'number' },
  { label: $t('scheduler.paramType.boolean'), value: 'boolean' },
];

// 布尔值选项
const booleanOptions = [
  { label: 'true', value: 'true' },
  { label: 'false', value: 'false' },
];

// 解析 JSON 字符串为数组
function parseJsonToItems(jsonStr: string): ArgItem[] {
  if (!jsonStr || jsonStr.trim() === '') {
    return [];
  }
  try {
    const arr = JSON.parse(jsonStr);
    if (!Array.isArray(arr)) {
      return [];
    }
    return arr.map((value) => {
      let type: 'boolean' | 'number' | 'string' = 'string';
      let strValue = String(value);

      if (typeof value === 'number') {
        type = 'number';
      } else if (typeof value === 'boolean') {
        type = 'boolean';
        strValue = value ? 'true' : 'false';
      }

      return { value: strValue, type };
    });
  } catch {
    return [];
  }
}

// 将数组转换为 JSON 字符串
function itemsToJson(itemList: ArgItem[]): string {
  if (itemList.length === 0) {
    return '';
  }

  const arr = itemList.map((item) => {
    if (item.type === 'number') {
      return Number(item.value) || 0;
    } else if (item.type === 'boolean') {
      return item.value === 'true';
    }
    return item.value;
  });

  return JSON.stringify(arr);
}

// 监听外部值变化
watch(
  () => props.modelValue,
  (newVal) => {
    const parsed = parseJsonToItems(newVal || '');
    if (JSON.stringify(parsed) !== JSON.stringify(items.value)) {
      items.value = parsed;
    }
  },
  { immediate: true },
);

// 监听内部值变化，同步到外部
watch(
  items,
  (newItems) => {
    const json = itemsToJson(newItems);
    if (json !== props.modelValue) {
      emit('update:modelValue', json);
    }
  },
  { deep: true },
);

// 添加新参数
function addItem() {
  items.value.push({ value: '', type: 'string' });
}

// 删除参数
function removeItem(index: number) {
  items.value.splice(index, 1);
}

// 处理类型变化
function handleTypeChange(
  index: number,
  type: 'boolean' | 'number' | 'string',
) {
  const item = items.value[index];
  if (!item) return;

  item.type = type;

  // 重置值
  if (type === 'boolean') {
    item.value = 'false';
  } else if (type === 'number') {
    item.value = '0';
  }
}
</script>

<template>
  <div class="task-args-editor">
    <div v-if="items.length === 0" class="empty-state">
      <span class="text-muted">{{ $t('scheduler.noArgs') }}</span>
    </div>

    <div v-for="(item, index) in items" :key="index" class="arg-row">
      <span class="arg-index">{{ index + 1 }}</span>
      <ElSelect
        :model-value="item.type"
        class="arg-type"
        @change="
          (val: string) =>
            handleTypeChange(index, val as 'string' | 'number' | 'boolean')
        "
      >
        <ElOption
          v-for="opt in typeOptions"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </ElSelect>
      <template v-if="item.type === 'boolean'">
        <ElSelect v-model="item.value" class="arg-value">
          <ElOption
            v-for="opt in booleanOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </ElSelect>
      </template>
      <template v-else-if="item.type === 'number'">
        <ElInput
          v-model="item.value"
          type="number"
          :placeholder="$t('scheduler.argValue')"
          class="arg-value"
        />
      </template>
      <template v-else>
        <ElInput
          v-model="item.value"
          :placeholder="$t('scheduler.argValue')"
          class="arg-value"
        />
      </template>
      <ElButton
        type="danger"
        text
        circle
        size="small"
        @click="removeItem(index)"
      >
        <Trash2 class="size-4" />
      </ElButton>
    </div>

    <ElButton type="primary" text size="small" @click="addItem">
      <Plus class="mr-1 size-4" />
      {{ $t('scheduler.addArg') }}
    </ElButton>
  </div>
</template>

<style lang="scss" scoped>
.task-args-editor {
  width: 100%;
}

.empty-state {
  padding: 12px;
  text-align: center;
  color: var(--el-text-color-placeholder);
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  margin-bottom: 8px;
}

.arg-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.arg-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.arg-type {
  width: 100px;
}

.arg-value {
  flex: 1;
  min-width: 200px;
}
</style>
