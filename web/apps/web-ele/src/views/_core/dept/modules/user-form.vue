<script lang="ts" setup>
import type { VbenFormSchema } from '#/adapter/form';
import type { DeptUser } from '#/api/core/dept';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { useVbenForm } from '#/adapter/form';
import { ZqDialog } from '#/components/zq-dialog';

const emit = defineEmits<{ success: [] }>();
const userData = ref<DeptUser>();
const visible = ref(false);
const formSchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'username',
    label: $t('system.user.account'),
    componentProps: { disabled: true },
  },
  {
    component: 'Input',
    fieldName: 'name',
    label: $t('system.user.userName'),
    componentProps: { disabled: true },
  },
  {
    component: 'Input',
    fieldName: 'email',
    label: $t('system.user.email'),
    componentProps: { disabled: true },
  },
  {
    component: 'Input',
    fieldName: 'mobile',
    label: $t('system.user.mobile'),
    componentProps: { disabled: true },
  },
];

const [Form, formApi] = useVbenForm({
  layout: 'vertical',
  schema: formSchema,
  showDefaultActions: false,
});

const getModalTitle = computed(() =>
  $t('ui.actionTitle.view', [$t('system.user.name')]),
);

function onConfirm() {
  visible.value = false;
  emit('success');
}

function open(data: DeptUser) {
  visible.value = true;
  userData.value = data;
  formApi.setValues(userData.value);
}

defineExpose({
  open,
});
</script>

<template>
  <ZqDialog v-model="visible" :title="getModalTitle" @confirm="onConfirm">
    <Form class="mx-4" />
  </ZqDialog>
</template>
