<script lang="ts" setup>
import type { ApiTokenApi } from '#/api/core/api-token';

import { computed, onMounted, ref } from 'vue';

import { $t } from '@vben/locales';
import { Copy, KeyRound, Plus, Trash2 } from '@vben/icons';

import {
  ElAlert,
  ElButton,
  ElDatePicker,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElTag,
  ElTooltip,
} from 'element-plus';

import {
  createApiTokenApi,
  getApiTokenListApi,
  revokeApiTokenApi,
} from '#/api/core/api-token';
import { ZqDialog } from '#/components/zq-dialog';

defineOptions({ name: 'ApiTokenManagement' });

const tokens = ref<ApiTokenApi.TokenItem[]>([]);
const loading = ref(false);

const createDialogVisible = ref(false);
const createLoading = ref(false);
const createForm = ref<ApiTokenApi.CreateTokenRequest>({
  name: '',
  expires_at: null,
  description: '',
});

const createdToken = ref<null | string>(null);
const showTokenDialog = ref(false);
const tokenCopied = ref(false);

async function loadTokens() {
  loading.value = true;
  try {
    tokens.value = await getApiTokenListApi();
  } catch {
    ElMessage.error($t('apiToken.loadError'));
  } finally {
    loading.value = false;
  }
}

function openCreateDialog() {
  createForm.value = { name: '', expires_at: null, description: '' };
  createDialogVisible.value = true;
}

async function handleCreate() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning($t('apiToken.nameRequired'));
    return;
  }

  createLoading.value = true;
  try {
    const payload: ApiTokenApi.CreateTokenRequest = {
      name: createForm.value.name.trim(),
      description: createForm.value.description || undefined,
    };
    if (createForm.value.expires_at) {
      payload.expires_at = new Date(
        createForm.value.expires_at,
      ).toISOString();
    }
    const result = await createApiTokenApi(payload);
    createdToken.value = result.token;
    tokenCopied.value = false;
    createDialogVisible.value = false;
    showTokenDialog.value = true;
    await loadTokens();
  } catch {
    ElMessage.error($t('apiToken.createError'));
  } finally {
    createLoading.value = false;
  }
}

async function handleRevoke(token: ApiTokenApi.TokenItem) {
  try {
    await ElMessageBox.confirm(
      $t('apiToken.revokeConfirm', [token.name]),
      $t('apiToken.revokeTitle'),
      { type: 'warning', confirmButtonText: $t('apiToken.confirmRevoke') },
    );
    await revokeApiTokenApi(token.id);
    ElMessage.success($t('apiToken.revokeSuccess'));
    await loadTokens();
  } catch {
    // cancelled
  }
}

async function copyToken() {
  if (!createdToken.value) return;
  try {
    await navigator.clipboard.writeText(createdToken.value);
    tokenCopied.value = true;
    ElMessage.success($t('apiToken.copySuccess'));
  } catch {
    ElMessage.error($t('apiToken.copyError'));
  }
}

function getExpirationStatus(token: ApiTokenApi.TokenItem) {
  if (!token.expires_at) {
    return { label: $t('apiToken.neverExpires'), type: 'success' as const };
  }
  const now = new Date();
  const expiresAt = new Date(token.expires_at);
  if (expiresAt < now) {
    return { label: $t('apiToken.expired'), type: 'danger' as const };
  }
  const daysLeft = Math.ceil(
    (expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24),
  );
  if (daysLeft <= 7) {
    return {
      label: $t('apiToken.expiresSoon', [daysLeft]),
      type: 'warning' as const,
    };
  }
  return { label: token.expires_at, type: 'info' as const };
}

function formatDate(dateStr?: null | string) {
  if (!dateStr) return '-';
  return dateStr;
}

const expirationShortcuts = computed(() => [
  {
    text: $t('apiToken.days7'),
    value: () => {
      const d = new Date();
      d.setDate(d.getDate() + 7);
      return d;
    },
  },
  {
    text: $t('apiToken.days30'),
    value: () => {
      const d = new Date();
      d.setDate(d.getDate() + 30);
      return d;
    },
  },
  {
    text: $t('apiToken.days60'),
    value: () => {
      const d = new Date();
      d.setDate(d.getDate() + 60);
      return d;
    },
  },
  {
    text: $t('apiToken.days90'),
    value: () => {
      const d = new Date();
      d.setDate(d.getDate() + 90);
      return d;
    },
  },
  {
    text: $t('apiToken.days365'),
    value: () => {
      const d = new Date();
      d.setFullYear(d.getFullYear() + 1);
      return d;
    },
  },
]);

onMounted(() => {
  loadTokens();
});
</script>

<template>
  <div class="api-token-management">
    <!-- Header -->
    <div class="mb-4 flex items-center justify-between">
      <p class="text-sm text-[var(--el-text-color-secondary)]">
        {{ $t('apiToken.description') }}
      </p>
      <ElButton type="primary" @click="openCreateDialog">
        <Plus class="mr-1 h-4 w-4" />
        {{ $t('apiToken.createToken') }}
      </ElButton>
    </div>

    <!-- Token List -->
    <div v-if="tokens.length > 0" class="space-y-3">
      <div
        v-for="token in tokens"
        :key="token.id"
        class="flex items-center justify-between rounded-lg border border-[var(--el-border-color)] p-4 transition-colors hover:bg-[var(--el-fill-color-light)]"
      >
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <KeyRound class="h-4 w-4 text-[var(--el-color-primary)]" />
            <span class="font-medium text-[var(--el-text-color-primary)]">
              {{ token.name }}
            </span>
            <ElTag
              :type="getExpirationStatus(token).type"
              size="small"
              effect="light"
            >
              {{ getExpirationStatus(token).label }}
            </ElTag>
          </div>
          <div
            class="mt-2 flex items-center gap-4 text-xs text-[var(--el-text-color-secondary)]"
          >
            <span>{{ token.token_prefix }}</span>
            <span v-if="token.description">{{ token.description }}</span>
            <span>
              {{ $t('apiToken.createdAt') }}:
              {{ formatDate(token.sys_create_datetime) }}
            </span>
            <span>
              {{ $t('apiToken.lastUsed') }}:
              {{ formatDate(token.last_used_at) }}
            </span>
          </div>
        </div>
        <ElTooltip :content="$t('apiToken.revokeToken')" placement="top">
          <ElButton
            type="danger"
            text
            circle
            @click="handleRevoke(token)"
          >
            <Trash2 class="h-4 w-4" />
          </ElButton>
        </ElTooltip>
      </div>
    </div>

    <!-- Empty State -->
    <ElEmpty v-else-if="!loading" :description="$t('apiToken.empty')" />

    <!-- Create Token Dialog -->
    <ZqDialog
      v-model="createDialogVisible"
      :title="$t('apiToken.createToken')"
      :confirm-loading="createLoading"
      width="480px"
      @confirm="handleCreate"
    >
      <ElForm label-position="top">
        <ElFormItem :label="$t('apiToken.tokenName')" required>
          <ElInput
            v-model="createForm.name"
            :placeholder="$t('apiToken.tokenNamePlaceholder')"
            maxlength="100"
            show-word-limit
          />
        </ElFormItem>

        <ElFormItem :label="$t('apiToken.expirationDate')">
          <ElDatePicker
            v-model="createForm.expires_at"
            type="datetime"
            :placeholder="$t('apiToken.neverExpiresHint')"
            :shortcuts="expirationShortcuts"
            :disabled-date="(date: Date) => date < new Date()"
            class="w-full"
            clearable
          />
        </ElFormItem>

        <ElFormItem :label="$t('apiToken.tokenDescription')">
          <ElInput
            v-model="createForm.description"
            type="textarea"
            :rows="2"
            :placeholder="$t('apiToken.tokenDescriptionPlaceholder')"
            maxlength="500"
            show-word-limit
          />
        </ElFormItem>
      </ElForm>
    </ZqDialog>

    <!-- Token Display Dialog -->
    <ZqDialog
      v-model="showTokenDialog"
      :title="$t('apiToken.tokenCreated')"
      width="560px"
      :show-footer="false"
    >
      <ElAlert
        :title="$t('apiToken.tokenWarning')"
        type="warning"
        show-icon
        :closable="false"
        class="mb-4"
      />
      <div
        class="flex items-center gap-2 rounded-lg bg-[var(--el-fill-color)] p-3"
      >
        <code
          class="flex-1 break-all text-sm text-[var(--el-text-color-primary)]"
        >
          {{ createdToken }}
        </code>
        <ElButton type="primary" size="small" @click="copyToken">
          <Copy class="mr-1 h-3.5 w-3.5" />
          {{ tokenCopied ? $t('apiToken.copied') : $t('apiToken.copy') }}
        </ElButton>
      </div>
    </ZqDialog>
  </div>
</template>
