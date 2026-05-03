<script lang="ts" setup>
import { useUserStore } from '@vben/stores';

import OrgChartPanel from './modules/OrgChartPanel.vue';

const userStore = useUserStore();
const currentUserId = userStore.userInfo?.id;
</script>

<template>
  <div class="org-chart-page">
    <div class="org-chart-content">
      <OrgChartPanel :user-id="currentUserId" />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.org-chart-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 12px;
}

.org-chart-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: var(--el-bg-color);
  border-radius: 8px;
}
</style>
