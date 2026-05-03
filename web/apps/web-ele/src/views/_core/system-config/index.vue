<script lang="ts" setup>
import type { CardListItem, CardListOptions } from '#/components/card-list';
import type { ZqTabItem } from '#/components/zq-tabs';

import { computed, onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';
import {
  BellRing,
  Bot,
  CircleHelp,
  IconifyIcon,
  RefreshCw,
  Shield,
} from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElMessage,
  ElMessageBox,
  ElScrollbar,
} from 'element-plus';

import {
  deleteGroupConfigApi,
  getAllConfigsApi,
} from '#/api/core/system-config';
import { CardList } from '#/components/card-list';
import { ZqDialog } from '#/components/zq-dialog';
import { ZqTabs } from '#/components/zq-tabs';

import ConfigForm from './modules/config-form.vue';
import DingtalkSyncForm from './modules/dingtalk-sync-form.vue';
import FeishuSyncForm from './modules/feishu-sync-form.vue';
import WecomSyncForm from './modules/wecom-sync-form.vue';

defineOptions({ name: 'SystemConfigManager' });

interface ConfigMenuItem extends CardListItem {
  id: string;
  name: string;
  group: string;
  icon: string;
  category: 'notify' | 'oauth' | 'sync';
}

const SSO_GROUPS = [
  'oauth_gitee',
  'oauth_github',
  'oauth_qq',
  'oauth_google',
  'oauth_wechat',
  'oauth_microsoft',
  'oauth_dingtalk',
  'oauth_feishu',
  'oauth_wecom',
];

const NOTIFY_GROUPS = [
  'notify_email',
  'notify_sms',
  'notify_dingtalk',
  'notify_feishu',
  'notify_wecom',
  'notify_wechat_mp',
];

const SYNC_GROUPS = [
  'sync_dingtalk',
  'sync_wecom',
  'sync_feishu',
];

const GROUP_ICONS: Record<string, string> = {
  oauth_gitee: 'simple-icons:gitee',
  oauth_github: 'simple-icons:github',
  oauth_qq: 'simple-icons:tencentqq',
  oauth_google: 'simple-icons:google',
  oauth_wechat: 'simple-icons:wechat',
  oauth_microsoft: 'simple-icons:microsoft',
  oauth_dingtalk: 'ri:dingding-line',
  oauth_feishu: 'simple-icons:bytedance',
  oauth_wecom: 'simple-icons:wechat',
  notify_email: 'mdi:email-outline',
  notify_sms: 'mdi:message-text-outline',
  notify_dingtalk: 'ri:dingding-line',
  notify_feishu: 'simple-icons:bytedance',
  notify_wecom: 'simple-icons:wechat',
  notify_wechat_mp: 'simple-icons:wechat',
  sync_dingtalk: 'ri:dingding-line',
  sync_wecom: 'simple-icons:wechat',
  sync_feishu: 'simple-icons:bytedance',
};

const activeTab = ref<string>('oauth');
const allConfigs = ref<Record<string, Record<string, any>>>({});
const selectedMenuId = ref<string>('oauth_gitee');
const loading = ref(false);
const saving = ref(false);
const configFormRef = ref<InstanceType<typeof ConfigForm>>();
const syncFormRef = ref<InstanceType<typeof DingtalkSyncForm>>();
const wecomSyncFormRef = ref<InstanceType<typeof WecomSyncForm>>();
const feishuSyncFormRef = ref<InstanceType<typeof FeishuSyncForm>>();
const syncSaving = ref(false);
const showGuideDialog = ref(false);

const menuItems = computed<ConfigMenuItem[]>(() => {
  const items: ConfigMenuItem[] = [];

  for (const group of SSO_GROUPS) {
    items.push({
      id: group,
      name: $t(`system-config.groups.${group}`),
      group,
      icon: GROUP_ICONS[group] || 'mdi:key',
      category: 'oauth',
    });
  }

  for (const group of NOTIFY_GROUPS) {
    items.push({
      id: group,
      name: $t(`system-config.groups.${group}`),
      group,
      icon: GROUP_ICONS[group] || 'mdi:bell-ring',
      category: 'notify',
    });
  }

  for (const group of SYNC_GROUPS) {
    items.push({
      id: group,
      name: $t(`system-config.groups.${group}`),
      group,
      icon: GROUP_ICONS[group] || 'mdi:sync',
      category: 'sync',
    });
  }

  return items;
});

const currentItems = computed(() =>
  menuItems.value.filter((i) => i.category === activeTab.value),
);

const selectedItem = computed(() =>
  menuItems.value.find((i) => i.id === selectedMenuId.value),
);

const modelConfigFormRef = ref<InstanceType<typeof ModelConfigForm>>();

const tabItems = computed<ZqTabItem[]>(() => [
  { key: 'oauth', label: $t('system-config.ssoConfig'), icon: Shield },
  { key: 'notify', label: $t('system-config.notifyConfig'), icon: BellRing },
  // { key: 'model', label: $t('system-config.modelConfig'), icon: Bot },
  { key: 'sync', label: $t('system-config.syncConfig'), icon: RefreshCw },
]);

const cardListOptions: CardListOptions<ConfigMenuItem> = {
  searchFields: [{ field: 'name' }],
  titleField: 'name',
  displayMode: 'center',
};

async function loadAllConfigs() {
  loading.value = true;
  try {
    allConfigs.value = await getAllConfigsApi();
  } catch {
    // ignore
  } finally {
    loading.value = false;
  }
}

function handleMenuSelect(id: string | undefined) {
  if (id) {
    selectedMenuId.value = id;
  }
}

function handleTabChange(tab: string) {
  activeTab.value = tab;
  const items = menuItems.value.filter((i) => i.category === tab);
  if (items.length > 0 && !items.some((i) => i.id === selectedMenuId.value)) {
    selectedMenuId.value = items[0]!.id;
  }
}

async function handleSave() {
  saving.value = true;
  try {
    await configFormRef.value?.save();
  } finally {
    saving.value = false;
  }
}

async function handleReset() {
  try {
    await ElMessageBox.confirm(
      $t('system-config.resetConfirm'),
      $t('system-config.reset'),
      { type: 'warning' },
    );
    await deleteGroupConfigApi(selectedMenuId.value);
    ElMessage.success($t('system-config.resetSuccess'));
    await loadAllConfigs();
  } catch {
    // cancelled
  }
}

function handleSaved() {
  loadAllConfigs();
}

async function handleSyncSave() {
  syncSaving.value = true;
  try {
    if (selectedMenuId.value === 'sync_wecom') {
      await wecomSyncFormRef.value?.save();
    } else if (selectedMenuId.value === 'sync_feishu') {
      await feishuSyncFormRef.value?.save();
    } else {
      await syncFormRef.value?.save();
    }
  } finally {
    syncSaving.value = false;
  }
}

onMounted(() => {
  loadAllConfigs();
});
</script>

<template>
  <Page auto-content-height>
    <div class="flex h-full">
      <!-- 左侧竖向 Tab -->
      <div class="bg-background mr-3 flex-shrink-0 rounded-[8px] p-4">
        <ZqTabs
          v-model="activeTab"
          :items="tabItems"
          vertical
          @change="handleTabChange"
        />
      </div>

      <!-- 列表（oauth/notify/sync tab 显示） -->
      <template v-if="activeTab !== 'model'">
        <div class="mr-3 w-[250px] flex-shrink-0">
          <ElCard shadow="never" class="h-full !border-none">
            <ElScrollbar>
              <CardList
                :items="currentItems"
                :selected-id="selectedMenuId"
                :options="cardListOptions"
                :loading="false"
                class="config-menu"
                @select="handleMenuSelect"
              >
                <template #item="{ item }">
                  <div class="flex items-center gap-2 text-sm">
                    <IconifyIcon :icon="item.icon" class="size-4 opacity-60" />
                    {{ item.name }}
                  </div>
                </template>
              </CardList>
            </ElScrollbar>
          </ElCard>
        </div>

        <!-- 右侧内容 -->
        <div class="flex-1 overflow-hidden">
          <!-- 同步配置 -->
          <template v-if="activeTab === 'sync'">
            <ElCard
              shadow="never"
              class="config-card flex h-full flex-col !border-none"
            >
              <template #header>
                <div class="card-header">
                  <IconifyIcon
                    :icon="selectedItem?.icon || ''"
                    class="mr-2 size-5 opacity-60"
                  />
                  <span>{{ selectedItem?.name }}</span>
                  <div class="ml-auto flex items-center gap-2">
                    <CircleHelp
                      class="size-5 cursor-pointer opacity-50 transition-opacity hover:opacity-100"
                      @click="showGuideDialog = true"
                    />
                    <ElButton
                      type="primary"
                      :loading="syncSaving"
                      @click="handleSyncSave"
                    >
                      {{ $t('system-config.save') }}
                    </ElButton>
                  </div>
                </div>
              </template>
              <DingtalkSyncForm
                v-if="selectedMenuId === 'sync_dingtalk'"
                ref="syncFormRef"
              />
              <WecomSyncForm
                v-else-if="selectedMenuId === 'sync_wecom'"
                ref="wecomSyncFormRef"
              />
              <FeishuSyncForm
                v-else-if="selectedMenuId === 'sync_feishu'"
                ref="feishuSyncFormRef"
              />
            </ElCard>

            <!-- 配置步骤弹窗 -->
            <ZqDialog
              v-model="showGuideDialog"
              :title="selectedMenuId === 'sync_wecom' ? $t('wecom-sync.guideTitle') : selectedMenuId === 'sync_feishu' ? $t('feishu-sync.guideTitle') : $t('dingtalk-sync.guideTitle')"
              width="680px"
              :show-footer="false"
              max-height="70vh"
            >
              <div class="space-y-5 px-2 py-1">
                <div
                  v-for="(step, idx) in (selectedMenuId === 'sync_wecom' ? 5 : selectedMenuId === 'sync_feishu' ? 5 : 6)"
                  :key="`${selectedMenuId}-${idx}`"
                  class="flex gap-3"
                >
                  <div
                    class="flex size-7 flex-shrink-0 items-center justify-center rounded-full text-sm font-semibold text-white"
                    style="background-color: var(--el-color-primary)"
                  >
                    {{ idx + 1 }}
                  </div>
                  <div class="flex-1">
                    <div
                      class="mb-1 text-sm font-semibold"
                      style="color: var(--el-text-color-primary)"
                    >
                      {{ selectedMenuId === 'sync_wecom'
                        ? $t(`wecom-sync.guideStep${idx + 1}Title`)
                        : selectedMenuId === 'sync_feishu'
                          ? $t(`feishu-sync.guideStep${idx + 1}Title`)
                          : $t(`dingtalk-sync.guideStep${idx + 1}Title`)
                      }}
                    </div>
                    <div
                      class="text-sm leading-relaxed"
                      style="color: var(--el-text-color-secondary)"
                    >
                      {{ selectedMenuId === 'sync_wecom'
                        ? $t(`wecom-sync.guideStep${idx + 1}Desc`)
                        : selectedMenuId === 'sync_feishu'
                          ? $t(`feishu-sync.guideStep${idx + 1}Desc`)
                          : $t(`dingtalk-sync.guideStep${idx + 1}Desc`)
                      }}
                    </div>
                  </div>
                </div>
              </div>
            </ZqDialog>
          </template>

          <!-- SSO/通知配置：通用表单 -->
          <template v-else>
            <ElCard
              shadow="never"
              class="config-card flex h-full flex-col !border-none"
            >
              <template #header>
                <div class="card-header">
                  <IconifyIcon
                    :icon="selectedItem?.icon || ''"
                    class="mr-2 size-5 opacity-60"
                  />
                  <span>{{ selectedItem?.name }}</span>
                  <div class="ml-auto flex gap-2">
                    <ElButton @click="handleReset">
                      {{ $t('system-config.reset') }}
                    </ElButton>
                    <ElButton
                      type="primary"
                      :loading="saving"
                      @click="handleSave"
                    >
                      {{ $t('system-config.save') }}
                    </ElButton>
                  </div>
                </div>
              </template>

              <ElScrollbar class="flex-1">
                <ConfigForm
                  ref="configFormRef"
                  :group="selectedMenuId"
                  :config-data="allConfigs[selectedMenuId] || {}"
                  :loading="loading"
                  @saved="handleSaved"
                />
              </ElScrollbar>
            </ElCard>
          </template>
        </div>
      </template>

      <!-- 模型配置（model tab） -->
      <div v-else class="flex-1 overflow-hidden">
        <ModelConfigForm ref="modelConfigFormRef" />
      </div>
    </div>
  </Page>
</template>

<style scoped>
.config-menu :deep(.el-card__body) {
  padding: 0;
}

.config-menu :deep(.mb-4.flex) {
  display: none;
}

.config-card :deep(.el-card__body) {
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
