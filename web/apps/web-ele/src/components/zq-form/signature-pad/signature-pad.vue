<script setup lang="ts">
import type { SignaturePadEmits, SignaturePadProps } from './types';

import { computed, ref, watch } from 'vue';

import { Eraser, PenLine, Smartphone } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import { getFileUrl } from '#/composables/useFileUrl';

import MobileSignatureDialog from './MobileSignatureDialog.vue';
import SignatureDialog from './SignatureDialog.vue';

defineOptions({
  name: 'SignaturePad',
  inheritAttrs: false,
});

const props = withDefaults(defineProps<SignaturePadProps>(), {
  penColor: '#000000',
  penWidth: 2,
  backgroundColor: '#ffffff',
  width: '100%',
  height: 200,
  disabled: false,
  readonly: false,
  placeholder: '',
  source: 'form',
});

const emit = defineEmits<SignaturePadEmits>();

// 状态
const signatureUrl = ref<string>('');
const isHovering = ref(false);
const signatureDialogVisible = ref(false);
const mobileSignatureDialogVisible = ref(false);

// 计算属性
const isDisabled = computed(() => props.disabled || props.readonly);
const hasSignature = computed(() => !!props.modelValue && !!signatureUrl.value);

const containerStyle = computed(() => ({
  width: typeof props.width === 'number' ? `${props.width}px` : props.width,
  height: `${props.height}px`,
}));

const placeholderText = computed(
  () => props.placeholder || $t('form-design.signaturePad.placeholder'),
);

// 打开立即签名弹窗
function openSignatureDialog() {
  if (isDisabled.value) return;
  signatureDialogVisible.value = true;
}

// 打开手机签名弹窗
function openMobileSignatureDialog() {
  if (isDisabled.value) return;
  mobileSignatureDialogVisible.value = true;
}

// 签名完成回调
function handleSignatureComplete(fileId: string) {
  emit('update:modelValue', fileId);
  emit('change', fileId);
  emit('signed');
  signatureDialogVisible.value = false;
  mobileSignatureDialogVisible.value = false;
}

// 清除签名
function clearSignature() {
  if (isDisabled.value) return;
  signatureUrl.value = '';
  emit('update:modelValue', null);
  emit('change', null);
  emit('cleared');
}

// 加载已有签名
async function loadSignature(fileId: string) {
  if (!fileId) {
    signatureUrl.value = '';
    return;
  }

  try {
    const url = await getFileUrl(fileId);
    signatureUrl.value = url;
  } catch (error) {
    console.error('Load signature failed:', error);
    signatureUrl.value = '';
  }
}

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      loadSignature(newValue);
    } else {
      signatureUrl.value = '';
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="signature-pad">
    <!-- 已有签名时显示图片 -->
    <div
      v-if="hasSignature"
      class="signature-pad__preview"
      :style="containerStyle"
      @mouseenter="isHovering = true"
      @mouseleave="isHovering = false"
    >
      <img :src="signatureUrl" alt="signature" class="signature-pad__image" />
      <Transition name="fade">
        <div v-if="isHovering && !isDisabled" class="signature-pad__overlay">
          <div class="signature-pad__actions">
            <ElButton
              type="primary"
              size="small"
              plain
              :icon="PenLine"
              @click="openSignatureDialog"
            >
              {{ $t('form-design.signaturePad.resignNow') }}
            </ElButton>
            <ElButton
              type="danger"
              size="small"
              :icon="Eraser"
              @click="clearSignature"
            >
              {{ $t('form-design.signaturePad.clear') }}
            </ElButton>
          </div>
        </div>
      </Transition>
    </div>

    <!-- 未签名时显示触发区域 -->
    <div
      v-else
      class="signature-pad__trigger"
      :class="{
        'signature-pad__trigger--disabled': isDisabled,
        'signature-pad__trigger--hover': isHovering,
      }"
      :style="containerStyle"
      @mouseenter="isHovering = true"
      @mouseleave="isHovering = false"
    >
      <!-- 默认状态 -->
      <div v-if="!isHovering || isDisabled" class="signature-pad__placeholder">
        <PenLine class="signature-pad__placeholder-icon" />
        <span class="text-sm">{{ placeholderText }}</span>
      </div>

      <!-- Hover 状态显示操作按钮 -->
      <Transition name="fade">
        <div v-if="isHovering && !isDisabled" class="signature-pad__actions">
          <ElButton
            type="primary"
            plain
            size="small"
            :icon="PenLine"
            @click="openSignatureDialog"
          >
            {{ $t('form-design.signaturePad.signNow') }}
          </ElButton>
          <ElButton
            type="default"
            size="small"
            :icon="Smartphone"
            @click="openMobileSignatureDialog"
          >
            {{ $t('form-design.signaturePad.mobileSign') }}
          </ElButton>
        </div>
      </Transition>
    </div>

    <!-- 立即签名弹窗 -->
    <SignatureDialog
      v-model:visible="signatureDialogVisible"
      :pen-color="penColor"
      :pen-width="penWidth"
      :background-color="backgroundColor"
      :source="source"
      @complete="handleSignatureComplete"
    />

    <!-- 手机签名弹窗 -->
    <MobileSignatureDialog
      v-model:visible="mobileSignatureDialogVisible"
      :source="source"
      @complete="handleSignatureComplete"
    />
  </div>
</template>

<style scoped>
.signature-pad {
  width: 100%;
}

.signature-pad__trigger {
  position: relative;
  border: 2px dashed var(--el-border-color);
  border-radius: 8px;
  background-color: var(--el-fill-color-lighter);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
}

.signature-pad__trigger:hover {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.signature-pad__trigger--disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.signature-pad__trigger--disabled:hover {
  border-color: var(--el-border-color);
  background-color: var(--el-fill-color-lighter);
}

.signature-pad__placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-placeholder);
  pointer-events: none;
  user-select: none;
}

.signature-pad__placeholder-icon {
  width: 30px;
  height: 30px;
  opacity: 0.5;
}

.signature-pad__actions {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  gap: 12px;
}

.signature-pad__preview {
  position: relative;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background-color: var(--el-fill-color-lighter);
  overflow: hidden;
}

.signature-pad__image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.signature-pad__overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.4);
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
