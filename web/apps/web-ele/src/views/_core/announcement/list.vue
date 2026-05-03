<script lang="ts" setup>
import type { UserAnnouncement } from '#/api/core/announcement';

import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';

import { Loader2, RotateCw, Search } from '@vben/icons';
import { $t } from '@vben/locales';

import dayjs from 'dayjs';
import {
  ElBadge,
  ElEmpty,
  ElInput,
  ElOption,
  ElSelect,
  ElSkeleton,
  ElSkeletonItem,
  ElTag,
} from 'element-plus';

import {
  getUnreadAnnouncementCountApi,
  getUserAnnouncementListApi,
  markAnnouncementReadApi,
} from '#/api/core/announcement';
import { FuPage } from '#/components/fu-page';

defineOptions({ name: 'AnnouncementList' });

// 未读数量
const unreadCount = ref(0);

// 列表相关
const searchKeyword = ref('');
const unreadFilter = ref('');
const list = ref<UserAnnouncement[]>([]);
const loading = ref(false);
const loadingMore = ref(false);
const refreshing = ref(false);
const pagination = ref({ current: 1, pageSize: 20, total: 0 });
const hasMore = computed(() => list.value.length < pagination.value.total);
const reachedEnd = ref(false);

// 列表根元素引用（用于查找滚动容器）
const listRootRef = ref<HTMLElement>();
let scrollEl: HTMLElement | null = null;

// 选中的公告
const selectedItem = ref<null | UserAnnouncement>(null);
const detailLoading = ref(false);

// 优先级映射
type TagType = 'danger' | 'info' | 'warning';
const priorityMap: Record<number, { label: string; type: TagType }> = {
  0: { label: $t('announcement.priorityNormal'), type: 'info' },
  1: { label: $t('announcement.priorityImportant'), type: 'warning' },
  2: { label: $t('announcement.priorityUrgent'), type: 'danger' },
};

// 加载未读数量
async function loadUnreadCount() {
  try {
    const res = await getUnreadAnnouncementCountApi();
    unreadCount.value = res.count;
  } catch (error) {
    console.error('加载未读数量失败:', error);
  }
}

// 加载列表
async function loadList() {
  list.value = [];
  loading.value = true;
  pagination.value.current = 1;
  reachedEnd.value = false;
  try {
    const res = await getUserAnnouncementListApi({
      page: 1,
      pageSize: pagination.value.pageSize,
      unread_only: unreadFilter.value === 'true',
    });
    list.value = res.items || [];
    pagination.value.total = res.total || 0;

    if (list.value.length > 0 && !selectedItem.value) {
      handleSelect(list.value[0]!);
    }
  } catch (error: any) {
    console.error('加载列表失败:', error);
  } finally {
    loading.value = false;
  }
}

// 加载更多
async function loadMore() {
  if (loadingMore.value || loading.value || !hasMore.value) return;
  loadingMore.value = true;
  const nextPage = pagination.value.current + 1;
  try {
    const res = await getUserAnnouncementListApi({
      page: nextPage,
      pageSize: pagination.value.pageSize,
      unread_only: unreadFilter.value === 'true',
    });
    list.value = [...list.value, ...(res.items || [])];
    pagination.value.current = nextPage;
    pagination.value.total = res.total || 0;
    if (list.value.length >= pagination.value.total) {
      reachedEnd.value = true;
    }
  } catch (error: any) {
    console.error('加载更多失败:', error);
  } finally {
    loadingMore.value = false;
  }
}

// 刷新
async function handleRefresh() {
  refreshing.value = true;
  await loadList();
  await loadUnreadCount();
  refreshing.value = false;
}

// 搜索
function handleSearch() {
  selectedItem.value = null;
  loadList();
}

// 选中公告并标记已读
async function handleSelect(item: UserAnnouncement) {
  selectedItem.value = item;
  detailLoading.value = true;

  if (!item.is_read) {
    try {
      await markAnnouncementReadApi(item.id);
      item.is_read = true;
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    } catch (error) {
      console.error('标记已读失败:', error);
    }
  }

  // 短暂延迟让骨架屏展示
  setTimeout(() => {
    detailLoading.value = false;
  }, 300);
}

// 格式化时间
function formatTime(time: null | string | undefined) {
  if (!time) return '-';
  return dayjs(time).format('YYYY-MM-DD HH:mm');
}

// 滚动加载：监听最近的 ElScrollbar 滚动容器
function handleScroll() {
  if (!scrollEl || loading.value || loadingMore.value || !hasMore.value) return;
  const { scrollTop, scrollHeight, clientHeight } = scrollEl;
  if (scrollHeight - scrollTop - clientHeight < 100) {
    loadMore();
  }
}

function initScrollListener() {
  let el: HTMLElement | null = listRootRef.value ?? null;
  while (el) {
    if (el.classList.contains('el-scrollbar__wrap')) {
      scrollEl = el;
      break;
    }
    el = el.parentElement;
  }
  scrollEl?.addEventListener('scroll', handleScroll);
}

function destroyScrollListener() {
  scrollEl?.removeEventListener('scroll', handleScroll);
  scrollEl = null;
}

onMounted(async () => {
  await Promise.all([loadList(), loadUnreadCount()]);
  await nextTick();
  initScrollListener();
});

onBeforeUnmount(() => {
  destroyScrollListener();
});
</script>

<template>
  <FuPage
    left-width="320px"
    :left-min-width="280"
    :left-max-width="450"
    :left-padding="false"
    :right-padding="false"
  >
    <!-- 左侧头部 -->
    <template #left-header>
      <div class="flex w-full items-center gap-2 pt-3">
        <ElInput
          v-model="searchKeyword"
          :placeholder="$t('announcement.keywordPlaceholder')"
          clearable
          size="default"
          class="flex-1"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <Search class="h-3.5 w-3.5" />
          </template>
        </ElInput>
        <ElSelect
          v-model="unreadFilter"
          :placeholder="$t('announcement.status')"
          clearable
          size="default"
          style="width: 85px"
          @change="handleSearch"
        >
          <ElOption value="" :label="$t('announcement.unreadOnlyAll')" />
          <ElOption value="true" :label="$t('announcement.unreadOnlyUnread')" />
        </ElSelect>
        <RotateCw
          class="h-4 w-4 shrink-0 cursor-pointer text-[var(--el-text-color-secondary)] transition-colors hover:text-[var(--el-color-primary)]"
          :class="{ 'animate-spin': refreshing }"
          @click="handleRefresh"
        />
        <ElBadge
          v-if="unreadCount > 0"
          :value="unreadCount"
          :max="99"
          class="shrink-0"
        >
          <ElTag type="danger" size="small">
            {{ $t('announcement.unreadLabel') }}
          </ElTag>
        </ElBadge>
      </div>
    </template>

    <!-- 左侧列表 -->
    <template #left>
      <div ref="listRootRef" class="px-4">
        <!-- 骨架屏 -->
        <template v-if="loading && list.length === 0">
          <div
            v-for="i in 8"
            :key="i"
            class="mb-2 rounded-lg border border-transparent p-3"
          >
            <ElSkeleton :rows="0" animated>
              <template #template>
                <div class="mb-2 flex items-center justify-between">
                  <ElSkeletonItem variant="text" style="width: 60%" />
                  <ElSkeletonItem
                    variant="text"
                    style="width: 50px; height: 14px"
                  />
                </div>
                <!-- <div class="mb-2">
                  <ElSkeletonItem variant="text" style="width: 90%; height: 14px" />
                </div> -->
                <div class="flex items-center justify-between">
                  <ElSkeletonItem
                    variant="text"
                    style="width: 80px; height: 14px"
                  />
                  <ElSkeletonItem
                    variant="text"
                    style="width: 60px; height: 14px"
                  />
                </div>
              </template>
            </ElSkeleton>
          </div>
        </template>

        <!-- 列表内容 -->
        <template v-else-if="list.length > 0">
          <div
            v-for="item in list"
            :key="item.id"
            class="mb-2 cursor-pointer rounded-[8px] p-3 transition-colors"
            :class="[
              selectedItem?.id === item.id
                ? 'bg-primary/15 dark:bg-accent text-primary'
                : 'hover:bg-[var(--el-fill-color-light)]',
            ]"
            @click="handleSelect(item)"
          >
            <!-- 标题行 -->
            <div class="mb-2 flex items-start justify-between gap-2 text-sm">
              <div class="flex flex-1 items-center gap-1.5 truncate">
                <span
                  v-if="!item.is_read"
                  class="h-2 w-2 shrink-0 rounded-full bg-[var(--el-color-danger)]"
                ></span>
                <ElTag
                  v-if="item.is_top"
                  type="danger"
                  size="small"
                  class="shrink-0"
                >
                  {{ $t('announcement.topTag') }}
                </ElTag>
                <span
                  class="truncate"
                  :class="{ 'font-medium': !item.is_read }"
                  :title="item.title"
                >
                  {{ item.title }}
                </span>
              </div>
              <ElTag
                :type="priorityMap[item.priority]?.type || 'info'"
                size="small"
                class="shrink-0"
              >
                {{
                  priorityMap[item.priority]?.label ||
                  $t('announcement.priorityNormal')
                }}
              </ElTag>
            </div>
            <!-- 摘要 -->
            <!-- <div
              v-if="item.summary"
              class="text-muted-foreground mb-2 line-clamp-2 text-xs"
            >
              {{ item.summary }}
            </div> -->
            <!-- 底部信息 -->
            <div class="mt-2 flex items-center justify-between">
              <span class="text-muted-foreground text-xs">
                {{ item.publisher_name }}
              </span>
              <span class="text-muted-foreground text-xs">
                {{ formatTime(item.publish_time) }}
              </span>
            </div>
          </div>

          <!-- 加载更多 / 没有更多 -->
          <div class="py-4 text-center">
            <div
              v-if="loadingMore"
              class="text-muted-foreground flex items-center justify-center gap-2 text-xs"
            >
              <Loader2 class="h-4 w-4 animate-spin" />
              {{ $t('announcement.loadingMore') }}
            </div>
            <span v-else-if="reachedEnd" class="text-muted-foreground text-xs">
              {{ $t('announcement.noMore') }}
            </span>
          </div>
        </template>

        <!-- 空状态 -->
        <ElEmpty v-else :description="$t('announcement.emptyList')" />
      </div>
    </template>

    <!-- 右侧头部 -->
    <template #right-header>
      <div class="flex items-center justify-between">
        <span class="text-sm font-medium">
          {{ selectedItem?.title || $t('announcement.detailTitle') }}
        </span>
        <div
          v-if="selectedItem"
          class="flex items-center gap-2 text-xs text-[var(--el-text-color-secondary)]"
        >
          <span>{{ selectedItem.publisher_name }}</span>
          <span>{{ formatTime(selectedItem.publish_time) }}</span>
          <ElTag
            :type="priorityMap[selectedItem.priority]?.type || 'info'"
            size="small"
          >
            {{
              priorityMap[selectedItem.priority]?.label ||
              $t('announcement.priorityNormal')
            }}
          </ElTag>
        </div>
      </div>
    </template>

    <!-- 右侧内容 -->
    <template #right>
      <!-- 未选中 -->
      <div v-if="!selectedItem" class="flex h-full items-center justify-center">
        <ElEmpty :description="$t('announcement.selectHint')" />
      </div>

      <!-- 骨架屏 -->
      <div v-else-if="detailLoading" class="p-5">
        <ElSkeleton :rows="0" animated>
          <template #template>
            <!-- 标题骨架 -->
            <ElSkeletonItem variant="h1" style="width: 50%; height: 24px" />
            <div class="mt-3 flex items-center gap-3">
              <ElSkeletonItem
                variant="text"
                style="width: 80px; height: 14px"
              />
              <ElSkeletonItem
                variant="text"
                style="width: 120px; height: 14px"
              />
              <ElSkeletonItem
                variant="text"
                style="width: 60px; height: 20px; border-radius: 4px"
              />
            </div>
            <!-- 摘要骨架 -->
            <div class="mt-5 rounded bg-[var(--el-fill-color-lighter)] p-3">
              <ElSkeletonItem
                variant="text"
                style="width: 100%; height: 14px"
              />
              <ElSkeletonItem
                variant="text"
                style="width: 80%; height: 14px; margin-top: 8px"
              />
            </div>
            <!-- 正文骨架 -->
            <div class="mt-5 flex flex-col gap-3">
              <ElSkeletonItem
                variant="text"
                style="width: 100%; height: 14px"
              />
              <ElSkeletonItem variant="text" style="width: 95%; height: 14px" />
              <ElSkeletonItem variant="text" style="width: 88%; height: 14px" />
              <ElSkeletonItem
                variant="text"
                style="width: 100%; height: 14px"
              />
              <ElSkeletonItem variant="text" style="width: 70%; height: 14px" />
            </div>
            <!-- 图片占位 -->
            <ElSkeletonItem
              variant="image"
              style="
                width: 100%;
                height: 180px;
                margin-top: 20px;
                border-radius: 8px;
              "
            />
            <!-- 更多正文骨架 -->
            <div class="mt-5 flex flex-col gap-3">
              <ElSkeletonItem
                variant="text"
                style="width: 100%; height: 14px"
              />
              <ElSkeletonItem variant="text" style="width: 92%; height: 14px" />
              <ElSkeletonItem variant="text" style="width: 85%; height: 14px" />
              <ElSkeletonItem variant="text" style="width: 60%; height: 14px" />
            </div>
          </template>
        </ElSkeleton>
      </div>

      <!-- 详情内容 -->
      <div v-else class="h-full overflow-y-auto p-5">
        <!-- 摘要 -->
        <div
          v-if="selectedItem.summary"
          class="mb-4 border-l-4 border-[var(--el-color-primary)] bg-[var(--el-fill-color-light)] py-3 pl-4 pr-3 text-sm text-[var(--el-text-color-regular)]"
        >
          {{ selectedItem.summary }}
        </div>

        <!-- 富文本内容 -->
        <div
          class="announcement-content prose max-w-none"
          v-html="selectedItem.content"
        ></div>
      </div>
    </template>
  </FuPage>
</template>

<style scoped>
.announcement-content :deep(img) {
  max-width: 100%;
}

.announcement-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
}

.announcement-content :deep(td),
.announcement-content :deep(th) {
  border: 1px solid var(--el-border-color);
  padding: 8px;
}

.announcement-content :deep(blockquote) {
  border-left: 4px solid var(--el-border-color);
  padding-left: 16px;
  margin: 8px 0;
  color: var(--el-text-color-secondary);
}

.announcement-content :deep(a) {
  color: var(--el-color-primary);
  text-decoration: underline;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
