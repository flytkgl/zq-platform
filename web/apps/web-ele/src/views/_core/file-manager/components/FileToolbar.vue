<script setup lang="ts">
import { computed, ref } from 'vue';

import {
  ChevronRight,
  Home,
  LayoutGrid,
  List,
  Plus,
  RotateCw,
  Search,
  Trash2,
  Upload,
} from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElBreadcrumb,
  ElBreadcrumbItem,
  ElButton,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElProgress,
} from 'element-plus';

import { batchDelete, uploadFile } from '#/api/core/file';

import { useFileManager } from '../composables/useFileManager';

const {
  viewMode,
  breadcrumbs,
  currentFolderId,
  selectedFileIds,
  navigateToFolder,
  openCreateFolderDialog,
  fetchFiles,
  clearSelection,
} = useFileManager();

const fileInputRef = ref<HTMLInputElement | null>(null);
// ... (rest of the code)

const deleting = ref(false);

const handleBatchDelete = async () => {
  if (selectedFileIds.value.size === 0) return;

  try {
    await ElMessageBox.confirm(
      $t('file-manager.batchDeleteConfirm', {
        count: selectedFileIds.value.size,
      }),
      $t('file-manager.tip'),
      {
        type: 'warning',
        confirmButtonText: $t('file-manager.confirm'),
        cancelButtonText: $t('file-manager.cancel'),
      },
    );

    deleting.value = true;
    await batchDelete({ ids: [...selectedFileIds.value] });
    ElMessage.success($t('file-manager.deleteSuccess'));
    clearSelection();
    fetchFiles();
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error);
    }
  } finally {
    deleting.value = false;
  }
};
const folderInputRef = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const uploadProgress = ref(0);
const uploadingFileName = ref('');
const uploadedCount = ref(0);
const totalUploadCount = ref(0);

const uploadStatusText = computed(() => {
  if (!uploading.value) return '';
  if (totalUploadCount.value <= 1) return uploadingFileName.value;
  return `(${uploadedCount.value + 1}/${totalUploadCount.value}) ${uploadingFileName.value}`;
});

const handleBreadcrumbClick = (id: null | string, name: string) => {
  navigateToFolder(id, name);
};

const handleCreateFolder = () => {
  openCreateFolderDialog();
};

const handleUploadFile = () => {
  fileInputRef.value?.click();
};

const handleUploadFolder = () => {
  folderInputRef.value?.click();
};

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = target.files;

  if (!files || files.length === 0) return;

  uploading.value = true;
  uploadProgress.value = 0;
  uploadedCount.value = 0;
  totalUploadCount.value = files.length;
  let successCount = 0;
  let failCount = 0;

  try {
    for (const file of files) {
      if (!file) continue;

      uploadingFileName.value = file.name;
      uploadProgress.value = 0;

      try {
        await uploadFile(file, {
          parentId: currentFolderId.value || undefined,
          onProgress: (e) => {
            uploadProgress.value = e.percentage;
          },
        });
        successCount++;
        uploadedCount.value = successCount + failCount;
      } catch (error) {
        console.error(`Failed to upload ${file.name}`, error);
        failCount++;
        uploadedCount.value = successCount + failCount;
      }
    }

    if (successCount > 0) {
      ElMessage.success(
        $t('file-manager.uploadSuccess', { count: successCount }),
      );
      fetchFiles();
    }
    if (failCount > 0) {
      ElMessage.error($t('file-manager.uploadFailed', { count: failCount }));
    }
  } catch (error) {
    console.error(error);
    ElMessage.error($t('file-manager.uploadError'));
  } finally {
    uploading.value = false;
    uploadProgress.value = 0;
    uploadingFileName.value = '';
    target.value = '';
  }
};
</script>

<template>
  <div class="border-border border-b">
    <div class="flex items-center justify-between px-4 py-3">
      <!-- Hidden Inputs -->
      <input
        ref="fileInputRef"
        type="file"
        multiple
        class="hidden"
        @change="handleFileChange"
      />
      <input
        ref="folderInputRef"
        type="file"
        webkitdirectory
        class="hidden"
        @change="handleFileChange"
      />

      <!-- Breadcrumbs -->
      <div class="mr-4 flex flex-1 items-center overflow-hidden">
        <ElBreadcrumb :separator-icon="ChevronRight">
          <ElBreadcrumbItem
            v-for="(item, index) in breadcrumbs"
            :key="item.id || 'root'"
          >
            <span
              class="hover:text-primary flex cursor-pointer items-center gap-1"
              :class="{
                'text-foreground font-bold': index === breadcrumbs.length - 1,
              }"
              @click="handleBreadcrumbClick(item.id, item.name)"
            >
              <Home v-if="index === 0" class="size-4" />
              {{ item.name }}
            </span>
          </ElBreadcrumbItem>
        </ElBreadcrumb>
      </div>

      <!-- Actions -->
      <div class="flex flex-shrink-0 items-center gap-2 sm:gap-3">
        <ElInput :placeholder="$t('file-manager.search')" class="w-32 sm:w-48">
          <template #prefix>
            <Search class="size-4" />
          </template>
        </ElInput>

        <div class="flex items-center rounded-lg border p-1">
          <button
            class="hover:bg-accent p-2"
            :class="{ 'bg-accent text-primary': viewMode === 'list' }"
            @click="viewMode = 'list'"
            :title="$t('file-manager.listView')"
          >
            <List class="size-4" />
          </button>
          <button
            class="hover:bg-accent p-2"
            :class="{ 'bg-accent text-primary': viewMode === 'grid' }"
            @click="viewMode = 'grid'"
            :title="$t('file-manager.gridView')"
          >
            <LayoutGrid class="size-4" />
          </button>
        </div>

        <ElButton circle @click="fetchFiles">
          <template #icon>
            <RotateCw class="size-4" :class="{ 'animate-spin': uploading }" />
          </template>
        </ElButton>

        <ElButton
          v-if="selectedFileIds.size > 0"
          type="danger"
          plain
          :loading="deleting"
          @click="handleBatchDelete"
        >
          <Trash2 v-if="!deleting" class="mr-2 size-4" />
          {{ $t('file-manager.batchDelete') }}
        </ElButton>

        <ElButton
          type="primary"
          plain
          @click="handleCreateFolder"
          class="hidden sm:flex"
        >
          <Plus class="mr-2 size-4" /> {{ $t('file-manager.newFolder') }}
        </ElButton>

        <ElDropdown trigger="click">
          <ElButton type="primary" :loading="uploading" class="hidden sm:flex">
            <Upload class="mr-2 size-4" /> {{ $t('file-manager.upload') }}
          </ElButton>
          <ElButton
            circle
            type="primary"
            :loading="uploading"
            class="flex sm:hidden"
          >
            <Plus class="size-4" />
          </ElButton>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem @click="handleUploadFile">
                {{ $t('file-manager.uploadFile') }}
              </ElDropdownItem>
              <ElDropdownItem @click="handleUploadFolder">
                {{ $t('file-manager.uploadFolder') }}
              </ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
      </div>
    </div>

    <!-- 上传进度条 -->
    <div v-if="uploading" class="flex items-center gap-3 px-4 py-2">
      <span class="text-muted-foreground max-w-48 truncate text-xs">
        {{ uploadStatusText }}
      </span>
      <ElProgress
        :percentage="uploadProgress"
        :stroke-width="6"
        class="flex-1"
      />
    </div>
  </div>
</template>
