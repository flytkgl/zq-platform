<script lang="ts" setup>
import type { User } from '#/api/core';

import { ref } from 'vue';

import { Page } from '@vben/common-ui';
import { Edit, Plus, RotateCw, Trash2 } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElMessage, ElMessageBox, ElTag } from 'element-plus';

import {
  batchDeleteUserApi,
  deleteUserApi,
  getUserListApi,
  resetUserPasswordApi,
} from '#/api/core';
import { UserAvatar } from '#/components/user-avatar';
import { useZqTable } from '#/components/zq-table';

import {
  getGenderOptions,
  getLoginTypeOptions,
  getStatusOptions,
  getUserTypeOptions,
  useSearchFormSchema,
  useZqTableColumns,
} from './data';
import Form from './modules/form.vue';

defineOptions({ name: 'SystemUser' });

const formRef = ref<InstanceType<typeof Form>>();
const selectedRows = ref<User[]>([]);

// 状态映射
const statusOptions = getStatusOptions();
const genderOptions = getGenderOptions();
const userTypeOptions = getUserTypeOptions();
const loginTypeOptions = getLoginTypeOptions();

type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';

function getTagType(value: any, options: any[]): TagType {
  const option = options.find((o) => o.value === value);
  return (option?.type as TagType) || 'info';
}

function getTagLabel(value: any, options: any[]): string {
  const option = options.find((o) => o.value === value);
  return option?.label || String(value);
}

/**
 * 编辑用户
 */
function onEdit(row: User) {
  formRef.value?.open(row);
}

/**
 * 创建新用户
 */
function onCreate() {
  formRef.value?.open();
}

/**
 * 删除单个用户
 */
function onDelete(row: User) {
  if (row.id === 'a0000000-0000-0000-0000-000000000001') {
    ElMessage.warning($t('user.cannotDeleteAdmin'));
    return;
  }

  ElMessageBox.confirm(
    $t('ui.actionMessage.deleteConfirm', [row.name]),
    $t('common.delete'),
    {
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
      type: 'warning',
    },
  )
    .then(async () => {
      try {
        await deleteUserApi(row.id);
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
 * 批量删除用户
 */
function onBatchDelete() {
  if (selectedRows.value.length === 0) {
    ElMessage.warning($t('user.selectUsersToDelete'));
    return;
  }

  // 检查是否包含管理员账户
  const hasAdmin = selectedRows.value.some(
    (row) => row.id === 'a0000000-0000-0000-0000-000000000001',
  );
  if (hasAdmin) {
    ElMessage.warning($t('user.cannotDeleteAdmin'));
    return;
  }

  // 确认删除
  const names = selectedRows.value.map((row: User) => row.name).join('、');
  const confirmMessage = $t('user.batchDeleteConfirm', [
    selectedRows.value.length,
    names,
  ]);

  ElMessageBox.confirm(confirmMessage, $t('user.batchDeleteTitle'), {
    confirmButtonText: $t('common.confirm'),
    cancelButtonText: $t('common.cancel'),
    type: 'warning',
  })
    .then(async () => {
      try {
        const ids = selectedRows.value.map((row: User) => row.id);
        await batchDeleteUserApi({ ids });
        ElMessage.success(
          $t('user.deleteSuccess', [selectedRows.value.length]),
        );
        selectedRows.value = [];
        refreshGrid();
      } catch {
        ElMessage.error($t('user.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

/**
 * 重置密码
 */
function onResetPassword(row: User) {
  if (row.id === 'a0000000-0000-0000-0000-000000000001') {
    ElMessage.warning($t('user.cannotResetAdminPassword'));
    return;
  }

  ElMessageBox.confirm(
    $t('user.resetPasswordConfirm', [row.name]),
    $t('user.resetPasswordTitle'),
    {
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
      type: 'warning',
    },
  )
    .then(async () => {
      try {
        await resetUserPasswordApi(row.id, {
          new_password: 'admin123',
          confirm_password: 'admin123',
        });
        ElMessage.success($t('user.resetPasswordSuccess', [row.name]));
      } catch {
        ElMessage.error($t('user.resetPasswordError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

// 处理选择变化
function handleSelectionChange(items: Record<string, any>[]) {
  // 过滤掉管理员账户
  selectedRows.value = (items as User[]).filter(
    (row) => row.id !== 'a0000000-0000-0000-0000-000000000001',
  );
}

// 列表 API
const fetchUserList = async (params: any) => {
  const res = await getUserListApi({
    page: params.page.currentPage,
    pageSize: params.page.pageSize,
    name: params.form?.name,
    username: params.form?.username,
    last_login_type: params.form?.last_login_type,
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
      autoLoad: true,
      ajax: {
        query: fetchUserList,
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
    schema: useSearchFormSchema(),
    showCollapseButton: true,
    submitOnChange: true,
  },
});

/**
 * 刷新表格
 */
function refreshGrid() {
  gridApi.reload();
}
</script>

<template>
  <Page auto-content-height>
    <Form ref="formRef" @success="refreshGrid" />

    <Grid @selection-change="handleSelectionChange">
      <!-- 工具栏操作 -->
      <template #toolbar-actions>
        <ElButton type="primary" :icon="Plus" @click="onCreate">
          {{ $t('ui.actionTitle.create', [$t('user.name')]) }}
        </ElButton>
        <ElButton type="danger" plain @click="onBatchDelete">
          {{ $t('user.batchDelete') }}
          {{ selectedRows.length > 0 ? `(${selectedRows.length})` : '' }}
        </ElButton>
      </template>

      <!-- 头像列 -->
      <template #cell-avatar="{ row }">
        <div class="flex items-center justify-center">
          <UserAvatar
            :user="row as any"
            :size="34"
            :font-size="16"
            :shadow="false"
          />
        </div>
      </template>

      <!-- 用户类型列 -->
      <template #cell-user_type="{ row }">
        <ElTag :type="getTagType(row.user_type, userTypeOptions)" size="small">
          {{ getTagLabel(row.user_type, userTypeOptions) }}
        </ElTag>
      </template>

      <!-- 性别列 -->
      <template #cell-gender="{ row }">
        <ElTag :type="getTagType(row.gender, genderOptions)" size="small">
          {{ getTagLabel(row.gender, genderOptions) }}
        </ElTag>
      </template>

      <!-- 状态列 -->
      <template #cell-user_status="{ row }">
        <ElTag :type="getTagType(row.user_status, statusOptions)" size="small">
          {{ getTagLabel(row.user_status, statusOptions) }}
        </ElTag>
      </template>

      <!-- 最后登录方式列 -->
      <template #cell-last_login_type="{ row }">
        <ElTag
          v-if="row.last_login_type"
          :type="getTagType(row.last_login_type, loginTypeOptions)"
          size="small"
        >
          {{ getTagLabel(row.last_login_type, loginTypeOptions) }}
        </ElTag>
        <span v-else>-</span>
      </template>

      <!-- 操作列 -->
      <template #cell-actions="{ row }">
        <ElButton link type="primary" :icon="Edit" @click="onEdit(row)">
          {{ $t('common.edit') }}
        </ElButton>
        <ElButton
          link
          type="warning"
          :icon="RotateCw"
          @click="onResetPassword(row)"
        >
          {{ $t('user.resetPassword') }}
        </ElButton>
        <ElButton
          v-if="row.id !== 'a0000000-0000-0000-0000-000000000001'"
          link
          type="danger"
          :icon="Trash2"
          @click="onDelete(row)"
        >
          {{ $t('common.delete') }}
        </ElButton>
      </template>
    </Grid>
  </Page>
</template>
