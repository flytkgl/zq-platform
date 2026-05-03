<script lang="ts" setup>
import type { CallbackStatus, FeishuDeptTreeNode, SyncTypeStats } from '#/api/core/feishu-sync';

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
} from '#/api/core/feishu-sync';

defineOptions({ name: 'FeishuSyncForm' });

// ==================== 配置表单 ====================
const configForm = ref({
  app_id: '',
  app_secret: '',
  sync_dept_id: '',
  sync_root_dept_id: '',
  enable_dept_event: '',
  enable_user_event: '',
  callback_url: '',
  encrypt_key: '',
  verification_token: '',
});

const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const syncingDept = ref(false);
const syncingUser = ref(false);

// ==================== 回调状态 ====================
const callbackStatus = ref<CallbackStatus>({ registered: false });

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
  nodes: FeishuDeptTreeNode[],
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
  statsData.value[0]!.typeLabel = $t('feishu-sync.syncDept');
  statsData.value[1]!.typeLabel = $t('feishu-sync.syncUser');
  eventsData.value[0]!.label = $t('feishu-sync.enableSyncDept');
  eventsData.value[0]!.description = $t('feishu-sync.enableSyncDeptDesc');
  eventsData.value[1]!.label = $t('feishu-sync.enableSyncUser');
  eventsData.value[1]!.description = $t('feishu-sync.enableSyncUserDesc');
}

async function loadConfig() {
  loading.value = true;
  try {
    const config = await getSyncConfigApi();
    configForm.value.app_id = config.app_id || '';
    configForm.value.app_secret = config.app_secret || '';
    configForm.value.sync_dept_id = config.sync_dept_id || '';
    configForm.value.sync_root_dept_id = config.sync_root_dept_id || '';
    configForm.value.enable_dept_event = config.enable_dept_event || '';
    configForm.value.enable_user_event = config.enable_user_event || '';
    configForm.value.callback_url = config.callback_url || '';
    configForm.value.encrypt_key = config.encrypt_key || '';
    configForm.value.verification_token = config.verification_token || '';

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
      app_id: configForm.value.app_id,
      app_secret: configForm.value.app_secret,
    });
    ElMessage.success($t('feishu-sync.testSuccess'));
    await loadDeptTree();
  } catch {
    ElMessage.error($t('feishu-sync.testFail'));
  } finally {
    testing.value = false;
  }
}

// ==================== 加载部门树 ====================
async function loadDeptTree() {
  deptTreeLoading.value = true;
  try {
    const tree = await getDeptTreeApi({
      app_id: configForm.value.app_id,
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
    ElMessage.success($t('feishu-sync.syncDeptSuccess'));
    await loadStats();
  } catch {
    ElMessage.error($t('feishu-sync.syncFail'));
  } finally {
    syncingDept.value = false;
  }
}

async function handleSyncUser() {
  syncingUser.value = true;
  try {
    await syncUserApi();
    ElMessage.success($t('feishu-sync.syncUserSuccess'));
    await loadStats();
  } catch {
    ElMessage.error($t('feishu-sync.syncFail'));
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
      app_id: configForm.value.app_id || undefined,
      app_secret: configForm.value.app_secret || undefined,
      sync_dept_id: configForm.value.sync_dept_id || undefined,
      sync_root_dept_id: configForm.value.sync_root_dept_id || undefined,
      enable_dept_event: eventsData.value[0]!.enabled ? 'true' : 'false',
      enable_user_event: eventsData.value[1]!.enabled ? 'true' : 'false',
      callback_url: configForm.value.callback_url || undefined,
      encrypt_key: configForm.value.encrypt_key || undefined,
      verification_token: configForm.value.verification_token || undefined,
    });
    ElMessage.success($t('feishu-sync.saveSuccess'));
  } catch {
    ElMessage.error($t('feishu-sync.saveFail'));
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

function generateRandomEncryptKey() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const arr = new Uint8Array(32);
  crypto.getRandomValues(arr);
  configForm.value.encrypt_key = Array.from(arr, (b) => chars[b % chars.length]).join('');
}

function generateRandomVerificationToken() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const arr = new Uint8Array(32);
  crypto.getRandomValues(arr);
  configForm.value.verification_token = Array.from(arr, (b) => chars[b % chars.length]).join('');
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
          <ElFormItem :label="$t('feishu-sync.appId')">
            <ElInput
              v-model="configForm.app_id"
              :placeholder="$t('feishu-sync.appIdPlaceholder')"
              clearable
              class="!w-[400px]"
            />
          </ElFormItem>
          <ElFormItem :label="$t('feishu-sync.appSecret')">
            <div class="flex items-center gap-3">
              <ElInput
                v-model="configForm.app_secret"
                :placeholder="$t('feishu-sync.appSecretPlaceholder')"
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
                {{ testing ? $t('feishu-sync.testing') : $t('feishu-sync.testConnection') }}
              </ElButton>
            </div>
          </ElFormItem>

          <!-- 同步范围 -->
          <ElFormItem :label="$t('feishu-sync.syncScope')">
            <ElTreeSelect
              v-model="configForm.sync_dept_id"
              :data="deptTreeData"
              :placeholder="$t('feishu-sync.syncScopePlaceholder')"
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
            {{ hasSynced ? $t('feishu-sync.syncScopeLocked') : $t('feishu-sync.syncScopeTip') }}
          </div>
        </ElForm>

        <!-- 同步统计表 -->
        <div>
          <ElTable :data="statsData" border stripe>
            <ElTableColumn
              prop="typeLabel"
              :label="$t('feishu-sync.syncType')"
              width="120"
            />
            <ElTableColumn
              prop="total_count"
              :label="$t('feishu-sync.totalCount')"
              width="100"
              align="center"
            />
            <ElTableColumn
              prop="success_count"
              :label="$t('feishu-sync.successCount')"
              width="120"
              align="center"
            />
            <ElTableColumn
              prop="fail_count"
              :label="$t('feishu-sync.failCount')"
              width="120"
              align="center"
            />
            <ElTableColumn
              prop="not_synced"
              :label="$t('feishu-sync.notSynced')"
              width="120"
              align="center"
            />
            <ElTableColumn
              :label="$t('feishu-sync.syncTime')"
              min-width="180"
            >
              <template #default="{ row }">
                {{ formatTime(row.sync_time) }}
              </template>
            </ElTableColumn>
            <ElTableColumn
              :label="$t('feishu-sync.operation')"
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
                  {{ isSyncing(row) ? $t('feishu-sync.syncing') : $t('feishu-sync.sync') }}
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
            {{ $t('feishu-sync.triggerEvents') }}
          </div>
          <ElTable :data="eventsData" border stripe>
            <ElTableColumn width="60" align="center">
              <template #default="{ row }">
                <ElCheckbox v-model="row.enabled" />
              </template>
            </ElTableColumn>
            <ElTableColumn
              prop="label"
              :label="$t('feishu-sync.triggerEvent')"
              width="200"
            />
            <ElTableColumn
              prop="description"
              :label="$t('feishu-sync.description')"
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
            {{ $t('feishu-sync.callbackConfig') }}
          </div>
          <ElAlert
            type="info"
            :closable="false"
            show-icon
            class="!mb-4"
          >
            <template #default>
              {{ $t('feishu-sync.callbackConfigTip') }}
            </template>
          </ElAlert>

          <ElForm label-width="120px" label-position="left">
            <ElFormItem :label="$t('feishu-sync.callbackUrl')">
              <ElInput
                v-model="configForm.callback_url"
                :placeholder="$t('feishu-sync.callbackUrlPlaceholder')"
                clearable
                class="!w-[500px]"
              />
            </ElFormItem>
            <ElFormItem :label="$t('feishu-sync.encryptKey')">
              <div class="flex items-center gap-3">
                <ElInput
                  v-model="configForm.encrypt_key"
                  :placeholder="$t('feishu-sync.encryptKeyPlaceholder')"
                  show-password
                  clearable
                  class="!w-[400px]"
                />
                <ElButton @click="generateRandomEncryptKey">
                  <template #icon>
                    <KeyRound class="size-4" />
                  </template>
                  {{ $t('feishu-sync.generateRandom') }}
                </ElButton>
              </div>
            </ElFormItem>
            <ElFormItem :label="$t('feishu-sync.verificationToken')">
              <div class="flex items-center gap-3">
                <ElInput
                  v-model="configForm.verification_token"
                  :placeholder="$t('feishu-sync.verificationTokenPlaceholder')"
                  show-password
                  clearable
                  class="!w-[400px]"
                />
                <ElButton @click="generateRandomVerificationToken">
                  <template #icon>
                    <KeyRound class="size-4" />
                  </template>
                  {{ $t('feishu-sync.generateRandom') }}
                </ElButton>
              </div>
            </ElFormItem>

            <!-- 回调状态 -->
            <ElFormItem :label="$t('feishu-sync.callbackStatus')">
              <div class="flex items-center gap-3">
                <ElTag
                  :type="callbackStatus.registered ? 'success' : 'info'"
                >
                  {{ callbackStatus.registered ? $t('feishu-sync.callbackConfigured') : $t('feishu-sync.callbackNotConfigured') }}
                </ElTag>
              </div>
            </ElFormItem>

            <ElFormItem
              v-if="callbackStatus.registered && callbackStatus.subscribed_events?.length"
              :label="$t('feishu-sync.subscribedEvents')"
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
