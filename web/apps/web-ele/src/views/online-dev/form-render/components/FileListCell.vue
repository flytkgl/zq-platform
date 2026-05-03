<script lang="ts" setup>
import { computed, ref, watch } from 'vue';

import { Download, FileText } from '@vben/icons';

import {
  ElButton,
  ElMessage,
  ElPopover,
  ElScrollbar,
  ElSkeleton,
  ElSkeletonItem,
  ElTooltip,
} from 'element-plus';

import { getFilesInfo } from '#/api/core/file';
import { getFileUrl } from '#/composables/useFileUrl';

interface FileInfo {
  id: string;
  name: string;
  size: number;
  mime_type?: string;
}

const props = defineProps<{
  fileIds: string[];
}>();

const downloadingFiles = ref<Set<string>>(new Set());
const filesInfo = ref<FileInfo[]>([]);
const loading = ref(false);
const hasLoadedInfo = ref(false);

const fileCount = computed(() => props.fileIds.length);

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Number.parseFloat((bytes / k ** i).toFixed(1))} ${sizes[i]}`;
}

// 加载文件信息
async function loadFilesInfo() {
  if (props.fileIds.length === 0) {
    filesInfo.value = [];
    return;
  }

  loading.value = true;
  try {
    const result = await getFilesInfo(props.fileIds);
    filesInfo.value = result.map((item: any) => ({
      id: item.id,
      name: item.name || '未知文件',
      size: item.size || 0,
      mime_type: item.mime_type,
    }));
    hasLoadedInfo.value = true;
  } catch (error) {
    console.error('获取文件信息失败:', error);
    // 降级处理：使用 ID 作为文件名
    filesInfo.value = props.fileIds.map((id, index) => ({
      id,
      name: `文件 ${index + 1}`,
      size: 0,
    }));
  } finally {
    loading.value = false;
  }
}

// 弹窗显示时加载文件信息
function handlePopoverShow() {
  if (!hasLoadedInfo.value) {
    loadFilesInfo();
  }
}

// 下载文件
async function handleDownload(file: FileInfo) {
  if (downloadingFiles.value.has(file.id)) return;

  downloadingFiles.value.add(file.id);
  try {
    // 获取带 token 的 URL
    const tokenUrl = await getFileUrl(file.id);
    // 添加 download 参数
    const downloadUrl = `${tokenUrl + (tokenUrl.includes('?') ? '&' : '?')}download=true`;

    // 使用 fetch 获取文件 blob
    const response = await fetch(downloadUrl);
    if (!response.ok) {
      throw new Error(`下载失败: ${response.status}`);
    }
    const blob = await response.blob();

    // 创建 blob URL
    const url = window.URL.createObjectURL(blob);

    // 创建隐藏的 a 标签触发下载
    const link = document.createElement('a');
    link.href = url;
    link.download = file.name || 'download';
    document.body.append(link);
    link.click();
    link.remove();

    // 清理 blob URL
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('下载文件失败:', error);
    ElMessage.error('下载文件失败');
  } finally {
    downloadingFiles.value.delete(file.id);
  }
}

// 监听 fileIds 变化时重置加载状态
watch(
  () => props.fileIds,
  () => {
    hasLoadedInfo.value = false;
    filesInfo.value = [];
  },
  { deep: true },
);
</script>

<template>
  <div class="file-list-cell">
    <ElPopover
      v-if="fileCount > 0"
      placement="bottom-start"
      :width="280"
      trigger="click"
      @show="handlePopoverShow"
    >
      <template #reference>
        <ElButton link type="primary" class="file-trigger">
          <FileText class="mr-1" :style="{ width: '14px', height: '14px' }" />
          {{ fileCount }} {{ fileCount === 1 ? '个文件' : '个文件' }}
        </ElButton>
      </template>

      <div class="file-popover-content">
        <div class="popover-header">
          <span class="popover-title">文件列表</span>
        </div>

        <div style="height: 160px; overflow: hidden">
          <ElScrollbar v-if="!loading" max-height="200px">
            <div class="popover-file-list">
              <div
                v-for="file in filesInfo"
                :key="file.id"
                class="popover-file-item"
              >
                <FileText class="popover-file-icon" />
                <div class="popover-file-info">
                  <ElTooltip :content="file.name" placement="top">
                    <span class="popover-file-name">{{ file.name }}</span>
                  </ElTooltip>
                  <span class="popover-file-size">{{
                    formatFileSize(file.size)
                  }}</span>
                </div>
                <ElButton
                  text
                  type="primary"
                  size="small"
                  :loading="downloadingFiles.has(file.id)"
                  @click="handleDownload(file)"
                >
                  <Download :style="{ width: '14px', height: '14px' }" />
                </ElButton>
              </div>
            </div>
          </ElScrollbar>

          <!-- 骨架屏加载状态 -->
          <div v-else class="popover-file-list" style="padding: 12px">
            <div
              v-for="i in 3"
              :key="i"
              class="popover-file-item"
              style="margin-bottom: 12px"
            >
              <ElSkeleton animated>
                <template #template>
                  <div style="display: flex; align-items: center; gap: 8px">
                    <ElSkeletonItem
                      variant="circle"
                      style="width: 16px; height: 16px"
                    />
                    <div style="flex: 1">
                      <ElSkeletonItem
                        variant="text"
                        style="width: 90%; margin-bottom: 4px"
                      />
                    </div>
                    <ElSkeletonItem
                      variant="button"
                      style="width: 24px; height: 24px"
                    />
                  </div>
                </template>
              </ElSkeleton>
            </div>
          </div>
        </div>
      </div>
    </ElPopover>
    <span v-else>-</span>
  </div>
</template>

<style lang="scss" scoped>
.file-list-cell {
  display: inline-flex;
  align-items: center;
}

.file-trigger {
  padding: 0;
}

.file-popover-content {
  padding: 0;
  margin: -12px;
}

.popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background-color: hsl(var(--background) / 50%);
  border-bottom: 1px solid hsl(var(--border));
}

.popover-title {
  font-size: 14px;
  font-weight: 600;
  color: hsl(var(--foreground));
}

.popover-file-list {
  padding: 8px;
}

.popover-file-item {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px;
  margin-bottom: 4px;
  background-color: hsl(var(--background));
  border-radius: 6px;
  transition: all 0.3s;

  &:last-child {
    margin-bottom: 0;
  }

  &:hover {
    background-color: hsl(var(--primary) / 5%);
  }
}

.popover-file-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  color: hsl(var(--primary));
}

.popover-file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.popover-file-name {
  overflow: hidden;
  font-size: 14px;
  color: hsl(var(--foreground));
  text-overflow: ellipsis;
  white-space: nowrap;
}

.popover-file-size {
  font-size: 12px;
  color: hsl(var(--foreground) / 60%);
}
</style>
