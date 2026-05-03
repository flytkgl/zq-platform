<script setup lang="ts">
import type {
  ImageSelectorEmits,
  ImageSelectorFile,
  ImageSelectorProps,
} from './types';

import { computed, onBeforeUnmount, ref, watch } from 'vue';

import {
  Check,
  CloudUploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  FileImageOutlined,
  IconifyIcon,
} from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElDialog,
  ElImageViewer,
  ElMessage,
  ElProgress,
  ElScrollbar,
} from 'element-plus';

import {
  getFilesInfo,
  getRecentImages,
  uploadFile as uploadFileApi,
} from '#/api/core/file';
import { getFileUrl } from '#/composables/useFileUrl';

import { ImageCropper } from '../../image-cropper';

defineOptions({
  name: 'ImageSelector',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<Props>(), {
  multiple: false,
  placeholder: () => $t('ui.placeholder.select') || '请选择图片',
  disabled: false,
  clearable: true,
  showImageInfo: true,
  maxSize: 10, // 默认10MB
  maxWidth: 0, // 不限制
  maxHeight: 0,
  minWidth: 0,
  minHeight: 0,
  accept: () => ['image/*'],
  gridColumns: 4,
  sortable: false,
  enableCrop: false,
  cropAspectRatio: undefined,
  cropShape: 'rect',
  size: undefined, // 默认不限制，使用网格自适应
  width: undefined, // 触发器宽度，优先级高于 size
  height: undefined, // 触发器高度，优先级高于 size
  source: 'form',
});

const emit = defineEmits<ImageSelectorEmits>();

interface Props extends ImageSelectorProps {}

// 扩展的图片类型，包含上传状态
type UploadingImage = ImageSelectorFile & {
  failed?: boolean;
  originalFile?: File;
  progress?: number;
  uploading?: boolean;
};

// 状态
const modalVisible = ref(false);
const uploadedImages = ref<UploadingImage[]>([]);
const confirmedImages = ref<UploadingImage[]>([]);
const uploadInputRef = ref<HTMLInputElement>();
const isDragging = ref(false);
const previewVisible = ref(false);
const previewImageUrls = ref<string[]>([]);
const previewInitialIndex = ref(0);

// 选中的图片 ID 集合
const selectedImages = ref<Set<string>>(new Set());

// 最近上传的图片
const recentImages = ref<
  Array<{
    id: string;
    loading: boolean;
    name: string;
    size?: number;
    sys_create_datetime?: string;
    url: string;
  }>
>([]);
const recentLoading = ref(false);

// 裁剪相关状态
const cropperVisible = ref(false);
const cropperImageSrc = ref('');
const cropperImageData = ref<{ file: File }>();

// 监听 modelValue 变化，加载已有图片
watch(
  () => props.modelValue,
  async (newValue) => {
    if (!newValue) {
      confirmedImages.value = [];
      return;
    }

    const ids = Array.isArray(newValue) ? newValue : [newValue];
    if (ids.length === 0) {
      confirmedImages.value = [];
      return;
    }

    // 将 ID 转换为图片对象，先占位
    const images = ids.map((id) => ({
      id: String(id),
      name: '',
      path: '',
      url: '',
    }));
    confirmedImages.value = images;

    // 批量获取文件完整信息
    getFilesInfo(ids.map(String))
      .then((infos) => {
        for (const info of infos) {
          if (!info) continue;
          const idx = confirmedImages.value.findIndex(
            (item) => item.id === String(info.id),
          );
          if (idx !== -1 && confirmedImages.value[idx]) {
            confirmedImages.value[idx] = {
              ...confirmedImages.value[idx],
              name: info.name || confirmedImages.value[idx]!.name,
              size: info.file_size ?? info.size,
              mime_type: info.mime_type,
              sys_create_datetime: info.sys_create_datetime,
            } as (typeof confirmedImages.value)[number];
          }
        }
        confirmedImages.value = [...confirmedImages.value];
      })
      .catch(() => {});

    // 异步加载每个图片的URL
    for (const img of images) {
      const imgId = img.id;
      getFileUrl(imgId).then((url) => {
        const updatedImages = [...confirmedImages.value];
        const index = updatedImages.findIndex((item) => item.id === imgId);
        if (index !== -1 && updatedImages[index]) {
          updatedImages[index] = {
            ...updatedImages[index],
            url,
          } as (typeof updatedImages)[number];
          confirmedImages.value = updatedImages;
        }
      });
    }
  },
  { immediate: true },
);

// 计算属性：acceptString
const acceptString = computed(() => {
  if (props.accept && props.accept.length > 0) {
    return props.accept.join(',');
  }
  return 'image/*';
});

// 计算属性：已选图片列表
const selectedImagesList = computed(() => {
  if (modalVisible.value && uploadedImages.value.length > 0) {
    return uploadedImages.value.filter((img) =>
      selectedImages.value.has(img.id),
    );
  }

  if (confirmedImages.value.length > 0) {
    return confirmedImages.value;
  }

  return [];
});

// 计算属性：网格样式
const gridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${props.gridColumns}, 1fr)`,
}));

// 计算属性：触发器大小样式
const triggerSizeStyle = computed(() => {
  // 优先使用 width 和 height
  if (props.width || props.height) {
    return {
      width: props.width
        ? `${props.width}px`
        : (props.height
          ? `${props.height}px`
          : 'auto'),
      height: props.height
        ? `${props.height}px`
        : (props.width
          ? `${props.width}px`
          : 'auto'),
      paddingTop: 0,
      flexShrink: 0,
    };
  }
  // 其次使用 size（正方形）
  if (props.size > 0 && props.size > 0) {
    return {
      width: `${props.size}px`,
      height: `${props.size}px`,
      paddingTop: 0,
      flexShrink: 0,
    };
  }
  return {};
});

// 加载最近上传的图片
async function loadRecentImages() {
  recentImages.value = [];
  recentLoading.value = true;
  try {
    const items = await getRecentImages(20);
    recentImages.value = (items || []).map((item: any) => ({
      id: String(item.id),
      name: item.name || '',
      url: '',
      loading: true,
      size: item.file_size,
      sys_create_datetime: item.sys_create_datetime,
    }));
    // 异步加载每张图片的 URL
    for (const img of recentImages.value) {
      getFileUrl(img.id)
        .then((url) => {
          img.url = url;
          img.loading = false;
        })
        .catch(() => {
          img.loading = false;
        });
    }
  } catch (error) {
    console.error('Failed to load recent images:', error);
  } finally {
    recentLoading.value = false;
  }
}

// 选择最近上传的图片
function selectRecentImage(img: {
  id: string;
  name: string;
  size?: number;
  sys_create_datetime?: string;
  url: string;
}) {
  // 检查是否已在上传列表中
  const exists = uploadedImages.value.find((u) => u.id === img.id);
  if (exists) {
    toggleImageSelection(img.id);
    return;
  }

  // 单选模式：清空现有
  if (!props.multiple) {
    uploadedImages.value.forEach((u) => {
      if (u.previewUrl) URL.revokeObjectURL(u.previewUrl);
    });
    uploadedImages.value = [];
    selectedImages.value.clear();
  }

  // 添加到上传列表并自动选中
  uploadedImages.value.push({
    id: img.id,
    name: img.name,
    path: '',
    url: img.url,
    size: img.size,
    sys_create_datetime: img.sys_create_datetime,
    uploading: false,
    failed: false,
    progress: 100,
  });
  selectedImages.value.add(img.id);
}

// 打开对话框
function openModal() {
  if (props.disabled) return;

  // 从已确认的图片初始化
  uploadedImages.value = confirmedImages.value.map((img) => ({ ...img }));
  selectedImages.value = new Set(confirmedImages.value.map((img) => img.id));

  modalVisible.value = true;
  loadRecentImages();
}

// 关闭对话框
function closeModal() {
  modalVisible.value = false;
}

// 打开文件选择器
function openFileSelector() {
  uploadInputRef.value?.click();
}

// 处理文件输入变化
async function handleFileInputChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  if (files && files.length > 0) {
    await handleImagesUpload([...files]);
  }
  // 清空 input，允许重复选择同一文件
  target.value = '';
}

// 处理图片上传
async function handleImagesUpload(files: File[]) {
  // 单选模式：清空现有图片
  if (!props.multiple) {
    if (files.length > 1) {
      ElMessage.warning('单选模式下只能选择一张图片');
      files = files[0] ? [files[0]] : [];
    }
    // 清空现有图片和预览
    uploadedImages.value.forEach((img) => {
      if (img.previewUrl) {
        URL.revokeObjectURL(img.previewUrl);
      }
    });
    uploadedImages.value = [];
    selectedImages.value.clear();
  }

  // 验证并上传
  const validFiles = await validateImages(files);

  if (validFiles.length === 0) {
    return;
  }

  // 如果启用裁剪功能，逐个打开裁剪对话框
  if (props.enableCrop) {
    for (const file of validFiles) {
      await handleCropImage(file);
    }
  } else {
    // 并发上传
    await Promise.all(validFiles.map((file) => uploadSingleImage(file)));
  }
}

// 验证图片
async function validateImages(files: File[]): Promise<File[]> {
  const validFiles: File[] = [];

  for (const file of files) {
    // 检查文件类型
    if (!file.type.startsWith('image/')) {
      ElMessage.error(`${file.name} 不是有效的图片文件`);
      continue;
    }

    // 检查文件大小
    if (props.maxSize && file.size > props.maxSize * 1024 * 1024) {
      ElMessage.error(`${file.name} 超过最大文件大小 ${props.maxSize}MB`);
      continue;
    }

    // 检查图片尺寸
    try {
      const dimensions = await getImageDimensions(file);

      if (props.minWidth && dimensions.width < props.minWidth) {
        ElMessage.error(`${file.name} 宽度小于最小要求 ${props.minWidth}px`);
        continue;
      }

      if (props.minHeight && dimensions.height < props.minHeight) {
        ElMessage.error(`${file.name} 高度小于最小要求 ${props.minHeight}px`);
        continue;
      }

      if (props.maxWidth && dimensions.width > props.maxWidth) {
        ElMessage.error(`${file.name} 宽度超过最大限制 ${props.maxWidth}px`);
        continue;
      }

      if (props.maxHeight && dimensions.height > props.maxHeight) {
        ElMessage.error(`${file.name} 高度超过最大限制 ${props.maxHeight}px`);
        continue;
      }

      validFiles.push(file);
    } catch {
      ElMessage.error(`无法读取 ${file.name} 的图片信息`);
    }
  }

  return validFiles;
}

// 获取图片尺寸
function getImageDimensions(
  file: File,
): Promise<{ height: number; width: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);

    img.addEventListener('load', () => {
      URL.revokeObjectURL(url);
      resolve({ width: img.width, height: img.height });
    });

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load image'));
    };

    img.src = url;
  });
}

// 上传单个图片
async function uploadSingleImage(file: File) {
  const uploadItem: UploadingImage = {
    id: `temp_${Date.now()}_${Math.random()}`,
    name: file.name,
    path: '',
    uploading: true,
    progress: 0,
    failed: false,
    originalFile: file,
    sys_create_datetime: new Date().toISOString(),
  };

  // 生成本地预览
  uploadItem.previewUrl = URL.createObjectURL(file);

  // 获取图片尺寸
  try {
    const dimensions = await getImageDimensions(file);
    uploadItem.width = dimensions.width;
    uploadItem.height = dimensions.height;
  } catch {
    // 忽略错误
  }

  uploadedImages.value.push(uploadItem);

  try {
    // 使用真实的上传进度
    const response = await uploadFileApi(file, {
      source: props.source,
      onProgress: (progressEvent) => {
        const item = uploadedImages.value.find(
          (img) => img.id === uploadItem.id,
        );
        if (item) {
          item.progress = progressEvent.percentage;
        }
      },
    });

    if (response && response.id) {
      // 通过数组查找来更新，确保响应式更新
      const item = uploadedImages.value.find((img) => img.id === uploadItem.id);
      if (item) {
        item.id = String(response.id);
        item.path = response.path || '';
        // 使用 getFileUrl 生成正确的 API 访问 URL
        getFileUrl(String(response.id)).then((url) => {
          item.url = url;
        });
        item.size = response.file_size ?? response.size;
        item.mime_type = response.mime_type;
        item.sys_create_datetime =
          response.sys_create_datetime || item.sys_create_datetime;
        item.uploading = false;
        item.progress = 100;

        // 自动选中上传成功的图片
        selectedImages.value.add(item.id);
      }

      ElMessage.success(`${file.name} 上传成功`);
    } else {
      throw new Error('Upload failed');
    }
  } catch (error) {
    console.error('Upload error:', error);
    const item = uploadedImages.value.find((img) => img.id === uploadItem.id);
    if (item) {
      item.uploading = false;
      item.failed = true;
      item.progress = 0;
    }
    ElMessage.error(`${file.name} 上传失败`);
  }
}

// 打开裁剪对话框
async function handleCropImage(file: File): Promise<void> {
  return new Promise((resolve) => {
    // 创建预览 URL
    cropperImageSrc.value = URL.createObjectURL(file);
    cropperImageData.value = { file };
    cropperVisible.value = true;

    // 等待裁剪完成或取消
    const unwatch = watch(cropperVisible, (newVal) => {
      if (!newVal) {
        // 清理预览 URL
        if (cropperImageSrc.value) {
          URL.revokeObjectURL(cropperImageSrc.value);
          cropperImageSrc.value = '';
        }
        cropperImageData.value = undefined;
        unwatch();
        resolve();
      }
    });
  });
}

// 处理裁剪确认
async function handleCropConfirm(result: {
  blob: Blob;
  canvas: HTMLCanvasElement;
}) {
  if (!cropperImageData.value) {
    return;
  }

  const { file } = cropperImageData.value;

  // 创建裁剪后的文件
  const croppedFile = new File([result.blob], file.name, { type: file.type });

  // 上传裁剪后的图片
  await uploadSingleImage(croppedFile);

  // 关闭裁剪对话框
  cropperVisible.value = false;
}

// 重试上传
async function handleRetryUpload(image: UploadingImage) {
  if (!image.originalFile) {
    ElMessage.error('无法重新上传：原始文件已丢失');
    return;
  }

  // 重置状态
  image.uploading = true;
  image.failed = false;
  image.progress = 0;

  try {
    // 使用真实的上传进度
    const response = await uploadFileApi(image.originalFile, {
      source: props.source,
      onProgress: (progressEvent) => {
        const item = uploadedImages.value.find((img) => img.id === image.id);
        if (item) {
          item.progress = progressEvent.percentage;
        }
      },
    });

    if (response && response.id) {
      image.id = String(response.id);
      image.path = response.path || '';
      // 使用 getFileUrl 生成正确的 API 访问 URL
      getFileUrl(String(response.id)).then((url) => {
        image.url = url;
      });
      image.size = response.size;
      image.mime_type = response.mime_type;
      image.uploading = false;
      image.failed = false;
      image.progress = 100;

      // 自动选中重新上传成功的图片
      selectedImages.value.add(image.id);

      ElMessage.success(`${image.name} 重新上传成功`);
    } else {
      throw new Error('Upload failed');
    }
  } catch (error) {
    console.error('Retry upload error:', error);
    image.uploading = false;
    image.failed = true;
    image.progress = 0;
    ElMessage.error(`${image.name} 重新上传失败`);
  }
}

// 删除图片
function handleDeleteImage(imageId: string) {
  const index = uploadedImages.value.findIndex((img) => img.id === imageId);
  if (index !== -1) {
    const image = uploadedImages.value[index];
    if (image && image.previewUrl) {
      URL.revokeObjectURL(image.previewUrl);
    }
    uploadedImages.value.splice(index, 1);
    selectedImages.value.delete(imageId);
  }
}

// 切换图片选中状态
function toggleImageSelection(imageId: string) {
  if (props.multiple) {
    // 多选模式：切换选中状态
    if (selectedImages.value.has(imageId)) {
      selectedImages.value.delete(imageId);
    } else {
      selectedImages.value.add(imageId);
    }
  } else {
    // 单选模式：清空其他选择
    selectedImages.value.clear();
    selectedImages.value.add(imageId);
  }
}

// 预览图片
function handlePreviewImage(image: UploadingImage) {
  // 如果对话框打开，使用 uploadedImages；否则使用 confirmedImages
  const imageSource = modalVisible.value
    ? uploadedImages.value
    : confirmedImages.value;

  // 获取所有已上传完成的图片URL（优先使用服务器URL）
  const imageList = imageSource
    .filter((img) => !img.uploading && !img.failed)
    .map((img) => img.url || img.previewUrl || '');

  // 找到当前图片的索引
  const currentIndex = imageSource
    .filter((img) => !img.uploading && !img.failed)
    .findIndex((img) => img.id === image.id);

  previewImageUrls.value = imageList;
  previewInitialIndex.value = Math.max(currentIndex, 0);
  previewVisible.value = true;
}

// 关闭预览
function handleClosePreview() {
  previewVisible.value = false;
}

// 确认选择
function handleConfirm() {
  const selected = uploadedImages.value.filter(
    (img) => selectedImages.value.has(img.id) && !img.uploading && !img.failed,
  );

  if (selected.length === 0) {
    ElMessage.warning('请至少选择一张图片');
    return;
  }

  // 更新已确认的图片（不保留 previewUrl，避免 blob URL 失效）
  confirmedImages.value = selected.map((img) => {
    const { previewUrl, ...rest } = img;
    // 确保使用正确的 API URL
    if (!rest.url) {
      getFileUrl(rest.id).then((url) => {
        rest.url = url;
      });
    }
    return rest;
  });

  // 更新 v-model
  if (props.multiple) {
    const ids = selected.map((img) => img.id);
    selectedImages.value = new Set(ids);
    emit('update:modelValue', ids);
    emit('change', ids);
  } else {
    const id = selected[0]?.id;
    selectedImages.value = new Set(id ? [id] : []);
    emit('update:modelValue', id);
    emit('change', id);
  }

  closeModal();
}

// 清空选择
function handleClear() {
  selectedImages.value.clear();
  confirmedImages.value = [];
  uploadedImages.value = [];
  emit('update:modelValue', props.multiple ? [] : null);
  emit('change', props.multiple ? [] : null);
}

// 从触发器中移除图片
function handleRemoveFromTrigger(imageId: string) {
  const index = confirmedImages.value.findIndex((img) => img.id === imageId);
  if (index !== -1) {
    const image = confirmedImages.value[index];
    if (image && image.previewUrl) {
      URL.revokeObjectURL(image.previewUrl);
    }
    confirmedImages.value.splice(index, 1);
  }

  selectedImages.value.delete(imageId);

  if (props.multiple) {
    const ids = confirmedImages.value.map((img) => img.id);
    emit('update:modelValue', ids);
    emit('change', ids);
  } else {
    emit('update:modelValue', null);
    emit('change', null);
  }
}

// 拖拽事件处理
function handleDragEnter(e: DragEvent) {
  e.preventDefault();
  e.stopPropagation();
  isDragging.value = true;
}

function handleDragOver(e: DragEvent) {
  e.preventDefault();
  e.stopPropagation();
}

function handleDragLeave(e: DragEvent) {
  e.preventDefault();
  e.stopPropagation();
  // 只有当离开整个对话框区域时才设置为 false
  if (e.target === e.currentTarget) {
    isDragging.value = false;
  }
}

async function handleDrop(e: DragEvent) {
  e.preventDefault();
  e.stopPropagation();
  isDragging.value = false;

  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    await handleImagesUpload([...files]);
  }
}

// 格式化文件大小
function formatFileSize(bytes?: number): string {
  if (!bytes) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

// 格式化图片尺寸
function formatImageDimensions(image: UploadingImage): string {
  if (image.width && image.height) {
    return `${image.width} × ${image.height}`;
  }
  return '-';
}

// 格式化日期时间
function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  } catch {
    return '-';
  }
}

// 清理预览 URL
function cleanupPreviewUrls() {
  uploadedImages.value.forEach((img) => {
    if (img.previewUrl) {
      URL.revokeObjectURL(img.previewUrl);
    }
  });
}

// 监听对话框关闭
watch(modalVisible, (newVal) => {
  if (!newVal) {
    cleanupPreviewUrls();
  }
});

// 组件卸载时清理
onBeforeUnmount(() => {
  cleanupPreviewUrls();
  confirmedImages.value.forEach((img) => {
    if (img.previewUrl) {
      URL.revokeObjectURL(img.previewUrl);
    }
  });
});

// 暴露方法
defineExpose({
  openModal,
});
</script>

<template>
  <div class="image-selector">
    <!-- 触发器 - 网格显示 -->
    <div
      class="image-selector-trigger-grid"
      :class="{
        disabled,
        multiple,
        'has-size': size,
      }"
    >
      <!-- 已选图片显示 -->
      <template v-if="selectedImagesList.length === 0">
        <!-- 空状态 - 点击上传 -->
        <div
          class="image-grid-item upload-placeholder"
          :class="{ 'is-circle': cropShape === 'circle' }"
          :style="triggerSizeStyle"
          @click="!disabled && openModal()"
        >
          <FileImageOutlined class="placeholder-icon" />
          <span class="placeholder-text">{{ placeholder }}</span>
        </div>
      </template>

      <template v-else>
        <!-- 单选模式：只显示一张图片 -->
        <template v-if="!multiple && selectedImagesList[0]">
          <div
            class="image-grid-item image-preview"
            :class="{ 'is-circle': cropShape === 'circle' }"
            :style="triggerSizeStyle"
            @click.stop="handlePreviewImage(selectedImagesList[0] as UploadingImage)"
          >
            <img
              v-if="
                selectedImagesList[0].url || selectedImagesList[0].previewUrl
              "
              :src="
                selectedImagesList[0].url || selectedImagesList[0].previewUrl
              "
              :alt="selectedImagesList[0].name"
              class="preview-image"
              :class="{ 'is-circle': cropShape === 'circle' }"
            />
            <div
              v-if="clearable && !disabled"
              class="image-remove-btn"
              @click.stop="handleRemoveFromTrigger(selectedImagesList[0].id)"
            >
              <DeleteOutlined />
            </div>
          </div>
        </template>

        <!-- 多选模式：显示所有图片 + 上传按钮 -->
        <template v-else>
          <div
            v-for="image in selectedImagesList"
            :key="image.id"
            class="image-grid-item image-preview"
            :class="{ 'is-circle': cropShape === 'circle' }"
            :style="triggerSizeStyle"
            @click.stop="handlePreviewImage(image as UploadingImage)"
          >
            <img
              v-if="image.url || image.previewUrl"
              :src="image.url || image.previewUrl"
              :alt="image.name"
              class="preview-image"
              :class="{ 'is-circle': cropShape === 'circle' }"
            />
            <div
              v-if="!disabled"
              class="image-remove-btn"
              @click.stop="handleRemoveFromTrigger(image.id)"
            >
              <DeleteOutlined />
            </div>
          </div>

          <!-- 继续上传按钮 -->
          <div
            class="image-grid-item upload-placeholder"
            :style="triggerSizeStyle"
            @click="!disabled && openModal()"
          >
            <CloudUploadOutlined class="placeholder-icon" />
            <span class="placeholder-text">继续上传</span>
          </div>
        </template>
      </template>
    </div>

    <!-- Modal -->
    <ElDialog
      v-model="modalVisible"
      :title="multiple ? '选择图片' : '选择图片'"
      width="70%"
      class="image-selector-dialog"
      align-center
      append-to-body
    >
      <div class="image-selector-layout">
        <!-- 左侧：最近上传的图片 -->
        <div class="recent-images-panel border">
          <div class="recent-images-header">
            <span class="recent-images-title">最近上传</span>
          </div>
          <ElScrollbar class="recent-images-scroll">
            <div v-if="recentLoading" class="recent-images-grid">
              <div v-for="i in 8" :key="i" class="recent-image-item">
                <div
                  class="bg-muted animate-pulse rounded"
                  style="width: 100%; aspect-ratio: 1 / 1"
                ></div>
              </div>
            </div>
            <div
              v-else-if="recentImages.length === 0"
              class="recent-images-empty"
            >
              <FileImageOutlined class="recent-empty-icon" />
              <span class="recent-empty-text">暂无图片</span>
            </div>
            <div v-else class="recent-images-grid">
              <div
                v-for="img in recentImages"
                :key="img.id"
                class="recent-image-item"
                :class="{ selected: selectedImages.has(img.id) }"
                @click="!img.loading && selectRecentImage(img)"
              >
                <div
                  v-if="img.loading || !img.url"
                  class="bg-muted animate-pulse rounded"
                  style="width: 100%; aspect-ratio: 1 / 1"
                ></div>
                <img
                  v-else
                  :src="img.url"
                  :alt="img.name"
                  class="recent-image-img"
                />
                <div
                  v-if="selectedImages.has(img.id)"
                  class="recent-image-check"
                >
                  <Check class="size-3" />
                </div>
              </div>
            </div>
          </ElScrollbar>
        </div>

        <!-- 右侧：上传区域 -->
        <div
          class="image-selector-modal"
          :class="{ 'is-dragging': isDragging }"
          @dragenter="handleDragEnter"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @drop="handleDrop"
        >
          <!-- 隐藏的文件输入框 -->
          <input
            ref="uploadInputRef"
            type="file"
            :accept="acceptString"
            :multiple="multiple"
            style="display: none"
            @change="handleFileInputChange"
          />

          <!-- 拖拽提示遮罩 -->
          <div v-if="isDragging" class="drag-overlay">
            <div class="upload-area">
              <CloudUploadOutlined class="upload-area-icon" />
              <div class="upload-area-title">松开鼠标上传图片</div>
              <div class="upload-area-hint">
                <span v-if="accept && accept.length > 0">
                  支持格式：{{ accept.join(', ') }}
                </span>
                <span v-if="maxSize"> · 单张图片最大 {{ maxSize }}MB </span>
              </div>
            </div>
          </div>

          <!-- 上传区域（没有图片时显示） -->
          <div
            v-if="uploadedImages.length === 0 && !isDragging"
            class="upload-area-wrapper"
          >
            <div class="upload-area" @click="openFileSelector">
              <CloudUploadOutlined class="upload-area-icon" />
              <div class="upload-area-title">点击或拖拽图片到此处上传</div>
              <div class="upload-area-hint">
                <span v-if="accept && accept.length > 0">
                  支持格式：{{ accept.join(', ') }}
                </span>
                <span v-if="maxSize"> · 单张图片最大 {{ maxSize }}MB </span>
                <span v-if="minWidth || minHeight || maxWidth || maxHeight">
                  ·
                  <template v-if="minWidth && minHeight">
                    最小尺寸 {{ minWidth }}×{{ minHeight }}px
                  </template>
                  <template v-if="maxWidth && maxHeight">
                    · 最大尺寸 {{ maxWidth }}×{{ maxHeight }}px
                  </template>
                </span>
              </div>
            </div>
          </div>

          <!-- 图片网格（有图片时显示） -->
          <div
            v-if="uploadedImages.length > 0"
            class="image-selector-content ml-3 h-full rounded-[8px] border"
          >
            <!-- 顶部工具栏 -->
            <div class="toolbar mt-3">
              <div class="toolbar-info">
                <span class="info-text">
                  已上传
                  {{
                    uploadedImages.filter(
                      (img) => !img.uploading && !img.failed,
                    ).length
                  }}
                  张
                  <template v-if="!multiple">（单选）</template>
                  <template v-else-if="selectedImages.size > 0">
                    · 已选 {{ selectedImages.size }} 张
                  </template>
                </span>
              </div>
              <div class="toolbar-actions">
                <ElButton type="primary" @click="openFileSelector">
                  <CloudUploadOutlined class="icon-wrapper" />
                  {{ multiple ? '继续上传' : '替换图片' }}
                </ElButton>
              </div>
            </div>

            <!-- 图片网格 -->
            <ElScrollbar class="image-grid-scrollbar flex-1 min-h-0">
              <div class="image-grid" :style="gridStyle">
                <div
                  v-for="image in uploadedImages"
                  :key="image.id"
                  class="image-card"
                  :class="{
                    selected: selectedImages.has(image.id),
                    uploading: image.uploading,
                    failed: image.failed,
                  }"
                >
                  <!-- 选中标记 -->
                  <div
                    v-if="!image.uploading && !image.failed"
                    class="image-card-checkbox"
                    @click="toggleImageSelection(image.id)"
                  >
                    <div class="checkbox-inner">
                      <Check
                        v-if="selectedImages.has(image.id)"
                        class="size-3.5"
                      />
                    </div>
                  </div>

                  <!-- 图片预览 -->
                  <div class="image-card-preview">
                    <img
                      v-if="image.previewUrl || image.url"
                      :src="image.previewUrl || image.url"
                      :alt="image.name"
                      class="image-card-img"
                      @click="
                        !image.uploading &&
                        !image.failed &&
                        handlePreviewImage(image)
                      "
                    />

                    <!-- 上传中遮罩 -->
                    <div v-if="image.uploading" class="image-card-mask">
                      <ElProgress
                        type="circle"
                        :percentage="image.progress || 0"
                        :width="80"
                        :stroke-width="6"
                        color="#67c23a"
                      />
                    </div>

                    <!-- 失败遮罩 -->
                    <div v-if="image.failed" class="image-card-mask failed">
                      <div class="failed-content">
                        <IconifyIcon
                          icon="i-carbon:warning"
                          class="failed-icon"
                        />
                        <div class="failed-text">上传失败</div>
                        <ElButton
                          size="small"
                          type="primary"
                          @click="handleRetryUpload(image)"
                        >
                          重试
                        </ElButton>
                      </div>
                    </div>

                    <!-- 操作按钮 -->
                    <div v-if="!image.uploading" class="image-card-actions">
                      <ElButton
                        circle
                        size="small"
                        @click.stop="handlePreviewImage(image)"
                      >
                        <EyeOutlined />
                      </ElButton>
                      <ElButton
                        circle
                        size="small"
                        type="danger"
                        @click.stop="handleDeleteImage(image.id)"
                      >
                        <DeleteOutlined />
                      </ElButton>
                    </div>
                  </div>

                  <!-- 图片信息 -->
                  <div v-if="showImageInfo" class="image-card-info">
                    <div class="image-card-name" :title="image.name">
                      {{ image.name }}
                    </div>
                    <div class="image-card-meta">
                      <span>{{ formatFileSize(image.size) }}</span>
                      <span>{{
                        formatDateTime(image.sys_create_datetime)
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </ElScrollbar>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <ElButton @click="closeModal">取消</ElButton>
          <ElButton
            type="primary"
            :disabled="
              selectedImages.size === 0 ||
              uploadedImages.some((img) => img.uploading || img.failed)
            "
            @click="handleConfirm"
          >
            确定
            <template v-if="selectedImages.size > 0">
              ({{ selectedImages.size }})
            </template>
          </ElButton>
        </div>
      </template>
    </ElDialog>

    <!-- 图片预览 - 使用 Element Plus 的 ImageViewer -->
    <Teleport to="body">
      <ElImageViewer
        v-if="previewVisible"
        :url-list="previewImageUrls"
        :initial-index="previewInitialIndex"
        :z-index="3000"
        :hide-on-click-modal="true"
        @close="handleClosePreview"
      />
    </Teleport>

    <!-- 图片裁剪对话框 -->
    <ImageCropper
      v-model="cropperVisible"
      :image-src="cropperImageSrc"
      :aspect-ratio="cropAspectRatio"
      :shape="cropShape"
      @confirm="handleCropConfirm"
    />
  </div>
</template>

<style lang="scss" scoped>
.image-selector {
  width: 100%;
}

// 触发器 - 网格布局
.image-selector-trigger-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;

  &.disabled {
    pointer-events: none;
    opacity: 0.6;
  }

  // 当设置了 size 时，使用 flex 布局
  &.has-size {
    display: flex;
    flex-wrap: wrap;
    grid-template-columns: none;
  }
}

// 网格项 - 正方形
.image-grid-item {
  position: relative;
  width: 100%;
  min-width: 100px; // 最小宽度，防止在画布中显示为横线
  min-height: 100px; // 最小高度，防止在画布中显示为横线
  aspect-ratio: 1 / 1; // 1:1 正方形，使用 aspect-ratio 替代 padding-top
  overflow: hidden;
  border: 2px dashed hsl(var(--border));
  border-radius: 8px;
  transition: all 0.3s;

  &.upload-placeholder {
    cursor: pointer;
    background-color: hsl(var(--background));
    border-style: dashed;

    &:hover {
      background-color: hsl(var(--primary) / 5%);
      border-color: hsl(var(--primary));
    }

    &.is-circle {
      border-radius: 50%;
    }

    .placeholder-icon,
    .placeholder-text {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    }

    .placeholder-icon {
      margin-top: -20px;
      font-size: 36px;
      color: hsl(var(--primary));
    }

    .placeholder-text {
      margin-top: 20px;
      font-size: 14px;
      color: hsl(var(--muted-foreground));
      white-space: nowrap;
    }
  }

  &.image-preview {
    cursor: pointer;
    border-color: hsl(var(--border));
    border-style: solid;

    &:hover {
      border-color: hsl(var(--primary));

      .image-remove-btn {
        opacity: 1;
      }
    }
  }
}

// 预览图片
.preview-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;

  &.is-circle {
    border-radius: 50%;
  }
}

// 圆形容器
.image-preview.is-circle {
  border-radius: 50%;

  .image-remove-btn {
    top: 50%;
    right: auto;
    left: 50%;
    width: 24px;
    height: 24px;
    font-size: 12px;
    border-radius: 50%;
    opacity: 0;
    transform: translate(-50%, -50%);
    z-index: 10;
  }

  &:hover .image-remove-btn {
    opacity: 1;
  }

  .image-remove-btn:hover {
    transform: translate(-50%, -50%) scale(1.1);
  }
}

// 右上角删除按钮
.image-remove-btn {
  position: absolute;
  top: 1px;
  right: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 12px;
  height: 12px;
  font-size: 8px;
  color: #fff;
  cursor: pointer;
  background-color: var(--el-color-danger);
  border-radius: 50%;
  opacity: 0;
  transition: all 0.2s;

  &:hover {
    background-color: var(--el-color-danger-dark-2);
    transform: scale(1.1);
  }
}

// 对话框样式
.image-selector-dialog {
  :deep(.el-dialog__body) {
    padding: 0;
  }
}

// 左右布局
.image-selector-layout {
  display: flex;
  min-height: 600px;
  max-height: 600px;
}

// 左侧最近上传面板
.recent-images-panel {
  display: flex;
  flex-direction: column;
  width: 250px;
  flex-shrink: 0;
  // background-color: hsl(var(--background-deep));
  border-radius: 8px;
}

.recent-images-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid hsl(var(--border));
}

.recent-images-title {
  font-size: 14px;
  font-weight: 600;
  color: hsl(var(--foreground));
}

.recent-images-scroll {
  flex: 1;
  min-height: 0;
}

.recent-images-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  padding: 12px;
}

.recent-image-item {
  position: relative;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  border-radius: 6px;
  transition: all 0.2s;

  &:hover {
    border-color: hsl(var(--primary) / 50%);
  }

  &.selected {
    border-color: hsl(var(--primary));
  }
}

.recent-image-img {
  display: block;
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 4px;
}

.recent-image-check {
  position: absolute;
  top: 4px;
  right: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  font-size: 12px;
  color: white;
  background-color: hsl(var(--primary));
  border-radius: 4px;
}

.recent-images-empty {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: hsl(var(--muted-foreground));

  .recent-empty-icon {
    font-size: 36px;
  }

  .recent-empty-text {
    font-size: 13px;
  }
}

.image-selector-modal {
  position: relative;
  flex: 1;
  min-height: 400px;
  overflow: hidden;
  background-color: hsl(var(--background));
}

.is-dragging {
  .drag-overlay {
    pointer-events: auto;
    opacity: 1;
  }
}

.drag-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 100;
  width: 95%;
  pointer-events: none;
  opacity: 0;
  transform: translate(-50%, -50%);
  transition: opacity 0.2s;

  .upload-area {
    cursor: default;
    background-color: hsl(var(--background) / 98%);
    border-color: hsl(var(--primary));
    box-shadow: 0 4px 20px rgb(0 0 0 / 15%);

    .upload-area-icon {
      color: hsl(var(--primary));
      transform: scale(1.1);
    }

    .upload-area-title {
      color: hsl(var(--primary));
    }

    .upload-area-hint {
      color: hsl(var(--foreground) / 70%);
    }
  }
}

.upload-area-wrapper {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 95%;
  transform: translate(-50%, -50%);
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 210px 40px;
  cursor: pointer;
  background-color: hsl(var(--background) / 50%);
  border: 2px dashed hsl(var(--border));
  border-radius: 12px;
  transition: all 0.3s;

  &:hover {
    background-color: hsl(var(--primary) / 5%);
    border-color: hsl(var(--primary));

    .upload-area-icon {
      transform: scale(1.1);
    }
  }

  .upload-area-icon {
    margin-bottom: 24px;
    font-size: 72px;
    color: hsl(var(--foreground) / 40%);
    transition: all 0.3s;
  }

  .upload-area-title {
    margin-bottom: 12px;
    font-size: 18px;
    font-weight: 600;
    color: hsl(var(--foreground));
  }

  .upload-area-hint {
    font-size: 14px;
    color: hsl(var(--foreground) / 60%);
    text-align: center;

    span {
      margin: 0 4px;
    }
  }
}

.image-selector-content {
  display: flex;
  flex-direction: column;
  padding: 0 20px;
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  // margin-bottom: 12px;

  .toolbar-info {
    .info-text {
      font-size: 14px;
      color: hsl(var(--foreground) / 80%);
    }
  }

  .toolbar-actions {
    .icon-wrapper {
      margin-right: 4px;
      font-size: 18px;
    }
  }
}

.image-grid-scrollbar {
  :deep(.el-scrollbar__view) {
    padding: 4px;
  }
}

.image-grid {
  display: grid;
  gap: 16px;
}

.image-card {
  position: relative;
  overflow: hidden;
  cursor: pointer;
  background-color: hsl(var(--background));
  border: 2px solid transparent;
  border-radius: 8px;
  transition: all 0.3s;

  &:hover:not(.uploading):not(.failed) {
    box-shadow: 0 4px 12px rgb(0 0 0 / 10%);

    .image-card-actions {
      opacity: 1;
    }
  }

  &.selected {
    border-color: hsl(var(--primary));

    .image-card-checkbox .checkbox-inner {
      background-color: hsl(var(--primary));
      border-color: hsl(var(--primary));
    }
  }

  &.uploading {
    pointer-events: none;
  }

  &.failed {
    border-color: hsl(var(--destructive) / 30%);
  }
}

.image-card-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  cursor: pointer;

  .checkbox-inner {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    font-size: 14px;
    color: white;
    background-color: rgb(0 0 0 / 30%);
    border: 2px solid white;
    border-radius: 4px;
    transition: all 0.3s;

    &:hover {
      background-color: hsl(var(--primary) / 80%);
      border-color: hsl(var(--primary));
    }
  }
}

.image-card-preview {
  position: relative;
  width: 100%;
  padding-top: 75%; // 4:3 aspect ratio，更合理的缩略图比例
  overflow: hidden;
  background-color: hsl(var(--background) / 50%);
}

.image-card-img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  object-fit: cover;
}

.image-card-mask {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgb(0 0 0 / 75%);

  // 上传进度样式优化
  :deep(.el-progress) {
    .el-progress__text {
      font-size: 14px !important;
      font-weight: 600;
      color: white !important;
    }

    .el-progress-circle__track {
      stroke: rgb(255 255 255 / 20%);
    }
  }

  &.failed {
    background-color: rgb(0 0 0 / 85%);
  }
}

.failed-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  color: white;

  .failed-icon {
    font-size: 32px;
    color: hsl(var(--destructive));
  }

  .failed-text {
    font-size: 14px;
  }
}

.image-card-actions {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 5;
  display: flex;
  gap: 8px;
  opacity: 0;
  transform: translate(-50%, -50%);
  transition: opacity 0.3s;
}

.image-card-info {
  padding: 8px 12px;
  background-color: hsl(var(--background));
}

.image-card-name {
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
  color: hsl(var(--foreground));
  white-space: nowrap;
}

.image-card-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: hsl(var(--foreground) / 60%);

  span {
    &:first-child {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
