import type { VxeTableGridOptions } from '@vben/plugins/vxe-table';

import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn } from '#/adapter/vxe-table';
import type { DeptUser } from '#/api/core/dept';

import { $t } from '@vben/locales';

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
 * 获取用户表格列配置
 */
export function useUserColumns(
  onActionClick?: OnActionClickFn<DeptUser>,
): VxeTableGridOptions<DeptUser>['columns'] {
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
