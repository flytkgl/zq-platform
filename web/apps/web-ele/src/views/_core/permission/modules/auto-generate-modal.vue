<script lang="ts" setup>
import { ref } from 'vue';

import { $t } from '@vben/locales';

import { ElMessage } from 'element-plus';

import {
  batchCreatePermissionsFromRoutesApi,
  getAllRoutesApi,
} from '#/api/core/permission';
import { ZqDialog } from '#/components/zq-dialog';

import RouteSelector from './route-selector.vue';

interface RouteItem {
  path: string;
  method: string;
  operation_id: string;
  summary: string;
  // 编辑字段
  name?: string;
  code?: string;
  permission_type?: number;
  http_method?: number;
  is_active?: boolean;
  selected?: boolean;
}

const emit = defineEmits<{
  success: [];
}>();

const loading = ref(false);
const allRoutes = ref<RouteItem[]>([]);
const currentMenuId = ref<string>('');
const currentMenuName = ref<string>('');
const routeSelectorRef = ref<InstanceType<typeof RouteSelector>>();
const visible = ref(false);
const confirmLoading = ref(false);

// HTTP 方法映射
const methodMap: Record<string, { code: number; name: string }> = {
  GET: { name: 'read', code: 0 },
  POST: { name: 'create', code: 1 },
  PUT: { name: 'update', code: 2 },
  DELETE: { name: 'delete', code: 3 },
  PATCH: { name: 'part_update', code: 4 },
};

// 提交
async function onSubmit() {
  if (!currentMenuId.value) {
    ElMessage.warning($t('permission.selectMenuFirst'));
    return;
  }

  // 检查重复
  const checkResult = routeSelectorRef.value?.checkDuplicates();
  if (checkResult?.hasError) {
    ElMessage.error(checkResult.message);
    return;
  }

  const selectedRoutes = allRoutes.value.filter((r) => r.selected);
  if (selectedRoutes.length === 0) {
    ElMessage.warning($t('permission.selectAtLeastOneRoute'));
    return;
  }

  confirmLoading.value = true;

  try {
    const result = await batchCreatePermissionsFromRoutesApi({
      menu_id: currentMenuId.value,
      routes: selectedRoutes.map((route) => ({
        path: route.path,
        method: route.method,
        name: route.name,
        code: route.code,
        summary: route.summary,
        permission_type: route.permission_type,
        http_method: route.http_method,
        is_active: route.is_active,
      })),
    });

    ElMessage.success(
      $t('permission.createSuccess', {
        created: result.created,
        skipped:
          result.skipped > 0
            ? $t('permission.skipped', { count: result.skipped })
            : '',
      }),
    );

    if (result.failed > 0) {
      ElMessage.warning(
        $t('permission.createFailed', {
          failed: result.failed,
          errors: result.errors.join('; '),
        }),
      );
    }

    visible.value = false;
    emit('success');
  } catch {
    ElMessage.error($t('permission.createError'));
  } finally {
    confirmLoading.value = false;
  }
}

// 初始化路由数据
async function initRoutes() {
  loading.value = true;
  try {
    const routes = await getAllRoutesApi();
    allRoutes.value = routes.map((route) => {
      const methodInfo = methodMap[route.method] || {
        name: route.method,
        code: 0,
      };
      return {
        ...route,
        name: `${route.summary || route.operation_id}`,
        code: `${route.path.split('/')[3]}:${methodInfo.name.toLowerCase()}`,
        permission_type: 1,
        http_method: methodInfo.code,
        is_active: true,
        selected: false,
      };
    });
  } catch {
    ElMessage.error($t('permission.getRoutesFailed'));
  } finally {
    loading.value = false;
  }
}

function open(data: { menuId: string; menuName: string }) {
  visible.value = true;
  currentMenuId.value = data.menuId;
  currentMenuName.value = data.menuName;
  allRoutes.value = [];
  initRoutes();
}

defineExpose({
  open,
});
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="$t('permission.autoGenerateApi')"
    :confirm-loading="confirmLoading"
    :default-fullscreen="true"
    @confirm="onSubmit"
  >
    <div class="auto-generate-container">
      <!-- 路由选择器 -->
      <RouteSelector
        ref="routeSelectorRef"
        :routes="allRoutes"
        :loading="loading"
        @update:routes="(routes) => (allRoutes = routes)"
      />
    </div>
  </ZqDialog>
</template>

<style scoped lang="scss">
.auto-generate-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}
</style>
