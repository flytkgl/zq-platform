<script lang="ts" setup>
import type { LoginLog } from '#/api/core/login-log';

import { computed } from 'vue';

import { useVbenDrawer } from '@vben/common-ui';
import { $t } from '@vben/locales';

import { ElDescriptions, ElDescriptionsItem, ElTag } from 'element-plus';

import {
  getDeviceTypeOptions,
  getFailureReasonOptions,
  getStatusOptions,
} from '../data';

interface Props {
  log?: LoginLog;
}

const props = defineProps<Props>();

const [Drawer, drawerApi] = useVbenDrawer({
  title: $t('loginLog.detailTitle'),
  footer: false,
  loading: false,
});

/**
 * 获取登录状态显示
 */
const statusDisplay = computed(() => {
  if (!props.log) return '';
  const option = getStatusOptions().find(
    (opt) => opt.value === props.log?.status,
  );
  return option?.label || '';
});

/**
 * 获取登录状态类型
 */
const statusType = computed(() => {
  if (!props.log) return 'info';
  const option = getStatusOptions().find(
    (opt) => opt.value === props.log?.status,
  );
  return option?.type || 'info';
});

/**
 * 获取失败原因显示
 */
const failureReasonDisplay = computed(() => {
  if (!props.log || props.log.failure_reason === undefined) return '';
  const option = getFailureReasonOptions().find(
    (opt) => opt.value === props.log?.failure_reason,
  );
  return option?.label || '';
});

/**
 * 获取设备类型显示
 */
const deviceTypeDisplay = computed(() => {
  if (!props.log) return '';
  const option = getDeviceTypeOptions().find(
    (opt) => opt.value === props.log?.device_type,
  );
  return option?.label || props.log.device_type || '';
});

/**
 * 格式化时长
 */
function formatDuration(seconds?: number) {
  if (!seconds) return $t('loginLog.formatZeroSeconds');

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  const parts = [];
  if (hours > 0) parts.push($t('loginLog.formatHours', [hours]));
  if (minutes > 0) parts.push($t('loginLog.formatMinutes', [minutes]));
  if (secs > 0) parts.push($t('loginLog.formatSeconds', [secs]));

  return parts.join('');
}

defineExpose({
  open: drawerApi.open,
  close: drawerApi.close,
});
</script>

<template>
  <Drawer>
    <template v-if="log">
      <ElDescriptions :column="1" border>
        <ElDescriptionsItem :label="$t('loginLog.username')">
          {{ log.username }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('loginLog.userId')" v-if="log.user_id">
          {{ log.user_id }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('loginLog.status')">
          <ElTag :type="statusType as any">{{ statusDisplay }}</ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('loginLog.failureReason')"
          v-if="log.status === 0 && log.failure_reason !== undefined"
        >
          <ElTag type="danger">{{ failureReasonDisplay }}</ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('loginLog.failureMessage')"
          v-if="log.status === 0 && log.failure_message"
        >
          {{ log.failure_message }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('loginLog.loginIp')">
          {{ log.login_ip }}
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('loginLog.ipLocation')"
          v-if="log.ip_location"
        >
          {{ log.ip_location }}
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('loginLog.browserType')"
          v-if="log.browser_type"
        >
          {{ log.browser_type }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('loginLog.osType')" v-if="log.os_type">
          {{ log.os_type }}
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('loginLog.deviceType')"
          v-if="log.device_type"
        >
          <ElTag type="info">{{ deviceTypeDisplay }}</ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('loginLog.duration')"
          v-if="log.duration"
        >
          {{ formatDuration(log.duration) }}
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('loginLog.sessionId')"
          v-if="log.session_id"
        >
          {{ log.session_id }}
        </ElDescriptionsItem>
        <ElDescriptionsItem
          :label="$t('loginLog.userAgent')"
          v-if="log.user_agent"
        >
          <div class="max-w-full break-all text-sm">
            {{ log.user_agent }}
          </div>
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('loginLog.remark')" v-if="log.remark">
          {{ log.remark }}
        </ElDescriptionsItem>
        <ElDescriptionsItem :label="$t('loginLog.loginTime')">
          {{ log.sys_create_datetime }}
        </ElDescriptionsItem>
      </ElDescriptions>
    </template>
    <template v-else>
      <div class="py-8 text-center text-gray-500">
        {{ $t('loginLog.noData') }}
      </div>
    </template>
  </Drawer>
</template>
