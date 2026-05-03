<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';

import {
  AlignJustify,
  Bold,
  Code,
  Heading1,
  Heading2,
  Heading3,
  Highlighter,
  Italic,
  List,
  ListOrdered,
  Minus,
  Quote,
} from '@vben/icons';

interface CommandItem {
  title: string;
  description: string;
  icon: string;
  command: (props: any) => void;
}

interface Props {
  items: CommandItem[];
  command: (item: CommandItem) => void;
}

const props = defineProps<Props>();

const selectedIndex = ref(0);

const iconComponents: Record<string, any> = {
  Text: AlignJustify,
  Heading1,
  Heading2,
  Heading3,
  List,
  ListOrdered,
  Quote,
  Code,
  Minus,
  Bold,
  Italic,
  Highlighter,
};

const filteredItems = computed(() => props.items || []);

function selectItem(index: number) {
  const item = filteredItems.value[index];
  if (item) {
    props.command(item);
  }
}

function onKeyDown(event: KeyboardEvent) {
  if (event.key === 'ArrowUp') {
    event.preventDefault();
    selectedIndex.value =
      (selectedIndex.value + filteredItems.value.length - 1) %
      filteredItems.value.length;
    return true;
  }

  if (event.key === 'ArrowDown') {
    event.preventDefault();
    selectedIndex.value =
      (selectedIndex.value + 1) % filteredItems.value.length;
    return true;
  }

  if (event.key === 'Enter') {
    event.preventDefault();
    selectItem(selectedIndex.value);
    return true;
  }

  return false;
}

onMounted(() => {
  selectedIndex.value = 0;
});

onUnmounted(() => {
  selectedIndex.value = 0;
});

defineExpose({
  onKeyDown,
});
</script>

<template>
  <div class="slash-command-menu">
    <div
      v-for="(item, index) in filteredItems"
      :key="index"
      class="slash-command-item"
      :class="{ 'is-selected': index === selectedIndex }"
      @click="selectItem(index)"
      @mouseenter="selectedIndex = index"
    >
      <div class="slash-command-icon">
        <component :is="iconComponents[item.icon]" class="h-4 w-4" />
      </div>
      <div class="slash-command-content">
        <div class="slash-command-title">{{ item.title }}</div>
        <div class="slash-command-description">{{ item.description }}</div>
      </div>
    </div>
    <div v-if="filteredItems.length === 0" class="slash-command-empty">
      没有找到匹配的命令
    </div>
  </div>
</template>

<style>
/* 覆盖 tippy.js 的默认样式 */
.tippy-box {
  background-color: transparent !important;
  color: inherit !important;
}

.tippy-content {
  padding: 0 !important;
}

.tippy-arrow {
  display: none !important;
}
</style>

<style scoped>
.slash-command-menu {
  min-width: 280px;
  max-width: 400px;
  max-height: 400px;
  overflow-y: auto;
  background: var(--el-bg-color);
  /* border: 1px solid var(--el-border-color); */
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 0.5rem;
}

/* 美化滚动条 - 鼠标悬停时显示 */
.slash-command-menu::-webkit-scrollbar {
  width: 6px;
}

.slash-command-menu::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 3px;
}

.slash-command-menu::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 3px;
  transition: background 0.2s;
}

.slash-command-menu:hover::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
}

.slash-command-menu::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-darker);
}

.slash-command-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.slash-command-item:hover,
.slash-command-item.is-selected {
  background-color: var(--el-fill-color-light);
}

.slash-command-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.375rem;
  background-color: var(--el-fill-color);
  color: var(--el-text-color-regular);
  flex-shrink: 0;
}

.slash-command-content {
  flex: 1;
  min-width: 0;
}

.slash-command-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 0.125rem;
}

.slash-command-description {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
}

.slash-command-empty {
  padding: 1rem;
  text-align: center;
  color: var(--el-text-color-placeholder);
  font-size: 0.875rem;
}
</style>
