<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';

import { Folder, MoreVertical } from '@vben/icons';
import { $t } from '@vben/locales';
import { useUserStore } from '@vben/stores';

import {
  ElCheckbox,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElMessage,
  ElMessageBox,
  ElImageViewer as ImageViewer,
  ElInfiniteScroll as vInfiniteScroll,
} from 'element-plus';

import { deleteItem } from '#/api/core/file';
import { getFileTypeIcon } from '#/assets/file-icons';
import { getFileUrl } from '#/composables/useFileUrl';

import { useFileManager } from '../composables/useFileManager';
import RenameDialog from './RenameDialog.vue';

const {
  currentFolderId,
  viewMode,
  fileList,
  loading,
  loadingMore,
  noMore,
  selectedFileIds,
  navigateToFolder,
  fetchFiles,
  loadMore,
  clearSelection,
} = useFileManager();

const renameDialogVisible = ref(false);
const currentItem = ref<any>(null);

// 图片预览状态
const previewVisible = ref(false);
const previewUrlList = ref<string[]>([]);
const previewInitialIndex = ref(0);

// 图片URL缓存映射
const imageUrlMap = ref<Map<string, string>>(new Map());

// 获取图片URL（从缓存中获取）
function getImageUrl(id: string): string {
  return imageUrlMap.value.get(id) || '';
}

// 批量加载文件列表中所有图片的URL
async function loadImageUrls() {
  const images = fileList.value.filter(
    (f) => isImage(f.file_ext) && f.id && !imageUrlMap.value.has(f.id),
  );
  if (images.length === 0) return;

  // 并发批量获取所有图片URL
  const results = await Promise.allSettled(
    images.map(async (img) => {
      const url = await getFileUrl(img.id!);
      return { id: img.id!, url };
    }),
  );

  for (const result of results) {
    if (result.status === 'fulfilled' && result.value.url) {
      imageUrlMap.value.set(result.value.id, result.value.url);
    }
  }
}

// 全选相关计算属性
const isAllSelected = computed(() => {
  return (
    fileList.value.length > 0 &&
    selectedFileIds.value.size === fileList.value.length
  );
});

const isIndeterminate = computed(() => {
  return (
    selectedFileIds.value.size > 0 &&
    selectedFileIds.value.size < fileList.value.length
  );
});

// 处理全选
const handleSelectAll = (val: any) => {
  if (val) {
    fileList.value.forEach((item) => selectedFileIds.value.add(item.id!));
  } else {
    clearSelection();
  }
};

// 监听文件夹变化，自动刷新列表并清空选中
watch(currentFolderId, () => {
  clearSelection();
  imageUrlMap.value.clear();
  fetchFiles();
});

// 监听文件列表变化，加载图片URL
watch(
  fileList,
  () => {
    loadImageUrls();
  },
  { immediate: true },
);

onMounted(fetchFiles);

// 处理 Grid/List 选中
const handleGridSelect = (id: string, value: boolean) => {
  if (value) {
    selectedFileIds.value.add(id);
  } else {
    selectedFileIds.value.delete(id);
  }
};

const isImage = (ext?: string) => {
  if (!ext) return false;
  const extension = ext.toLowerCase().replace('.', '');
  return ['bmp', 'gif', 'jpeg', 'jpg', 'png', 'svg', 'webp'].includes(
    extension,
  );
};

const isFolder = (item: any) => {
  return (item.file_type || item.fileType || item.type) === 'folder';
};

// 单击选中/取消选中
const handleItemClick = (item: any) => {
  const id = item.id!;
  if (selectedFileIds.value.has(id)) {
    selectedFileIds.value.delete(id);
  } else {
    selectedFileIds.value.clear();
    selectedFileIds.value.add(id);
  }
};

// 双击打开
const handleItemOpen = async (item: any) => {
  const type = item.file_type || item.fileType || item.type;

  if (type === 'folder') {
    navigateToFolder(item.id, item.name);
  } else if (isImage(item.file_ext)) {
    const images = fileList.value.filter((f) => isImage(f.file_ext));
    const urls = await Promise.all(images.map((img) => getFileUrl(img.id!)));
    previewUrlList.value = urls;

    const index = images.findIndex((img) => img.id === item.id);
    previewInitialIndex.value = index === -1 ? 0 : index;

    previewVisible.value = true;
  } else {
    const query = new URLSearchParams({
      name: item.name || '',
      ext: item.file_ext || '',
    });
    window.open(`/file-preview/${item.id}?${query.toString()}`, '_blank');
  }
};

const closePreview = () => {
  previewVisible.value = false;
};

const handleDownload = async (item: any) => {
  if (isFolder(item)) {
    ElMessage.warning($t('file-manager.folderDownloadNotSupported'));
    return;
  }

  try {
    // 获取带 token 的 URL
    const tokenUrl = await getFileUrl(item.id);
    // 添加 download 参数
    const downloadUrl = `${tokenUrl + (tokenUrl.includes('?') ? '&' : '?')}download=true`;

    // 使用 fetch 获取文件 blob
    const response = await fetch(downloadUrl);
    if (!response.ok) {
      throw new Error(`下载失败: ${response.status}`);
    }
    const blob = await response.blob();

    // 创建 blob URL 并下载
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = item.name || 'download';
    document.body.append(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('下载文件失败:', error);
    ElMessage.error($t('file-manager.downloadFailed') || '下载文件失败');
  }
};

const handleDelete = async (item: any) => {
  try {
    await ElMessageBox.confirm(
      $t('file-manager.deleteConfirm', { name: item.name }),
      $t('file-manager.tip'),
      {
        type: 'warning',
        confirmButtonText: $t('file-manager.confirm'),
        cancelButtonText: $t('file-manager.cancel'),
      },
    );

    await deleteItem(item.id);
    ElMessage.success($t('file-manager.deleteSuccess'));
    fetchFiles();
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error);
    }
  }
};

const openRenameDialog = (item: any) => {
  currentItem.value = item;
  renameDialogVisible.value = true;
};

const handleAction = (action: string, item: any) => {
  switch (action) {
    case 'delete': {
      handleDelete(item);
      break;
    }
    case 'download': {
      handleDownload(item);
      break;
    }
    case 'open': {
      handleItemOpen(item);
      break;
    }
    case 'rename': {
      openRenameDialog(item);
      break;
    }
  }
};

// 判断当前用户是否可以操作该文件（重命名/删除）
const userStore = useUserStore();
debugger;
const canOperate = (item: any) => {
  // 系统文件夹不可操作
  if (item.is_system) return false;
  // 超管可以操作所有文件
  if (userStore.userRoles?.includes('super')) return true;
  // 普通用户只能操作自己的文件
  return item.sys_creator_id === userStore.userInfo?.userId;
};

// 格式化大小
const formatSize = (size?: number) => {
  if (size === undefined || size === null) return '-';
  if (size === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  let s = size;
  while (s >= 1024 && i < units.length - 1) {
    s /= 1024;
    i++;
  }
  return `${s.toFixed(2)} ${units[i]}`;
};
</script>

<template>
  <div
    v-loading="loading"
    v-infinite-scroll="loadMore"
    :infinite-scroll-disabled="noMore || loadingMore"
    :infinite-scroll-distance="200"
    class="h-full w-full overflow-y-auto"
  >
    <div
      v-if="fileList.length === 0 && !loading"
      class="flex h-full items-center justify-center"
    >
      <ElEmpty :description="$t('file-manager.noFiles')" />
    </div>

    <!-- Grid View -->
    <template v-else-if="viewMode === 'grid'">
      <div class="bg-background sticky top-0 z-20 flex items-center px-4 py-2">
        <ElCheckbox
          :model-value="isAllSelected"
          :indeterminate="isIndeterminate"
          @change="handleSelectAll"
        >
          {{ $t('file-manager.selectAll') }}
          {{ selectedFileIds.size > 0 ? `(${selectedFileIds.size})` : '' }}
        </ElCheckbox>
      </div>
      <div
        class="grid grid-cols-2 gap-4 px-4 py-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6"
      >
        <div
          v-for="item in fileList"
          :key="item.id"
          class="border-border bg-card hover:bg-accent group relative flex cursor-pointer flex-col rounded-lg border p-4 transition-colors"
          :class="{
            'ring-primary bg-accent ring-2': selectedFileIds.has(item.id!),
          }"
          @click="handleItemClick(item)"
          @dblclick="handleItemOpen(item)"
        >
          <!-- Checkbox for Grid -->
          <div class="absolute left-2 top-2 z-10" @click.stop>
            <ElCheckbox
              :model-value="selectedFileIds.has(item.id!)"
              @change="(val) => handleGridSelect(item.id!, Boolean(val))"
            />
          </div>

          <!-- 操作按钮 -->
          <div class="absolute right-2 top-2 z-10" @click.stop>
            <ElDropdown trigger="click">
              <button
                class="invisible rounded-full p-1 hover:bg-gray-200 group-hover:visible dark:hover:bg-gray-700"
              >
                <MoreVertical class="size-4 text-gray-500" />
              </button>
              <template #dropdown>
                <ElDropdownMenu>
                  <ElDropdownItem @click="handleAction('open', item)">
                    {{ $t('file-manager.open') }}
                  </ElDropdownItem>
                  <ElDropdownItem
                    v-if="!isFolder(item)"
                    @click="handleAction('download', item)"
                  >
                    {{ $t('file-manager.download') }}
                  </ElDropdownItem>
                  <ElDropdownItem
                    v-if="canOperate(item)"
                    divided
                    @click="handleAction('rename', item)"
                  >
                    {{ $t('file-manager.rename') }}
                  </ElDropdownItem>
                  <ElDropdownItem
                    v-if="canOperate(item)"
                    class="text-red-500"
                    @click="handleAction('delete', item)"
                  >
                    {{ $t('file-manager.delete') }}
                  </ElDropdownItem>
                </ElDropdownMenu>
              </template>
            </ElDropdown>
          </div>

          <div
            class="flex flex-1 items-center justify-center overflow-hidden py-4"
          >
            <template v-if="isImage(item.file_ext)">
              <img
                v-if="getImageUrl(item.id!)"
                :src="getImageUrl(item.id!)"
                class="h-16 w-full object-contain"
                loading="lazy"
              />
              <div
                v-else
                class="bg-muted h-16 w-full animate-pulse rounded"
              ></div>
            </template>
            <Folder v-else-if="isFolder(item)" class="size-16 text-blue-500" />
            <img v-else :src="getFileTypeIcon(item.file_ext)" class="size-16" />
          </div>
          <div class="px-2 text-center">
            <span
              class="block truncate text-sm font-medium"
              :title="item.name"
              >{{ item.name }}</span
            >
          </div>
        </div>
      </div>
    </template>

    <!-- List View -->
    <template v-else>
      <div class="bg-background sticky top-0 z-20 flex items-center px-4 py-2">
        <ElCheckbox
          :model-value="isAllSelected"
          :indeterminate="isIndeterminate"
          @change="handleSelectAll"
        >
          {{ $t('file-manager.selectAll') }}
          {{ selectedFileIds.size > 0 ? `(${selectedFileIds.size})` : '' }}
        </ElCheckbox>
      </div>
      <!-- 列表表头 -->
      <div
        class="text-muted-foreground flex items-center gap-3 border-b border-[var(--el-border-color)] px-4 py-2 text-xs font-medium"
      >
        <div class="w-8"></div>
        <div class="w-8"></div>
        <div class="min-w-0 flex-1">{{ $t('file-manager.name') }}</div>
        <div class="hidden w-24 text-right sm:block">
          {{ $t('file-manager.size') }}
        </div>
        <div class="hidden w-40 text-right md:block">
          {{ $t('file-manager.modifiedTime') }}
        </div>
        <div class="w-8"></div>
      </div>
      <!-- 列表行 -->
      <div class="px-4">
        <div
          v-for="item in fileList"
          :key="item.id"
          class="hover:bg-accent group flex cursor-pointer items-center gap-3 rounded-md px-0 py-2 transition-colors"
          :class="{
            'bg-accent': selectedFileIds.has(item.id!),
          }"
          @click="handleItemClick(item)"
          @dblclick="handleItemOpen(item)"
        >
          <!-- Checkbox -->
          <div class="w-8 flex-shrink-0 text-center" @click.stop>
            <ElCheckbox
              :model-value="selectedFileIds.has(item.id!)"
              @change="(val) => handleGridSelect(item.id!, Boolean(val))"
            />
          </div>
          <!-- 图标 -->
          <div class="flex w-8 flex-shrink-0 items-center justify-center">
            <template v-if="isImage(item.file_ext)">
              <img
                v-if="getImageUrl(item.id!)"
                :src="getImageUrl(item.id!)"
                class="size-6 rounded object-cover"
                loading="lazy"
              />
              <div v-else class="bg-muted size-6 animate-pulse rounded"></div>
            </template>
            <Folder v-else-if="isFolder(item)" class="size-6 text-blue-500" />
            <img v-else :src="getFileTypeIcon(item.file_ext)" class="size-6" />
          </div>
          <!-- 文件名 -->
          <div class="min-w-0 flex-1">
            <span class="block truncate text-sm" :title="item.name">{{
              item.name
            }}</span>
          </div>
          <!-- 大小 -->
          <div
            class="text-muted-foreground hidden w-24 flex-shrink-0 text-right text-xs sm:block"
          >
            {{ isFolder(item) ? '-' : formatSize(item.file_size || item.size) }}
          </div>
          <!-- 修改时间 -->
          <div
            class="text-muted-foreground hidden w-40 flex-shrink-0 text-right text-xs md:block"
          >
            {{ item.updated_time?.substring(0, 16) }}
          </div>
          <!-- 操作 -->
          <div class="w-8 flex-shrink-0 text-center" @click.stop>
            <ElDropdown trigger="click">
              <button
                class="invisible rounded-full p-1 hover:bg-gray-200 group-hover:visible dark:hover:bg-gray-700"
              >
                <MoreVertical class="size-4 text-gray-500" />
              </button>
              <template #dropdown>
                <ElDropdownMenu>
                  <ElDropdownItem @click="handleAction('open', item)">
                    {{ $t('file-manager.open') }}
                  </ElDropdownItem>
                  <ElDropdownItem
                    v-if="!isFolder(item)"
                    @click="handleAction('download', item)"
                  >
                    {{ $t('file-manager.download') }}
                  </ElDropdownItem>
                  <ElDropdownItem
                    v-if="canOperate(item)"
                    divided
                    @click="handleAction('rename', item)"
                  >
                    {{ $t('file-manager.rename') }}
                  </ElDropdownItem>
                  <ElDropdownItem
                    v-if="canOperate(item)"
                    class="text-red-500"
                    @click="handleAction('delete', item)"
                  >
                    {{ $t('file-manager.delete') }}
                  </ElDropdownItem>
                </ElDropdownMenu>
              </template>
            </ElDropdown>
          </div>
        </div>
      </div>
    </template>

    <!-- 无限滚动加载提示 -->
    <div
      v-if="fileList.length > 0"
      class="text-muted-foreground flex items-center justify-center py-4 text-xs"
    >
      <template v-if="loadingMore">
        <span class="mr-2 animate-spin">&#9696;</span>
        {{ $t('common.loading') }}
      </template>
      <template v-else-if="noMore">
        {{ $t('common.noMore') }}
      </template>
    </div>

    <RenameDialog v-model:visible="renameDialogVisible" :item="currentItem" />

    <ImageViewer
      v-if="previewVisible"
      :url-list="previewUrlList"
      :initial-index="previewInitialIndex"
      @close="closePreview"
    />
  </div>
</template>
