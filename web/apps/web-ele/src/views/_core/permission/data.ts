import type { Column } from 'element-plus';

import type { VbenFormSchema } from '#/adapter/form';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';

/**
 * 权限类型选项
 */
export function getPermissionTypeOptions() {
  return [
    {
      value: 1,
      label: $t('permission.permissionTypes.api'),
      description: $t('permission.permissionTypes.apiDesc'),
      color: 'green',
    },
  ];
}

export const PERMISSION_TYPE_OPTIONS = getPermissionTypeOptions();

/**
 * HTTP 方法选项
 */
export const HTTP_METHOD_OPTIONS = [
  { value: 0, label: 'GET', method: 'GET' },
  { value: 1, label: 'POST', method: 'POST' },
  { value: 2, label: 'PUT', method: 'PUT' },
  { value: 3, label: 'DELETE', method: 'DELETE' },
  { value: 4, label: 'PATCH', method: 'PATCH' },
  { value: 5, label: 'ALL', method: 'ALL' },
];

/**
 * 获取权限表单 Schema
 */
export function getFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('permission.permissionName'),
      rules: z
        .string()
        .min(1, $t('permission.validationErrors.nameRequired'))
        .max(64, $t('permission.validationErrors.nameMaxLength')),
      componentProps: {
        placeholder: $t('permission.placeholder.name'),
      },
    },
    {
      component: 'Input',
      fieldName: 'code',
      label: $t('permission.permissionCode'),
      rules: z
        .string()
        .min(1, $t('permission.validationErrors.codeRequired'))
        .max(64, $t('permission.validationErrors.codeMaxLength'))
        .regex(/^[\w:]+$/, $t('permission.validationErrors.codeFormat')),
      componentProps: {
        placeholder: $t('permission.placeholder.code'),
      },
    },
    {
      component: 'Input',
      fieldName: 'api_path',
      label: $t('permission.apiPath'),
      rules: z.string().optional(),
      componentProps: {
        placeholder: $t('permission.placeholder.apiPath'),
      },
      dependencies: {
        triggerFields: ['permission_type'],
      },
    },
    {
      component: 'RadioGroup',
      fieldName: 'http_method',
      label: $t('permission.httpMethod'),
      defaultValue: 0,
      componentProps: {
        buttonStyle: 'solid',
        options: HTTP_METHOD_OPTIONS,
        isButton: true,
      },
      dependencies: {
        triggerFields: ['permission_type'],
      },
    },
    {
      component: 'RadioGroup',
      fieldName: 'is_active',
      label: $t('common.status'),
      defaultValue: true,
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('common.enabled'), value: true },
          { label: $t('common.disabled'), value: false },
        ],
        isButton: true,
      },
    },
  ];
}

/**
 * 获取权限列表搜索 Schema
 */
export function getSearchFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('permission.permissionName'),
    },
    {
      component: 'Input',
      fieldName: 'code',
      label: $t('permission.permissionCode'),
    },
  ];
}

/**
 * 获取 ZqTable 表格列配置
 */
export function useZqTableColumns(): Column[] {
  return [
    {
      key: 'name',
      dataKey: 'name',
      title: $t('permission.permissionName'),
      width: 150,
    },
    {
      key: 'code',
      dataKey: 'code',
      title: $t('permission.permissionCode'),
      width: 180,
    },
    {
      key: 'permission_type',
      title: $t('permission.permissionType'),
      width: 100,
      align: 'center' as const,
      slots: { default: 'cell-permission_type' },
    },
    {
      key: 'http_method',
      title: $t('permission.httpMethod'),
      width: 100,
      align: 'center' as const,
      slots: { default: 'cell-http_method' },
    },
    {
      key: 'api_path',
      dataKey: 'api_path',
      title: $t('permission.apiPath'),
      width: 220,
    },
    {
      key: 'description',
      dataKey: 'description',
      title: $t('permission.description'),
      width: 150,
    },
    {
      key: 'actions',
      title: $t('permission.operation'),
      width: 150,
      fixed: true,
      align: 'center' as const,
      slots: { default: 'cell-actions' },
    },
  ];
}
