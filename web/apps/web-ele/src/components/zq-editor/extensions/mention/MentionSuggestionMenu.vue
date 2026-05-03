<script setup lang="ts">
import type { User } from '#/api/core/user';

import { onMounted, onUnmounted, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { UserAvatar } from '#/components/user-avatar';

interface Props {
  items: User[];
  command: (attrs: { id: string; label: string }) => void;
}

const props = defineProps<Props>();
const selectedIndex = ref(0);
const menuRef = ref<HTMLElement>();

watch(
  () => props.items,
  () => {
    selectedIndex.value = 0;
  },
);

function selectUser(index: number) {
  const user = props.items[index];
  if (user) {
    props.command({ id: user.id, label: user.name || user.username });
  }
}

function scrollToSelected() {
  const el = menuRef.value?.children[selectedIndex.value] as
    | HTMLElement
    | undefined;
  el?.scrollIntoView({ block: 'nearest' });
}

function onKeyDown(event: KeyboardEvent): boolean {
  const len = props.items.length;
  if (len === 0) return false;

  if (event.key === 'ArrowUp') {
    event.preventDefault();
    selectedIndex.value = (selectedIndex.value + len - 1) % len;
    scrollToSelected();
    return true;
  }
  if (event.key === 'ArrowDown') {
    event.preventDefault();
    selectedIndex.value = (selectedIndex.value + 1) % len;
    scrollToSelected();
    return true;
  }
  if (event.key === 'Enter') {
    event.preventDefault();
    selectUser(selectedIndex.value);
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

defineExpose({ onKeyDown });
</script>

<template>
  <div class="zq-mention-menu">
    <template v-if="items.length > 0">
      <div
        ref="menuRef"
        class="zq-mention-menu__list"
      >
        <button
          v-for="(user, index) in items"
          :key="user.id"
          class="zq-mention-menu__item"
          :class="{ 'is-selected': index === selectedIndex }"
          @click="selectUser(index)"
          @mouseenter="selectedIndex = index"
        >
          <UserAvatar
            :user-id="user.id"
            :size="24"
            class="zq-mention-menu__avatar"
          />
          <div class="zq-mention-menu__info">
            <span class="zq-mention-menu__name">{{ user.name || user.username }}</span>
            <span v-if="user.dept_name" class="zq-mention-menu__dept">{{ user.dept_name }}</span>
          </div>
        </button>
      </div>
    </template>
    <div v-else class="zq-mention-menu__empty">
      {{ $t('zq-editor.mention.noResults') }}
    </div>
  </div>
</template>

<style>
.tippy-box[data-theme~='zq-mention'] {
  background-color: transparent !important;
  color: inherit !important;
}

.tippy-box[data-theme~='zq-mention'] .tippy-content {
  padding: 0 !important;
}

.tippy-box[data-theme~='zq-mention'] .tippy-arrow {
  display: none !important;
}
</style>

<style scoped>
.zq-mention-menu {
  min-width: 240px;
  max-width: 320px;
  max-height: 280px;
  overflow-y: auto;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  box-shadow: var(--el-box-shadow-light);
  padding: 4px;
}

.zq-mention-menu__list {
  display: flex;
  flex-direction: column;
}

.zq-mention-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 8px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  transition: background-color 0.12s;
  text-align: left;
}

.zq-mention-menu__item:hover,
.zq-mention-menu__item.is-selected {
  background-color: var(--el-fill-color-light);
}

.zq-mention-menu__avatar {
  flex-shrink: 0;
}

.zq-mention-menu__info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
  overflow: hidden;
}

.zq-mention-menu__name {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.zq-mention-menu__dept {
  font-size: 0.6875rem;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.zq-mention-menu__empty {
  padding: 12px 16px;
  text-align: center;
  color: var(--el-text-color-placeholder);
  font-size: 0.8125rem;
}
</style>
