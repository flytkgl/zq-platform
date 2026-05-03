<script lang="ts" setup>
import type { CallbackStatus, SyncTypeStats, WecomDeptTreeNode } from '#/api/core/wecom-sync';

import { onMounted, ref } from 'vue';

import { KeyRound, Link2, RefreshCw, Webhook } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElAlert,
  ElButton,
  ElCheckbox,
  ElDivider,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElScrollbar,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTreeSelect,
} from 'element-plus';

import {
  getCallbackStatusApi,
  getDeptTreeApi,
  getSyncConfigApi,
  getSyncStatsApi,
  syncDeptApi,
  syncUserApi,
  testConnectionApi,
  updateSyncConfigApi,
} from '#/api/core/wecom-sync';

defineOptions({ name: 'WecomSyncForm' });

const configForm = ref({
  corp_id: '',
  corp_secret: '',
  sync_dept_id: '',
  sync_root_dept_id: '',
  enable_dept_event: '',
  enable_user_event: '',
  callback_url: '',
  callback_token: '',
  callback_aes_key: '',
});

const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const syncingDept = ref(false);
const syncingUser = ref(false);

const callbackStatus = ref<CallbackStatus>({ registered: false });

interface StatsRow {
  type: string;
  typeLabel: string;
  total_count: number;
  success_count: number;
  fail_count: number;
  not_synced: number;
  sync_time: null | string;
}

const statsData = ref<StatsRow[]>([
  {
    type: 'dept',
    typeLabel: '',
    total_count: 0,
    success_count: 0,
    fail_count: 0,
    not_synced: 0,
    sync_time: null,
  },
  {
    type: 'user',
    typeLabel: '',
    total_count: 0,
    success_count: 0,
    fail_count: 0,
    not_synced: 0,
    sync_time: null,
  },
]);

interface EventRow {
  key: string;
  label: string;
  description: string;
  enabled: boolean;
}

const eventsData = ref<EventRow[]>([
  {
    key: 'enable_dept_event',
    label: '',
    description: '',
    enabled: false,
  },
  {
    key: 'enable_user_event',
    label: '',
    description: '',
    enabled: false,
  },
]);

const deptTreeData = ref<any[]>([]);
const deptTreeLoading = ref(false);
const hasSynced = ref(false);

function transformDeptTree(
  nodes: WecomDeptTreeNode[],
): Array<{ children?: any[]; label: string; value: string }> {
  return nodes.map((node) => ({
    value: String(node.dept_id),
    label: node.name,
    children:
      node.children && node.children.length > 0
        ? transformDeptTree(node.children)
        : undefined,
  }));
}

function updateLabels() {
  statsData.value[0]!.typeLabel = $t('wecom-sync.syncDept');
  statsData.value[1]!.typeLabel = $t('wecom-sync.syncUser');
  eventsData.value[0]!.label = $t('wecom-sync.enableSyncDept');
  eventsData.value[0]!.description = $t('wecom-sync.enableSyncDeptDesc');
  eventsData.value[1]!.label = $t('wecom-sync.enableSyncUser');
  eventsData.value[1]!.description = $t('wecom-sync.enableSyncUserDesc');
}

async function loadConfig() {
  loading.value = true;
  try {
    const config = await getSyncConfigApi();
    configForm.value.corp_id = config.corp_id || '';
    configForm.value.corp_secret = config.corp_secret || '';
    configForm.value.sync_dept_id = config.sync_dept_id || '';
    configForm.value.sync_root_dept_id = config.sync_root_dept_id || '';
    configForm.value.enable_dept_event = config.enable_dept_event || '';
    configForm.value.enable_user_event = config.enable_user_event || '';
    configForm.value.callback_url = config.callback_url || '';
    configForm.value.callback_token = config.callback_token || '';
    configForm.value.callback_aes_key = config.callback_aes_key || '';

    eventsData.value[0]!.enabled = config.enable_dept_event === 'true';
    eventsData.value[1]!.enabled = config.enable_user_event === 'true';
  } catch {
    // ignore
  } finally {
    loading.value = false;
  }
}

async function loadStats() {
  try {
    const stats = await getSyncStatsApi();
    const deptStats: SyncTypeStats = stats.dept;
    const userStats: SyncTypeStats = stats.user;

    statsData.value[0] = {
      ...statsData.value[0]!,
      total_count: deptStats.total_count,
      success_count: deptStats.success_count,
      fail_count: deptStats.fail_count,
      not_synced: deptStats.not_synced,
      sync_time: deptStats.sync_time,
    };
    statsData.value[1] = {
      ...statsData.value[1]!,
      total_count: userStats.total_count,
      success_count: userStats.success_count,
      fail_count: userStats.fail_count,
      not_synced: userStats.not_synced,
      sync_time: userStats.sync_time,
    };

    hasSynced.value = deptStats.success_count > 0;
  } catch {
    // ignore
  }
}

async function handleTestConnection() {
  testing.value = true;
  try {
    await testConnectionApi({
      corp_id: configForm.value.corp_id,
      corp_secret: configForm.value.corp_secret,
    });
    ElMessage.success($t('wecom-sync.testSuccess'));
    await loadDeptTree();
  } catch {
    ElMessage.error($t('wecom-sync.testFail'));
  } finally {
    testing.value = false;
  }
}

async function loadDeptTree() {
  deptTreeLoading.value = true;
  try {
    const tree = await getDeptTreeApi({
      corp_id: configForm.value.corp_id,
      corp_secret: configForm.value.corp_secret,
    });
    deptTreeData.value = transformDeptTree(tree);
  } catch {
    // ignore
  } finally {
    deptTreeLoading.value = false;
  }
}

async function handleSyncDept() {
  syncingDept.value = true;
  try {
    await syncDeptApi();
    ElMessage.success($t('wecom-sync.syncDeptSuccess'));
    await loadStats();
  } catch {
    ElMessage.error($t('wecom-sync.syncFail'));
  } finally {
    syncingDept.value = false;
  }
}

async function handleSyncUser() {
  syncingUser.value = true;
  try {
    await syncUserApi();
    ElMessage.success($t('wecom-sync.syncUserSuccess'));
    await loadStats();
  } catch {
    ElMessage.error($t('wecom-sync.syncFail'));
  } finally {
    syncingUser.value = false;
  }
}

function handleSync(row: StatsRow) {
  if (row.type === 'dept') {
    handleSyncDept();
  } else {
    handleSyncUser();
  }
}

function isSyncing(row: StatsRow): boolean {
  return row.type === 'dept' ? syncingDept.value : syncingUser.value;
}

async function handleSave() {
  saving.value = true;
  try {
    await updateSyncConfigApi({
      corp_id: configForm.value.corp_id || undefined,
      corp_secret: configForm.value.corp_secret || undefined,
      sync_dept_id: configForm.value.sync_dept_id || undefined,
      sync_root_dept_id: configForm.value.sync_root_dept_id || undefined,
      enable_dept_event: eventsData.value[0]!.enabled ? 'true' : 'false',
      enable_user_event: eventsData.value[1]!.enabled ? 'true' : 'false',
      callback_url: configForm.value.callback_url || undefined,
      callback_token: configForm.value.callback_token || undefined,
      callback_aes_key: configForm.value.callback_aes_key || undefined,
    });
    ElMessage.success($t('wecom-sync.saveSuccess'));
  } catch {
    ElMessage.error($t('wecom-sync.saveFail'));
  } finally {
    saving.value = false;
  }
}

defineExpose({ save: handleSave, saving });

async function loadCallbackStatus() {
  try {
    callbackStatus.value = await getCallbackStatusApi();
  } catch {
    callbackStatus.value = { registered: false };
  }
}

function generateRandomToken() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const arr = new Uint8Array(32);
  crypto.getRandomValues(arr);
  configForm.value.callback_token = Array.from(arr, (b) => chars[b % chars.length]).join('');
}

function generateRandomAesKey() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const arr = new Uint8Array(43);
  crypto.getRandomValues(arr);
  configForm.value.callback_aes_key = Array.from(arr, (b) => chars[b % chars.length]).join('');
}

function formatTime(val: null | string): string {
  if (!val) return '';
  try {
    return new Date(val).toLocaleString();
  } catch {
    return val;
  }
}

onMounted(async () => {
  updateLabels();
  await loadConfig();
  await Promise.all([loadStats(), loadCallbackStatus()]);
});
</script>

<template>
  <div class="flex h-full flex-col">
    <ElScrollbar class="flex-1">
      <div v-loading="loading" class="space-y-6 p-6">
        <!-- 凭证配置 -->
        <ElForm label-width="120px" label-position="left">
          <ElFormItem :label="$t('wecom-sync.corpId')">
            <ElInput
              v-model="configForm.corp_id"
              :placeholder="$t('wecom-sync.corpIdPlaceholder')"
              clearable
              class="!w-[400px]"
            />
          </ElFormItem>
          <ElFormItem :label="$t('wecom-sync.corpSecret')">
            <div class="flex items-center gap-3">
              <ElInput
                v-model="configForm.corp_secret"
                :placeholder="$t('wecom-sync.corpSecretPlaceholder')"
                show-password
                clearable
                class="!w-[400px]"
              />
              <ElButton
                :loading="testing"
                @click="handleTestConnection"
              >
                <template v-if="!testing" #icon>
                  <Link2 class="size-4" />
                </template>
                {{ testing ? $t('wecom-sync.testing') : $t('wecom-sync.testConnection') }}
              </ElButton>
            </div>
          </ElFormItem>

          <!-- 同步范围 -->
          <ElFormItem :label="$t('wecom-sync.syncScope')">
            <ElTreeSelect
              v-model="configForm.sync_dept_id"
              :data="deptTreeData"
              :placeholder="$t('wecom-sync.syncScopePlaceholder')"
              :loading="deptTreeLoading"
              :disabled="hasSynced"
              check-strictly
              filterable
              class="!w-[400px]"
              node-key="value"
              :props="{ label: 'label', children: 'children' }"
            />
          </ElFormItem>
          <div
            class="mb-6 ml-[120px] text-xs"
            style="color: var(--el-text-color-secondary)"
          >
            {{ hasSynced ? $t('wecom-sync.syncScopeLocked') : $t('wecom-sync.syncScopeTip') }}
          </div>
        </ElForm>

        <!-- 同步统计表 -->
        <div>
          <ElTable :data="statsData" border stripe>
            <ElTableColumn
              prop="typeLabel"
              :label="$t('wecom-sync.syncType')"
              width="120"
            />
            <ElTableColumn
              prop="total_count"
              :label="$t('wecom-sync.totalCount')"
              width="100"
              align="center"
            />
            <ElTableColumn
              prop="success_count"
              :label="$t('wecom-sync.successCount')"
              width="120"
              align="center"
            />
            <ElTableColumn
              prop="fail_count"
              :label="$t('wecom-sync.failCount')"
              width="120"
              align="center"
            />
            <ElTableColumn
              prop="not_synced"
              :label="$t('wecom-sync.notSynced')"
              width="120"
              align="center"
            />
            <ElTableColumn
              :label="$t('wecom-sync.syncTime')"
              min-width="180"
            >
              <template #default="{ row }">
                {{ formatTime(row.sync_time) }}
              </template>
            </ElTableColumn>
            <ElTableColumn
              :label="$t('wecom-sync.operation')"
              width="100"
              align="center"
              fixed="right"
            >
              <template #default="{ row }">
                <ElButton
                  type="primary"
                  link
                  :loading="isSyncing(row)"
                  @click="handleSync(row)"
                >
                  <template v-if="!isSyncing(row)" #icon>
                    <RefreshCw class="size-3.5" />
                  </template>
                  {{ isSyncing(row) ? $t('wecom-sync.syncing') : $t('wecom-sync.sync') }}
                </ElButton>
              </template>
            </ElTableColumn>
          </ElTable>
        </div>

        <!-- 触发事件 -->
        <div>
          <div
            class="mb-3 text-sm font-medium"
            style="color: var(--el-text-color-primary)"
          >
            {{ $t('wecom-sync.triggerEvents') }}
          </div>
          <ElTable :data="eventsData" border stripe>
            <ElTableColumn width="60" align="center">
              <template #default="{ row }">
                <ElCheckbox v-model="row.enabled" />
              </template>
            </ElTableColumn>
            <ElTableColumn
              prop="label"
              :label="$t('wecom-sync.triggerEvent')"
              width="200"
            />
            <ElTableColumn
              prop="description"
              :label="$t('wecom-sync.description')"
            />
          </ElTable>
        </div>

        <!-- 事件回调配置 -->
        <ElDivider />
        <div>
          <div
            class="mb-2 flex items-center gap-2 text-sm font-medium"
            style="color: var(--el-text-color-primary)"
          >
            <Webhook class="size-4" />
            {{ $t('wecom-sync.callbackConfig') }}
          </div>
          <ElAlert
            type="info"
            :closable="false"
            show-icon
            class="!mb-4"
          >
            <template #default>
              {{ $t('wecom-sync.callbackConfigTip') }}
            </template>
          </ElAlert>

          <ElForm label-width="120px" label-position="left">
            <ElFormItem :label="$t('wecom-sync.callbackUrl')">
              <ElInput
                v-model="configForm.callback_url"
                :placeholder="$t('wecom-sync.callbackUrlPlaceholder')"
                clearable
                class="!w-[500px]"
              />
            </ElFormItem>
            <ElFormItem :label="$t('wecom-sync.callbackToken')">
              <div class="flex items-center gap-3">
                <ElInput
                  v-model="configForm.callback_token"
                  :placeholder="$t('wecom-sync.callbackTokenPlaceholder')"
                  show-password
                  clearable
                  class="!w-[400px]"
                />
                <ElButton @click="generateRandomToken">
                  <template #icon>
                    <KeyRound class="size-4" />
                  </template>
                  {{ $t('wecom-sync.generateRandom') }}
                </ElButton>
              </div>
            </ElFormItem>
            <ElFormItem :label="$t('wecom-sync.callbackAesKey')">
              <div class="flex items-center gap-3">
                <ElInput
                  v-model="configForm.callback_aes_key"
                  :placeholder="$t('wecom-sync.callbackAesKeyPlaceholder')"
                  show-password
                  clearable
                  class="!w-[400px]"
                />
                <ElButton @click="generateRandomAesKey">
                  <template #icon>
                    <KeyRound class="size-4" />
                  </template>
                  {{ $t('wecom-sync.generateRandom') }}
                </ElButton>
              </div>
            </ElFormItem>

            <!-- 回调状态 -->
            <ElFormItem :label="$t('wecom-sync.callbackStatus')">
              <div class="flex items-center gap-3">
                <ElTag
                  :type="callbackStatus.registered ? 'success' : 'info'"
                >
                  {{ callbackStatus.registered ? $t('wecom-sync.callbackRegistered') : $t('wecom-sync.callbackNotRegistered') }}
                </ElTag>
              </div>
            </ElFormItem>

            <ElFormItem
              v-if="callbackStatus.registered && callbackStatus.subscribed_events?.length"
              :label="$t('wecom-sync.subscribedEvents')"
            >
              <div class="flex flex-wrap gap-1">
                <ElTag
                  v-for="event in callbackStatus.subscribed_events"
                  :key="event"
                  size="small"
                >
                  {{ event }}
                </ElTag>
              </div>
            </ElFormItem>
          </ElForm>
        </div>
      </div>
    </ElScrollbar>
  </div>
</template>
