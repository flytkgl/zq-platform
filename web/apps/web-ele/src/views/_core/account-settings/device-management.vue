<script setup lang="ts">
import type { DeviceApi } from '#/api/core/device';

import { onMounted, reactive, ref } from 'vue';

import { Monitor } from '@vben/icons';

import {
  ElButton,
  ElCard,
  ElDialog,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
} from 'element-plus';

import {
  getDeviceListApi,
  logoutDeviceApi,
  logoutOtherDevicesApi,
  renameDeviceApi,
} from '#/api/core/device';

import DeviceItem from './device-item.vue';

const loading = ref(false);
const deviceList = reactive<DeviceApi.DeviceListResponse>({
  current_device: undefined,
  online_devices: [],
  total_count: 0,
});

const renameDialogVisible = ref(false);
const renameForm = reactive({
  device_id: '',
  device_name: '',
});

// 加载设备列表
async function loadDevices() {
  loading.value = true;
  try {
    const res = await getDeviceListApi();
    Object.assign(deviceList, res);
  } catch {
    ElMessage.error('加载设备列表失败');
  } finally {
    loading.value = false;
  }
}

// 重命名设备
function handleRename(device: DeviceApi.DeviceInfo) {
  renameForm.device_id = device.device_id;
  renameForm.device_name = device.device_name || '';
  renameDialogVisible.value = true;
}

// 确认重命名
async function handleRenameConfirm() {
  if (!renameForm.device_name.trim()) {
    ElMessage.warning('请输入设备名称');
    return;
  }

  try {
    await renameDeviceApi(renameForm.device_id, {
      device_name: renameForm.device_name,
    });
    ElMessage.success('重命名成功');
    renameDialogVisible.value = false;
    await loadDevices();
  } catch {
    ElMessage.error('重命名失败');
  }
}

// 登出指定设备
async function handleLogoutDevice(device: DeviceApi.DeviceInfo) {
  try {
    await ElMessageBox.confirm(
      `确定要强制登出该设备吗？该设备将在下次刷新时被踢出。`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    );

    await logoutDeviceApi(device.device_id);
    ElMessage.success('已强制登出该设备');
    await loadDevices();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败');
    }
  }
}

// 登出所有其他设备
async function handleLogoutAllDevices() {
  try {
    await ElMessageBox.confirm(
      `确定要登出所有其他设备吗？这将强制所有其他设备下次刷新时重新登录。`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    );

    await logoutOtherDevicesApi();
    ElMessage.success('已登出所有其他设备');
    await loadDevices();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败');
    }
  }
}

onMounted(() => {
  loadDevices();
});
</script>

<template>
  <div class="device-management">
    <!-- 统计信息 -->
    <ElCard class="mb-4">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-semibold">设备管理</span>
          <ElButton
            v-if="deviceList.online_devices.length > 0"
            type="danger"
            plain
            size="small"
            @click="handleLogoutAllDevices"
          >
            登出所有其他设备
          </ElButton>
        </div>
      </template>

      <div class="flex gap-8 text-sm">
        <div>
          <span class="text-gray-500">当前在线:</span>
          <span class="text-primary ml-2 text-xl font-bold">
            {{ deviceList.total_count }}
          </span>
          <span class="ml-1 text-gray-500">台设备</span>
        </div>
      </div>
    </ElCard>

    <!-- 当前设备 -->
    <ElCard v-if="deviceList.current_device" class="mb-4">
      <template #header>
        <div class="flex items-center">
          <Monitor class="mr-2 size-5 text-green-500" />
          <span class="font-semibold">当前设备 (你正在使用)</span>
        </div>
      </template>

      <DeviceItem
        :device="deviceList.current_device"
        :is-current="true"
        @rename="handleRename"
      />
    </ElCard>

    <!-- 其他在线设备 -->
    <ElCard v-if="deviceList.online_devices.length > 0">
      <template #header>
        <div class="flex items-center">
          <Monitor class="mr-2 size-5 text-blue-500" />
          <span class="font-semibold">其他在线设备</span>
        </div>
      </template>

      <div class="space-y-4">
        <DeviceItem
          v-for="device in deviceList.online_devices"
          :key="device.device_id"
          :device="device"
          @rename="handleRename"
          @logout="handleLogoutDevice"
        />
      </div>
    </ElCard>

    <!-- 无其他设备提示 -->
    <ElEmpty
      v-if="!loading && deviceList.online_devices.length === 0"
      description="暂无其他设备登录"
    />

    <!-- 重命名对话框 -->
    <ElDialog v-model="renameDialogVisible" title="重命名设备" width="400px">
      <ElForm :model="renameForm" label-width="80px">
        <ElFormItem label="设备名称">
          <ElInput
            v-model="renameForm.device_name"
            placeholder="请输入设备名称，如：办公室电脑"
            maxlength="50"
            show-word-limit
          />
        </ElFormItem>
      </ElForm>

      <template #footer>
        <ElButton @click="renameDialogVisible = false">取消</ElButton>
        <ElButton type="primary" @click="handleRenameConfirm"> 确定 </ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.device-management {
  max-width: 800px;
}
</style>
