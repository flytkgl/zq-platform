import type { ExtendedFormApi } from '@vben/common-ui';

import type { ZqPaginationInfo, ZqTableProps } from './types';

import { reactive, ref } from 'vue';

import {
  bindMethods,
  isBoolean,
  isFunction,
  mergeWithArrayOverride,
  StateHandler,
} from '@vben/utils';

import { Store } from './store';

function getDefaultState(): ZqTableProps {
  return {
    class: '',
    gridClass: '',
    gridOptions: {
      proxyConfig: {
        autoLoad: true,
      },
      pagerConfig: {
        enabled: true,
        pageSize: 20,
        pageSizes: [10, 20, 50, 100],
        currentPage: 1,
        total: 0,
      },
    },
    gridEvents: {},
    formOptions: undefined,
    showSearchForm: true,
  };
}

export class ZqTableApi<T extends Record<string, any> = any> {
  public formApi = {} as ExtendedFormApi;

  public loading = ref(false);
  public pagination = reactive<ZqPaginationInfo>({
    currentPage: 1,
    pageSize: 20,
    total: 0,
  });

  public state: null | ZqTableProps<T> = null;
  // 状态存储
  public store: Store<ZqTableProps<T>>;
  // 响应式数据供组件消费
  public tableData = ref<T[]>([]);
  public total = ref(0);

  private isMounted = false;
  private stateHandler: StateHandler;

  constructor(options: ZqTableProps = {}) {
    const storeState = { ...options };
    const defaultState = getDefaultState();
    this.store = new Store<ZqTableProps>(
      mergeWithArrayOverride(storeState, defaultState),
      {
        onUpdate: () => {
          this.state = this.store.state;
          this.syncStateToRefs();
        },
      },
    );

    this.state = this.store.state;
    this.stateHandler = new StateHandler();
    bindMethods(this);
    this.syncStateToRefs();
  }

  handlePageChange(currentPage: number, pageSize: number) {
    this.pagination.currentPage = currentPage;
    this.pagination.pageSize = pageSize;
    // 更新 store 中的 pagerConfig，保持一致性
    this.setState((prev) => ({
      gridOptions: {
        ...prev.gridOptions,
        pagerConfig: {
          ...prev.gridOptions?.pagerConfig,
          currentPage,
          pageSize,
        },
      },
    }));
    this.reload();
  }

  mount(formApi: ExtendedFormApi) {
    if (!this.isMounted) {
      this.formApi = formApi;
      this.stateHandler.setConditionTrue();
      this.isMounted = true;
    }
  }

  // 模拟 commitProxy('query')
  async query(params: Record<string, any> = {}) {
    await this.reload(params);
  }

  // 核心数据加载逻辑
  async reload(params: Record<string, any> = {}) {
    console.log('[ZqTable] reload called, state:', this.state?.gridOptions);
    const { proxyConfig } = this.state?.gridOptions || {};
    if (!proxyConfig?.ajax?.query) {
      console.warn(
        '[ZqTable] No ajax.query configured, proxyConfig:',
        proxyConfig,
      );
      this.setLoading(false);
      return;
    }

    console.log('[ZqTable] Starting data load...');
    this.setLoading(true);
    try {
      // 1. 获取表单数据（带超时保护）
      let formData: Record<string, any> = {};
      try {
        if (
          this.isMounted &&
          this.formApi &&
          typeof this.formApi.getValues === 'function'
        ) {
          // 添加超时保护，避免 formApi 未就绪时卡住
          const timeoutPromise = new Promise<Record<string, any>>((_, reject) =>
            setTimeout(() => reject(new Error('Form API timeout')), 100),
          );
          formData = await Promise.race([
            this.formApi.getValues() as Promise<Record<string, any>>,
            timeoutPromise,
          ]).catch(() => ({}));
        }
      } catch {
        // 表单未初始化时忽略错误
        formData = {};
      }

      // 2. 组装参数
      const queryParams = {
        page: {
          currentPage: this.pagination.currentPage,
          pageSize: this.pagination.pageSize,
          total: this.pagination.total,
        },
        form: { ...formData, ...params },
        sort: {}, // TODO: 实现排序
      };

      // 3. 调用用户传入的 ajax 方法
      const queryFn = proxyConfig.ajax!.query as (params: any) => Promise<any>;
      const result = await queryFn(queryParams);

      // 4. 更新数据
      // 适配不同的返回格式: { items: [], total: 0 } 或 []
      if (Array.isArray(result)) {
        this.tableData.value = result;
        this.total.value = result.length;
      } else if (result && typeof result === 'object') {
        this.tableData.value = result.items || result.data || [];
        this.total.value = result.total || 0;
      }

      // 更新分页状态
      this.pagination.total = this.total.value;
    } catch (error) {
      console.error('Load data failed', error);
    } finally {
      this.setLoading(false);
    }
  }

  setGridOptions(options: Partial<ZqTableProps['gridOptions']>) {
    this.setState({
      gridOptions: options,
    });
  }

  setLoading(isLoading: boolean) {
    this.loading.value = isLoading;
  }

  setState(
    stateOrFn:
      | ((prev: ZqTableProps<T>) => Partial<ZqTableProps<T>>)
      | Partial<ZqTableProps<T>>,
  ) {
    if (isFunction(stateOrFn)) {
      this.store.setState((prev) => {
        return mergeWithArrayOverride(stateOrFn(prev), prev);
      });
    } else {
      this.store.setState((prev) => mergeWithArrayOverride(stateOrFn, prev));
    }
  }

  toggleSearchForm(show?: boolean) {
    this.setState({
      showSearchForm: isBoolean(show) ? show : !this.state?.showSearchForm,
    });
    return this.state?.showSearchForm;
  }

  unmount() {
    this.isMounted = false;
    this.stateHandler.reset();
  }

  private syncStateToRefs() {
    if (this.state?.gridOptions?.data) {
      this.tableData.value = this.state.gridOptions.data;
    }
    if (this.state?.gridOptions?.pagerConfig) {
      const { currentPage, pageSize, total } =
        this.state.gridOptions.pagerConfig;
      if (currentPage !== undefined) this.pagination.currentPage = currentPage;
      if (pageSize !== undefined) this.pagination.pageSize = pageSize;
      if (total !== undefined) this.pagination.total = total;
    }
  }
}
