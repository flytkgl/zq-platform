<script lang="ts" setup>
import type { DeptTreeNode } from '#/api/core/dept';

import { computed, onMounted, ref, watch } from 'vue';

import { IconifyIcon, Loader, Plus, Search } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElSkeleton,
  ElSkeletonItem,
  ElTooltip,
} from 'element-plus';

import {
  deleteDeptApi,
  getDeptByParentApi,
  getDeptDetailApi,
  searchDeptApi,
} from '#/api/core/dept';

import DeptFormModal from './dept-form-modal.vue';

const emit = defineEmits<{
  select: [deptIds: string[] | undefined, hasChildren?: boolean];
}>();

const treeData = ref<DeptTreeNode[]>([]);
const loading = ref(false);
const selectedDeptId = ref<string>();
const searchKeyword = ref<string>('');
const hoveredDeptId = ref<string>();
const expandedDeptIds = ref<Set<string>>(new Set());
const loadingDeptIds = ref<Set<string>>(new Set());
const searchResults = ref<DeptTreeNode[]>([]);
const isSearching = ref(false);
const currentOperatingDeptId = ref<null | string>(null);
const currentOperatingParentId = ref<null | string>(null);
const deptFormModalRef = ref<InstanceType<typeof DeptFormModal>>();

/**
 * 加载顶级部门数据（只加载第一级）
 */
async function fetchDeptList() {
  try {
    loading.value = true;
    // 只获取顶级部门
    const data = await getDeptByParentApi();
    treeData.value = Array.isArray(data) ? data : [];

    // 自动选中第一个部门
    if (treeData.value.length > 0 && !selectedDeptId.value) {
      const firstDept = treeData.value.at(0);
      if (firstDept) {
        selectedDeptId.value = firstDept.id;
        emit('select', [firstDept.id], hasChildren(firstDept));
      }
    }
  } finally {
    loading.value = false;
  }
}

/**
 * 加载子部门（懒加载）
 */
async function loadChildren(parentId: string) {
  try {
    loadingDeptIds.value.add(parentId);
    const data = await getDeptByParentApi(parentId);

    // 更新树数据中的子部门
    function updateNodeChildren(nodes: DeptTreeNode[], targetId: string) {
      for (const node of nodes) {
        if (node.id === targetId) {
          node.children = Array.isArray(data) ? data : [];
          return true;
        }
        if (
          node.children &&
          node.children.length > 0 &&
          updateNodeChildren(node.children, targetId)
        ) {
          return true;
        }
      }
      return false;
    }

    updateNodeChildren(treeData.value, parentId);
  } catch {
    ElMessage.error($t('ui.actionMessage.loadError'));
  } finally {
    loadingDeptIds.value.delete(parentId);
  }
}

/**
 * 切换节点展开/折叠
 */
async function toggleNodeExpanded(dept: DeptTreeNode) {
  if (expandedDeptIds.value.has(dept.id)) {
    expandedDeptIds.value.delete(dept.id);
  } else {
    expandedDeptIds.value.add(dept.id);

    // 如果子部门未加载，则加载
    if (!dept.children || dept.children.length === 0) {
      await loadChildren(dept.id);
    }
  }
}

/**
 * 选择部门
 */
function onDeptSelect(dept: DeptTreeNode) {
  selectedDeptId.value = dept.id;
  emit('select', [dept.id], hasChildren(dept));
}

/**
 * 添加部门
 */
function onAddDept() {
  currentOperatingDeptId.value = null;
  currentOperatingParentId.value = null;
  deptFormModalRef.value?.open();
}

/**
 * 编辑部门
 */
function onEditDept(dept: DeptTreeNode) {
  currentOperatingDeptId.value = dept.id;
  deptFormModalRef.value?.open(dept);
}

/**
 * 在当前部门下新建子部门
 */
function onAddChildDept(dept: DeptTreeNode) {
  currentOperatingDeptId.value = null;
  currentOperatingParentId.value = dept.id;
  deptFormModalRef.value?.open({ parent_id: dept.id } as any);
}

/**
 * 删除部门
 */
async function onDeleteDept(dept: DeptTreeNode) {
  ElMessageBox.confirm(
    $t('ui.actionMessage.deleteConfirm', [dept.name]),
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
        await deleteDeptApi(dept.id);
        ElMessage.success($t('ui.actionMessage.deleteSuccess', [dept.name]));
        fetchDeptList();
      } catch {
        ElMessage.error($t('ui.actionMessage.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

/**
 * 在树中查找并更新节点数据
 */
function updateNodeInTree(
  nodes: DeptTreeNode[],
  deptId: string,
  updatedData: Partial<DeptTreeNode>,
): boolean {
  for (const node of nodes) {
    if (node.id === deptId) {
      // 找到节点，更新数据（保留 children）
      Object.assign(node, { ...updatedData, children: node.children });
      return true;
    }
    if (
      node.children &&
      node.children.length > 0 &&
      updateNodeInTree(node.children, deptId, updatedData)
    ) {
      return true;
    }
  }
  return false;
}

/**
 * 表单成功回调
 */
async function onDeptFormSuccess(formData?: any) {
  const isUpdate = currentOperatingDeptId.value !== null;

  try {
    if (isUpdate) {
      // 修改操作：只刷新当前节点数据
      const updatedDept = await getDeptDetailApi(currentOperatingDeptId.value!);
      updateNodeInTree(
        treeData.value,
        currentOperatingDeptId.value!,
        updatedDept,
      );
      ElMessage.success($t('dept.updateSuccess'));
    } else {
      // 新增操作：刷新父节点的子列表
      // 优先使用表单提交的parent_id，其次使用记录的parent_id
      const parentId = formData?.parent_id || currentOperatingParentId.value;

      if (parentId) {
        // 如果父节点已展开，重新加载其子部门
        if (expandedDeptIds.value.has(parentId)) {
          await loadChildren(parentId);
        }
      } else {
        // 顶级部门，重新加载顶级列表
        await fetchDeptList();
      }
    }
  } catch (error) {
    console.error('刷新部门数据失败:', error);
    // 失败时重新加载整个树
    await fetchDeptList();
  } finally {
    // 重置操作标记
    currentOperatingDeptId.value = null;
    currentOperatingParentId.value = null;
  }
}

/**
 * 检查部门是否有子部门
 */
function hasChildren(dept: DeptTreeNode): boolean {
  // 首先检查 child_count 字段（后端返回的子部门数量）
  if ('child_count' in dept && typeof dept.child_count === 'number') {
    return dept.child_count > 0;
  }
  // 如果没有 child_count 字段，则检查 children 属性
  if (!dept.children) {
    return false; // 没有信息表示没有子部门
  }
  return dept.children.length > 0;
}

/**
 * 自动展开搜索结果中的所有节点
 */
function autoExpandSearchResults(nodes: DeptTreeNode[]) {
  nodes.forEach((node) => {
    expandedDeptIds.value.add(node.id);
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
      const results = await searchDeptApi(newVal);
      searchResults.value = results || [];
      // 自动展开搜索结果中的所有节点，显示完整路径
      if (results && results.length > 0) {
        autoExpandSearchResults(results);
      }
    } catch (error) {
      console.error($t('dept.searchFailed'), error);
      searchResults.value = [];
    } finally {
      isSearching.value = false;
    }
  }, 300);
});

/**
 * 过滤树数据：如果有搜索结果则使用搜索结果，否则使用完整树
 */
const filteredTreeData = computed(() => {
  if (searchKeyword.value.trim() && searchResults.value.length > 0) {
    return searchResults.value;
  }
  return treeData.value;
});

/**
 * 渲染树形列表
 */
const renderTreeList = (nodes: DeptTreeNode[], level: number = 0): any[] => {
  return nodes.flatMap((node) => [
    { node, level, isNode: true },
    ...(expandedDeptIds.value.has(node.id) &&
    node.children &&
    node.children.length > 0
      ? renderTreeList(node.children, level + 1)
      : []),
  ]);
};

const flattenedTree = computed(() => renderTreeList(filteredTreeData.value));

onMounted(() => {
  fetchDeptList();
});
</script>

<template>
  <ElCard
    style="border: none"
    class="mr-[10px] flex h-full flex-col"
    shadow="never"
  >
    <DeptFormModal ref="deptFormModalRef" @success="onDeptFormSuccess" />

    <!-- 搜索和添加区域 -->
    <div class="mb-4 flex gap-2">
      <ElInput
        v-model="searchKeyword"
        :placeholder="$t('common.search')"
        clearable
        :prefix-icon="Search"
      />
      <ElButton :icon="Plus" @click="onAddDept" />
    </div>

    <!-- 部门树列表 -->
    <div class="flex-1 overflow-auto">
      <ElSkeleton :loading="loading || isSearching" animated :count="8">
        <template #template>
          <div class="space-y-1">
            <div v-for="i in 8" :key="i" class="dept-skeleton-item">
              <ElSkeletonItem
                variant="text"
                style="width: 100%; height: 40px"
              />
            </div>
          </div>
        </template>
        <template #default>
          <div class="space-y-2">
            <div
              v-for="(item, index) in flattenedTree"
              :key="`${item.node.id}-${index}`"
              class="dept-item flex cursor-pointer items-center rounded-[8px] px-3 py-2 transition-colors"
              :class="[
                selectedDeptId === item.node.id
                  ? 'bg-primary/15 dark:bg-accent text-primary'
                  : 'hover:bg-[var(--el-fill-color-light)]',
              ]"
              :style="{ paddingLeft: `calc(12px + ${item.level * 20}px)` }"
              @mouseenter="hoveredDeptId = item.node.id"
              @mouseleave="hoveredDeptId = undefined"
              @click="onDeptSelect(item.node)"
            >
              <div class="flex min-w-0 flex-1 items-center gap-1">
                <!-- 展开/折叠按钮 -->
                <div
                  v-if="hasChildren(item.node)"
                  class="hover:text-primary flex w-5 flex-shrink-0 cursor-pointer items-center justify-center"
                  @click.stop="toggleNodeExpanded(item.node)"
                >
                  <Loader
                    v-if="loadingDeptIds.has(item.node.id)"
                    class="size-4 animate-spin"
                  />
                  <IconifyIcon
                    v-else
                    icon="ep:caret-right"
                    class="size-4 transform transition-transform"
                    :class="
                      expandedDeptIds.has(item.node.id) ? 'rotate-90' : ''
                    "
                  />
                </div>
                <div v-else class="w-5 flex-shrink-0"></div>
                <!-- 部门名称 -->
                <div class="truncate text-sm" :title="item.node.name">
                  {{ item.node.name }}
                </div>
              </div>

              <!-- 操作图标 -->
              <div
                v-if="hoveredDeptId === item.node.id"
                class="ml-2 flex flex-shrink-0 gap-0.5"
                @click.stop
              >
                <ElTooltip :content="$t('dept.addChildDept')" placement="top">
                  <ElButton
                    type="primary"
                    text
                    size="small"
                    circle
                    @click="onAddChildDept(item.node)"
                  >
                    <IconifyIcon icon="ep:plus" class="size-4" />
                  </ElButton>
                </ElTooltip>
                <ElTooltip :content="$t('dept.edit')" placement="top">
                  <ElButton
                    type="primary"
                    text
                    size="small"
                    circle
                    style="margin-left: 0"
                    @click="onEditDept(item.node)"
                  >
                    <IconifyIcon icon="ep:edit" class="size-4" />
                  </ElButton>
                </ElTooltip>
                <ElButton
                  type="danger"
                  text
                  size="small"
                  circle
                  style="margin-left: 0"
                  :title="$t('common.delete')"
                  @click="onDeleteDept(item.node)"
                >
                  <IconifyIcon icon="ep:delete" class="size-4" />
                </ElButton>
              </div>
            </div>
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

/* 让 ElCard 的 body 参与 flex 布局，使列表区域可滚动 */
:deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 骨架屏样式 */
.dept-skeleton-item {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 12px;
}

/* 部门项样式 */
.dept-item {
  min-height: 40px;
}
</style>
