<script lang="ts" setup>
import type { ResourceFieldsMetadata } from '#/api/core/field-permission';

import { onMounted, ref, watch } from 'vue';

import { CircleHelp, Settings } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElEmpty,
  ElMessage,
  ElScrollbar,
  ElTooltip,
} from 'element-plus';

import { getAllResourceFieldsApi } from '#/api/core/field-permission';
import { useAppContextStore } from '#/store/app-context';

import FieldPermissionDrawer from './field-permission-drawer.vue';

const props = defineProps<Props>();

const emit = defineEmits<{
  success: [];
}>();

const appContextStore = useAppContextStore();

interface Props {
  roleId?: string;
  height?: number;
}

const loading = ref(false);
const resourceTypes = ref<ResourceFieldsMetadata[]>([]);
const drawerRef = ref<InstanceType<typeof FieldPermissionDrawer>>();
const currentResourceType = ref<string>();

// 加载已配置字段元数据的资源类型
async function loadResourceTypes() {
  if (!props.roleId) {
    resourceTypes.value = [];
    return;
  }

  loading.value = true;
  try {
    // 获取当前应用ID，子应用访问时只显示该应用的资源
    const applicationId = appContextStore.currentApp?.id;
    resourceTypes.value = await getAllResourceFieldsApi(applicationId);
  } catch (error) {
    console.error('Failed to load resource types:', error);
    ElMessage.error($t('role.resourceScope.loadResourceTypesFailed'));
    resourceTypes.value = [];
  } finally {
    loading.value = false;
  }
}

// 打开字段权限配置抽屉
function openFieldPermissionDrawer(resourceType: string) {
  currentResourceType.value = resourceType;
  drawerRef.value?.open();
}

// 配置成功回调
function onConfigSuccess() {
  emit('success');
}

// 监听角色变化
watch(
  () => props.roleId,
  () => {
    loadResourceTypes();
  },
);

onMounted(() => {
  if (props.roleId) {
    loadResourceTypes();
  }
});
</script>

<template>
  <ElCard
    class="flex flex-col border border-[var(--el-border-color)]"
    shadow="never"
    :style="{ height: props.height ? `${props.height}px` : 'auto' }"
    :body-style="{
      padding: '0',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
    }"
  >
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <span class="text-xs font-medium">{{
            $t('role.fieldPermission.title')
          }}</span>
          <ElTooltip
            :content="$t('role.fieldPermission.helpTip')"
            placement="top"
          >
            <CircleHelp
              class="h-3.5 w-3.5 cursor-help text-[var(--el-text-color-secondary)]"
            />
          </ElTooltip>
        </div>
      </div>
    </template>

    <div v-if="!roleId" class="flex h-20 items-center justify-center">
      <ElEmpty :description="$t('role.resourceScope.selectRole')" />
    </div>

    <div v-else-if="loading" class="flex h-20 items-center justify-center">
      <span class="text-xs text-gray-400">{{
        $t('role.permissions.loading')
      }}</span>
    </div>

    <div v-else class="min-h-0 flex-1">
      <ElScrollbar style="height: 100%">
        <div class="space-y-1 p-2">
          <!-- 资源类型列表 -->
          <div
            v-for="resourceType in resourceTypes"
            :key="resourceType.resource_type"
            class="flex h-[36px] cursor-pointer items-center gap-2 rounded-[6px] border border-[var(--el-border-color)] bg-[var(--el-bg-color)] px-2 transition-colors hover:bg-[var(--el-fill-color-light)]"
            @click="openFieldPermissionDrawer(resourceType.resource_type)"
          >
            <!-- 资源类型名称 -->
            <div class="flex-1">
              <span class="text-xs" :title="resourceType.display_name">
                {{ resourceType.display_name }}
              </span>
            </div>

            <!-- 配置按钮 -->
            <div class="flex-shrink-0">
              <ElButton :icon="Settings" link size="small" type="primary">
                {{ $t('role.fieldPermission.config') }}
              </ElButton>
            </div>
          </div>

          <!-- 空状态 -->
          <div
            v-if="resourceTypes.length === 0"
            class="flex h-20 items-center justify-center"
          >
            <ElEmpty :description="$t('role.resourceScope.noResourceTypes')" />
          </div>
        </div>
      </ElScrollbar>
    </div>
  </ElCard>

  <!-- 字段权限配置抽屉 -->
  <FieldPermissionDrawer
    ref="drawerRef"
    :role-id="roleId"
    :resource-type="currentResourceType"
    @success="onConfigSuccess"
  />
</template>

<style scoped></style>
