<script lang="ts" setup>
import type {
  ResourceScopeConfig,
  ResourceType,
} from '#/api/core/resource-scope';

import { onMounted, ref, watch } from 'vue';

import { CircleHelp, Trash as Delete, Plus } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElEmpty,
  ElMessage,
  ElOption,
  ElPopconfirm,
  ElScrollbar,
  ElSelect,
  ElTooltip,
} from 'element-plus';

import { getDeptTreeApi } from '#/api/core/dept';
import {
  batchUpdateRoleResourceScopesApi,
  DATA_SCOPE_OPTIONS,
  getResourceTypesApi,
  getRoleResourceScopesApi,
} from '#/api/core/resource-scope';
import { useAppContextStore } from '#/store/app-context';

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
const saving = ref(false);
const resourceTypes = ref<ResourceType[]>([]);
const deptTree = ref<any[]>([]);
const configs = ref<ResourceScopeConfig[]>([]);

// 数据权限范围选项
const dataScopeOptions = DATA_SCOPE_OPTIONS;

// 获取数据权限范围的显示名称
function getDataScopeLabel(value: number): string {
  const option = dataScopeOptions.find((opt) => opt.value === value);
  return option?.label || $t('role.dataScopes.unknown');
}

// 加载资源类型
async function loadResourceTypes() {
  try {
    // 获取当前应用ID，子应用访问时只显示该应用的资源
    const applicationId = appContextStore.currentApp?.id;
    resourceTypes.value = await getResourceTypesApi(applicationId);
  } catch (error) {
    console.error('Failed to load resource types:', error);
    ElMessage.error($t('role.resourceScope.loadResourceTypesFailed'));
  }
}

// 加载部门树
async function loadDeptTree() {
  try {
    deptTree.value = await getDeptTreeApi();
  } catch (error) {
    console.error('Failed to load department tree:', error);
    ElMessage.error($t('role.resourceScope.loadDeptsFailed'));
  }
}

// 加载角色的资源权限配置
async function loadRoleResourceScopes() {
  if (!props.roleId) {
    configs.value = [];
    return;
  }

  loading.value = true;
  try {
    const data = await getRoleResourceScopesApi(props.roleId);
    configs.value = data || [];
  } catch (error) {
    console.error('Failed to load resource scope config:', error);
    ElMessage.error($t('role.resourceScope.loadFailed'));
    configs.value = [];
  } finally {
    loading.value = false;
  }
}

// 添加新配置
function addConfig() {
  // 找出未配置的资源类型
  const configuredTypes = new Set(configs.value.map((c) => c.resource_type));
  const availableTypes = resourceTypes.value.filter(
    (rt) => !configuredTypes.has(rt.resource_type),
  );

  if (availableTypes.length === 0) {
    ElMessage.warning($t('role.resourceScope.allTypesConfigured'));
    return;
  }

  configs.value.push({
    role_id: props.roleId!,
    resource_type: availableTypes[0].resource_type,
    data_scope: 0, // 默认全部数据
    dept_ids: null,
  });
}

// 删除配置
function removeConfig(index: number) {
  configs.value.splice(index, 1);
}

// 获取可选的资源类型（排除已配置的）
function getAvailableResourceTypes(currentType?: string) {
  const configuredTypes = new Set(
    configs.value
      .map((c) => c.resource_type)
      .filter((type) => type !== currentType),
  );
  return resourceTypes.value.filter(
    (rt) => !configuredTypes.has(rt.resource_type),
  );
}

// 保存配置
async function saveConfigs() {
  if (!props.roleId) {
    ElMessage.warning($t('role.resourceScope.selectRole'));
    return;
  }

  // 验证配置
  for (const config of configs.value) {
    if (!config.resource_type) {
      ElMessage.warning($t('role.resourceScope.selectResourceType'));
      return;
    }
    if (
      config.data_scope === 4 &&
      (!config.dept_ids || config.dept_ids.length === 0)
    ) {
      ElMessage.warning($t('role.resourceScope.customDeptRequired'));
      return;
    }
  }

  saving.value = true;
  try {
    await batchUpdateRoleResourceScopesApi({
      role_id: props.roleId,
      configs: configs.value.map((c) => ({
        resource_type: c.resource_type,
        data_scope: c.data_scope,
        dept_ids: c.data_scope === 4 ? c.dept_ids : null,
      })),
    });

    ElMessage.success($t('role.resourceScope.saveSuccess'));
    emit('success');
    await loadRoleResourceScopes();
  } catch (error) {
    console.error('Failed to save:', error);
    ElMessage.error($t('role.resourceScope.saveFailed'));
  } finally {
    saving.value = false;
  }
}

// 监听角色变化
watch(
  () => props.roleId,
  () => {
    loadRoleResourceScopes();
  },
);

onMounted(() => {
  loadResourceTypes();
  loadDeptTree();
  if (props.roleId) {
    loadRoleResourceScopes();
  }
});

defineExpose({
  save: saveConfigs,
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
            $t('role.resourceScope.title')
          }}</span>
          <ElTooltip
            :content="$t('role.resourceScope.helpTip')"
            placement="top"
          >
            <CircleHelp
              class="h-3.5 w-3.5 cursor-help text-[var(--el-text-color-secondary)]"
            />
          </ElTooltip>
        </div>
        <div class="flex flex-shrink-0 gap-1">
          <ElButton
            :disabled="!roleId || saving"
            :icon="Plus"
            link
            size="small"
            type="primary"
            @click="addConfig"
          >
            {{ $t('role.resourceScope.addResource') }}
          </ElButton>
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
          <!-- 配置项列表 -->
          <div
            v-for="(config, index) in configs"
            :key="index"
            class="flex h-[36px] items-center gap-2 rounded-[6px] border border-[var(--el-border-color)] bg-[var(--el-bg-color)] px-2 transition-colors hover:bg-[var(--el-fill-color-light)]"
          >
            <!-- 资源类型 -->
            <div class="w-[100px] flex-shrink-0">
              <ElSelect
                v-model="config.resource_type"
                :placeholder="$t('role.resourceScope.resourceType')"
                size="small"
                style="width: 100%"
              >
                <ElOption
                  v-for="rt in getAvailableResourceTypes(config.resource_type)"
                  :key="rt.resource_type"
                  :label="rt.display_name"
                  :value="rt.resource_type"
                >
                  <span class="text-xs">{{ rt.display_name }}</span>
                </ElOption>
              </ElSelect>
            </div>

            <!-- 数据权限范围 -->
            <div class="w-[120px] flex-shrink-0">
              <ElSelect
                v-model="config.data_scope"
                :placeholder="$t('role.resourceScope.dataPermission')"
                size="small"
                style="width: 100%"
              >
                <ElOption
                  v-for="option in dataScopeOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </ElSelect>
            </div>

            <!-- 自定义部门 -->
            <div class="flex-1">
              <ElSelect
                v-if="config.data_scope === 4"
                v-model="config.dept_ids"
                clearable
                collapse-tags
                collapse-tags-tooltip
                filterable
                multiple
                :placeholder="$t('role.resourceScope.selectDept')"
                size="small"
                style="width: 100%"
              >
                <ElOption
                  v-for="dept in deptTree"
                  :key="dept.id"
                  :label="dept.name"
                  :value="dept.id"
                />
              </ElSelect>
              <span v-else class="text-xs text-gray-400">
                {{ getDataScopeLabel(config.data_scope) }}
              </span>
            </div>

            <!-- 删除按钮 -->
            <div class="flex-shrink-0">
              <ElPopconfirm
                :confirm-button-text="$t('common.confirm')"
                :cancel-button-text="$t('common.cancel')"
                :title="$t('role.resourceScope.deleteConfirm')"
                @confirm="removeConfig(index)"
              >
                <template #reference>
                  <ElButton :icon="Delete" link size="small" type="danger" />
                </template>
              </ElPopconfirm>
            </div>
          </div>

          <!-- 空状态 -->
          <div
            v-if="configs.length === 0"
            class="flex h-12 items-center justify-center text-sm text-[var(--el-text-color-secondary)]"
          >
            {{ $t('role.resourceScope.noConfig') }}
          </div>
        </div>
      </ElScrollbar>
    </div>
  </ElCard>
</template>

<style scoped></style>
