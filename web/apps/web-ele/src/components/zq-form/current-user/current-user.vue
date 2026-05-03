<script lang="ts" setup>
import type { CurrentUserEmits, CurrentUserProps } from './types';

import { computed, onMounted, ref, watch } from 'vue';

import { useUserStore } from '@vben/stores';

import { ElInput } from 'element-plus';

defineOptions({
  name: 'CurrentUser',
});

const props = withDefaults(defineProps<CurrentUserProps>(), {
  displayField: 'nickname',
  valueField: 'realName',
  showAvatar: false,
  disabled: true,
  placeholder: '当前用户',
  fillMode: 'onCreate',
});

const emit = defineEmits<CurrentUserEmits>();

const userStore = useUserStore();
const displayText = ref('');
const internalValue = ref('');

const userInfo = computed(() => userStore.userInfo);

const getDisplayText = () => {
  if (!userInfo.value) return '';

  switch (props.displayField) {
    case 'name':
    case 'nickname': {
      return userInfo.value.realName || userInfo.value.username || '';
    }
    case 'username': {
      return userInfo.value.username || '';
    }
    default: {
      return userInfo.value.realName || userInfo.value.username || '';
    }
  }
};

const getValue = () => {
  if (!userInfo.value) return '';

  switch (props.valueField) {
    case 'realName': {
      return userInfo.value.realName || userInfo.value.username || '';
    }
    case 'username': {
      return userInfo.value.username || '';
    }
    case 'id':
    default: {
      return userInfo.value.userId || '';
    }
  }
};

const updateValue = (force = false) => {
  const value = getValue();
  displayText.value = getDisplayText();
  internalValue.value = value;

  // 根据 fillMode 决定是否更新值
  // onCreate: 仅在值为空时填充
  // always: 始终填充
  if (value) {
    if (force || props.fillMode === 'always') {
      emit('update:modelValue', value);
      emit('change', value);
    } else if (props.fillMode === 'onCreate' && !props.modelValue) {
      emit('update:modelValue', value);
      emit('change', value);
    }
  }
};

// 如果已有值且是 onCreate 模式，保持显示
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && props.fillMode === 'onCreate') {
      // 已有值时，显示已有值（可能是其他用户）
      displayText.value = newVal;
    }
  },
  { immediate: true },
);

watch(
  userInfo,
  () => {
    if (props.fillMode === 'always' || !props.modelValue) {
      updateValue();
    }
  },
  { immediate: true },
);

onMounted(() => {
  // onCreate 模式下，只有值为空时才填充
  if (props.fillMode === 'onCreate') {
    if (!props.modelValue) {
      updateValue(true);
    }
  } else {
    updateValue(true);
  }
});
</script>

<template>
  <div class="current-user-wrapper flex w-full items-center gap-2">
    <ElInput
      v-model="displayText"
      :placeholder="placeholder"
      :disabled="true"
      readonly
      class="current-user-input w-full"
    >
      <template v-if="showAvatar && userInfo?.avatar" #prefix>
        <img
          :src="userInfo.avatar"
          alt="avatar"
          class="h-5 w-5 rounded-full object-cover"
        />
      </template>
    </ElInput>
  </div>
</template>

<style scoped>
.current-user-input :deep(.el-input__inner) {
  cursor: default;
}
</style>
