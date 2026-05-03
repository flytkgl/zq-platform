<script lang="ts" setup>
import type { FormInstance, FormRules } from 'element-plus';

import type {
  Announcement,
  AnnouncementCreate,
  AnnouncementListItem,
} from '#/api/core/announcement';

import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue';

import {
  ArrowLeft,
  Edit,
  Eye,
  Loader2,
  Play,
  Plus,
  RotateCw,
  Save,
  Search,
  Trash2,
} from '@vben/icons';
import { $t } from '@vben/locales';

import dayjs from 'dayjs';
import {
  ElButton,
  ElDatePicker,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElSelect,
  ElSkeleton,
  ElSkeletonItem,
  ElSwitch,
  ElTag,
} from 'element-plus';

import {
  createAnnouncementApi,
  deleteAnnouncementApi,
  getAnnouncementDetailApi,
  getAnnouncementListApi,
  getReadStatsApi,
  publishAnnouncementApi,
  updateAnnouncementApi,
} from '#/api/core/announcement';
import { FuPage } from '#/components/fu-page';
import { UserAvatar } from '#/components/user-avatar';
import { ZqDrawer } from '#/components/zq-drawer';
import { RichTextEditor } from '#/components/zq-form/rich-text-editor';

defineOptions({ name: 'AnnouncementManager' });

// ============ 右侧面板模式: view / create / edit ============
type PanelMode = 'create' | 'edit' | 'view';
const panelMode = ref<PanelMode>('view');
const saving = ref(false);
const formRef = ref<FormInstance>();
const formRules: FormRules = {
  title: [
    {
      required: true,
      message: () => $t('announcement.formTitleRequired'),
      trigger: 'blur',
    },
  ],
  content: [
    {
      required: true,
      message: () => $t('announcement.formContentRequired'),
      trigger: 'blur',
    },
  ],
};

// ============ 列表相关 ============

const searchKeyword = ref('');
const statusFilter = ref('');
const list = ref<AnnouncementListItem[]>([]);
const loading = ref(false);
const loadingMore = ref(false);
const refreshing = ref(false);
const pagination = ref({ current: 1, pageSize: 20, total: 0 });
const hasMore = computed(() => list.value.length < pagination.value.total);
const reachedEnd = ref(false);

// 选中的公告
const selectedItem = ref<AnnouncementListItem | null>(null);
// 右侧详情数据
const detailData = ref<Announcement | null>(null);
const detailLoading = ref(false);

// 是否处于编辑/新增模式
const isEditing = computed(
  () => panelMode.value === 'create' || panelMode.value === 'edit',
);

// 状态映射
type TagType = 'danger' | 'info' | 'success' | 'warning';
const statusMap: Record<string, { label: string; type: TagType }> = {
  draft: { label: $t('announcement.statusDraft'), type: 'info' },
  published: { label: $t('announcement.statusPublished'), type: 'success' },
  expired: { label: $t('announcement.statusExpired'), type: 'warning' },
};

// 优先级映射
const priorityMap: Record<number, { label: string; type: TagType }> = {
  0: { label: $t('announcement.priorityNormal'), type: 'info' },
  1: { label: $t('announcement.priorityImportant'), type: 'warning' },
  2: { label: $t('announcement.priorityUrgent'), type: 'danger' },
};

// 接收范围映射
const targetTypeMap: Record<string, string> = {
  all: $t('announcement.targetTypeAll'),
  dept: $t('announcement.targetTypeDept'),
  role: $t('announcement.targetTypeRole'),
  user: $t('announcement.targetTypeUser'),
};

// 加载列表
async function loadList() {
  list.value = [];
  loading.value = true;
  pagination.value.current = 1;
  reachedEnd.value = false;
  try {
    const res = await getAnnouncementListApi({
      page: 1,
      pageSize: pagination.value.pageSize,
      keyword: searchKeyword.value || undefined,
      status: statusFilter.value || undefined,
    });
    list.value = res.items || [];
    pagination.value.total = res.total || 0;

    if (
      list.value.length > 0 &&
      !selectedItem.value &&
      panelMode.value === 'view'
    ) {
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
    const res = await getAnnouncementListApi({
      page: nextPage,
      pageSize: pagination.value.pageSize,
      keyword: searchKeyword.value || undefined,
      status: statusFilter.value || undefined,
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
  refreshing.value = false;
}

// 搜索
function handleSearch() {
  if (isEditing.value) return;
  selectedItem.value = null;
  detailData.value = null;
  loadList();
}

// 选中公告
async function handleSelect(item: AnnouncementListItem) {
  if (isEditing.value) return;
  selectedItem.value = item;
  panelMode.value = 'view';
  detailLoading.value = true;
  try {
    detailData.value = await getAnnouncementDetailApi(item.id);
  } catch (error: any) {
    console.error('加载详情失败:', error);
    detailData.value = null;
  } finally {
    detailLoading.value = false;
  }
}

// 格式化时间
function formatTime(time: null | string | undefined) {
  if (!time) return '-';
  return dayjs(time).format('YYYY-MM-DD HH:mm');
}

// ============ 编辑表单 ============

const editId = ref('');
const formData = ref<AnnouncementCreate>({
  title: '',
  content: '',
  summary: '',
  status: 'draft',
  priority: 0,
  is_top: false,
  target_type: 'all',
  target_ids: [],
  publish_time: undefined,
  expire_time: undefined,
});

function resetForm() {
  formData.value = {
    title: '',
    content: '',
    summary: '',
    status: 'draft',
    priority: 0,
    is_top: false,
    target_type: 'all',
    target_ids: [],
    publish_time: undefined,
    expire_time: undefined,
  };
}

// 新增 - 切换到右侧新增模式
function handleCreate() {
  editId.value = '';
  resetForm();
  panelMode.value = 'create';
}

// 编辑 - 切换到右侧编辑模式
function handleEdit() {
  if (!detailData.value) return;
  editId.value = detailData.value.id;

  formData.value = {
    title: detailData.value.title,
    content: detailData.value.content,
    summary: detailData.value.summary,
    status: detailData.value.status,
    priority: detailData.value.priority,
    is_top: detailData.value.is_top,
    target_type: detailData.value.target_type,
    target_ids: detailData.value.target_ids,
    publish_time: detailData.value.publish_time,
    expire_time: detailData.value.expire_time,
  };

  panelMode.value = 'edit';
}

// 取消编辑 - 返回查看模式
function handleCancelEdit() {
  panelMode.value = 'view';
  if (!selectedItem.value && !detailData.value) {
    panelMode.value = 'view';
  }
}

// 删除
async function handleDelete() {
  if (!selectedItem.value) return;
  const item = selectedItem.value;
  try {
    await ElMessageBox.confirm(
      $t('announcement.deleteConfirm', { title: item.title }),
      $t('announcement.deleteConfirmTitle'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        type: 'warning',
      },
    );
    await deleteAnnouncementApi(item.id);
    ElMessage.success($t('announcement.deleteSuccess'));
    selectedItem.value = null;
    detailData.value = null;
    panelMode.value = 'view';
    await loadList();
  } catch {
    // 用户取消
  }
}

// 发布
async function handlePublish() {
  if (!selectedItem.value) return;
  try {
    await ElMessageBox.confirm(
      $t('announcement.publishConfirm'),
      $t('announcement.publishConfirmTitle'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        type: 'warning',
      },
    );
    await publishAnnouncementApi(selectedItem.value.id);
    ElMessage.success($t('announcement.publishSuccess'));
    await loadList();
    if (selectedItem.value) {
      await handleSelect(selectedItem.value);
    }
  } catch {
    // 用户取消
  }
}

// 保存
async function handleSave() {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
  } catch {
    return;
  }
  saving.value = true;
  try {
    if (panelMode.value === 'edit') {
      await updateAnnouncementApi(editId.value, formData.value);
      ElMessage.success($t('announcement.updateSuccess'));
    } else {
      await createAnnouncementApi(formData.value);
      ElMessage.success($t('announcement.createSuccess'));
    }
    panelMode.value = 'view';
    await loadList();
    if (selectedItem.value) {
      await handleSelect(selectedItem.value);
    }
  } catch (error) {
    console.error('保存失败:', error);
  } finally {
    saving.value = false;
  }
}

// ============ 阅读统计抽屉 ============

const statsDrawerVisible = ref(false);
const statsLoading = ref(false);
const statsData = ref<{ readers: any[]; total_read: number }>({
  total_read: 0,
  readers: [],
});
const statsSearchKeyword = ref('');
const STATS_PAGE_SIZE = 30;
const statsDisplayCount = ref(STATS_PAGE_SIZE);

const filteredReaders = computed(() => {
  let readers = statsData.value.readers;
  if (statsSearchKeyword.value) {
    const kw = statsSearchKeyword.value.toLowerCase();
    readers = readers.filter((r: any) =>
      r.user_name?.toLowerCase().includes(kw),
    );
  }
  return readers;
});

const displayedReaders = computed(() =>
  filteredReaders.value.slice(0, statsDisplayCount.value),
);
const statsHasMore = computed(
  () => statsDisplayCount.value < filteredReaders.value.length,
);

function loadMoreReaders() {
  if (statsHasMore.value) {
    statsDisplayCount.value += STATS_PAGE_SIZE;
  }
}

watch(statsSearchKeyword, () => {
  statsDisplayCount.value = STATS_PAGE_SIZE;
});

function handleViewStats() {
  if (!selectedItem.value) return;
  statsSearchKeyword.value = '';
  statsDrawerVisible.value = true;
}

async function loadStatsData() {
  if (!selectedItem.value) return;
  statsLoading.value = true;
  try {
    const res = await getReadStatsApi(selectedItem.value.id);
    statsData.value = res;
  } catch (error) {
    console.error('获取统计失败:', error);
  } finally {
    statsLoading.value = false;
  }
}

// ============ 右侧头部标题 ============

const rightHeaderTitle = computed(() => {
  if (panelMode.value === 'create') return $t('announcement.createTitle');
  if (panelMode.value === 'edit') return $t('announcement.editTitle');
  return detailData.value?.title || $t('announcement.detailTitle');
});

// ============ 左侧滚动加载 ============

const fuPageRef = ref();
let scrollEl: HTMLElement | null = null;

function handleListScroll() {
  if (!scrollEl || loading.value || loadingMore.value || !hasMore.value) return;
  const { scrollTop, scrollHeight, clientHeight } = scrollEl;
  if (scrollHeight - scrollTop - clientHeight < 100) {
    loadMore();
  }
}

// ============ 生命周期 ============

onMounted(async () => {
  await loadList();
  await nextTick();
  // 找到 FuPage 左侧 ElScrollbar 的滚动容器（第一个 splitter panel 内的 scrollbar）
  const el = fuPageRef.value?.$el;
  if (el) {
    const leftPanel = el.querySelector('.el-splitter-panel:first-child');
    scrollEl = leftPanel?.querySelector('.el-scrollbar__wrap') as HTMLElement;
    scrollEl?.addEventListener('scroll', handleListScroll);
  }
});

onBeforeUnmount(() => {
  scrollEl?.removeEventListener('scroll', handleListScroll);
  scrollEl = null;
});
</script>

<template>
  <div>
    <FuPage
      ref="fuPageRef"
      left-width="320px"
      :left-min-width="280"
      :left-max-width="450"
      :left-padding="false"
      :right-padding="false"
    >
      <!-- 左侧头部：搜索 + 状态筛选 + 刷新 + 新增 -->
      <template #left-header>
        <div class="flex w-full items-center gap-2 pt-3">
          <ElInput
            v-model="searchKeyword"
            :placeholder="$t('announcement.keywordPlaceholder')"
            clearable
            size="default"
            class="flex-1"
            :disabled="isEditing"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          >
            <template #prefix>
              <Search class="h-3.5 w-3.5" />
            </template>
          </ElInput>
          <ElSelect
            v-model="statusFilter"
            :placeholder="$t('announcement.status')"
            clearable
            size="default"
            style="width: 85px"
            :disabled="isEditing"
            @change="handleSearch"
          >
            <ElOption value="" :label="$t('announcement.statusAll')" />
            <ElOption value="draft" :label="$t('announcement.statusDraft')" />
            <ElOption
              value="published"
              :label="$t('announcement.statusPublished')"
            />
            <ElOption
              value="expired"
              :label="$t('announcement.statusExpired')"
            />
          </ElSelect>
          <RotateCw
            class="h-4 w-4 shrink-0 cursor-pointer text-[var(--el-text-color-secondary)] transition-colors hover:text-[var(--el-color-primary)]"
            :class="{
              'animate-spin': refreshing,
              'pointer-events-none opacity-50': isEditing,
            }"
            @click="handleRefresh"
          />
          <Plus
            class="h-4.2 w-4.2 shrink-0 cursor-pointer text-[var(--el-text-color-secondary)] transition-colors hover:text-[var(--el-color-primary)]"
            :class="{ 'pointer-events-none opacity-50': isEditing }"
            @click="handleCreate"
          />
        </div>
      </template>

      <!-- 左侧列表 -->
      <template #left>
        <div class="px-4">
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
                selectedItem?.id === item.id && !isEditing
                  ? 'bg-primary/15 dark:bg-accent text-primary'
                  : 'hover:bg-[var(--el-fill-color-light)]',
                isEditing ? 'pointer-events-none opacity-60' : '',
              ]"
              @click="handleSelect(item)"
            >
              <!-- 标题行 -->
              <div class="mb-2 flex items-start justify-between gap-2 text-sm">
                <div class="flex flex-1 items-center gap-1.5 truncate">
                  <ElTag
                    v-if="item.is_top"
                    type="danger"
                    size="small"
                    class="shrink-0"
                  >
                    {{ $t('announcement.topTag') }}
                  </ElTag>
                  <span class="truncate" :title="item.title">
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
                <div class="flex items-center gap-1.5">
                  <ElTag
                    :type="statusMap[item.status]?.type || 'info'"
                    size="small"
                  >
                    {{ statusMap[item.status]?.label || item.status }}
                  </ElTag>
                </div>
                <span class="text-muted-foreground text-xs">
                  {{ formatTime(item.publish_time || item.created_at) }}
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
              <span
                v-else-if="reachedEnd"
                class="text-muted-foreground text-xs"
              >
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
          <div class="flex items-center gap-2">
            <!-- 编辑模式下显示返回按钮 -->
            <ArrowLeft
              v-if="isEditing"
              class="h-4 w-4 shrink-0 cursor-pointer text-[var(--el-text-color-secondary)] transition-colors hover:text-[var(--el-color-primary)]"
              @click="handleCancelEdit"
            />
            <span class="text-sm font-medium">{{ rightHeaderTitle }}</span>
          </div>
          <!-- 查看模式操作按钮 -->
          <div
            v-if="panelMode === 'view' && detailData"
            class="flex items-center gap-1"
          >
            <ElButton
              v-if="detailData.status === 'draft'"
              text
              size="small"
              type="success"
              :icon="Play"
              @click="handlePublish"
            >
              {{ $t('announcement.publishButton') }}
            </ElButton>
            <ElButton
              v-if="detailData.status === 'published'"
              text
              size="small"
              :icon="Eye"
              @click="handleViewStats"
            >
              {{ $t('announcement.statsButton') }}
            </ElButton>
            <ElButton
              text
              size="small"
              type="primary"
              :icon="Edit"
              @click="handleEdit"
            >
              {{ $t('announcement.editButton') }}
            </ElButton>
            <ElButton
              text
              size="small"
              type="danger"
              :icon="Trash2"
              @click="handleDelete"
            >
              {{ $t('announcement.deleteButton') }}
            </ElButton>
          </div>
          <!-- 编辑模式操作按钮 -->
          <div v-if="isEditing" class="flex items-center gap-1">
            <ElButton size="small" @click="handleCancelEdit">
              {{ $t('announcement.formCancelButton') }}
            </ElButton>
            <ElButton
              type="primary"
              size="small"
              :icon="Save"
              :loading="saving"
              @click="handleSave"
            >
              {{ $t('announcement.formSaveButton') }}
            </ElButton>
          </div>
        </div>
      </template>

      <!-- 右侧内容 -->
      <template #right>
        <!-- ========== 编辑/新增模式 ========== -->
        <div v-if="isEditing" class="h-full overflow-y-auto p-5">
          <ElForm
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="100px"
            label-position="top"
          >
            <ElFormItem
              :label="$t('announcement.formTitleLabel')"
              prop="title"
              required
            >
              <ElInput
                v-model="formData.title"
                :placeholder="$t('announcement.formTitlePlaceholder')"
              />
            </ElFormItem>
            <ElFormItem :label="$t('announcement.formSummaryLabel')">
              <ElInput
                v-model="formData.summary"
                type="textarea"
                :rows="2"
                :placeholder="$t('announcement.formSummaryPlaceholder')"
              />
            </ElFormItem>
            <div class="grid grid-cols-2 gap-4">
              <ElFormItem :label="$t('announcement.formPriorityLabel')">
                <ElSelect v-model="formData.priority" style="width: 100%">
                  <ElOption
                    :value="0"
                    :label="$t('announcement.priorityNormal')"
                  />
                  <ElOption
                    :value="1"
                    :label="$t('announcement.priorityImportant')"
                  />
                  <ElOption
                    :value="2"
                    :label="$t('announcement.priorityUrgent')"
                  />
                </ElSelect>
              </ElFormItem>
              <ElFormItem :label="$t('announcement.formTopLabel')">
                <ElSwitch v-model="formData.is_top" />
              </ElFormItem>
              <ElFormItem :label="$t('announcement.formTargetTypeLabel')">
                <ElSelect v-model="formData.target_type" style="width: 100%">
                  <ElOption
                    value="all"
                    :label="$t('announcement.targetTypeAll')"
                  />
                  <ElOption
                    value="dept"
                    :label="$t('announcement.targetTypeDept')"
                  />
                  <ElOption
                    value="role"
                    :label="$t('announcement.targetTypeRole')"
                  />
                  <ElOption
                    value="user"
                    :label="$t('announcement.targetTypeUser')"
                  />
                </ElSelect>
              </ElFormItem>
              <ElFormItem :label="$t('announcement.formExpireTimeLabel')">
                <ElDatePicker
                  v-model="formData.expire_time"
                  type="datetime"
                  :placeholder="$t('announcement.formExpireTimePlaceholder')"
                  style="width: 100%"
                />
              </ElFormItem>
            </div>
            <ElFormItem
              :label="$t('announcement.formContentLabel')"
              prop="content"
              required
            >
              <RichTextEditor
                v-model="formData.content"
                class="w-full"
                :placeholder="$t('announcement.formContentPlaceholder')"
                :min-height="200"
                :max-height="500"
                :toolbar-config="{
                  groups: [
                    'history',
                    'heading',
                    'format',
                    'color',
                    'align',
                    'list',
                    'insert',
                    'blockquote',
                    'divider',
                    'clear',
                  ],
                  insert: {
                    link: true,
                    image: true,
                    table: true,
                    attachment: true,
                    video: true,
                  },
                }"
              />
            </ElFormItem>
          </ElForm>
        </div>

        <!-- ========== 查看模式 ========== -->
        <template v-else>
          <!-- 未选中 -->
          <div
            v-if="!selectedItem"
            class="flex h-full items-center justify-center"
          >
            <ElEmpty :description="$t('announcement.selectHint')" />
          </div>

          <!-- 加载中 - 骨架屏 -->
          <div v-else-if="detailLoading" class="h-full p-5">
            <!-- 元信息骨架 -->
            <div class="mb-4 flex items-center gap-3">
              <ElSkeletonItem
                variant="button"
                style="width: 60px; height: 22px; border-radius: 4px"
              />
              <ElSkeletonItem
                variant="button"
                style="width: 50px; height: 22px; border-radius: 4px"
              />
              <ElSkeletonItem
                variant="text"
                style="width: 120px; height: 14px"
              />
              <ElSkeletonItem
                variant="text"
                style="width: 100px; height: 14px"
              />
              <ElSkeletonItem
                variant="text"
                style="width: 140px; height: 14px"
              />
            </div>
            <!-- 摘要骨架 -->
            <div class="mb-4 rounded bg-[var(--el-fill-color-light)] p-3">
              <ElSkeletonItem variant="text" style="width: 90%; height: 14px" />
            </div>
            <!-- 内容骨架 -->
            <div class="flex flex-col gap-3">
              <ElSkeletonItem
                variant="text"
                style="width: 100%; height: 16px"
              />
              <ElSkeletonItem variant="text" style="width: 95%; height: 16px" />
              <ElSkeletonItem variant="text" style="width: 80%; height: 16px" />
              <ElSkeletonItem
                variant="text"
                style="width: 100%; height: 16px"
              />
              <ElSkeletonItem variant="text" style="width: 60%; height: 16px" />
              <div class="mt-2">
                <ElSkeletonItem
                  variant="image"
                  style="width: 100%; height: 200px; border-radius: 8px"
                />
              </div>
              <ElSkeletonItem variant="text" style="width: 90%; height: 16px" />
              <ElSkeletonItem variant="text" style="width: 75%; height: 16px" />
            </div>
          </div>

          <!-- 详情内容 -->
          <div v-else-if="detailData" class="h-full overflow-y-auto p-5">
            <!-- 元信息 -->
            <div
              class="mb-4 flex flex-wrap items-center gap-3 text-sm text-[var(--el-text-color-secondary)]"
            >
              <ElTag
                :type="statusMap[detailData.status]?.type || 'info'"
                size="small"
              >
                {{ statusMap[detailData.status]?.label || detailData.status }}
              </ElTag>
              <ElTag
                :type="priorityMap[detailData.priority]?.type || 'info'"
                size="small"
              >
                {{
                  priorityMap[detailData.priority]?.label ||
                  $t('announcement.priorityNormal')
                }}
              </ElTag>
              <span>{{ $t('announcement.publisherLabel') }}:
                {{ detailData.publisher_name || '-' }}</span>
              <span>{{ $t('announcement.targetType') }}:
                {{
                  targetTypeMap[detailData.target_type] ||
                  detailData.target_type
                }}</span>
              <span>{{ $t('announcement.publishTimeLabel') }}:
                {{ formatTime(detailData.publish_time) }}</span>
              <span v-if="detailData.expire_time">{{ $t('announcement.formExpireTimeLabel') }}:
                {{ formatTime(detailData.expire_time) }}</span>
              <span>{{ $t('announcement.readCount') }}:
                {{ detailData.read_count }}</span>
            </div>

            <!-- 摘要 -->
            <div
              v-if="detailData.summary"
              class="mb-4 border-l-4 border-[var(--el-color-primary)] bg-[var(--el-fill-color-light)] py-3 pl-4 pr-3 text-sm text-[var(--el-text-color-regular)]"
            >
              {{ detailData.summary }}
            </div>

            <!-- 富文本内容 -->
            <div
              class="announcement-content prose max-w-none"
              v-html="detailData.content"
            ></div>
          </div>
        </template>
      </template>
    </FuPage>

    <!-- 阅读统计抽屉 -->
    <ZqDrawer
      v-model="statsDrawerVisible"
      :title="$t('announcement.statsTitle')"
      size="400px"
      :show-footer="false"
      :loading="statsLoading"
      :close-on-click-modal="true"
      @open="loadStatsData"
    >
      <!-- 统计概览 -->
      <div
        class="mb-4 flex items-center gap-3 rounded-lg bg-[var(--el-fill-color-light)] p-4"
      >
        <div class="text-2xl font-semibold text-[var(--el-color-primary)]">
          {{ statsData.total_read }}
        </div>
        <div class="text-sm text-[var(--el-text-color-secondary)]">
          {{
            $t('announcement.statsReadCount', { count: statsData.total_read })
          }}
        </div>
      </div>

      <!-- 搜索 + 标题 -->
      <div class="mb-3 flex items-center justify-between">
        <span class="text-muted-foreground text-xs">
          {{ $t('announcement.statsUserLabel') }}
          <template
            v-if="
              statsSearchKeyword &&
              filteredReaders.length !== statsData.readers.length
            "
          >
            ({{ filteredReaders.length }}/{{ statsData.readers.length }})
          </template>
        </span>
        <ElInput
          v-if="statsData.readers.length > 10"
          v-model="statsSearchKeyword"
          :placeholder="$t('announcement.keywordPlaceholder')"
          clearable
          size="small"
          style="width: 150px"
        >
          <template #prefix>
            <Search class="h-3 w-3" />
          </template>
        </ElInput>
      </div>

      <!-- 读者列表 -->
      <div v-if="statsData.readers.length === 0 && !statsLoading" class="py-6">
        <ElEmpty :description="$t('common.noData')" />
      </div>
      <div
        v-else-if="filteredReaders.length === 0 && !statsLoading"
        class="py-6"
      >
        <ElEmpty :description="$t('common.noData')" />
      </div>
      <div
        v-else
        v-infinite-scroll="loadMoreReaders"
        :infinite-scroll-disabled="!statsHasMore"
        :infinite-scroll-distance="100"
        class="stats-reader-list"
      >
        <div
          v-for="reader in displayedReaders"
          :key="reader.user_id"
          class="flex items-center justify-between rounded-lg px-3 py-2 transition-colors hover:bg-[var(--el-fill-color-light)]"
        >
          <div class="flex items-center gap-3">
            <UserAvatar
              :user-id="reader.user_id"
              :name="reader.user_name"
              :size="32"
              :font-size="13"
              :shadow="false"
            />
            <span class="text-sm">{{ reader.user_name }}</span>
          </div>
          <span class="text-muted-foreground text-xs">{{
            formatTime(reader.read_at)
          }}</span>
        </div>
        <div
          v-if="statsHasMore"
          class="text-muted-foreground flex items-center justify-center py-3 text-xs"
        >
          <Loader2 class="mr-1 h-3 w-3 animate-spin" />
          {{ $t('announcement.loadingMore') }}
        </div>
      </div>
    </ZqDrawer>
  </div>
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

.stats-reader-list {
  max-height: calc(100vh - 320px);
  overflow-y: auto;
}
</style>
