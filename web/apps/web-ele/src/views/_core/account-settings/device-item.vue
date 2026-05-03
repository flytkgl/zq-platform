<script setup lang="ts">
import type { DeviceApi } from '#/api/core/device';

import { computed } from 'vue';

import { Monitor, Smartphone } from '@vben/icons';

import { ElButton, ElTag } from 'element-plus';

interface Props {
  device: DeviceApi.DeviceInfo;
  isCurrent?: boolean;
}

interface Emits {
  (e: 'rename', device: DeviceApi.DeviceInfo): void;
  (e: 'logout', device: DeviceApi.DeviceInfo): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 设备显示名称
const deviceDisplayName = computed(() => {
  if (props.device.device_name) {
    return props.device.device_name;
  }
  return `${props.device.browser_type || 'Unknown'} · ${props.device.os_type || 'Unknown'}`;
});

// 格式化时间
function formatTime(timeStr: string) {
  try {
    const date = new Date(timeStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60_000);
    const hours = Math.floor(diff / 3_600_000);
    const days = Math.floor(diff / 86_400_000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 30) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  } catch {
    return timeStr;
  }
}

function handleRename() {
  emit('rename', props.device);
}

function handleLogout() {
  emit('logout', props.device);
}
</script>

<template>
  <div
    class="device-item border-b border-gray-100 pb-4 last:border-0 last:pb-0"
  >
    <div class="flex items-start justify-between">
      <div class="flex items-start gap-3">
        <!-- 设备图标 -->
        <div class="mt-1">
          <Smartphone
            v-if="device.device_type === 'mobile'"
            class="size-6 text-gray-600"
          />
          <Monitor
            v-else-if="device.device_type === 'tablet'"
            class="size-6 text-gray-600"
          />
          <Monitor v-else class="size-6 text-gray-600" />
        </div>

        <!-- 设备信息 -->
        <div class="flex-1">
          <div class="mb-1 flex items-center gap-2">
            <span class="text-base font-semibold">
              {{ deviceDisplayName }}
            </span>
            <ElTag v-if="isCurrent" type="success" size="small">
              当前设备
            </ElTag>
            <ElTag
              v-if="device.is_online"
              type="success"
              size="small"
              effect="plain"
            >
              在线
            </ElTag>
          </div>

          <div class="space-y-1 text-sm text-gray-600">
            <div class="flex items-center gap-4">
              <span>{{ device.browser_type }} · {{ device.os_type }}</span>
            </div>
            <div class="flex items-center gap-4">
              <span>IP: {{ device.ip_address }}</span>
            </div>
            <div v-if="device.last_active_time" class="flex items-center gap-4">
              <span>最后活跃: {{ formatTime(device.last_active_time) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex gap-2">
        <ElButton size="small" @click="handleRename"> 重命名 </ElButton>
        <ElButton
          v-if="!isCurrent"
          type="danger"
          size="small"
          plain
          @click="handleLogout"
        >
          强制登出
        </ElButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.device-item {
  padding-top: 1rem;
}

.device-item:first-child {
  padding-top: 0;
}
</style>
