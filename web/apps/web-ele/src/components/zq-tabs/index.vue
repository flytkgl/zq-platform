<script lang="ts" setup>
import type { Component } from 'vue';

export interface ZqTabItem {
  key: string;
  label: string;
  icon?: Component;
}

const props = withDefaults(
  defineProps<{
    items: ZqTabItem[];
    modelValue?: string;
    vertical?: boolean;
  }>(),
  {
    modelValue: '',
    vertical: false,
  },
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
  (e: 'change', value: string): void;
}>();

function handleClick(key: string) {
  emit('update:modelValue', key);
  emit('change', key);
}
</script>

<template>
  <div class="zq-tabs" :class="{ 'zq-tabs--vertical': vertical }">
    <div
      v-for="item in items"
      :key="item.key"
      class="zq-tabs__item"
      :class="{ active: modelValue === item.key }"
      @click="handleClick(item.key)"
    >
      <component v-if="item.icon" :is="item.icon" class="zq-tabs__icon" />
      <span>{{ item.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.zq-tabs {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 7px;
  background: var(--el-bg-color-page);
  border-radius: 10px;
}

.zq-tabs--vertical {
  flex-direction: column;
  align-items: stretch;
  height: 100%;
}

.zq-tabs__item {
  display: flex;
  flex: 1;
  gap: 4px;
  align-items: center;
  justify-content: center;
  padding: 6px 16px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.zq-tabs--vertical .zq-tabs__item {
  flex: none;
  flex-direction: column;
  justify-content: center;
  padding: 12px 8px;
  gap: 6px;
}

.zq-tabs__item:hover {
  color: var(--el-text-color-primary);
  background: var(--el-fill-color-light);
}

.zq-tabs__item.active {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-8);
}

.zq-tabs__icon {
  width: 16px;
  height: 16px;
}

.zq-tabs--vertical .zq-tabs__icon {
  width: 18px;
  height: 18px;
}
</style>
