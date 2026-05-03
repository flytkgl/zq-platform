<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';

import { RotateCcw } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElMessage } from 'element-plus';

import { uploadFile as uploadFileApi } from '#/api/core/file';
import { ZqDialog } from '#/components/zq-dialog';

interface Props {
  visible: boolean;
  penColor?: string;
  penWidth?: number;
  backgroundColor?: string;
  source?: string;
}

const props = withDefaults(defineProps<Props>(), {
  penColor: '#000000',
  penWidth: 2,
  backgroundColor: '#ffffff',
  source: 'form',
});

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void;
  (e: 'complete', fileId: string): void;
}>();

// Canvas 相关
const canvasRef = ref<HTMLCanvasElement>();
const containerRef = ref<HTMLDivElement>();
let ctx: CanvasRenderingContext2D | null = null;
let isDrawing = false;
let lastX = 0;
let lastY = 0;

// 状态
const hasSignature = ref(false);
const isUploading = ref(false);

// 计算属性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
});

// 初始化画布
function initCanvas() {
  if (!canvasRef.value || !containerRef.value) return;

  const canvas = canvasRef.value;
  const container = containerRef.value;

  // 设置画布尺寸
  const rect = container.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;

  ctx = canvas.getContext('2d');
  if (!ctx) return;

  // 设置画笔样式
  ctx.strokeStyle = props.penColor;
  ctx.lineWidth = props.penWidth;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  // 设置背景
  if (props.backgroundColor !== 'transparent') {
    ctx.fillStyle = props.backgroundColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }
}

// 获取鼠标/触摸位置
function getPosition(e: MouseEvent | TouchEvent): { x: number; y: number } {
  const canvas = canvasRef.value;
  if (!canvas) return { x: 0, y: 0 };

  const rect = canvas.getBoundingClientRect();

  if ('touches' in e) {
    const touch = e.touches[0];
    return {
      x: touch ? touch.clientX - rect.left : 0,
      y: touch ? touch.clientY - rect.top : 0,
    };
  }

  return {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
  };
}

// 开始绘制
function startDrawing(e: MouseEvent | TouchEvent) {
  if (!ctx) return;

  e.preventDefault();
  isDrawing = true;
  const pos = getPosition(e);
  lastX = pos.x;
  lastY = pos.y;
}

// 绘制中
function draw(e: MouseEvent | TouchEvent) {
  if (!isDrawing || !ctx) return;

  e.preventDefault();
  const pos = getPosition(e);

  ctx.beginPath();
  ctx.moveTo(lastX, lastY);
  ctx.lineTo(pos.x, pos.y);
  ctx.stroke();

  lastX = pos.x;
  lastY = pos.y;
  hasSignature.value = true;
}

// 结束绘制
function stopDrawing() {
  isDrawing = false;
}

// 清除签名
function clearSignature() {
  const canvas = canvasRef.value;
  if (!canvas || !ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 重新填充背景
  if (props.backgroundColor !== 'transparent') {
    ctx.fillStyle = props.backgroundColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  hasSignature.value = false;
}

// 确认签名
async function confirmSignature() {
  const canvas = canvasRef.value;
  if (!canvas || !hasSignature.value) {
    ElMessage.warning($t('form-design.signaturePad.pleaseSign'));
    return;
  }

  try {
    isUploading.value = true;

    // 创建一个新的 canvas，先填充白色背景再绘制签名
    const exportCanvas = document.createElement('canvas');
    exportCanvas.width = canvas.width;
    exportCanvas.height = canvas.height;
    const exportCtx = exportCanvas.getContext('2d');
    if (!exportCtx) {
      throw new Error('Failed to create export canvas');
    }

    // 填充白色背景
    exportCtx.fillStyle = '#ffffff';
    exportCtx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);

    // 绘制签名
    exportCtx.drawImage(canvas, 0, 0);

    // 转换为 Blob
    const blob = await new Promise<Blob | null>((resolve) => {
      exportCanvas.toBlob(resolve, 'image/png');
    });

    if (!blob) {
      throw new Error('Failed to create signature image');
    }

    // 创建 File 对象
    const file = new File([blob], `signature_${Date.now()}.png`, {
      type: 'image/png',
    });

    // 上传文件
    const result = await uploadFileApi(file, { source: props.source });

    if (result?.id) {
      emit('complete', result.id);
      dialogVisible.value = false;
    }
  } catch (error) {
    console.error('Upload signature failed:', error);
    ElMessage.error($t('form-design.signaturePad.uploadFailed'));
  } finally {
    isUploading.value = false;
  }
}

// 取消
function handleCancel() {
  dialogVisible.value = false;
  hasSignature.value = false;
}

// 弹窗打开后初始化画布
function handleOpened() {
  nextTick(() => {
    initCanvas();
  });
}

// 监听画笔属性变化
watch(
  () => [props.penColor, props.penWidth],
  () => {
    if (ctx) {
      ctx.strokeStyle = props.penColor;
      ctx.lineWidth = props.penWidth;
    }
  },
);

// 窗口大小变化时重新初始化
let resizeObserver: null | ResizeObserver = null;

watch(dialogVisible, (visible) => {
  if (visible) {
    nextTick(() => {
      if (containerRef.value) {
        resizeObserver = new ResizeObserver(() => {
          initCanvas();
        });
        resizeObserver.observe(containerRef.value);
      }
    });
  } else {
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    hasSignature.value = false;
  }
});

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
});
</script>

<template>
  <ZqDialog
    v-model="dialogVisible"
    :title="$t('form-design.signaturePad.signNow')"
    width="700px"
    :close-on-click-modal="false"
    @opened="handleOpened"
  >
    <div class="signature-dialog">
      <div class="signature-dialog__tip">
        {{ $t('form-design.signaturePad.dialogTip') }}
      </div>

      <div ref="containerRef" class="signature-dialog__canvas-wrapper">
        <canvas
          ref="canvasRef"
          class="signature-dialog__canvas"
          @mousedown="startDrawing"
          @mousemove="draw"
          @mouseup="stopDrawing"
          @mouseleave="stopDrawing"
          @touchstart="startDrawing"
          @touchmove="draw"
          @touchend="stopDrawing"
        ></canvas>

        <!-- 占位提示 -->
        <div v-if="!hasSignature" class="signature-dialog__placeholder">
          {{ $t('form-design.signaturePad.drawHere') }}
        </div>
      </div>

      <!-- 工具栏 -->
      <div class="signature-dialog__toolbar">
        <ElButton
          type="default"
          :icon="RotateCcw"
          :disabled="!hasSignature"
          @click="clearSignature"
        >
          {{ $t('form-design.signaturePad.redo') }}
        </ElButton>
      </div>
    </div>

    <template #footer>
      <ElButton @click="handleCancel">
        {{ $t('common.cancel') }}
      </ElButton>
      <ElButton
        type="primary"
        :loading="isUploading"
        :disabled="!hasSignature"
        @click="confirmSignature"
      >
        {{ $t('form-design.signaturePad.confirmSign') }}
      </ElButton>
    </template>
  </ZqDialog>
</template>

<style scoped>
.signature-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.signature-dialog__tip {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.signature-dialog__canvas-wrapper {
  position: relative;
  height: 300px;
  border: 2px dashed var(--el-border-color);
  border-radius: 8px;
  background-color: var(--el-fill-color-lighter);
  overflow: hidden;
  cursor: crosshair;
  touch-action: none;
}

.signature-dialog__canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.signature-dialog__placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 16px;
  color: var(--el-text-color-placeholder);
  pointer-events: none;
  user-select: none;
}

.signature-dialog__toolbar {
  display: flex;
  justify-content: flex-end;
}
</style>
