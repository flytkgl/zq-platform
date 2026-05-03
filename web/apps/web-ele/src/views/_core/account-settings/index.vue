<script lang="ts" setup>
import type { User } from '#/api/core';
import type { CardListItem, CardListOptions } from '#/components/card-list';

import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { ElCard, ElMessage } from 'element-plus';

import { getCurrentUserProfileApi } from '#/api/core';
import { CardList } from '#/components/card-list';

import ApiTokenManagement from './api-token-management.vue';
import DeviceManagement from './device-management.vue';
import PasswordForm from './modules/password-form.vue';
import ProfileForm from './modules/profile-form.vue';

defineOptions({ name: 'AccountSettings' });

// 菜单项类型
interface SettingMenuItem extends CardListItem {
  id: string;
  name: string;
  key: 'apiToken' | 'device' | 'password' | 'profile';
}

// 菜单项数据
const menuItems = ref<SettingMenuItem[]>([
  {
    id: 'profile',
    name: $t('user.basicInfo'),
    key: 'profile',
  },
  {
    id: 'password',
    name: $t('user.changePassword'),
    key: 'password',
  },
  {
    id: 'device',
    name: $t('apiToken.deviceManagement'),
    key: 'device',
  },
  {
    id: 'apiToken',
    name: $t('apiToken.title'),
    key: 'apiToken',
  },
]);

const loading = ref(false);
const selectedMenuId = ref<string>('profile');
const userProfile = ref<null | User>(null);

// CardList 配置
const cardListOptions: CardListOptions<SettingMenuItem> = {
  searchFields: [{ field: 'name' }],
  titleField: 'name',
  displayMode: 'center', // 一行居中显示
};

/**
 * 处理菜单选择
 */
function handleMenuSelect(id: string | undefined) {
  selectedMenuId.value = id || 'profile';
}

/**
 * 加载当前用户信息
 */
async function loadUserProfile() {
  loading.value = true;
  try {
    const data = await getCurrentUserProfileApi();
    userProfile.value = data;
  } catch {
    ElMessage.error($t('user.loadProfileError'));
  } finally {
    loading.value = false;
  }
}

/**
 * 处理表单成功回调
 */
async function handleFormSuccess() {
  await loadUserProfile();
}

onMounted(() => {
  loadUserProfile();
});
</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full">
      <!-- 左侧菜单 -->
      <div class="w-1/6">
        <CardList
          :items="menuItems"
          :selected-id="selectedMenuId"
          :options="cardListOptions"
          :loading="false"
          class="account-settings-menu"
          @select="handleMenuSelect"
        >
          <template #item="{ item }">
            <div class="text-sm font-medium">{{ item.name }}</div>
          </template>
        </CardList>
      </div>

      <!-- 右侧表单 -->
      <div class="flex-1">
        <ElCard shadow="never" class="h-full">
          <template #header>
            <div class="card-header">
              <span>
                {{
                  selectedMenuId === 'profile'
                    ? $t('user.basicInfo')
                    : selectedMenuId === 'password'
                      ? $t('user.changePassword')
                      : selectedMenuId === 'device'
                        ? $t('apiToken.deviceManagement')
                        : $t('apiToken.title')
                }}
              </span>
            </div>
          </template>
          <!-- 基本信息表单 -->
          <template v-if="selectedMenuId === 'profile'">
            <ProfileForm
              :user-profile="userProfile"
              @success="handleFormSuccess"
            />
          </template>

          <!-- 修改密码表单 -->
          <template v-else-if="selectedMenuId === 'password'">
            <PasswordForm @success="handleFormSuccess" />
          </template>

          <!-- 设备管理 -->
          <template v-else-if="selectedMenuId === 'device'">
            <DeviceManagement />
          </template>

          <!-- API Token 管理 -->
          <template v-else-if="selectedMenuId === 'apiToken'">
            <ApiTokenManagement />
          </template>
        </ElCard>
      </div>
    </div>
  </Page>
</template>

<style scoped>
.account-settings-menu :deep(.el-card__body) {
  padding: 16px;
}

/* 隐藏搜索和添加按钮 */
.account-settings-menu :deep(.mb-4.flex) {
  display: none;
}

.account-settings-menu :deep(.el-form-item__label) {
  font-weight: 500;
}

.card-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
</style>
