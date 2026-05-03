<script lang="ts" setup>
import type { ValidationError } from '../utils/formValidator';
import type { TableConfig } from './data-source-config.vue';

import { computed, ref, watch } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { $t } from '@vben/locales';

import { CircleClose, Warning } from '@element-plus/icons-vue';
import {
  ElButton,
  ElDialog,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElMessage,
  ElOption,
  ElScrollbar,
  ElSelect,
  ElSwitch,
} from 'element-plus';

import {
  createFormApi,
  getFormDetailApi,
  updateFormApi,
} from '#/api/online-dev/form-manager';
import GradientColorPicker from '#/components/dashboard-design/components/GradientColorPicker.vue';
// 导入表单设计器组件
import FormDesign from '#/components/form-design/index.vue';
import { useFormDesignStore } from '#/components/form-design/store/formDesignStore';
import { ZqIconPicker } from '#/components/zq-form/zq-icon-picker';
import { useAppContextStore } from '#/store/app-context';

import { validateBeforeSave, validateFormConfig } from '../utils/formValidator';
import DataSourceConfig from './data-source-config.vue';
import ListDesign from './list-design.vue';

interface Props {
  modelValue: boolean;
  formId?: null | string; // 编辑时传入表单ID
}

const props = defineProps<Props>();

const emit = defineEmits<{
  save: [];
  'update:modelValue': [value: boolean];
}>();

const formDesignStore = useFormDesignStore();
const appContextStore = useAppContextStore();
const loading = ref(false);
const isEditMode = computed(() => !!props.formId);

// 当前步骤
const currentStep = ref(0);

// 预设渐变色选项
const presetGradients = [
  {
    label: '主题蓝渐变',
    value: 'linear-gradient(135deg, #007aff 0%, #00d4ff 100%)',
  },
  {
    label: '绿色渐变',
    value: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
  },
  {
    label: '粉紫渐变',
    value: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  },
  {
    label: '天蓝渐变',
    value: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  },
  {
    label: '橙黄渐变',
    value: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  },
  {
    label: '深蓝渐变',
    value: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
  },
  {
    label: '金红渐变',
    value: 'linear-gradient(135deg, #f5af19 0%, #f12711 100%)',
  },
  {
    label: '紫粉渐变',
    value: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  },
];

// 基础信息表单
const basicForm = ref({
  name: '',
  code: '',
  form_type: 'normal' as 'normal' | 'workflow',
  sort: 0,
  description: '',
  show_in_mobile: false,
  icon: '',
  icon_bg_color: '',
});

// 数据表配置
const tableConfigs = ref<TableConfig[]>([]);

// 表单设计字段列表（扁平化）
const formFields = ref<any[]>([]);

// 列表设计组件引用
const listDesignRef = ref();

// 列表设计数据
const listDesignData = ref<Record<string, any>>({});

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const steps = [
  { title: $t('form-manager.editor.steps.basic'), index: 1 },
  { title: $t('form-manager.editor.steps.database'), index: 2 },
  { title: $t('form-manager.editor.steps.form'), index: 3 },
  { title: $t('form-manager.editor.steps.list'), index: 4 },
];

const canGoNext = computed(() => {
  if (currentStep.value === 0) {
    // 基础信息验证：名称、编码必填
    return basicForm.value.name && basicForm.value.code;
  }
  if (currentStep.value === 1) {
    // 数据库配置验证：必须配置主表
    const hasMainTable = tableConfigs.value.some((t) => t.type === 'main');
    return hasMainTable;
  }
  return true;
});

// 监听主表变化，自动同步字段到表单设计器
watch(
  () => tableConfigs.value,
  (newConfigs) => {
    const mainTable = newConfigs.find((t) => t.type === 'main');
    if (mainTable) {
      // 可以在这里做一些字段同步逻辑
      console.log('主表字段:', mainTable.fields);
    }
  },
  { deep: true },
);

// 提取子表配置给列表设计器使用
const subTablesForListDesign = computed(() => {
  return tableConfigs.value
    .filter((t) => t.type === 'sub')
    .map((t) => ({
      tableName: t.tableName,
      alias: t.alias,
      foreignKey: t.foreignKey || '',
      relatedField: t.relatedField || 'id',
    }));
});

// 监听弹窗打开，编辑模式下加载数据
watch(
  () => props.modelValue,
  async (visible) => {
    if (visible && props.formId) {
      await loadFormData(props.formId);
    }
  },
);

// 加载表单数据
async function loadFormData(formId: string) {
  loading.value = true;
  try {
    const form = await getFormDetailApi(formId);

    // 恢复基础信息
    basicForm.value = {
      name: form.name,
      code: form.code,
      form_type: form.form_type || 'normal',
      description: form.description,
      sort: form.sort,
      show_in_mobile: form.show_in_mobile || false,
      icon: form.icon || '',
      icon_bg_color: form.icon_bg_color || '',
    };

    // 恢复表配置（从 form_config 中）
    if (form.form_config?.tableConfigs) {
      tableConfigs.value = form.form_config.tableConfigs;
    }

    // 恢复表单设计
    if (form.form_config?.items) {
      formDesignStore.formConf.items = form.form_config.items;
    }

    // 恢复表单属性配置
    if (form.form_config?.labelWidth !== undefined) {
      formDesignStore.formConf.labelWidth = form.form_config.labelWidth;
    }
    if (form.form_config?.labelPosition) {
      formDesignStore.formConf.labelPosition = form.form_config.labelPosition;
    }
    if (form.form_config?.size) {
      formDesignStore.formConf.size = form.form_config.size;
    }
    // 恢复布局间距
    if (form.form_config?.formPadding !== undefined) {
      formDesignStore.formConf.formPadding = form.form_config.formPadding;
    }
    if (form.form_config?.formMargin !== undefined) {
      formDesignStore.formConf.formMargin = form.form_config.formMargin;
    }
    if (form.form_config?.itemSpacing !== undefined) {
      formDesignStore.formConf.itemSpacing = form.form_config.itemSpacing;
    }
    // 恢复容器尺寸
    if (form.form_config?.formWidth) {
      formDesignStore.formConf.formWidth = form.form_config.formWidth;
    }
    if (form.form_config?.formMaxWidth !== undefined) {
      formDesignStore.formConf.formMaxWidth = form.form_config.formMaxWidth;
    }
    // 恢复外观样式
    if (form.form_config?.formBackground !== undefined) {
      formDesignStore.formConf.formBackground = form.form_config.formBackground;
    }
    if (form.form_config?.formBorder !== undefined) {
      formDesignStore.formConf.formBorder = form.form_config.formBorder;
    }
    if (form.form_config?.formBorderRadius !== undefined) {
      formDesignStore.formConf.formBorderRadius =
        form.form_config.formBorderRadius;
    }
    if (form.form_config?.formShadow !== undefined) {
      formDesignStore.formConf.formShadow = form.form_config.formShadow;
    }
    // 恢复全局禁用
    if (form.form_config?.disabled !== undefined) {
      formDesignStore.formConf.disabled = form.form_config.disabled;
    }

    // 恢复列表设计
    if (form.list_config) {
      // 直接传递完整的 list_config，让 list-design 组件自己处理
      listDesignData.value = form.list_config;
      // 尝试设置到组件
      setTimeout(() => {
        listDesignRef.value?.setData(form.list_config);
      }, 0);
    }
  } catch (error: any) {
    ElMessage.error(error?.message || $t('form-manager.editor.loadFailed'));
  } finally {
    loading.value = false;
  }
}

const canGoPrev = computed(() => currentStep.value > 0);

const isLastStep = computed(() => currentStep.value === steps.length - 1);

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
  // 从主表中查找
  const mainTable = tableConfigs.value.find((t) => t.type === 'main');
  if (mainTable) {
    const field = mainTable.fields.find((f: any) => f.name === fieldName);
    if (field) return field.type || '';
  }
  return '';
}

// 递归提取表单字段（排除子表单及其内部字段，子表数据通常通过详情页展示）
// 保存完整的组件配置信息，供列表设计中的查询字段使用
function extractFields(items: any[]): any[] {
  // 定义布局/展示类组件，这些组件不应该出现在查询和列表字段中
  const layoutTypes = new Set([
    'alert',
    'collapse',
    'divider',
    'grid',
    'html',
    'spacer',
    'sub-table',
    'tabs',
    'text',
    'timeline',
    'title',
  ]);

  const fields: any[] = [];
  const seenFields = new Set<string>(); // 用于去重

  items.forEach((item) => {
    // 跳过布局/展示类组件，但需要递归处理其子组件
    if (layoutTypes.has(item.type)) {
      // grid 组件：columns[].children
      if (item.columns && Array.isArray(item.columns)) {
        item.columns.forEach((col: any) => {
          if (col.children && Array.isArray(col.children)) {
            extractFields(col.children).forEach((f) => {
              if (!seenFields.has(f.field)) {
                seenFields.add(f.field);
                fields.push(f);
              }
            });
          }
        });
      }
      // tabs/collapse 组件：items[].children
      if (item.items && Array.isArray(item.items)) {
        item.items.forEach((subItem: any) => {
          if (subItem.children && Array.isArray(subItem.children)) {
            extractFields(subItem.children).forEach((f) => {
              if (!seenFields.has(f.field)) {
                seenFields.add(f.field);
                fields.push(f);
              }
            });
          }
        });
      }
      // 其他布局组件直接有 children（如 tabs 的旧结构）
      if (item.children && Array.isArray(item.children)) {
        extractFields(item.children).forEach((f) => {
          if (!seenFields.has(f.field)) {
            seenFields.add(f.field);
            fields.push(f);
          }
        });
      }
      return;
    }

    // 只添加有 field 属性的真实表单字段（去重）
    if (item.field && !seenFields.has(item.field)) {
      seenFields.add(item.field);
      const dbType = getFieldDbType(item.field);
      fields.push({
        label: item.label,
        field: item.field,
        component: item.type,
        // 保存选项数据（用于 select、radio、checkbox、cascader、tree-select 等组件）
        options: item.options,
        // 保存组件属性（用于日期格式、multiple 等配置）
        props: item.props,
        // 数据库字段类型（用于列表设计中判断是否显示统计开关）
        dbType,
        isNumeric: isNumericDbType(dbType),
        // 表单数据选择器配置（用于列表设计中显示关联字段选择）
        // 注意：dataSourceType 存储在 item.dataSource.type 中，formCode 存储在 item.dataSource.formCode 中
        // form-selector 组件的 formCode 存储在 item.formSelectorConfig.formCode 中
        dataSourceType: item.dataSource?.type || item.props?.dataSourceType,
        formCode:
          item.dataSource?.formCode ||
          item.formSelectorConfig?.formCode ||
          item.props?.formCode,
        // form-selector / table-selector 的 valueField 和 labelField
        valueField:
          item.formSelectorConfig?.valueField ||
          item.props?.valueField ||
          item.dataSource?.formValueField ||
          'id',
        labelField:
          item.formSelectorConfig?.labelField ||
          item.props?.labelField ||
          item.dataSource?.formLabelField ||
          'name',
        // table-selector 额外配置
        dictCode: item.dataSource?.dictCode || item.props?.dictCode,
        dataSourceCode:
          item.dataSource?.dataSourceCode || item.props?.dataSourceCode,
        columns: item.props?.columns,
        searchFields: item.props?.searchFields,
      });
    }
  });

  // 添加数据源中的系统字段（这些字段由后端自动处理，不在表单设计中添加，但可以在列表中显示）
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
        // 根据字段名称确定默认组件类型
        let component = 'input';
        let props: any;

        switch (dbField.name) {
          case 'sys_create_datetime':
          case 'sys_update_datetime': {
            // 创建时间、更新时间使用日期范围选择器
            component = 'date-picker';
            props = { type: 'datetimerange' };

            break;
          }
          case 'sys_creator_id':
          case 'sys_modifier_id': {
            // 创建人、修改人使用用户选择器
            component = 'user-select';

            break;
          }
          case 'sys_dept_id': {
            // 部门使用部门选择器
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
          props,
          dbType,
          isNumeric: isNumericDbType(dbType),
          isSystemField: true, // 标记为系统字段
        });
      }
    });
  }

  return fields;
}

const validationErrors = ref<ValidationError[]>([]);
const validationDialogVisible = ref(false);
const pendingAction = ref<(() => void) | null>(null);

const hasOnlyWarnings = computed(() => {
  return (
    validationErrors.value.length > 0 &&
    validationErrors.value.every((e) => e.type === 'warning')
  );
});

function handleContinueAnyway() {
  validationDialogVisible.value = false;
  if (pendingAction.value) {
    pendingAction.value();
    pendingAction.value = null;
  }
}

function handleNext() {
  if (currentStep.value < steps.length - 1) {
    // 步骤3：表单设计验证 (索引为2)
    if (currentStep.value === 2) {
      validationErrors.value = [];
      const items = formDesignStore.formConf.items;

      // 1. 非空校验
      if (items.length === 0) {
        ElMessage.warning($t('form-manager.editor.validate.perfectDesign'));
        return;
      }

      // 2. 调用通用校验逻辑
      validationErrors.value = validateFormConfig(items, tableConfigs.value);

      if (validationErrors.value.length > 0) {
        const hasErrors = validationErrors.value.some(
          (e) => e.type === 'error',
        );
        if (hasErrors) {
          pendingAction.value = null;
          validationDialogVisible.value = true;
          return;
        }
        pendingAction.value = () => {
          formFields.value = extractFields(items);
          currentStep.value++;
        };
        validationDialogVisible.value = true;
        return;
      }

      // 提取字段供下一步使用
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

async function handleSave() {
  loading.value = true;
  try {
    // 构建主表配置
    const mainTable = tableConfigs.value.find((t) => t.type === 'main');
    if (!mainTable) {
      ElMessage.error($t('form-manager.editor.validate.database'));
      loading.value = false;
      return;
    }

    // 获取列表设计数据
    if (listDesignRef.value) {
      listDesignData.value = listDesignRef.value.getData();
    }

    // 保存前整体校验
    const currentFormFields = extractFields(formDesignStore.formConf.items);

    const saveValidationErrors = validateBeforeSave(
      { items: formDesignStore.formConf.items },
      tableConfigs.value,
      listDesignData.value,
      currentFormFields,
    );

    const criticalErrors = saveValidationErrors.filter(
      (e) => e.type === 'error',
    );

    if (criticalErrors.length > 0) {
      validationErrors.value = saveValidationErrors;
      pendingAction.value = null;
      validationDialogVisible.value = true;
      loading.value = false;
      return;
    }

    const warnings = saveValidationErrors.filter((e) => e.type === 'warning');
    if (warnings.length > 0) {
      validationErrors.value = warnings;
      pendingAction.value = () => doSave();
      validationDialogVisible.value = true;
      loading.value = false;
      return;
    }

    await doSave();
  } catch (error: any) {
    ElMessage.error(error?.message || $t('common.saveFailed'));
  } finally {
    loading.value = false;
  }
}

async function doSave() {
  loading.value = true;
  try {
    const mainTable = tableConfigs.value.find((t) => t.type === 'main');

    const subTables = tableConfigs.value
      .filter((t) => t.type === 'sub')
      .map((t) => ({
        table_name: t.tableName,
        table_schema: t.meta?.schema || '',
        table_database: t.meta?.database || '',
        alias: t.alias,
        foreign_key: t.foreignKey || '',
        related_field: t.relatedField || 'id',
        relation_type: t.relationType || 'one-to-many',
        sort: 0,
      }));

    const formData = {
      application_id: appContextStore.currentApp?.id,
      name: basicForm.value.name,
      code: basicForm.value.code,
      form_type: basicForm.value.form_type,
      description: basicForm.value.description,
      sort: basicForm.value.sort,
      show_in_mobile: basicForm.value.show_in_mobile,
      icon: basicForm.value.icon,
      icon_bg_color: basicForm.value.icon_bg_color,
      db_config: mainTable?.meta?.dbName || 'default',
      main_table: mainTable?.tableName,
      main_table_schema: mainTable?.meta?.schema || '',
      main_table_database: mainTable?.meta?.database || '',
      form_config: {
        items: formDesignStore.formConf.items,
        labelWidth: formDesignStore.formConf.labelWidth,
        labelPosition: formDesignStore.formConf.labelPosition,
        size: formDesignStore.formConf.size,
        formPadding: formDesignStore.formConf.formPadding,
        formMargin: formDesignStore.formConf.formMargin,
        itemSpacing: formDesignStore.formConf.itemSpacing,
        formWidth: formDesignStore.formConf.formWidth,
        formMaxWidth: formDesignStore.formConf.formMaxWidth,
        formBackground: formDesignStore.formConf.formBackground,
        formBorder: formDesignStore.formConf.formBorder,
        formBorderRadius: formDesignStore.formConf.formBorderRadius,
        formShadow: formDesignStore.formConf.formShadow,
        disabled: formDesignStore.formConf.disabled,
        tableConfigs: tableConfigs.value,
      },
      list_config: listDesignData.value,
      sub_tables: subTables,
    };

    await (isEditMode.value && props.formId
      ? updateFormApi(props.formId, formData)
      : createFormApi(formData));

    emit('save');
    handleClose();
  } catch (error: any) {
    ElMessage.error(error?.message || $t('common.saveFailed'));
  } finally {
    loading.value = false;
  }
}

function handleClose() {
  dialogVisible.value = false;
  // 重置状态
  currentStep.value = 0;
  basicForm.value = {
    name: '',
    code: '',
    form_type: 'normal',
    sort: 0,
    description: '',
    show_in_mobile: false,
    icon: '',
    icon_bg_color: '',
  };
  tableConfigs.value = [];
  // 清空表单设计
  formDesignStore.formConf.items = [];
  formDesignStore.setActive(null);

  // 重置列表设计
  listDesignData.value = {};
  listDesignRef.value?.setData({});
}
</script>

<template>
  <ElDialog
    v-model="dialogVisible"
    :show-close="false"
    fullscreen
    destroy-on-close
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    body-class="h-[calc(100vh-96px)]"
    header-class="!pb-0"
  >
    <template #header>
      <div
        class="bg-background-deep flex h-14 w-full items-center justify-between rounded-[8px] px-6 shadow-sm"
      >
        <!-- 左侧：Logo和标题 -->
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <div
              class="bg-primary flex h-8 w-8 items-center justify-center rounded"
            >
              <span class="text-sm font-bold text-white">F</span>
            </div>
            <span class="text-foreground/70 text-base font-medium">{{
              $t('form-manager.editor.title')
            }}</span>
          </div>
        </div>

        <!-- 中间：步骤条 -->
        <div class="absolute left-1/2 flex -translate-x-1/2 items-center">
          <template v-for="(step, index) in steps" :key="index">
            <div
              class="flex cursor-pointer items-center px-4 py-1"
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
              class="bg-border h-[1px] w-8"
              :class="{ 'bg-primary/50': index < currentStep }"
            ></div>
          </template>
        </div>

        <!-- 右侧：操作按钮 -->
        <div class="flex items-center gap-3">
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
          <ElButton
            v-if="isLastStep"
            type="primary"
            :loading="loading"
            @click="handleSave"
          >
            {{ $t('common.save') }}
          </ElButton>
          <ElButton @click="handleClose"> {{ $t('common.close') }} </ElButton>
        </div>
      </div>
    </template>

    <!-- 步骤内容 -->
    <div class="h-full overflow-hidden">
      <!-- 步骤1: 基础信息 -->
      <div
        v-show="currentStep === 0"
        class="flex h-full items-center justify-center"
      >
        <div class="align-self-center w-[600px]">
          <div class="border-border bg-card rounded-lg border p-8 shadow-sm">
            <h3 class="mb-6 text-center text-lg font-medium">
              {{ $t('form-manager.editor.steps.basic') }}
            </h3>
            <ElScrollbar max-height="calc(100vh - 300px)">
              <ElForm
                :model="basicForm"
                label-position="top"
                class="form-content px-4"
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
                    :disabled="isEditMode"
                  />
                  <div
                    v-if="
                      basicForm.code &&
                      !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(basicForm.code)
                    "
                    class="el-form-item__error"
                  >
                    {{ $t('form-manager.codeFormatError') }}
                  </div>
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
                <ElFormItem :label="$t('form-manager.showInMobile')">
                  <ElSwitch v-model="basicForm.show_in_mobile" />
                  <span class="text-muted-foreground ml-2 text-sm">{{
                    $t('form-manager.showInMobileTip')
                  }}</span>
                </ElFormItem>
                <template v-if="basicForm.show_in_mobile">
                  <ElFormItem :label="$t('form-manager.icon')">
                    <ZqIconPicker
                      v-model="basicForm.icon"
                      :placeholder="$t('form-manager.iconPlaceholder')"
                      :icons="WORKFLOW_ICONS"
                      :auto-fetch-api="false"
                    />
                  </ElFormItem>
                  <ElFormItem :label="$t('form-manager.iconBgColor')">
                    <ElScrollbar max-height="280px" class="w-full">
                      <div class="flex w-full flex-col gap-3 pr-2">
                        <!-- 预设渐变色快捷选择 -->
                        <div class="flex flex-wrap gap-2">
                          <div
                            v-for="gradient in presetGradients"
                            :key="gradient.value"
                            class="h-8 w-8 cursor-pointer rounded-md border-2 transition-all hover:scale-110"
                            :class="
                              basicForm.icon_bg_color === gradient.value
                                ? 'border-primary ring-primary/30 ring-2'
                                : 'border-transparent'
                            "
                            :style="{ background: gradient.value }"
                            :title="gradient.label"
                            @click="basicForm.icon_bg_color = gradient.value"
                          ></div>
                        </div>
                        <!-- 渐变色编辑器 -->
                        <GradientColorPicker
                          v-model="basicForm.icon_bg_color"
                        />
                        <!-- 预览 -->
                        <div
                          v-if="basicForm.icon_bg_color"
                          class="flex items-center gap-2"
                        >
                          <span class="text-muted-foreground text-xs"
                            >{{ $t('form-manager.iconPreview') }}:</span
                          >
                          <div
                            class="flex h-10 w-10 items-center justify-center rounded-lg"
                            :style="{ background: basicForm.icon_bg_color }"
                          >
                            <IconifyIcon
                              v-if="basicForm.icon"
                              :icon="basicForm.icon"
                              class="h-6 w-6 text-white"
                            />
                            <span v-else class="text-xs text-white">A</span>
                          </div>
                        </div>
                      </div>
                    </ElScrollbar>
                  </ElFormItem>
                </template>
              </ElForm>
            </ElScrollbar>
          </div>
        </div>
      </div>

      <!-- 步骤2: 数据库设计 -->
      <div v-show="currentStep === 1" class="h-full overflow-hidden py-4">
        <div class="bg-card h-full w-full overflow-hidden rounded-lg shadow-sm">
          <DataSourceConfig v-model="tableConfigs" />
        </div>
      </div>

      <!-- 步骤3: 表单设计 -->
      <div v-show="currentStep === 2" class="h-full overflow-hidden">
        <FormDesign :data-source="tableConfigs" />
      </div>

      <!-- 步骤4: 列表设计 -->
      <div
        v-show="currentStep === 3"
        class="flex h-full items-start justify-center overflow-hidden"
      >
        <ListDesign
          ref="listDesignRef"
          :form-fields="formFields"
          :form-type="basicForm.form_type"
          :sub-tables="subTablesForListDesign"
        />
      </div>
    </div>

    <!-- 校验错误报告弹窗 -->
    <ElDialog
      v-model="validationDialogVisible"
      :title="
        hasOnlyWarnings
          ? $t('form-manager.editor.validate.warningTitle')
          : $t('form-manager.editor.validate.title')
      "
      width="500px"
      :show-close="true"
      class="validation-dialog"
      append-to-body
    >
      <div class="flex flex-col gap-3">
        <div
          v-if="hasOnlyWarnings"
          class="flex items-center gap-2 rounded bg-yellow-50 p-3 text-yellow-600 dark:bg-yellow-900/20 dark:text-yellow-400"
        >
          <ElIcon class="text-xl"><Warning /></ElIcon>
          <span class="text-sm font-medium">{{
            $t('form-manager.editor.validate.warningTip')
          }}</span>
        </div>
        <div
          v-else
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
        <div class="flex justify-end gap-2">
          <ElButton @click="validationDialogVisible = false">
            {{ $t('common.confirm') }}
          </ElButton>
          <ElButton
            v-if="hasOnlyWarnings && pendingAction"
            type="primary"
            @click="handleContinueAnyway"
          >
            {{ $t('form-manager.editor.validate.continueAnyway') }}
          </ElButton>
        </div>
      </template>
    </ElDialog>
  </ElDialog>
</template>

<style scoped>
/* 基础信息表单样式 - 组件内部样式使用 :deep */

/* .form-content :deep(.el-form-item) {
  margin-bottom: 20px;
}

.form-content :deep(.el-input__wrapper),
.form-content :deep(.el-textarea__inner) {
  box-shadow: none;
  border: 1px solid var(--el-border-color);
}

.form-content :deep(.el-input__wrapper:hover),
.form-content :deep(.el-textarea__inner:hover) {
  border-color: var(--el-border-color-hover);
}

.form-content :deep(.el-input__wrapper.is-focus),
.form-content :deep(.el-textarea__inner:focus) {
  border-color: var(--el-color-primary);
} */
</style>
