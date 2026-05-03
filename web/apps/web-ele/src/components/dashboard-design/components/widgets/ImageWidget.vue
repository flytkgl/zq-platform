<script setup lang="ts">
import type { DashboardWidget } from '../../store/dashboardDesignStore';

import { computed, ref, watch } from 'vue';

import { ElImage } from 'element-plus';

import { getFileUrl } from '#/composables/useFileUrl';

const props = defineProps<{
  isDesignMode?: boolean;
  widget: DashboardWidget;
}>();

const widgetProps = computed(() => props.widget.props);

// 主图URL（响应式）
const imageSrc = ref('');

// 预览图片列表（响应式）
const previewList = ref<string[]>([]);

// 异步解析图片URL
async function resolveImageUrl(url: string): Promise<string> {
  if (!url) return '';
  if (url.startsWith('file://')) {
    const fileId = url.slice(7);
    return await getFileUrl(fileId);
  }
  return url;
}

// 加载图片URL
async function loadImageUrls() {
  // 加载主图
  imageSrc.value = await resolveImageUrl(widgetProps.value.src || '');

  // 加载预览列表
  const list = widgetProps.value.previewSrcList || [];
  previewList.value =
    list.length === 0 && imageSrc.value
      ? [imageSrc.value]
      : await Promise.all(list.map((url: string) => resolveImageUrl(url)));
}

// 监听图片源变化
watch(
  () => [widgetProps.value.src, widgetProps.value.previewSrcList],
  () => {
    loadImageUrls();
  },
  { immediate: true, deep: true },
);
</script>

<template>
  <div class="image-widget flex h-full w-full flex-col">
    <!-- 标题 -->
    <div
      v-if="widgetProps.title"
      class="mb-2 flex-shrink-0 text-sm font-medium"
      style="color: var(--el-text-color-primary)"
    >
      {{ widgetProps.title }}
    </div>

    <!-- 图片容器 -->
    <div class="relative min-h-0 flex-1 overflow-hidden rounded">
      <ElImage
        :src="imageSrc"
        :alt="widgetProps.alt || '图片'"
        :fit="widgetProps.fit || 'cover'"
        :lazy="widgetProps.lazy !== false"
        :preview-src-list="isDesignMode ? [] : previewList"
        :z-index="widgetProps.zIndex || 2000"
        :hide-on-click-modal="widgetProps.hideOnClickModal || false"
        class="h-full w-full"
        :preview-teleported="true"
      >
        <template #error>
          <div
            class="flex h-full w-full items-center justify-center"
            style="background-color: var(--el-fill-color-light)"
          >
            <span style="color: var(--el-text-color-secondary)">
              加载失败
            </span>
          </div>
        </template>
        <template #placeholder>
          <div
            class="flex h-full w-full items-center justify-center"
            style="background-color: var(--el-fill-color-lighter)"
          >
            <span style="color: var(--el-text-color-placeholder)">
              加载中...
            </span>
          </div>
        </template>
      </ElImage>
    </div>
  </div>
</template>

<style scoped>
.image-widget :deep(.el-image) {
  display: block;
}

.image-widget :deep(.el-image__inner) {
  transition: transform 0.3s ease;
}

.image-widget:hover :deep(.el-image__inner) {
  transform: scale(1.02);
}
</style>
