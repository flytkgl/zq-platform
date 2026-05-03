<script lang="ts" setup>
/**
 * 设计编辑面板
 * 用于工作流中每步设计完成后的编辑
 * 使用 FormEditorContent 公共组件，根据当前步骤显示对应内容
 */
import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';
import { Maximize, Minimize } from '@vben/icons';

import { ElButton } from 'element-plus';

import FormEditorContent from './FormEditorContent.vue';

// 设计类型
export type DesignType = 'form_basic_info' | 'database_design' | 'form_ui_design' | 'list_config' | 'form_publish' | 'dashboard_basic_info' | 'dashboard_design' | 'dashboard_publish';

// 设计数据
export interface DesignData {
  type: DesignType;
  title: string;
  data: Record<string, any>;
  nodeId: string;
  form_fields?: any[]; // 表单字段列表（用于列表设计）
  table_configs?: any[]; // 数据表配置（用于表单设计）
}

interface Props {
  visible: boolean;
  design?: DesignData;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:visible': [value: boolean];
  'save': [data: Record<string, any>];
  'confirm': [data: Record<string, any>];
  'close': [];
}>();

// 编辑器组件引用
const editorRef = ref<InstanceType<typeof FormEditorContent>>();

// 根据设计类型映射到步骤索引
const stepMap: Record<DesignType, number> = {
  'form_basic_info': 0,
  'database_design': 1,
  'form_ui_design': 2,
  'list_config': 3,
  'form_publish': 4,
  'dashboard_basic_info': 0,
  'dashboard_design': 0,
  'dashboard_publish': 0,
};

// 当前步骤
const currentStep = ref(0);

// 面板标题
const panelTitle = computed(() => {
  if (!props.design) return '';
  return props.design.title;
});

// 全屏状态
const isFullscreen = ref(false);

// 切换全屏
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

// 监听设计数据变化，设置当前步骤和初始化数据
watch(
  () => props.design,
  (newDesign) => {
    if (!newDesign) return;
    
    // 根据设计类型设置当前步骤
    currentStep.value = stepMap[newDesign.type] ?? 0;
    
    // 初始化编辑器数据
    if (editorRef.value) {
      initEditorData(newDesign);
    }
  },
  { immediate: true }
);

// 监听编辑器引用变化，初始化数据
watch(
  () => editorRef.value,
  (editor) => {
    if (editor && props.design) {
      initEditorData(props.design);
    }
  }
);

// 初始化编辑器数据
function initEditorData(design: DesignData) {
  if (!editorRef.value) return;
  
  switch (design.type) {
    case 'form_basic_info': {
      const data = design.data || {};
      editorRef.value.setData({
        basicForm: {
          name: data.name || '',
          code: data.code || '',
          form_type: data.form_type || 'normal',
          sort: data.sort || 0,
          description: data.description || '',
        },
      });
      break;
    }
    case 'database_design': {
      const tableData = design.data?.table || design.data || {};
      // 优先从 meta 中读取 schema，兼容旧数据从顶层读取
      const metaData = tableData.meta || {};
      editorRef.value.setData({
        tableConfigs: [{
          id: 'main-table',
          type: 'main',
          tableName: tableData.tableName || '',
          alias: tableData.alias || tableData.tableName || '',
          fields: tableData.fields || [],
          meta: {
            schema: metaData.schema || tableData.schema || '',
            schemaRaw: metaData.schemaRaw || tableData.schemaRaw || '',
            database: metaData.database || tableData.database || '',
          },
        }],
      });
      break;
    }
    case 'form_ui_design': {
      const formConfig = design.data || {};
      // 从 design 中获取 table_configs（后端在 waiting_config 中传递）
      const tableConfigs = design.table_configs || design.data?.table_configs || [];
      editorRef.value.setData({
        tableConfigs: tableConfigs,
        formConfig: {
          items: formConfig.items || [],
          labelWidth: formConfig.labelWidth || 120,
          labelPosition: formConfig.labelPosition || 'right',
          size: formConfig.size || 'default',
          formPadding: formConfig.formPadding || 20,
          formMargin: formConfig.formMargin || 0,
          itemSpacing: formConfig.itemSpacing || 18,
          formWidth: formConfig.formWidth || '100%',
          formMaxWidth: formConfig.formMaxWidth || 0,
          formBackground: formConfig.formBackground || false,
          formBorder: formConfig.formBorder || false,
          formBorderRadius: formConfig.formBorderRadius || 4,
          formShadow: formConfig.formShadow || false,
          disabled: formConfig.disabled || false,
          tableConfigs: tableConfigs,
        },
      });
      break;
    }
    case 'list_config': {
      // 从 design 中获取 form_fields（后端在 waiting_config 中传递）
      const formFields = design.form_fields || design.data?.form_fields || [];
      editorRef.value.setData({
        listConfig: design.data || {},
        formFields: formFields,
      });
      break;
    }
    case 'form_publish': {
      const publishData = design.data || {};
      editorRef.value.setData({
        publishData: {
          menu_name: publishData.menu_name || '',
          menu_parent_id: publishData.menu_parent_id,
          menu_icon: publishData.menu_icon || 'lucide:file-text',
          menu_order: publishData.menu_order ?? 1,
        },
      });
      break;
    }
  }
}

// 获取当前编辑的数据
function getCurrentData(): Record<string, any> {
  if (!editorRef.value) return {};
  
  const data = editorRef.value.getData();
  const designType = props.design?.type;
  
  switch (designType) {
    case 'form_basic_info':
      return { ...data.basicForm };
    case 'database_design':
      return {
        type: data.tableConfigs[0]?.type || 'main', // 添加 type 字段，默认为 main
        table: data.tableConfigs[0] ? {
          tableName: data.tableConfigs[0].tableName,
          alias: data.tableConfigs[0].alias,
          fields: data.tableConfigs[0].fields,
          meta: {
            schema: data.tableConfigs[0].meta?.schema || '',
            schemaRaw: data.tableConfigs[0].meta?.schemaRaw || '',
            database: data.tableConfigs[0].meta?.database || '',
          },
        } : {},
        dbConfig: props.design?.data?.dbConfig || 'default', // 保留原有的 dbConfig
      };
    case 'form_ui_design':
      return {
        items: data.formConfig.items,
        labelWidth: data.formConfig.labelWidth,
        labelPosition: data.formConfig.labelPosition,
      };
    case 'list_config':
      return { ...data.listConfig };
    case 'form_publish':
      return { ...data.publishData };
    default:
      return {};
  }
}

// 确认并继续
function handleConfirm() {
  const data = getCurrentData();
  emit('confirm', data);
}

// 关闭
function handleClose() {
  emit('update:visible', false);
  emit('close');
}
</script>

<template>
  <div
    v-if="visible"
    :class="[
      'border-border bg-card flex flex-col rounded-lg',
      isFullscreen ? 'fixed inset-0 z-50 ml-0' : 'ml-3 h-full w-full'
    ]"
  >
    <!-- 头部 -->
    <div
      class="border-border bg-muted/50 flex items-center justify-between border-b px-4 py-3"
    >
      <div class="text-foreground font-medium">
        {{ panelTitle }}
      </div>
      <div class="flex items-center gap-2">
        <ElButton size="small" @click="handleClose">{{ $t('common.cancel') }}</ElButton>
        <ElButton size="small" type="primary" @click="handleConfirm">{{ $t('common.confirmAndContinue') }}</ElButton>
        <ElButton 
          link 
          :icon="isFullscreen ? Minimize : Maximize" 
          :title="isFullscreen ? '退出全屏' : '全屏'"
          @click="toggleFullscreen" 
        />
      </div>
    </div>

    <!-- 内容区域：使用 FormEditorContent 公共组件 -->
    <div class="flex-1 overflow-hidden">
      <FormEditorContent
        ref="editorRef"
        :step="currentStep"
        :show-steps="true"
        :show-actions="false"
        :workflow-mode="true"
        @update:step="currentStep = $event"
      />
    </div>
  </div>
</template>

<style scoped>
.design-editor-panel {
  /* box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1); */
}
</style>
