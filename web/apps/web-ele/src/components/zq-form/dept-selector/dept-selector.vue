<script lang="ts" setup>
import type { DeptSelectorEmits, DeptSelectorProps } from './types';

import type { DeptTreeNode } from '#/api/core/dept';

import { computed, nextTick, ref, useAttrs, watch } from 'vue';

import { FolderTree, Search, X } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElEmpty,
  ElInput,
  ElOption,
  ElScrollbar,
  ElSelect,
  ElSkeleton,
  ElSkeletonItem,
  ElTree,
} from 'element-plus';

import { getDeptsByIds, getDeptTreeApi } from '#/api/core/dept';
import { ZqDialog } from '#/components/zq-dialog';

defineOptions({
  name: 'DeptSelector',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<Props>(), {
  multiple: false,
  placeholder: () => $t('ui.placeholder.select') || 'Please select',
  disabled: false,
  clearable: true,
  filterable: true,
});

const emit = defineEmits<DeptSelectorEmits>();

interface Props extends DeptSelectorProps {}

const attrs = useAttrs();

// ---- 状态 ----
const modalVisible = ref(false);
const treeData = ref<DeptTreeNode[]>([]);
const treeLoading = ref(false);
const treeLoaded = ref(false);
const searchText = ref('');
const treeRef = ref<InstanceType<typeof ElTree> | null>(null);

// 已确认的选中 ID
const selectedIds = ref<Set<string>>(new Set());
// 弹窗内临时选中 ID（未确认前）
const tempSelectedIds = ref<Set<string>>(new Set());
// 已选部门的名称缓存 { id -> 路径显示名 }
const deptNameCache = ref<Map<string, string>>(new Map());
// 初始值名称加载中
const initLoading = ref(false);

// ---- 工具函数 ----

// 从树中递归查找节点
const findNodeInTree = (
  nodes: DeptTreeNode[],
  id: string,
): DeptTreeNode | null => {
  for (const node of nodes) {
    if (node.id === id) return node;
    if (node.children) {
      const found = findNodeInTree(node.children, id);
      if (found) return found;
    }
  }
  return null;
};

// 构建部门路径（从根到目标节点）
const buildDeptPath = (id: string): string => {
  const parentMap = new Map<string, null | string>();
  const nameMap = new Map<string, string>();

  const walk = (nodes: DeptTreeNode[], parentId: null | string) => {
    for (const node of nodes) {
      parentMap.set(node.id, parentId);
      nameMap.set(node.id, node.name);
      if (node.children) walk(node.children, node.id);
    }
  };
  walk(treeData.value, null);

  const parts: string[] = [];
  let cur: null | string | undefined = id;
  while (cur) {
    const name = nameMap.get(cur);
    if (name) parts.unshift(name);
    cur = parentMap.get(cur);
  }
  return parts.join(' / ');
};

// 更新名称缓存
const refreshNameCache = (ids: Iterable<string>) => {
  for (const id of ids) {
    if (treeData.value.length > 0) {
      const path = buildDeptPath(id);
      if (path) {
        deptNameCache.value.set(id, path);
      }
    }
  }
};

// ---- 显示值 ----

const displayValue = computed({
  get() {
    if (selectedIds.value.size === 0) return undefined;
    return props.multiple ? [...selectedIds.value] : [...selectedIds.value][0];
  },
  set(_v) {
    // ElSelect 内部会尝试修改，忽略
  },
});

const selectedDeptsWithPath = computed(() => {
  return [...selectedIds.value].map((id) => ({
    id,
    display: initLoading.value
      ? $t('common.loading') || 'Loading...'
      : deptNameCache.value.get(id) || id,
  }));
});

const tempSelectedDeptsWithPath = computed(() => {
  return [...tempSelectedIds.value].map((id) => ({
    id,
    display: deptNameCache.value.get(id) || id,
  }));
});

// ---- 树数据加载 ----

const loadTree = async () => {
  if (treeLoaded.value) return;
  try {
    treeLoading.value = true;
    const result = await getDeptTreeApi();
    treeData.value = Array.isArray(result) ? result : [];
    treeLoaded.value = true;
    // 加载完树后刷新所有已选 ID 的名称
    refreshNameCache(selectedIds.value);
  } catch (error) {
    console.error('Failed to load dept tree:', error);
  } finally {
    treeLoading.value = false;
  }
};

// 根据 ID 列表加载部门名称（用于初始化时树还没加载的情况）
const loadNamesByIds = async (ids: string[]) => {
  if (ids.length === 0) return;
  // 过滤掉已有缓存的
  const missing = ids.filter((id) => !deptNameCache.value.has(id));
  if (missing.length === 0) return;

  try {
    initLoading.value = true;
    const result = await getDeptsByIds(missing);
    if (result && result.length > 0) {
      // getDeptsByIds 返回的是树形结构，递归提取所有节点名称
      const extractNames = (nodes: DeptTreeNode[], parentPath: string = '') => {
        for (const node of nodes) {
          const currentPath = parentPath
            ? `${parentPath} / ${node.name}`
            : node.name;
          // 只缓存目标 ID
          if (missing.includes(node.id)) {
            deptNameCache.value.set(node.id, currentPath);
          }
          if (node.children) {
            extractNames(node.children, currentPath);
          }
        }
      };
      extractNames(result);
    }
  } catch (error) {
    console.error('Failed to load dept names:', error);
  } finally {
    initLoading.value = false;
  }
};

// ---- ElTree 搜索过滤 ----

const filterNode = (value: string, data: DeptTreeNode): boolean => {
  if (!value) return true;
  return data.name.toLowerCase().includes(value.toLowerCase());
};

watch(searchText, (val) => {
  treeRef.value?.filter(val);
});

// ---- 节点点击选择 ----

const handleNodeClick = (data: DeptTreeNode) => {
  const id = data.id;
  if (props.multiple) {
    if (tempSelectedIds.value.has(id)) {
      tempSelectedIds.value.delete(id);
    } else {
      tempSelectedIds.value.add(id);
    }
    // 触发响应式更新
    tempSelectedIds.value = new Set(tempSelectedIds.value);
  } else {
    tempSelectedIds.value = new Set([id]);
  }
  // 确保名称缓存
  if (!deptNameCache.value.has(id)) {
    const path = buildDeptPath(id);
    if (path) deptNameCache.value.set(id, path);
  }
};

// ---- 弹窗操作 ----

const openModal = async () => {
  if (props.disabled) return;
  modalVisible.value = true;
};

const handleModalOpened = async () => {
  tempSelectedIds.value = new Set(selectedIds.value);
  searchText.value = '';
  await loadTree();
  // 树加载完后展开已选节点的父级
  await nextTick();
  for (const id of tempSelectedIds.value) {
    const node = findNodeInTree(treeData.value, id);
    if (node) {
      treeRef.value?.setCurrentKey(id);
    }
  }
};

const handleConfirm = () => {
  selectedIds.value = new Set(tempSelectedIds.value);
  refreshNameCache(selectedIds.value);

  const value = props.multiple
    ? [...selectedIds.value]
    : selectedIds.value.size > 0
      ? [...selectedIds.value][0]
      : '';

  emit('update:modelValue', value);
  emit('change', value);
  modalVisible.value = false;
};

const handleClear = (e?: MouseEvent) => {
  if (e) e.stopPropagation();
  tempSelectedIds.value.clear();
  selectedIds.value.clear();
  const emptyValue = props.multiple ? [] : '';
  emit('update:modelValue', emptyValue);
  emit('change', emptyValue);
};

const handleRemoveTag = (deptId: string) => {
  selectedIds.value.delete(deptId);
  const value = props.multiple ? [...selectedIds.value] : '';
  emit('update:modelValue', value);
  emit('change', value);
};

const handleRemoveTempTag = (deptId: string) => {
  tempSelectedIds.value.delete(deptId);
  tempSelectedIds.value = new Set(tempSelectedIds.value);
};

// ---- 外部 modelValue 同步 ----

watch(
  () => props.modelValue,
  async (newValue) => {
    selectedIds.value.clear();
    if (Array.isArray(newValue)) {
      newValue.forEach((v) => selectedIds.value.add(v));
    } else if (newValue) {
      selectedIds.value.add(newValue);
    }

    if (modalVisible.value) {
      tempSelectedIds.value = new Set(selectedIds.value);
    }

    // 确保有显示名称
    const ids = [...selectedIds.value];
    if (ids.length > 0) {
      if (treeLoaded.value) {
        refreshNameCache(ids);
      } else {
        await loadNamesByIds(ids);
      }
    }
  },
  { immediate: true },
);

// ---- 自定义节点样式类 ----

const getNodeClass = (data: DeptTreeNode): string => {
  return tempSelectedIds.value.has(data.id) ? 'dept-tree-node--selected' : '';
};

defineExpose({
  openModal,
});
</script>

<template>
  <div class="dept-selector">
    <!-- 选择框 -->
    <div
      class="dept-selector-input"
      :class="{ disabled, loading: initLoading }"
    >
      <ElSelect
        v-bind="attrs"
        v-model="displayValue"
        :placeholder="
          initLoading ? $t('common.loading') || 'Loading...' : placeholder
        "
        :disabled="disabled || initLoading"
        :clearable="clearable && selectedIds.size > 0"
        :multiple="multiple"
        :suffix-icon="FolderTree"
        readonly
        @click="openModal"
        @clear="() => handleClear()"
        @remove-tag="handleRemoveTag"
      >
        <ElOption
          v-for="item in selectedDeptsWithPath"
          :key="item.id"
          :label="item.display"
          :value="item.id"
        />
      </ElSelect>

      <!-- Loading 提示 -->
      <!-- <div v-if="initLoading" class="loading-indicator">
        <Loader class="size-4 animate-spin" />
        <span class="ml-2 text-xs text-gray-500">{{
          $t('common.loading') || 'Loading...'
        }}</span>
      </div> -->
    </div>

    <!-- Modal -->
    <ZqDialog
      v-model="modalVisible"
      :title="$t('system.user.selectDept') || 'Select Departments'"
      width="45%"
      :show-fullscreen-button="false"
      @opened="handleModalOpened"
    >
      <div class="dept-selector-content">
        <!-- 左侧：搜索 + 部门树 -->
        <div class="dept-selector-left">
          <div v-if="filterable" class="tree-search">
            <ElInput
              v-model="searchText"
              :placeholder="$t('common.search') || 'Search'"
              clearable
              :prefix-icon="Search"
            />
          </div>
          <ElScrollbar class="tree-scroll">
            <ElSkeleton :loading="treeLoading" animated :count="8">
              <template #template>
                <div class="tree-skeleton">
                  <div v-for="i in 8" :key="i" class="dept-skeleton-item">
                    <ElSkeletonItem
                      variant="text"
                      style="width: 100%; height: 36px; margin: 4px 0"
                    />
                  </div>
                </div>
              </template>
              <template #default>
                <div class="tree-body">
                  <ElEmpty
                    v-if="treeData.length === 0"
                    :description="$t('common.noData') || 'No Data'"
                  />
                  <ElTree
                    v-else
                    ref="treeRef"
                    :data="treeData"
                    node-key="id"
                    :props="{ label: 'name', children: 'children' }"
                    :filter-node-method="filterNode as any"
                    :default-expand-all="false"
                    :expand-on-click-node="false"
                    highlight-current
                    @node-click="handleNodeClick"
                  >
                    <template #default="{ data }">
                      <span class="dept-tree-node" :class="getNodeClass(data)">
                        {{ data.name }}
                      </span>
                    </template>
                  </ElTree>
                </div>
              </template>
            </ElSkeleton>
          </ElScrollbar>
        </div>

        <!-- 右侧：已选值 -->
        <div class="dept-selector-right">
          <div class="right-header">
            <span class="right-title">
              {{ $t('common.selected') || 'Selected' }}
              <span v-if="tempSelectedIds.size > 0" class="right-count">
                ({{ tempSelectedIds.size }})
              </span>
            </span>
            <ElButton
              v-if="tempSelectedIds.size > 0"
              link
              type="danger"
              size="small"
              @click="tempSelectedIds = new Set()"
            >
              {{ $t('common.clear') || 'Clear' }}
            </ElButton>
          </div>
          <ElScrollbar class="right-scroll">
            <div
              v-if="tempSelectedDeptsWithPath.length === 0"
              class="right-empty"
            >
              <ElEmpty
                :image-size="64"
                :description="$t('common.noData') || 'No Data'"
              />
            </div>
            <div v-else class="right-list">
              <div
                v-for="item in tempSelectedDeptsWithPath"
                :key="item.id"
                class="right-item"
              >
                <span class="right-item-name" :title="item.display">
                  {{ item.display }}
                </span>
                <ElButton
                  link
                  type="danger"
                  size="small"
                  class="right-item-remove"
                  @click="handleRemoveTempTag(item.id)"
                >
                  <X class="size-3.5" />
                </ElButton>
              </div>
            </div>
          </ElScrollbar>
        </div>
      </div>

      <template #footer>
        <div class="modal-footer">
          <ElButton @click="modalVisible = false">
            {{ $t('common.cancel') || 'Cancel' }}
          </ElButton>
          <ElButton type="primary" @click="handleConfirm">
            {{ $t('common.confirm') || 'Confirm' }}
          </ElButton>
        </div>
      </template>
    </ZqDialog>
  </div>
</template>

<style lang="scss" scoped>
.dept-selector {
  width: 100%;

  &-input {
    position: relative;
    cursor: pointer;

    &.disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }

    &.loading {
      cursor: wait;
    }

    :deep(.el-input) {
      &.is-disabled {
        background-color: var(--background-deep, #f5f7fa);
      }
    }

    .loading-indicator {
      position: absolute;
      top: 50%;
      right: 10px;
      z-index: 10;
      display: flex;
      gap: 6px;
      align-items: center;
      font-size: 12px;
      color: var(--el-color-info);
      pointer-events: none;
      transform: translateY(-50%);

      .size-4 {
        width: 16px;
        height: 16px;
      }
    }
  }

  &-content {
    display: flex;
    gap: 0;
    height: 500px;
    overflow: hidden;
    background-color: hsl(var(--background));
    box-shadow: 0 1px 3px hsl(var(--border) / 12%);
  }

  &-left {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-width: 0;
    // border-right: 1px solid hsl(var(--border));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);

    .tree-search {
      flex-shrink: 0;
      padding: 12px 12px 8px;
    }

    .tree-scroll {
      flex: 1;
      overflow-y: auto;
    }

    .tree-skeleton,
    .tree-body {
      padding: 4px 8px;
    }

    :deep(.el-tree) {
      --el-tree-node-hover-bg-color: var(--el-fill-color-light);

      background: transparent;

      .el-tree-node__content {
        height: 36px;
        border-radius: 6px;
      }

      .el-tree-node__expand-icon {
        font-size: 14px;
      }
    }

    .dept-tree-node {
      overflow: hidden;
      font-size: 14px;
      text-overflow: ellipsis;
      white-space: nowrap;
      transition: color 0.2s ease;

      &--selected {
        font-weight: 500;
        color: var(--el-color-primary);
      }
    }
  }

  &-right {
    display: flex;
    flex-direction: column;
    width: 320px;
    flex-shrink: 0;
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    margin-left: 12px;
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
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 6px 8px;
      border-radius: 6px;
      transition: background-color 0.15s ease;

      &:hover {
        background-color: var(--el-fill-color-light);

        .right-item-remove {
          opacity: 1;
        }
      }

      &-name {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        font-size: 13px;
        color: hsl(var(--foreground));
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      &-remove {
        flex-shrink: 0;
        opacity: 0;
        transition: opacity 0.15s ease;
      }
    }
  }
}

.modal-footer {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}

.dept-skeleton-item {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  width: 100%;
  padding: 4px 8px;
}
</style>
