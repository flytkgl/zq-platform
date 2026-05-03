<script lang="ts" setup>
import type { Permission, PermissionCreateInput } from '#/api/core/permission';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import { useVbenForm } from '#/adapter/form';
import {
  createPermissionApi,
  updatePermissionApi,
} from '#/api/core/permission';
import { ZqDialog } from '#/components/zq-dialog';

import { getFormSchema } from '../data';

const emit = defineEmits(['success']);
const permissionData = ref<Permission>();
const currentMenuId = ref<string>('');
const visible = ref(false);
const confirmLoading = ref(false);

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: getFormSchema(),
  showDefaultActions: false,
});

const getTitle = computed(() => {
  return permissionData.value?.id
    ? $t('permission.edit')
    : $t('permission.add');
});

async function onSubmit() {
  const { valid } = await formApi.validate();
  if (valid) {
    confirmLoading.value = true;
    try {
      const formData = await formApi.getValues<any>();

      const submitData: PermissionCreateInput = {
        ...formData,
        menu_id: currentMenuId.value,
      };

      await (permissionData.value?.id
        ? updatePermissionApi(permissionData.value.id, submitData)
        : createPermissionApi(submitData));

      visible.value = false;
      emit('success');
    } finally {
      confirmLoading.value = false;
    }
  }
}

function open(data?: Permission) {
  visible.value = true;
  if (data) {
    permissionData.value = data;
    currentMenuId.value = data.menu_id;
    formApi.setValues(data);
  } else {
    permissionData.value = undefined;
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
    content-height="600px"
    @confirm="onSubmit"
  >
    <Form class="mx-4" />
    <template #footer-left>
      <ElButton type="default" @click="() => formApi.resetForm()">
        {{ $t('common.reset') }}
      </ElButton>
    </template>
  </ZqDialog>
</template>
