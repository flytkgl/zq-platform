<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { CircleStencil, Cropper } from 'vue-advanced-cropper';
import 'vue-advanced-cropper/dist/style.css';

import { IconifyIcon } from '@vben/icons';

import { ElButton, ElDialog } from 'element-plus';

interface ImageCropperProps {
  modelValue: boolean;
  imageSrc: string;
  aspectRatio?: number; // 宽高比，例如 16/9, 4/3, 1 (正方形), undefined (自由裁剪)
  shape?: 'circle' | 'rect'; // 裁剪形状
}

interface ImageCropperEmits {
  (e: 'update:modelValue', value: boolean): void;
  (e: 'confirm', result: { blob: Blob; canvas: HTMLCanvasElement }): void;
}

const props = withDefaults(defineProps<ImageCropperProps>(), {
  aspectRatio: undefined,
  shape: 'rect',
});

const emit = defineEmits<ImageCropperEmits>();

const visible = ref(false);
const cropperRef = ref<InstanceType<typeof Cropper>>();

// 计算裁剪组件类型
const stencilComponent = computed(() => {
  return props.shape === 'circle' ? CircleStencil : undefined;
});

// 计算裁剪组件属性
const stencilProps = computed(() => {
  const baseProps: any = {};

  // 圆形裁剪时，aspectRatio 必须为 1
  if (props.shape === 'circle') {
    baseProps.aspectRatio = 1;
  } else if (props.aspectRatio !== undefined) {
    baseProps.aspectRatio = props.aspectRatio;
  }

  return baseProps;
});

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  (newVal) => {
    visible.value = newVal;
  },
  { immediate: true },
);

// 监听 visible 变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal);
});

// 向左旋转 90 度
function handleRotateLeft() {
  cropperRef.value?.rotate(-90);
}

// 向右旋转 90 度
function handleRotateRight() {
  cropperRef.value?.rotate(90);
}

// 水平翻转
function handleFlipHorizontal() {
  cropperRef.value?.flip(true, false);
}

// 垂直翻转
function handleFlipVertical() {
  cropperRef.value?.flip(false, true);
}

// 重置
function handleReset() {
  cropperRef.value?.reset();
}

// 取消
function handleCancel() {
  visible.value = false;
}

// 关闭
function handleClose() {
  visible.value = false;
}

// 确认裁剪
async function handleConfirm() {
  const result = cropperRef.value?.getResult();
  if (!result) {
    return;
  }

  const canvas = result.canvas;
  if (!canvas) {
    return;
  }

  // 将 canvas 转换为 Blob
  canvas.toBlob((blob) => {
    if (blob) {
      emit('confirm', { canvas, blob });
      visible.value = false;
    }
  }, 'image/png');
}
</script>

<template>
  <ElDialog
    v-model="visible"
    title="裁剪图片"
    width="800px"
    :close-on-click-modal="false"
    append-to-body
    @close="handleClose"
  >
    <div class="image-cropper-container">
      <Cropper
        ref="cropperRef"
        :src="imageSrc"
        :stencil-component="stencilComponent"
        :stencil-props="stencilProps"
        class="cropper"
      />
    </div>

    <template #footer>
      <div class="cropper-footer">
        <div class="cropper-actions">
          <ElButton @click="handleRotateLeft">
            <IconifyIcon icon="i-carbon:rotate-counterclockwise" class="mr-1" />
            向左旋转
          </ElButton>
          <ElButton @click="handleRotateRight">
            <IconifyIcon icon="i-carbon:rotate-clockwise" class="mr-1" />
            向右旋转
          </ElButton>
          <ElButton @click="handleFlipHorizontal">
            <IconifyIcon icon="i-carbon:arrows-horizontal" class="mr-1" />
            水平翻转
          </ElButton>
          <ElButton @click="handleFlipVertical">
            <IconifyIcon icon="i-carbon:arrows-vertical" class="mr-1" />
            垂直翻转
          </ElButton>
          <ElButton @click="handleReset">
            <IconifyIcon icon="i-carbon:reset" class="mr-1" />
            重置
          </ElButton>
        </div>

        <div class="cropper-confirm">
          <ElButton @click="handleCancel">取消</ElButton>
          <ElButton type="primary" @click="handleConfirm">确认裁剪</ElButton>
        </div>
      </div>
    </template>
  </ElDialog>
</template>

<style scoped lang="scss">
.image-cropper-container {
  width: 100%;
  height: 500px;
  background: hsl(var(--muted));

  .cropper {
    width: 100%;
    height: 100%;
  }
}

.cropper-footer {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .cropper-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }

  .cropper-confirm {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }
}
</style>
