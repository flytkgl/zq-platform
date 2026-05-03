<script lang="ts" setup>
import { onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import { ElEmpty, ElMessage, ElScrollbar } from 'element-plus';

import { getPageByCodeApi } from '#/api/online-dev/page-manager';
import DashboardRenderer from '#/components/dashboard-design/DashboardRenderer.vue';

defineOptions({ name: 'PageRender' });

const route = useRoute();
const loading = ref(false);
const pageConfig = ref<string>('');
const pageName = ref('');
const pageCode = ref('');

// 获取页面编码
function getPageCode(): string {
  // 优先从 query 获取
  if (route.query.pageCode) {
    return route.query.pageCode as string;
  }

  // 其次从 params 获取
  if (route.params.code) {
    return route.params.code as string;
  }

  // 最后从路径中提取（路径格式：/page-render/xxx）
  const pathParts = route.path.split('/').filter(Boolean);
  const length = pathParts.length;
  if (length >= 2 && pathParts[length - 2] === 'page-render') {
    return pathParts[length - 1] || '';
  }

  return '';
}

// 加载页面数据
async function loadPageData() {
  const code = getPageCode();
  if (!code) {
    ElMessage.error('页面编码不能为空');
    return;
  }

  pageCode.value = code;
  loading.value = true;

  try {
    const page = await getPageByCodeApi(code);
    pageName.value = page.name;
    pageConfig.value =
      page.page_config && Object.keys(page.page_config).length > 0
        ? JSON.stringify(page.page_config)
        : '';
  } catch (error: any) {
    ElMessage.error(error?.message || '加载页面失败');
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadPageData();
});

// 监听路由变化
watch(
  () => route.fullPath,
  () => {
    loadPageData();
  },
);
</script>

<template>
  <ElScrollbar class="rounded-[8px] py-3">
    <div v-loading="loading" class="h-[calc(100vh-120px)] rounded-[8px] px-3">
      <DashboardRenderer v-if="pageConfig" :config="pageConfig" />
      <ElEmpty v-else-if="!loading" description="暂无页面配置" />
    </div>
  </ElScrollbar>
</template>
