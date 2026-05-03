<script lang="ts" setup>
import type { FieldPermissions } from '#/api/online-dev/form-data-api';

import { computed, reactive, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { ElButton, ElForm, ElInput, ElMessage } from 'element-plus';

import {
  createFormDataApi,
  getFieldPermissionsApi,
  getFormDataDetailApi,
  updateFormDataApi,
} from '#/api/online-dev/form-data-api';
import PreviewItem from '#/components/form-design/components/PreviewItem.vue';
import { ZqDialog } from '#/components/zq-dialog';
import { ZqDrawer } from '#/components/zq-drawer';
import { useFormData } from '#/views/online-dev/form-manager/composables/useFormData';

interface DialogConfig {
  width?: string;
  fullscreen?: boolean;
  draggable?: boolean;
  closeOnClickModal?: boolean;
  closeOnPressEscape?: boolean;
}

interface DrawerConfig {
  size?: string;
  direction?: 'btt' | 'ltr' | 'rtl' | 'ttb';
  withHeader?: boolean;
  closeOnClickModal?: boolean;
  closeOnPressEscape?: boolean;
}

interface Props {
  modelValue: boolean;
  mode: 'add' | 'edit' | 'view';
  formCode: string;
  formConfig: any;
  editId?: null | string;
  containerType?: 'dialog' | 'drawer';
  dialogConfig?: DialogConfig;
  drawerConfig?: DrawerConfig;
  // 确认按钮显示
  showConfirmButton?: boolean;
  // 保存后行为：close-关闭返回列表, editMode-切换编辑模式, continueAdd-清空继续新增
  afterSaveAction?: 'close' | 'continueAdd' | 'editMode';
  // 发起流程相关
  formType?: 'normal' | 'workflow';
  enableStartWorkflowOnAdd?: boolean;
  boundWorkflows?: WorkflowListItem[];
  // 新增时的默认数据（用于子表单自动填充外键）
  defaultFormData?: Record<string, any>;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  saved: [];
  'update:modelValue': [value: boolean];
}>();

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const loading = ref(false);
const formRef = ref();
const formData = reactive<Record<string, any>>({});
const fieldPermissions = ref<FieldPermissions>({});
// 保存后不关闭时，新增切编辑用的内部状态
const currentEditId = ref<null | string>(null);
const currentMode = ref<'add' | 'edit' | 'view'>('add');

const { initFormData, extractMainData, extractSubTables, resetFormData } =
  useFormData(formData);

// 对话框标题
const dialogTitle = computed(() => {
  const titles = {
    add: '新增数据',
    edit: '编辑数据',
    view: '查看数据',
  };
  return titles[props.mode];
});

// 是否只读模式
const isReadonly = computed(() => props.mode === 'view');

// 表单配置
const formConf = computed(() => {
  return (
    props.formConfig || {
      items: [],
      labelWidth: 100,
      labelPosition: 'right',
      size: 'default',
    }
  );
});

// 加载编辑数据
async function loadEditData() {
  if (!props.editId || props.mode === 'add') return;

  loading.value = true;
  try {
    const detail = await getFormDataDetailApi(props.formCode, props.editId);
    console.log('加载表单数据详情:', detail);

    // 1. 处理主表数据
    // 兼容处理：后端可能返回 { main: {...}, sub_tables: {...} } 或者直接返回扁平对象
    let mainData = detail.main;

    // 如果没有 main 字段，且 detail 本身看起来像数据（不包含 main 属性），则尝试直接使用 detail
    if (!mainData && !detail.main && typeof detail === 'object') {
      // 排除 sub_tables 字段，防止污染主表数据
      const { sub_tables, ...rest } = detail;
      mainData = rest;
    }

    if (mainData) {
      // 对字符串值进行 trim 处理，解决数据库中存储的值带有空格的问题
      const trimmedData: Record<string, any> = {};
      Object.keys(mainData).forEach((key) => {
        const value = mainData[key];
        trimmedData[key] = typeof value === 'string' ? value.trim() : value;
      });
      Object.assign(formData, trimmedData);
    }

    // 2. 处理子表数据
    const subTables = detail.sub_tables;
    if (subTables) {
      Object.keys(subTables).forEach((key) => {
        if (Array.isArray(subTables[key])) {
          formData[key] = subTables[key].map((row: any) => ({
            ...row,
            _id: row.id || `${Date.now()}_${Math.random()}`,
            // 回显时默认非编辑状态，点击行内编辑按钮开启
            _isEditing: false,
          }));
        }
      });
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '加载数据失败');
  } finally {
    loading.value = false;
  }
}

// 加载字段权限
async function loadFieldPermissions() {
  try {
    fieldPermissions.value = await getFieldPermissionsApi(props.formCode);
  } catch (error) {
    console.error('加载字段权限失败:', error);
    fieldPermissions.value = {};
  }
}

// 监听弹窗打开
watch(
  () => props.modelValue,
  async (visible) => {
    if (visible) {
      // 重置内部状态
      currentEditId.value = null;
      currentMode.value = props.mode;
      // 重置表单数据
      resetFormData();
      fieldPermissions.value = {};
      // 初始化表单数据
      if (formConf.value.items) {
        initFormData(formConf.value.items);
      }
      // 新增模式时填充默认数据（如子表单的外键）
      if (props.mode === 'add' && props.defaultFormData) {
        Object.assign(formData, props.defaultFormData);
      }
      // 加载字段权限
      await loadFieldPermissions();
      // 编辑/查看模式加载数据
      if (props.mode !== 'add' && props.editId) {
        await loadEditData();
      }
    }
  },
);

// 是否显示确认按钮（默认显示，除非明确设置为 false）
const shouldShowConfirmButton = computed(() => {
  return props.showConfirmButton !== false;
});

// 是否显示发起流程按钮
const showStartWorkflowButton = computed(() => {
  return (
    props.mode === 'add' &&
    props.formType === 'workflow' &&
    props.enableStartWorkflowOnAdd &&
    props.boundWorkflows &&
    props.boundWorkflows.length > 0
  );
});

// 发起流程相关状态
const workflowStarting = ref(false);
const showWorkflowTitleDialog = ref(false);
const workflowTitle = ref('');

// 提交表单
async function handleSubmit() {
  if (isReadonly.value) {
    dialogVisible.value = false;
    return;
  }

  // 表单验证
  if (formRef.value) {
    try {
      await formRef.value.validate();
    } catch {
      ElMessage.warning('请检查表单填写是否正确');
      return;
    }
  }

  loading.value = true;
  try {
    const mainData = extractMainData(formConf.value.items);
    const subTables = extractSubTables(formConf.value.items);

    const payload = {
      main: mainData,
      sub_tables: Object.keys(subTables).length > 0 ? subTables : undefined,
    };

    const action = props.afterSaveAction || 'close';
    const isAdding = props.mode === 'add' && currentMode.value !== 'edit';

    if (isAdding) {
      const result = await createFormDataApi(props.formCode, payload);
      ElMessage.success('新增成功');

      emit('saved');
      if (action === 'editMode' && result?.id) {
        currentEditId.value = result.id;
        currentMode.value = 'edit';
        return;
      } else if (action === 'continueAdd') {
        resetFormData();
        if (formConf.value.items) {
          initFormData(formConf.value.items);
        }
        if (props.defaultFormData) {
          Object.assign(formData, props.defaultFormData);
        }
        return;
      }
    } else {
      const editIdToUse = props.editId || currentEditId.value;
      await updateFormDataApi(props.formCode, editIdToUse!, payload);
      ElMessage.success('更新成功');

      emit('saved');
      if (action !== 'close') {
        return;
      }
    }

    dialogVisible.value = false;
  } catch (error: any) {
    ElMessage.error(error?.message || '保存失败');
  } finally {
    loading.value = false;
  }
}

// 点击发起流程按钮
function handleStartWorkflowClick() {
  // 生成默认标题
  const workflow = props.boundWorkflows?.[0];
  workflowTitle.value = workflow?.name || '';
  showWorkflowTitleDialog.value = true;
}

// 确认发起流程
async function confirmStartWorkflow() {
  const workflow = props.boundWorkflows?.[0];
  if (!workflow) return;

  // 验证标题
  if (!workflowTitle.value.trim()) {
    ElMessage.warning($t('form-manager.listDesign.workflowTitleRequired'));
    return;
  }

  // 表单验证
  if (formRef.value) {
    try {
      await formRef.value.validate();
    } catch {
      ElMessage.warning('请检查表单填写是否正确');
      return;
    }
  }

  workflowStarting.value = true;
  showWorkflowTitleDialog.value = false;

  try {
    const mainData = extractMainData(formConf.value.items);
    const subTables = extractSubTables(formConf.value.items);

    const payload = {
      main: mainData,
      sub_tables: Object.keys(subTables).length > 0 ? subTables : undefined,
    };

    // 发起流程
    await startWorkflowApi({
      workflow_code: workflow.code,
      title: workflowTitle.value.trim(),
      form_data: payload,
    });

    ElMessage.success($t('form-manager.listDesign.startWorkflowSuccess'));
    emit('saved');
    dialogVisible.value = false;
  } catch (error: any) {
    ElMessage.error(
      error?.message || $t('form-manager.listDesign.startWorkflowFailed'),
    );
  } finally {
    workflowStarting.value = false;
  }
}

// 取消发起流程
function cancelStartWorkflow() {
  showWorkflowTitleDialog.value = false;
  workflowTitle.value = '';
}
</script>

<template>
  <!-- Dialog 容器 -->
  <ZqDialog
    v-if="props.containerType === 'dialog'"
    v-model="dialogVisible"
    :title="dialogTitle"
    :width="props.dialogConfig?.width || '800px'"
    :default-fullscreen="props.dialogConfig?.fullscreen ?? false"
    :draggable="props.dialogConfig?.draggable ?? true"
    :close-on-click-modal="props.dialogConfig?.closeOnClickModal ?? false"
    :close-on-press-escape="props.dialogConfig?.closeOnPressEscape ?? true"
    :loading="loading"
    :confirm-loading="loading"
    max-height="60vh"
    align-center
  >
    <div
      :style="{
        width: formConf.formWidth || '100%',
        maxWidth: formConf.formMaxWidth || 'none',
        padding: `${formConf.formPaddingTop ?? formConf.formPadding ?? 0}px ${formConf.formPaddingRight ?? formConf.formPadding ?? 0}px ${formConf.formPaddingBottom ?? formConf.formPadding ?? 0}px ${formConf.formPaddingLeft ?? formConf.formPadding ?? 0}px`,
        margin: `${formConf.formMarginTop ?? formConf.formMargin ?? 0}px ${formConf.formMarginRight ?? formConf.formMargin ?? 0}px ${formConf.formMarginBottom ?? formConf.formMargin ?? 0}px ${formConf.formMarginLeft ?? formConf.formMargin ?? 0}px`,
        backgroundColor: formConf.formBackground || 'transparent',
        border: formConf.formBorder
          ? '1px solid var(--el-border-color)'
          : 'none',
        borderRadius: formConf.formBorder
          ? `${formConf.formBorderRadius || 4}px`
          : '0',
        boxShadow: formConf.formShadow
          ? '0 2px 12px 0 rgba(0, 0, 0, 0.1)'
          : 'none',
      }"
    >
      <ElForm
        ref="formRef"
        :model="formData"
        :label-width="`${formConf.labelWidth || 100}px`"
        :label-position="formConf.labelPosition || 'right'"
        :size="formConf.size || 'default'"
        :disabled="isReadonly"
        class="pr-4"
        :style="{
          '--el-form-item-margin-bottom': `${formConf.itemSpacing || 18}px`,
        }"
      >
        <PreviewItem
          v-for="item in formConf.items"
          :key="item.id"
          :item="item"
          :model-value="formData"
          :is-edit="mode !== 'add'"
          :field-permissions="fieldPermissions"
          :form-code="formCode"
          :edit-id="editId ?? undefined"
        />
      </ElForm>
    </div>
    <template #footer>
      <div class="flex justify-end gap-2">
        <ElButton @click="dialogVisible = false">
          {{ isReadonly ? $t('common.close') : $t('common.cancel') }}
        </ElButton>
        <ElButton
          v-if="showStartWorkflowButton"
          type="success"
          :loading="workflowStarting"
          @click="handleStartWorkflowClick"
        >
          {{ $t('form-manager.listDesign.startWorkflow') }}
        </ElButton>
        <ElButton
          v-if="!isReadonly && shouldShowConfirmButton"
          type="primary"
          :loading="loading"
          @click="handleSubmit"
        >
          {{ $t('common.confirm') }}
        </ElButton>
      </div>
    </template>
  </ZqDialog>

  <!-- Drawer 容器 -->
  <ZqDrawer
    v-else
    v-model="dialogVisible"
    :title="dialogTitle"
    :size="props.drawerConfig?.size || '800px'"
    :direction="props.drawerConfig?.direction || 'rtl'"
    :with-header="props.drawerConfig?.withHeader ?? true"
    :close-on-click-modal="props.drawerConfig?.closeOnClickModal ?? false"
    :close-on-press-escape="props.drawerConfig?.closeOnPressEscape ?? true"
    :loading="loading"
    :confirm-loading="loading"
  >
    <div
      :style="{
        width: formConf.formWidth || '100%',
        maxWidth: formConf.formMaxWidth || 'none',
        padding: `${formConf.formPaddingTop ?? formConf.formPadding ?? 0}px ${formConf.formPaddingRight ?? formConf.formPadding ?? 0}px ${formConf.formPaddingBottom ?? formConf.formPadding ?? 0}px ${formConf.formPaddingLeft ?? formConf.formPadding ?? 0}px`,
        margin: `${formConf.formMarginTop ?? formConf.formMargin ?? 0}px ${formConf.formMarginRight ?? formConf.formMargin ?? 0}px ${formConf.formMarginBottom ?? formConf.formMargin ?? 0}px ${formConf.formMarginLeft ?? formConf.formMargin ?? 0}px`,
        backgroundColor: formConf.formBackground || 'transparent',
        border: formConf.formBorder
          ? '1px solid var(--el-border-color)'
          : 'none',
        borderRadius: formConf.formBorder
          ? `${formConf.formBorderRadius || 4}px`
          : '0',
        boxShadow: formConf.formShadow
          ? '0 2px 12px 0 rgba(0, 0, 0, 0.1)'
          : 'none',
      }"
    >
      <ElForm
        ref="formRef"
        :model="formData"
        :label-width="`${formConf.labelWidth || 100}px`"
        :label-position="formConf.labelPosition || 'right'"
        :size="formConf.size || 'default'"
        :disabled="isReadonly"
        class="pr-4"
        :style="{
          '--el-form-item-margin-bottom': `${formConf.itemSpacing || 18}px`,
        }"
      >
        <PreviewItem
          v-for="item in formConf.items"
          :key="item.id"
          :item="item"
          :model-value="formData"
          :is-edit="mode !== 'add'"
          :field-permissions="fieldPermissions"
          :form-code="formCode"
          :edit-id="editId ?? undefined"
        />
      </ElForm>
    </div>
    <template #footer>
      <div class="flex justify-end gap-2">
        <ElButton @click="dialogVisible = false">
          {{ isReadonly ? $t('common.close') : $t('common.cancel') }}
        </ElButton>
        <ElButton
          v-if="showStartWorkflowButton"
          type="success"
          :loading="workflowStarting"
          @click="handleStartWorkflowClick"
        >
          {{ $t('form-manager.listDesign.startWorkflow') }}
        </ElButton>
        <ElButton
          v-if="!isReadonly && shouldShowConfirmButton"
          type="primary"
          :loading="loading"
          @click="handleSubmit"
        >
          {{ $t('common.confirm') }}
        </ElButton>
      </div>
    </template>
  </ZqDrawer>

  <!-- 发起流程标题输入对话框 -->
  <ZqDialog
    v-model="showWorkflowTitleDialog"
    :title="$t('form-manager.listDesign.startWorkflow')"
    width="500px"
    :close-on-click-modal="false"
    @close="cancelStartWorkflow"
  >
    <div class="py-4">
      <div class="mb-2 text-sm text-[var(--el-text-color-regular)]">
        {{ $t('form-manager.listDesign.workflowTitleLabel') }}
      </div>
      <ElInput
        v-model="workflowTitle"
        :placeholder="$t('form-manager.listDesign.workflowTitlePlaceholder')"
        maxlength="200"
        show-word-limit
        clearable
        @keyup.enter="confirmStartWorkflow"
      />
    </div>
    <template #footer>
      <ElButton @click="cancelStartWorkflow">
        {{ $t('common.cancel') }}
      </ElButton>
      <ElButton
        type="primary"
        :loading="workflowStarting"
        @click="confirmStartWorkflow"
      >
        {{ $t('common.confirm') }}
      </ElButton>
    </template>
  </ZqDialog>
</template>
