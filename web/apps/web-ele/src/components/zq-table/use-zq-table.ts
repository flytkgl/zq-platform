import type { BaseFormComponentType } from '@vben/common-ui';

import type { ExtendedZqTableApi, ZqTableProps } from './types';

import { defineComponent, h, onBeforeUnmount } from 'vue';

import { ZqTableApi } from './api';
import { useStore } from './store';
import ZqTable from './zq-table.vue';

export function useZqTable<
  T extends Record<string, any> = any,
  D extends BaseFormComponentType = BaseFormComponentType,
>(options: ZqTableProps<T, D>) {
  const api = new ZqTableApi(options);
  const extendedApi: ExtendedZqTableApi<T, D> = api as ExtendedZqTableApi<T, D>;
  extendedApi.useStore = (selector) => {
    return useStore(api.store, selector);
  };

  const Grid = defineComponent(
    (props: ZqTableProps<T>, { attrs, slots }) => {
      onBeforeUnmount(() => {
        api.unmount();
      });
      api.setState({ ...props, ...attrs });
      return () => h(ZqTable, { ...props, ...attrs, api: extendedApi }, slots);
    },
    {
      name: 'ZqTable',
      inheritAttrs: false,
    },
  );

  return [Grid, extendedApi] as const;
}

export type UseZqTable = typeof useZqTable;
