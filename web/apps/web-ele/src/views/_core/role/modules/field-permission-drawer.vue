<script lang="ts" setup>
import type {
  FieldPermission,
  ResourceFieldMetadata,
  ResourceFieldsMetadata,
} from '#/api/core/field-permission';

import { ref, watch } from 'vue';

import { $t } from '@vben/locales';

import {
  ElMessage,
  ElOption,
  ElSelect,
  ElTable,
  ElTableColumn,
} from 'element-plus';

import {
  batchUpdateFieldPermissionsApi,
  getResourceFieldsApi,
  getRoleFieldPermissionsApi,
  MASK_RULE_OPTIONS,
  PERMISSION_TYPE_OPTIONS,
} from '#/api/core/field-permission';
import { ZqDrawer } from '#/components/zq-drawer';

interface Props {
  roleId?: string;
  resourceType?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  success: [];
}>();

const drawerRef = ref<InstanceType<typeof ZqDrawer>>();
const loading = ref(false);
const saving = ref(false);
const resourceMetadata = ref<null | ResourceFieldsMetadata>(null);
const fieldConfigs = ref<(FieldPermission & ResourceFieldMetadata)[]>([]);

// 打开抽屉
function open() {
  drawerRef.value?.open();
}

// 加载资源字段元数据
async function loadResourceMetadata() {
  if (!props.resourceType) {
    resourceMetadata.value = null;
    return;
  }

  try {
    const data = await getResourceFieldsApi(props.resourceType);
    resourceMetadata.value = data;
  } catch (error) {
    console.error('Failed to load resource metadata:', error);
    ElMessage.error($t('role.fieldPermission.loadMetadataFailed'));
  }
}

// 加载角色的字段权限配置
async function loadFieldPermissions() {
  if (!props.roleId || !props.resourceType) {
    fieldConfigs.value = [];
    return;
  }

  loading.value = true;
  try {
    // 加载资源元数据
    await loadResourceMetadata();

    if (!resourceMetadata.value) {
      fieldConfigs.value = [];
      return;
    }

    // 加载已配置的权限
    const configs = await getRoleFieldPermissionsApi(
      props.roleId,
      props.resourceType,
    );

    // 合并元数据和配置
    const configMap = new Map(configs.map((c) => [c.field_name, c]));

    fieldConfigs.value = resourceMetadata.value.fields.map((field) => {
      const config = configMap.get(field.field_name);
      return {
        ...field,
        permission_type: config?.permission_type || field.default_permission,
        mask_rule: config?.mask_rule,
      } as FieldPermission & ResourceFieldMetadata;
    });
  } catch (error) {
    console.error('Failed to load field permissions:', error);
    ElMessage.error($t('role.fieldPermission.loadFailed'));
    fieldConfigs.value = [];
  } finally {
    loading.value = false;
  }
}

// 保存配置
async function saveConfigs() {
  if (!props.roleId || !props.resourceType) {
    ElMessage.warning($t('role.fieldPermission.selectRoleAndResource'));
    return;
  }

  // 验证配置
  for (const config of fieldConfigs.value) {
    if (config.permission_type === 'masked' && !config.mask_rule) {
      ElMessage.warning(
        `${$t('role.fieldPermission.fieldName')} ${config.label} ${$t('role.fieldPermission.maskRuleRequired')}`,
      );
      return;
    }
  }

  saving.value = true;
  try {
    await batchUpdateFieldPermissionsApi({
      role_id: props.roleId,
      resource_type: props.resourceType,
      configs: fieldConfigs.value.map((c) => ({
        field_name: c.field_name,
        permission_type: c.permission_type,
        mask_rule: c.mask_rule,
      })),
    });

    ElMessage.success($t('role.fieldPermission.saveSuccess'));
    emit('success');
    drawerRef.value?.close();
  } catch (error) {
    console.error('Failed to save:', error);
    ElMessage.error($t('role.fieldPermission.saveFailed'));
  } finally {
    saving.value = false;
  }
}

// 获取脱敏规则标签
function getMaskRuleLabel(rule?: string): string {
  if (!rule) return '-';
  const option = MASK_RULE_OPTIONS.find((opt) => opt.value === rule);
  return option?.label || rule;
}

// 监听资源类型变化，自动加载数据
watch(
  () => props.resourceType,
  () => {
    if (props.resourceType) {
      loadFieldPermissions();
    }
  },
);

defineExpose({
  open,
});
</script>

<template>
  <ZqDrawer
    ref="drawerRef"
    :title="`${$t('role.fieldPermission.title')} - ${resourceMetadata?.display_name || ''}`"
    :loading="saving"
    :confirm-loading="saving"
    size="55%"
    @confirm="saveConfigs"
  >
    <div v-if="loading" class="flex h-60 items-center justify-center">
      <span class="text-sm text-[var(--el-text-color-secondary)]">{{
        $t('role.permissions.loading')
      }}</span>
    </div>

    <div
      v-else-if="fieldConfigs.length === 0"
      class="flex h-60 items-center justify-center"
    >
      <span class="text-sm text-[var(--el-text-color-secondary)]">{{
        $t('role.fieldPermission.noConfig')
      }}</span>
    </div>

    <div v-else>
      <ElTable
        :data="fieldConfigs"
        size="small"
        stripe
        max-height="calc(100vh - 150px)"
      >
        <ElTableColumn
          prop="field_name"
          :label="$t('role.fieldPermission.fieldName')"
          width="150"
        />
        <ElTableColumn
          prop="label"
          :label="$t('role.fieldPermission.displayName')"
          width="120"
        />
        <ElTableColumn
          :label="$t('role.fieldPermission.sensitive')"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <span
              :class="
                row.sensitive
                  ? 'text-[var(--el-color-danger)]'
                  : 'text-[var(--el-text-color-secondary)]'
              "
            >
              {{ row.sensitive ? $t('common.yes') : $t('common.no') }}
            </span>
          </template>
        </ElTableColumn>
        <ElTableColumn
          :label="$t('role.fieldPermission.permissionType')"
          width="150"
        >
          <template #default="{ row }">
            <ElSelect
              v-model="row.permission_type"
              size="small"
              style="width: 100%"
            >
              <ElOption
                v-for="option in PERMISSION_TYPE_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
                :disabled="option.value === 'hidden' && row.required"
              />
            </ElSelect>
          </template>
        </ElTableColumn>
        <ElTableColumn :label="$t('role.fieldPermission.maskRule')" width="150">
          <template #default="{ row }">
            <ElSelect
              v-if="row.permission_type === 'masked'"
              v-model="row.mask_rule"
              size="small"
              style="width: 100%"
              :placeholder="$t('role.resourceScope.selectDataPermission')"
            >
              <ElOption
                v-for="option in MASK_RULE_OPTIONS"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </ElSelect>
            <span v-else class="text-xs text-[var(--el-text-color-secondary)]">
              {{ getMaskRuleLabel(row.mask_rule) }}
            </span>
          </template>
        </ElTableColumn>
        <ElTableColumn
          :label="$t('role.fieldPermission.description')"
          min-width="200"
        >
          <template #default="{ row }">
            <div class="text-xs text-[var(--el-text-color-regular)]">
              <span v-if="row.permission_type === 'read'">
                {{ $t('role.fieldPermission.permissionDesc.read') }}
              </span>
              <span v-else-if="row.permission_type === 'write'">
                {{ $t('role.fieldPermission.permissionDesc.write') }}
              </span>
              <span v-else-if="row.permission_type === 'hidden'">
                {{ $t('role.fieldPermission.permissionDesc.hidden') }}
              </span>
              <span v-else-if="row.permission_type === 'masked'">
                {{ $t('role.fieldPermission.permissionDesc.masked') }}
              </span>
            </div>
          </template>
        </ElTableColumn>
      </ElTable>
    </div>
  </ZqDrawer>
</template>

<style scoped>
:deep(.el-table) {
  font-size: 12px;
}

:deep(.el-table th) {
  background-color: var(--el-fill-color-light);
  font-weight: 500;
}
</style>
