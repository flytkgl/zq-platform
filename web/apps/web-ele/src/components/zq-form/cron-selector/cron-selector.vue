<script lang="ts" setup>
import type { CronSelectorEmits, CronSelectorProps } from './types';

import { computed, ref, watch } from 'vue';

import { EditOutlined } from '@vben/icons';

import { ElButton, ElInput } from 'element-plus';

import CronModal from './cron-modal.vue';

interface Props extends CronSelectorProps {
  placeholder?: string;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  disabled: false,
  hideSecond: true,
  hideYear: true,
  placeholder: 'Cron表达式',
});

const emit = defineEmits<CronSelectorEmits>();

const value = computed({
  get: () => props.modelValue || '',
  set: (val) => {
    emit('update:modelValue', val);
  },
});

const editCronValue = ref(props.modelValue || '');
const cronModalRef = ref();

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal !== editCronValue.value) {
      editCronValue.value = newVal || '';
    }
  },
);

function showConfigModal() {
  if (props.disabled) return;
  cronModalRef.value?.openModal();
}

function handleCronModalUpdate(newValue: string) {
  editCronValue.value = newValue;
}

function handleSubmit() {
  emit('change', editCronValue.value);
  emit('update:modelValue', editCronValue.value);
}
</script>

<template>
  <div class="cron-selector">
    <ElInput
      v-model="value"
      :placeholder="placeholder"
      readonly
      :disabled="disabled"
      clearable
    >
      <template #suffix>
        <ElButton
          link
          :icon="EditOutlined"
          @click="showConfigModal"
          :disabled="disabled"
        />
      </template>
    </ElInput>
    <CronModal
      ref="cronModalRef"
      v-model="editCronValue"
      :disabled="disabled"
      :hide-year="hideYear"
      :hide-second="hideSecond"
      :remote="remote"
      @update:model-value="handleCronModalUpdate"
      @ok="handleSubmit"
    />
  </div>
</template>

<style scoped lang="css">
.cron-selector {
  width: 100%;
}
</style>
