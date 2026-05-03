<script lang="ts" setup>
import type { Permission } from '#/api/core/permission';

import { ref, watch } from 'vue';

import { Edit, Plus, Trash2, Zap } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElMessage, ElMessageBox, ElTag } from 'element-plus';

import {
  batchDeletePermissionApi,
  deletePermissionApi,
  getPermissionListApi,
} from '#/api/core/permission';
import { useZqTable } from '#/components/zq-table';

import { getSearchFormSchema, useZqTableColumns } from '../data';
import AutoGenerateModal from './auto-generate-modal.vue';

interface Props {
  menuId?: string;
  menuName?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  add: [permission?: Permission];
}>();

const selectedRows = ref<Permission[]>([]);
const currentMenuId = ref<string>();
const autoGenerateModalRef = ref<InstanceType<typeof AutoGenerateModal>>();

// 权限类型映射
const permissionTypeMap: Record<number, { label: string; type: string }> = {
  1: { label: $t('permission.typeLabels.api'), type: 'success' },
  3: { label: $t('permission.typeLabels.other'), type: 'info' },
};

// HTTP 方法映射
const httpMethodMap: Record<number, { label: string; type: string }> = {
  0: { label: 'GET', type: 'success' },
  1: { label: 'POST', type: 'primary' },
  2: { label: 'PUT', type: 'warning' },
  3: { label: 'DELETE', type: 'danger' },
  4: { label: 'PATCH', type: 'info' },
  5: { label: 'ALL', type: '' },
};

// 监听 props 变化，更新当前菜单 ID
watch(
  () => props.menuId,
  (newMenuId) => {
    currentMenuId.value = newMenuId;
  },
);

/**
 * 编辑权限
 */
function onEdit(row: Permission) {
  emit('add', row);
}

/**
 * 删除单个权限
 */
function onDelete(row: Permission) {
  ElMessageBox.confirm(
    $t('permission.deleteConfirm', [row.name]),
    $t('common.tips'),
    {
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
      type: 'warning',
      showClose: false,
    },
  )
    .then(async () => {
      try {
        await deletePermissionApi(row.id);
        ElMessage.success($t('ui.actionMessage.deleteSuccess', [row.name]));
        refreshGrid();
      } catch {
        ElMessage.error($t('ui.actionMessage.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

/**
 * 批量删除权限
 */
function onBatchDelete() {
  if (selectedRows.value.length === 0) {
    ElMessage.warning($t('permission.selectToDelete'));
    return;
  }

  const names = selectedRows.value
    .map((row: Permission) => row.name)
    .join('、');

  ElMessageBox.confirm(
    $t('permission.batchDeleteConfirm', [selectedRows.value.length, names]),
    $t('common.tips'),
    {
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
      type: 'warning',
      showClose: false,
    },
  )
    .then(async () => {
      try {
        const ids = selectedRows.value.map((row: Permission) => row.id);
        await batchDeletePermissionApi({ ids });
        ElMessage.success(
          $t('permission.batchDeleteSuccess', [selectedRows.value.length]),
        );
        selectedRows.value = [];
        refreshGrid();
      } catch {
        ElMessage.error($t('permission.batchDeleteFailed'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

// 处理选择变化
function handleSelectionChange(items: Record<string, any>[]) {
  selectedRows.value = items as Permission[];
}

/**
 * 菜单选择事件
 */
function onMenuSelect(menuId: string | undefined) {
  currentMenuId.value = menuId;
  selectedRows.value = [];
  refreshGrid();
}

/**
 * 打开自动生成权限 Modal
 */
function onAutoScan() {
  if (!currentMenuId.value) {
    ElMessage.warning($t('permission.selectMenuFirst'));
    return;
  }

  autoGenerateModalRef.value?.open({
    menuId: currentMenuId.value,
    menuName: props.menuName || '',
  });
}

/**
 * 权限生成成功回调
 */
function onAutoGenerateSuccess() {
  refreshGrid();
}

// 列表 API
const fetchPermissionList = async (params: any) => {
  if (!currentMenuId.value) {
    return { items: [], total: 0 };
  }
  const res = await getPermissionListApi({
    page: params.page.currentPage,
    pageSize: params.page.pageSize,
    menu_id: currentMenuId.value,
    name: params.form?.name,
    code: params.form?.code,
  });
  return {
    items: res.items,
    total: res.total,
  };
};

// 使用 ZqTable
const [Grid, gridApi] = useZqTable({
  gridOptions: {
    columns: useZqTableColumns(),
    border: true,
    stripe: true,
    showSelection: true,
    showIndex: true,
    proxyConfig: {
      autoLoad: false,
      ajax: {
        query: fetchPermissionList,
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
    schema: getSearchFormSchema(),
    showCollapseButton: false,
    submitOnChange: false,
  },
});

/**
 * 刷新表格
 */
function refreshGrid() {
  gridApi.reload();
}
watch(
  () => props.menuId,
  (newMenuId) => {
    if (newMenuId) {
      onMenuSelect(newMenuId);
    }
  },
);

// 暴露公共方法
defineExpose({
  loadPermissions: refreshGrid,
});
</script>

<template>
  <Grid @selection-change="handleSelectionChange">
    <!-- 工具栏操作 -->
    <template #toolbar-actions>
      <ElButton type="primary" :icon="Plus" @click="emit('add')">
        {{ $t('permission.add') }}
      </ElButton>
      <ElButton type="success" :icon="Zap" @click="onAutoScan">
        {{ $t('permission.quickAddApiPermission') }}
      </ElButton>
      <ElButton type="danger" plain @click="onBatchDelete">
        {{ $t('permission.batchDelete') }}
        {{ selectedRows.length > 0 ? `(${selectedRows.length})` : '' }}
      </ElButton>
    </template>

    <!-- 权限类型列 -->
    <template #cell-permission_type="{ row }">
      <ElTag
        v-if="permissionTypeMap[row.permission_type]"
        :type="permissionTypeMap[row.permission_type].type as any"
        size="small"
      >
        {{ permissionTypeMap[row.permission_type].label }}
      </ElTag>
      <span v-else>{{ $t('permission.typeLabels.unknown') }}</span>
    </template>

    <!-- HTTP 方法列 -->
    <template #cell-http_method="{ row }">
      <template v-if="row.permission_type === 1">
        <ElTag
          v-if="httpMethodMap[row.http_method]"
          :type="httpMethodMap[row.http_method].type as any"
          size="small"
        >
          {{ httpMethodMap[row.http_method].label }}
        </ElTag>
        <span v-else>UNKNOWN</span>
      </template>
      <span v-else>-</span>
    </template>

    <!-- 操作列 -->
    <template #cell-actions="{ row }">
      <ElButton link type="primary" :icon="Edit" @click="onEdit(row)">
        {{ $t('common.edit') }}
      </ElButton>
      <ElButton link type="danger" :icon="Trash2" @click="onDelete(row)">
        {{ $t('common.delete') }}
      </ElButton>
    </template>
  </Grid>

  <!-- 自动生成权限 Modal -->
  <AutoGenerateModal
    ref="autoGenerateModalRef"
    @success="onAutoGenerateSuccess"
  />
</template>
