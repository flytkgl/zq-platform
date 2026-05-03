<script setup lang="ts">
import type { TableConfig } from './store/formDesignStore';

import { watch } from 'vue';

import AttributePanel from './components/AttributePanel.vue';
import DesignCanvas from './components/DesignCanvas.vue';
import MaterialPanel from './components/MaterialPanel.vue';
import { useFormDesignStore } from './store/formDesignStore';

const props = defineProps<{
  dataSource?: TableConfig[];
}>();

const store = useFormDesignStore();

// 监听数据源变化，更新 Store
watch(
  () => props.dataSource,
  (val) => {
    if (val) {
      store.setDataSource(val);
    }
  },
  { immediate: true, deep: true },
);
</script>

<template>
  <div
    class="form-design-container bg-background-deep flex h-full w-full gap-3 overflow-hidden"
  >
    <!-- Left: Material Panel -->
    <div class="h-full w-72 flex-shrink-0">
      <MaterialPanel />
    </div>

    <!-- Center: Design Canvas -->
    <div class="relative h-full flex-1 overflow-hidden">
      <DesignCanvas />
    </div>

    <!-- Right: Attribute Panel -->
    <div class="h-full flex-shrink-0">
      <AttributePanel />
    </div>
  </div>
</template>

<style scoped>
.form-design-container {
  /* Ensure container takes full height relative to its parent */
  height: 100%;
}
</style>
