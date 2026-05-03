import type { VbenFormSchema } from '#/adapter/form';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';

/**
 * 获取性别选项
 */
export function getGenderOptions() {
  return [
    { label: $t('user.unknown'), value: 0 },
    { label: $t('user.male'), value: 1 },
    { label: $t('user.female'), value: 2 },
  ];
}

/**
 * 获取基本信息表单配置
 */
export function getProfileFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('user.userName'),
      rules: z
        .string()
        .min(2, $t('ui.formRules.minLength', [$t('user.userName'), 2]))
        .max(64, $t('ui.formRules.maxLength', [$t('user.userName'), 64]))
        .optional()
        .or(z.literal('')),
    },
    {
      component: 'ImageSelector',
      componentProps: {
        enableCrop: true,
        cropShape: 'circle',
        maxSize: 2,
        placeholder: $t('user.selectAvatar'),
      },
      fieldName: 'avatar',
      label: $t('user.avatar'),
      help: $t('user.avatarHelp'),
    },
    {
      component: 'Input',
      fieldName: 'email',
      label: $t('user.email'),
      rules: z
        .string()
        .email($t('user.emailFormatError'))
        .max(255, $t('ui.formRules.maxLength', [$t('user.email'), 255]))
        .optional()
        .or(z.literal('')),
    },
    {
      component: 'Input',
      fieldName: 'mobile',
      label: $t('user.mobile'),
      rules: z
        .string()
        .regex(/^1[3-9]\d{9}$/, $t('user.mobileFormatError'))
        .optional()
        .or(z.literal('')),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: getGenderOptions(),
        isButton: true,
      },
      defaultValue: 0,
      fieldName: 'gender',
      label: $t('user.gender'),
    },
    {
      component: 'DatePicker',
      componentProps: {
        placeholder: $t('user.selectBirthday'),
        valueFormat: 'YYYY-MM-DD',
      },
      fieldName: 'birthday',
      label: $t('user.birthday'),
    },
    {
      component: 'Input',
      fieldName: 'city',
      label: $t('user.city'),
      rules: z
        .string()
        .max(100, $t('ui.formRules.maxLength', [$t('user.city'), 100]))
        .optional()
        .or(z.literal('')),
    },
    {
      component: 'Input',
      fieldName: 'address',
      label: $t('user.address'),
      rules: z
        .string()
        .max(200, $t('ui.formRules.maxLength', [$t('user.address'), 200]))
        .optional()
        .or(z.literal('')),
    },
    {
      component: 'Textarea',
      componentProps: {
        placeholder: $t('user.bioPlaceholder'),
        rows: 3,
      },
      fieldName: 'bio',
      label: $t('user.bio'),
    },
  ];
}

/**
 * 获取密码修改表单配置
 */
export function getPasswordFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      componentProps: {
        type: 'password',
        showPassword: true,
        placeholder: $t('user.oldPasswordPlaceholder'),
      },
      fieldName: 'old_password',
      label: $t('user.oldPassword'),
      rules: z
        .string()
        .min(1, $t('ui.formRules.required', [$t('user.oldPassword')])),
    },
    {
      component: 'Input',
      componentProps: {
        type: 'password',
        showPassword: true,
        placeholder: $t('user.newPasswordPlaceholder'),
      },
      fieldName: 'new_password',
      label: $t('user.newPassword'),
      rules: z
        .string()
        .min(6, $t('ui.formRules.minLength', [$t('user.newPassword'), 6]))
        .max(20, $t('ui.formRules.maxLength', [$t('user.newPassword'), 20])),
    },
    {
      component: 'Input',
      componentProps: {
        type: 'password',
        showPassword: true,
        placeholder: $t('user.confirmPasswordPlaceholder'),
      },
      fieldName: 'confirm_password',
      label: $t('user.confirmPassword'),
      rules: z
        .string()
        .min(1, $t('ui.formRules.required', [$t('user.confirmPassword')])),
    },
  ];
}
