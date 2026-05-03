<script lang="ts" setup>
import type { TableConfig } from '#/views/online-dev/form-manager/modules/data-source-config.vue';
/**
 * 表单编辑器内容组件
 * 包含步骤条和所有步骤内容，可用于 Modal 或右侧面板
 */
import type { ValidationError } from '#/views/online-dev/form-manager/utils/formValidator';

import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { CircleClose, Warning } from '@element-plus/icons-vue';
import {
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElOption,
  ElScrollbar,
  ElSelect,
} from 'element-plus';

import FormDesign from '#/components/form-design/index.vue';
import { useFormDesignStore } from '#/components/form-design/store/formDesignStore';
import PublishInfoEditor from '#/components/form-editor/PublishInfoEditor.vue';
import DataSourceConfig from '#/views/online-dev/form-manager/modules/data-source-config.vue';
import ListDesign from '#/views/online-dev/form-manager/modules/list-design.vue';
import { validateFormConfig } from '#/views/online-dev/form-manager/utils/formValidator';

// 基础信息表单类型
export interface BasicFormData {
  name: string;
  code: string;
  form_type: 'normal' | 'workflow';
  sort: number;
  description: string;
}

// 组件属性
interface Props {
  // 当前步骤（0-3），外部控制时使用
  step?: number;
  // 是否显示步骤条
  showSteps?: boolean;
  // 是否显示操作按钮
  showActions?: boolean;
  // 是否为只读模式
  readonly?: boolean;
  // 工作流模式：隐藏左侧数据库树，主表/从表可编辑
  workflowMode?: boolean;
  // 初始基础信息
  initialBasicForm?: BasicFormData;
  // 初始表配置
  initialTableConfigs?: TableConfig[];
  // 初始列表设计数据
  initialListDesign?: Record<string, any>;
}

const props = withDefaults(defineProps<Props>(), {
  step: undefined,
  showSteps: true,
  showActions: true,
  readonly: false,
  workflowMode: false,
  initialBasicForm: undefined,
  initialTableConfigs: undefined,
  initialListDesign: undefined,
});

const emit = defineEmits<{
  cancel: [];
  save: [data: FormEditorData];
  'step-change': [step: number];
  'update:step': [step: number];
}>();

// 发布配置数据类型
export interface PublishFormData {
  menu_name: string;
  menu_parent_id?: string;
  menu_icon: string;
  menu_order: number;
}

// 导出的数据类型
export interface FormEditorData {
  basicForm: BasicFormData;
  tableConfigs: TableConfig[];
  formConfig: {
    disabled: boolean;
    formBackground: boolean;
    formBorder: boolean;
    formBorderRadius: number;
    formMargin: number;
    formMaxWidth: number;
    formPadding: number;
    formShadow: boolean;
    formWidth: string;
    items: any[];
    itemSpacing: number;
    labelPosition: 'left' | 'right' | 'top';
    labelWidth: number;
    size: 'default' | 'large' | 'small';
    tableConfigs: TableConfig[];
  };
  listConfig: Record<string, any>;
  formFields: any[];
  publishData?: PublishFormData;
}

const formDesignStore = useFormDesignStore();

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
const basicForm = ref<BasicFormData>({
  name: '',
  code: '',
  form_type: 'normal',
  sort: 0,
  description: '',
});

// 数据表配置
const tableConfigs = ref<TableConfig[]>([]);

// 表单设计字段列表（扁平化）
const formFields = ref<any[]>([]);

// 列表设计组件引用
const listDesignRef = ref();

// 列表设计数据
const listDesignData = ref<Record<string, any>>({});

// 发布配置数据（工作流模式）
const publishData = ref({
  menu_name: '',
  menu_parent_id: undefined as string | undefined,
  menu_icon: 'lucide:file-text',
  menu_order: 0,
});

// 步骤定义
const steps = computed(() => {
  const baseSteps = [
    { title: $t('form-manager.editor.steps.basic'), index: 1 },
    { title: $t('form-manager.editor.steps.database'), index: 2 },
    { title: $t('form-manager.editor.steps.form'), index: 3 },
    { title: $t('form-manager.editor.steps.list'), index: 4 },
  ];
  // 工作流模式下添加发布步骤
  if (props.workflowMode) {
    baseSteps.push({
      title: $t('form-manager.editor.steps.publish'),
      index: 5,
    });
  }
  return baseSteps;
});

// 是否可以进入下一步
const canGoNext = computed(() => {
  if (currentStep.value === 0) {
    return basicForm.value.name && basicForm.value.code;
  }
  if (currentStep.value === 1) {
    const hasMainTable = tableConfigs.value.some((t) => t.type === 'main');
    return hasMainTable;
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
    }
  },
  { immediate: true },
);

watch(
  () => props.initialTableConfigs,
  (val) => {
    if (val) {
      tableConfigs.value = [...val];
    }
  },
  { immediate: true },
);

watch(
  () => props.initialListDesign,
  (val) => {
    if (val) {
      listDesignData.value = { ...val };
      setTimeout(() => {
        listDesignRef.value?.setData(val);
      }, 0);
    }
  },
  { immediate: true },
);

// 根据数据库字段类型判断是否为数值类型
function isNumericDbType(dbType: string): boolean {
  if (!dbType) return false;
  const type = dbType.toLowerCase();
  return (
    type.includes('int') ||
    type.includes('decimal') ||
    type.includes('numeric') ||
    type.includes('float') ||
    type.includes('double') ||
    type.includes('real') ||
    type.includes('money')
  );
}

// 从 tableConfigs 中查找字段的数据库类型
function getFieldDbType(fieldName: string): string {
  const mainTable = tableConfigs.value.find((t) => t.type === 'main');
  if (mainTable) {
    const field = mainTable.fields.find((f: any) => f.name === fieldName);
    if (field) return field.type || '';
  }
  return '';
}

// 递归提取表单字段
function extractFields(items: any[]): any[] {
  const layoutTypes = new Set([
    'alert',
    'collapse',
    'divider',
    'grid',
    'html',
    'spacer',
    'steps',
    'sub-table',
    'tabs',
    'text',
    'timeline',
    'title',
  ]);

  let fields: any[] = [];
  items.forEach((item) => {
    if (layoutTypes.has(item.type)) {
      if (item.children) {
        fields = fields.concat(extractFields(item.children));
      }
      if (item.columns) {
        item.columns.forEach((col: any) => {
          if (col.children) {
            fields = fields.concat(extractFields(col.children));
          }
        });
      }
      if (item.items) {
        item.items.forEach((subItem: any) => {
          if (subItem.children) {
            fields = fields.concat(extractFields(subItem.children));
          }
        });
      }
      return;
    }

    if (item.field) {
      const dbType = getFieldDbType(item.field);
      fields.push({
        label: item.label,
        field: item.field,
        component: item.type,
        options: item.options,
        props: item.props,
        dbType,
        isNumeric: isNumericDbType(dbType),
      });
    }
  });

  // 添加系统字段
  const mainTable = tableConfigs.value.find((t) => t.type === 'main');
  if (mainTable) {
    const systemFields = new Set([
      'sys_create_datetime',
      'sys_creator_id',
      'sys_dept_id',
      'sys_modifier_id',
      'sys_update_datetime',
    ]);
    const existingFieldNames = new Set(fields.map((f) => f.field));

    mainTable.fields.forEach((dbField: any) => {
      if (
        systemFields.has(dbField.name) &&
        !existingFieldNames.has(dbField.name)
      ) {
        const dbType = dbField.type || '';
        let component = 'input';
        let fieldProps: any;

        switch (dbField.name) {
          case 'sys_create_datetime':
          case 'sys_update_datetime': {
            component = 'date-picker';
            fieldProps = { type: 'datetimerange' };

            break;
          }
          case 'sys_creator_id':
          case 'sys_modifier_id': {
            component = 'user-select';

            break;
          }
          case 'sys_dept_id': {
            component = 'dept-select';

            break;
          }
          // No default
        }

        fields.push({
          label: dbField.comment || dbField.name,
          field: dbField.name,
          component,
          options: undefined,
          props: fieldProps,
          dbType,
          isNumeric: isNumericDbType(dbType),
          isSystemField: true,
        });
      }
    });
  }

  return fields;
}

const validationErrors = ref<ValidationError[]>([]);
const validationDialogVisible = ref(false);

function handleNext() {
  if (currentStep.value < steps.value.length - 1) {
    if (currentStep.value === 2) {
      validationErrors.value = [];
      const items = formDesignStore.formConf.items;

      if (items.length === 0) {
        return;
      }

      validationErrors.value = validateFormConfig(items, tableConfigs.value);

      if (validationErrors.value.length > 0) {
        validationDialogVisible.value = true;
        return;
      }

      formFields.value = extractFields(items);
    }
    currentStep.value++;
  }
}

function handlePrev() {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
}

// 获取当前编辑器数据
function getData(): FormEditorData {
  if (listDesignRef.value) {
    listDesignData.value = listDesignRef.value.getData();
  }

  return {
    basicForm: { ...basicForm.value },
    tableConfigs: [...tableConfigs.value],
    formConfig: {
      items: formDesignStore.formConf.items,
      labelWidth: formDesignStore.formConf.labelWidth,
      labelPosition: formDesignStore.formConf.labelPosition as
        | 'left'
        | 'right'
        | 'top',
      size: formDesignStore.formConf.size as 'default' | 'large' | 'small',
      formPadding: formDesignStore.formConf.formPadding,
      formMargin: formDesignStore.formConf.formMargin,
      itemSpacing: formDesignStore.formConf.itemSpacing,
      formWidth: formDesignStore.formConf.formWidth,
      formMaxWidth: Number(formDesignStore.formConf.formMaxWidth) || 0,
      formBackground: Boolean(formDesignStore.formConf.formBackground),
      formBorder: Boolean(formDesignStore.formConf.formBorder),
      formBorderRadius: formDesignStore.formConf.formBorderRadius,
      formShadow: Boolean(formDesignStore.formConf.formShadow),
      disabled: Boolean(formDesignStore.formConf.disabled),
      tableConfigs: [...tableConfigs.value],
    },
    listConfig: { ...listDesignData.value },
    formFields: [...formFields.value],
    publishData: { ...publishData.value },
  };
}

// 设置编辑器数据
function setData(data: Partial<FormEditorData>) {
  if (data.basicForm) {
    basicForm.value = { ...data.basicForm };
  }
  if (data.tableConfigs) {
    tableConfigs.value = [...data.tableConfigs];
  }
  if (data.formConfig) {
    if (data.formConfig.items) {
      formDesignStore.formConf.items = data.formConfig.items;
    }
    if (data.formConfig.labelWidth !== undefined) {
      formDesignStore.formConf.labelWidth = data.formConfig.labelWidth;
    }
    if (data.formConfig.labelPosition) {
      formDesignStore.formConf.labelPosition = data.formConfig.labelPosition;
    }
    if (data.formConfig.size > 0) {
      formDesignStore.formConf.size = data.formConfig.size;
    }
    if (data.formConfig.formPadding !== undefined) {
      formDesignStore.formConf.formPadding = data.formConfig.formPadding;
    }
    if (data.formConfig.formMargin !== undefined) {
      formDesignStore.formConf.formMargin = data.formConfig.formMargin;
    }
    if (data.formConfig.itemSpacing !== undefined) {
      formDesignStore.formConf.itemSpacing = data.formConfig.itemSpacing;
    }
    if (data.formConfig.formWidth) {
      formDesignStore.formConf.formWidth = data.formConfig.formWidth;
    }
    if (data.formConfig.formMaxWidth !== undefined) {
      (formDesignStore.formConf as any).formMaxWidth =
        data.formConfig.formMaxWidth;
    }
    if (data.formConfig.formBackground !== undefined) {
      (formDesignStore.formConf as any).formBackground =
        data.formConfig.formBackground;
    }
    if (data.formConfig.formBorder !== undefined) {
      formDesignStore.formConf.formBorder = data.formConfig.formBorder;
    }
    if (data.formConfig.formBorderRadius !== undefined) {
      formDesignStore.formConf.formBorderRadius =
        data.formConfig.formBorderRadius;
    }
    if (data.formConfig.formShadow !== undefined) {
      formDesignStore.formConf.formShadow = data.formConfig.formShadow;
    }
    if (data.formConfig.disabled !== undefined) {
      formDesignStore.formConf.disabled = data.formConfig.disabled;
    }
  }
  if (data.listConfig) {
    listDesignData.value = { ...data.listConfig };
    setTimeout(() => {
      listDesignRef.value?.setData(data.listConfig);
    }, 0);
  }
  if (data.formFields) {
    formFields.value = [...data.formFields];
  }
  if (data.publishData) {
    publishData.value = {
      menu_name: data.publishData.menu_name || '',
      menu_parent_id: data.publishData.menu_parent_id,
      menu_icon: data.publishData.menu_icon || 'lucide:file-text',
      menu_order: data.publishData.menu_order || 0,
    };
  }
}

// 重置编辑器
function reset() {
  internalStep.value = 0;
  basicForm.value = {
    name: '',
    code: '',
    form_type: 'normal',
    sort: 0,
    description: '',
  };
  tableConfigs.value = [];
  formDesignStore.formConf.items = [];
  formDesignStore.setActive(null);
  listDesignData.value = {};
  listDesignRef.value?.setData({});
  formFields.value = [];
}

function handleSave() {
  emit('save', getData());
}

function handleCancel() {
  emit('cancel');
}

// 跳转到指定步骤
function goToStep(step: number) {
  if (step >= 0 && step < steps.value.length) {
    currentStep.value = step;
  }
}

// 暴露方法
defineExpose({
  getData,
  setData,
  reset,
  goToStep,
  currentStep,
  basicForm,
  tableConfigs,
  formFields,
});
</script>

<template>
  <div class="form-editor-content flex h-full flex-col">
    <!-- 步骤条（工作流模式下隐藏） -->
    <div
      v-if="showSteps && !workflowMode"
      class="border-border bg-background flex-shrink-0 border-b px-4 py-3"
    >
      <div class="flex items-center justify-center">
        <template v-for="(step, index) in steps" :key="index">
          <div
            class="flex cursor-pointer items-center px-3 py-1"
            @click="index < currentStep ? (currentStep = index) : null"
          >
            <div
              class="flex items-center justify-center rounded-full border px-3 py-1 text-sm transition-all"
              :class="[
                index === currentStep
                  ? 'bg-primary/10 border-primary text-primary font-medium'
                  : index < currentStep
                    ? 'border-primary/50 text-primary/80 bg-transparent'
                    : 'border-border text-muted-foreground bg-transparent',
              ]"
            >
              <span
                class="mr-2 flex h-5 w-5 items-center justify-center rounded-full text-xs"
                :class="
                  index === currentStep
                    ? 'bg-primary text-white'
                    : index < currentStep
                      ? 'bg-primary/80 text-white'
                      : 'bg-muted text-muted-foreground'
                "
              >
                {{ step.index }}
              </span>
              {{ step.title }}
            </div>
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
            <h3
              v-if="!workflowMode"
              class="mb-6 text-center text-lg font-medium"
            >
              {{ $t('form-manager.editor.steps.basic') }}
            </h3>
            <ElForm
              :model="basicForm"
              label-width="100px"
              label-position="right"
              :disabled="readonly"
            >
              <ElFormItem :label="$t('form-manager.name')" required>
                <ElInput
                  v-model="basicForm.name"
                  :placeholder="$t('form-manager.placeholder.name')"
                  clearable
                />
              </ElFormItem>
              <ElFormItem :label="$t('form-manager.code')" required>
                <ElInput
                  v-model="basicForm.code"
                  :placeholder="$t('form-manager.placeholder.code')"
                  clearable
                />
              </ElFormItem>
              <ElFormItem :label="$t('form-manager.type')" required>
                <ElSelect
                  v-model="basicForm.form_type"
                  :placeholder="$t('form-manager.placeholder.type')"
                  class="w-full"
                >
                  <ElOption
                    :label="$t('form-manager.typeMap.normal')"
                    value="normal"
                  />
                  <ElOption
                    :label="$t('form-manager.typeMap.workflow')"
                    value="workflow"
                  />
                </ElSelect>
              </ElFormItem>
              <ElFormItem :label="$t('common.sort')">
                <ElInput
                  v-model.number="basicForm.sort"
                  type="number"
                  placeholder="0"
                />
              </ElFormItem>
              <ElFormItem :label="$t('form-manager.description')">
                <ElInput
                  v-model="basicForm.description"
                  type="textarea"
                  :rows="4"
                  :placeholder="$t('form-manager.editor.placeholder.remark')"
                />
              </ElFormItem>
            </ElForm>
          </div>
        </div>
      </div>

      <!-- 步骤2: 数据库设计 -->
      <div v-show="currentStep === 1" class="h-full overflow-hidden p-4">
        <div class="bg-card h-full w-full overflow-hidden rounded-lg shadow-sm">
          <DataSourceConfig
            v-model="tableConfigs"
            :readonly="readonly"
            :workflow-mode="workflowMode"
          />
        </div>
      </div>

      <!-- 步骤3: 表单设计 -->
      <div v-show="currentStep === 2" class="h-full overflow-hidden">
        <FormDesign :data-source="tableConfigs" :readonly="readonly" />
      </div>

      <!-- 步骤4: 列表设计 -->
      <div
        v-show="currentStep === 3"
        class="flex h-full items-start justify-center overflow-hidden"
      >
        <ListDesign
          ref="listDesignRef"
          :form-fields="formFields"
          :readonly="readonly"
        />
      </div>

      <!-- 步骤5: 发布表单（仅工作流模式） -->
      <div
        v-if="workflowMode"
        v-show="currentStep === 4"
        class="flex h-full items-center justify-center overflow-y-auto"
      >
        <div class="w-full max-w-[600px] px-4">
          <div class="border-border bg-card rounded-lg border p-6 shadow-sm">
            <h3 class="mb-6 text-center text-lg font-medium">
              {{ $t('form-manager.editor.steps.publish') }}
            </h3>
            <PublishInfoEditor
              v-model="publishData"
              :form-code="basicForm.code"
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

    <!-- 校验错误报告弹窗 -->
    <ElDialog
      v-model="validationDialogVisible"
      :title="$t('form-manager.editor.validate.title')"
      width="500px"
      :show-close="true"
      append-to-body
    >
      <div class="flex flex-col gap-3">
        <div
          class="flex items-center gap-2 rounded bg-red-50 p-3 text-red-600 dark:bg-red-900/20 dark:text-red-400"
        >
          <ElIcon class="text-xl"><Warning /></ElIcon>
          <span class="text-sm font-medium">{{
            $t('form-manager.editor.validate.repairTip')
          }}</span>
        </div>

        <div class="border-border rounded border p-1">
          <ElScrollbar max-height="400px">
            <div
              v-for="(error, index) in validationErrors"
              :key="index"
              class="border-border/50 hover:bg-muted/50 flex items-start gap-3 border-b p-3 last:border-0"
            >
              <ElIcon
                class="mt-0.5 text-lg"
                :class="
                  error.type === 'error' ? 'text-red-500' : 'text-yellow-500'
                "
              >
                <CircleClose v-if="error.type === 'error'" />
                <Warning v-else />
              </ElIcon>
              <div class="flex flex-col">
                <span class="text-foreground text-sm font-medium">{{
                  error.component
                }}</span>
                <span class="text-muted-foreground text-xs">{{
                  error.message
                }}</span>
              </div>
            </div>
          </ElScrollbar>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end">
          <ElButton @click="validationDialogVisible = false">
            {{ $t('common.confirm') }}
          </ElButton>
        </div>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.form-editor-content {
  min-height: 0;
}
</style>
