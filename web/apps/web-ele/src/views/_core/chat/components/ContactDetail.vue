<script setup lang="ts">
import type { User } from '#/api/core/user';

import { onMounted, ref, watch } from 'vue';

import { MessageSquare, Network } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElSkeleton, ElSkeletonItem, ElTooltip } from 'element-plus';

import { getUserDetailApi } from '#/api/core/user';
import DeptTag from '#/components/dept-tag/index.vue';
import PostTag from '#/components/post-tag/index.vue';
import RoleTag from '#/components/role-tag/index.vue';
import UserAvatar from '#/components/user-avatar/index.vue';
import UserProfileDialog from '#/components/user-avatar/UserProfileDialog.vue';

const props = defineProps<{
  onlineUsers?: Set<string>;
  userId: string;
}>();

const emit = defineEmits<{
  startChat: [user: User];
}>();

const loading = ref(false);
const userDetail = ref<User>();
const profileDialogVisible = ref(false);

async function loadUserDetail() {
  if (!props.userId) return;
  loading.value = true;
  try {
    userDetail.value = await getUserDetailApi(props.userId);
  } catch (error) {
    console.error('加载用户详情失败:', error);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadUserDetail();
});

watch(
  () => props.userId,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      userDetail.value = undefined;
      loadUserDetail();
    }
  },
);
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 加载骨架屏 -->
    <div v-if="loading" class="flex flex-1 items-center justify-center">
      <ElSkeleton animated :loading="true">
        <template #template>
          <div class="flex flex-col items-center px-6">
            <ElSkeletonItem
              variant="circle"
              style="width: 80px; height: 80px"
            />
            <ElSkeletonItem
              variant="text"
              style="width: 120px; margin-top: 16px"
            />
            <ElSkeletonItem
              variant="text"
              style="width: 80px; margin-top: 6px"
            />
            <div class="mt-4 flex flex-col items-center gap-2">
              <ElSkeletonItem variant="text" style="width: 160px" />
              <ElSkeletonItem variant="text" style="width: 140px" />
            </div>
            <div class="mt-6 flex gap-6">
              <ElSkeletonItem
                variant="circle"
                style="width: 44px; height: 44px"
              />
              <ElSkeletonItem
                variant="circle"
                style="width: 44px; height: 44px"
              />
            </div>
          </div>
        </template>
      </ElSkeleton>
    </div>

    <template v-else-if="userDetail">
      <div class="flex flex-1 items-center justify-center">
        <div class="flex flex-col items-center px-6">
          <!-- 头像 -->
          <UserAvatar
            :user-id="userDetail.id"
            :name="userDetail.name || userDetail.username"
            :avatar="userDetail.avatar"
            :size="80"
            :font-size="32"
            :shadow="true"
            :show-popover="false"
          />

          <!-- 姓名 & 用户名 -->
          <div class="mt-4 text-center">
            <div class="flex items-center justify-center gap-2">
              <span
                class="text-lg font-semibold text-[var(--el-text-color-primary)]"
              >
                {{ userDetail.name || userDetail.username }}
              </span>
              <!-- <span
                class="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[11px] leading-none"
                :class="props.onlineUsers?.has(userDetail.id)
                  ? 'bg-[var(--el-color-success-light-9)] text-[var(--el-color-success)]'
                  : 'bg-[var(--el-fill-color)] text-[var(--el-text-color-placeholder)]'"
              >
                <span
                  class="inline-block h-1.5 w-1.5 rounded-full"
                  :class="props.onlineUsers?.has(userDetail.id)
                    ? 'bg-[var(--el-color-success)]'
                    : 'bg-[var(--el-text-color-placeholder)]'"
                />
                {{ props.onlineUsers?.has(userDetail.id) ? $t('chat.online') : $t('chat.offline') }}
              </span> -->
            </div>
            <div class="mt-0.5 text-xs text-[var(--el-text-color-secondary)]">
              @{{ userDetail.username }}
            </div>
            <div
              v-if="userDetail.bio"
              class="mt-2 max-w-[280px] text-xs leading-relaxed text-[var(--el-text-color-placeholder)]"
            >
              {{ userDetail.bio }}
            </div>
          </div>

          <!-- 详细信息 -->
          <div class="contact-details">
            <div v-if="userDetail.email" class="detail-row">
              <span class="detail-label">邮箱</span>
              <span class="detail-value">{{ userDetail.email }}</span>
            </div>
            <div v-if="userDetail.mobile" class="detail-row">
              <span class="detail-label">手机</span>
              <span class="detail-value">{{ userDetail.mobile }}</span>
            </div>
            <div v-if="userDetail.city" class="detail-row">
              <span class="detail-label">城市</span>
              <span class="detail-value">{{ userDetail.city }}</span>
            </div>
            <div v-if="userDetail.dept_id" class="detail-row">
              <span class="detail-label">部门</span>
              <span class="detail-value">
                <DeptTag :dept-id="userDetail.dept_id" />
              </span>
            </div>
            <div v-if="userDetail.post_id" class="detail-row">
              <span class="detail-label">岗位</span>
              <span class="detail-value">
                <PostTag :post-id="userDetail.post_id" />
              </span>
            </div>
            <div
              v-if="userDetail.role_ids && userDetail.role_ids.length > 0"
              class="detail-row"
            >
              <span class="detail-label">角色</span>
              <span class="detail-value">
                <RoleTag :role-ids="userDetail.role_ids" />
              </span>
            </div>
            <div v-if="userDetail.manager_id" class="detail-row">
              <span class="detail-label">经理</span>
              <span class="detail-value">
                <UserAvatar
                  :user-id="userDetail.manager_id"
                  :size="20"
                  :font-size="10"
                  :shadow="false"
                  show-info
                  hide-username
                  info-position="right"
                />
              </span>
            </div>
          </div>

          <!-- 操作按钮组 -->
          <div class="mt-6 flex items-center justify-center gap-6">
            <ElTooltip :content="$t('chat.startChat')" placement="bottom">
              <button class="action-btn" @click="emit('startChat', userDetail)">
                <MessageSquare class="h-5 w-5" />
              </button>
            </ElTooltip>
            <ElTooltip :content="$t('chat.contactOrg')" placement="bottom">
              <button class="action-btn" @click="profileDialogVisible = true">
                <Network class="h-5 w-5" />
              </button>
            </ElTooltip>
          </div>
        </div>
      </div>
    </template>

    <!-- 组织架构弹窗 -->
    <UserProfileDialog
      v-if="userId"
      v-model="profileDialogVisible"
      :user-id="userId"
    />
  </div>
</template>

<style scoped>
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  transition: all 0.2s;
}

.action-btn:hover {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.action-btn--primary {
  color: #fff;
  background: var(--el-color-primary);
}

.action-btn--primary:hover {
  background: var(--el-color-primary-light-3);
  color: #fff;
}

.contact-details {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 280px;
  margin-top: 16px;
  padding-top: 1px;
}

.detail-row {
  display: flex;
  align-items: center;
  padding: 6px 0;
  font-size: 13px;
}

.detail-label {
  flex-shrink: 0;
  width: 48px;
  color: var(--el-text-color-secondary);
  text-align: right;
  margin-right: 8px;
}

.detail-value {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}
</style>
