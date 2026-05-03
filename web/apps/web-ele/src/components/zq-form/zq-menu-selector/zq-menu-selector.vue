<script lang="ts" setup>
/**
 * 菜单选择器组件
 * 支持两种显示模式：dialog（带触发器的弹窗选择）和 popup（只有弹窗，无触发器）
 * 支持单选和多选
 */
import type { MenuItem, MenuSelectorProps } from './types';

import { computed, ref, watch } from 'vue';

import { ChevronDown, ChevronRight, IconifyIcon, X } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCheckbox,
  ElEmpty,
  ElOption,
  ElScrollbar,
  ElSelect,
} from 'element-plus';

import { ZqDialog } from '#/components/zq-dialog';
import { useAppContextStore } from '#/store/app-context';

defineOptions({
  name: 'ZqMenuSelector',
});

const props = withDefaults(defineProps<MenuSelectorProps>(), {
  modelValue: null,
  mode: 'dialog',
  placeholder: '请选择菜单',
  disabled: false,
  clearable: true,
  multiple: false,
  dialogTitle: '选择菜单',
  dialogWidth: '400px',
  applicationId: undefined,
  systemOnly: false,
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: null | string | string[]): void;
  (e: 'change', menu: MenuItem | MenuItem[] | null): void;
  (e: 'select', menu: MenuItem): void;
}>();

const appContextStore = useAppContextStore();

// 实际使用的 applicationId：优先用外部传入的，否则自动取当前应用
const resolvedApplicationId = computed(
  () => props.applicationId ?? appContextStore.currentApp?.id,
);

// 菜单数据
const menuTreeData = ref<MenuItem[]>([]);
const menuTreeLoaded = ref(false);
const loading = ref(false);

// 弹窗可见性
const dialogVisible = ref(false);

// 单选时选中的菜单
const selectedMenu = ref<MenuItem | null>(null);

// 多选时选中的菜单列表
const selectedMenus = ref<MenuItem[]>([]);

// 展开的菜单 ID 集合
const expandedMenuIds = ref<Set<string>>(new Set());

// 处理菜单数据，添加 title 字段用于显示
const processMenuData = (menus: any[]): MenuItem[] => {
  return menus.map((menu) => {
    // 优先使用 title，其次使用 name
    const rawTitle = menu.title || menu.name;
    // 尝试翻译，如果翻译结果与原值相同则说明不是国际化 key
    const translatedTitle = rawTitle ? $t(rawTitle) : rawTitle;
    const displayTitle =
      translatedTitle === rawTitle ? rawTitle : translatedTitle;
    return {
      ...menu,
      title: displayTitle,
      children: menu.children ? processMenuData(menu.children) : undefined,
    };
  });
};

// 过滤只保留系统菜单
const filterSystemMenus = (menus: any[]): any[] => {
  return menus
    .filter((menu) => menu.is_system === true)
    .map((menu) => ({
      ...menu,
      children: menu.children ? filterSystemMenus(menu.children) : undefined,
    }))
    .filter(
      (menu) => menu.is_system || (menu.children && menu.children.length > 0),
    );
};

// 加载菜单树
const loadMenuTree = async () => {
  if (menuTreeLoaded.value) return;
  loading.value = true;
  try {
    const { getAllMenuTreeApi } = await import('#/api/core/menu');
    // 如果指定了 applicationId，则不包含系统菜单（除非 systemOnly 为 true）
    const includeSystem = props.systemOnly || !resolvedApplicationId.value;
    const data = await getAllMenuTreeApi(
      resolvedApplicationId.value,
      true,
      includeSystem,
    );

    // 如果 systemOnly 为 true，过滤只保留系统菜单
    let processedData = data || [];
    if (props.systemOnly) {
      processedData = filterSystemMenus(processedData);
    }

    menuTreeData.value = processMenuData(processedData);
    menuTreeLoaded.value = true;
    // 默认展开所有父级菜单
    expandAllParents();
  } catch (error) {
    console.error('Failed to load menu tree:', error);
  } finally {
    loading.value = false;
  }
};

// 根据 ID 在树中查找菜单
const findMenuInTree = (
  id: null | string | undefined,
  menus: MenuItem[],
): MenuItem | null => {
  if (!id) return null;
  for (const menu of menus) {
    if (menu.id === id) return menu;
    if (menu.children && menu.children.length > 0) {
      const found = findMenuInTree(id, menu.children);
      if (found) return found;
    }
  }
  return null;
};

// 扁平化菜单树用于 dialog 显示（支持折叠）
const flattenedMenuList = computed(() => {
  const result: {
    hasChildren: boolean;
    isExpanded: boolean;
    level: number;
    menu: MenuItem;
  }[] = [];
  const flatten = (
    menus: MenuItem[],
    level: number,
    parentExpanded: boolean,
  ) => {
    for (const menu of menus) {
      const hasChildren = !!(menu.children && menu.children.length > 0);
      const isExpanded = expandedMenuIds.value.has(menu.id);

      // 只有父级展开时才显示子菜单
      if (parentExpanded) {
        result.push({ menu, level, hasChildren, isExpanded });
      }

      // 如果有子菜单且已展开，继续遍历
      if (hasChildren && isExpanded) {
        flatten(menu.children!, level + 1, true);
      }
    }
  };
  flatten(menuTreeData.value, 0, true);
  return result;
});

// 切换菜单展开/折叠状态
const toggleExpand = (menuId: string, event: Event) => {
  event.stopPropagation();
  if (expandedMenuIds.value.has(menuId)) {
    expandedMenuIds.value.delete(menuId);
  } else {
    expandedMenuIds.value.add(menuId);
  }
};

// 初始化时展开所有父级菜单
const expandAllParents = () => {
  const expand = (menus: MenuItem[]) => {
    for (const menu of menus) {
      if (menu.children && menu.children.length > 0) {
        expandedMenuIds.value.add(menu.id);
        expand(menu.children);
      }
    }
  };
  expand(menuTreeData.value);
};

// 判断菜单是否被选中（多选模式）
const isMenuSelected = (menuId: string): boolean => {
  if (props.multiple) {
    return selectedMenus.value.some((m) => m.id === menuId);
  }
  return selectedMenu.value?.id === menuId;
};

// 获取菜单的所有后代ID
const getAllDescendantIds = (menu: MenuItem): string[] => {
  const ids: string[] = [];
  if (menu.children && menu.children.length > 0) {
    for (const child of menu.children) {
      ids.push(child.id);
      ids.push(...getAllDescendantIds(child));
    }
  }
  return ids;
};

// 获取菜单的所有后代菜单
const getAllDescendants = (menu: MenuItem): MenuItem[] => {
  const descendants: MenuItem[] = [];
  if (menu.children && menu.children.length > 0) {
    for (const child of menu.children) {
      descendants.push(child);
      descendants.push(...getAllDescendants(child));
    }
  }
  return descendants;
};

// 判断菜单是否为半选中状态（部分子菜单被选中）
const isMenuIndeterminate = (menu: MenuItem): boolean => {
  if (!props.multiple || !menu.children || menu.children.length === 0) {
    return false;
  }
  const descendantIds = getAllDescendantIds(menu);
  const selectedIds = new Set(selectedMenus.value.map((m) => m.id));
  const selectedCount = descendantIds.filter((id) =>
    selectedIds.has(id),
  ).length;
  // 部分选中（不是全部也不是零个）
  return selectedCount > 0 && selectedCount < descendantIds.length;
};

// 判断菜单是否全选（所有子菜单都被选中）
const isMenuAllSelected = (menu: MenuItem): boolean => {
  if (!props.multiple) {
    return selectedMenu.value?.id === menu.id;
  }
  if (!menu.children || menu.children.length === 0) {
    return selectedMenus.value.some((m) => m.id === menu.id);
  }
  const descendantIds = getAllDescendantIds(menu);
  const selectedIds = new Set(selectedMenus.value.map((m) => m.id));
  return descendantIds.every((id) => selectedIds.has(id));
};

// 打开弹窗
const openDialog = async () => {
  if (props.disabled) return;
  dialogVisible.value = true;
  await loadMenuTree();
};

// 选择菜单（支持级联选择）
const selectMenu = (menu: MenuItem, event?: Event) => {
  if (event) {
    event.stopPropagation();
  }

  if (props.multiple) {
    // 多选模式：支持级联选择
    const isCurrentlySelected = selectedMenus.value.some(
      (m) => m.id === menu.id,
    );
    const descendants = getAllDescendants(menu);

    if (isCurrentlySelected || isMenuAllSelected(menu)) {
      // 取消选择：移除当前菜单和所有后代
      const idsToRemove = new Set([menu.id, ...descendants.map((d) => d.id)]);
      selectedMenus.value = selectedMenus.value.filter(
        (m) => !idsToRemove.has(m.id),
      );
    } else {
      // 选中：添加当前菜单和所有后代
      const existingIds = new Set(selectedMenus.value.map((m) => m.id));
      const menusToAdd = [menu, ...descendants].filter(
        (m) => !existingIds.has(m.id),
      );
      selectedMenus.value.push(...menusToAdd);
    }

    const ids = selectedMenus.value.map((m) => m.id);
    emit('update:modelValue', ids.length > 0 ? ids : null);
    emit(
      'change',
      selectedMenus.value.length > 0 ? [...selectedMenus.value] : null,
    );
  } else {
    // 单选模式
    selectedMenu.value = menu;
    emit('update:modelValue', menu.id);
    emit('change', menu);
    dialogVisible.value = false;
  }
  emit('select', menu);
};

// 移除选中的菜单（多选模式）
const removeMenu = (menuId: string) => {
  const index = selectedMenus.value.findIndex((m) => m.id === menuId);
  if (index !== -1) {
    selectedMenus.value.splice(index, 1);
    const ids = selectedMenus.value.map((m) => m.id);
    emit('update:modelValue', ids.length > 0 ? ids : null);
    emit(
      'change',
      selectedMenus.value.length > 0 ? [...selectedMenus.value] : null,
    );
  }
};

// 暴露方法供外部调用
defineExpose({
  open: openDialog,
  close: () => {
    dialogVisible.value = false;
  },
  loadMenuTree,
});

// 清除选择
const clearSelection = () => {
  if (props.multiple) {
    selectedMenus.value = [];
  } else {
    selectedMenu.value = null;
  }
  emit('update:modelValue', null);
  emit('change', null);
};

// 计算 ElSelect 显示的选项（处理加载中状态）
const displayOptions = computed(() => {
  if (props.multiple) {
    // 多选模式
    if (selectedMenus.value.length > 0) {
      return selectedMenus.value.map((m) => ({
        id: m.id,
        label: m.title || m.name,
      }));
    }
    // 有值但还在加载中
    if (
      Array.isArray(props.modelValue) &&
      props.modelValue.length > 0 &&
      !menuTreeLoaded.value
    ) {
      return props.modelValue.map((id) => ({
        id,
        label: $t('common.loading') || 'Loading...',
      }));
    }
    return [];
  } else {
    // 单选模式
    if (selectedMenu.value) {
      return [
        {
          id: selectedMenu.value.id,
          label: selectedMenu.value.title || selectedMenu.value.name,
        },
      ];
    }
    // 有值但还在加载中
    if (
      typeof props.modelValue === 'string' &&
      props.modelValue &&
      !menuTreeLoaded.value
    ) {
      return [
        {
          id: props.modelValue,
          label: $t('common.loading') || 'Loading...',
        },
      ];
    }
    return [];
  }
});

// 监听 modelValue 变化，更新选中菜单
watch(
  () => props.modelValue,
  async (newVal) => {
    if (newVal && !menuTreeLoaded.value) {
      await loadMenuTree();
    }

    if (props.multiple) {
      // 多选模式
      selectedMenus.value =
        Array.isArray(newVal) && newVal.length > 0 && menuTreeLoaded.value
          ? newVal
              .map((id) => findMenuInTree(id, menuTreeData.value))
              .filter((m): m is MenuItem => m !== null)
          : [];
    } else {
      // 单选模式
      if (typeof newVal === 'string' && menuTreeLoaded.value) {
        selectedMenu.value = findMenuInTree(newVal, menuTreeData.value);
      } else if (!newVal) {
        selectedMenu.value = null;
      }
    }
  },
  { immediate: true },
);
</script>

<template>
  <!-- Popup 模式（只有弹窗，无触发器） -->
  <template v-if="mode === 'popup'">
    <ZqDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :width="dialogWidth"
      append-to-body
      :show-footer="false"
    >
      <div v-if="menuTreeLoaded" class="h-[400px]">
        <ElScrollbar height="380px">
          <div class="space-y-1 pr-2">
            <div
              v-for="item in flattenedMenuList"
              :key="item.menu.id"
              class="hover:bg-primary/10 flex cursor-pointer items-center gap-1 rounded px-2 py-2 transition-colors"
              :class="{
                'bg-primary/10': isMenuSelected(item.menu.id),
              }"
              :style="{ paddingLeft: `${8 + item.level * 16}px` }"
              @click="selectMenu(item.menu)"
            >
              <!-- 折叠/展开按钮 -->
              <span
                v-if="item.hasChildren"
                class="flex h-5 w-5 shrink-0 cursor-pointer items-center justify-center rounded hover:bg-gray-200 dark:hover:bg-gray-700"
                @click="toggleExpand(item.menu.id, $event)"
              >
                <ChevronDown
                  v-if="item.isExpanded"
                  class="h-4 w-4 text-gray-400"
                />
                <ChevronRight v-else class="h-4 w-4 text-gray-400" />
              </span>
              <span v-else class="w-5 shrink-0"></span>

              <IconifyIcon
                v-if="item.menu.icon"
                :icon="item.menu.icon"
                class="h-4 w-4 shrink-0 text-gray-500"
              />
              <span class="flex-1 truncate text-sm">{{ item.menu.title }}</span>
              <span
                v-if="multiple && isMenuSelected(item.menu.id)"
                class="text-primary shrink-0 text-sm"
                >✓</span
              >
            </div>
            <div
              v-if="flattenedMenuList.length === 0"
              class="py-8 text-center text-sm text-gray-400"
            >
              暂无可用菜单
            </div>
          </div>
        </ElScrollbar>
      </div>
      <div
        v-else
        class="flex h-[400px] items-center justify-center text-gray-400"
      >
        加载中...
      </div>
    </ZqDialog>
  </template>

  <!-- Dialog 模式（使用 ElSelect 作为触发器） -->
  <template v-else>
    <div class="zq-menu-selector w-full">
      <ElSelect
        :model-value="
          multiple
            ? displayOptions.map((o) => o.id)
            : displayOptions[0]?.id || ''
        "
        :placeholder="placeholder"
        :disabled="disabled"
        :clearable="clearable"
        :multiple="multiple"
        collapse-tags
        collapse-tags-tooltip
        class="w-full"
        popper-class="zq-menu-selector-hidden-dropdown"
        @click="openDialog"
        @clear="clearSelection"
        @remove-tag="removeMenu"
      >
        <ElOption
          v-for="opt in displayOptions"
          :key="opt.id"
          :value="opt.id"
          :label="opt.label"
        />
      </ElSelect>
    </div>

    <!-- 菜单选择弹窗 -->
    <ZqDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      append-to-body
    >
      <div class="menu-selector-content">
        <!-- 左侧：菜单树 -->
        <div class="menu-selector-left">
          <div v-if="menuTreeLoaded" class="menu-tree-container">
            <ElScrollbar class="menu-tree-scroll">
              <div class="menu-tree-body">
                <div
                  v-for="item in flattenedMenuList"
                  :key="item.menu.id"
                  class="menu-item"
                  :class="{
                    'menu-item--selected':
                      isMenuSelected(item.menu.id) ||
                      isMenuAllSelected(item.menu),
                  }"
                  :style="{ paddingLeft: `${12 + item.level * 16}px` }"
                  @click="selectMenu(item.menu, $event)"
                >
                  <!-- 折叠/展开按钮 -->
                  <span
                    v-if="item.hasChildren"
                    class="menu-expand-btn"
                    @click="toggleExpand(item.menu.id, $event)"
                  >
                    <ChevronDown
                      v-if="item.isExpanded"
                      class="size-4 text-gray-400"
                    />
                    <ChevronRight v-else class="size-4 text-gray-400" />
                  </span>
                  <span v-else class="menu-expand-placeholder"></span>

                  <!-- 多选模式下显示 checkbox -->
                  <ElCheckbox
                    v-if="multiple"
                    :model-value="isMenuAllSelected(item.menu)"
                    :indeterminate="isMenuIndeterminate(item.menu)"
                    class="shrink-0"
                    @click.stop
                    @change="() => selectMenu(item.menu)"
                  />

                  <IconifyIcon
                    v-if="item.menu.icon"
                    :icon="item.menu.icon"
                    class="size-4 shrink-0 text-gray-500"
                  />
                  <span class="menu-item-title">{{ item.menu.title }}</span>
                </div>
                <div v-if="flattenedMenuList.length === 0" class="menu-empty">
                  {{ $t('common.noData') || '暂无可用菜单' }}
                </div>
              </div>
            </ElScrollbar>
          </div>
          <div v-else class="menu-loading">
            {{ $t('common.loading') || '加载中...' }}
          </div>
        </div>

        <!-- 右侧：已选值 -->
        <div class="menu-selector-right">
          <div class="right-header">
            <span class="right-title">
              {{ $t('common.selected') || '已选择' }}
              <span
                v-if="multiple && selectedMenus.length > 0"
                class="right-count"
              >
                ({{ selectedMenus.length }})
              </span>
              <span v-else-if="!multiple && selectedMenu" class="right-count">
                (1)
              </span>
            </span>
            <ElButton
              v-if="
                (multiple && selectedMenus.length > 0) ||
                (!multiple && selectedMenu)
              "
              link
              type="danger"
              size="small"
              @click="clearSelection"
            >
              {{ $t('common.clear') || '清空' }}
            </ElButton>
          </div>
          <ElScrollbar class="right-scroll">
            <div
              v-if="
                (multiple && selectedMenus.length === 0) ||
                (!multiple && !selectedMenu)
              "
              class="right-empty"
            >
              <ElEmpty
                :image-size="64"
                :description="$t('common.noData') || '暂无数据'"
              />
            </div>
            <div v-else class="right-list">
              <!-- 多选模式 -->
              <template v-if="multiple">
                <div
                  v-for="menu in selectedMenus"
                  :key="menu.id"
                  class="right-item"
                >
                  <IconifyIcon
                    v-if="menu.icon"
                    :icon="menu.icon"
                    class="size-4 shrink-0 text-gray-500"
                  />
                  <span
                    class="right-item-name"
                    :title="menu.title || menu.name"
                  >
                    {{ menu.title || menu.name }}
                  </span>
                  <ElButton
                    link
                    type="danger"
                    size="small"
                    class="right-item-remove"
                    @click="removeMenu(menu.id)"
                  >
                    <X class="size-3.5" />
                  </ElButton>
                </div>
              </template>
              <!-- 单选模式 -->
              <template v-else-if="selectedMenu">
                <div class="right-item">
                  <IconifyIcon
                    v-if="selectedMenu.icon"
                    :icon="selectedMenu.icon"
                    class="size-4 shrink-0 text-gray-500"
                  />
                  <span
                    class="right-item-name"
                    :title="selectedMenu.title || selectedMenu.name"
                  >
                    {{ selectedMenu.title || selectedMenu.name }}
                  </span>
                  <ElButton
                    link
                    type="danger"
                    size="small"
                    class="right-item-remove"
                    @click="clearSelection"
                  >
                    <X class="size-3.5" />
                  </ElButton>
                </div>
              </template>
            </div>
          </ElScrollbar>
        </div>
      </div>

      <template #footer>
        <div class="modal-footer">
          <ElButton @click="dialogVisible = false">
            {{ $t('common.cancel') || '取消' }}
          </ElButton>
          <ElButton type="primary" @click="dialogVisible = false">
            {{ $t('common.confirm') || '确认' }}
          </ElButton>
        </div>
      </template>
    </ZqDialog>
  </template>
</template>

<style lang="scss" scoped>
.zq-menu-selector :deep(.el-select__wrapper) {
  cursor: pointer;
}

.menu-selector-content {
  display: flex;
  gap: 0;
  height: 500px;
  overflow: hidden;
  background-color: hsl(var(--background));
  box-shadow: 0 1px 3px hsl(var(--border) / 12%);
}

.menu-selector-left {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);

  .menu-tree-container {
    display: flex;
    flex: 1;
    flex-direction: column;
    overflow: hidden;
  }

  .menu-tree-scroll {
    flex: 1;
    overflow-y: auto;
  }

  .menu-tree-body {
    padding: 8px;
  }

  .menu-item {
    display: flex;
    gap: 4px;
    align-items: center;
    height: 36px;
    padding-right: 12px;
    cursor: pointer;
    border-radius: 6px;
    transition: all 0.15s ease;

    &:hover {
      background-color: var(--el-fill-color-light);
    }

    &--selected {
      background-color: var(--el-color-primary-light-9);

      .menu-item-title {
        font-weight: 500;
        color: var(--el-color-primary);
      }
    }
  }

  .menu-expand-btn {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    cursor: pointer;
    border-radius: 4px;

    &:hover {
      background-color: var(--el-fill-color);
    }
  }

  .menu-expand-placeholder {
    flex-shrink: 0;
    width: 20px;
  }

  .menu-item-title {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    font-size: 14px;
    text-overflow: ellipsis;
    white-space: nowrap;
    transition: color 0.15s ease;
  }

  .menu-empty {
    padding: 40px 0;
    font-size: 14px;
    color: hsl(var(--muted-foreground));
    text-align: center;
  }

  .menu-loading {
    display: flex;
    flex: 1;
    align-items: center;
    justify-content: center;
    color: hsl(var(--muted-foreground));
  }
}

.menu-selector-right {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  width: 280px;
  margin-left: 12px;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);

  .right-header {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px 8px;

    .right-title {
      font-size: 13px;
      font-weight: 500;
      color: hsl(var(--foreground));

      .right-count {
        font-weight: 400;
        color: hsl(var(--muted-foreground));
      }
    }
  }

  .right-scroll {
    flex: 1;
    overflow-y: auto;
  }

  .right-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 40px 0;
  }

  .right-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 4px 8px;
  }

  .right-item {
    display: flex;
    gap: 8px;
    align-items: center;
    justify-content: space-between;
    padding: 6px 8px;
    border-radius: 6px;
    transition: background-color 0.15s ease;

    &:hover {
      background-color: var(--el-fill-color-light);

      .right-item-remove {
        opacity: 1;
      }
    }
  }

  .right-item-name {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    font-size: 13px;
    color: hsl(var(--foreground));
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .right-item-remove {
    flex-shrink: 0;
    opacity: 0;
    transition: opacity 0.15s ease;
  }
}

.modal-footer {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}
</style>

<style>
/* 隐藏下拉菜单，因为我们使用弹窗选择 */
.zq-menu-selector-hidden-dropdown {
  display: none !important;
}
</style>
