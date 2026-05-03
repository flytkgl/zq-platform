<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus';

import { computed, ref } from 'vue';

import { $t } from '@vben/locales';

import { ElButton, ElForm, ElFormItem, ElMessage } from 'element-plus';

import { ZqDialog } from '#/components/zq-dialog';
import { UserSelector } from '#/components/zq-form/user-selector';

const props = defineProps<{
  existingMemberIds?: string[];
}>();

const emit = defineEmits<{
  confirm: [memberIds: string[]];
}>();

const visible = defineModel<boolean>({ default: false });

const formRef = ref<FormInstance>();
const loading = ref(false);
const formData = ref({
  member_ids: [] as string[],
});

const rules = computed<FormRules>(() => ({
  member_ids: [
    { required: true, message: $t('chat.membersRequired'), trigger: 'change' },
  ],
}));

function handleOpen() {
  formData.value = { member_ids: [] };
}

async function handleConfirm() {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
  } catch {
    return;
  }
  // 过滤掉已有成员
  const newIds = formData.value.member_ids.filter(
    (id) => !props.existingMemberIds?.includes(id),
  );
  if (newIds.length === 0) {
    ElMessage.warning($t('chat.allMembersExist'));
    return;
  }
  loading.value = true;
  try {
    emit('confirm', newIds);
    visible.value = false;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="$t('chat.addMember')"
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
