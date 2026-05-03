<script lang="ts" setup>
import type { FieldPermissions } from '#/api/online-dev/form-data-api';
import type { FormMeta } from '#/api/online-dev/form-manager';

import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import { ArrowLeft, Save } from '@vben/icons';

import { ElButton, ElForm, ElMessage } from 'element-plus';

import {
  createFormDataApi,
  getFieldPermissionsApi,
  getFormDataDetailApi,
  updateFormDataApi,
} from '#/api/online-dev/form-data-api';
import { getFormByCodeApi } from '#/api/online-dev/form-manager';
import PreviewItem from '#/components/form-design/components/PreviewItem.vue';
import { useFormData } from '#/views/online-dev/form-manager/composables/useFormData';

defineOptions({ name: 'FormLayout' });

const route = useRoute();
const router = useRouter();

// 从路由获取参数
const formCode = computed(() => route.params.code as string);
const mode = computed(() => {
  const path = route.path;
  if (path.includes('/add')) return 'add';
  if (path.includes('/edit')) return 'edit';
  if (path.includes('/view')) return 'view';
  return 'add';
});
const editId = computed(() => route.params.id as string | undefined);

// 表单元数据
const formMeta = ref<FormMeta | null>(null);
const loading = ref(false);
const saving = ref(false);
const formRef = ref();
const formData = reactive<Record<string, any>>({});

// 字段权限
const fieldPermissions = ref<FieldPermissions>({});

const { initFormData, extractMainData, extractSubTables, resetFormData } =
  useFormData(formData);

// 页面标题
const pageTitle = computed(() => {
  const formName = formMeta.value?.name || '';
  const titles = {
    add: `新增${formName}`,
    edit: `编辑${formName}`,
    view: `查看${formName}`,
  };
  return titles[mode.value];
});

// 是否只读模式
const isReadonly = computed(() => mode.value === 'view');

// 是否显示返回按钮
const showBackButton = computed(() => {
  const pageConfig = formMeta.value?.list_config?.page;
  return pageConfig?.showBackButton ?? true;
});

// 表单配置
const formConf = computed(() => {
  return (
    formMeta.value?.form_config || {
      items: [],
      labelWidth: 100,
      labelPosition: 'right',
      size: 'default',
    }
  );
});

// 加载字段权限
async function loadFieldPermissions() {
  if (!formCode.value) return;
  try {
    fieldPermissions.value = await getFieldPermissionsApi(formCode.value);
  } catch (error) {
    console.error('加载字段权限失败:', error);
    fieldPermissions.value = {};
  }
}

// 加载表单元数据
async function loadFormMeta() {
  if (!formCode.value) return;

  loading.value = true;
  try {
    await loadFieldPermissions();

    formMeta.value = await getFormByCodeApi(formCode.value);

    if (formMeta.value.form_config?.items) {
      initFormData(formMeta.value.form_config.items);
    }

    if ((mode.value === 'edit' || mode.value === 'view') && editId.value) {
      await loadEditData();
    }
  } catch (error) {
    console.error('Failed to load form meta:', error);
    ElMessage.error('加载表单配置失败');
  } finally {
    loading.value = false;
  }
}

// 加载编辑数据
async function loadEditData() {
  if (!editId.value) return;

  try {
    const detail = await getFormDataDetailApi(formCode.value, editId.value);
    console.log('加载表单数据详情:', detail);

    let mainData = detail.main;

    if (!mainData && !detail.main && typeof detail === 'object') {
      const { sub_tables, ...rest } = detail;
      mainData = rest;
    }

    if (mainData) {
      const trimmedData: Record<string, any> = {};
      Object.keys(mainData).forEach((key) => {
        const value = mainData[key];
        trimmedData[key] = typeof value === 'string' ? value.trim() : value;
      });
      Object.assign(formData, trimmedData);
    }

    const subTables = detail.sub_tables;
    if (subTables) {
      Object.keys(subTables).forEach((key) => {
        if (Array.isArray(subTables[key])) {
          formData[key] = subTables[key].map((row: any) => ({
            ...row,
            _id: row.id || `${Date.now()}_${Math.random()}`,
            _isEditing: false,
          }));
        }
      });
    }
  } catch (error: any) {
    console.error('Failed to load form data:', error);
    ElMessage.error(error?.message || '加载数据失败');
  }
}

// 保存表单
async function handleSave() {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();
  } catch {
    ElMessage.warning('请检查表单填写是否正确');
    return;
  }

  saving.value = true;
  try {
    const mainData = extractMainData(formMeta.value!.form_config.items);
    const subTables = extractSubTables(formMeta.value!.form_config.items);

    const payload = {
      main: mainData,
      sub_tables: subTables,
    };

    const listCfg = formMeta.value?.list_config;
    const action = listCfg?.afterSaveAction
      || (listCfg?.closeAfterSave === false ? 'editMode' : 'close');

    if (mode.value === 'add') {
      const result = await createFormDataApi(formCode.value, payload);
      ElMessage.success('创建成功');

      if (action === 'editMode' && result?.id) {
        const editPath = route.path.replace(/\/add$/, `/edit/${result.id}`);
        router.replace(editPath);
        return;
      } else if (action === 'continueAdd') {
        resetFormData();
        if (formMeta.value?.form_config?.items) {
          initFormData(formMeta.value.form_config.items);
        }
        return;
      }
    } else if (mode.value === 'edit') {
      await updateFormDataApi(formCode.value, editId.value!, payload);
      ElMessage.success('更新成功');
      if (action !== 'close') {
        return;
      }
    }

    handleBack();
  } catch (error: any) {
    console.error('Failed to save form data:', error);
    ElMessage.error(error.message || '保存失败');
  } finally {
    saving.value = false;
  }
}

// 返回列表页
function handleBack() {
  // 检查是否为子应用模式
  const match = route.path.match(/^\/app\/([^/]+)/);
  const devMatch = route.path.match(/^\/app-dev\/([^/]+)/);

  if (match && match[1]) {
    router.push(`/app/${match[1]}/form-render/${formCode.value}`);
  } else if (devMatch && devMatch[1]) {
    router.push(`/app-dev/${devMatch[1]}/form-render/${formCode.value}`);
  } else {
    router.push(`/form-render/${formCode.value}`);
  }
}

onMounted(() => {
  loadFormMeta();
});

// 监听路由变化
watch(
  () => [route.params.code, route.params.id, route.path],
  () => {
    resetFormData();
    loadFormMeta();
  },
);
</script>

<template>
  <Page :title="pageTitle" auto-content-height>
    <template #title>
      <div class="header-back flex items-center gap-2">
        <ElButton
          v-if="showBackButton"
          :icon="ArrowLeft"
          text
          @click="handleBack"
        >
          返回
        </ElButton>
        <h1 class="header-title">{{ pageTitle }}</h1>
      </div>
    </template>
    <template #extra>
      <div class="flex items-center gap-2">
        <ElButton
          v-if="!isReadonly"
          type="primary"
          :icon="Save"
          :loading="saving"
          @click="handleSave"
        >
          保存
        </ElButton>
      </div>
    </template>

    <div v-loading="loading" class="h-full overflow-auto">
      <div
        v-if="!loading && formMeta"
        class="form-container"
        :style="{
          width: formConf.formWidth || '100%',
          maxWidth: formConf.formMaxWidth || '100%',
          padding: `${formConf.formPaddingTop ?? formConf.formPadding ?? 24}px ${formConf.formPaddingRight ?? formConf.formPadding ?? 24}px ${formConf.formPaddingBottom ?? formConf.formPadding ?? 24}px ${formConf.formPaddingLeft ?? formConf.formPadding ?? 24}px`,
          margin: `${formConf.formMarginTop ?? formConf.formMargin ?? 0}px ${formConf.formMarginRight ?? formConf.formMargin ?? 0}px ${formConf.formMarginBottom ?? formConf.formMargin ?? 0}px ${formConf.formMarginLeft ?? formConf.formMargin ?? 0}px`,
          backgroundColor: formConf.formBackground || 'var(--el-bg-color)',
          border: formConf.formBorder
            ? '1px solid var(--el-border-color)'
            : 'none',
          borderRadius: formConf.formBorder
            ? `${formConf.formBorderRadius || 8}px`
            : '8px',
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
            :edit-id="editId"
          />
        </ElForm>
      </div>

      <div v-else-if="!loading && !formMeta" class="empty-state">
        <p class="text-muted-foreground">表单配置不存在</p>
      </div>
    </div>
  </Page>
</template>

<style scoped>
.header-back {
  flex-shrink: 0;
}
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}
/* .header-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.5;
} */
</style>
