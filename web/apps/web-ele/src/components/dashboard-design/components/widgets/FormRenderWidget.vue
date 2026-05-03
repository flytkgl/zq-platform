<script setup lang="ts">
import type { DashboardWidget } from '../../store/dashboardDesignStore';

import { computed } from 'vue';

import { ListChecks } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElEmpty } from 'element-plus';

import FormDataList from '#/views/online-dev/form-render/components/FormDataList.vue';

const props = defineProps<{
  isDesignMode?: boolean;
  widget: DashboardWidget;
}>();

const formCode = computed(() => props.widget.props.formCode || '');
</script>

<template>
  <div class="form-render-widget flex h-full flex-col">
    <div v-if="widget.props.title" class="widget-header">
      <span class="text-muted-foreground text-sm font-medium">{{
        widget.props.title
      }}</span>
    </div>

    <div v-if="isDesignMode" class="design-placeholder">
      <ListChecks class="h-8 w-8 text-gray-400" />
      <div class="mt-2 text-sm text-gray-500">
        {{ $t('dashboard-design.widgets.formRender.placeholder') }}
      </div>
      <div class="mt-1 text-xs text-gray-400">
        {{ formCode || $t('dashboard-design.widgets.formRender.noFormCode') }}
      </div>
    </div>

    <template v-else>
      <div v-if="!formCode" class="empty-state">
        <ElEmpty
          :description="$t('dashboard-design.widgets.formRender.noFormCode')"
        />
      </div>

      <div v-else class="min-h-0 flex-1 overflow-hidden">
        <FormDataList :form-code="formCode" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.widget-header {
  padding: 8px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.design-placeholder,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}

.design-placeholder {
  background: var(--el-fill-color-lighter);
}
</style>
