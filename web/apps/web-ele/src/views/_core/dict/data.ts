import type { VxeTableGridOptions } from '@vben/plugins/vxe-table';

import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn } from '#/adapter/vxe-table';
import type { DictItem } from '#/api/core/dict';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';

/**
 * 获取字典搜索表单的字段配置
 */
export function useDictSearchFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('dict.dictName'),
    },
    {
      component: 'Input',
      fieldName: 'code',
      label: $t('dict.dictCode'),
    },
  ];
}

/**
 * 获取字典表单配置
 */
export function useDictFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('dict.dictName'),
      rules: z
        .string()
        .min(2, $t('ui.formRules.minLength', [$t('dict.dictName'), 2]))
        .max(100, $t('ui.formRules.maxLength', [$t('dict.dictName'), 100])),
    },
    {
      component: 'Input',
      fieldName: 'code',
      label: $t('dict.dictCode'),
      rules: z
        .string()
        .min(2, $t('ui.formRules.minLength', [$t('dict.dictCode'), 2]))
        .max(100, $t('ui.formRules.maxLength', [$t('dict.dictCode'), 100]))
        .regex(/^\w+$/, $t('dict.codeFormatError')),
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
      label: $t('dict.status'),
    },
  ];
}

/**
 * 获取字典项搜索表单配置
 */
export function useDictItemSearchFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'label',
      label: $t('dict.itemLabel'),
    },
    {
      component: 'Input',
      fieldName: 'value',
      label: $t('dict.itemValue'),
    },
  ];
}

/**
 * 获取字典项表单配置
 */
export function useDictItemFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'label',
      label: $t('dict.itemLabel'),
      rules: z
        .string()
        .min(1, $t('ui.formRules.required', [$t('dict.itemLabel')]))
        .max(100, $t('ui.formRules.maxLength', [$t('dict.itemLabel'), 100])),
    },
    {
      component: 'Input',
      fieldName: 'value',
      label: $t('dict.itemValue'),
      rules: z
        .string()
        .min(1, $t('ui.formRules.required', [$t('dict.itemValue')]))
        .max(100, $t('ui.formRules.maxLength', [$t('dict.itemValue'), 100])),
    },
    // {
    //   component: 'Input',
    //   fieldName: 'icon',
    //   label: $t('dict.itemIcon'),
    //   rules: z
    //     .string()
    //     .max(100, $t('ui.formRules.maxLength', [$t('dict.itemIcon'), 100]))
    //     .optional(),
    // },
    {
      component: 'Textarea',
      componentProps: {
        placeholder: $t('dict.remarkPlaceholder'),
        rows: 3,
      },
      fieldName: 'remark',
      label: $t('dict.remark'),
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
      label: $t('dict.status'),
    },
  ];
}

/**
 * 获取字典项表格列配置
 */
export function useDictItemColumns(
  onActionClick?: OnActionClickFn<DictItem>,
): VxeTableGridOptions<DictItem>['columns'] {
  return [
    {
      field: 'label',
      title: $t('dict.itemLabel'),
      minWidth: 120,
    },
    {
      field: 'value',
      title: $t('dict.itemValue'),
      minWidth: 120,
    },
    // {
    //   field: 'icon',
    //   title: $t('dict.itemIcon'),
    //   minWidth: 100,
    // },
    {
      field: 'status',
      title: $t('dict.status'),
      minWidth: 80,
      cellRender: {
        name: 'CellStatus',
        attrs: {
          onClick: onActionClick,
        },
      },
    },
    {
      align: 'right',
      cellRender: {
        attrs: {
          nameField: 'label',
          nameTitle: $t('dict.itemLabel'),
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
