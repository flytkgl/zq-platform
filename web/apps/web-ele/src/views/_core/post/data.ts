import type { VxeTableGridOptions } from '@vben/plugins/vxe-table';

import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn } from '#/adapter/vxe-table';
import type { Post } from '#/api/core/post';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';

/**
 * 获取搜索表单的字段配置
 */
export function useSearchFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('system.user.userName'),
    },
    {
      component: 'Input',
      fieldName: 'username',
      label: $t('system.user.account'),
    },
  ];
}

/**
 * 获取岗位类型选项
 */
export function getPostTypeOptions() {
  return [
    { label: $t('post.types.management'), value: 0 },
    { label: $t('post.types.technical'), value: 1 },
    { label: $t('post.types.business'), value: 2 },
    { label: $t('post.types.functional'), value: 3 },
    { label: $t('post.types.other'), value: 4 },
  ];
}

/**
 * 获取岗位级别选项
 */
export function getPostLevelOptions() {
  return [
    { label: $t('post.levels.senior'), value: 0 },
    { label: $t('post.levels.middle'), value: 1 },
    { label: $t('post.levels.basic'), value: 2 },
    { label: $t('post.levels.staff'), value: 3 },
  ];
}

/**
 * 获取岗位树列配置
 */
export function usePostTreeColumns(
  onActionClick?: OnActionClickFn<Post>,
): VxeTableGridOptions<Post>['columns'] {
  return [
    {
      field: 'name',
      title: $t('post.postName'),
      minWidth: 150,
    },
  ];
}

export function useFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('post.postName'),
      rules: z
        .string()
        .min(2, $t('ui.formRules.minLength', [$t('post.postName'), 2]))
        .max(64, $t('ui.formRules.maxLength', [$t('post.postName'), 64])),
    },
    {
      component: 'Input',
      fieldName: 'code',
      label: $t('post.postCode'),
      rules: z
        .string()
        .min(2, $t('ui.formRules.minLength', [$t('post.postCode'), 2]))
        .max(32, $t('ui.formRules.maxLength', [$t('post.postCode'), 32]))
        .regex(/^[\w-]+$/, $t('post.codeFormatError')),
    },
    {
      component: 'Select',
      componentProps: {
        options: getPostTypeOptions(),
      },
      defaultValue: 4,
      fieldName: 'post_type',
      label: $t('post.postType'),
    },
    {
      component: 'Select',
      componentProps: {
        options: getPostLevelOptions(),
      },
      defaultValue: 3,
      fieldName: 'post_level',
      label: $t('post.postLevel'),
    },
    {
      component: 'DeptSelector',
      componentProps: {
        placeholder: $t('post.selectDepartment'),
      },
      fieldName: 'dept_id',
      label: $t('post.department'),
    },
    {
      component: 'Textarea',
      componentProps: {
        placeholder: $t('post.descriptionPlaceholder'),
        rows: 3,
      },
      fieldName: 'description',
      label: $t('post.description'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        options: [
          { label: $t('common.enabled'), value: true },
          { label: $t('common.disabled'), value: false },
        ],
      },
      defaultValue: true,
      fieldName: 'status',
      label: $t('post.status'),
    },
  ];
}

/**
 * 获取用户表格列配置
 */
export function useUserColumns(
  onActionClick?: OnActionClickFn<Post>,
): VxeTableGridOptions<Post>['columns'] {
  return [
    {
      type: 'checkbox',
      minWidth: 60,
      align: 'center',
      fixed: 'left',
    },
    {
      field: 'username',
      title: $t('system.user.account'),
      minWidth: 120,
    },
    {
      field: 'name',
      title: $t('system.user.userName'),
      minWidth: 120,
    },
    {
      field: 'email',
      title: $t('system.user.email'),
      minWidth: 180,
    },
    {
      align: 'right',
      cellRender: {
        attrs: {
          nameField: 'name',
          nameTitle: $t('system.user.userName'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: ['edit', 'delete'],
      },
      field: 'operation',
      fixed: 'right',
      headerAlign: 'center',
      showOverflow: false,
      title: $t('system.user.operation'),
      minWidth: 150,
    },
  ];
}
