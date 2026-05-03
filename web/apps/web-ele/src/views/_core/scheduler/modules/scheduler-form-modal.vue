<script lang="ts" setup>
import type { SchedulerJob } from '#/api/core/scheduler';

import { computed, ref, watch } from 'vue';

import { useVbenForm } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import {
  createSchedulerJobApi,
  updateSchedulerJobApi,
} from '#/api/core/scheduler';
import { ZqDialog } from '#/components/zq-dialog';
import { useAppContextStore } from '#/store/app-context';

import { useJobFormSchema } from '../data';

const emit = defineEmits(['success']);

const appContextStore = useAppContextStore();

const formData = ref<SchedulerJob>();
const triggerType = ref<'cron' | 'date' | 'interval'>('cron');
const visible = ref(false);
const confirmLoading = ref(false);

const getTitle = computed(() => {
  return formData.value?.id
    ? $t('scheduler.editJob')
    : $t('scheduler.createJob');
});

// 根据当前的 trigger_type 动态生成表单配置
const formSchema = computed(() => useJobFormSchema() as any);

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: formSchema as any,
  showDefaultActions: false,
});

function resetForm() {
  formApi.resetForm();
  formApi.setValues(formData.value || {});
}

/**
 * 处理触发器类型变更
 */
function handleTriggerTypeChange(value: string) {
  triggerType.value = value as 'cron' | 'date' | 'interval';
}

async function onSubmit() {
  const { valid } = await formApi.validate();
  if (valid) {
    confirmLoading.value = true;
    const data = await formApi.getValues();
    try {
      if (!formData.value?.id) {
        data.application_id = appContextStore.currentApp?.id;
      }
      await (formData.value?.id
        ? updateSchedulerJobApi(formData.value.id, data as any)
        : createSchedulerJobApi(data as any));
      visible.value = false;
      emit('success');
    } finally {
      confirmLoading.value = false;
    }
  }
}

function open(data?: SchedulerJob) {
  visible.value = true;
  if (data) {
    formData.value = data;
    triggerType.value = data.trigger_type;
    formApi.setValues(formData.value);
  } else {
    formData.value = undefined;
    triggerType.value = 'cron';
    formApi.resetForm();
  }
}

defineExpose({
  open,
});

// 监听trigger_type变更时重新渲染表单
watch(
  () => triggerType.value,
  () => {
    // 触发表单重新渲染
  },
);
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="getTitle"
    :confirm-loading="confirmLoading"
    width="800px"
    @confirm="onSubmit"
  >
    <Form class="mx-4" @trigger-type-change="handleTriggerTypeChange" />
    <template #footer-left>
      <ElButton @click="resetForm">
        {{ $t('common.reset') || '重置' }}
      </ElButton>
    </template>
  </ZqDialog>
</template>
