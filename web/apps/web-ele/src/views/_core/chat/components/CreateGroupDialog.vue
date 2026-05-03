<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { ElButton, ElForm, ElFormItem, ElInput } from 'element-plus';

import { ZqDialog } from '#/components/zq-dialog';
import { UserSelector } from '#/components/zq-form/user-selector';

const emit = defineEmits<{
  confirm: [name: string, memberIds: string[]];
}>();

const visible = defineModel<boolean>({ default: false });

const formRef = ref<FormInstance>();
const loading = ref(false);
const formData = ref({
  name: '',
  member_ids: [] as string[],
});

const rules = computed<FormRules>(() => ({
  name: [
    { required: true, message: $t('chat.groupNameRequired'), trigger: 'blur' },
  ],
  member_ids: [
    { required: true, message: $t('chat.membersRequired'), trigger: 'change' },
  ],
}));

function handleOpen() {
  formData.value = { name: '', member_ids: [] };
}

async function handleConfirm() {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
  } catch {
    return;
  }
  loading.value = true;
  try {
    emit('confirm', formData.value.name, formData.value.member_ids);
    visible.value = false;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="$t('chat.newGroup')"
    width="500px"
    @open="handleOpen"
  >
    <ElForm
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="90px"
      label-position="left"
    >
      <ElFormItem :label="$t('chat.groupName')" prop="name">
        <ElInput
          v-model="formData.name"
          :placeholder="$t('chat.groupNamePlaceholder')"
          maxlength="100"
          show-word-limit
        />
      </ElFormItem>
      <ElFormItem :label="$t('chat.selectMembers')" prop="member_ids">
        <UserSelector
          v-model="formData.member_ids"
          multiple
          :placeholder="$t('chat.selectMembersPlaceholder')"
        />
      </ElFormItem>
    </ElForm>
    <template #footer>
      <ElButton @click="visible = false">{{ $t('common.cancel') }}</ElButton>
      <ElButton type="primary" :loading="loading" @click="handleConfirm">
        {{ $t('common.confirm') }}
      </ElButton>
    </template>
  </ZqDialog>
</template>
