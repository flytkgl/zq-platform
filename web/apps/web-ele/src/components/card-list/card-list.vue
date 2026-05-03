<script lang="ts" setup generic="T extends CardListItem">
import type { CardListItem, CardListOptions } from './types';

import { computed, ref } from 'vue';

import { Plus, Search } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElInput,
  ElSkeleton,
  ElSkeletonItem,
} from 'element-plus';

interface Props<T extends CardListItem = CardListItem> {
  /**
   * 列表数据
   */
  items: T[];
  /**
   * 正在加载状态
   */
  loading?: boolean;
  /**
   * 当前选中的项ID
   */
  selectedId?: string;
  /**
   * 悬停的项ID（用于显示操作按钮）
   */
  hoveredId?: string;
  /**
   * 搜索关键词
   */
  searchKeyword?: string;
  /**
   * 卡片列表配置
   */
  options: CardListOptions<T>;
}

interface Emits {
  /**
   * 项目被选中
   */
  select: [id: string | undefined];
  /**
   * 搜索关键词变化
   */
  'update:searchKeyword': [value: string];
  /**
   * 悬停状态变化
   */
  'update:hoveredId': [id: string | undefined];
  /**
   * 添加按钮点击
   */
  add: [];
  /**
   * 编辑按钮点击
   */
  edit: [item: T, event: Event];
  /**
   * 删除按钮点击
   */
  delete: [item: T, event: Event];
  /**
   * 详情按钮点击
   */
  detail: [item: T, event: Event];
  /**
   * 表单提交成功
   */
  'form-success': [];
}

const props = withDefaults(defineProps<Props<T>>(), {
  loading: false,
  selectedId: undefined,
  hoveredId: undefined,
  searchKeyword: '',
});

const emit = defineEmits<Emits>();
// 显示模式
const displayMode = computed(() => props.options.displayMode || 'default');
const isCenterMode = computed(() => displayMode.value === 'center');

const localSearchKeyword = ref(props.searchKeyword);

// 监听搜索关键词变化
function onSearchChange(value: string) {
  localSearchKeyword.value = value;
  emit('update:searchKeyword', value);
}

// 计算过滤后的列表
const filteredItems = computed(() => {
  if (!localSearchKeyword.value.trim()) {
    return props.items;
  }

  const keyword = localSearchKeyword.value.toLowerCase();
  return props.items.filter((item) => {
    return props.options.searchFields.some((field) => {
      const value = item[field.field];
      if (value === null || value === undefined) {
        return false;
      }
      return String(value).toLowerCase().includes(keyword);
    });
  });
});

function onItemSelect(id: string) {
  emit('select', id);
}

function onAddClick() {
  emit('add');
}

function onEditClick(item: T, event: Event) {
  emit('edit', item, event);
}

function onDeleteClick(item: T, event: Event) {
  emit('delete', item, event);
}

function onDetailClick(item: T, event: Event) {
  emit('detail', item, event);
}

function onMouseEnter(id: string) {
  emit('update:hoveredId', id);
}

function onMouseLeave() {
  emit('update:hoveredId', undefined);
}

// 获取项目标题
function getItemTitle(item: T): string {
  return String(item[props.options.titleField]);
}
</script>

<template>
  <ElCard shadow="never" style="border: none" class="flex h-full flex-col">
    <!-- 搜索和添加区域 -->
    <div class="mb-4 flex gap-2">
      <ElInput
        :model-value="localSearchKeyword"
        :placeholder="$t('common.search')"
        clearable
        :prefix-icon="Search"
        @update:model-value="onSearchChange"
      />
      <ElButton :icon="Plus" @click="onAddClick" />
    </div>

    <!-- 项目列表 -->
    <div class="flex-1 overflow-auto">
      <ElSkeleton
        :loading="loading"
        animated
        :count="options.skeletonCount ?? 8"
      >
        <template #template>
          <div class="space-y-1">
            <div
              v-for="i in options.skeletonCount ?? 8"
              :key="i"
              class="card-list-skeleton-item"
            >
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
              v-for="item in filteredItems"
              :key="item.id"
              class="card-list-item cursor-pointer rounded-[8px] px-3 py-2 transition-colors"
              :class="[
                selectedId === item.id
                  ? 'bg-primary/15 dark:bg-accent text-primary'
                  : 'hover:bg-[var(--el-fill-color-light)]',
                isCenterMode ? 'card-list-item-center' : '',
              ]"
              @mouseenter="onMouseEnter(item.id)"
              @mouseleave="onMouseLeave"
              @click="onItemSelect(item.id)"
            >
              <!-- 居中模式：一行靠左显示 -->
              <template v-if="isCenterMode">
                <div class="flex w-full items-center justify-start">
                  <!-- 插槽：自定义项目内容 -->
                  <slot
                    name="item"
                    :item="item"
                    :hovered="hoveredId === item.id"
                  >
                    <!-- 默认显示标题 -->
                    <div
                      class="text-sm font-medium"
                      :title="getItemTitle(item)"
                    >
                      {{ getItemTitle(item) }}
                    </div>
                  </slot>
                </div>
              </template>

              <!-- 默认模式：两行显示 -->
              <template v-else>
                <!-- 第一行：标题和操作按钮 -->
                <div class="mb-1 flex items-center justify-between">
                  <div class="min-w-0 flex-1">
                    <!-- 插槽：自定义项目内容 -->
                    <slot
                      name="item"
                      :item="item"
                      :hovered="hoveredId === item.id"
                    >
                      <!-- 默认显示标题 -->
                      <div
                        class="truncate text-sm font-medium"
                        :title="getItemTitle(item)"
                      >
                        {{ getItemTitle(item) }}
                      </div>
                    </slot>
                  </div>

                  <!-- 操作按钮插槽 -->
                  <slot
                    v-if="hoveredId === item.id"
                    name="actions"
                    :item="item"
                    @edit="onEditClick(item, $event)"
                    @delete="onDeleteClick(item, $event)"
                    @detail="onDetailClick(item, $event)"
                  ></slot>
                </div>

                <!-- 第二行及以后：详细信息 -->
                <slot name="details" :item="item"></slot>
              </template>
            </div>
          </div>
        </template>
      </ElSkeleton>
    </div>

    <!-- 其他插槽 -->
    <slot name="modal"></slot>
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
.card-list-skeleton-item {
  box-sizing: border-box;
  width: 100%;
  padding: 8px 12px;
}

/* 项目样式 */
.card-list-item {
  min-height: 56px;
}

/* 居中模式样式（一行靠左显示） */
.card-list-item-center {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  min-height: 40px;
}
</style>
