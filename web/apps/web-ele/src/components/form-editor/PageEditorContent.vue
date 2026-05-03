<script lang="ts" setup>
/**
 * 页面编辑器内容组件
 * 包含步骤条和所有步骤内容，可用于 Modal 或工作流节点确认面板
 * 步骤：1.基础信息 -> 2.页面设计 -> 3.发布（工作流模式）
 */
import type { PageBasicInfo } from './PageBasicInfoEditor.vue';
import type { PagePublishInfo } from './PagePublishInfoEditor.vue';

import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { ElButton } from 'element-plus';

import DashboardDesign from '#/components/dashboard-design/index.vue';
import { useDashboardDesignStore } from '#/components/dashboard-design/store/dashboardDesignStore';

import PageBasicInfoEditor from './PageBasicInfoEditor.vue';
import PagePublishInfoEditor from './PagePublishInfoEditor.vue';

// 导出的数据类型
export interface PageEditorData {
  basicForm: PageBasicInfo;
  pageConfig: Record<string, any>;
  publishData?: PagePublishInfo;
}

// 组件属性
interface Props {
  // 当前步骤（0-2），外部控制时使用
  step?: number;
  // 是否显示步骤条
  showSteps?: boolean;
  // 是否显示操作按钮
  showActions?: boolean;
  // 是否为只读模式
  readonly?: boolean;
  // 工作流模式：显示发布步骤
  workflowMode?: boolean;
  // 是否为编辑模式（编码不可修改）
  isEditMode?: boolean;
  // 初始基础信息
  initialBasicForm?: PageBasicInfo;
  // 初始页面配置
  initialPageConfig?: Record<string, any>;
  // 初始发布数据
  initialPublishData?: PagePublishInfo;
}

const props = withDefaults(defineProps<Props>(), {
  step: undefined,
  showSteps: true,
  showActions: true,
  readonly: false,
  workflowMode: false,
  isEditMode: false,
  initialBasicForm: undefined,
  initialPageConfig: undefined,
  initialPublishData: undefined,
});

const emit = defineEmits<{
  cancel: [];
  save: [data: PageEditorData];
  'step-change': [step: number];
  'update:step': [step: number];
}>();

const dashboardDesignStore = useDashboardDesignStore();

// 当前步骤（内部状态）
const internalStep = ref(0);

// 计算当前步骤（支持外部控制）
const currentStep = computed({
  get: () => (props.step === undefined ? internalStep.value : props.step),
  set: (val) => {
    if (props.step === undefined) {
      internalStep.value = val;
    } else {
      emit('update:step', val);
    }
    emit('step-change', val);
  },
});

// 基础信息表单
const basicForm = ref<PageBasicInfo>({
  name: '',
  code: '',
  category: 'dashboard',
  description: '',
  sort: 0,
});

// 发布配置数据（工作流模式）
const publishData = ref<PagePublishInfo>({
  menu_name: '',
  menu_parent_id: undefined,
  menu_icon: 'lucide:layout-dashboard',
  menu_order: 0,
});

// 步骤定义
const steps = computed(() => {
  const baseSteps = [
    { title: $t('page-manager.editor.steps.basic'), index: 1 },
    { title: $t('page-manager.editor.steps.design'), index: 2 },
  ];
  // 工作流模式下添加发布步骤
  if (props.workflowMode) {
    baseSteps.push({
      title: $t('page-manager.editor.steps.publish'),
      index: 3,
    });
  }
  return baseSteps;
});

// 是否可以进入下一步
const canGoNext = computed(() => {
  if (currentStep.value === 0) {
    return basicForm.value.name && basicForm.value.code;
  }
  return true;
});

const canGoPrev = computed(() => currentStep.value > 0);
const isLastStep = computed(() => currentStep.value === steps.value.length - 1);

// 监听初始数据
watch(
  () => props.initialBasicForm,
  (val) => {
    if (val) {
      basicForm.value = { ...val };
      // 同步菜单名称
      if (props.workflowMode && !publishData.value.menu_name) {
        publishData.value.menu_name = val.name;
      }
    }
  },
  { immediate: true },
);

watch(
  () => props.initialPageConfig,
  (val) => {
    if (val && Object.keys(val).length > 0) {
      dashboardDesignStore.importConfig(JSON.stringify(val));
    }
  },
  { immediate: true },
);

watch(
  () => props.initialPublishData,
  (val) => {
    if (val) {
      publishData.value = { ...val };
    }
  },
  { immediate: true },
);

// 监听基础信息变化，同步菜单名称
watch(
  () => basicForm.value.name,
  (name) => {
    if (props.workflowMode && name && !publishData.value.menu_name) {
      publishData.value.menu_name = name;
    }
  },
);

// 上一步
function handlePrev() {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
}

// 下一步
function handleNext() {
  if (currentStep.value < steps.value.length - 1 && canGoNext.value) {
    currentStep.value++;
  }
}

// 保存
function handleSave() {
  const pageConfig = JSON.parse(dashboardDesignStore.exportConfig());

  const data: PageEditorData = {
    basicForm: { ...basicForm.value },
    pageConfig,
  };

  if (props.workflowMode) {
    data.publishData = { ...publishData.value };
  }

  emit('save', data);
}

// 取消
function handleCancel() {
  emit('cancel');
}

// 获取当前数据（供外部调用）
function getData(): PageEditorData {
  const pageConfig = JSON.parse(dashboardDesignStore.exportConfig());

  const data: PageEditorData = {
    basicForm: { ...basicForm.value },
    pageConfig,
  };

  if (props.workflowMode) {
    data.publishData = { ...publishData.value };
  }

  return data;
}

// 设置数据（供外部调用）
function setData(data: Partial<PageEditorData>) {
  if (data.basicForm) {
    basicForm.value = { ...data.basicForm };
  }
  if (data.pageConfig && Object.keys(data.pageConfig).length > 0) {
    dashboardDesignStore.importConfig(JSON.stringify(data.pageConfig));
  }
  if (data.publishData) {
    publishData.value = { ...data.publishData };
  }
}

// 重置
function reset() {
  basicForm.value = {
    name: '',
    code: '',
    category: 'dashboard',
    description: '',
    sort: 0,
  };
  publishData.value = {
    menu_name: '',
    menu_parent_id: undefined,
    menu_icon: 'lucide:layout-dashboard',
    menu_order: 0,
  };
  dashboardDesignStore.clearCanvas();
  currentStep.value = 0;
}

// 暴露方法
defineExpose({
  getData,
  setData,
  reset,
  currentStep,
});
</script>

<template>
  <div class="page-editor-content flex h-full flex-col">
    <!-- 步骤条 -->
    <div
      v-if="showSteps"
      class="border-border bg-background flex-shrink-0 border-b px-4 py-3"
    >
      <div class="flex items-center justify-center gap-2">
        <template v-for="(step, index) in steps" :key="step.index">
          <div
            class="flex cursor-pointer items-center gap-2 rounded-full px-3 py-1.5 text-sm transition-colors"
            :class="{
              'bg-primary text-primary-foreground': index === currentStep,
              'text-muted-foreground hover:text-foreground':
                index !== currentStep,
            }"
            @click="index <= currentStep ? (currentStep = index) : null"
          >
            <span
              class="flex h-5 w-5 items-center justify-center rounded-full text-xs"
              :class="{
                'bg-primary-foreground text-primary': index === currentStep,
                'bg-muted': index !== currentStep,
              }"
            >
              {{ step.index }}
            </span>
            {{ step.title }}
          </div>
          <div
            v-if="index < steps.length - 1"
            class="bg-border h-[1px] w-6"
            :class="{ 'bg-primary/50': index < currentStep }"
          ></div>
        </template>
      </div>
    </div>

    <!-- 步骤内容 -->
    <div class="flex-1 overflow-hidden">
      <!-- 步骤1: 基础信息 -->
      <div
        v-show="currentStep === 0"
        class="flex h-full items-center justify-center overflow-y-auto"
      >
        <div class="w-full max-w-[600px] px-4">
          <div class="border-border bg-card rounded-lg border p-6 shadow-sm">
            <PageBasicInfoEditor
              v-model="basicForm"
              :is-edit-mode="isEditMode"
              :show-title="true"
            />
          </div>
        </div>
      </div>

      <!-- 步骤2: 页面设计 -->
      <div v-show="currentStep === 1" class="h-full overflow-hidden">
        <DashboardDesign :readonly="readonly" />
      </div>

      <!-- 步骤3: 发布（仅工作流模式） -->
      <div
        v-if="workflowMode"
        v-show="currentStep === 2"
        class="flex h-full items-center justify-center overflow-y-auto"
      >
        <div class="w-full max-w-[600px] px-4">
          <div class="border-border bg-card rounded-lg border p-6 shadow-sm">
            <h3 class="mb-6 text-center text-lg font-medium">
              {{ $t('page-manager.editor.steps.publish') }}
            </h3>
            <PagePublishInfoEditor
              v-model="publishData"
              :page-code="basicForm.code"
              :show-route-info="true"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div
      v-if="showActions"
      class="border-border bg-background flex-shrink-0 border-t px-4 py-3"
    >
      <div class="flex items-center justify-end gap-3">
        <ElButton v-if="canGoPrev" @click="handlePrev">
          {{ $t('common.prev') }}
        </ElButton>
        <ElButton
          v-if="!isLastStep"
          type="primary"
          :disabled="!canGoNext"
          @click="handleNext"
        >
          {{ $t('common.next') }}
        </ElButton>
        <ElButton v-if="isLastStep" type="primary" @click="handleSave">
          {{ $t('common.save') }}
        </ElButton>
        <ElButton @click="handleCancel">{{ $t('common.cancel') }}</ElButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-editor-content {
  min-height: 0;
}
</style>
