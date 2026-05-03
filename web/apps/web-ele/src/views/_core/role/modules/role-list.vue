<script lang="ts" setup>
import type { Role } from '#/api/core/role';
import type { CardListOptions } from '#/components/card-list';

import { onMounted, ref } from 'vue';

import { IconifyIcon, Users } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElButton, ElMessage, ElMessageBox, ElTooltip } from 'element-plus';

import { deleteRoleApi, getRoleListApi } from '#/api/core/role';
import { CardList } from '#/components/card-list';

import RoleFormModal from './role-form-modal.vue';

const emit = defineEmits<{
  select: [roleId: string | undefined];
  showUsers: [role: Role];
}>();

const roleList = ref<Role[]>([]);
const loading = ref(false);
const selectedRoleId = ref<string>();
const searchKeyword = ref<string>('');
const hoveredRoleId = ref<string>();
const roleFormModalRef = ref<InstanceType<typeof RoleFormModal>>();

// 卡片列表配置
const cardListOptions: CardListOptions<Role> = {
  searchFields: [{ field: 'name' }, { field: 'code' }],
  titleField: 'name',
};

async function fetchRoleList() {
  try {
    loading.value = true;
    const response = await getRoleListApi({ page: 1, pageSize: 100 });
    roleList.value = response.items || [];

    // 自动选中第一个角色
    if (roleList.value.length > 0 && !selectedRoleId.value) {
      const firstRole = roleList.value.at(0);
      if (firstRole) {
        selectedRoleId.value = firstRole.id;
        emit('select', firstRole.id);
      }
    }
  } finally {
    loading.value = false;
  }
}

/**
 * 处理角色选择
 */
function onRoleSelect(roleId: string | undefined) {
  selectedRoleId.value = roleId;
  emit('select', roleId);
}

/**
 * 打开添加角色对话框
 */
function onAddRole() {
  roleFormModalRef.value?.open();
}

/**
 * 打开编辑角色对话框
 */
function onEditRole(role: Role, e?: Event) {
  e?.stopPropagation();
  roleFormModalRef.value?.open(role);
}

/**
 * 删除角色
 */
async function onDeleteRole(role: Role, e?: Event) {
  e?.stopPropagation();

  ElMessageBox.confirm(
    $t('ui.actionMessage.deleteConfirm', [role.name]),
    $t('common.delete'),
    {
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
      type: 'warning',
      showClose: false,
    },
  )
    .then(async () => {
      try {
        await deleteRoleApi(role.id);
        ElMessage.success($t('ui.actionMessage.deleteSuccess', [role.name]));

        // 如果删除的是当前选中的角色，清除选中状态
        if (selectedRoleId.value === role.id) {
          selectedRoleId.value = undefined;
          emit('select', undefined);
        }

        await fetchRoleList();
      } catch {
        ElMessage.error($t('ui.actionMessage.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

/**
 * 添加角色成功后的回调
 */
async function onRoleFormSuccess() {
  ElMessage.success(
    $t('ui.actionMessage.createSuccess', [$t('role.name')]),
  );
  await fetchRoleList();
}

/**
 * 获取数据范围文本
 */
function getDataRangeText(dataScope: number): string {
  const rangeMap: Record<number, string> = {
    0: $t('role.dataScopes.self'),
    1: $t('role.dataScopes.dept'),
    2: $t('role.dataScopes.deptAndSubShort'),
    3: $t('role.dataScopes.all'),
    4: $t('role.dataScopes.custom'),
  };
  return rangeMap[dataScope] || $t('role.dataScopes.unknown');
}

onMounted(() => {
  fetchRoleList();
});
</script>

<template>
  <CardList
    :items="roleList"
    :loading="loading"
    :selected-id="selectedRoleId"
    :hovered-id="hoveredRoleId"
    :search-keyword="searchKeyword"
    :options="cardListOptions"
    @select="onRoleSelect"
    @update:search-keyword="(v) => (searchKeyword = v)"
    @update:hovered-id="(v) => (hoveredRoleId = v)"
    @add="onAddRole"
    @edit="onEditRole"
    @delete="onDeleteRole"
  >
    <!-- 自定义项目渲染 -->
    <template #item="{ item }">
      <div class="truncate text-sm" :title="item.name">
        {{ item.name }}
      </div>
    </template>

    <!-- 详细信息 -->
    <template #details="{ item }">
      <div class="flex items-center gap-2 text-xs opacity-70">
        <!-- 角色编码 -->
        <span class="truncate" :title="item.code">
          {{ item.code }}
        </span>

        <!-- 分隔符 -->
        <span class="text-gray-400">|</span>

        <!-- 状态 -->
        <span class="flex-shrink-0">
          {{ item.status ? $t('common.enabled') : $t('common.disabled') }}
        </span>

        <!-- 数据范围 -->
        <span v-if="item.data_scope !== undefined" class="flex-shrink-0">
          {{ getDataRangeText(item.data_scope) }}
        </span>

        <!-- 备注 -->
        <span v-if="item.remark" class="flex-1 truncate" :title="item.remark">
          {{ item.remark }}
        </span>
      </div>
    </template>

    <!-- 操作按钮 -->
    <template #actions="{ item }">
      <div class="ml-2 flex flex-shrink-0 gap-0.5" @click.stop>
        <ElTooltip :content="$t('role.users')" placement="top">
          <ElButton
            type="primary"
            text
            size="small"
            circle
            @click="emit('showUsers', item)"
          >
            <Users class="size-4" />
          </ElButton>
        </ElTooltip>
        <ElTooltip :content="$t('role.edit')" placement="top">
          <ElButton
            type="primary"
            text
            size="small"
            circle
            @click="onEditRole(item, $event)"
          >
            <IconifyIcon icon="ep:edit" class="size-4" />
          </ElButton>
        </ElTooltip>
        <ElButton
          type="danger"
          text
          size="small"
          circle
          style="margin-left: 0"
          :title="$t('common.delete')"
          @click="onDeleteRole(item, $event)"
        >
          <IconifyIcon icon="ep:delete" class="size-4" />
        </ElButton>
      </div>
    </template>

    <!-- Modal 组件 -->
    <template #modal>
      <RoleFormModal ref="roleFormModalRef" @success="onRoleFormSuccess" />
    </template>
  </CardList>
</template>

<style scoped>
/* 输入框前置图标样式 */
:deep(.el-input__icon) {
  cursor: pointer;
}

/* 文本按钮样式 */
:deep(.el-button--text) {
  padding: 0 4px;
}
</style>
