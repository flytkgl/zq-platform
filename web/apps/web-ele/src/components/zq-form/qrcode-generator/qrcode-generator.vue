<script setup lang="ts">
import type { QRCodeGeneratorEmits, QRCodeGeneratorProps } from './types';

import { computed, nextTick, onMounted, ref, watch } from 'vue';

import { Copy, Download, QrCode } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElMessage, ElTooltip } from 'element-plus';
import QRCode from 'qrcode';

defineOptions({
  name: 'QRCodeGenerator',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<QRCodeGeneratorProps>(), {
  dataSource: 'static',
  qrcodeType: 'text',
  size: 200,
  errorCorrectionLevel: 'M',
  foregroundColor: '#000000',
  backgroundColor: '#FFFFFF',
  logoSize: 40,
  margin: 2,
  showContent: false,
  enableDownload: false,
  enableCopy: false,
  downloadFilename: 'qrcode',
  disabled: false,
  readonly: false,
  placeholder: '',
});

const emit = defineEmits<QRCodeGeneratorEmits>();

// 状态
const qrcodeUrl = ref<string>('');
const isGenerating = ref(false);
const canvasRef = ref<HTMLCanvasElement>();

// 计算二维码内容
const qrcodeContent = computed(() => {
  let content = '';

  switch (props.dataSource) {
    case 'field': {
      if (props.boundField && props.formData) {
        content = String(props.formData[props.boundField] || '');
      }
      break;
    }
    case 'formula': {
      if (props.formula && props.formData) {
        content = parseFormula(props.formula, props.formData);
      }
      break;
    }
    case 'static': {
      content = props.modelValue || '';
      break;
    }
  }

  // 根据二维码类型格式化内容
  return formatContent(content);
});

// 解析公式中的变量
function parseFormula(formula: string, data: Record<string, any>): string {
  return formula.replaceAll(/\{\{(\w+)\}\}/g, (_, key) => {
    return String(data[key] || '');
  });
}

// 根据类型格式化内容
function formatContent(content: string): string {
  if (!content) return '';

  switch (props.qrcodeType) {
    case 'email': {
      return `mailto:${content}`;
    }
    case 'sms': {
      return `sms:${content}`;
    }
    case 'tel': {
      return `tel:${content}`;
    }
    case 'url': {
      // 自动添加 http:// 前缀
      if (
        content &&
        !content.startsWith('http://') &&
        !content.startsWith('https://')
      ) {
        return `https://${content}`;
      }
      return content;
    }
    default: {
      return content;
    }
  }
}

// 生成二维码
async function generateQRCode() {
  const content = qrcodeContent.value;
  if (!content) {
    qrcodeUrl.value = '';
    return;
  }

  isGenerating.value = true;

  try {
    // 使用 canvas 生成二维码
    const canvas = canvasRef.value;
    if (!canvas) return;

    await QRCode.toCanvas(canvas, content, {
      width: props.size,
      margin: props.margin,
      errorCorrectionLevel: props.errorCorrectionLevel,
      color: {
        dark: props.foregroundColor,
        light: props.backgroundColor,
      },
    });

    // 如果有 Logo，绘制 Logo
    if (props.logoUrl) {
      await drawLogo(canvas, props.logoUrl);
    }

    // 转换为 Data URL
    qrcodeUrl.value = canvas.toDataURL('image/png');

    emit('generated', content);
  } catch (error) {
    console.error('Generate QRCode failed:', error);
    ElMessage.error($t('form-design.qrcode.generateError'));
  } finally {
    isGenerating.value = false;
  }
}

// 绘制 Logo
async function drawLogo(
  canvas: HTMLCanvasElement,
  logoUrl: string,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      resolve();
      return;
    }

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.addEventListener('load', () => {
      const logoSize = props.logoSize;
      const x = (canvas.width - logoSize) / 2;
      const y = (canvas.height - logoSize) / 2;

      // 绘制白色背景
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(x - 2, y - 2, logoSize + 4, logoSize + 4);

      // 绘制 Logo
      ctx.drawImage(img, x, y, logoSize, logoSize);
      resolve();
    });
    img.onerror = () => {
      console.warn('Load logo failed');
      resolve();
    };
    img.src = logoUrl;
  });
}

// 下载二维码
function downloadQRCode() {
  if (!qrcodeUrl.value) return;

  const link = document.createElement('a');
  link.download = `${props.downloadFilename}.png`;
  link.href = qrcodeUrl.value;
  link.click();

  emit('downloaded');
  ElMessage.success($t('form-design.qrcode.downloadSuccess'));
}

// 复制二维码内容
async function copyContent() {
  const content = qrcodeContent.value;
  if (!content) return;

  try {
    await navigator.clipboard.writeText(content);
    emit('copied');
    ElMessage.success($t('form-design.qrcode.copySuccess'));
  } catch (error) {
    console.error('Copy failed:', error);
    ElMessage.error($t('form-design.qrcode.copyError'));
  }
}

// 占位提示文本
const placeholderText = computed(
  () => props.placeholder || $t('form-design.qrcode.placeholder'),
);

// 容器样式
const containerStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
}));

// 监听内容变化，重新生成二维码
watch(
  () => [
    qrcodeContent.value,
    props.size,
    props.foregroundColor,
    props.backgroundColor,
    props.errorCorrectionLevel,
    props.margin,
    props.logoUrl,
  ],
  () => {
    nextTick(() => {
      generateQRCode();
    });
  },
  { immediate: true },
);

onMounted(() => {
  generateQRCode();
});
</script>

<template>
  <div class="qrcode-generator">
    <!-- 二维码显示区域 -->
    <div
      class="qrcode-generator__container"
      :class="{
        'qrcode-generator__container--empty': !qrcodeContent,
        'qrcode-generator__container--disabled': disabled,
      }"
      :style="containerStyle"
    >
      <!-- 隐藏的 canvas 用于生成 -->
      <canvas ref="canvasRef" style="display: none"></canvas>

      <!-- 二维码图片 -->
      <img
        v-if="qrcodeUrl"
        :src="qrcodeUrl"
        alt="QRCode"
        class="qrcode-generator__image"
      />

      <!-- 空状态 -->
      <div v-else class="qrcode-generator__placeholder">
        <QrCode class="qrcode-generator__placeholder-icon" />
        <span class="qrcode-generator__placeholder-text">{{
          placeholderText
        }}</span>
      </div>

      <!-- 加载状态 -->
      <div v-if="isGenerating" class="qrcode-generator__loading">
        <div class="qrcode-generator__spinner"></div>
      </div>
    </div>

    <!-- 内容显示 -->
    <div v-if="showContent && qrcodeContent" class="qrcode-generator__content">
      <ElTooltip :content="qrcodeContent" placement="top" :show-after="300">
        <span class="qrcode-generator__content-text">{{ qrcodeContent }}</span>
      </ElTooltip>
    </div>

    <!-- 操作按钮 -->
    <div
      v-if="(enableDownload || enableCopy) && qrcodeUrl && !disabled"
      class="qrcode-generator__actions"
    >
      <ElButton
        v-if="enableDownload"
        type="primary"
        size="small"
        :icon="Download"
        @click="downloadQRCode"
      >
        {{ $t('form-design.qrcode.download') }}
      </ElButton>
      <ElButton
        v-if="enableCopy"
        size="small"
        :icon="Copy"
        @click="copyContent"
      >
        {{ $t('form-design.qrcode.copy') }}
      </ElButton>
    </div>
  </div>
</template>

<style scoped>
.qrcode-generator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.qrcode-generator__container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #fff;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  overflow: hidden;
}

.qrcode-generator__container--empty {
  border-style: dashed;
}

.qrcode-generator__container--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.qrcode-generator__image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.qrcode-generator__placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--el-text-color-placeholder);
}

.qrcode-generator__placeholder-icon {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.qrcode-generator__placeholder-text {
  font-size: 12px;
  text-align: center;
  max-width: 80%;
}

.qrcode-generator__loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.8);
}

.qrcode-generator__spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--el-border-color);
  border-top-color: var(--el-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.qrcode-generator__content {
  max-width: 100%;
  padding: 0 8px;
}

.qrcode-generator__content-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  word-break: break-all;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.qrcode-generator__actions {
  display: flex;
  gap: 8px;
}
</style>
