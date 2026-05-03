<script lang="ts" setup>
import { computed, ref } from 'vue';

import { ZqDialog } from '#/components/zq-dialog';

import CronInner from './cron-inner.vue';

interface Props {
  modelValue?: string;
  disabled?: boolean;
  hideSecond?: boolean;
  hideYear?: boolean;
  remote?: (
    cron: string,
    timestamp: number,
    callback: (result: string) => void,
  ) => void;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  disabled: false,
  hideSecond: true,
  hideYear: true,
});

const emit = defineEmits(['update:modelValue', 'ok']);

const visible = ref(false);
const innerValue = ref(props.modelValue);

const attrs = computed(() => ({
  modelValue: innerValue.value,
  disabled: props.disabled,
  hideSecond: props.hideSecond,
  hideYear: props.hideYear,
  remote: props.remote,
}));

function openModal() {
  visible.value = true;
  innerValue.value = props.modelValue;
}

function handleCancel() {
  visible.value = false;
}

function handleSubmit() {
  emit('update:modelValue', innerValue.value);
  handleCancel();
  emit('ok');
}

function handleCronChange(value: string) {
  innerValue.value = value;
}

defineExpose({
  openModal,
});
</script>

<template>
  <ZqDialog
    v-model="visible"
    title="Cron表达式"
    width="50%"
    @cancel="handleCancel"
    @confirm="handleSubmit"
  >
    <CronInner v-bind="attrs" @change="handleCronChange" />
  </ZqDialog>
</template>
