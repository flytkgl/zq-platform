<script lang="ts" setup>
import type { Role } from '#/api/core/role';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import { useVbenForm } from '#/adapter/form';
import { createRoleApi, updateRoleApi } from '#/api/core/role';
import { ZqDialog } from '#/components/zq-dialog';

import { useFormSchema } from '../data';

const emit = defineEmits(['success']);
const formData = ref<Role>();
const visible = ref(false);
const confirmLoading = ref(false);
const getTitle = computed(() => {
  return formData.value?.id
    ? $t('ui.actionTitle.edit', [$t('role.name')])
    : $t('ui.actionTitle.create', [$t('role.name')]);
});

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: useFormSchema(),
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
        ? updateRoleApi(formData.value.id, data)
        : createRoleApi(data));
      visible.value = false;
      emit('success');
    } finally {
      confirmLoading.value = false;
    }
  }
}

function open(data?: Role) {
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
