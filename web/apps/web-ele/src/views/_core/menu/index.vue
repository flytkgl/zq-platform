<script lang="ts" setup>
import type { Menu } from '#/api/core/menu';

import { nextTick, ref } from 'vue';

import { Page } from '@vben/common-ui';

import MenuForm from './modules/menu-form.vue';
import MenuTree from './modules/menu-tree.vue';

defineOptions({ name: 'SystemMenu' });

const selectedMenu = ref<Menu>();
const menuTreeRef = ref();
const menuFormRef = ref();

/**
 * 菜单选择事件
 * @param menu 选中的菜单（可能为 undefined）
 * @param autoEdit 是否自动进入编辑模式（用于新增菜单后）
 */
function onMenuSelect(menu: Menu | undefined, autoEdit = false) {
  selectedMenu.value = menu;

  // 如果需要自动进入编辑模式（用于新增菜单后）
  if (autoEdit && menu) {
    nextTick(() => {
      if (menuFormRef.value?.enterEditMode) {
        menuFormRef.value.enterEditMode();
      }
    });
  }
}

/**
 * 菜单编辑成功，只刷新当前节点
 */
function onFormSuccess() {
  // 通知树组件刷新当前选中的节点
  if (menuTreeRef.value?.refreshCurrentNode && selectedMenu.value?.id) {
    menuTreeRef.value.refreshCurrentNode(selectedMenu.value.id);
  }
  // 不清空 selectedMenu，保持当前选中的菜单
}
</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full">
      <!-- 左侧：菜单树 -->
      <div class="w-[280px]">
        <MenuTree ref="menuTreeRef" @select="onMenuSelect" />
      </div>

      <!-- 右侧：菜单表单 -->
      <div class="flex-1">
        <MenuForm
          :key="selectedMenu?.id || 'new'"
          ref="menuFormRef"
          :menu="selectedMenu"
          @success="onFormSuccess"
        />
      </div>
    </div>
  </Page>
</template>
