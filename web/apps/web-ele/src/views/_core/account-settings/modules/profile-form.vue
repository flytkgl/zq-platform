<script lang="ts" setup>
import type { User, UserProfileUpdateInput } from '#/api/core';

import { reactive, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import {
  ElButton,
  ElDatePicker,
  ElDivider,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElRadio,
  ElRadioGroup,
} from 'element-plus';

import { patchUserProfileApi } from '#/api/core';
import { ImageSelector } from '#/components/zq-form/image-selector';

defineOptions({ name: 'ProfileForm' });

const props = withDefaults(defineProps<Props>(), {
  userProfile: null,
});

const emit = defineEmits<{
  success: [];
}>();

interface Props {
  userProfile?: null | User;
}

const loading = ref(false);

// 基本信息表单数据
const profileForm = reactive<UserProfileUpdateInput>({
  name: '',
  email: '',
  mobile: '',
  avatar: '',
  gender: 0,
  birthday: '',
  city: '',
  address: '',
  bio: '',
});

// 表单引用
const profileFormRef = ref<InstanceType<typeof ElForm>>();

// 性别选项
const genderOptions = [
  { label: $t('user.unknown'), value: 0 },
  { label: $t('user.male'), value: 1 },
  { label: $t('user.female'), value: 2 },
];

// 表单验证规则
const profileRules = {
  name: [
    {
      min: 2,
      max: 64,
      message: `${$t('ui.formRules.minLength', [$t('user.userName'), 2])}，${$t(
        'ui.formRules.maxLength',
        [$t('user.userName'), 64],
      )}`,
      trigger: 'blur',
    },
  ],
  email: [
    {
      type: 'email' as const,
      message: $t('user.emailFormatError'),
      trigger: 'blur',
    },
  ],
  mobile: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: $t('user.mobileFormatError'),
      trigger: 'blur',
    },
  ],
};

/**
 * 加载用户信息
 */
function loadUserProfile() {
  if (props.userProfile) {
    Object.assign(profileForm, {
      name: props.userProfile.name || '',
      email: props.userProfile.email || '',
      mobile: props.userProfile.mobile || '',
      avatar: props.userProfile.avatar || '',
      gender: props.userProfile.gender ?? 0,
      birthday: props.userProfile.birthday || '',
      city: props.userProfile.city || '',
      address: props.userProfile.address || '',
      bio: props.userProfile.bio || '',
    });
  }
}

/**
 * 保存基本信息
 */
async function handleSaveProfile() {
  if (!profileFormRef.value) return;

  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      await patchUserProfileApi({ ...profileForm });
      ElMessage.success($t('user.updateProfileSuccess'));
      // 通知父组件重新加载用户信息
      emit('success');
    } catch (error: any) {
      ElMessage.error(error?.message || $t('user.updateProfileError'));
    } finally {
      loading.value = false;
    }
  });
}

/**
 * 头像上传成功回调
 */
function handleAvatarChange(value: string | string[] | undefined) {
  if (!value) {
    profileForm.avatar = '';
    return;
  }
  profileForm.avatar = Array.isArray(value) ? value[0] || '' : value || '';
}

/**
 * 重置表单
 */
function handleReset() {
  loadUserProfile();
}

// 监听 userProfile 变化，自动更新表单
watch(
  () => props.userProfile,
  (newVal) => {
    if (newVal) {
      Object.assign(profileForm, {
        name: newVal.name || '',
        email: newVal.email || '',
        mobile: newVal.mobile || '',
        avatar: newVal.avatar || '',
        gender: newVal.gender ?? 0,
        birthday: newVal.birthday || '',
        city: newVal.city || '',
        address: newVal.address || '',
        bio: newVal.bio || '',
      });
    }
  },
  { immediate: true },
);

// 初始化加载用户信息
loadUserProfile();
</script>

<template>
  <ElForm
    ref="profileFormRef"
    :model="profileForm"
    :rules="profileRules"
    label-width="120px"
    label-position="right"
  >
    <!-- 头像区域 -->
    <ElFormItem :label="$t('user.avatar')">
      <div class="flex items-center gap-6">
        <div class="flex-1">
          <ImageSelector
            v-model="profileForm.avatar"
            :enable-crop="true"
            crop-shape="circle"
            :max-size="2"
            :size="100"
            :placeholder="$t('user.selectAvatar')"
            @update:model-value="handleAvatarChange"
          />
          <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">
            {{ $t('user.avatarHelp') }}
          </p>
        </div>
      </div>
    </ElFormItem>

    <ElDivider />

    <!-- 基本信息 -->
    <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
      <ElFormItem :label="$t('user.userName')" prop="name">
        <ElInput
          v-model="profileForm.name"
          :placeholder="$t('user.userName')"
          clearable
        />
      </ElFormItem>

      <ElFormItem :label="$t('user.email')" prop="email">
        <ElInput
          v-model="profileForm.email"
          type="email"
          :placeholder="$t('user.email')"
          clearable
        />
      </ElFormItem>

      <ElFormItem :label="$t('user.mobile')" prop="mobile">
        <ElInput
          v-model="profileForm.mobile"
          :placeholder="$t('user.mobile')"
          clearable
        />
      </ElFormItem>

      <ElFormItem :label="$t('user.gender')">
        <ElRadioGroup v-model="profileForm.gender">
          <ElRadio
            v-for="option in genderOptions"
            :key="option.value"
            :label="option.value"
          >
            {{ option.label }}
          </ElRadio>
        </ElRadioGroup>
      </ElFormItem>

      <ElFormItem :label="$t('user.birthday')">
        <ElDatePicker
          v-model="profileForm.birthday"
          type="date"
          :placeholder="$t('user.selectBirthday')"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </ElFormItem>

      <ElFormItem :label="$t('user.city')">
        <ElInput
          v-model="profileForm.city"
          :placeholder="$t('user.city')"
          clearable
        />
      </ElFormItem>
    </div>

    <ElFormItem :label="$t('user.address')">
      <ElInput
        v-model="profileForm.address"
        :placeholder="$t('user.address')"
        clearable
      />
    </ElFormItem>

    <ElFormItem :label="$t('user.bio')">
      <ElInput
        v-model="profileForm.bio"
        type="textarea"
        :rows="4"
        :placeholder="$t('user.bioPlaceholder')"
        :maxlength="500"
        show-word-limit
      />
    </ElFormItem>

    <!-- 保存按钮 -->
    <ElFormItem>
      <ElButton type="primary" :loading="loading" @click="handleSaveProfile">
        {{ $t('common.save') }}
      </ElButton>
      <ElButton @click="handleReset">
        {{ $t('common.reset') }}
      </ElButton>
    </ElFormItem>
  </ElForm>
</template>
