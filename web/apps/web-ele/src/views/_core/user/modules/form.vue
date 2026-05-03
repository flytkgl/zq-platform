<script lang="ts" setup>
import type { User } from '#/api/core';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { useVbenForm } from '#/adapter/form';
import { createUserApi, updateUserApi } from '#/api/core';
import { ZqDrawer } from '#/components/zq-drawer';

import { getFormSchema } from '../data';

const emit = defineEmits<{
  success: [];
}>();

const formData = ref<User>();
const visible = ref(false);
const confirmLoading = ref(false);

const [Form, formApi] = useVbenForm({
  commonConfig: {
    colon: true,
    componentProps: {
      class: 'w-full',
    },
  },
  schema: getFormSchema(),
  showDefaultActions: false,
  wrapperClass: 'grid-cols-1 gap-x-4',
});

async function open(data?: User) {
  visible.value = true;
  // 先重置表单，确保从默认值开始
  await formApi.resetForm();
  if (data) {
    formData.value = data;
    // 使用 filterFields: false 确保所有字段都被设置
    await formApi.setValues(formData.value, false);
  } else {
    formData.value = undefined;
  }
}

defineExpose({
  open,
});

const getDrawerTitle = computed(() =>
  formData.value?.id
    ? $t('ui.actionTitle.edit', [$t('user.name')])
    : $t('ui.actionTitle.create', [$t('user.name')]),
);

async function onSubmit() {
  const { valid } = await formApi.validate();
  if (valid) {
    confirmLoading.value = true;
    const data = await formApi.getValues<Omit<User, 'id'>>();
    try {
      await (formData.value?.id
        ? updateUserApi(formData.value.id, data)
        : createUserApi(data));
      visible.value = false;
      emit('success');
    } finally {
      confirmLoading.value = false;
    }
  }
}
</script>

<template>
  <ZqDrawer
    v-model="visible"
    :title="getDrawerTitle"
    :confirm-loading="confirmLoading"
    size="700px"
    @confirm="onSubmit"
  >
    <Form class="mx-4" />
  </ZqDrawer>
</template>
