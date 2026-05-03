<script lang="ts" setup>
import { ref } from 'vue';

import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { ElButton, ElMessage, ElMessageBox } from 'element-plus';

import { addPostUsersApi, removePostUsersApi } from '#/api/core/post';
import { UserListPanel } from '#/components/user-list-panel';
import { UserSelector } from '#/components/zq-form/user-selector';

import PostList from './modules/post-list.vue';

defineOptions({ name: 'SystemPost' });

const currentPostId = ref<string>();
const tempSelectedUsers = ref<Set<string>>(new Set());
const userListPanelRef = ref<InstanceType<typeof UserListPanel>>();

/**
 * 岗位选择事件
 */
function onPostSelect(postId: string | undefined) {
  currentPostId.value = postId;
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
 * 新增用户到岗位（作为 UserSelector 的 onConfirm 回调）
 */
async function handleAddUsers(userIds: string | string[]) {
  if (!currentPostId.value) {
    ElMessage.warning($t('post.selectPostFirst') || '请先选择岗位');
    throw new Error('请先选择岗位');
  }

  const userIdsArray = Array.isArray(userIds) ? userIds : [userIds];

  if (userIdsArray.length === 0) {
    ElMessage.warning($t('post.selectUsersFirst') || '请先选择用户');
    throw new Error('请先选择用户');
  }

  await addPostUsersApi(currentPostId.value, {
    user_ids: userIdsArray,
  });

  ElMessage.success($t('post.addUsersSuccess') || '添加成功');
  // 刷新用户列表
  userListPanelRef.value?.reload();
}

/**
 * 从岗位删除用户
 */
async function handleRemoveUsers() {
  if (!currentPostId.value) {
    ElMessage.warning($t('post.selectPostFirst') || '请先选择岗位');
    return;
  }

  if (tempSelectedUsers.value.size === 0) {
    ElMessage.warning($t('post.selectUsersFirst') || '请先选择用户');
    return;
  }

  const userIds = [...tempSelectedUsers.value];
  const confirmMessage =
    $t('post.removeUsersConfirm', [tempSelectedUsers.value.size]) ||
    `确定要删除选中的 ${tempSelectedUsers.value.size} 个用户吗？`;

  try {
    await ElMessageBox.confirm(confirmMessage, $t('common.delete') || '删除', {
      confirmButtonText: $t('common.confirm') || '确定',
      cancelButtonText: $t('common.cancel') || '取消',
      type: 'warning',
    });

    await removePostUsersApi(currentPostId.value, {
      user_ids: userIds,
    });
    ElMessage.success($t('post.removeUsersSuccess') || '删除成功');
    tempSelectedUsers.value.clear();
    // 刷新用户列表
    userListPanelRef.value?.reload();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to remove users:', error);
      ElMessage.error($t('post.removeUsersFailed') || '删除失败');
    }
  }
}
</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full">
      <!-- 岗位列表 -->
      <div class="mr-3 w-1/6">
        <PostList @select="onPostSelect" />
      </div>

      <!-- 主内容区：用户列表 -->
      <div class="w-5/6">
        <UserListPanel
          ref="userListPanelRef"
          :data-source="currentPostId ? 'post' : 'all'"
          :source-id="currentPostId"
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
                :disabled="!currentPostId"
                display-mode="button"
                :placeholder="$t('common.add') || '新增'"
                :on-confirm="handleAddUsers"
              />
              <ElButton
                type="danger"
                plain
                :disabled="!currentPostId || tempSelectedUsers.size === 0"
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
