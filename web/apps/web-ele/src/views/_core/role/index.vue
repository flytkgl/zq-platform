<script lang="ts" setup>
import type { Role } from '#/api/core/role';

import { nextTick, ref } from 'vue';

import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { ElButton, ElMessage, ElMessageBox } from 'element-plus';

import {
  addRoleUsersApi,
  getRoleDetailApi,
  removeRoleUsersApi,
} from '#/api/core/role';
import { UserListPanel } from '#/components/user-list-panel';
import { UserSelector } from '#/components/zq-form/user-selector';

import PermissionAssignPanel from './modules/permission-assign-panel.vue';
import RoleList from './modules/role-list.vue';

defineOptions({ name: 'SystemRole' });

const currentRole = ref<Role>();

// 右侧面板模式：permission-权限配置, users-用户列表
type PanelMode = 'permission' | 'users';
const panelMode = ref<PanelMode>('permission');
const usersRole = ref<Role>();
const tempSelectedUsers = ref<Set<string>>(new Set());
const userListPanelRef = ref<InstanceType<typeof UserListPanel>>();

/**
 * 角色选择事件
 */
async function onRoleSelect(roleId: string | undefined) {
  panelMode.value = 'permission';
  if (roleId) {
    try {
      const role = await getRoleDetailApi(roleId);
      currentRole.value = role;
    } catch (error) {
      console.error($t('role.permissions.getRoleDetailFailed'), error);
      currentRole.value = undefined;
    }
  } else {
    currentRole.value = undefined;
  }
}

/**
 * 显示角色用户面板
 */
function onShowUsers(role: Role) {
  usersRole.value = role;
  tempSelectedUsers.value.clear();
  panelMode.value = 'users';
  nextTick(() => {
    userListPanelRef.value?.reload();
  });
}

/**
 * 处理用户选择
 */
function handleUserSelect(userId: string) {
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
 * 新增用户到角色
 */
async function handleAddUsers(userIds: string | string[]) {
  if (!usersRole.value?.id) {
    ElMessage.warning($t('role.permissions.noRoleSelected'));
    throw new Error('No role selected');
  }
  const userIdsArray = Array.isArray(userIds) ? userIds : [userIds];
  if (userIdsArray.length === 0) return;

  await addRoleUsersApi(usersRole.value.id, { user_ids: userIdsArray });
  ElMessage.success($t('role.addUsersSuccess'));
  userListPanelRef.value?.reload();
}

/**
 * 从角色移除用户
 */
async function handleRemoveUsers() {
  if (!usersRole.value?.id || tempSelectedUsers.value.size === 0) return;

  const userIds = [...tempSelectedUsers.value];
  try {
    await ElMessageBox.confirm(
      $t('role.removeUsersConfirm', [tempSelectedUsers.value.size]),
      $t('common.delete'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        type: 'warning',
      },
    );
    await removeRoleUsersApi(usersRole.value.id, { user_ids: userIds });
    ElMessage.success($t('role.removeUsersSuccess'));
    tempSelectedUsers.value.clear();
    userListPanelRef.value?.reload();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to remove users:', error);
      ElMessage.error($t('role.removeUsersFailed'));
    }
  }
}

/**
 * 权限分配成功
 */
function onPermissionSuccess() {
  // 权限分配成功，可以在这里做其他操作
}
</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full">
      <!-- 左侧：角色列表 -->
      <div class="mr-3 w-1/6">
        <RoleList @select="onRoleSelect" @show-users="onShowUsers" />
      </div>

      <!-- 右侧：权限配置面板 -->
      <div v-if="panelMode === 'permission'" class="w-5/6">
        <PermissionAssignPanel
          :role="currentRole"
          @success="onPermissionSuccess"
        />
      </div>

      <!-- 右侧：用户列表面板 -->
      <div v-else-if="panelMode === 'users'" class="w-5/6">
        <UserListPanel
          ref="userListPanelRef"
          :data-source="usersRole?.id ? 'role' : 'all'"
          :source-id="usersRole?.id"
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
              <!-- <span class="text-sm font-medium">
                {{ usersRole?.name }} - {{ $t('role.users') }}
              </span> -->
              <UserSelector
                :multiple="true"
                :disabled="!usersRole?.id"
                display-mode="button"
                :placeholder="$t('common.add')"
                :on-confirm="handleAddUsers"
              />
              <ElButton
                type="danger"
                plain
                :disabled="!usersRole?.id || tempSelectedUsers.size === 0"
                @click="handleRemoveUsers"
              >
                {{ $t('common.delete') }}
              </ElButton>
            </div>
          </template>
        </UserListPanel>
      </div>
    </div>
  </Page>
</template>
