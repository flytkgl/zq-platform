<script lang="ts" setup>
import type { DictItem } from '#/api/core/dict';

import { computed, nextTick, onMounted, ref, watch } from 'vue';

import { IconifyIcon, Plus, Search } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElEmpty,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElScrollbar,
  ElSkeleton,
  ElSkeletonItem,
  ElTooltip,
} from 'element-plus';

import {
  createDictItemApi,
  deleteDictItemApi,
  getDictItemListApi,
  updateDictItemApi,
} from '#/api/core/dict';

const props = defineProps<{
  dictId?: string;
}>();
const dictItemList = ref<DictItem[]>([]);
const loading = ref(false);
const isLoadingMore = ref(false);
const savingNewItemId = ref<null | string>(null);
const savingEditItem = ref(false);
const searchKeyword = ref<string>('');
const newItemList = ref<
  Array<{
    icon: string;
    id: string;
    label: string;
    remark: string;
    sort: number;
    status: boolean;
    value: string;
  }>
>([]);
const editingItemId = ref<null | string>(null);
const currentPage = ref(1);
const pageSize = ref(20);
const totalItems = ref(0);
const hasLoadedMore = ref(false);
let newItemCounter = 0;
const editingFormData = ref<Partial<DictItem>>({});

// 是否还有更多数据
const hasMoreData = computed(() => {
  const totalLoaded = currentPage.value * pageSize.value;
  return totalLoaded < totalItems.value;
});

// 计算过滤后的字典项列表
const filteredDictItemList = computed(() => {
  if (!searchKeyword.value.trim()) {
    return dictItemList.value;
  }

  const keyword = searchKeyword.value.toLowerCase();
  return dictItemList.value.filter(
    (item) =>
      item.label?.toLowerCase().includes(keyword) ||
      false ||
      item.value?.toLowerCase().includes(keyword) ||
      false,
  );
});

async function fetchDictItemList(isLoadMore = false) {
  if (!props.dictId) {
    dictItemList.value = [];
    return;
  }

  if (isLoadMore) {
    isLoadingMore.value = true;
  } else {
    loading.value = true;
    currentPage.value = 1;
    hasLoadedMore.value = false;
  }

  try {
    const response = await getDictItemListApi({
      page: currentPage.value,
      pageSize: pageSize.value,
      dict_id: props.dictId,
    });

    dictItemList.value =
      currentPage.value === 1
        ? response.items || []
        : [...dictItemList.value, ...(response.items || [])];
    totalItems.value = response.total || 0;
  } finally {
    if (isLoadMore) {
      isLoadingMore.value = false;
    } else {
      loading.value = false;
    }
  }
}

/**
 * 重置并重新加载
 */
function reload() {
  currentPage.value = 1;
  hasLoadedMore.value = false;
  fetchDictItemList();
}

/**
 * 处理滚动到底部
 */
async function handleScrollToBottom() {
  if (isLoadingMore.value || !hasMoreData.value || loading.value) {
    return;
  }

  hasLoadedMore.value = true;
  currentPage.value += 1;
  await fetchDictItemList(true);
}

/**
 * 打开添加字典项输入行
 */
function onAddDictItem() {
  // 自动计算排序值：最大排序值 + 1
  const existingSorts = [
    ...dictItemList.value.map((item) => item.sort || 0),
    ...newItemList.value.map((item) => item.sort || 0),
  ];
  const maxSort = existingSorts.length > 0 ? Math.max(...existingSorts) : 0;
  newItemCounter++;
  newItemList.value.unshift({
    id: `new_${Date.now()}_${newItemCounter}`,
    label: '',
    value: '',
    icon: '',
    sort: maxSort + 1,
    status: true,
    remark: '',
  });

  // 滚动到顶部
  nextTick(() => {
    const scrollbar = document.querySelector('.dict-item-scrollbar');
    if (scrollbar) {
      const scrollElement = scrollbar.querySelector('.el-scrollbar__wrap');
      if (scrollElement) {
        scrollElement.scrollTop = 0;
      }
    }
  });
}

/**
 * 保存新字典项
 */
async function onSaveNewItem(newItem: {
  icon: string;
  id: string;
  label: string;
  remark: string;
  sort: number;
  status: boolean;
  value: string;
}) {
  if (!newItem.label || !newItem.value) {
    ElMessage.warning(
      $t('ui.formRules.required', [
        `${$t('dict.itemLabel')}/${$t('dict.itemValue')}`,
      ]),
    );
    return;
  }

  try {
    savingNewItemId.value = newItem.id;
    await createDictItemApi({
      dict_id: props.dictId!,
      label: newItem.label,
      value: newItem.value,
      icon: newItem.icon,
      sort: newItem.sort,
      status: newItem.status,
      remark: newItem.remark,
    });
    ElMessage.success(
      $t('ui.actionMessage.createSuccess', [$t('dict.itemName')]),
    );
    newItemList.value = newItemList.value.filter((i) => i.id !== newItem.id);
    await reload();
  } catch {
    ElMessage.error($t('ui.actionMessage.createError'));
  } finally {
    savingNewItemId.value = null;
  }
}

/**
 * 取消新增
 */
function onCancelNewItem(newItemId: string) {
  newItemList.value = newItemList.value.filter((i) => i.id !== newItemId);
}

/**
 * 打开编辑字典项（在当前行编辑）
 */
function onEditDictItem(item: DictItem) {
  editingItemId.value = item.id;
  editingFormData.value = { ...item };
}

/**
 * 保存编辑的字典项
 */
async function onSaveEditItem() {
  if (!editingFormData.value.label || !editingFormData.value.value) {
    ElMessage.warning(
      $t('ui.formRules.required', [
        `${$t('dict.itemLabel')}/${$t('dict.itemValue')}`,
      ]),
    );
    return;
  }

  try {
    savingEditItem.value = true;
    await updateDictItemApi(editingItemId.value!, editingFormData.value);
    ElMessage.success(
      $t('ui.actionMessage.updateSuccess', [$t('dict.itemName')]),
    );
    editingItemId.value = null;
    editingFormData.value = {};
    await reload();
  } catch {
    ElMessage.error($t('ui.actionMessage.updateError'));
  } finally {
    savingEditItem.value = false;
  }
}

/**
 * 取消编辑
 */
function onCancelEdit() {
  editingItemId.value = null;
  editingFormData.value = {};
}

/**
 * 删除字典项
 */
async function onDeleteDictItem(item: DictItem) {
  ElMessageBox.confirm(
    $t('ui.actionMessage.deleteConfirm', [item.label || item.value]),
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
        await deleteDictItemApi(item.id);
        ElMessage.success(
          $t('ui.actionMessage.deleteSuccess', [item.label || item.value]),
        );
        await reload();
      } catch {
        ElMessage.error($t('ui.actionMessage.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

// 监听 dictId 变化
watch(
  () => props.dictId,
  () => {
    reload();
  },
);

// 监听搜索文本变化
watch(searchKeyword, () => {
  reload();
});

onMounted(() => {
  reload();
});
</script>

<template>
  <ElCard
    shadow="never"
    style="border: none"
    class="flex h-full flex-col"
    :body-style="{
      display: 'flex',
      flexDirection: 'column',
      flex: 1,
      padding: '0',
      overflow: 'hidden',
      minHeight: 0,
    }"
  >
    <template #header>
      <div class="flex w-full items-center justify-between">
        <span>{{ $t('dict.itemName') }}</span>
        <div class="flex items-center gap-2">
          <ElInput
            v-model="searchKeyword"
            :placeholder="$t('common.search')"
            clearable
            :prefix-icon="Search"
            :disabled="!dictId"
            class="w-40"
          />
          <ElTooltip :content="$t('common.add')" placement="top">
            <ElButton :icon="Plus" :disabled="!dictId" @click="onAddDictItem" />
          </ElTooltip>
        </div>
      </div>
    </template>

    <!-- 骨架屏加载状态 -->
    <div v-if="dictId && loading" class="p-4">
      <ElSkeleton :rows="10" animated>
        <template #template>
          <div class="space-y-2">
            <div
              v-for="i in 10"
              :key="i"
              class="rounded-lg border border-gray-200 bg-white p-4"
            >
              <div class="flex items-end gap-4">
                <div class="flex flex-1 flex-col">
                  <ElSkeletonItem
                    variant="text"
                    style="width: 60px; height: 16px; margin-bottom: 8px"
                  />
                  <ElSkeletonItem
                    variant="button"
                    style="width: 100%; height: 32px"
                  />
                </div>
                <div class="flex flex-1 flex-col">
                  <ElSkeletonItem
                    variant="text"
                    style="width: 60px; height: 16px; margin-bottom: 8px"
                  />
                  <ElSkeletonItem
                    variant="button"
                    style="width: 100%; height: 32px"
                  />
                </div>
                <div class="flex w-20 flex-col">
                  <ElSkeletonItem
                    variant="text"
                    style="width: 40px; height: 16px; margin-bottom: 8px"
                  />
                  <ElSkeletonItem
                    variant="button"
                    style="width: 100%; height: 32px"
                  />
                </div>
                <div class="flex flex-shrink-0 items-center justify-end gap-2">
                  <ElSkeletonItem
                    variant="circle"
                    style="width: 32px; height: 32px"
                  />
                  <ElSkeletonItem
                    variant="circle"
                    style="width: 32px; height: 32px"
                  />
                </div>
              </div>
            </div>
          </div>
        </template>
      </ElSkeleton>
    </div>

    <!-- 空状态 - 居中显示 -->
    <div
      v-else-if="
        dictId &&
        filteredDictItemList.length === 0 &&
        newItemList.length === 0 &&
        !loading
      "
      class="flex h-full items-center justify-center"
    >
      <ElEmpty :description="$t('dict.noData')" />
    </div>

    <!-- 字典项列表 - 卡片式布局 -->
    <ElScrollbar
      v-else-if="dictId"
      class="dict-item-scrollbar"
      :distance="40"
      @end-reached="handleScrollToBottom"
    >
      <div class="p-4">
        <div class="space-y-2">
          <!-- 新增行 -->
          <div
            v-for="newItem in newItemList"
            :key="newItem.id"
            class="border-primary rounded-lg border bg-blue-50 p-4"
          >
            <!-- 标签、值、排序和操作在同一行 -->
            <div class="flex items-end gap-4">
              <!-- 标签 -->
              <div class="flex flex-1 flex-col">
                <label class="mb-1 text-xs font-medium text-gray-600">
                  {{ $t('dict.itemLabel') }} *
                </label>
                <ElInput
                  v-model="newItem.label"
                  :placeholder="$t('dict.itemLabel')"
                  class="text-sm"
                />
              </div>

              <!-- 值 -->
              <div class="flex flex-1 flex-col">
                <label class="mb-1 text-xs font-medium text-gray-600">
                  {{ $t('dict.itemValue') }} *
                </label>
                <ElInput
                  v-model="newItem.value"
                  :placeholder="$t('dict.itemValue')"
                  class="text-sm"
                />
              </div>

              <!-- 排序 -->
              <div class="flex w-20 flex-col">
                <label class="mb-1 text-xs font-medium text-gray-600">
                  {{ $t('dict.sort') }}
                </label>
                <ElInput
                  v-model.number="newItem.sort"
                  type="number"
                  :placeholder="$t('dict.sort')"
                  class="text-sm"
                />
              </div>

              <!-- 操作按钮 -->
              <div class="flex flex-shrink-0 items-center justify-end gap-2">
                <ElTooltip :content="$t('common.save')" placement="top">
                  <ElButton
                    type="success"
                    text
                    size="small"
                    :loading="savingNewItemId === newItem.id"
                    @click="onSaveNewItem(newItem)"
                  >
                    <IconifyIcon
                      v-if="savingNewItemId !== newItem.id"
                      icon="ep:check"
                      class="size-4"
                    />
                  </ElButton>
                </ElTooltip>
                <ElTooltip :content="$t('common.cancel')" placement="top">
                  <ElButton
                    type="warning"
                    text
                    size="small"
                    :disabled="savingNewItemId === newItem.id"
                    @click="onCancelNewItem(newItem.id)"
                  >
                    <IconifyIcon icon="ep:close" class="size-4" />
                  </ElButton>
                </ElTooltip>
              </div>
            </div>
          </div>

          <!-- 现有项列表 -->
          <div
            v-for="item in filteredDictItemList"
            :key="item.id"
            class="rounded-lg border bg-white p-4 transition-all"
            :class="[
              editingItemId === item.id
                ? 'border-primary bg-blue-50'
                : 'hover:border-primary border-gray-200 hover:shadow-md',
            ]"
          >
            <!-- 标签、值、排序和操作在同一行 -->
            <div class="flex items-end gap-4">
              <!-- 标签 -->
              <div class="flex flex-1 flex-col">
                <label class="mb-1 text-xs font-medium text-gray-600">
                  {{ $t('dict.itemLabel') }}
                </label>
                <ElInput
                  v-if="editingItemId === item.id"
                  v-model="editingFormData.label"
                  :placeholder="$t('dict.itemLabel')"
                  class="text-sm"
                />
                <ElInput
                  v-else
                  :model-value="item.label"
                  :placeholder="$t('dict.itemLabel')"
                  disabled
                  class="text-sm"
                />
              </div>

              <!-- 值 -->
              <div class="flex flex-1 flex-col">
                <label class="mb-1 text-xs font-medium text-gray-600">
                  {{ $t('dict.itemValue') }}
                </label>
                <ElInput
                  v-if="editingItemId === item.id"
                  v-model="editingFormData.value"
                  :placeholder="$t('dict.itemValue')"
                  class="text-sm"
                />
                <ElInput
                  v-else
                  :model-value="item.value"
                  :placeholder="$t('dict.itemValue')"
                  disabled
                  class="text-sm"
                />
              </div>

              <!-- 排序 -->
              <div class="flex w-20 flex-col">
                <label class="mb-1 text-xs font-medium text-gray-600">
                  {{ $t('dict.sort') }}
                </label>
                <ElInput
                  v-if="editingItemId === item.id"
                  v-model.number="editingFormData.sort"
                  type="number"
                  class="text-sm"
                />
                <ElInput
                  v-else
                  :model-value="item.sort"
                  type="number"
                  disabled
                  class="text-sm"
                />
              </div>

              <!-- 操作按钮 -->
              <div class="flex flex-shrink-0 items-center justify-end">
                <template v-if="editingItemId === item.id">
                  <!-- 编辑状态下的保存和取消 -->
                  <ElTooltip :content="$t('common.save')" placement="top">
                    <ElButton
                      type="success"
                      text
                      size="small"
                      :loading="savingEditItem"
                      @click="onSaveEditItem"
                    >
                      <IconifyIcon
                        v-if="!savingEditItem"
                        icon="ep:check"
                        class="size-4"
                      />
                    </ElButton>
                  </ElTooltip>
                  <ElTooltip :content="$t('common.cancel')" placement="top">
                    <ElButton
                      type="warning"
                      text
                      size="small"
                      :disabled="savingEditItem"
                      @click="onCancelEdit"
                    >
                      <IconifyIcon icon="ep:close" class="size-4" />
                    </ElButton>
                  </ElTooltip>
                </template>
                <template v-else>
                  <!-- 正常状态下的编辑和删除 -->
                  <ElTooltip :content="$t('dict.edit')" placement="top">
                    <ElButton
                      type="primary"
                      text
                      size="small"
                      @click="onEditDictItem(item)"
                    >
                      <IconifyIcon icon="ep:edit" class="size-4" />
                    </ElButton>
                  </ElTooltip>
                  <ElTooltip :content="$t('common.delete')" placement="top">
                    <ElButton
                      type="danger"
                      text
                      size="small"
                      @click="onDeleteDictItem(item)"
                    >
                      <IconifyIcon icon="ep:delete" class="size-4" />
                    </ElButton>
                  </ElTooltip>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载更多提示 -->
        <div v-if="isLoadingMore" class="flex items-center justify-center py-4">
          <div class="loading-spinner"></div>
          <span class="ml-2 text-sm text-gray-500">{{
            $t('common.loading')
          }}</span>
        </div>

        <!-- 无更多数据提示 -->
        <div
          v-else-if="
            filteredDictItemList.length > 0 && !hasMoreData && hasLoadedMore
          "
          class="py-4 text-center text-sm text-gray-500"
        >
          {{ $t('common.noMore') || 'No more data' }}
        </div>
      </div>
    </ElScrollbar>

    <!-- 未选择字典时的空状态 -->
    <div v-else class="flex h-full items-center justify-center">
      <ElEmpty :description="$t('dict.selectDictFirst')" />
    </div>
  </ElCard>
</template>

<style scoped>
.dict-item-scrollbar {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--el-color-primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
