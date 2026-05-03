<script lang="ts" setup>
import type { Dict } from '#/api/core/dict';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { ElButton, ElSwitch } from 'element-plus';

import { useVbenForm } from '#/adapter/form';
import { createDictApi, updateDictApi } from '#/api/core/dict';
import { ZqDialog } from '#/components/zq-dialog';
import { useAppContextStore } from '#/store/app-context';

import { useDictFormSchema } from '../data';

const emit = defineEmits(['success']);
const appContextStore = useAppContextStore();
const isGlobal = ref(false);

const formData = ref<Dict>();
const visible = ref(false);
const confirmLoading = ref(false);
const getTitle = computed(() => {
  return formData.value?.id
    ? $t('ui.actionTitle.edit', [$t('dict.name')])
    : $t('ui.actionTitle.create', [$t('dict.name')]);
});

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: useDictFormSchema(),
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
      if (!formData.value?.id) {
        data.application_id = appContextStore.currentApp?.id;
      }
      data.is_global = isGlobal.value;
      await (formData.value?.id
        ? updateDictApi(formData.value.id, data)
        : createDictApi(data));
      visible.value = false;
      emit('success');
    } finally {
      confirmLoading.value = false;
    }
  }
}

function open(data?: Dict) {
  visible.value = true;
  if (data) {
    formData.value = data;
    isGlobal.value = data.is_global ?? false;
    formApi.setValues(formData.value);
  } else {
    formData.value = undefined;
    isGlobal.value = false;
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
    width="500px"
  >
    <Form class="mx-4" />
    <div class="mx-4 mb-2 flex items-center gap-2">
      <span class="text-sm">{{ $t('dict.isGlobal') }}</span>
      <ElSwitch v-model="isGlobal" />
    </div>
    <template #footer-left>
      <ElButton type="primary" @click="resetForm">
        {{ $t('common.reset') }}
      </ElButton>
    </template>
  </ZqDialog>
</template>
