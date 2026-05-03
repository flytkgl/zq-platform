<script lang="ts" setup>
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type { LoginLog } from '#/api/core/login-log';

import { ref } from 'vue';

import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { ElButton, ElMessage, ElMessageBox } from 'element-plus';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  batchDeleteLoginLogApi,
  deleteLoginLogApi,
  getLoginLogDetailApi,
  getLoginLogListApi,
} from '#/api/core/login-log';

import { useColumns, useSearchFormSchema } from './data';
import DetailDrawer from './modules/detail-drawer.vue';

defineOptions({ name: 'SystemLoginLog' });

const selectedRows = ref<LoginLog[]>([]);
const detailDrawerRef = ref();
const currentLog = ref<LoginLog>();

/**
 * 查看详情
 */
async function onDetail(row: LoginLog) {
  try {
    const log = await getLoginLogDetailApi(row.id);
    currentLog.value = log;
    detailDrawerRef.value?.open();
  } catch (error) {
    ElMessage.error($t('loginLog.getDetailError'));
    console.error($t('loginLog.getDetailError'), error);
  }
}

/**
 * 删除单条日志
 */
function onDelete(row: LoginLog) {
  ElMessageBox.confirm(
    $t('loginLog.deleteConfirm', [row.username]),
    $t('common.delete'),
    {
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
      type: 'warning',
    },
  )
    .then(async () => {
      try {
        await deleteLoginLogApi(row.id);
        ElMessage.success($t('loginLog.deleteSuccess'));
        refreshGrid();
      } catch {
        ElMessage.error($t('loginLog.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

/**
 * 批量删除日志
 */
function onBatchDelete() {
  if (selectedRows.value.length === 0) {
    ElMessage.warning($t('loginLog.selectLogsToDelete'));
    return;
  }

  const usernames = selectedRows.value
    .map((row: LoginLog) => row.username)
    .join('、');
  const confirmMessage = $t('loginLog.batchDeleteConfirm', [
    selectedRows.value.length,
    usernames,
  ]);

  ElMessageBox.confirm(confirmMessage, $t('loginLog.batchDeleteTitle'), {
    confirmButtonText: $t('common.confirm'),
    cancelButtonText: $t('common.cancel'),
    type: 'warning',
  })
    .then(async () => {
      try {
        const ids = selectedRows.value.map((row: LoginLog) => row.id);
        await batchDeleteLoginLogApi(ids);
        ElMessage.success($t('loginLog.deleteSuccess'));
        selectedRows.value = [];
        refreshGrid();
      } catch {
        ElMessage.error($t('loginLog.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

/**
 * 表格操作按钮的回调函数
 */
function onActionClick({ code, row }: OnActionClickParams<LoginLog>) {
  switch (code) {
    case 'delete': {
      onDelete(row);
      break;
    }
    case 'detail': {
      onDetail(row);
      break;
    }
  }
}

const [Grid, gridApi] = useVbenVxeGrid({
  formOptions: {
    schema: useSearchFormSchema(),
    submitOnChange: true,
  },
  gridEvents: {
    checkboxAll: ({ records }: { records: LoginLog[] }) => {
      selectedRows.value = records;
    },
    checkboxChange: ({ records }: { records: LoginLog[] }) => {
      selectedRows.value = records;
    },
  },
  gridOptions: {
    columns: useColumns(onActionClick),
    height: 'auto',
    keepSource: true,
    proxyConfig: {
      ajax: {
        query: async ({ page }, formValues) => {
          const params = {
            page: page.currentPage,
            pageSize: page.pageSize,
            ...formValues,
          };
          return await getLoginLogListApi(params);
        },
      },
    },
    checkboxConfig: {
      reserve: true,
      trigger: 'default',
    },
    toolbarConfig: {
      custom: true,
      export: false,
      refresh: { code: 'query' },
      search: true,
      zoom: true,
    },
  } as VxeTableGridOptions<LoginLog>,
});

/**
 * 刷新表格
 */
function refreshGrid() {
  gridApi.query();
}
</script>

<template>
  <Page auto-content-height>
    <DetailDrawer ref="detailDrawerRef" :log="currentLog" />

    <Grid>
      <template #table-title>
        <ElButton type="danger" plain @click="onBatchDelete">
          {{ $t('loginLog.batchDelete') }}
          {{ selectedRows.length > 0 ? `(${selectedRows.length})` : '' }}
        </ElButton>
      </template>
    </Grid>
  </Page>
</template>
