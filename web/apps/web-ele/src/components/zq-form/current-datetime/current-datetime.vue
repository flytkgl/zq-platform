<script lang="ts" setup>
import type { CurrentDatetimeEmits, CurrentDatetimeProps } from './types';

import { computed, onMounted, onUnmounted, ref, watch } from 'vue';

import dayjs from 'dayjs';
import { ElInput } from 'element-plus';

defineOptions({
  name: 'CurrentDatetime',
});

const props = withDefaults(defineProps<CurrentDatetimeProps>(), {
  type: 'datetime',
  disabled: true,
  placeholder: '当前时间',
  autoUpdate: false,
  fillMode: 'onCreate',
});

const emit = defineEmits<CurrentDatetimeEmits>();

const displayText = ref('');
let timer: null | ReturnType<typeof setInterval> = null;

const displayFormat = computed(() => {
  if (props.format) return props.format;

  switch (props.type) {
    case 'date': {
      return 'YYYY-MM-DD';
    }
    case 'time': {
      return 'HH:mm:ss';
    }
    case 'datetime':
    default: {
      return 'YYYY-MM-DD HH:mm:ss';
    }
  }
});

const valueFormatComputed = computed(() => {
  if (props.valueFormat) return props.valueFormat;
  return displayFormat.value;
});

const updateValue = (force = false) => {
  const now = dayjs();
  const formattedDisplay = now.format(displayFormat.value);
  const formattedValue = now.format(valueFormatComputed.value);

  displayText.value = formattedDisplay;

  // 根据 fillMode 决定是否更新值
  // onCreate: 仅在值为空时填充（创建时间）
  // onUpdate: 每次都更新（更新时间）
  // always: 始终更新
  if (force || props.fillMode === 'onUpdate' || props.fillMode === 'always') {
    emit('update:modelValue', formattedValue);
    emit('change', formattedValue);
  } else if (props.fillMode === 'onCreate' && !props.modelValue) {
    emit('update:modelValue', formattedValue);
    emit('change', formattedValue);
  }
};

// 如果已有值，显示已有值
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && props.fillMode === 'onCreate') {
      displayText.value = dayjs(newVal).format(displayFormat.value);
    }
  },
  { immediate: true },
);

watch(
  () => props.type,
  () => {
    if (props.fillMode !== 'onCreate' || !props.modelValue) {
      updateValue();
    }
  },
);

onMounted(() => {
  // onCreate 模式下，只有值为空时才填充
  if (props.fillMode === 'onCreate') {
    if (props.modelValue) {
      displayText.value = dayjs(props.modelValue).format(displayFormat.value);
    } else {
      updateValue(true);
    }
  } else {
    // onUpdate 或 always 模式，始终更新
    updateValue(true);
  }

  if (props.autoUpdate) {
    timer = setInterval(() => {
      updateValue();
    }, 1000);
  }
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
});
</script>

<template>
  <div class="current-datetime-wrapper w-full">
    <ElInput
      v-model="displayText"
      :placeholder="placeholder"
      :disabled="true"
      readonly
      class="current-datetime-input w-full"
    />
  </div>
</template>

<style scoped>
.current-datetime-input :deep(.el-input__inner) {
  cursor: default;
}
</style>
