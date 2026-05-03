<script setup lang="ts">
import type { AiOcrConfig } from '#/components/form-design/store/formDesignStore';

import { computed, ref, watch } from 'vue';

import {
  DeleteOutlined,
  EyeOutlined,
  FileImageOutlined,
  FileOutlined,
  Sparkles,
} from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElDialog,
  ElImageViewer,
  ElMessage,
  ElProgress,
  ElTag,
} from 'element-plus';

import { uploadFile as uploadFileApi } from '#/api/core/file';
import { requestClient } from '#/api/request';
import { getFileUrl } from '#/composables/useFileUrl';

defineOptions({
  name: 'AiImageOcr',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<Props>(), {
  multiple: false,
  placeholder: () => $t('form-design.aiImageOcr.uploadPlaceholder'),
  disabled: false,
  clearable: true,
  maxSize: 10,
});

const emit = defineEmits<Emits>();

interface Props {
  modelValue?: string | string[];
  multiple?: boolean;
  placeholder?: string;
  disabled?: boolean;
  clearable?: boolean;
  maxSize?: number;
  height?: number;
  aiOcrConfig?: AiOcrConfig;
  formData?: Record<string, any>;
}

interface Emits {
  (e: 'update:modelValue', value: string | string[] | undefined): void;
  (e: 'change', value: string | string[] | undefined): void;
  (
    e: 'ocr-success',
    data: { extractedData: null | Record<string, any>; rawText: string },
  ): void;
  (e: 'fill-fields', data: Record<string, any>): void;
}

// 状态
const uploadInputRef = ref<HTMLInputElement>();
const isUploading = ref(false);
const isRecognizing = ref(false);
const uploadProgress = ref(0);
const currentImageId = ref<string>('');
const currentImageUrl = ref<string>('');
const currentFileMimeType = ref<string>('');
const previewVisible = ref(false);
const ocrResult = ref<null | {
  extractedData: null | Record<string, any>;
  rawText: string;
}>(null);

// 文件类型到accept属性的映射
const FILE_TYPE_ACCEPT_MAP: Record<string, string[]> = {
  image: ['image/*'],
  text: [
    '.txt',
    '.md',
    '.log',
    '.py',
    '.js',
    '.ts',
    '.jsx',
    '.tsx',
    '.vue',
    '.html',
    '.css',
    '.json',
    '.yaml',
    '.yml',
    '.xml',
    '.csv',
  ],
  pdf: ['.pdf', 'application/pdf'],
  word: [
    '.doc',
    '.docx',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ],
  excel: [
    '.xls',
    '.xlsx',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ],
};

// 计算属性
const hasFile = computed(() => !!currentImageId.value);

// 计算接受的文件类型
const acceptString = computed(() => {
  const types = props.aiOcrConfig?.acceptFileTypes || ['image'];
  if (types.includes('all')) {
    return '*/*';
  }
  const accepts: string[] = [];
  types.forEach((type) => {
    if (FILE_TYPE_ACCEPT_MAP[type]) {
      accepts.push(...FILE_TYPE_ACCEPT_MAP[type]);
    }
  });
  return accepts.join(',') || 'image/*';
});

// 判断是否为图片文件
const isImageFile = computed(() => {
  if (!currentImageId.value) return false;
  const url = currentImageUrl.value.toLowerCase();
  const mimeType = currentFileMimeType.value.toLowerCase();
  return (
    mimeType.startsWith('image/') ||
    url.includes('image/') ||
    /\.(jpg|jpeg|png|gif|bmp|webp|svg)$/i.test(url)
  );
});

// 判断是否为PDF文件
const isPdfFile = computed(() => {
  if (!currentImageId.value) return false;
  const url = currentImageUrl.value.toLowerCase();
  const mimeType = currentFileMimeType.value.toLowerCase();
  return (
    mimeType === 'application/pdf' ||
    url.includes('application/pdf') ||
    url.endsWith('.pdf')
  );
});

const templateTypeLabel = computed(() => {
  const labels: Record<string, string> = {
    custom: $t('form-design.aiImageOcr.customTemplate'),
    id_card: $t('form-design.aiImageOcr.idCard'),
    business_license: $t('form-design.aiImageOcr.businessLicense'),
    invoice: $t('form-design.aiImageOcr.invoice'),
    receipt: $t('form-design.aiImageOcr.receipt'),
    contract: $t('form-design.aiImageOcr.contract'),
  };
  return labels[props.aiOcrConfig?.templateType || 'custom'] || labels.custom;
});

// 获取支持的文件类型标签
const acceptedFileTypesLabel = computed(() => {
  const types = props.aiOcrConfig?.acceptFileTypes || ['image'];
  if (types.includes('all')) {
    return $t('form-design.aiImageOcr.allFiles');
  }
  const labels: Record<string, string> = {
    image: $t('form-design.aiImageOcr.imageFile'),
    text: $t('form-design.aiImageOcr.textFile'),
    pdf: 'PDF',
    word: 'Word',
    excel: 'Excel',
  };
  return types.map((t) => labels[t] || t).join(', ');
});

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  async (newValue) => {
    if (!newValue) {
      currentImageId.value = '';
      currentImageUrl.value = '';
      currentFileMimeType.value = '';
      return;
    }
    const id = Array.isArray(newValue) ? newValue[0] : newValue;
    if (id && id !== currentImageId.value) {
      currentImageId.value = id;
      currentImageUrl.value = await getFileUrl(id);
      // 从后端获取文件信息
      try {
        const fileInfo = await requestClient.get<{ mime_type?: string }>(
          `/api/core/file_manager/${id}`,
        );
        currentFileMimeType.value = fileInfo.mime_type || '';
      } catch (error) {
        console.warn('Failed to fetch file info:', error);
      }
    }
  },
  { immediate: true },
);

// 打开文件选择器
function openFileSelector() {
  if (props.disabled) return;
  uploadInputRef.value?.click();
}

// 处理文件选择
async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  target.value = '';

  // 验证文件类型
  const acceptedTypes = props.aiOcrConfig?.acceptFileTypes || ['image'];
  const isValidType = validateFileType(file, acceptedTypes);
  if (!isValidType) {
    ElMessage.error($t('form-design.aiImageOcr.invalidFileType'));
    return;
  }

  // 验证文件大小
  if (props.maxSize && file.size > props.maxSize * 1024 * 1024) {
    ElMessage.error(
      $t('form-design.aiImageOcr.fileTooLarge', { size: props.maxSize }),
    );
    return;
  }

  await uploadAndRecognize(file);
}

// 验证文件类型
function validateFileType(file: File, acceptedTypes: string[]): boolean {
  if (acceptedTypes.includes('all')) return true;

  const fileName = file.name.toLowerCase();
  const mimeType = file.type.toLowerCase();

  for (const type of acceptedTypes) {
    const accepts = FILE_TYPE_ACCEPT_MAP[type] || [];
    for (const accept of accepts) {
      if (accept.startsWith('.')) {
        // 扩展名匹配
        if (fileName.endsWith(accept)) return true;
      } else if (accept.endsWith('/*')) {
        // MIME 类型通配符匹配
        const prefix = accept.replace('/*', '');
        if (mimeType.startsWith(prefix)) return true;
      } else {
        // 完整 MIME 类型匹配
        if (mimeType === accept) return true;
      }
    }
  }
  return false;
}

// 上传并识别
async function uploadAndRecognize(file: File) {
  try {
    isUploading.value = true;
    uploadProgress.value = 0;

    // 上传文件
    const response = await uploadFileApi(file, {
      source: 'form',
      onProgress: (progressEvent) => {
        uploadProgress.value = progressEvent.percentage;
      },
    });

    if (!response?.id) {
      throw new Error($t('form-design.aiImageOcr.uploadFailed'));
    }

    currentImageId.value = response.id;
    currentImageUrl.value = await getFileUrl(response.id);
    currentFileMimeType.value = file.type;
    isUploading.value = false;

    // 更新 modelValue
    emit('update:modelValue', response.id);
    emit('change', response.id);

    // 如果启用了 AI 识别，开始识别
    if (props.aiOcrConfig?.enabled) {
      await recognizeImage(response.id);
    }
  } catch (error: any) {
    console.error('Upload failed:', error);
    ElMessage.error(error.message || $t('form-design.aiImageOcr.uploadFailed'));
    isUploading.value = false;
  }
}

// AI 识别文件
async function recognizeImage(fileId: string) {
  if (!props.aiOcrConfig?.enabled) return;

  try {
    isRecognizing.value = true;

    // 构建请求参数
    const requestData: any = {
      fileId,
    };

    // 如果有结构化输出配置
    if (
      props.aiOcrConfig.outputSchema &&
      props.aiOcrConfig.outputSchema.length > 0
    ) {
      requestData.outputSchema = props.aiOcrConfig.outputSchema;
    }

    // 如果有自定义提示词
    if (props.aiOcrConfig.customPrompt) {
      requestData.prompt = props.aiOcrConfig.customPrompt;
    }

    // 调用 OCR API
    const result = await requestClient.post<{
      error: null | string;
      extractedData: null | Record<string, any>;
      rawText: null | string;
      success: boolean;
    }>('/api/core/file_manager/ocr/recognize', requestData);

    if (!result.success) {
      throw new Error(
        result.error || $t('form-design.aiImageOcr.recognizeFailed'),
      );
    }

    ocrResult.value = {
      rawText: result.rawText || '',
      extractedData: result.extractedData,
    };

    emit('ocr-success', ocrResult.value);

    if (result.extractedData) {
      applyFieldMapping(result.extractedData);
    } else {
      ElMessage.success($t('form-design.aiImageOcr.recognizeSuccess'));
    }
  } catch (error: any) {
    console.error('OCR failed:', error);
    ElMessage.error(
      error.message || $t('form-design.aiImageOcr.recognizeFailed'),
    );
  } finally {
    isRecognizing.value = false;
  }
}

// 应用字段映射
function applyFieldMapping(extractedData: Record<string, any>) {
  if (!props.aiOcrConfig?.fieldMapping?.length) {
    // 没有配置映射，直接发送原始数据
    emit('fill-fields', extractedData);
    ElMessage.success($t('form-design.aiImageOcr.fillSuccess'));
    return;
  }

  const mappedData: Record<string, any> = {};
  for (const mapping of props.aiOcrConfig.fieldMapping) {
    const value = extractedData[mapping.source];
    if (value !== undefined) {
      mappedData[mapping.target] = value;
    }
  }

  emit('fill-fields', mappedData);
  ElMessage.success($t('form-design.aiImageOcr.fillSuccess'));
}

// 预览图片
function handlePreview() {
  if (currentImageUrl.value) {
    previewVisible.value = true;
  }
}

// 删除图片
function handleDelete() {
  currentImageId.value = '';
  currentImageUrl.value = '';
  ocrResult.value = null;
  emit('update:modelValue', undefined);
  emit('change', undefined);
}

// 重新识别
async function handleReRecognize() {
  if (currentImageId.value) {
    await recognizeImage(currentImageId.value);
  }
}
</script>

<template>
  <div class="ai-image-ocr">
    <!-- 上传区域 -->
    <div
      class="upload-area"
      :class="{
        'has-file': hasFile,
        'is-disabled': disabled,
        'is-uploading': isUploading,
        'is-recognizing': isRecognizing,
      }"
      :style="{ height: height ? `${height}px` : undefined }"
      @click="!hasFile && openFileSelector()"
    >
      <!-- 隐藏的文件输入 -->
      <input
        ref="uploadInputRef"
        type="file"
        :accept="acceptString"
        style="display: none"
        @change="handleFileChange"
      />

      <!-- 空状态 -->
      <template v-if="!hasFile && !isUploading">
        <div class="upload-placeholder">
          <div class="upload-icon">
            <Sparkles class="ai-icon" />
            <FileImageOutlined class="image-icon" />
          </div>
          <div class="upload-text">{{ placeholder }}</div>
          <div class="upload-hint">
            <ElTag size="small" type="primary">
              {{ templateTypeLabel }}
            </ElTag>
            <ElTag size="small" type="info" class="ml-1">
              {{ acceptedFileTypesLabel }}
            </ElTag>
          </div>
        </div>
      </template>

      <!-- 上传中 -->
      <template v-else-if="isUploading">
        <div class="upload-progress">
          <ElProgress
            type="circle"
            :percentage="uploadProgress"
            :width="80"
            :stroke-width="6"
          />
          <div class="progress-text">
            {{ $t('form-design.aiImageOcr.uploading') }}
          </div>
        </div>
      </template>

      <!-- 已上传文件 -->
      <template v-else>
        <div class="file-preview">
          <!-- 图片预览 -->
          <img
            v-if="isImageFile"
            :src="currentImageUrl"
            alt="uploaded"
            class="preview-img"
          />
          <!-- PDF预览 -->
          <iframe
            v-else-if="isPdfFile"
            :src="`${currentImageUrl}#toolbar=0&navpanes=0&scrollbar=1`"
            class="pdf-preview"
            frameborder="0"
          ></iframe>
          <!-- 其他文件显示图标 -->
          <div v-else class="file-icon-wrapper">
            <FileOutlined class="file-icon" />
            <div class="file-name">
              {{ $t('form-design.aiImageOcr.fileUploaded') }}
            </div>
          </div>

          <!-- 识别中遮罩 -->
          <div v-if="isRecognizing" class="recognizing-mask">
            <div class="recognizing-content">
              <Sparkles class="recognizing-icon" />
              <div class="recognizing-text">
                {{ $t('form-design.aiImageOcr.recognizing') }}
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div v-if="!isRecognizing" class="file-actions">
            <ElButton
              v-if="isImageFile || isPdfFile"
              circle
              size="small"
              @click.stop="handlePreview"
            >
              <EyeOutlined />
            </ElButton>
            <ElButton
              v-if="aiOcrConfig?.enabled"
              circle
              size="small"
              type="primary"
              @click.stop="handleReRecognize"
            >
              <Sparkles />
            </ElButton>
            <ElButton
              v-if="clearable"
              circle
              size="small"
              type="danger"
              @click.stop="handleDelete"
            >
              <DeleteOutlined />
            </ElButton>
          </div>

          <!-- AI 标识 -->
          <div v-if="aiOcrConfig?.enabled" class="ai-badge">
            <Sparkles class="badge-icon" />
            AI
          </div>
        </div>
      </template>
    </div>

    <!-- 图片预览 -->
    <ElImageViewer
      v-if="previewVisible && isImageFile"
      :url-list="[currentImageUrl]"
      :z-index="3000"
      @close="previewVisible = false"
    />

    <!-- PDF预览对话框 -->
    <ElDialog
      v-model="previewVisible"
      v-if="isPdfFile"
      :title="$t('form-design.aiImageOcr.preview')"
      width="80%"
      top="5vh"
    >
      <iframe
        :src="`${currentImageUrl}#toolbar=0&navpanes=0&scrollbar=1`"
        style="width: 100%; height: 70vh; border: none"
      ></iframe>
    </ElDialog>
  </div>
</template>

<style lang="scss" scoped>
.ai-image-ocr {
  width: 100%;
}

.upload-area {
  position: relative;
  width: 100%;
  min-height: 120px;
  border: 2px dashed var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: var(--el-fill-color-lighter);

  &:hover:not(.is-disabled):not(.has-file) {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
  }

  &.has-file {
    cursor: default;
    border-style: solid;
  }

  &.is-disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  gap: 8px;

  .upload-icon {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;

    .image-icon {
      font-size: 40px;
      color: var(--el-color-primary);
    }

    .ai-icon {
      position: absolute;
      top: -8px;
      right: -12px;
      font-size: 20px;
      color: var(--el-color-warning);
      animation: sparkle 1.5s ease-in-out infinite;
    }
  }

  .upload-text {
    font-size: 14px;
    color: var(--el-text-color-regular);
  }

  .upload-hint {
    margin-top: 4px;
  }
}

.upload-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  gap: 12px;

  .progress-text {
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.file-preview {
  position: relative;
  width: 100%;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;

  .preview-img {
    max-width: 100%;
    max-height: 200px;
    object-fit: contain;
    border-radius: 4px;
  }

  .pdf-preview {
    width: 100%;
    height: 100%;
    min-height: 400px;
    border: none;
    border-radius: 4px;
  }

  .file-icon-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 16px;

    .file-icon {
      font-size: 48px;
      color: var(--el-color-primary);
    }

    .file-name {
      font-size: 14px;
      color: var(--el-text-color-regular);
    }
  }

  .file-actions {
    position: absolute;
    bottom: 12px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 8px;
    opacity: 0;
    transition: opacity 0.3s;
  }

  &:hover .file-actions {
    opacity: 1;
  }

  .ai-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    background: linear-gradient(
      135deg,
      var(--el-color-primary),
      var(--el-color-primary-light-3)
    );
    color: white;
    font-size: 12px;
    font-weight: 500;
    border-radius: 4px;

    .badge-icon {
      font-size: 14px;
    }
  }
}

.recognizing-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 8px;

  .recognizing-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    color: white;

    .recognizing-icon {
      font-size: 32px;
      animation: sparkle 1s ease-in-out infinite;
    }

    .recognizing-text {
      font-size: 14px;
    }
  }
}

.confirm-content {
  .extracted-data {
    max-height: 300px;
    overflow-y: auto;
    text-align: left;
    padding: 12px;
    background: var(--el-fill-color-light);
    border-radius: 4px;

    .data-item {
      display: flex;
      padding: 8px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);

      &:last-child {
        border-bottom: none;
      }

      .data-label {
        flex-shrink: 0;
        width: 120px;
        font-weight: 500;
        color: var(--el-text-color-secondary);
      }

      .data-value {
        flex: 1;
        color: var(--el-text-color-primary);
        word-break: break-all;
      }
    }
  }
}

@keyframes sparkle {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}
</style>
