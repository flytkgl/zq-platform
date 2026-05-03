<script setup lang="ts">
import type { RedisKeyDetail } from '#/api/core/redis-manager';

import { ref, watch } from 'vue';

import { Clock, Copy, Edit, Key, Trash2 } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElDescriptions,
  ElDescriptionsItem,
  ElEmpty,
  ElMessage,
  ElMessageBox,
  ElScrollbar,
  ElTag,
} from 'element-plus';

import {
  deleteRedisKeyApi,
  getRedisKeyDetailApi,
  renameRedisKeyApi,
  setRedisKeyExpireApi,
} from '#/api/core/redis-manager';

interface Props {
  dbIndex: number;
  selectedKey?: string;
}

interface Emits {
  (e: 'edit-key', key: string): void;
  (e: 'key-deleted'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const keyDetail = ref<null | RedisKeyDetail>(null);
const loading = ref(false);
const refreshing = ref(false);

// 刷新键详情
async function handleRefresh() {
  refreshing.value = true;
  try {
    await loadKeyDetail();
  } finally {
    // 延迟一点时间，让动画更明显
    setTimeout(() => {
      refreshing.value = false;
    }, 500);
  }
}

// 加载键详情
async function loadKeyDetail() {
  if (!props.selectedKey) {
    keyDetail.value = null;
    return;
  }

  try {
    loading.value = true;
    const detail = await getRedisKeyDetailApi(props.dbIndex, props.selectedKey);
    keyDetail.value = detail;
  } catch (error) {
    console.error('Failed to load key detail:', error);
    ElMessage.error($t('redis-manager.loadKeyDetailFailed'));
    keyDetail.value = null;
  } finally {
    loading.value = false;
  }
}

// 删除键
async function handleDelete() {
  if (!props.selectedKey) return;

  try {
    await ElMessageBox.confirm(
      $t('redis-manager.deleteConfirm', { key: props.selectedKey }),
      $t('redis-manager.confirmDelete'),
      {
        type: 'warning',
      },
    );

    await deleteRedisKeyApi(props.dbIndex, props.selectedKey);
    ElMessage.success($t('redis-manager.deleteSuccess'));
    emit('key-deleted');
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete key:', error);
      ElMessage.error($t('redis-manager.deleteFailed'));
    }
  }
}

// 重命名键
async function handleRename() {
  if (!props.selectedKey) return;

  try {
    const { value: newKey } = await ElMessageBox.prompt(
      $t('redis-manager.renamePrompt'),
      $t('redis-manager.renameKey'),
      {
        confirmButtonText: $t('redis-manager.confirm'),
        cancelButtonText: $t('redis-manager.cancel'),
        inputValue: props.selectedKey,
        inputPattern: /.+/,
        inputErrorMessage: $t('redis-manager.keyRequired'),
      },
    );

    if (newKey && newKey !== props.selectedKey) {
      await renameRedisKeyApi(props.dbIndex, {
        old_key: props.selectedKey,
        new_key: newKey,
      });
      ElMessage.success($t('redis-manager.renameSuccess'));
      emit('key-deleted'); // 触发刷新
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to rename key:', error);
      ElMessage.error($t('redis-manager.renameFailed'));
    }
  }
}

// 设置过期时间
async function handleSetExpire() {
  if (!props.selectedKey) return;

  try {
    const { value: ttl } = await ElMessageBox.prompt(
      $t('redis-manager.setExpirePrompt'),
      $t('redis-manager.setExpire'),
      {
        confirmButtonText: $t('redis-manager.confirm'),
        cancelButtonText: $t('redis-manager.cancel'),
        inputValue: keyDetail.value?.ttl?.toString() || '-1',
        inputPattern: /^-?\d+$/,
        inputErrorMessage: $t('redis-manager.invalidNumber'),
      },
    );

    if (ttl) {
      await setRedisKeyExpireApi(props.dbIndex, {
        key: props.selectedKey,
        ttl: Number.parseInt(ttl),
      });
      ElMessage.success($t('redis-manager.setSuccess'));
      loadKeyDetail();
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to set expire:', error);
      ElMessage.error($t('redis-manager.setFailed'));
    }
  }
}

// 复制值
function handleCopyValue() {
  if (!keyDetail.value) return;

  const value =
    typeof keyDetail.value.value === 'string'
      ? keyDetail.value.value
      : JSON.stringify(keyDetail.value.value, null, 2);

  navigator.clipboard.writeText(value);
  ElMessage.success($t('redis-manager.copySuccess'));
}

// 格式化TTL
function formatTTL(ttl: number): string {
  if (ttl === -1) return $t('redis-manager.permanent');
  if (ttl === -2) return $t('redis-manager.expired');
  if (ttl < 60) return `${ttl}${$t('redis-manager.seconds')}`;
  if (ttl < 3600)
    return `${Math.floor(ttl / 60)}${$t('redis-manager.minutes')}`;
  if (ttl < 86_400)
    return `${Math.floor(ttl / 3600)}${$t('redis-manager.hours')}`;
  return `${Math.floor(ttl / 86_400)}${$t('redis-manager.days')}`;
}

// 获取类型标签颜色
function getTypeTagColor(
  type: string,
): 'danger' | 'info' | 'primary' | 'success' | 'warning' {
  const colorMap: Record<
    string,
    'danger' | 'info' | 'primary' | 'success' | 'warning'
  > = {
    hash: 'primary',
    list: 'warning',
    set: 'danger',
    string: 'success',
    zset: 'info',
  };
  return colorMap[type] || 'info';
}

// 监听选中键变化
watch(
  () => props.selectedKey,
  () => {
    loadKeyDetail();
  },
  { immediate: true },
);

// 暴露给父组件
defineExpose({
  handleRefresh,
  refreshing,
});
</script>

<template>
  <div class="flex h-full flex-col">
    <ElScrollbar class="flex-1">
      <div v-if="loading" class="flex h-64 items-center justify-center">
        <span class="text-gray-400">{{ $t('redis-manager.loading') }}</span>
      </div>

      <ElEmpty
        v-else-if="!selectedKey"
        :description="$t('redis-manager.selectKeyPrompt')"
        :image-size="100"
      />

      <div v-else-if="keyDetail" class="p-4">
        <!-- 键信息 -->
        <ElDescriptions :column="1" border>
          <ElDescriptionsItem :label="$t('redis-manager.keyName')">
            <div class="flex items-center justify-between">
              <span class="font-mono">{{ keyDetail.key }}</span>
              <button
                class="rounded p-1 text-blue-500 transition-colors hover:bg-blue-50"
                :title="$t('redis-manager.copy')"
                @click="handleCopyValue"
              >
                <Copy :size="16" />
              </button>
            </div>
          </ElDescriptionsItem>

          <ElDescriptionsItem :label="$t('redis-manager.type')">
            <ElTag :type="getTypeTagColor(keyDetail.type)" size="small">
              {{ keyDetail.type }}
            </ElTag>
          </ElDescriptionsItem>

          <ElDescriptionsItem :label="$t('redis-manager.ttl')">
            <div class="flex items-center justify-between">
              <span>{{ formatTTL(keyDetail.ttl) }}</span>
              <button
                class="rounded p-1 text-blue-500 transition-colors hover:bg-blue-50"
                :title="$t('redis-manager.setExpire')"
                @click="handleSetExpire"
              >
                <Clock :size="16" />
              </button>
            </div>
          </ElDescriptionsItem>

          <ElDescriptionsItem
            v-if="keyDetail.size !== undefined && keyDetail.size > 0"
            :label="$t('redis-manager.size')"
          >
            {{ keyDetail.size }} {{ $t('redis-monitor.bits') }}
          </ElDescriptionsItem>

          <ElDescriptionsItem
            v-if="keyDetail.encoding"
            :label="$t('redis-manager.encoding')"
          >
            {{ keyDetail.encoding }}
          </ElDescriptionsItem>
        </ElDescriptions>

        <!-- 值显示 -->
        <div class="mt-4">
          <div class="mb-2 flex items-center justify-between">
            <span class="font-semibold">{{ $t('redis-manager.value') }}</span>
            <div class="flex gap-2">
              <ElButton
                size="small"
                type="primary"
                @click="emit('edit-key', keyDetail.key)"
              >
                <Edit :size="14" class="mr-1" />
                {{ $t('redis-manager.editKey') }}
              </ElButton>
              <ElButton size="small" @click="handleRename">
                <Key :size="14" class="mr-1" />
                {{ $t('redis-manager.renameKey') }}
              </ElButton>
              <ElButton size="small" type="danger" @click="handleDelete">
                <Trash2 :size="14" class="mr-1" />
                {{ $t('redis-manager.deleteKey') }}
              </ElButton>
            </div>
          </div>

          <!-- String 类型 -->
          <div
            v-if="keyDetail.type === 'string'"
            class="rounded border bg-gray-50 p-3 dark:bg-gray-800"
          >
            <pre class="whitespace-pre-wrap break-all text-sm">{{
              keyDetail.value
            }}</pre>
          </div>

          <!-- List 类型 -->
          <div
            v-else-if="keyDetail.type === 'list'"
            class="rounded border bg-gray-50 p-3 dark:bg-gray-800"
          >
            <div
              v-for="(item, index) in keyDetail.value"
              :key="index"
              class="mb-2 flex items-start gap-2 border-b pb-2 last:border-b-0 last:pb-0"
            >
              <span class="font-mono text-xs text-gray-500">[{{ index }}]</span>
              <span class="flex-1 break-all text-sm">{{ item }}</span>
            </div>
          </div>

          <!-- Set 类型 -->
          <div
            v-else-if="keyDetail.type === 'set'"
            class="rounded border bg-gray-50 p-3 dark:bg-gray-800"
          >
            <div class="flex flex-wrap gap-2">
              <ElTag
                v-for="(item, index) in keyDetail.value"
                :key="index"
                size="small"
              >
                {{ item }}
              </ElTag>
            </div>
          </div>

          <!-- ZSet 类型 -->
          <div
            v-else-if="keyDetail.type === 'zset'"
            class="rounded border bg-gray-50 p-3 dark:bg-gray-800"
          >
            <div
              v-for="(item, index) in keyDetail.value"
              :key="index"
              class="mb-2 flex items-center justify-between border-b pb-2 last:border-b-0 last:pb-0"
            >
              <span class="break-all text-sm">{{ item.member }}</span>
              <ElTag size="small" type="info">{{ item.score }}</ElTag>
            </div>
          </div>

          <!-- Hash 类型 -->
          <div
            v-else-if="keyDetail.type === 'hash'"
            class="rounded border bg-gray-50 p-3 dark:bg-gray-800"
          >
            <div
              v-for="(value, field) in keyDetail.value"
              :key="field"
              class="mb-2 border-b pb-2 last:border-b-0 last:pb-0"
            >
              <div class="mb-1 font-mono text-xs text-gray-500">
                {{ field }}
              </div>
              <div class="break-all text-sm">{{ value }}</div>
            </div>
          </div>
        </div>
      </div>

      <ElEmpty v-else :description="$t('redis-manager.keyNotExist')" />
    </ElScrollbar>
  </div>
</template>

<style scoped>
/* 自定义样式 */
</style>
