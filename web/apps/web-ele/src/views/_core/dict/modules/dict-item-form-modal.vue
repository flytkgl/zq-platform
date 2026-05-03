<script lang="ts" setup>
import type { DictItem } from '#/api/core/dict';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import { useVbenForm } from '#/adapter/form';
import { createDictItemApi, updateDictItemApi } from '#/api/core/dict';
import { ZqDialog } from '#/components/zq-dialog';

import { useDictItemFormSchema } from '../data';

const emit = defineEmits(['success']);
const formData = ref<DictItem>();
const dictId = ref<string>();
const visible = ref(false);
const confirmLoading = ref(false);

const getTitle = computed(() => {
  return formData.value?.id
    ? $t('ui.actionTitle.edit', [$t('dict.itemName')])
    : $t('ui.actionTitle.create', [$t('dict.itemName')]);
});

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: useDictItemFormSchema(),
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
      const payload = {
        ...data,
        dict_id: dictId.value,
      };
      await (formData.value?.id
        ? updateDictItemApi(formData.value.id, payload)
        : createDictItemApi(payload));
      visible.value = false;
      emit('success');
    } finally {
      confirmLoading.value = false;
    }
  }
}

function open(data?: any) {
  visible.value = true;
  if (data?.id) {
    formData.value = data;
    dictId.value = data.dict_id;
    formApi.setValues(formData.value);
  } else {
    formData.value = undefined;
    dictId.value = data?.dictId;
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
