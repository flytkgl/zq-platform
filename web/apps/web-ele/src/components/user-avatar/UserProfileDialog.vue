<script lang="ts" setup>
import { computed } from 'vue';

import { ZqDialog } from '#/components/zq-dialog';
import { $t } from '#/locales';
import OrgChartPanel from '#/views/_core/org-chart/modules/OrgChartPanel.vue';

defineOptions({
  name: 'UserProfileDialog',
});

const props = defineProps<{
  modelValue: boolean;
  userId: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="$t('user-avatar.profile.organization')"
    width="80%"
    :show-footer="false"
    content-height="70vh"
    destroy-on-close
  >
    <div class="org-chart-wrapper">
      <OrgChartPanel :user-id="userId" :show-mode-toggle="true" />
    </div>
  </ZqDialog>
</template>

<style lang="scss" scoped>
.org-chart-wrapper {
  height: 65vh;
  overflow: hidden;
}
</style>
