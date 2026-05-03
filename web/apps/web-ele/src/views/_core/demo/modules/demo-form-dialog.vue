<script lang="ts" setup>
import type { Demo } from '#/api/core/demo';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import { useVbenForm, z } from '#/adapter/form';
import { createDemoApi, updateDemoApi } from '#/api/core/demo';
import { ZqDialog } from '#/components/zq-dialog';

const emit = defineEmits(['success']);
const formData = ref<Demo>();
const visible = ref(false);
const confirmLoading = ref(false);

const getTitle = computed(() => {
  return formData.value?.id ? $t('demos.demo.edit') : $t('demos.demo.create');
});

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: [
    {
      component: 'Input',
      fieldName: 'title',
      label: $t('demos.demo.title'),
      rules: z
        .string()
        .min(1, $t('ui.formRules.required', [$t('demos.demo.title')]))
        .max(100, $t('ui.formRules.maxLength', [$t('demos.demo.title'), 100])),
    },
    {
      component: 'Textarea',
      componentProps: {
        placeholder: $t('demos.demo.contentPlaceholder'),
        rows: 4,
      },
      fieldName: 'content',
      label: $t('demos.demo.content'),
    },
    {
      component: 'Select',
      componentProps: {
        options: [
          { label: $t('demos.demo.statusDraft'), value: 0 },
          { label: $t('demos.demo.statusPublished'), value: 1 },
          { label: $t('demos.demo.statusArchived'), value: 2 },
        ],
      },
      defaultValue: 1,
      fieldName: 'status',
      label: $t('demos.demo.status'),
      rules: z.number(),
    },
    {
      component: 'Select',
      componentProps: {
        options: [
          { label: $t('demos.demo.priorityLow'), value: 0 },
          { label: $t('demos.demo.priorityMedium'), value: 1 },
          { label: $t('demos.demo.priorityHigh'), value: 2 },
        ],
      },
      defaultValue: 0,
      fieldName: 'priority',
      label: $t('demos.demo.priority'),
      rules: z.number(),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        options: [
          { label: $t('common.enabled'), value: true },
          { label: $t('common.disabled'), value: false },
        ],
      },
      defaultValue: true,
      fieldName: 'is_active',
      label: $t('demos.demo.isActive'),
    },
  ],
  showDefaultActions: false,
});

function resetForm() {
  formApi.resetForm();
  formApi.setValues(formData.value || {});
}

async function onSubmit() {
  const { valid } = await formApi.validate();
  if (valid) {
    confirmLoading.value = true;
    const data = await formApi.getValues();
    try {
      await (formData.value?.id
        ? updateDemoApi(formData.value.id, data)
        : createDemoApi(data));
      visible.value = false;
      emit('success');
    } finally {
      confirmLoading.value = false;
    }
  }
}

function open(data?: Demo) {
  visible.value = true;
  if (data) {
    formData.value = data;
    formApi.setValues(formData.value);
  } else {
    formData.value = undefined;
    formApi.resetForm();
  }
}

defineExpose({
  open,
});
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="getTitle"
    :confirm-loading="confirmLoading"
    @confirm="onSubmit"
  >
    <Form class="mx-4" />
    <template #footer-left>
      <ElButton type="primary" @click="resetForm">
        {{ $t('common.reset') }}
      </ElButton>
    </template>
  </ZqDialog>
</template>
