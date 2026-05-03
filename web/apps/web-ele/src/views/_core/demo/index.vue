<script lang="ts" setup>
import type { Demo } from '#/api/core/demo';

import { ref } from 'vue';

import { Page } from '@vben/common-ui';
import { Download, Edit, Plus, Trash2, Upload } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElMessage, ElMessageBox, ElTag } from 'element-plus';

import {
  deleteDemoApi,
  downloadDemoTemplateApi,
  exportDemoExcelApi,
  getDemoListApi,
  importDemoExcelApi,
} from '#/api/core/demo';
import { useZqTable } from '#/components/zq-table';

import DemoFormDialog from './modules/demo-form-dialog.vue';

defineOptions({ name: 'DemoManager' });

const demoFormDialogRef = ref<InstanceType<typeof DemoFormDialog>>();

const fetchDemoList = async (params: any) => {
  const res = await getDemoListApi({
    page: params.page.currentPage,
    pageSize: params.page.pageSize,
    title: params.form?.title,
    status: params.form?.status,
    priority: params.form?.priority,
  });
  return {
    items: res.items,
    total: res.total,
  };
};

const [Grid, gridApi] = useZqTable({
  gridOptions: {
    columns: [
      {
        key: 'title',
        title: $t('demos.demo.title'),
        minWidth: 200,
      },
      {
        key: 'content',
        title: $t('demos.demo.content'),
        minWidth: 250,
        showOverflow: true,
      },
      {
        key: 'status',
        title: $t('demos.demo.status'),
        width: 100,
        align: 'center',
        slots: { default: 'cell-status' },
      },
      {
        key: 'priority',
        title: $t('demos.demo.priority'),
        width: 100,
        align: 'center',
        slots: { default: 'cell-priority' },
      },
      {
        key: 'is_active',
        title: $t('demos.demo.isActive'),
        width: 100,
        align: 'center',
        slots: { default: 'cell-is_active' },
      },
      {
        key: 'sys_create_datetime',
        title: $t('demos.demo.createTime'),
        width: 170,
        slots: { default: 'cell-create_time' },
      },
      {
        key: 'actions',
        title: $t('common.action'),
        width: 150,
        fixed: 'right',
        align: 'center',
        slots: { default: 'cell-actions' },
      },
    ],
    border: true,
    stripe: true,
    showSelection: true,
    showIndex: true,
    proxyConfig: {
      autoLoad: true,
      ajax: {
        query: fetchDemoList,
      },
    },
    pagerConfig: {
      enabled: true,
      pageSize: 20,
    },
    toolbarConfig: {
      search: true,
      refresh: true,
      zoom: true,
      custom: true,
    },
  },
  formOptions: {
    schema: [
      {
        fieldName: 'title',
        label: $t('demos.demo.title'),
        component: 'Input',
        componentProps: {
          placeholder: $t('demos.demo.searchPlaceholder'),
        },
      },
      {
        fieldName: 'status',
        label: $t('demos.demo.status'),
        component: 'Select',
        componentProps: {
          options: [
            { label: $t('common.all'), value: '' },
            { label: $t('demos.demo.statusDraft'), value: 0 },
            { label: $t('demos.demo.statusPublished'), value: 1 },
            { label: $t('demos.demo.statusArchived'), value: 2 },
          ],
        },
      },
      {
        fieldName: 'priority',
        label: $t('demos.demo.priority'),
        component: 'Select',
        componentProps: {
          options: [
            { label: $t('common.all'), value: '' },
            { label: $t('demos.demo.priorityLow'), value: 0 },
            { label: $t('demos.demo.priorityMedium'), value: 1 },
            { label: $t('demos.demo.priorityHigh'), value: 2 },
          ],
        },
      },
    ],
    showCollapseButton: false,
    submitOnChange: false,
  },
});

type TagType = 'danger' | 'info' | 'success' | 'warning';

const statusMap: Record<number, { label: string; type: TagType }> = {
  0: { label: $t('demos.demo.statusDraft'), type: 'info' },
  1: { label: $t('demos.demo.statusPublished'), type: 'success' },
  2: { label: $t('demos.demo.statusArchived'), type: 'warning' },
};

const priorityMap: Record<number, { label: string; type: TagType }> = {
  0: { label: $t('demos.demo.priorityLow'), type: 'info' },
  1: { label: $t('demos.demo.priorityMedium'), type: 'warning' },
  2: { label: $t('demos.demo.priorityHigh'), type: 'danger' },
};

function handleCreate() {
  demoFormDialogRef.value?.open();
}

async function handleEdit(row: Demo) {
  demoFormDialogRef.value?.open(row);
}

async function handleDelete(row: Demo) {
  try {
    await ElMessageBox.confirm(
      $t('demos.demo.deleteConfirm'),
      $t('demos.demo.delete'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        type: 'warning',
      },
    );
    await deleteDemoApi(row.id);
    ElMessage.success($t('demos.demo.deleteSuccess'));
    gridApi.reload();
  } catch {
    // 用户取消
  }
}

async function handleFormSuccess() {
  gridApi.reload();
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString();
}

async function handleExport() {
  try {
    const blob = await exportDemoExcelApi();
    const url = window.URL.createObjectURL(blob as Blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `demo_export_${Date.now()}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
    ElMessage.success($t('demos.demo.exportExcel'));
  } catch (error) {
    console.error('导出失败:', error);
    ElMessage.error($t('common.error'));
  }
}

async function handleDownloadTemplate() {
  try {
    const blob = await downloadDemoTemplateApi();
    const url = window.URL.createObjectURL(blob as Blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'demo_template.xlsx';
    link.click();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('下载模板失败:', error);
    ElMessage.error($t('common.error'));
  }
}

async function handleImport(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  try {
    const result = await importDemoExcelApi(file);
    ElMessage.success($t('demos.demo.importSuccess'));
    gridApi.reload();
  } catch (error) {
    console.error('导入失败:', error);
    ElMessage.error($t('common.error'));
  } finally {
    input.value = '';
  }
}
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <ElButton type="primary" :icon="Plus" @click="handleCreate">
          {{ $t('demos.demo.create') }}
        </ElButton>
        <ElButton :icon="Download" @click="handleExport">
          {{ $t('demos.demo.exportExcel') }}
        </ElButton>
        <ElButton :icon="Download" @click="handleDownloadTemplate">
          {{ $t('demos.demo.downloadTemplate') }}
        </ElButton>
        <label>
          <ElButton :icon="Upload">
            {{ $t('demos.demo.importExcel') }}
          </ElButton>
          <input
            type="file"
            accept=".xlsx"
            style="display: none"
            @change="handleImport"
          />
        </label>
      </template>

      <template #cell-status="{ row }">
        <ElTag :type="statusMap[row.status]?.type || 'info'" size="small">
          {{ statusMap[row.status]?.label || row.status }}
        </ElTag>
      </template>

      <template #cell-priority="{ row }">
        <ElTag :type="priorityMap[row.priority]?.type || 'info'" size="small">
          {{ priorityMap[row.priority]?.label || row.priority }}
        </ElTag>
      </template>

      <template #cell-is_active="{ row }">
        <ElTag :type="row.is_active ? 'success' : 'info'" size="small">
          {{ row.is_active ? $t('common.enabled') : $t('common.disabled') }}
        </ElTag>
      </template>

      <template #cell-create_time="{ row }">
        {{ formatDate(row.sys_create_datetime) }}
      </template>

      <template #cell-actions="{ row }">
        <ElButton link type="primary" :icon="Edit" @click="handleEdit(row)">
          {{ $t('common.edit') }}
        </ElButton>
        <ElButton link type="danger" :icon="Trash2" @click="handleDelete(row)">
          {{ $t('common.delete') }}
        </ElButton>
      </template>
    </Grid>

    <DemoFormDialog ref="demoFormDialogRef" @success="handleFormSuccess" />
  </Page>
</template>
