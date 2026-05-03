<script lang="ts" setup>
import type { Dept } from '#/api/core/dept';

import { ref, watch } from 'vue';

import { Building2 } from '@vben/icons';

import { ElPopover, ElSkeleton, ElTag } from 'element-plus';

import { getDeptDetailApi } from '#/api/core/dept';

defineOptions({ name: 'DeptTag' });

const props = defineProps<{
  deptId?: string;
  showIcon?: boolean;
}>();

const detail = ref<Dept | null>(null);
const loading = ref(false);
const hasLoaded = ref(false);

// 缓存：避免重复请求
const cache = new Map<string, Dept>();

async function loadDetail() {
  if (hasLoaded.value || !props.deptId) return;

  const cached = cache.get(props.deptId);
  if (cached) {
    detail.value = cached;
    hasLoaded.value = true;
    return;
  }

  loading.value = true;
  try {
    const res = await getDeptDetailApi(props.deptId);
    detail.value = res;
    cache.set(props.deptId, res);
    hasLoaded.value = true;
  } catch (error) {
    console.error('Failed to load dept detail:', error);
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.deptId,
  () => {
    hasLoaded.value = false;
    detail.value = null;
    loadDetail();
  },
  { immediate: true },
);
</script>

<template>
  <ElPopover
    v-if="deptId"
    trigger="hover"
    placement="top"
    :width="240"
    :show-arrow="true"
  >
    <template #reference>
      <ElTag
        v-if="detail"
        size="small"
        class="dept-tag"
        :disable-transitions="true"
      >
        <Building2 v-if="showIcon" class="mr-1 h-3 w-3" />
        {{ detail.name }}
      </ElTag>
      <span v-else class="tag-skeleton"></span>
    </template>

    <div v-if="loading" class="py-2">
      <ElSkeleton :rows="3" animated />
    </div>
    <div v-else-if="detail" class="dept-detail">
      <div class="mb-2 flex items-center gap-2">
        <Building2 class="h-4 w-4 text-[var(--el-color-primary)]" />
        <span class="text-sm font-medium text-[var(--el-text-color-primary)]">
          {{ detail.name }}
        </span>
      </div>
      <div class="detail-grid">
        <div v-if="detail.code" class="detail-row">
          <span class="detail-label">编码</span>
          <span class="detail-value">{{ detail.code }}</span>
        </div>
        <div v-if="detail.dept_type_display" class="detail-row">
          <span class="detail-label">类型</span>
          <span class="detail-value">{{ detail.dept_type_display }}</span>
        </div>
        <div v-if="detail.lead_name" class="detail-row">
          <span class="detail-label">负责人</span>
          <span class="detail-value">{{ detail.lead_name }}</span>
        </div>
        <div v-if="detail.phone" class="detail-row">
          <span class="detail-label">电话</span>
          <span class="detail-value">{{ detail.phone }}</span>
        </div>
        <div v-if="detail.email" class="detail-row">
          <span class="detail-label">邮箱</span>
          <span class="detail-value">{{ detail.email }}</span>
        </div>
        <div v-if="detail.description" class="detail-row">
          <span class="detail-label">描述</span>
          <span class="detail-value">{{ detail.description }}</span>
        </div>
      </div>
    </div>
  </ElPopover>
  <span v-else class="text-xs text-[var(--el-text-color-placeholder)]">-</span>
</template>

<style scoped>
.dept-tag {
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
