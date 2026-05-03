<script lang="ts" setup>
import type { ValidationError } from '../utils/formValidator';
import type { TableConfig } from '../modules/data-source-config.vue';

import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { ArrowLeft, Save } from '@vben/icons';
import { $t } from '@vben/locales';

import { CircleClose, Warning } from '@element-plus/icons-vue';
import {
  ElButton,
  ElDialog,
  ElIcon,
  ElMessage,
  ElScrollbar,
} from 'element-plus';

import {
  getFormDetailApi,
  updateFormApi,
} from '#/api/online-dev/form-manager';
import FormDesign from '#/components/form-design/index.vue';
import { useFormDesignStore } from '#/components/form-design/store/formDesignStore';

import { validateBeforeSave, validateFormConfig } from '../utils/formValidator';
import DataSourceConfig from '../modules/data-source-config.vue';
import ListDesign from '../modules/list-design.vue';

const route = useRoute();
const router = useRouter();
const formDesignStore = useFormDesignStore();

const formId = route.params.id as string;
const loading = ref(false);
const formName = ref('');
const formCode = ref('');
const formType = ref<'normal' | 'workflow'>('normal');

// 自动保存状态
const autoSaveStatus = ref<'saved' | 'saving' | 'unsaved'>('saved');
const autoSaveTimer = ref<null | ReturnType<typeof setTimeout>>(null);

// 当前步骤
const currentStep = ref(0);

// 数据表配置
const tableConfigs = ref<TableConfig[]>([]);

// 表单设计字段列表（扁平化）
const formFields = ref<any[]>([]);

// 列表设计组件引用
const listDesignRef = ref();

// 列表设计数据
const listDesignData = ref<Record<string, any>>({});

const steps = [
  { title: $t('form-manager.editor.steps.database'), index: 1 },
  { title: $t('form-manager.editor.steps.form'), index: 2 },
  { title: $t('form-manager.editor.steps.list'), index: 3 },
];

const canGoNext = computed(() => {
  if (currentStep.value === 0) {
    const hasMainTable = tableConfigs.value.some((t) => t.type === 'main');
    return hasMainTable;
  }
  return true;
});

const canGoPrev = computed(() => currentStep.value > 0);
const isLastStep = computed(() => currentStep.value === steps.length - 1);

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

  const fields: any[] = [];
  const seenFields = new Set<string>();

  items.forEach((item) => {
    if (layoutTypes.has(item.type)) {
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

    if (item.field && !seenFields.has(item.field)) {
      seenFields.add(item.field);
      const dbType = getFieldDbType(item.field);
      fields.push({
        label: item.label,
        field: item.field,
        component: item.type,
        options: item.options,
        props: item.props,
        dbType,
        isNumeric: isNumericDbType(dbType),
        dataSourceType: item.dataSource?.type || item.props?.dataSourceType,
        formCode:
          item.dataSource?.formCode ||
          item.formSelectorConfig?.formCode ||
          item.props?.formCode,
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
        dictCode: item.dataSource?.dictCode || item.props?.dictCode,
        dataSourceCode:
          item.dataSource?.dataSourceCode || item.props?.dataSourceCode,
        columns: item.props?.columns,
        searchFields: item.props?.searchFields,
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
        let props: any;

        switch (dbField.name) {
          case 'sys_create_datetime':
          case 'sys_update_datetime': {
            component = 'date-picker';
            props = { type: 'datetimerange' };
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
        }

        fields.push({
          label: dbField.comment || dbField.name,
          field: dbField.name,
          component,
          options: undefined,
          props,
          dbType,
          isNumeric: isNumericDbType(dbType),
          isSystemField: true,
        });
      }
    });
  }

  return fields;
}

// 校验相关
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
    // 步骤2：表单设计验证 (索引为1)
    if (currentStep.value === 1) {
      validationErrors.value = [];
      const items = formDesignStore.formConf.items;

      if (items.length === 0) {
        ElMessage.warning($t('form-manager.editor.validate.perfectDesign'));
        return;
      }

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

// 加载表单数据
async function loadFormData() {
  if (!formId) return;
  loading.value = true;
  try {
    const form = await getFormDetailApi(formId);

    formName.value = form.name;
    formCode.value = form.code;
    formType.value = form.form_type || 'normal';

    // 恢复表配置
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
    if (form.form_config?.formPadding !== undefined) {
      formDesignStore.formConf.formPadding = form.form_config.formPadding;
    }
    if (form.form_config?.formMargin !== undefined) {
      formDesignStore.formConf.formMargin = form.form_config.formMargin;
    }
    if (form.form_config?.itemSpacing !== undefined) {
      formDesignStore.formConf.itemSpacing = form.form_config.itemSpacing;
    }
    if (form.form_config?.formWidth) {
      formDesignStore.formConf.formWidth = form.form_config.formWidth;
    }
    if (form.form_config?.formMaxWidth !== undefined) {
      formDesignStore.formConf.formMaxWidth = form.form_config.formMaxWidth;
    }
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
    if (form.form_config?.disabled !== undefined) {
      formDesignStore.formConf.disabled = form.form_config.disabled;
    }

    // 恢复列表设计
    if (form.list_config) {
      listDesignData.value = form.list_config;
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

// 保存
async function handleSave(showMessage = true) {
  loading.value = true;
  autoSaveStatus.value = 'saving';
  try {
    const mainTable = tableConfigs.value.find((t) => t.type === 'main');
    if (!mainTable) {
      ElMessage.error($t('form-manager.editor.validate.database'));
      loading.value = false;
      autoSaveStatus.value = 'unsaved';
      return;
    }

    if (listDesignRef.value) {
      listDesignData.value = listDesignRef.value.getData();
    }

    // 保存前校验
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
      autoSaveStatus.value = 'unsaved';
      return;
    }

    const warnings = saveValidationErrors.filter((e) => e.type === 'warning');
    if (warnings.length > 0 && showMessage) {
      validationErrors.value = warnings;
      pendingAction.value = () => doSave(showMessage);
      validationDialogVisible.value = true;
      loading.value = false;
      return;
    }

    await doSave(showMessage);
  } catch (error: any) {
    autoSaveStatus.value = 'unsaved';
    if (showMessage) {
      ElMessage.error(error?.message || $t('common.saveFailed'));
    }
  } finally {
    loading.value = false;
  }
}

async function doSave(showMessage = true) {
  loading.value = true;
  autoSaveStatus.value = 'saving';
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

    await updateFormApi(formId, formData);
    autoSaveStatus.value = 'saved';
    if (showMessage) {
      ElMessage.success($t('form-manager.saveSuccess'));
    }
  } catch (error: any) {
    autoSaveStatus.value = 'unsaved';
    if (showMessage) {
      ElMessage.error(error?.message || $t('common.saveFailed'));
    }
  } finally {
    loading.value = false;
  }
}

// 返回上一页
function handleBack() {
  // 清空表单设计
  formDesignStore.formConf.items = [];
  formDesignStore.setActive(null);
  router.back();
}

// 监听主表变化
watch(
  () => tableConfigs.value,
  () => {
    const mainTable = tableConfigs.value.find((t) => t.type === 'main');
    if (mainTable) {
      console.log('主表字段:', mainTable.fields);
    }
  },
  { deep: true },
);

onMounted(() => {
  loadFormData();
});
</script>

<template>
  <div class="flex h-screen w-full flex-col">
    <!-- Header -->
    <header
      class="bg-background-deep z-10 mx-4 mt-4 flex h-14 shrink-0 items-center justify-between rounded-[8px] px-4"
    >
      <div class="flex items-center gap-4">
        <ElButton link :icon="ArrowLeft" @click="handleBack" />
        <div v-if="formName" class="flex flex-col">
          <span class="text-foreground text-sm font-bold">{{ formName }}</span>
          <span class="text-muted-foreground font-mono text-xs">{{
            formCode
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
        <span class="text-muted-foreground text-xs">
          <template v-if="autoSaveStatus === 'saving'">{{
            $t('form-manager.editor.autoSave.saving')
          }}</template>
          <template v-else-if="autoSaveStatus === 'saved'">{{
            $t('form-manager.editor.autoSave.saved')
          }}</template>
          <template v-else>{{
            $t('form-manager.editor.autoSave.unsaved')
          }}</template>
        </span>
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
          type="primary"
          :loading="loading"
          :icon="Save"
          @click="handleSave(true)"
        >
          {{ $t('common.save') }}
        </ElButton>
      </div>
    </header>

    <!-- 步骤内容 -->
    <div
      class="relative mx-4 mb-4 flex-1 overflow-hidden rounded-[8px]"
      v-loading="loading"
    >
      <!-- 步骤1: 数据库设计 -->
      <div v-show="currentStep === 0" class="h-full overflow-hidden py-4">
        <div class="bg-card h-full w-full overflow-hidden rounded-lg shadow-sm">
          <DataSourceConfig v-model="tableConfigs" />
        </div>
      </div>

      <!-- 步骤2: 表单设计 -->
      <div v-show="currentStep === 1" class="h-full overflow-hidden">
        <FormDesign :data-source="tableConfigs" />
      </div>

      <!-- 步骤3: 列表设计 -->
      <div
        v-show="currentStep === 2"
        class="flex h-full items-start justify-center overflow-hidden"
      >
        <ListDesign
          ref="listDesignRef"
          :form-fields="formFields"
          :form-type="formType"
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
  </div>
</template>
