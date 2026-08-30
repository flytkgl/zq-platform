<script setup lang="ts">
import type { TableConfig } from './store/formDesignStore';

import { ref, watch } from 'vue';

import AttributePanel from './components/AttributePanel.vue';
import DesignCanvas from './components/DesignCanvas.vue';
import MaterialPanel from './components/MaterialPanel.vue';
import WriteBackRuleEditor from './components/WriteBackRuleEditor.vue';
import { useFormDesignStore } from './store/formDesignStore';

const props = defineProps<{
  dataSource?: TableConfig[];
  formId?: string;
  formCode?: string;
  formName?: string;
  readonly?: boolean;
}>();

const store = useFormDesignStore();
const materialPanelRef = ref<InstanceType<typeof MaterialPanel>>();
const writebackMode = ref(false);
const selectedWritebackRuleId = ref<string>();

function openNewWritebackRule() {
  selectedWritebackRuleId.value = undefined;
}
function openWritebackRule(id: string) {
  selectedWritebackRuleId.value = id;
}
function closeWritebackEditor() {
  selectedWritebackRuleId.value = undefined;
}
function saveWritebackRule() {
  materialPanelRef.value?.refreshWritebackRules();
  selectedWritebackRuleId.value = undefined;
}

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
      <MaterialPanel
        ref="materialPanelRef"
        :form-id="props.formId"
        :readonly="props.readonly"
        @writeback-mode-change="writebackMode = $event"
        @writeback-create="openNewWritebackRule"
        @writeback-edit="openWritebackRule"
      />
    </div>

    <!-- Center: Design Canvas -->
    <div class="relative h-full flex-1 overflow-hidden">
      <WriteBackRuleEditor
        v-if="writebackMode"
        :form-id="props.formId"
        :source-form-name="props.formName"
        :table-configs="props.dataSource || []"
        :rule-id="selectedWritebackRuleId"
        :readonly="props.readonly"
        @saved="saveWritebackRule"
        @cancel="closeWritebackEditor"
      />
      <DesignCanvas v-else />
    </div>

    <!-- Right: Attribute Panel -->
    <div v-if="!writebackMode" class="h-full flex-shrink-0">
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
