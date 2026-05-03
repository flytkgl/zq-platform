import type { Column } from 'element-plus';

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
 * 获取状态选项
 */
export function getStatusOptions() {
  return [
    { type: 'danger', label: $t('common.disabled'), value: 0 },
    { type: 'success', label: $t('common.enabled'), value: 1 },
    { type: 'warning', label: $t('user.locked'), value: 2 },
  ];
}

/**
 * 获取用户类型选项
 */
export function getUserTypeOptions() {
  return [
    { label: $t('user.systemUser'), value: 0, type: 'danger' },
    { label: $t('user.normalUser'), value: 1, type: 'primary' },
    { label: $t('user.externalUser'), value: 2, type: 'warning' },
  ];
}

/**
 * 获取登录方式选项
 */
export function getLoginTypeOptions() {
  return [
    { label: '密码登录', value: 'password', type: 'info' },
    { label: '验证码登录', value: 'code', type: 'info' },
    { label: '二维码登录', value: 'qrcode', type: 'info' },
    { label: 'Gitee', value: 'gitee', type: 'success' },
    { label: 'GitHub', value: 'github', type: 'success' },
    { label: 'QQ', value: 'qq', type: 'success' },
    { label: 'Google', value: 'google', type: 'success' },
    { label: '微信', value: 'wechat', type: 'success' },
    { label: '微软', value: 'microsoft', type: 'success' },
    { label: '钉钉', value: 'dingtalk', type: 'success' },
    { label: '飞书', value: 'feishu', type: 'success' },
  ];
}

/**
 * 获取搜索表单的字段配置
 */
export function useSearchFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('user.userName'),
    },
    {
      component: 'Input',
      fieldName: 'username',
      label: $t('user.account'),
    },
    {
      component: 'Select',
      fieldName: 'last_login_type',
      label: '最后登录方式',
      componentProps: {
        placeholder: '请选择登录方式',
        options: getLoginTypeOptions(),
        clearable: true,
      },
    },
  ];
}

/**
 * 获取编辑表单的字段配置
 */
export function getFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'username',
      label: $t('user.account'),
      rules: z
        .string()
        .min(3, $t('ui.formRules.minLength', [$t('user.account'), 3]))
        .max(150, $t('ui.formRules.maxLength', [$t('user.account'), 150])),
    },
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('user.userName'),
      rules: z
        .string()
        .min(2, $t('ui.formRules.minLength', [$t('user.userName'), 2]))
        .max(64, $t('ui.formRules.maxLength', [$t('user.userName'), 64])),
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
        .nullish()
        .or(z.literal('')),
    },
    {
      component: 'Input',
      fieldName: 'mobile',
      label: $t('user.mobile'),
      rules: z
        .string()
        .regex(/^1[3-9]\d{9}$/, $t('user.mobileFormatError'))
        .nullish()
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
        .nullish()
        .or(z.literal('')),
    },
    {
      component: 'Input',
      fieldName: 'address',
      label: $t('user.address'),
      rules: z
        .string()
        .max(200, $t('ui.formRules.maxLength', [$t('user.address'), 200]))
        .nullish()
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
    {
      component: 'DeptSelector',
      componentProps: {
        placeholder: $t('user.selectDept'),
      },
      fieldName: 'dept_id',
      label: $t('user.dept'),
    },
    {
      component: 'UserSelector',
      componentProps: {
        placeholder: $t('user.selectManager'),
      },
      fieldName: 'manager_id',
      label: $t('user.manager'),
    },
    {
      component: 'PostSelector',
      componentProps: {
        placeholder: $t('user.selectPost'),
      },
      fieldName: 'post_id',
      label: $t('user.post'),
    },
    {
      component: 'RoleSelector',
      componentProps: {
        multiple: true,
        placeholder: $t('user.selectRole'),
      },
      fieldName: 'role_ids',
      label: $t('user.role'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: getUserTypeOptions(),
        isButton: true,
      },
      defaultValue: 1,
      fieldName: 'user_type',
      label: $t('user.userType'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: getStatusOptions(),
        isButton: true,
      },
      defaultValue: 1,
      fieldName: 'user_status',
      label: $t('user.status'),
    },
  ];
}

/**
 * 获取 ZqTable 表格列配置
 */
export function useZqTableColumns(): Column[] {
  return [
    {
      key: 'avatar',
      title: $t('user.avatar'),
      width: 80,
      align: 'center' as const,
      slots: { default: 'cell-avatar' },
    },
    {
      key: 'username',
      dataKey: 'username',
      title: $t('user.account'),
      width: 120,
    },
    {
      key: 'name',
      dataKey: 'name',
      title: $t('user.userName'),
      width: 120,
    },
    {
      key: 'email',
      dataKey: 'email',
      title: $t('user.email'),
      width: 180,
    },
    {
      key: 'mobile',
      dataKey: 'mobile',
      title: $t('user.mobile'),
      width: 130,
    },
    {
      key: 'user_type',
      title: $t('user.userType'),
      width: 100,
      align: 'center' as const,
      slots: { default: 'cell-user_type' },
    },
    {
      key: 'gender',
      title: $t('user.gender'),
      width: 80,
      align: 'center' as const,
      slots: { default: 'cell-gender' },
    },
    {
      key: 'birthday',
      dataKey: 'birthday',
      title: $t('user.birthday'),
      width: 120,
    },
    {
      key: 'city',
      dataKey: 'city',
      title: $t('user.city'),
      width: 120,
    },
    {
      key: 'dept_name',
      dataKey: 'dept_name',
      title: $t('user.dept'),
      width: 140,
    },
    {
      key: 'manager_name',
      dataKey: 'manager_name',
      title: $t('user.manager'),
      width: 120,
    },
    {
      key: 'user_status',
      title: $t('user.status'),
      width: 100,
      align: 'center' as const,
      slots: { default: 'cell-user_status' },
    },
    {
      key: 'last_login_type',
      title: '最后登录方式',
      width: 120,
      align: 'center' as const,
      slots: { default: 'cell-last_login_type' },
    },
    {
      key: 'last_login',
      dataKey: 'last_login',
      title: '最后登录时间',
      width: 180,
    },
    {
      key: 'sys_create_datetime',
      dataKey: 'sys_create_datetime',
      title: $t('user.createTime'),
      width: 180,
    },
    {
      key: 'actions',
      title: $t('user.operation'),
      width: 250,
      fixed: true,
      align: 'center' as const,
      slots: { default: 'cell-actions' },
    },
  ];
}
