<script lang="ts" setup>
import type { Ref } from 'vue';

import type { OrgChartNode } from '#/api/core/org-chart';

import { computed, inject, onMounted, ref } from 'vue';

import { ElTag } from 'element-plus';

import { getOrgChartChildrenApi } from '#/api/core/org-chart';
import { UserAvatar } from '#/components/user-avatar';

defineOptions({
  name: 'OrgNode',
});

const props = withDefaults(
  defineProps<{
    autoExpand?: boolean;
    initialChildren?: OrgChartNode[];
    node: OrgChartNode;
  }>(),
  { autoExpand: false, initialChildren: undefined },
);

const emit = defineEmits<{
  (e: 'node-click', id: string): void;
}>();

const focusMode = inject<Ref<boolean>>('orgChartFocusMode', ref(false));

const expanded = ref(false);
const children = ref<OrgChartNode[]>([]);
const loading = ref(false);
const loaded = ref(false);
const partialLoaded = ref(false);
const childrenKey = ref(0);
const focusedChildId = ref<null | string>(null);

const visibleChildren = computed(() => {
  if (focusMode.value && focusedChildId.value) {
    return children.value.filter((c) => c.id === focusedChildId.value);
  }
  return children.value;
});

async function loadChildren() {
  if (loaded.value && !partialLoaded.value) return;
  loading.value = true;
  try {
    children.value = await getOrgChartChildrenApi(props.node.id);
    loaded.value = true;
    partialLoaded.value = false;
  } catch (error) {
    console.error('Failed to load children:', error);
  } finally {
    loading.value = false;
  }
}

function onChildClick(childId: string) {
  if (!focusMode.value) return;
  focusedChildId.value = childId;
}

async function toggleExpand() {
  if (props.node.subordinate_count === 0) return;
  emit('node-click', props.node.id);
  await loadChildren();
  if (focusMode.value) {
    // 聚焦模式：重置聚焦状态，显示所有直接下属，子树收起
    focusedChildId.value = null;
    childrenKey.value++;
    expanded.value = true;
  } else {
    expanded.value = !expanded.value;
  }
}

onMounted(async () => {
  if (props.initialChildren && props.initialChildren.length > 0) {
    children.value = props.initialChildren;
    loaded.value = true;
    partialLoaded.value = true;
    expanded.value = true;
    // 预加载的汇报链只有一个子节点，直接聚焦，不显示框
    if (props.initialChildren.length === 1) {
      focusedChildId.value = props.initialChildren[0]!.id;
    }
  } else if (props.autoExpand && props.node.subordinate_count > 0) {
    await loadChildren();
    expanded.value = true;
  }
});
</script>

<template>
  <div class="org-node-wrapper">
    <!-- 当前节点 -->
    <div class="org-node" @click="toggleExpand">
      <div
        class="node-card"
        :class="{
          'has-children': node.subordinate_count > 0,
          'is-expanded': expanded,
          'is-loading': loading,
        }"
      >
        <UserAvatar
          :user-id="node.id"
          :name="node.name"
          :avatar="node.avatar"
          :size="48"
          :font-size="20"
          :shadow="false"
          :show-popover="true"
          :auto-load="false"
        />
        <div class="node-info">
          <div class="node-name">{{ node.name || node.username }}</div>
          <div v-if="node.post_name" class="node-post">
            {{ node.post_name }}
          </div>
          <div v-if="node.dept_name" class="node-dept">
            {{ node.dept_name }}
          </div>
        </div>
        <ElTag
          v-if="node.subordinate_count > 0"
          size="small"
          round
          :type="expanded ? 'primary' : 'info'"
          class="node-count"
        >
          {{ node.subordinate_count }}
        </ElTag>
      </div>
    </div>

    <!-- 子节点连接线 + 子节点列表 -->
    <template v-if="expanded && visibleChildren.length > 0">
      <!-- 聚焦模式 -->
      <div v-if="focusMode" class="org-children-wrapper">
        <div class="connector-down"></div>
        <div
          class="focus-children-container"
          :class="{ 'has-box': !focusedChildId }"
        >
          <div
            v-for="child in visibleChildren"
            :key="`${child.id}-${childrenKey}`"
            class="focus-child-item"
          >
            <OrgNode
              :node="child"
              :initial-children="(child as any).children"
              @node-click="onChildClick"
            />
          </div>
        </div>
      </div>

      <!-- 展开模式：每个子节点单独连线 -->
      <div v-else class="org-children-wrapper">
        <div class="connector-down"></div>
        <div class="connector-horizontal">
          <div class="connector-line"></div>
        </div>
        <div class="org-children">
          <div
            v-for="child in visibleChildren"
            :key="`${child.id}-${childrenKey}`"
            class="org-child-branch"
          >
            <div class="connector-up"></div>
            <OrgNode
              :node="child"
              :initial-children="(child as any).children"
              @node-click="onChildClick"
            />
          </div>
        </div>
      </div>
    </template>

    <!-- 加载中 -->
    <div v-if="loading" class="org-loading">
      <div class="loading-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.org-node-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.org-node {
  display: flex;
  justify-content: center;
}

.node-card {
  display: flex;
  gap: 10px;
  align-items: center;
  width: 220px;
  padding: 12px 16px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  cursor: default;
  transition: all 0.25s ease;

  &.has-children {
    cursor: pointer;

    &:hover {
      border-color: var(--el-color-primary-light-3);
      box-shadow: 0 4px 12px rgb(0 0 0 / 8%);
      transform: translateY(-1px);
    }
  }

  &.is-expanded {
    border-color: var(--el-color-primary-light-5);
    background: var(--el-color-primary-light-9);
  }

  &.is-loading {
    opacity: 0.7;
  }
}

.node-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.node-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.node-post {
  font-size: 12px;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.node-dept {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.node-count {
  flex-shrink: 0;
  margin-left: 4px;
}

// 连接线样式
.org-children-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.connector-down {
  width: 2px;
  height: 24px;
  background: var(--el-border-color);
}

.connector-horizontal {
  position: relative;
  width: 100%;
}

.connector-line {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 2px;
  margin: 0 auto;
  background: var(--el-border-color);
}

.org-children {
  display: flex;
  gap: 0;
  justify-content: center;
}

.org-child-branch {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 16px;
}

.connector-up {
  width: 2px;
  height: 24px;
  background: var(--el-border-color);
}

// 动态计算横线宽度
.org-children {
  position: relative;

  // 横线只覆盖第一个到最后一个子节点中心之间
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 0;
  }
}

// 重新实现连接线：用子节点的 ::before 画
.connector-horizontal {
  display: none;
}

.org-children-wrapper {
  .org-children {
    position: relative;

    // 横线
    &::before {
      content: '';
      position: absolute;
      top: 0;
      height: 2px;
      background: var(--el-border-color);
    }
  }

  // 单个子节点不需要横线
  .org-children:has(.org-child-branch:only-child)::before {
    display: none;
  }

  // 多个子节点：横线从第一个到最后一个中心
  .org-children:has(.org-child-branch:nth-child(2))::before {
    left: calc(50% / var(--child-count));
    right: calc(50% / var(--child-count));
  }
}

// 使用更简单的方式：每个子节点分支顶部都有竖线，横线用 border 实现
.org-children {
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    right: 50%;
    height: 2px;
    background: var(--el-border-color);
  }

  .org-child-branch {
    &:first-child ~ .org-child-branch {
      // 有兄弟节点时
    }
  }
}

// 最终方案：用 JS 计算的方式太复杂，改用简单的 border 方案
// 每个子节点分支用 border-top 连接
.org-children {
  &::before {
    display: none;
  }
}

.org-child-branch {
  position: relative;

  // 左半横线
  &::before {
    content: '';
    position: absolute;
    top: 0;
    right: 50%;
    left: 0;
    height: 2px;
    background: var(--el-border-color);
  }

  // 右半横线
  &::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    left: 50%;
    height: 2px;
    background: var(--el-border-color);
  }

  // 第一个子节点：只有右半横线
  &:first-child::before {
    display: none;
  }

  // 最后一个子节点：只有左半横线
  &:last-child::after {
    display: none;
  }

  // 唯一子节点：不需要横线
  &:only-child::before,
  &:only-child::after {
    display: none;
  }
}

// 聚焦模式容器
.focus-children-container {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  max-width: calc(232px * 4 + 36px);
  transition: all 0.25s ease;

  &.has-box {
    padding: 16px;
    background: var(--el-bg-color-page);
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 10px;
  }
}

.focus-child-item {
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

// 加载动画
.org-loading {
  padding: 12px 0;
}

.loading-dots {
  display: flex;
  gap: 6px;
  justify-content: center;

  span {
    width: 6px;
    height: 6px;
    background: var(--el-color-primary);
    border-radius: 50%;
    animation: dot-bounce 1.4s infinite ease-in-out both;

    &:nth-child(1) {
      animation-delay: -0.32s;
    }

    &:nth-child(2) {
      animation-delay: -0.16s;
    }
  }
}

@keyframes dot-bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }

  40% {
    transform: scale(1);
  }
}
</style>
