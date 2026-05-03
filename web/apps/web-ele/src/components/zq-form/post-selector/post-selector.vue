<script lang="ts" setup>
import type { PostSelectorEmits, PostSelectorProps } from './types';

import { computed, onMounted, ref, useAttrs, watch } from 'vue';

import { Award, Search, X } from '@vben/icons';
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
} from 'element-plus';

import { getPostListApi, getPostsByIds } from '#/api/core/post';
import { ZqDialog } from '#/components/zq-dialog';

defineOptions({
  name: 'PostSelector',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<Props>(), {
  multiple: false,
  placeholder: () => $t('ui.placeholder.select') || 'Please select',
  disabled: false,
  clearable: true,
  filterable: true,
});

const emit = defineEmits<PostSelectorEmits>();

interface Props extends PostSelectorProps {}

const attrs = useAttrs();

const modalVisible = ref(false);
const posts = ref<any[]>([]);
const selectedPosts = ref<Set<string>>(
  new Set(
    Array.isArray(props.modelValue)
      ? props.modelValue
      : props.modelValue
        ? [props.modelValue]
        : [],
  ),
);
// 临时选择（用于 modal 中的选择，未确认前）
const tempSelectedPosts = ref<Set<string>>(new Set());
const postLoading = ref(false);
const searchText = ref('');
// 分页相关
const currentPage = ref(1);
const pageSize = ref(20);
const totalPosts = ref(0);
const isLoadingMore = ref(false);
// 标记是否已经尝试过加载更多（用于显示"没有更多数据"提示）
const hasTriedLoadMore = ref(false);
// 标记是否已加载过岗位数据
const hasLoadedPosts = ref(false);
// 标记是否已加载过完整列表（用于弹窗）
const hasLoadedFullList = ref(false);

// 计算显示值（只显示已确认的值）
const displayValue = computed({
  get() {
    if (selectedPosts.value.size === 0) return undefined;
    if (props.multiple) {
      return [...selectedPosts.value];
    }
    return [...selectedPosts.value][0];
  },
  set(_value) {
    // ElSelect 会改变这个值，但我们不需要处理
  },
});

// 获取已选岗位的信息
const selectedPostsWithInfo = computed(() => {
  const result = [];
  const seenIds = new Set<string>(); // 用于去重

  for (const postId of selectedPosts.value) {
    // 避免重复添加
    if (seenIds.has(postId)) continue;
    seenIds.add(postId);

    const post = posts.value.find((p) => p.id === postId);
    if (post) {
      result.push({
        id: post.id,
        name: post.name,
        code: post.code,
      });
    } else {
      // 找不到岗位信息时显示"正在加载中"
      result.push({
        id: postId,
        name: $t('common.loading') || 'Loading...',
        code: '',
      });
    }
  }
  return result;
});

// 获取临时选择岗位的信息
const tempSelectedPostsWithInfo = computed(() => {
  const result = [];
  const seenIds = new Set<string>(); // 用于去重

  for (const postId of tempSelectedPosts.value) {
    // 避免重复添加
    if (seenIds.has(postId)) continue;

    const post = posts.value.find((p) => p.id === postId);
    if (post) {
      seenIds.add(postId);
      result.push({
        id: post.id,
        name: post.name,
        code: post.code,
      });
    }
  }
  return result;
});

// 加载岗位数据（分页）
const loadPosts = async (page: number = 1, append: boolean = false) => {
  try {
    if (page === 1) {
      postLoading.value = true;
    } else {
      isLoadingMore.value = true;
    }

    const result = await getPostListApi({
      page,
      pageSize: pageSize.value,
      name: searchText.value || undefined,
    });

    if (result) {
      // 无论是追加还是重新加载，都需要去重
      const existingIds = new Set(posts.value.map((p) => p.id));
      const newItems = (result.items || []).filter(
        (item: any) => !existingIds.has(item.id),
      );

      if (append) {
        // 追加数据（触底加载）
        posts.value = [...posts.value, ...newItems];
      } else {
        // 重新加载（首次加载或搜索）
        // 合并已有数据（已选项）和新加载的数据
        posts.value = [...posts.value, ...newItems];
      }

      totalPosts.value = result.total || 0;
      currentPage.value = page;
      hasLoadedPosts.value = true;
      // 标记已加载完整列表
      hasLoadedFullList.value = true;
    }

    postLoading.value = false;
    isLoadingMore.value = false;
  } catch (error) {
    console.error('Failed to load posts:', error);
    postLoading.value = false;
    isLoadingMore.value = false;
  }
};

// 根据ID加载特定岗位信息（用于编辑时显示已选岗位的名称）
const loadPostsByIds = async (ids: string[]) => {
  if (!ids || ids.length === 0) return;

  try {
    postLoading.value = true;

    // 调用后端API按ID查询岗位信息
    const result = await getPostsByIds(ids);

    if (result && result.length > 0) {
      // 合并数据，去重
      const existingIds = new Set(posts.value.map((p) => p.id));
      const newPosts = result.filter((p: any) => !existingIds.has(p.id));
      posts.value = [...posts.value, ...newPosts];
      hasLoadedPosts.value = true;
    }

    postLoading.value = false;
  } catch (error) {
    console.error('Failed to load posts by ids:', error);
    postLoading.value = false;
  }
};

// 岗位列表直接使用 posts
const filteredPosts = computed(() => {
  return posts.value;
});

// 判断是否还有更多数据
const hasMoreData = computed(() => {
  return posts.value.length < totalPosts.value;
});

// 防抖搜索定时器
let searchTimer: null | ReturnType<typeof setTimeout> = null;

// 监听搜索文本变化，执行服务端搜索
watch(searchText, () => {
  // 清除之前的定时器
  if (searchTimer) {
    clearTimeout(searchTimer);
  }

  // 设置新的防抖定时器
  searchTimer = setTimeout(() => {
    // 重置分页并重新加载
    currentPage.value = 1;
    loadPosts(1, false);
  }, 300);
});

// 处理岗位选择
const handlePostSelect = (postId: string) => {
  if (props.multiple) {
    if (tempSelectedPosts.value.has(postId)) {
      tempSelectedPosts.value.delete(postId);
    } else {
      tempSelectedPosts.value.add(postId);
    }
  } else {
    // 单选模式
    tempSelectedPosts.value.clear();
    tempSelectedPosts.value.add(postId);
    // 单选时直接确认并关闭
    handleConfirm();
  }
};

// 打开modal
const openModal = async () => {
  if (props.disabled) return;
  modalVisible.value = true;
};

// 打开modal后加载数据
const handleModalOpened = async () => {
  // 初始化临时选择为已选择的值
  tempSelectedPosts.value = new Set(selectedPosts.value);

  // 只有在未加载过完整列表时才加载第一页数据
  if (!hasLoadedFullList.value) {
    await loadPosts(1, false);
  }
};

// 触底加载更多
const handleScroll = ({
  scrollTop,
}: {
  scrollLeft: number;
  scrollTop: number;
}) => {
  const scrollbarRef = document.querySelector(
    '.post-selector-left .el-scrollbar__wrap',
  );
  if (!scrollbarRef) return;

  const scrollHeight = scrollbarRef.scrollHeight;
  const clientHeight = scrollbarRef.clientHeight;

  // 当滚动到底部附近 50px 时触发加载
  if (
    scrollTop + clientHeight >= scrollHeight - 50 &&
    hasMoreData.value &&
    !isLoadingMore.value &&
    !postLoading.value
  ) {
    hasTriedLoadMore.value = true;
    loadPosts(currentPage.value + 1, true);
  }
};

// 确认选择
const handleConfirm = () => {
  // 将临时选择的值保存到 selectedPosts（已确认）
  selectedPosts.value = new Set(tempSelectedPosts.value);

  const value = props.multiple
    ? [...selectedPosts.value]
    : selectedPosts.value.size > 0
      ? [...selectedPosts.value][0]
      : '';

  emit('update:modelValue', value);
  emit('change', value);
  modalVisible.value = false;
};

// 清除选择
const handleClear = (e?: MouseEvent) => {
  if (e) {
    e.stopPropagation();
  }
  tempSelectedPosts.value.clear();
  selectedPosts.value.clear();
  const emptyValue = props.multiple ? [] : '';
  emit('update:modelValue', emptyValue);
  emit('change', emptyValue);
};

// 删除单个选中项（多选模式下点击标签删除按钮）
const handleRemoveTag = (postId: string) => {
  selectedPosts.value.delete(postId);
  const value = props.multiple ? [...selectedPosts.value] : '';
  emit('update:modelValue', value);
  emit('change', value);
};

// 监听外部 modelValue 变化
const updateInternalValue = () => {
  selectedPosts.value.clear();
  tempSelectedPosts.value.clear();
  if (Array.isArray(props.modelValue)) {
    props.modelValue.forEach((v) => selectedPosts.value.add(v));
  } else if (props.modelValue) {
    selectedPosts.value.add(props.modelValue);
  }
  // 打开 modal 时初始化临时选择
  if (modalVisible.value) {
    tempSelectedPosts.value = new Set(selectedPosts.value);
  }
};

// 监听 modelValue 变化，如果有值且岗位数据未加载，则加载
watch(
  () => props.modelValue,
  async (newValue) => {
    updateInternalValue();

    // 如果有选中值且岗位数据未加载，则加载岗位数据
    if (
      ((Array.isArray(newValue) && newValue.length > 0) ||
        (typeof newValue === 'string' && newValue)) &&
      !hasLoadedPosts.value
    ) {
      const ids = Array.isArray(newValue) ? newValue : [newValue];
      await loadPostsByIds(ids);
    }
  },
  { immediate: true },
);

// 组件挂载时，如果有初始值，则加载岗位数据
onMounted(async () => {
  if (
    (Array.isArray(props.modelValue) && props.modelValue.length > 0) ||
    (typeof props.modelValue === 'string' && props.modelValue)
  ) {
    const ids = Array.isArray(props.modelValue)
      ? props.modelValue
      : [props.modelValue];
    await loadPostsByIds(ids);
  }
});

defineExpose({
  openModal,
});
</script>

<template>
  <div class="post-selector">
    <!-- 选择框 -->
    <div class="post-selector-input" :class="{ disabled }">
      <ElSelect
        v-bind="attrs"
        v-model="displayValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :clearable="clearable && selectedPosts.size > 0"
        :multiple="multiple"
        :suffix-icon="Award"
        readonly
        @click="openModal"
        @clear="() => handleClear()"
        @remove-tag="handleRemoveTag"
      >
        <ElOption
          v-for="item in selectedPostsWithInfo"
          :key="item.id"
          :label="item.name"
          :value="item.id"
        />
      </ElSelect>
    </div>

    <!-- Modal -->
    <ZqDialog
      v-model="modalVisible"
      :title="$t('system.user.selectPost') || 'Select Posts'"
      width="45%"
      :show-fullscreen-button="false"
      @opened="handleModalOpened"
    >
      <div class="post-selector-content">
        <!-- 左侧：搜索 + 岗位列表 -->
        <div class="post-selector-left">
          <div v-if="filterable" class="list-search">
            <ElInput
              v-model="searchText"
              :placeholder="$t('common.search') || 'Search'"
              clearable
              :prefix-icon="Search"
            />
          </div>
          <ElScrollbar class="list-scroll" @scroll="handleScroll">
            <ElSkeleton :loading="postLoading" animated :count="8">
              <template #template>
                <div class="list-skeleton">
                  <div v-for="i in 8" :key="i" class="post-skeleton-item">
                    <ElSkeletonItem
                      variant="text"
                      style="width: 100%; height: 36px; margin: 4px 0"
                    />
                  </div>
                </div>
              </template>
              <template #default>
                <div class="list-body">
                  <ElEmpty
                    v-if="filteredPosts.length === 0 && !postLoading"
                    :description="$t('common.noData') || 'No Data'"
                  />
                  <div v-else class="post-list">
                    <div
                      v-for="post in filteredPosts"
                      :key="post.id"
                      class="post-item"
                      :class="{
                        'post-item--selected': tempSelectedPosts.has(post.id),
                      }"
                      @click="handlePostSelect(post.id)"
                    >
                      <div class="post-name">{{ post.name }}</div>
                      <div v-if="post.code" class="post-code">
                        {{ post.code }}
                      </div>
                    </div>

                    <!-- 加载更多提示 -->
                    <div v-if="isLoadingMore" class="loading-more">
                      <ElSkeletonItem
                        variant="text"
                        style="width: 100%; height: 36px"
                      />
                    </div>

                    <!-- 没有更多数据提示 -->
                    <div
                      v-if="
                        !hasMoreData &&
                        filteredPosts.length > 0 &&
                        hasTriedLoadMore
                      "
                      class="no-more-data"
                    >
                      {{ $t('common.noMoreData') || 'No more data' }}
                    </div>
                  </div>
                </div>
              </template>
            </ElSkeleton>
          </ElScrollbar>
        </div>

        <!-- 右侧：已选值 -->
        <div class="post-selector-right">
          <div class="right-header">
            <span class="right-title">
              {{ $t('common.selected') || 'Selected' }}
              <span v-if="tempSelectedPosts.size > 0" class="right-count">
                ({{ tempSelectedPosts.size }})
              </span>
            </span>
            <ElButton
              v-if="tempSelectedPosts.size > 0"
              link
              type="danger"
              size="small"
              @click="
                () => {
                  tempSelectedPosts.clear();
                  tempSelectedPosts = new Set();
                }
              "
            >
              {{ $t('common.clear') || 'Clear' }}
            </ElButton>
          </div>
          <ElScrollbar class="right-scroll">
            <div
              v-if="tempSelectedPostsWithInfo.length === 0"
              class="right-empty"
            >
              <ElEmpty
                :image-size="64"
                :description="$t('common.noData') || 'No Data'"
              />
            </div>
            <div v-else class="right-list">
              <div
                v-for="item in tempSelectedPostsWithInfo"
                :key="item.id"
                class="right-item"
              >
                <span class="right-item-name" :title="item.name">
                  {{ item.name }}
                  <span v-if="item.code" class="right-item-code"
                    >({{ item.code }})</span
                  >
                </span>
                <ElButton
                  link
                  type="danger"
                  size="small"
                  class="right-item-remove"
                  @click="
                    () => {
                      tempSelectedPosts.delete(item.id);
                      tempSelectedPosts = new Set(tempSelectedPosts);
                    }
                  "
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
.post-selector {
  width: 100%;

  &-input {
    cursor: pointer;

    &.disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }

    :deep(.el-input) {
      &.is-disabled {
        background-color: var(--background-deep, #f5f7fa);
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
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);

    .list-search {
      flex-shrink: 0;
      padding: 12px 12px 8px;
    }

    .list-scroll {
      flex: 1;
      overflow-y: auto;
    }

    .list-skeleton,
    .list-body {
      padding: 4px 8px;
    }

    .post-list {
      display: flex;
      flex-direction: column;
    }

    .post-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 36px;
      padding: 0 12px;
      cursor: pointer;
      border-radius: 6px;
      transition: all 0.15s ease;

      &:hover {
        background-color: var(--el-fill-color-light);
      }

      &--selected {
        background-color: var(--el-color-primary-light-9);

        .post-name {
          font-weight: 500;
          color: var(--el-color-primary);
        }
      }

      .post-name {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        font-size: 14px;
        text-overflow: ellipsis;
        white-space: nowrap;
        transition: color 0.15s ease;
      }

      .post-code {
        flex-shrink: 0;
        padding: 2px 6px;
        margin-left: 8px;
        font-size: 11px;
        color: hsl(var(--muted-foreground));
        white-space: nowrap;
        background: hsl(var(--background-deep) / 50%);
        border-radius: 4px;
      }
    }

    .loading-more {
      padding: 8px;
    }

    .no-more-data {
      padding: 12px;
      font-size: 12px;
      color: hsl(var(--muted-foreground));
      text-align: center;
    }
  }

  &-right {
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    width: 320px;
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

      &-name {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        font-size: 13px;
        color: hsl(var(--foreground));
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      &-code {
        font-size: 11px;
        color: hsl(var(--muted-foreground));
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

.post-skeleton-item {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  width: 100%;
  padding: 4px 8px;
}
</style>
