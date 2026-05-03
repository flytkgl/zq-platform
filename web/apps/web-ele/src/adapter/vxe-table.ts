import type { VxeTableGridOptions } from '@vben/plugins/vxe-table';
import type { Recordable } from '@vben/types';

import { h } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { $t, $te } from '@vben/locales';
import { setupVbenVxeTable, useVbenVxeGrid } from '@vben/plugins/vxe-table';
import { get, isFunction, isString } from '@vben/utils';

import {
  ElButton,
  ElImage,
  ElPopconfirm,
  ElTag,
  ElTooltip,
} from 'element-plus';

import { useVbenForm } from './form';

setupVbenVxeTable({
  configVxeTable: (vxeUI) => {
    vxeUI.setConfig({
      grid: {
        align: 'center',
        border: false,
        columnConfig: {
          resizable: true,
        },
        minHeight: 180,
        formConfig: {
          // 全局禁用vxe-table的表单配置，使用formOptions
          enabled: false,
        },
        proxyConfig: {
          autoLoad: true,
          response: {
            result: 'items',
            total: 'total',
            list: '',
          },
          showActionMsg: true,
          showResponseMsg: false,
        },
        round: true,
        showOverflow: true,
        size: 'medium',
      } as VxeTableGridOptions,
    });

    // 表格配置项可以用 cellRender: { name: 'CellImage' },
    vxeUI.renderer.add('CellImage', {
      renderTableDefault(_renderOpts, params) {
        const { column, row } = params;
        const src = row[column.field];
        return h(ElImage, { src, previewSrcList: [src] });
      },
    });

    // 表格配置项可以用 cellRender: { name: 'CellLink' },
    vxeUI.renderer.add('CellLink', {
      renderTableDefault(renderOpts) {
        const { props } = renderOpts;
        return h(
          ElButton,
          { size: 'small', link: true },
          { default: () => props?.text },
        );
      },
    });

    // 单元格渲染： Tag
    vxeUI.renderer.add('CellTag', {
      renderTableDefault({ options, props }, { column, row }) {
        const value = get(row, column.field);
        const tagOptions = options ?? [
          { type: 'success', label: $t('common.enabled'), value: true },
          { type: 'danger', label: $t('common.disabled'), value: false },
        ];
        const tagItem = tagOptions.find((item) => item.value === value);
        return h(
          ElTag,
          {
            type: tagItem?.type ?? 'info',
            ...props,
          },
          { default: () => tagItem?.label ?? value },
        );
      },
    });

    /**
     * 注册表格的操作按钮渲染器
     */
    vxeUI.renderer.add('CellOperation', {
      renderTableDefault({ attrs, options, props }, { column, row }) {
        const defaultProps = { size: 'small', link: true, ...props };
        let align = 'end';
        switch (column.align) {
          case 'center': {
            align = 'center';
            break;
          }
          case 'left': {
            align = 'start';
            break;
          }
          default: {
            align = 'end';
            break;
          }
        }
        const presets: Recordable<Recordable<any>> = {
          delete: {
            type: 'danger',
            text: $t('common.delete'),
            icon: 'ep:delete',
          },
          edit: {
            text: $t('common.edit'),
            icon: 'ep:edit',
            type: 'primary',
          },
        };
        const operations: Array<Recordable<any>> = (
          options || ['edit', 'delete']
        )
          .map((opt) => {
            if (isString(opt)) {
              return presets[opt]
                ? { code: opt, ...presets[opt], ...defaultProps }
                : {
                    code: opt,
                    text: $te(`common.${opt}`) ? $t(`common.${opt}`) : opt,
                    type: 'primary', // 自定义按钮默认使用主题色
                    ...defaultProps,
                  };
            } else {
              // 对象配置的按钮，如果没有 type，也默认为 primary
              const buttonConfig = {
                ...defaultProps,
                ...presets[opt.code],
                ...opt,
              };
              if (!buttonConfig.type && !presets[opt.code]) {
                buttonConfig.type = 'primary';
              }
              return buttonConfig;
            }
          })
          .map((opt) => {
            const optBtn: Recordable<any> = {};
            Object.keys(opt).forEach((key) => {
              optBtn[key] = isFunction(opt[key]) ? opt[key](row) : opt[key];
            });
            return optBtn;
          })
          .filter((opt) => opt.show !== false);

        function renderBtn(opt: Recordable<any>, listen = true) {
          const { icon, text, code, ...btnProps } = opt;
          const buttonType =
            btnProps.type === 'danger'
              ? 'danger'
              : (btnProps.type === 'primary'
                ? 'primary'
                : 'default');

          const button = h(
            ElButton,
            {
              ...btnProps,
              type: buttonType,
              size: 'small',
              link: true,
              circle: !!icon,
              onClick: listen
                ? () =>
                    attrs?.onClick?.({
                      code,
                      row,
                    })
                : undefined,
            },
            {
              default: () => {
                if (icon) {
                  return h(IconifyIcon, { class: 'size-4', icon });
                }
                return text;
              },
            },
          );

          // 如果有图标，用 Tooltip 包装；否则直接返回按钮
          if (icon) {
            return h(
              ElTooltip,
              {
                content: text,
                placement: 'top',
              },
              {
                default: () => button,
              },
            );
          }

          return button;
        }

        function renderConfirm(opt: Recordable<any>) {
          const { icon, text } = opt;

          const button = h(
            ElButton,
            {
              type: 'danger',
              size: 'small',
              link: true,
              circle: !!icon,
              title: icon ? text : undefined,
            },
            {
              default: () => {
                if (icon) {
                  return h(IconifyIcon, { class: 'size-4', icon });
                }
                return text;
              },
            },
          );

          return h(
            ElPopconfirm,
            {
              title: $t('ui.actionTitle.delete', [attrs?.nameTitle || '']),
              confirmButtonText: $t('common.confirm'),
              cancelButtonText: $t('common.cancel'),
              confirmButtonType: 'danger',
              onConfirm: () => {
                attrs?.onClick?.({
                  code: opt.code,
                  row,
                });
              },
            },
            {
              reference: () => button,
              default: () =>
                $t('ui.actionMessage.deleteConfirm', [
                  row[attrs?.nameField || 'name'],
                ]),
            },
          );
        }

        const btns = operations.map((opt) =>
          opt.code === 'delete' ? renderConfirm(opt) : renderBtn(opt),
        );
        return h(
          'div',
          {
            class: 'flex table-operations',
            style: { justifyContent: align },
          },
          btns,
        );
      },
    });

    // 这里可以自行扩展 vxe-table 的全局配置，比如自定义格式化
    // vxeUI.formats.add
  },
  useVbenForm,
});

// 自定义类型定义
export type OnActionClickParams<T = Recordable<any>> = {
  code: string;
  row: T;
};

export type OnActionClickFn<T = Recordable<any>> = (
  params: OnActionClickParams<T>,
) => void;

export { useVbenVxeGrid };

export type * from '@vben/plugins/vxe-table';
