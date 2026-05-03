<script lang="ts" setup>
/**
 * 任务关键字参数编辑器
 * 可视化的键值对编辑组件，替代 JSON 文本输入
 */
import { ref, watch } from 'vue';

import { Plus, Trash2 } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElInput, ElOption, ElSelect } from 'element-plus';

interface KwargItem {
  key: string;
  value: string;
  type: 'boolean' | 'number' | 'string';
}

const props = defineProps<{
  modelValue?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const items = ref<KwargItem[]>([]);

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

// 解析 JSON 字符串为键值对数组
function parseJsonToItems(jsonStr: string): KwargItem[] {
  if (!jsonStr || jsonStr.trim() === '') {
    return [];
  }
  try {
    const obj = JSON.parse(jsonStr);
    if (typeof obj !== 'object' || obj === null || Array.isArray(obj)) {
      return [];
    }
    return Object.entries(obj).map(([key, value]) => {
      let type: 'boolean' | 'number' | 'string' = 'string';
      let strValue = String(value);

      if (typeof value === 'number') {
        type = 'number';
      } else if (typeof value === 'boolean') {
        type = 'boolean';
        strValue = value ? 'true' : 'false';
      }

      return { key, value: strValue, type };
    });
  } catch {
    return [];
  }
}

// 将键值对数组转换为 JSON 字符串
function itemsToJson(itemList: KwargItem[]): string {
  const validItems = itemList.filter((item) => item.key.trim() !== '');
  if (validItems.length === 0) {
    return '';
  }

  const obj: Record<string, any> = {};
  for (const item of validItems) {
    let value: any = item.value;

    if (item.type === 'number') {
      value = Number(item.value) || 0;
    } else if (item.type === 'boolean') {
      value = item.value === 'true';
    }

    obj[item.key] = value;
  }

  return JSON.stringify(obj);
}

// 监听外部值变化
watch(
  () => props.modelValue,
  (newVal) => {
    const parsed = parseJsonToItems(newVal || '');
    // 只有当解析结果与当前不同时才更新
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
  items.value.push({ key: '', value: '', type: 'string' });
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
  <div class="task-kwargs-editor">
    <div v-if="items.length === 0" class="empty-state">
      <span class="text-muted">{{ $t('scheduler.noParams') }}</span>
    </div>

    <div v-for="(item, index) in items" :key="index" class="param-row">
      <ElInput
        v-model="item.key"
        :placeholder="$t('scheduler.paramKey')"
        class="param-key"
      />
      <ElSelect
        :model-value="item.type"
        class="param-type"
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
        <ElSelect v-model="item.value" class="param-value">
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
          :placeholder="$t('scheduler.paramValue')"
          class="param-value"
        />
      </template>
      <template v-else>
        <ElInput
          v-model="item.value"
          :placeholder="$t('scheduler.paramValue')"
          class="param-value"
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
      {{ $t('scheduler.addParam') }}
    </ElButton>
  </div>
</template>

<style lang="scss" scoped>
.task-kwargs-editor {
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

.param-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.param-key {
  flex: 1;
  min-width: 120px;
}

.param-type {
  width: 100px;
}

.param-value {
  flex: 2;
  min-width: 150px;
}
</style>
