<script lang="ts" setup generic="T extends Record<string, any>">
import type { VbenFormProps } from '@vben/common-ui';

import type { PaginationProps } from './types';

import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';

import { useVbenForm } from '@vben/common-ui';
import { LayoutGrid, List, RefreshCw } from '@vben/icons';

import {
  ElButton,
  ElButtonGroup,
  ElCheckbox,
  ElEmpty,
  ElPagination,
  ElScrollbar,
  ElTooltip,
} from 'element-plus';

interface Props {
  data?: T[];
  api?: (params: any) => Promise<T[] | { items: T[]; total?: number }>;
  params?: Record<string, any>;
  autoLoad?: boolean;
  title?: string;
  mode?: 'card' | 'list';
  rowKey?: string;
  showToolbar?: boolean;
  selection?: boolean;
  pagination?: boolean | PaginationProps;
  cardGrid?: {
    gutter?: number;
    lg?: number;
    md?: number;
    sm?: number;
    xl?: number;
    xs?: number;
  };
  cardActionPosition?: 'footer' | 'overlay';
  searchForm?: VbenFormProps;
  /**
   * 内容区域高度，设置后分页器会固定在底部
   * 例如: '500px', 'calc(100vh - 200px)'
   * 如果设置为 'auto'，则会自动计算剩余高度
   */
  contentHeight?: string;
  /**
   * 自动计算高度时的底部偏移量（默认 50px，用于预留分页器和底部边距）
   */
  bottomOffset?: number;
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  api: undefined,
  params: () => ({}),
  autoLoad: true,
  title: '',
  mode: 'card',
  rowKey: 'id',
  showToolbar: true,
  selection: false,
  pagination: true,
  cardGrid: () => ({
    xs: 24,
    sm: 12,
    md: 8,
    lg: 6,
    xl: 6,
    gutter: 16,
  }),
  cardActionPosition: 'footer',
  searchForm: undefined,
  contentHeight: undefined,
  bottomOffset: 50,
});

const emit = defineEmits<{
  refresh: [];
  'selection-change': [selection: T[]];
  'update:mode': [mode: 'card' | 'list'];
}>();

// --- State ---
const loading = ref(false);
const localMode = ref(props.mode);
const items = ref<T[]>([]);
const total = ref(0);
const selectedKeys = ref<Set<number | string>>(new Set());
const searchParams = ref<Record<string, any>>({});

// 动态高度计算
const containerRef = ref<HTMLElement | null>(null);
const calculatedHeight = ref<string>('');

const [Form, formApi] = useVbenForm(props.searchForm || {});

defineExpose({
  formApi,
  fetchData,
});

// Pagination State
const currentPage = ref(1);
const pageSize = ref(20);

// --- Computed ---
const isCardMode = computed(() => localMode.value === 'card');

const displayItems = computed(() => {
  return props.api ? items.value : props.data;
});

const showPagination = computed(() => {
  return props.pagination !== false;
});

const paginationProps = computed(() => {
  const defaultProps = {
    currentPage: currentPage.value,
    pageSize: pageSize.value,
    pageSizes: [10, 20, 50, 100],
    layout: 'total, sizes, prev, pager, next, jumper',
    total: total.value,
  };
  if (typeof props.pagination === 'object') {
    return { ...defaultProps, ...props.pagination };
  }
  return defaultProps;
});

// Grid Class logic for Tailwind
const gridClasses = computed(() => {
  // We'll use style binding for the grid instead of classes for dynamic cols if needed,
  // but mapping props to tailwind grid-cols classes is cleaner if we stick to standard breakpoints.
  // However, since Element Plus Col works with span (24 grid), we can also use ElRow/ElCol.
  // Let's use standard CSS Grid with styles for maximum flexibility.
  return {
    display: 'grid',
    gridTemplateColumns: `repeat(auto-fill, minmax(250px, 1fr))`,
    gap: `${props.cardGrid.gutter}px`,
  };
});

const allSelected = computed(() => {
  const currentItems = displayItems.value || [];
  return (
    currentItems.length > 0 &&
    currentItems.every((item) => selectedKeys.value.has(item[props.rowKey]))
  );
});

const isIndeterminate = computed(() => {
  const currentItems = displayItems.value || [];
  const selectedCount = currentItems.filter((item) =>
    selectedKeys.value.has(item[props.rowKey]),
  ).length;
  return selectedCount > 0 && selectedCount < currentItems.length;
});

// 实际使用的内容高度
const actualContentHeight = computed(() => {
  if (props.contentHeight === 'auto') {
    return calculatedHeight.value || '400px';
  }
  return props.contentHeight;
});

// 计算剩余高度
function calculateHeight() {
  if (props.contentHeight !== 'auto' || !containerRef.value) return;

  nextTick(() => {
    const rect = containerRef.value?.getBoundingClientRect();
    if (rect) {
      const viewportHeight = window.innerHeight;
      const remainingHeight = viewportHeight - rect.top - props.bottomOffset;
      calculatedHeight.value = `${Math.max(200, remainingHeight)}px`;
    }
  });
}

// --- Methods ---

function setMode(mode: 'card' | 'list') {
  localMode.value = mode;
  emit('update:mode', mode);
}

// Data Fetching
async function fetchData() {
  if (!props.api) return;

  loading.value = true;
  try {
    const requestParams = {
      page: currentPage.value,
      pageSize: pageSize.value,
      ...props.params,
      ...searchParams.value,
    };

    const res = await props.api(requestParams);
    if (Array.isArray(res)) {
      items.value = res;
      total.value = res.length;
    } else {
      items.value = res.items || [];
      total.value = res.total || 0;
    }
  } catch (error) {
    console.error('Failed to fetch data:', error);
  } finally {
    loading.value = false;
  }
}

// Selection Logic
function toggleSelection(item: any) {
  if (!props.selection) return;
  const key = item[props.rowKey];
  if (selectedKeys.value.has(key)) {
    selectedKeys.value.delete(key);
  } else {
    selectedKeys.value.add(key);
  }
  emitSelectionChange();
}

function toggleSelectAll(val: boolean | number | string) {
  if (!props.selection) return;
  const currentItems = displayItems.value || [];
  if (val) {
    currentItems.forEach((item) => selectedKeys.value.add(item[props.rowKey]));
  } else {
    currentItems.forEach((item) =>
      selectedKeys.value.delete(item[props.rowKey]),
    );
  }
  emitSelectionChange();
}

function emitSelectionChange() {
  const currentItems = displayItems.value || [];
  const selectedItems = currentItems.filter((item) =>
    selectedKeys.value.has(item[props.rowKey]),
  );
  emit('selection-change', selectedItems as T[]);
}

function isSelected(item: any) {
  return selectedKeys.value.has(item[props.rowKey]);
}

function handlePageChange(val: number) {
  currentPage.value = val;
  fetchData();
}

function handleSizeChange(val: number) {
  pageSize.value = val;
  currentPage.value = 1; // Reset to first page
  fetchData();
}

function handleRefresh() {
  fetchData();
  emit('refresh');
}

async function handleSearch(params: Record<string, any>) {
  searchParams.value = params;
  currentPage.value = 1;
  await fetchData();
}

// --- Lifecycle & Watchers ---

watch(
  () => props.params,
  () => {
    if (props.api) {
      currentPage.value = 1;
      fetchData();
    }
  },
  { deep: true },
);

watch(
  () => props.mode,
  (val) => {
    if (val) localMode.value = val;
  },
);

onMounted(() => {
  if (props.api && props.autoLoad) {
    fetchData();
  } else if (props.data) {
    // If using static data, just init total if needed
    total.value = props.data.length;
  }

  // 自动计算高度
  if (props.contentHeight === 'auto') {
    calculateHeight();
    window.addEventListener('resize', calculateHeight);
  }
});

onUnmounted(() => {
  if (props.contentHeight === 'auto') {
    window.removeEventListener('resize', calculateHeight);
  }
});
</script>

<template>
  <div class="multi-data-view w-full">
    <!-- Search Form -->
    <div v-if="searchForm" class="bg-card mb-4 rounded-lg border p-4">
      <Form @submit="handleSearch" />
    </div>

    <!-- Header -->
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <!-- Title Slot -->
        <div class="text-lg font-bold">
          <slot name="header">
            {{ title }}
          </slot>
        </div>

        <!-- Selection Status -->
        <div
          v-if="selection && selectedKeys.size > 0"
          class="text-muted-foreground flex items-center gap-2 text-sm"
        >
          <span>已选择 {{ selectedKeys.size }} 项</span>
          <ElButton link type="primary" @click="toggleSelectAll(false)">
            清空
          </ElButton>
        </div>
      </div>

      <!-- Right Toolbar -->
      <div class="flex items-center gap-2">
        <slot name="toolbar"></slot>

        <div v-if="showToolbar" class="flex items-center">
          <div class="bg-border mx-2 h-4 w-[1px]"></div>
          <ElButtonGroup>
            <ElTooltip content="卡片视图" placement="top">
              <ElButton
                :type="localMode === 'card' ? 'primary' : ''"
                :icon="LayoutGrid"
                @click="setMode('card')"
              />
            </ElTooltip>
            <ElTooltip content="列表视图" placement="top">
              <ElButton
                :type="localMode === 'list' ? 'primary' : ''"
                :icon="List"
                @click="setMode('list')"
              />
            </ElTooltip>
            <ElTooltip content="刷新" placement="top">
              <ElButton :icon="RefreshCw" @click="handleRefresh" />
            </ElTooltip>
          </ElButtonGroup>
        </div>
      </div>
    </div>

    <!-- Content Area -->
    <div ref="containerRef" v-loading="loading" class="min-h-[200px]">
      <ElScrollbar v-if="actualContentHeight" :height="actualContentHeight">
        <!-- Empty State -->
        <div
          v-if="!loading && (!displayItems || displayItems.length === 0)"
          class="py-8"
        >
          <slot name="empty">
            <ElEmpty description="暂无数据" />
          </slot>
        </div>

        <template v-else>
          <!-- Card Mode -->
          <div v-if="isCardMode" class="grid-container" :style="gridClasses">
            <div
              v-for="item in displayItems"
              :key="item[rowKey]"
              class="bg-card group relative overflow-hidden rounded-xl border shadow-sm transition-all duration-200"
              :class="[
                isSelected(item) ? 'ring-primary ring-2' : 'hover:shadow-lg',
              ]"
            >
              <!-- Card Selection Checkbox (Top Left) -->
              <div
                v-if="selection"
                class="absolute left-2 top-2 z-10"
                :class="{
                  'opacity-0 group-hover:opacity-100': !isSelected(item),
                }"
              >
                <ElCheckbox
                  :model-value="isSelected(item)"
                  @change="toggleSelection(item)"
                  @click.stop
                />
              </div>

              <!-- Card Content -->
              <div class="relative z-[1] p-4">
                <slot name="card" :item="item">
                  <!-- Default Fallback -->
                  <div class="font-medium">{{ item[title] || item.name }}</div>
                </slot>
              </div>

              <!-- Card Actions Overlay (Center) -->
              <div
                v-if="cardActionPosition === 'overlay'"
                class="absolute inset-0 z-[10] flex items-center justify-center opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                style="background-color: rgb(0 0 0 / 60%)"
              >
                <div class="flex items-center gap-2" @click.stop>
                  <slot name="actions" :item="item"></slot>
                </div>
              </div>

              <!-- Card Footer Actions -->
              <div
                v-if="cardActionPosition === 'footer'"
                class="border-border flex items-center justify-end gap-2 border-t bg-gray-50 px-4 py-2 dark:bg-gray-800/50"
              >
                <slot name="actions" :item="item"></slot>
              </div>
            </div>
          </div>

          <!-- List Mode -->
          <div v-else class="flex flex-col gap-2">
            <!-- List Header (Optional for Select All) -->
            <div
              v-if="selection"
              class="bg-muted/30 flex items-center rounded px-4 py-2"
            >
              <ElCheckbox
                :model-value="allSelected"
                :indeterminate="isIndeterminate"
                @change="toggleSelectAll"
              >
                全选
              </ElCheckbox>
            </div>

            <div
              v-for="item in displayItems"
              :key="item[rowKey]"
              class="hover:bg-accent/50 group flex items-center justify-between rounded border p-3 transition-colors"
              :class="{ 'bg-primary/5 border-primary/30': isSelected(item) }"
            >
              <div class="flex flex-1 items-center gap-4">
                <!-- List Selection Checkbox -->
                <ElCheckbox
                  v-if="selection"
                  :model-value="isSelected(item)"
                  @change="toggleSelection(item)"
                />

                <div class="flex-1">
                  <slot name="list" :item="item">
                    <!-- Default Fallback -->
                    <div class="font-medium">
                      {{ item[title] || item.name }}
                    </div>
                  </slot>
                </div>
              </div>

              <!-- List Actions -->
              <div class="ml-4 flex items-center gap-2">
                <slot name="actions" :item="item"></slot>
              </div>
            </div>
          </div>
        </template>
      </ElScrollbar>

      <!-- Without Scrollbar (no contentHeight) -->
      <template v-else>
        <!-- Empty State -->
        <div
          v-if="!loading && (!displayItems || displayItems.length === 0)"
          class="py-8"
        >
          <slot name="empty">
            <ElEmpty description="暂无数据" />
          </slot>
        </div>

        <template v-else>
          <!-- Card Mode -->
          <div v-if="isCardMode" class="grid-container" :style="gridClasses">
            <div
              v-for="item in displayItems"
              :key="item[rowKey]"
              class="bg-card group relative overflow-hidden rounded-xl border shadow-sm transition-all duration-200"
              :class="[
                isSelected(item) ? 'ring-primary ring-2' : 'hover:shadow-lg',
              ]"
            >
              <!-- Card Selection Checkbox (Top Left) -->
              <div
                v-if="selection"
                class="absolute left-2 top-2 z-10"
                :class="{
                  'opacity-0 group-hover:opacity-100': !isSelected(item),
                }"
              >
                <ElCheckbox
                  :model-value="isSelected(item)"
                  @change="toggleSelection(item)"
                  @click.stop
                />
              </div>

              <!-- Card Content -->
              <div class="relative z-[1] p-4">
                <slot name="card" :item="item">
                  <!-- Default Fallback -->
                  <div class="font-medium">{{ item[title] || item.name }}</div>
                </slot>
              </div>

              <!-- Card Actions Overlay (Center) -->
              <div
                v-if="cardActionPosition === 'overlay'"
                class="absolute inset-0 z-[10] flex items-center justify-center opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                style="background-color: rgb(0 0 0 / 60%)"
              >
                <div class="flex items-center gap-2" @click.stop>
                  <slot name="actions" :item="item"></slot>
                </div>
              </div>

              <!-- Card Footer Actions -->
              <div
                v-if="cardActionPosition === 'footer'"
                class="border-border flex items-center justify-end gap-2 border-t bg-gray-50 px-4 py-2 dark:bg-gray-800/50"
              >
                <slot name="actions" :item="item"></slot>
              </div>
            </div>
          </div>

          <!-- List Mode -->
          <div v-else class="flex flex-col gap-2">
            <!-- List Header (Optional for Select All) -->
            <div
              v-if="selection"
              class="bg-muted/30 flex items-center rounded px-4 py-2"
            >
              <ElCheckbox
                :model-value="allSelected"
                :indeterminate="isIndeterminate"
                @change="toggleSelectAll"
              >
                全选
              </ElCheckbox>
            </div>

            <div
              v-for="item in displayItems"
              :key="item[rowKey]"
              class="hover:bg-accent/50 group flex items-center justify-between rounded border p-3 transition-colors"
              :class="{ 'bg-primary/5 border-primary/30': isSelected(item) }"
            >
              <div class="flex flex-1 items-center gap-4">
                <!-- List Selection Checkbox -->
                <ElCheckbox
                  v-if="selection"
                  :model-value="isSelected(item)"
                  @change="toggleSelection(item)"
                />

                <div class="flex-1">
                  <slot name="list" :item="item">
                    <!-- Default Fallback -->
                    <div class="font-medium">
                      {{ item[title] || item.name }}
                    </div>
                  </slot>
                </div>
              </div>

              <!-- List Actions -->
              <div class="ml-4 flex items-center gap-2">
                <slot name="actions" :item="item"></slot>
              </div>
            </div>
          </div>
        </template>
      </template>
    </div>

    <!-- Footer Pagination -->
    <div v-if="showPagination" class="mt-4 flex justify-end">
      <slot name="footer">
        <ElPagination
          v-bind="paginationProps"
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </slot>
    </div>
  </div>
</template>

<style scoped>
.grid-container {
  display: grid;

  /* Default responsive grid if no specific config provided via style binding overrides */
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}
</style>
