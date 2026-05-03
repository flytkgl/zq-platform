import type { SystemFileManagerApi } from '#/api/core/file';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { getFileList } from '#/api/core/file';

// 使用单例模式或者在顶层组件 provide
const currentFolderId = ref<null | string>(null);
const viewMode = ref<'grid' | 'list'>('grid');
const selectedFileIds = ref<Set<string>>(new Set());
const fileList = ref<SystemFileManagerApi.FileItem[]>([]);
const loading = ref(false);
const loadingMore = ref(false);
const breadcrumbs = ref<Array<{ id: null | string; name: string }>>([
  { id: null, name: $t('file-manager.myFiles') },
]);
const createFolderDialogVisible = ref(false);

// 无限滚动分页状态
const currentPage = ref(1);
const pageSize = ref(50);
const total = ref(0);
const noMore = computed(() => fileList.value.length >= total.value);

export function useFileManager() {
  const toggleViewMode = () => {
    viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid';
  };

  const fetchFiles = async () => {
    currentPage.value = 1;
    loading.value = true;
    try {
      const res = await getFileList({
        parent_id: currentFolderId.value,
        page: 1,
        pageSize: pageSize.value,
      });
      fileList.value = res.items;
      total.value = res.total;
    } catch (error) {
      console.error(error);
    } finally {
      loading.value = false;
    }
  };

  const loadMore = async () => {
    if (noMore.value || loadingMore.value || loading.value) return;
    loadingMore.value = true;
    currentPage.value++;
    try {
      const res = await getFileList({
        parent_id: currentFolderId.value,
        page: currentPage.value,
        pageSize: pageSize.value,
      });
      fileList.value = [...fileList.value, ...res.items];
      total.value = res.total;
    } catch (error) {
      console.error(error);
      currentPage.value--;
    } finally {
      loadingMore.value = false;
    }
  };

  const navigateToFolder = (folderId: null | string, folderName?: string) => {
    currentFolderId.value = folderId;
    selectedFileIds.value.clear();

    // 更新面包屑 (这里只是简单的逻辑，实际可能需要根据树结构查找完整路径)
    if (folderId === null) {
      breadcrumbs.value = [{ id: null, name: $t('file-manager.myFiles') }];
    } else if (folderName) {
      // 如果是点击面包屑导航回去，需要截断
      const index = breadcrumbs.value.findIndex((b) => b.id === folderId);
      if (index === -1) {
        // 进入新文件夹
        breadcrumbs.value.push({ id: folderId, name: folderName });
      } else {
        breadcrumbs.value = breadcrumbs.value.slice(0, index + 1);
      }
    }
    // fetchFiles 由 FileList.vue 中的 watch(currentFolderId) 自动触发
  };

  const toggleSelection = (id: string, multi: boolean) => {
    if (multi) {
      if (selectedFileIds.value.has(id)) {
        selectedFileIds.value.delete(id);
      } else {
        selectedFileIds.value.add(id);
      }
    } else {
      selectedFileIds.value.clear();
      selectedFileIds.value.add(id);
    }
  };

  const clearSelection = () => {
    selectedFileIds.value.clear();
  };

  const openCreateFolderDialog = () => {
    createFolderDialogVisible.value = true;
  };

  return {
    currentFolderId,
    viewMode,
    selectedFileIds,
    fileList,
    loading,
    loadingMore,
    noMore,
    breadcrumbs,
    createFolderDialogVisible,
    toggleViewMode,
    navigateToFolder,
    toggleSelection,
    clearSelection,
    fetchFiles,
    loadMore,
    openCreateFolderDialog,
  };
}
