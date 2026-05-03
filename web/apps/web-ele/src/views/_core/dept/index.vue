<script lang="ts" setup>
import { ref } from 'vue';

import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { ElButton, ElMessage, ElMessageBox } from 'element-plus';

import { addDeptUsersApi, removeDeptUsersApi } from '#/api/core/dept';
import { UserListPanel } from '#/components/user-list-panel';
import { UserSelector } from '#/components/zq-form/user-selector';

import DeptTree from './modules/dept-tree.vue';

defineOptions({ name: 'SystemDept' });

const currentDeptId = ref<string>();
const tempSelectedUsers = ref<Set<string>>(new Set());
const userListPanelRef = ref<InstanceType<typeof UserListPanel>>();

/**
 * 部门选择事件
 */
function onDeptSelect(deptIds: string[] | undefined) {
  currentDeptId.value = deptIds?.[0];
  tempSelectedUsers.value.clear();
}

/**
 * 处理用户选择
 */
function handleUserSelect(userId: string, _user: any) {
  if (tempSelectedUsers.value.has(userId)) {
    tempSelectedUsers.value.delete(userId);
  } else {
    tempSelectedUsers.value.add(userId);
  }
}

/**
 * 处理移除用户
 */
function handleRemoveUser(userId: string) {
  tempSelectedUsers.value.delete(userId);
}

/**
 * 新增用户到部门（作为 UserSelector 的 onConfirm 回调）
 */
async function handleAddUsers(userIds: string | string[]) {
  if (!currentDeptId.value) {
    ElMessage.warning($t('dept.selectDeptFirst') || '请先选择部门');
    throw new Error('请先选择部门');
  }

  const userIdsArray = Array.isArray(userIds) ? userIds : [userIds];

  if (userIdsArray.length === 0) {
    ElMessage.warning($t('dept.selectUsersFirst') || '请先选择用户');
    throw new Error('请先选择用户');
  }

  await addDeptUsersApi(currentDeptId.value, {
    user_ids: userIdsArray,
  });

  ElMessage.success($t('dept.addUsersSuccess') || '添加成功');
  // 刷新用户列表
  userListPanelRef.value?.reload();
}

/**
 * 从部门删除用户
 */
async function handleRemoveUsers() {
  if (!currentDeptId.value) {
    ElMessage.warning($t('dept.selectDeptFirst') || '请先选择部门');
    return;
  }

  if (tempSelectedUsers.value.size === 0) {
    ElMessage.warning($t('dept.selectUsersFirst') || '请先选择用户');
    return;
  }

  const userIds = [...tempSelectedUsers.value];
  const confirmMessage =
    $t('dept.removeUsersConfirm', [tempSelectedUsers.value.size]) ||
    `确定要删除选中的 ${tempSelectedUsers.value.size} 个用户吗？`;

  try {
    await ElMessageBox.confirm(confirmMessage, $t('common.delete') || '删除', {
      confirmButtonText: $t('common.confirm') || '确定',
      cancelButtonText: $t('common.cancel') || '取消',
      type: 'warning',
    });

    await removeDeptUsersApi(currentDeptId.value, {
      user_ids: userIds,
    });
    ElMessage.success($t('dept.removeUsersSuccess') || '删除成功');
    tempSelectedUsers.value.clear();
    // 刷新用户列表
    userListPanelRef.value?.reload();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to remove users:', error);
      ElMessage.error($t('dept.removeUsersFailed') || '删除失败');
    }
  }
}
</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full">
      <!-- 部门树 -->
      <div class="w-1/6">
        <DeptTree @select="onDeptSelect" />
      </div>

      <!-- 主内容区：用户列表 -->
      <div class="w-5/6">
        <UserListPanel
          ref="userListPanelRef"
          :data-source="currentDeptId ? 'dept' : 'all'"
          :source-id="currentDeptId"
          :temp-selected-users="tempSelectedUsers"
          :filterable="true"
          :multiple="true"
          :selectable="true"
          :show-selected-tags="false"
          :show-border="false"
          @user-select="handleUserSelect"
          @remove-user="handleRemoveUser"
        >
          <template #title>
            <div class="flex items-center gap-2">
              <UserSelector
                :multiple="true"
                :disabled="!currentDeptId"
                display-mode="button"
                :placeholder="$t('common.add') || '新增'"
                :on-confirm="handleAddUsers"
              />
              <ElButton
                type="danger"
                :disabled="!currentDeptId || tempSelectedUsers.size === 0"
                @click="handleRemoveUsers"
              >
                {{ $t('common.delete') || '删除' }}
              </ElButton>
            </div>
          </template>
        </UserListPanel>
      </div>
    </div>
  </Page>
</template>
