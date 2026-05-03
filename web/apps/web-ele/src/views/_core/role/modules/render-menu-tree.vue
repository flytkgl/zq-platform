<!-- eslint-disable vue/no-unused-vars -->
<script lang="ts" setup>
import { inject } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { $t } from '@vben/locales';

interface MenuNode {
  id: string;
  name: string;
  label?: string;
  permission_count?: number;
  children?: Array<any | MenuNode>;
}

interface Props {
  menu: MenuNode;
  level?: number;
}

const props = withDefaults(defineProps<Props>(), {
  level: 0,
});

const toggleMenu = inject<(menuId: string) => void>('toggleMenu');
const selectMenu = inject<(menuId: string) => void>('selectMenu');
const toggleMenuExpanded =
  inject<(menuId: string) => void>('toggleMenuExpanded');
const selectedMenuIds = inject<Set<string>>('selectedMenuIds');
const selectedMenuId = inject<string>('selectedMenuId');
const expandedMenuIds = inject<Set<string>>('expandedMenuIds');
</script>

<template>
  <div class="space-y-0.5">
    <!-- 菜单项 -->
    <div
      class="flex h-[42px] cursor-pointer items-center rounded-[8px] px-3 transition-colors"
      :class="[
        selectedMenuId === menu.id
          ? 'bg-primary/15 dark:bg-accent text-primary'
          : 'hover:bg-[var(--el-fill-color-light)]',
      ]"
      :style="{ paddingLeft: `calc(12px + ${level * 20}px)` }"
      @click="selectMenu?.(menu.id)"
    >
      <div class="flex min-w-0 flex-1 items-center gap-2">
        <!-- 展开/折叠按钮 -->
        <div
          v-if="menu.children && menu.children.length > 0"
          class="hover:text-primary flex w-4 flex-shrink-0 cursor-pointer items-center justify-center"
          @click.stop="toggleMenuExpanded?.(menu.id)"
        >
          <IconifyIcon
            icon="ep:caret-right"
            class="size-4 transform transition-transform"
            :class="expandedMenuIds?.has(menu.id) ? 'rotate-90' : ''"
          />
        </div>
        <div v-else class="w-4 flex-shrink-0"></div>

        <!-- 菜单复选框 -->
        <input
          type="checkbox"
          :checked="selectedMenuIds?.has(menu.id)"
          class="size-4 cursor-pointer rounded border-gray-300 transition-colors"
          @change="toggleMenu?.(menu.id)"
          @click.stop
        />
        <!-- 菜单名称 -->
        <span
          class="truncate text-xs"
          :title="menu.label ? $t(menu.label) : menu.name"
        >
          {{ menu.label ? $t(menu.label) : menu.name }}
        </span>
      </div>

      <!-- 权限计数 -->
      <span
        v-if="menu.permission_count && menu.permission_count > 0"
        class="ml-2 flex-shrink-0 text-xs text-gray-400"
      >
        {{ menu.permission_count }} {{ $t('role.permissions.permissionCount') }}
      </span>
    </div>

    <!-- 子菜单（递归） -->
    <div
      v-if="
        expandedMenuIds?.has(menu.id) &&
        menu.children &&
        menu.children.length > 0
      "
      class="space-y-0.5"
    >
      <template v-for="child in menu.children" :key="child.id">
        <RenderMenuTree :menu="child" :level="level + 1" />
      </template>
    </div>
  </div>
</template>

<style scoped>
/* 复选框自定义样式 */
input[type='checkbox'] {
  accent-color: var(--el-color-primary);
  cursor: pointer;
}

input[type='checkbox']:indeterminate {
  accent-color: var(--el-color-primary);
}
</style>
