<script lang="ts" setup>
/**
 * 移动端签名页面（无需登录）
 * 用于扫码后在手机上完成签名
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { Check, Pen, RotateCcw } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElMessage } from 'element-plus';

import { getSignatureTokenInfo, uploadSignatureImage } from '#/api/core/file';

defineOptions({ name: 'MobileSignaturePage' });

const route = useRoute();

// 签名令牌
const token = computed(() => route.params.token as string);

// 页面状态
const loading = ref(true);
const error = ref('');
const tokenInfo = ref<null | {
  expired_at: string;
  source: string;
  token: string;
}>(null);
const signSuccess = ref(false);

// 签名画布
const canvasRef = ref<HTMLCanvasElement>();
const containerRef = ref<HTMLDivElement>();
let ctx: CanvasRenderingContext2D | null = null;
let isDrawing = false;
let lastX = 0;
let lastY = 0;

// 状态
const hasSignature = ref(false);
const isUploading = ref(false);

// 加载令牌信息
async function loadTokenInfo() {
  if (!token.value) {
    error.value = $t('form-design.signaturePad.invalidSignUrl');
    loading.value = false;
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    tokenInfo.value = await getSignatureTokenInfo(token.value);
  } catch (error_: any) {
    console.error('Load token info failed:', error_);
    error.value = error_.message || $t('form-design.signaturePad.loadFailed');
  } finally {
    loading.value = false;
  }
}

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
  ctx.strokeStyle = '#000000';
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

  // 设置白色背景
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
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

  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
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

    // 转换为 Blob
    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, 'image/png');
    });

    if (!blob) {
      throw new Error('Failed to create signature image');
    }

    // 创建 File 对象
    const file = new File([blob], `signature_${Date.now()}.png`, {
      type: 'image/png',
    });

    // 上传签名图片并完成签名（一步完成）
    await uploadSignatureImage(token.value, file);

    signSuccess.value = true;
    ElMessage.success($t('form-design.signaturePad.signCompleted'));
  } catch (error_: any) {
    console.error('Sign failed:', error_);
    ElMessage.error(
      error_.message || $t('form-design.signaturePad.uploadFailed'),
    );
  } finally {
    isUploading.value = false;
  }
}

// 窗口大小变化时重新初始化
let resizeObserver: null | ResizeObserver = null;

onMounted(async () => {
  await loadTokenInfo();

  if (tokenInfo.value) {
    nextTick(() => {
      initCanvas();

      if (containerRef.value) {
        resizeObserver = new ResizeObserver(() => {
          initCanvas();
        });
        resizeObserver.observe(containerRef.value);
      }
    });
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
  <div class="mobile-signature-page">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <div class="loading-text">{{ $t('common.loading') }}</div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <div class="error-title">{{ error }}</div>
      <div class="error-subtitle">
        {{ $t('form-design.signaturePad.checkSignUrl') }}
      </div>
    </div>

    <!-- 签署成功 -->
    <div v-else-if="signSuccess" class="success-container">
      <div class="success-animation">
        <div class="success-checkmark">
          <Check class="success-icon" />
        </div>
      </div>
      <div class="success-title">
        {{ $t('form-design.signaturePad.signCompleted') }}
      </div>
      <div class="success-subtitle">
        {{ $t('form-design.signaturePad.signCompletedTip') }}
      </div>
      <div class="success-tip">
        {{ $t('form-design.signaturePad.canClosePage') }}
      </div>
    </div>

    <!-- 签名内容 -->
    <div v-else-if="tokenInfo" class="signature-container">
      <!-- 顶部提示栏 -->
      <div class="signature-header">
        <div class="header-icon">
          <Pen />
        </div>
        <div class="header-content">
          <div class="header-title">
            {{ $t('form-design.signaturePad.mobileSign') }}
          </div>
          <div class="header-tip">
            {{ $t('form-design.signaturePad.signatureTip') }}
          </div>
        </div>
      </div>

      <!-- 签名画布区域 -->
      <div class="canvas-section">
        <div ref="containerRef" class="canvas-wrapper">
          <canvas
            ref="canvasRef"
            class="signature-canvas"
            @mousedown="startDrawing"
            @mousemove="draw"
            @mouseup="stopDrawing"
            @mouseleave="stopDrawing"
            @touchstart="startDrawing"
            @touchmove="draw"
            @touchend="stopDrawing"
          ></canvas>

          <!-- 占位提示 -->
          <div v-if="!hasSignature" class="canvas-placeholder">
            <Pen class="placeholder-icon" />
            <div class="placeholder-text">
              {{ $t('form-design.signaturePad.drawHere') }}
            </div>
          </div>

          <!-- 签名引导线 -->
          <div class="guide-line"></div>

          <!-- 签名提示文字 -->
          <!-- <div class="guide-text">{{ $t('form-design.signaturePad.signHere') }}</div> -->
        </div>
      </div>

      <!-- 底部操作区 -->
      <div class="action-section">
        <!-- 清除按钮 -->
        <button
          class="action-button action-button--secondary"
          :disabled="!hasSignature"
          @click="clearSignature"
        >
          <RotateCcw class="action-icon" />
          <span>{{ $t('form-design.signaturePad.redo') }}</span>
        </button>

        <!-- 确认按钮 -->
        <button
          class="action-button action-button--primary"
          :class="{ 'is-loading': isUploading, 'is-disabled': !hasSignature }"
          :disabled="!hasSignature || isUploading"
          @click="confirmSignature"
        >
          <div v-if="isUploading" class="button-loading">
            <div class="loading-spinner-small"></div>
          </div>
          <Check v-else class="action-icon" />
          <span>{{
            isUploading
              ? $t('form-design.signaturePad.uploading')
              : $t('form-design.signaturePad.confirmSign')
          }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 页面容器 */
.mobile-signature-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f7fa 0%, #e8ecf1 100%);
  display: flex;
  flex-direction: column;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 20px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top-color: var(--el-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 15px;
  color: var(--el-text-color-regular);
  font-weight: 500;
}

/* 错误状态 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 32px;
  text-align: center;
}

.error-icon {
  font-size: 64px;
  margin-bottom: 24px;
}

.error-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
}

.error-subtitle {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

/* 成功状态 */
.success-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 32px;
  text-align: center;
}

.success-animation {
  margin-bottom: 32px;
}

.success-checkmark {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(103, 194, 58, 0.3);
  animation: scaleIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes scaleIn {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.success-icon {
  width: 40px;
  height: 40px;
  color: white;
  stroke-width: 3;
}

.success-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
}

.success-subtitle {
  font-size: 15px;
  color: var(--el-text-color-regular);
  margin-bottom: 24px;
  line-height: 1.6;
}

.success-tip {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  padding: 12px 20px;
  background-color: var(--el-fill-color-light);
  border-radius: 8px;
}

/* 签名容器 */
.signature-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: transparent;
}

/* 顶部提示栏 */
.signature-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.header-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(
    135deg,
    var(--el-color-primary) 0%,
    var(--el-color-primary-light-3) 100%
  );
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}

.header-icon svg {
  width: 20px;
  height: 20px;
}

.header-content {
  flex: 1;
  padding-top: 2px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.header-tip {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

/* 画布区域 */
.canvas-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.canvas-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
  max-height: 500px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  touch-action: none;
}

.signature-canvas {
  display: block;
  width: 100%;
  height: 100%;
  cursor: crosshair;
  touch-action: none;
}

/* 占位提示 */
.canvas-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
  user-select: none;
  opacity: 0.4;
}

.placeholder-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
  color: var(--el-text-color-placeholder);
}

.placeholder-text {
  font-size: 15px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

/* 引导线 */
.guide-line {
  position: absolute;
  bottom: 35%;
  left: 15%;
  right: 15%;
  height: 2px;
  background: repeating-linear-gradient(
    90deg,
    var(--el-border-color) 0,
    var(--el-border-color) 8px,
    transparent 8px,
    transparent 16px
  );
  pointer-events: none;
  opacity: 0.3;
}

.guide-text {
  position: absolute;
  bottom: 35%;
  left: 15%;
  transform: translateY(20px);
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  pointer-events: none;
  user-select: none;
}

/* 底部操作区 */
.action-section {
  display: flex;
  gap: 12px;
  padding: 16px 20px 32px;
  background: white;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
}

.action-button {
  flex: 1;
  height: 48px;
  border-radius: 12px;
  border: none;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.action-button::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition:
    width 0.6s,
    height 0.6s;
}

.action-button:active::before {
  width: 300px;
  height: 300px;
}

.action-icon {
  width: 20px;
  height: 20px;
  stroke-width: 2.5;
}

/* 次要按钮 */
.action-button--secondary {
  background: var(--el-fill-color);
  color: var(--el-text-color-primary);
  border: 1px solid var(--el-border-color);
}

.action-button--secondary:hover:not(:disabled) {
  background: var(--el-fill-color-light);
  border-color: var(--el-border-color-darker);
}

.action-button--secondary:active:not(:disabled) {
  transform: scale(0.98);
}

.action-button--secondary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 主要按钮 */
.action-button--primary {
  background: linear-gradient(
    135deg,
    var(--el-color-primary) 0%,
    var(--el-color-primary-light-3) 100%
  );
  color: white;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.action-button--primary:hover:not(:disabled):not(.is-loading) {
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
  transform: translateY(-1px);
}

.action-button--primary:active:not(:disabled):not(.is-loading) {
  transform: translateY(0) scale(0.98);
}

.action-button--primary.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.action-button--primary.is-loading {
  cursor: wait;
}

/* 按钮加载状态 */
.button-loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-spinner-small {
  width: 20px;
  height: 20px;
  border: 2.5px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 响应式优化 */
@media (max-width: 375px) {
  .canvas-wrapper {
    min-height: 350px;
  }

  .action-button {
    height: 44px;
    font-size: 15px;
  }
}

@media (min-width: 768px) {
  .canvas-wrapper {
    max-width: 600px;
    margin: 0 auto;
  }
}
</style>
