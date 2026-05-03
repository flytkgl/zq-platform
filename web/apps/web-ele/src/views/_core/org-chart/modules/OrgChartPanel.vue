<script lang="ts" setup>
import type { OrgChartNode } from '#/api/core/org-chart';

import { onBeforeUnmount, onMounted, provide, ref, watch } from 'vue';

import { Expand, Network } from '@vben/icons';

import { ElEmpty, ElScrollbar, ElTooltip } from 'element-plus';

import { getOrgChartChainApi, getOrgChartTopApi } from '#/api/core/org-chart';
import { $t } from '#/locales';

import OrgNode from './OrgNode.vue';

defineOptions({
  name: 'OrgChartPanel',
});

const props = withDefaults(
  defineProps<{
    showModeToggle?: boolean;
    userId?: string;
  }>(),
  { userId: undefined, showModeToggle: true },
);

const topNodes = ref<OrgChartNode[]>([]);
const loading = ref(true);

const focusMode = ref(true);
provide('orgChartFocusMode', focusMode);

// 拖拽平移
const scrollbarRef = ref<InstanceType<typeof ElScrollbar> | null>(null);
const containerRef = ref<HTMLElement | null>(null);
const isDragging = ref(false);
let startX = 0;
let startY = 0;
let scrollLeft = 0;
let scrollTop = 0;

function getWrapEl(): HTMLElement | null {
  return scrollbarRef.value?.wrapRef ?? null;
}

function onMouseDown(e: MouseEvent) {
  if ((e.target as HTMLElement).closest('.node-card')) return;
  const el = getWrapEl();
  if (!el) return;
  isDragging.value = true;
  startX = e.clientX;
  startY = e.clientY;
  scrollLeft = el.scrollLeft;
  scrollTop = el.scrollTop;
  containerRef.value?.classList.add('is-dragging');
  e.preventDefault();
}

function onMouseMove(e: MouseEvent) {
  if (!isDragging.value) return;
  const el = getWrapEl();
  if (!el) return;
  el.scrollLeft = scrollLeft - (e.clientX - startX);
  el.scrollTop = scrollTop - (e.clientY - startY);
}

function onMouseUp() {
  if (!isDragging.value) return;
  isDragging.value = false;
  containerRef.value?.classList.remove('is-dragging');
}

async function loadNodes() {
  loading.value = true;
  try {
    if (props.userId) {
      const chainRoot = await getOrgChartChainApi(props.userId);
      topNodes.value = [chainRoot];
    } else {
      topNodes.value = await getOrgChartTopApi();
    }
  } catch (error) {
    console.error('Failed to load org chart:', error);
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.userId,
  () => {
    loadNodes();
  },
);

onMounted(() => {
  loadNodes();
  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
});

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onMouseMove);
  document.removeEventListener('mouseup', onMouseUp);
});
</script>

<template>
  <div class="org-chart-panel">
    <!-- 加载骨架屏 -->
    <div v-if="loading" class="org-chart-skeleton">
      <div class="skeleton-tree">
        <div class="skeleton-node-wrapper">
          <div class="skeleton-node skeleton-animate"></div>
        </div>
        <div class="skeleton-connector-down"></div>
        <div class="skeleton-children">
          <div v-for="i in 4" :key="i" class="skeleton-child-branch">
            <div class="skeleton-connector-up"></div>
            <div class="skeleton-node skeleton-animate"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <ElEmpty
      v-else-if="topNodes.length === 0"
      :description="$t('org-chart.orgChart.empty')"
    />

    <!-- 组织架构树 -->
    <div
      v-else
      ref="containerRef"
      class="org-tree-container"
      @mousedown="onMouseDown"
    >
      <!-- 模式切换按钮 -->
      <div v-if="showModeToggle" class="mode-toggle">
        <ElTooltip
          :content="
            focusMode
              ? $t('org-chart.orgChart.expandMode')
              : $t('org-chart.orgChart.focusMode')
          "
          placement="left"
        >
          <button
            class="mode-toggle-btn"
            :class="{ active: focusMode }"
            @click="focusMode = !focusMode"
          >
            <Network v-if="!focusMode" :size="16" />
            <Expand v-else :size="16" />
          </button>
        </ElTooltip>
      </div>
      <ElScrollbar ref="scrollbarRef">
        <div class="org-tree-scroll">
          <div class="org-tree">
            <div v-for="node in topNodes" :key="node.id" class="org-tree-root">
              <OrgNode
                :node="node"
                :initial-children="(node as any).children"
              />
            </div>
          </div>
        </div>
      </ElScrollbar>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.org-chart-panel {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.org-chart-skeleton {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
}

.skeleton-tree {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.skeleton-node {
  width: 180px;
  height: 64px;
  background: var(--el-fill-color-light);
  border-radius: 10px;
}

.skeleton-animate {
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-connector-down {
  width: 2px;
  height: 24px;
  background: var(--el-fill-color);
}

.skeleton-connector-up {
  width: 2px;
  height: 24px;
  margin: 0 auto;
  background: var(--el-fill-color);
}

.skeleton-children {
  display: flex;
  gap: 0;
}

.skeleton-child-branch {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 16px;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    right: 50%;
    left: 0;
    height: 2px;
    background: var(--el-fill-color);
  }

  &::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    left: 50%;
    height: 2px;
    background: var(--el-fill-color);
  }

  &:first-child::before {
    display: none;
  }

  &:last-child::after {
    display: none;
  }
}

@keyframes skeleton-pulse {
  0% {
    opacity: 1;
  }

  50% {
    opacity: 0.4;
  }

  100% {
    opacity: 1;
  }
}

.org-tree-container {
  position: relative;
  width: 100%;
  height: 100%;
  cursor: grab;
  user-select: none;

  &.is-dragging {
    cursor: grabbing;
  }

  :deep(.el-scrollbar__wrap) {
    overflow: auto;
  }
}

.mode-toggle {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
}

.mode-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  color: var(--el-text-color-secondary);
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    color: var(--el-color-primary);
    border-color: var(--el-color-primary-light-3);
    box-shadow: 0 2px 8px rgb(0 0 0 / 8%);
  }

  &.active {
    color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
    border-color: var(--el-color-primary-light-5);
  }
}

.org-tree-scroll {
  display: inline-flex;
  min-width: 100%;
  min-height: 100%;
  justify-content: center;
  padding: 40px;
}

.org-tree {
  display: flex;
  flex-direction: column;
  gap: 0;
  align-items: center;
}

.org-tree-root {
  display: flex;
  justify-content: center;
}
</style>
