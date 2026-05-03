<script lang="ts" setup>
import type { Menu, MenuTreeNode } from '#/api/core/menu';

import { computed, onMounted, ref, watch } from 'vue';

import { IconifyIcon, Plus, Search } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElScrollbar,
  ElSkeleton,
  ElSkeletonItem,
  ElTooltip,
} from 'element-plus';

import {
  deleteMenuApi,
  getAllMenuTreeApi,
  getMenuDetailApi,
  searchMenuApi,
} from '#/api/core/menu';
import { ZqTabs } from '#/components/zq-tabs';
import { useAppContextStore } from '#/store/app-context';

import MenuFormModal from './menu-form-modal.vue';

const emit = defineEmits<{
  select: [menu: Menu | undefined, autoEdit?: boolean];
}>();

// 菜单编辑弹窗

const appContextStore = useAppContextStore();

const treeData = ref<MenuTreeNode[]>([]);
const loading = ref(false);
const selectedMenuId = ref<string>();
const searchKeyword = ref<string>('');
const menuTab = ref('app');
const menuTabItems = computed(() => [
  { key: 'app', label: $t('menu.appMenu') },
  { key: 'system', label: $t('menu.systemMenu') },
]);
const hoveredMenuId = ref<string>();
const expandedMenuIds = ref<Set<string>>(new Set());
const searchResults = ref<MenuTreeNode[]>([]);
const isSearching = ref(false);
const menuFormModalRef = ref<InstanceType<typeof MenuFormModal>>();

/**
 * 转换菜单数据结构
 * 将后端返回的扁平化数据转换为前端期望的 meta 结构
 */
function transformMenuData(menus: any[]) {
  return menus.map((menu) => ({
    ...menu,
    // 根据后端返回的 child_count 判断是否有子节点
    hasChild: menu.child_count && menu.child_count > 0,
    meta: {
      title: menu.title,
      icon: menu.icon,
      activeIcon: menu.activeIcon,
      activePath: menu.activePath,
      affixTab: menu.affixTab,
      badge: menu.badge,
      badgeType: menu.badgeType,
      badgeVariants: menu.badgeVariants,
      hideChildrenInMenu: menu.hideChildrenInMenu,
      hideInBreadcrumb: menu.hideInBreadcrumb,
      hideInMenu: menu.hideInMenu,
      hideInTab: menu.hideInTab,
      keepAlive: menu.keepAlive,
      link: menu.link,
      iframeSrc: menu.iframeSrc,
      openInNewWindow: menu.openInNewWindow,
      order: menu.order,
      query: menu.query,
      noBasicLayout: menu.noBasicLayout,
      maxNumOfOpenTab: menu.maxNumOfOpenTab,
    },
  }));
}

/**
 * 转换树形菜单数据结构（递归处理）
 * 将后端返回的树形数据转换为前端期望的 meta 结构
 */
function transformMenuTreeData(menus: any[]): MenuTreeNode[] {
  return menus.map((menu) => {
    const transformed: MenuTreeNode = {
      ...menu,
      // 判断是否有子节点
      hasChild: menu.children && menu.children.length > 0,
      meta: {
        title: menu.title,
        icon: menu.icon,
        activeIcon: menu.activeIcon,
        activePath: menu.activePath,
        affixTab: menu.affixTab,
        badge: menu.badge,
        badgeType: menu.badgeType,
        badgeVariants: menu.badgeVariants,
        hideChildrenInMenu: menu.hideChildrenInMenu,
        hideInBreadcrumb: menu.hideInBreadcrumb,
        hideInMenu: menu.hideInMenu,
        hideInTab: menu.hideInTab,
        keepAlive: menu.keepAlive,
        link: menu.link,
        iframeSrc: menu.iframeSrc,
        openInNewWindow: menu.openInNewWindow,
        order: menu.order,
        query: menu.query,
        noBasicLayout: menu.noBasicLayout,
        maxNumOfOpenTab: menu.maxNumOfOpenTab,
      },
    };

    // 递归处理子菜单
    if (menu.children && menu.children.length > 0) {
      transformed.children = transformMenuTreeData(menu.children);
    }

    return transformed;
  });
}

/**
 * 加载所有菜单数据（全量加载）
 */
async function fetchMenuList(autoSelectFirst = false) {
  try {
    loading.value = true;
    // 获取完整的菜单树（全量加载），传入当前应用ID
    const applicationId = appContextStore.currentApp?.id;
    const data = await getAllMenuTreeApi(applicationId, false);
    treeData.value = transformMenuTreeData(Array.isArray(data) ? data : []);

    // 如果需要自动选中第一个菜单
    if (autoSelectFirst && treeData.value.length > 0) {
      const firstMenu = treeData.value[0];
      if (firstMenu) {
        selectedMenuId.value = firstMenu.id;
        emit('select', firstMenu);
      }
    }
  } finally {
    loading.value = false;
  }
}

/**
 * 切换节点展开/折叠
 */
function toggleNodeExpanded(menu: MenuTreeNode) {
  if (expandedMenuIds.value.has(menu.id)) {
    expandedMenuIds.value.delete(menu.id);
  } else {
    expandedMenuIds.value.add(menu.id);
  }
}

/**
 * 选择菜单
 */
function onMenuSelect(menu: MenuTreeNode) {
  selectedMenuId.value = menu.id;
  emit('select', menu);
}

/**
 * 添加菜单
 */
function onAddMenu() {
  menuFormModalRef.value?.open();
}

/**
 * 在当前菜单下新建子菜单
 */
function onAddChildMenu(menu: MenuTreeNode) {
  menuFormModalRef.value?.open({
    parent_id: menu.id,
    parent_path: menu.path,
  });
}

/**
 * 删除菜单
 */
async function onDeleteMenu(menu: MenuTreeNode) {
  ElMessageBox.confirm(
    $t('ui.actionMessage.deleteConfirm', [menu.name]),
    $t('common.delete'),
    {
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
      type: 'warning',
      showClose: false,
    },
  )
    .then(async () => {
      try {
        await deleteMenuApi(menu.id);
        ElMessage.success($t('ui.actionMessage.deleteSuccess', [menu.name]));

        // 如果删除的是当前选中的菜单，清除选中状态
        if (selectedMenuId.value === menu.id) {
          selectedMenuId.value = undefined;
          emit('select', undefined);
        }

        // 保存当前展开的节点ID
        const currentExpandedIds = new Set(expandedMenuIds.value);
        // 从展开列表中移除被删除的菜单
        currentExpandedIds.delete(menu.id);

        // 重新加载整个菜单树
        await fetchMenuList();

        // 恢复展开状态
        expandedMenuIds.value = currentExpandedIds;
      } catch {
        ElMessage.error($t('ui.actionMessage.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

/**
 * 表单成功回调（新增菜单后）
 */
async function onMenuFormSuccess(menuData?: any) {
  // 保存当前展开的节点ID
  const currentExpandedIds = new Set(expandedMenuIds.value);

  // 重新加载整个菜单树
  await fetchMenuList();

  // 恢复展开状态
  expandedMenuIds.value = currentExpandedIds;

  if (menuData?.id) {
    // 自动选中新创建的菜单，并进入编辑模式
    const newMenu = await findMenuById(menuData.id);
    if (newMenu) {
      selectedMenuId.value = newMenu.id;
      emit('select', newMenu, true); // 传递 autoEdit = true

      // 自动展开新菜单的父节点
      if (menuData.parent_id) {
        expandedMenuIds.value.add(menuData.parent_id);
      }
    }
  }
}

/**
 * 检查菜单是否有子菜单
 */
function hasChildren(menu: MenuTreeNode): boolean {
  // 全量加载模式下，直接检查 children 属性
  return menu.children !== undefined && menu.children.length > 0;
}

/**
 * 自动展开搜索结果中的所有节点
 */
function autoExpandSearchResults(nodes: MenuTreeNode[]) {
  nodes.forEach((node) => {
    expandedMenuIds.value.add(node.id);
    if (node.children && node.children.length > 0) {
      autoExpandSearchResults(node.children);
    }
  });
}

/**
 * 防抖搜索定时器
 */
let searchTimer: null | ReturnType<typeof setTimeout> = null;

/**
 * 监听搜索文本变化，执行后端搜索
 */
watch(searchKeyword, (newVal) => {
  // 清除之前的定时器
  if (searchTimer) {
    clearTimeout(searchTimer);
  }

  if (!newVal.trim()) {
    searchResults.value = [];
    isSearching.value = false;
    return;
  }

  // 设置新的防抖定时器
  searchTimer = setTimeout(async () => {
    isSearching.value = true;
    try {
      const results = await searchMenuApi(newVal);
      // 转换搜索结果数据结构
      const transformedResults = transformMenuData(results || []);
      searchResults.value = transformedResults;
      // 自动展开搜索结果中的所有节点，显示完整路径
      if (transformedResults && transformedResults.length > 0) {
        autoExpandSearchResults(transformedResults);
      }
    } catch (error) {
      console.error($t('menu.searchFailed'), error);
      searchResults.value = [];
    } finally {
      isSearching.value = false;
    }
  }, 300);
});

/**
 * 递归过滤树节点：根据 is_system 字段过滤
 */
function filterTreeBySystem(
  nodes: MenuTreeNode[],
  isSystem: boolean,
): MenuTreeNode[] {
  return nodes
    .filter((node) => !!node.is_system === isSystem)
    .map((node) => ({
      ...node,
      children: node.children
        ? filterTreeBySystem(node.children, isSystem)
        : undefined,
    }));
}

/**
 * 过滤树数据：如果有搜索结果则使用搜索结果，否则使用完整树，并按 tab 过滤
 */
const filteredTreeData = computed(() => {
  let data: MenuTreeNode[];
  data =
    searchKeyword.value.trim() && searchResults.value.length > 0
      ? searchResults.value
      : treeData.value;
  const isSystem = menuTab.value === 'system';
  return filterTreeBySystem(data, isSystem);
});

/**
 * 渲染树形列表
 */
const renderTreeList = (nodes: MenuTreeNode[], level: number = 0): any[] => {
  return nodes.flatMap((node) => [
    { node, level, isNode: true },
    ...(expandedMenuIds.value.has(node.id) &&
    node.children &&
    node.children.length > 0
      ? renderTreeList(node.children, level + 1)
      : []),
  ]);
};

const flattenedTree = computed(() => renderTreeList(filteredTreeData.value));

/**
 * 暴露给父组件的方法：刷新整个树
 */
async function refreshTree() {
  // 保存当前展开的节点ID
  const currentExpandedIds = new Set(expandedMenuIds.value);

  // 重新加载整个菜单树
  await fetchMenuList();

  // 恢复展开状态
  expandedMenuIds.value = currentExpandedIds;
}

/**
 * 根据 ID 查找菜单（用于选中新创建的菜单）
 */
function findMenuById(menuId: string): MenuTreeNode | null {
  function search(nodes: MenuTreeNode[]): MenuTreeNode | null {
    for (const node of nodes) {
      if (node.id === menuId) {
        return node;
      }
      if (node.children && node.children.length > 0) {
        const found = search(node.children);
        if (found) return found;
      }
    }
    return null;
  }
  return search(treeData.value);
}

/**
 * 递归更新树中的指定节点
 */
function updateNodeInTree(
  nodes: MenuTreeNode[],
  menuId: string,
  updatedData: Menu,
): boolean {
  for (let i = 0; i < nodes.length; i++) {
    if (nodes[i].id === menuId) {
      // 保留 children 和 hasChild，更新其他属性
      const children = nodes[i].children;
      const hasChild = nodes[i].hasChild;

      // 将扁平化的 Menu 数据转换为带 meta 的结构
      nodes[i] = {
        ...updatedData,
        children,
        hasChild,
        meta: {
          title: updatedData.title,
          icon: updatedData.icon,
          activeIcon: updatedData.activeIcon,
          activePath: updatedData.activePath,
          affixTab: updatedData.affixTab,
          badge: updatedData.badge,
          badgeType: updatedData.badgeType,
          badgeVariants: updatedData.badgeVariants,
          hideChildrenInMenu: updatedData.hideChildrenInMenu,
          hideInBreadcrumb: updatedData.hideInBreadcrumb,
          hideInMenu: updatedData.hideInMenu,
          hideInTab: updatedData.hideInTab,
          keepAlive: updatedData.keepAlive,
          link: updatedData.link,
          iframeSrc: updatedData.iframeSrc,
          openInNewWindow: updatedData.openInNewWindow,
          order: updatedData.order,
          query: updatedData.query,
          noBasicLayout: updatedData.noBasicLayout,
          maxNumOfOpenTab: updatedData.maxNumOfOpenTab,
        },
      } as MenuTreeNode;
      return true;
    }
    if (
      nodes[i].children &&
      nodes[i].children!.length > 0 &&
      updateNodeInTree(nodes[i].children!, menuId, updatedData)
    ) {
      return true;
    }
  }
  return false;
}

/**
 * 暴露给父组件的方法：刷新指定节点（只更新当前节点，不刷新整个树）
 */
async function refreshCurrentNode(menuId: string) {
  try {
    // 获取最新的菜单详情
    const updatedMenu = await getMenuDetailApi(menuId);

    // 更新树中的节点数据
    updateNodeInTree(treeData.value, menuId, updatedMenu);

    // 重新选中该节点，触发表单更新
    const updatedNode = findMenuById(menuId);
    if (updatedNode) {
      emit('select', updatedNode);
    }
  } catch (error) {
    console.error($t('menu.refreshFailed'), error);
    ElMessage.error($t('menu.refreshFailed'));
  }
}

// 暴露方法给父组件
defineExpose({
  refreshTree,
  refreshCurrentNode,
});

onMounted(() => {
  fetchMenuList(true); // 首次加载时自动选中第一个菜单
});
</script>

<template>
  <ElCard
    style="border: none"
    class="mr-[10px] h-full"
    shadow="never"
    :body-style="{
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
    }"
  >
    <MenuFormModal ref="menuFormModalRef" @success="onMenuFormSuccess" />

    <!-- 搜索和添加区域 -->
    <div class="mb-3 flex flex-shrink-0 gap-2">
      <ElInput
        v-model="searchKeyword"
        :placeholder="$t('common.search')"
        clearable
        :prefix-icon="Search"
      />
      <ElButton :icon="Plus" @click="onAddMenu" />
    </div>

    <!-- 菜单类型切换 -->
    <div class="mb-3 flex-shrink-0">
      <ZqTabs v-model="menuTab" :items="menuTabItems" />
    </div>

    <!-- 菜单树列表 -->
    <div class="min-h-0 flex-1 overflow-hidden">
      <ElSkeleton :loading="loading || isSearching" animated :count="8">
        <template #template>
          <div class="space-y-1">
            <div v-for="i in 8" :key="i" class="menu-skeleton-item">
              <ElSkeletonItem
                variant="text"
                style="width: 100%; height: 40px"
              />
            </div>
          </div>
        </template>
        <template #default>
          <div style="height: 100%">
            <ElScrollbar style="height: 100%">
              <div class="space-y-1 pr-2">
                <div
                  v-for="(item, index) in flattenedTree"
                  :key="`${item.node.id}-${index}`"
                  class="flex h-[42px] cursor-pointer items-center justify-between rounded-[8px] px-3 transition-colors"
                  :class="[
                    selectedMenuId === item.node.id
                      ? 'bg-primary/15 dark:bg-accent text-primary'
                      : 'hover:bg-[var(--el-fill-color-light)]',
                  ]"
                  :style="{ paddingLeft: `calc(12px + ${item.level * 20}px)` }"
                  @mouseenter="hoveredMenuId = item.node.id"
                  @mouseleave="hoveredMenuId = undefined"
                  @click="onMenuSelect(item.node)"
                >
                  <!-- 菜单名称和展开/折叠按钮 -->
                  <div class="flex min-w-0 flex-1 items-center gap-1.5">
                    <!-- 展开/折叠按钮 -->
                    <div
                      v-if="hasChildren(item.node)"
                      class="hover:text-primary flex w-4 flex-shrink-0 cursor-pointer items-center justify-center"
                      @click.stop="toggleNodeExpanded(item.node)"
                    >
                      <IconifyIcon
                        icon="ep:caret-right"
                        class="size-4 transform transition-transform"
                        :class="
                          expandedMenuIds.has(item.node.id) ? 'rotate-90' : ''
                        "
                      />
                    </div>
                    <div v-else class="w-4 flex-shrink-0"></div>

                    <!-- 菜单图标 -->
                    <div class="text-primary size-4 flex-shrink-0">
                      <IconifyIcon
                        :icon="item.node.meta?.icon || 'carbon:circle-dash'"
                        class="size-full"
                      />
                    </div>

                    <!-- 菜单名称 -->
                    <div
                      class="truncate text-sm"
                      :title="
                        item.node.meta?.title
                          ? $t(item.node.meta.title)
                          : item.node.name
                      "
                    >
                      {{
                        item.node.meta?.title
                          ? $t(item.node.meta.title)
                          : item.node.name
                      }}
                    </div>
                  </div>

                  <!-- 操作图标 -->
                  <div
                    v-if="hoveredMenuId === item.node.id"
                    class="ml-2 flex flex-shrink-0 gap-0.5"
                    @click.stop
                  >
                    <ElTooltip
                      :content="$t('menu.addChildMenu')"
                      placement="top"
                    >
                      <ElButton
                        type="primary"
                        text
                        size="small"
                        circle
                        @click="onAddChildMenu(item.node)"
                      >
                        <IconifyIcon icon="ep:plus" class="size-4" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip :content="$t('menu.deleteMenu')" placement="top">
                      <ElButton
                        type="danger"
                        text
                        size="small"
                        circle
                        style="margin-left: 0"
                        :title="$t('common.delete')"
                        @click="onDeleteMenu(item.node)"
                      >
                        <IconifyIcon icon="ep:delete" class="size-4" />
                      </ElButton>
                    </ElTooltip>
                  </div>
                </div>
              </div>
            </ElScrollbar>
          </div>
        </template>
      </ElSkeleton>
    </div>
  </ElCard>
</template>

<style scoped>
/* 输入框前置图标样式 */
:deep(.el-input__icon) {
  cursor: pointer;
}

/* 文本按钮样式 */
:deep(.el-button--text) {
  padding: 0 4px;
}

/* 骨架屏样式 */
.menu-skeleton-item {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
}
</style>
