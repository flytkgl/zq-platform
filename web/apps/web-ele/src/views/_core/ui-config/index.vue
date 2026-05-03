<script lang="ts" setup>
import type { Component } from 'vue';

import type { CardListItem, CardListOptions } from '#/components/card-list';

import { ref } from 'vue';

import { Page } from '@vben/common-ui';
import { LogIn, Palette, Settings } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElCard, ElScrollbar, ElTooltip } from 'element-plus';

import { CardList } from '#/components/card-list';

import AppSettingsForm from './modules/app-settings-form.vue';
import LoginConfigForm from './modules/login-config-form.vue';
import UIPreferencesForm from './modules/ui-preferences-form.vue';

defineOptions({ name: 'UIConfigManager' });

interface SettingMenuItem extends CardListItem {
  id: string;
  name: string;
  key: 'app' | 'login' | 'ui';
  icon: Component;
}

const menuItems = ref<SettingMenuItem[]>([
  {
    id: 'app',
    name: $t('ui-config.appConfig'),
    key: 'app',
    icon: Settings,
  },
  {
    id: 'ui',
    name: $t('ui-config.styleConfig'),
    key: 'ui',
    icon: Palette,
  },
  {
    id: 'login',
    name: $t('ui-config.loginConfig.title'),
    key: 'login',
    icon: LogIn,
  },
]);

const selectedMenuId = ref<string>('app');

const uiPreferencesFormRef = ref<InstanceType<typeof UIPreferencesForm>>();
const appSettingsFormRef = ref<InstanceType<typeof AppSettingsForm>>();
const loginConfigFormRef = ref<InstanceType<typeof LoginConfigForm>>();
const saving = ref(false);

const cardListOptions: CardListOptions<SettingMenuItem> = {
  searchFields: [{ field: 'name' }],
  titleField: 'name',
  displayMode: 'center',
};

function handleMenuSelect(id: string | undefined) {
  selectedMenuId.value = id || 'ui';
}

function getMenuTitle(key: string): string {
  const item = menuItems.value.find((m) => m.id === key);
  return item?.name || '';
}

function getMenuIcon(key: string): Component | undefined {
  const item = menuItems.value.find((m) => m.id === key);
  return item?.icon;
}

function handleReset() {
  switch (selectedMenuId.value) {
    case 'app': {
      appSettingsFormRef.value?.reset();
      break;
    }
    case 'ui': {
      uiPreferencesFormRef.value?.reset();
      break;
    }
    case 'login': {
      loginConfigFormRef.value?.reset();
      break;
    }
  }
}

async function handleSave() {
  saving.value = true;
  try {
    switch (selectedMenuId.value) {
      case 'app': {
        await appSettingsFormRef.value?.save();
        break;
      }
      case 'ui': {
        await uiPreferencesFormRef.value?.save();
        break;
      }
      case 'login': {
        await loginConfigFormRef.value?.save();
        break;
      }
    }
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full">
      <!-- 左侧菜单 -->
      <div class="mr-3 w-[235px]">
        <CardList
          :items="menuItems"
          :selected-id="selectedMenuId"
          :options="cardListOptions"
          :loading="false"
          class="ui-config-menu"
          @select="handleMenuSelect"
        >
          <template #item="{ item }">
            <div class="flex items-center gap-2 text-sm font-medium">
              <component :is="item.icon" class="size-4" />
              {{ item.name }}
            </div>
          </template>
        </CardList>
      </div>

      <!-- 右侧内容 -->
      <div class="flex-1 overflow-hidden">
        <ElCard shadow="never" class="ui-config-card flex h-full flex-col">
          <template #header>
            <div class="card-header">
              <component
                :is="getMenuIcon(selectedMenuId)"
                class="mr-2 size-5"
              />
              <span>{{ getMenuTitle(selectedMenuId) }}</span>
              <div class="ml-auto flex gap-2">
                <ElTooltip
                  :content="$t('preferences.resetTip')"
                  placement="bottom"
                >
                  <ElButton @click="handleReset">
                    {{ $t('preferences.resetTitle') }}
                  </ElButton>
                </ElTooltip>
                <ElButton type="primary" :loading="saving" @click="handleSave">
                  {{ $t('ui-config.save') }}
                </ElButton>
              </div>
            </div>
          </template>

          <ElScrollbar class="flex-1">
            <!-- UI配置 -->
            <template v-if="selectedMenuId === 'ui'">
              <UIPreferencesForm ref="uiPreferencesFormRef" />
            </template>

            <!-- 应用配置 -->
            <template v-else-if="selectedMenuId === 'app'">
              <AppSettingsForm ref="appSettingsFormRef" />
            </template>

            <!-- 登录配置 -->
            <template v-else-if="selectedMenuId === 'login'">
              <LoginConfigForm ref="loginConfigFormRef" />
            </template>
          </ElScrollbar>
        </ElCard>
      </div>
    </div>
  </Page>
</template>

<style scoped>
.ui-config-menu :deep(.el-card__body) {
  padding: 16px;
}

.ui-config-menu :deep(.mb-4.flex) {
  display: none;
}

.ui-config-menu :deep(.el-form-item__label) {
  font-weight: 500;
}

.ui-config-card {
  border: none;
}

.ui-config-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.card-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
</style>
