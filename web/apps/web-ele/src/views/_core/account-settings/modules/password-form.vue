<script lang="ts" setup>
import type { UserChangePasswordInput } from '#/api/core';

import { reactive, ref } from 'vue';

import { $t } from '@vben/locales';

import { ElButton, ElForm, ElFormItem, ElInput, ElMessage } from 'element-plus';

import { changePasswordApi } from '#/api/core';

defineOptions({ name: 'PasswordForm' });

const emit = defineEmits<{
  success: [];
}>();

const loading = ref(false);

// 密码修改表单数据
const passwordForm = reactive<UserChangePasswordInput>({
  old_password: '',
  new_password: '',
  confirm_password: '',
});

// 表单引用
const passwordFormRef = ref<InstanceType<typeof ElForm>>();

// 表单验证规则
const passwordRules = {
  old_password: [
    {
      required: true,
      message: $t('ui.formRules.required', [$t('user.oldPassword')]),
      trigger: 'blur',
    },
  ],
  new_password: [
    {
      required: true,
      message: $t('ui.formRules.required', [$t('user.newPassword')]),
      trigger: 'blur',
    },
    {
      min: 6,
      max: 20,
      message: `${$t('ui.formRules.minLength', [
        $t('user.newPassword'),
        6,
      ])}，${$t('ui.formRules.maxLength', [$t('user.newPassword'), 20])}`,
      trigger: 'blur',
    },
  ],
  confirm_password: [
    {
      required: true,
      message: $t('ui.formRules.required', [$t('user.confirmPassword')]),
      trigger: 'blur',
    },
    {
      validator: (_rule: any, value: string, callback: Function) => {
        if (value === passwordForm.new_password) {
          callback();
        } else {
          callback(new Error($t('user.passwordNotMatch')));
        }
      },
      trigger: 'blur',
    },
  ],
};

/**
 * 修改密码
 */
async function handleChangePassword() {
  if (!passwordFormRef.value) return;

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return;

    // 验证新密码和确认密码是否一致
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      ElMessage.error($t('user.passwordNotMatch'));
      return;
    }

    loading.value = true;
    try {
      await changePasswordApi({ ...passwordForm });
      ElMessage.success($t('user.changePasswordSuccess'));
      // 清空表单
      Object.assign(passwordForm, {
        old_password: '',
        new_password: '',
        confirm_password: '',
      });
      passwordFormRef.value?.resetFields();
      emit('success');
    } catch (error: any) {
      ElMessage.error(error?.message || $t('user.changePasswordError'));
    } finally {
      loading.value = false;
    }
  });
}

/**
 * 重置表单
 */
function handleReset() {
  passwordFormRef.value?.resetFields();
}
</script>

<template>
  <ElForm
    ref="passwordFormRef"
    :model="passwordForm"
    :rules="passwordRules"
    label-width="120px"
    label-position="right"
  >
    <ElFormItem :label="$t('user.oldPassword')" prop="old_password">
      <ElInput
        v-model="passwordForm.old_password"
        type="password"
        :placeholder="$t('user.oldPasswordPlaceholder')"
        show-password
        clearable
      />
    </ElFormItem>

    <ElFormItem :label="$t('user.newPassword')" prop="new_password">
      <ElInput
        v-model="passwordForm.new_password"
        type="password"
        :placeholder="$t('user.newPasswordPlaceholder')"
        show-password
        clearable
      />
      <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
        {{ $t('account-settings.passwordLengthHint') }}
      </p>
    </ElFormItem>

    <ElFormItem :label="$t('user.confirmPassword')" prop="confirm_password">
      <ElInput
        v-model="passwordForm.confirm_password"
        type="password"
        :placeholder="$t('user.confirmPasswordPlaceholder')"
        show-password
        clearable
      />
    </ElFormItem>

    <!-- 保存按钮 -->
    <ElFormItem>
      <ElButton type="primary" :loading="loading" @click="handleChangePassword">
        {{ $t('common.save') }}
      </ElButton>
      <ElButton @click="handleReset">
        {{ $t('common.reset') }}
      </ElButton>
    </ElFormItem>
  </ElForm>
</template>
