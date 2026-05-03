<script lang="ts" setup>
/**
 * 子表单容器组件
 * 用于在 Dialog/Drawer/Page 模式下显示子表单
 * 注意：Layout 模式由 FormDataList 直接处理，不使用此组件
 */
import type { FormMeta } from '#/api/online-dev/form-manager';

import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { ElMessage } from 'element-plus';

import { getFormByCodeApi } from '#/api/online-dev/form-manager';
import { ZqDialog } from '#/components/zq-dialog';
import { ZqDrawer } from '#/components/zq-drawer';

import FormDataList from './FormDataList.vue';

interface SubTableButtonConfig {
  id: string;
  subTableName: string;
  subFormCode: string;
  buttonText: string;
  buttonIcon?: string;
  buttonType?:
    | 'danger'
    | 'default'
    | 'info'
    | 'primary'
    | 'success'
    | 'warning';
  containerType: 'dialog' | 'drawer' | 'layout' | 'page';
  containerConfig: {
    direction?: 'btt' | 'ltr' | 'rtl' | 'ttb';
    fullscreen?: boolean;
    renderMode?: 'condition' | 'route';
    size?: string;
    width?: string;
  };
  foreignKeyField?: string;
}

interface Props {
  modelValue: boolean;
  buttonConfig: SubTableButtonConfig;
  mainRecordId: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  closed: [];
  'update:modelValue': [value: boolean];
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

// 子表单元数据
const subFormMeta = ref<FormMeta | null>(null);
const loading = ref(false);

// 对话框/抽屉标题
const containerTitle = computed(() => {
  return (
    props.buttonConfig?.buttonText || $t('form-manager.formRender.subTableData')
  );
});

// 初始过滤条件（自动过滤当前主表记录的子表数据）
const initialFilters = computed(() => {
  if (!props.buttonConfig?.foreignKeyField || !props.mainRecordId) {
    return {};
  }
  return {
    [props.buttonConfig.foreignKeyField]: {
      type: 'eq',
      value: props.mainRecordId,
    },
  };
});

// 新增时的默认数据（自动填充外键）
const defaultFormData = computed(() => {
  if (!props.buttonConfig?.foreignKeyField || !props.mainRecordId) {
    return {};
  }
  return {
    [props.buttonConfig.foreignKeyField]: props.mainRecordId,
  };
});

// 加载子表单元数据
async function loadSubFormMeta() {
  if (!props.buttonConfig?.subFormCode) return;

  loading.value = true;
  try {
    subFormMeta.value = await getFormByCodeApi(props.buttonConfig.subFormCode);
  } catch (error) {
    console.error('加载子表单失败:', error);
    ElMessage.error($t('form-manager.formRender.loadSubFormFailed'));
  } finally {
    loading.value = false;
  }
}

// 关闭容器
function handleClose() {
  visible.value = false;
  emit('closed');
}

// 监听弹窗打开
watch(
  () => props.modelValue,
  async (val) => {
    if (val) {
      await loadSubFormMeta();
    }
  },
  { immediate: true },
);
</script>

<template>
  <!-- Dialog 模式 -->
  <ZqDialog
    v-if="buttonConfig?.containerType === 'dialog'"
    v-model="visible"
    :title="containerTitle"
    :width="buttonConfig?.containerConfig?.width || '80%'"
    :default-fullscreen="buttonConfig?.containerConfig?.fullscreen ?? false"
    :show-footer="false"
    destroy-on-close
    @closed="handleClose"
  >
    <div v-loading="loading" class="sub-table-form-content min-h-[400px]">
      <FormDataList
        v-if="subFormMeta"
        :form-code="buttonConfig.subFormCode"
        :initial-filters="initialFilters"
        :default-form-data="defaultFormData"
      />
    </div>
  </ZqDialog>

  <!-- Drawer 模式 -->
  <ZqDrawer
    v-else-if="buttonConfig?.containerType === 'drawer'"
    v-model="visible"
    :title="containerTitle"
    :size="buttonConfig?.containerConfig?.size || '70%'"
    :direction="buttonConfig?.containerConfig?.direction || 'rtl'"
    destroy-on-close
    @closed="handleClose"
  >
    <div v-loading="loading" class="sub-table-form-content min-h-[400px]">
      <FormDataList
        v-if="subFormMeta"
        :form-code="buttonConfig.subFormCode"
        :initial-filters="initialFilters"
        :default-form-data="defaultFormData"
      />
    </div>
  </ZqDrawer>

  <!-- Page 模式 - 使用全屏 Dialog -->
  <ZqDialog
    v-else-if="buttonConfig?.containerType === 'page'"
    v-model="visible"
    :title="containerTitle"
    :default-fullscreen="true"
    :show-footer="false"
    destroy-on-close
    @closed="handleClose"
  >
    <div v-loading="loading" class="sub-table-form-content h-full">
      <FormDataList
        v-if="subFormMeta"
        :form-code="buttonConfig.subFormCode"
        :initial-filters="initialFilters"
        :default-form-data="defaultFormData"
      />
    </div>
  </ZqDialog>
</template>

<style scoped>
.sub-table-form-content {
  display: flex;
  flex-direction: column;
}
</style>
