<script lang="ts" setup>
import type { Post } from '#/api/core/post';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import { useVbenForm } from '#/adapter/form';
import { createPostApi, updatePostApi } from '#/api/core/post';
import { ZqDialog } from '#/components/zq-dialog';

import { useFormSchema } from '../data';

const emit = defineEmits(['success']);
const formData = ref<Post>();
const visible = ref(false);
const confirmLoading = ref(false);
const getTitle = computed(() => {
  return formData.value?.id
    ? $t('ui.actionTitle.edit', [$t('post.name')])
    : $t('ui.actionTitle.create', [$t('post.name')]);
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
        ? updatePostApi(formData.value.id, data)
        : createPostApi(data));
      visible.value = false;
      emit('success');
    } finally {
      confirmLoading.value = false;
    }
  }
}

function open(data?: Post) {
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
