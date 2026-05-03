<script lang="ts" setup>
/**
 * 页面发布信息编辑器
 * 供 page-manager 和工作流节点共用
 */
import type { MenuItem } from '#/components/zq-form/zq-menu-selector/types';

import { watch } from 'vue';

import { $t } from '@vben/locales';

import { ElForm, ElFormItem, ElInput, ElInputNumber } from 'element-plus';

import { ZqIconPicker } from '#/components/zq-form/zq-icon-picker';
import { ZqMenuSelector } from '#/components/zq-form/zq-menu-selector';
import { useAppContextStore } from '#/store/app-context';

export interface PagePublishInfo {
  menu_name: string;
  menu_parent_id?: string;
  menu_icon: string;
  menu_order: number;
}

interface Props {
  modelValue: PagePublishInfo;
  pageCode?: string;
  showRouteInfo?: boolean;
  routePrefix?: string;
}

const props = withDefaults(defineProps<Props>(), {
  pageCode: '',
  showRouteInfo: true,
  routePrefix: '/page/',
});

const emit = defineEmits<{
  'update:modelValue': [value: PagePublishInfo];
}>();

const appContextStore = useAppContextStore();

// 更新表单数据
function updateFormData(key: keyof PagePublishInfo, value: any) {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: value,
  });
}

// 菜单选择回调
function handleMenuChange(menu: MenuItem | MenuItem[] | null) {
  if (menu && !Array.isArray(menu)) {
    updateFormData('menu_parent_id', menu.id);
  } else {
    updateFormData('menu_parent_id', undefined);
  }
}

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  () => {},
  { deep: true },
);
</script>

<template>
  <ElForm :model="modelValue" label-width="100px">
    <!-- 菜单配置 -->
    <div class="mb-4 font-medium">
      {{ $t('page-manager.publishDialog.menuConfig') }}
    </div>

    <ElFormItem :label="$t('page-manager.publishDialog.menuName')" required>
      <ElInput
        :model-value="modelValue.menu_name"
        :placeholder="$t('page-manager.placeholder.name')"
        @update:model-value="updateFormData('menu_name', $event)"
      />
    </ElFormItem>

    <ElFormItem :label="$t('page-manager.publishDialog.parentMenu')">
      <ZqMenuSelector
        :model-value="modelValue.menu_parent_id || null"
        mode="dialog"
        :placeholder="$t('page-manager.publishDialog.parentMenuPlaceholder')"
        :application-id="appContextStore.currentApp?.id"
        @change="handleMenuChange"
      />
    </ElFormItem>

    <ElFormItem :label="$t('page-manager.publishDialog.menuIcon')">
      <ZqIconPicker
        :model-value="modelValue.menu_icon"
        prefix="lucide"
        :auto-fetch-api="false"
        class="w-full"
        @update:model-value="updateFormData('menu_icon', $event)"
      />
    </ElFormItem>

    <ElFormItem :label="$t('common.sort')">
      <ElInputNumber
        :model-value="modelValue.menu_order"
        :min="0"
        :max="9999"
        class="w-full"
        @update:model-value="updateFormData('menu_order', $event ?? 0)"
      />
    </ElFormItem>

    <!-- 路由信息 -->
    <template v-if="showRouteInfo && pageCode">
      <div class="mb-4 mt-6 font-medium">
        {{ $t('page-manager.publishDialog.routeInfo') }}
      </div>

      <ElFormItem :label="$t('page-manager.publishDialog.accessPath')">
        <ElInput
          :model-value="`${routePrefix}${pageCode}`"
          disabled
          class="text-muted-foreground"
        />
      </ElFormItem>
    </template>
  </ElForm>
</template>
