<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';

import { Check, Clock, RefreshCw, Smartphone } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElIcon, ElMessage, ElResult } from 'element-plus';
import QRCode from 'qrcode';

import { checkSignatureStatus, createSignatureToken } from '#/api/core/file';
import { ZqDialog } from '#/components/zq-dialog';

interface Props {
  visible: boolean;
  source?: string;
}

const props = withDefaults(defineProps<Props>(), {
  source: 'form',
});

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void;
  (e: 'complete', fileId: string): void;
}>();

// 状态
const qrcodeUrl = ref('');
const callbackKey = ref('');
const expiredAt = ref('');
const isLoading = ref(false);
const isWaiting = ref(false);
const isCompleted = ref(false);
const completedFileId = ref('');
let pollInterval: null | ReturnType<typeof setInterval> = null;

// 计算属性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
});

// 过期时间显示
const expiredTimeText = computed(() => {
  if (!expiredAt.value) return '';
  const date = new Date(expiredAt.value);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
});

// 生成签名令牌和二维码
async function generateQRCode() {
  try {
    isLoading.value = true;

    // 调用后端API创建签名令牌
    const result = await createSignatureToken(props.source, 30);

    callbackKey.value = result.callback_key;
    expiredAt.value = result.expired_at;

    // 构建手机签名页面URL
    const baseUrl = window.location.origin;
    const signatureUrl = `${baseUrl}/mobile-signature/${result.token}`;

    // 生成二维码
    qrcodeUrl.value = await QRCode.toDataURL(signatureUrl, {
      width: 200,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#ffffff',
      },
    });

    // 开始轮询检查签名状态
    startPolling();
  } catch (error) {
    console.error('Generate QRCode failed:', error);
    ElMessage.error($t('form-design.signaturePad.qrcodeError'));
  } finally {
    isLoading.value = false;
  }
}

// 开始轮询检查签名状态
function startPolling() {
  isWaiting.value = true;

  // 调用后端API检查签名状态
  pollInterval = setInterval(async () => {
    if (!callbackKey.value) return;

    try {
      const result = await checkSignatureStatus(callbackKey.value);

      if (result.status === 'completed' && result.file_id) {
        completedFileId.value = result.file_id;
        isCompleted.value = true;
        isWaiting.value = false;
        stopPolling();
      } else if (result.status === 'expired') {
        isWaiting.value = false;
        stopPolling();
        ElMessage.warning($t('form-design.signaturePad.qrcodeExpired'));
      }
    } catch (error) {
      console.error('Check signature status failed:', error);
    }
  }, 2000);
}

// 停止轮询
function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
}

// 确认使用签名
function confirmSignature() {
  if (completedFileId.value) {
    emit('complete', completedFileId.value);
    dialogVisible.value = false;
  }
}

// 取消
function handleCancel() {
  dialogVisible.value = false;
}

// 重新生成二维码
function regenerateQRCode() {
  stopPolling();
  isCompleted.value = false;
  completedFileId.value = '';
  qrcodeUrl.value = '';
  callbackKey.value = '';
  expiredAt.value = '';
  generateQRCode();
}

// 弹窗打开时生成二维码
function handleOpened() {
  generateQRCode();
}

// 弹窗关闭时清理
watch(dialogVisible, (visible) => {
  if (!visible) {
    stopPolling();
    qrcodeUrl.value = '';
    callbackKey.value = '';
    expiredAt.value = '';
    isWaiting.value = false;
    isCompleted.value = false;
    completedFileId.value = '';
  }
});

onBeforeUnmount(() => {
  stopPolling();
});
</script>

<template>
  <ZqDialog
    v-model="dialogVisible"
    :title="$t('form-design.signaturePad.mobileSign')"
    width="420px"
    :close-on-click-modal="false"
    @opened="handleOpened"
  >
    <div class="mobile-signature-dialog">
      <!-- 签名完成状态 -->
      <template v-if="isCompleted">
        <ElResult
          icon="success"
          :title="$t('form-design.signaturePad.signCompleted')"
          :sub-title="$t('form-design.signaturePad.signCompletedTip')"
        >
          <template #icon>
            <div class="success-icon">
              <Check class="success-icon__check" />
            </div>
          </template>
        </ElResult>
      </template>

      <!-- 等待签名状态 -->
      <template v-else>
        <div v-loading="isLoading" class="mobile-signature-dialog__content">
          <div class="mobile-signature-dialog__icon">
            <Smartphone class="mobile-signature-dialog__smartphone" />
          </div>

          <div class="mobile-signature-dialog__tip">
            {{ $t('form-design.signaturePad.scanQrcodeTip') }}
          </div>

          <div class="mobile-signature-dialog__qrcode">
            <img v-if="qrcodeUrl" :src="qrcodeUrl" alt="QRCode" />
            <div v-else class="mobile-signature-dialog__loading">
              {{ $t('common.loading') }}
            </div>
          </div>

          <div v-if="isWaiting" class="mobile-signature-dialog__waiting">
            <span class="mobile-signature-dialog__dot"></span>
            {{ $t('form-design.signaturePad.waitingForSign') }}
          </div>

          <div v-if="expiredAt" class="mobile-signature-dialog__expired">
            <ElIcon><Clock /></ElIcon>
            <span>{{
              $t('form-design.signaturePad.qrcodeExpiredAt', {
                time: expiredTimeText,
              })
            }}</span>
          </div>
        </div>
      </template>
    </div>

    <template #footer>
      <template v-if="isCompleted">
        <ElButton @click="regenerateQRCode">
          {{ $t('form-design.signaturePad.resignMobile') }}
        </ElButton>
        <ElButton type="primary" @click="confirmSignature">
          {{ $t('form-design.signaturePad.useThisSignature') }}
        </ElButton>
      </template>
      <template v-else>
        <div class="mobile-signature-dialog__footer">
          <ElButton
            :icon="RefreshCw"
            :loading="isLoading"
            @click="regenerateQRCode"
          >
            {{ $t('form-design.signaturePad.refreshQrcode') }}
          </ElButton>
          <ElButton @click="handleCancel">
            {{ $t('common.cancel') }}
          </ElButton>
        </div>
      </template>
    </template>
  </ZqDialog>
</template>

<style scoped>
.mobile-signature-dialog {
  min-height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.mobile-signature-dialog__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.mobile-signature-dialog__icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--el-color-primary-light-9);
  border-radius: 50%;
}

.mobile-signature-dialog__smartphone {
  width: 24px;
  height: 24px;
  color: var(--el-color-primary);
}

.mobile-signature-dialog__tip {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.mobile-signature-dialog__qrcode {
  padding: 16px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.mobile-signature-dialog__qrcode img {
  display: block;
  width: 200px;
  height: 200px;
}

.mobile-signature-dialog__loading {
  width: 200px;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
}

.mobile-signature-dialog__waiting {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--el-color-primary);
}

.mobile-signature-dialog__dot {
  width: 8px;
  height: 8px;
  background-color: var(--el-color-primary);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.8);
  }
}

.success-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--el-color-success-light-9);
  border-radius: 50%;
}

.success-icon__check {
  width: 32px;
  height: 32px;
  color: var(--el-color-success);
}

.mobile-signature-dialog__expired {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.mobile-signature-dialog__footer {
  display: flex;
  justify-content: space-between;
  width: 100%;
}
</style>
