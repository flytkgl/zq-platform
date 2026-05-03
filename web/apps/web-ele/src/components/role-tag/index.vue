<script lang="ts" setup>
import type { Role } from '#/api/core/role';

import { ref, watch } from 'vue';

import { Shield } from '@vben/icons';

import { ElPopover, ElTag } from 'element-plus';

import { getRolesByIds } from '#/api/core/role';

defineOptions({ name: 'RoleTag' });

const props = defineProps<{
  roleIds?: string[];
  showIcon?: boolean;
}>();

const roles = ref<Role[]>([]);
const loading = ref(false);
const hasLoaded = ref(false);

// 缓存：避免重复请求
const cache = new Map<string, Role>();

async function loadRoles() {
  if (hasLoaded.value || !props.roleIds || props.roleIds.length === 0) return;

  const uncachedIds: string[] = [];
  const cachedRoles: Role[] = [];
  for (const id of props.roleIds) {
    const cached = cache.get(id);
    if (cached) {
      cachedRoles.push(cached);
    } else {
      uncachedIds.push(id);
    }
  }

  if (uncachedIds.length === 0) {
    roles.value = cachedRoles;
    hasLoaded.value = true;
    return;
  }

  loading.value = true;
  try {
    const res = await getRolesByIds(uncachedIds);
    const fetched = Array.isArray(res) ? res : [];
    for (const r of fetched) {
      cache.set(r.id, r);
    }
    roles.value = [...cachedRoles, ...fetched];
    hasLoaded.value = true;
  } catch (error) {
    console.error('Failed to load role details:', error);
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.roleIds,
  () => {
    hasLoaded.value = false;
    roles.value = [];
    loadRoles();
  },
  { deep: true, immediate: true },
);
</script>

<template>
  <div
    v-if="roleIds && roleIds.length > 0"
    class="inline-flex flex-wrap items-center gap-1"
  >
    <ElPopover
      v-for="role in roles"
      :key="role.id"
      trigger="hover"
      placement="top"
      :width="220"
      :show-arrow="true"
    >
      <template #reference>
        <ElTag size="small" class="role-tag" :disable-transitions="true">
          <Shield v-if="showIcon" class="mr-1 h-3 w-3" />
          {{ role.name }}
        </ElTag>
      </template>

      <div class="role-detail">
        <div class="mb-2 flex items-center gap-2">
          <Shield class="h-4 w-4 text-[var(--el-color-primary)]" />
          <span class="text-sm font-medium text-[var(--el-text-color-primary)]">
            {{ role.name }}
          </span>
        </div>
        <div class="detail-grid">
          <div v-if="role.code" class="detail-row">
            <span class="detail-label">编码</span>
            <span class="detail-value">{{ role.code }}</span>
          </div>
          <div v-if="role.role_type_display" class="detail-row">
            <span class="detail-label">类型</span>
            <span class="detail-value">{{ role.role_type_display }}</span>
          </div>
          <div v-if="role.description" class="detail-row">
            <span class="detail-label">描述</span>
            <span class="detail-value">{{ role.description }}</span>
          </div>
          <div v-if="role.remark" class="detail-row">
            <span class="detail-label">备注</span>
            <span class="detail-value">{{ role.remark }}</span>
          </div>
        </div>
      </div>
    </ElPopover>

    <!-- 未加载完成时显示骨架屏 -->
    <template v-if="!hasLoaded">
      <span v-for="id in roleIds" :key="id" class="tag-skeleton"></span>
    </template>
  </div>
  <span v-else class="text-xs text-[var(--el-text-color-placeholder)]">-</span>
</template>

<style scoped>
.role-tag {
  cursor: pointer;
}

.tag-skeleton {
  display: inline-block;
  width: 56px;
  height: 20px;
  vertical-align: middle;
  background: linear-gradient(
    90deg,
    var(--el-fill-color-light) 25%,
    var(--el-fill-color) 50%,
    var(--el-fill-color-light) 75%
  );
  background-size: 200% 100%;
  border-radius: 4px;
  animation: tag-shimmer 1.5s infinite;
}

@keyframes tag-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.detail-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
}

.detail-label {
  flex-shrink: 0;
  width: 42px;
  color: var(--el-text-color-secondary);
}

.detail-value {
  flex: 1;
  min-width: 0;
  color: var(--el-text-color-primary);
  word-break: break-all;
}
</style>
