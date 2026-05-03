<script lang="ts" setup>
import type { CallbackStatus, DingtalkDeptTreeNode, SyncTypeStats } from '#/api/core/dingtalk-sync';

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
  deleteCallbackApi,
  getCallbackStatusApi,
  getDeptTreeApi,
  getSyncConfigApi,
  getSyncStatsApi,
  registerCallbackApi,
  syncDeptApi,
  syncUserApi,
  testConnectionApi,
  updateSyncConfigApi,
} from '#/api/core/dingtalk-sync';

defineOptions({ name: 'DingtalkSyncForm' });

// ==================== 配置表单 ====================
const configForm = ref({
  corp_id: '',
  app_key: '',
  app_secret: '',
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

// ==================== 回调状态 ====================
const callbackStatus = ref<CallbackStatus>({ registered: false });
const registeringCallback = ref(false);

// ==================== 同步统计 ====================
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

// ==================== 触发事件 ====================
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

// ==================== 部门树（同步范围选择） ====================
const deptTreeData = ref<any[]>([]);
const deptTreeLoading = ref(false);
const hasSynced = ref(false);

function transformDeptTree(
  nodes: DingtalkDeptTreeNode[],
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

// ==================== 初始化 ====================
function updateLabels() {
  statsData.value[0]!.typeLabel = $t('dingtalk-sync.syncDept');
  statsData.value[1]!.typeLabel = $t('dingtalk-sync.syncUser');
  eventsData.value[0]!.label = $t('dingtalk-sync.enableSyncDept');
  eventsData.value[0]!.description = $t('dingtalk-sync.enableSyncDeptDesc');
  eventsData.value[1]!.label = $t('dingtalk-sync.enableSyncUser');
  eventsData.value[1]!.description = $t('dingtalk-sync.enableSyncUserDesc');
}

async function loadConfig() {
  loading.value = true;
  try {
    const config = await getSyncConfigApi();
    configForm.value.corp_id = config.corp_id || '';
    configForm.value.app_key = config.app_key || '';
    configForm.value.app_secret = config.app_secret || '';
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

// ==================== 连接测试 ====================
async function handleTestConnection() {
  testing.value = true;
  try {
    await testConnectionApi({
      app_key: configForm.value.app_key,
      app_secret: configForm.value.app_secret,
    });
    ElMessage.success($t('dingtalk-sync.testSuccess'));
    await loadDeptTree();
  } catch {
    ElMessage.error($t('dingtalk-sync.testFail'));
  } finally {
    testing.value = false;
  }
}

// ==================== 加载部门树 ====================
async function loadDeptTree() {
  deptTreeLoading.value = true;
  try {
    const tree = await getDeptTreeApi({
      app_key: configForm.value.app_key,
      app_secret: configForm.value.app_secret,
    });
    deptTreeData.value = transformDeptTree(tree);
  } catch {
    // ignore
  } finally {
    deptTreeLoading.value = false;
  }
}

// ==================== 同步操作 ====================
async function handleSyncDept() {
  syncingDept.value = true;
  try {
    await syncDeptApi();
    ElMessage.success($t('dingtalk-sync.syncDeptSuccess'));
    await loadStats();
  } catch {
    ElMessage.error($t('dingtalk-sync.syncFail'));
  } finally {
    syncingDept.value = false;
  }
}

async function handleSyncUser() {
  syncingUser.value = true;
  try {
    await syncUserApi();
    ElMessage.success($t('dingtalk-sync.syncUserSuccess'));
    await loadStats();
  } catch {
    ElMessage.error($t('dingtalk-sync.syncFail'));
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

// ==================== 保存配置 ====================
async function handleSave() {
  saving.value = true;
  try {
    await updateSyncConfigApi({
      corp_id: configForm.value.corp_id || undefined,
      app_key: configForm.value.app_key || undefined,
      app_secret: configForm.value.app_secret || undefined,
      sync_dept_id: configForm.value.sync_dept_id || undefined,
      sync_root_dept_id: configForm.value.sync_root_dept_id || undefined,
      enable_dept_event: eventsData.value[0]!.enabled ? 'true' : 'false',
      enable_user_event: eventsData.value[1]!.enabled ? 'true' : 'false',
      callback_url: configForm.value.callback_url || undefined,
      callback_token: configForm.value.callback_token || undefined,
      callback_aes_key: configForm.value.callback_aes_key || undefined,
    });
    ElMessage.success($t('dingtalk-sync.saveSuccess'));
  } catch {
    ElMessage.error($t('dingtalk-sync.saveFail'));
  } finally {
    saving.value = false;
  }
}

defineExpose({ save: handleSave, saving });

// ==================== 回调管理 ====================
async function loadCallbackStatus() {
  try {
    callbackStatus.value = await getCallbackStatusApi();
  } catch {
    callbackStatus.value = { registered: false };
  }
}

async function handleRegisterCallback() {
  registeringCallback.value = true;
  try {
    await registerCallbackApi();
    ElMessage.success($t('dingtalk-sync.registerSuccess'));
    await loadCallbackStatus();
  } catch {
    ElMessage.error($t('dingtalk-sync.registerFail'));
  } finally {
    registeringCallback.value = false;
  }
}

async function handleDeleteCallback() {
  registeringCallback.value = true;
  try {
    await deleteCallbackApi();
    ElMessage.success($t('dingtalk-sync.deleteCallbackSuccess'));
    await loadCallbackStatus();
  } catch {
    ElMessage.error($t('dingtalk-sync.deleteCallbackFail'));
  } finally {
    registeringCallback.value = false;
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

// ==================== 格式化时间 ====================
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
          <ElFormItem :label="$t('dingtalk-sync.corpId')">
            <ElInput
              v-model="configForm.corp_id"
              :placeholder="$t('dingtalk-sync.corpIdPlaceholder')"
              clearable
              class="!w-[400px]"
            />
          </ElFormItem>
          <ElFormItem :label="$t('dingtalk-sync.appKey')">
            <ElInput
              v-model="configForm.app_key"
              :placeholder="$t('dingtalk-sync.appKeyPlaceholder')"
              clearable
              class="!w-[400px]"
            />
          </ElFormItem>
          <ElFormItem :label="$t('dingtalk-sync.appSecret')">
            <div class="flex items-center gap-3">
              <ElInput
                v-model="configForm.app_secret"
                :placeholder="$t('dingtalk-sync.appSecretPlaceholder')"
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
                {{ testing ? $t('dingtalk-sync.testing') : $t('dingtalk-sync.testConnection') }}
              </ElButton>
            </div>
          </ElFormItem>

          <!-- 同步范围 -->
          <ElFormItem :label="$t('dingtalk-sync.syncScope')">
            <ElTreeSelect
              v-model="configForm.sync_dept_id"
              :data="deptTreeData"
              :placeholder="$t('dingtalk-sync.syncScopePlaceholder')"
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
            {{ hasSynced ? $t('dingtalk-sync.syncScopeLocked') : $t('dingtalk-sync.syncScopeTip') }}
          </div>
        </ElForm>

        <!-- 同步统计表 -->
        <div>
          <ElTable :data="statsData" border stripe>
            <ElTableColumn
              prop="typeLabel"
              :label="$t('dingtalk-sync.syncType')"
              width="120"
            />
            <ElTableColumn
              prop="total_count"
              :label="$t('dingtalk-sync.totalCount')"
              width="100"
              align="center"
            />
            <ElTableColumn
              prop="success_count"
              :label="$t('dingtalk-sync.successCount')"
              width="120"
              align="center"
            />
            <ElTableColumn
              prop="fail_count"
              :label="$t('dingtalk-sync.failCount')"
              width="120"
              align="center"
            />
            <ElTableColumn
              prop="not_synced"
              :label="$t('dingtalk-sync.notSynced')"
              width="120"
              align="center"
            />
            <ElTableColumn
              :label="$t('dingtalk-sync.syncTime')"
              min-width="180"
            >
              <template #default="{ row }">
                {{ formatTime(row.sync_time) }}
              </template>
            </ElTableColumn>
            <ElTableColumn
              :label="$t('dingtalk-sync.operation')"
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
                  {{ isSyncing(row) ? $t('dingtalk-sync.syncing') : $t('dingtalk-sync.sync') }}
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
            {{ $t('dingtalk-sync.triggerEvents') }}
          </div>
          <ElTable :data="eventsData" border stripe>
            <ElTableColumn width="60" align="center">
              <template #default="{ row }">
                <ElCheckbox v-model="row.enabled" />
              </template>
            </ElTableColumn>
            <ElTableColumn
              prop="label"
              :label="$t('dingtalk-sync.triggerEvent')"
              width="200"
            />
            <ElTableColumn
              prop="description"
              :label="$t('dingtalk-sync.description')"
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
            {{ $t('dingtalk-sync.callbackConfig') }}
          </div>
          <ElAlert
            type="info"
            :closable="false"
            show-icon
            class="!mb-4"
          >
            <template #default>
              {{ $t('dingtalk-sync.callbackConfigTip') }}
            </template>
          </ElAlert>

          <ElForm label-width="120px" label-position="left">
            <ElFormItem :label="$t('dingtalk-sync.callbackUrl')">
              <ElInput
                v-model="configForm.callback_url"
                :placeholder="$t('dingtalk-sync.callbackUrlPlaceholder')"
                clearable
                class="!w-[500px]"
              />
            </ElFormItem>
            <ElFormItem :label="$t('dingtalk-sync.callbackToken')">
              <div class="flex items-center gap-3">
                <ElInput
                  v-model="configForm.callback_token"
                  :placeholder="$t('dingtalk-sync.callbackTokenPlaceholder')"
                  show-password
                  clearable
                  class="!w-[400px]"
                />
                <ElButton @click="generateRandomToken">
                  <template #icon>
                    <KeyRound class="size-4" />
                  </template>
                  {{ $t('dingtalk-sync.generateRandom') }}
                </ElButton>
              </div>
            </ElFormItem>
            <ElFormItem :label="$t('dingtalk-sync.callbackAesKey')">
              <div class="flex items-center gap-3">
                <ElInput
                  v-model="configForm.callback_aes_key"
                  :placeholder="$t('dingtalk-sync.callbackAesKeyPlaceholder')"
                  show-password
                  clearable
                  class="!w-[400px]"
                />
                <ElButton @click="generateRandomAesKey">
                  <template #icon>
                    <KeyRound class="size-4" />
                  </template>
                  {{ $t('dingtalk-sync.generateRandom') }}
                </ElButton>
              </div>
            </ElFormItem>

            <!-- 回调状态 -->
            <ElFormItem :label="$t('dingtalk-sync.callbackStatus')">
              <div class="flex items-center gap-3">
                <ElTag
                  :type="callbackStatus.registered ? 'success' : 'info'"
                >
                  {{ callbackStatus.registered ? $t('dingtalk-sync.callbackRegistered') : $t('dingtalk-sync.callbackNotRegistered') }}
                </ElTag>
                <ElButton
                  v-if="!callbackStatus.registered"
                  type="primary"
                  :loading="registeringCallback"
                  @click="handleRegisterCallback"
                >
                  {{ registeringCallback ? $t('dingtalk-sync.registering') : $t('dingtalk-sync.registerCallback') }}
                </ElButton>
                <ElButton
                  v-else
                  type="danger"
                  :loading="registeringCallback"
                  @click="handleDeleteCallback"
                >
                  {{ $t('dingtalk-sync.deleteCallback') }}
                </ElButton>
              </div>
            </ElFormItem>

            <ElFormItem
              v-if="callbackStatus.registered && callbackStatus.subscribed_events?.length"
              :label="$t('dingtalk-sync.subscribedEvents')"
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
