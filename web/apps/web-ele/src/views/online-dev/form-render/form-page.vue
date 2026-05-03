<script lang="ts" setup>
import type { FieldPermissions } from '#/api/online-dev/form-data-api';
import type { FormMeta } from '#/api/online-dev/form-manager';

import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

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

defineOptions({ name: 'FormPage' });

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
  // 从表单的 list_config 中读取配置
  const pageConfig = formMeta.value?.list_config?.page;
  // 默认显示，只有明确设置为 false 时才隐藏
  return pageConfig?.showBackButton ?? false;
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
    // 先加载字段权限
    await loadFieldPermissions();

    formMeta.value = await getFormByCodeApi(formCode.value);

    // 初始化表单数据
    if (formMeta.value.form_config?.items) {
      initFormData(formMeta.value.form_config.items);
    }

    // 如果是编辑或查看模式，加载数据
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
  if (match && match[1]) {
    // 子应用模式
    router.push(`/app/${match[1]}/form-render/${formCode.value}`);
  } else {
    // 主应用模式
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
  <div class="form-page-container">
    <!-- 固定头部 -->
    <div class="form-page-header">
      <div class="header-content">
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
          <p v-if="formMeta?.description" class="header-description">
            {{ formMeta.description }}
          </p>
        </div>
        <div class="header-center">
          <!-- <h1 class="header-title">{{ pageTitle }}</h1>
          <p v-if="formMeta?.description" class="header-description">
            {{ formMeta.description }}
          </p> -->
        </div>
        <div class="header-actions">
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
      </div>
    </div>

    <!-- 可滚动内容区域 -->
    <div v-loading="loading" class="form-page-content">
      <div
        v-if="!loading && formMeta"
        class="form-container"
        :style="{
          width: formConf.formWidth || '100%',
          maxWidth: formConf.formMaxWidth || '1200px',
          padding: `${formConf.formPaddingTop ?? formConf.formPadding ?? 48}px ${formConf.formPaddingRight ?? formConf.formPadding ?? 48}px ${formConf.formPaddingBottom ?? formConf.formPadding ?? 48}px ${formConf.formPaddingLeft ?? formConf.formPadding ?? 48}px`,
          margin: `${formConf.formMarginTop ?? formConf.formMargin ?? 0}px ${formConf.formMarginRight ?? formConf.formMargin ?? 0}px ${formConf.formMarginBottom ?? formConf.formMargin ?? 0}px ${formConf.formMarginLeft ?? formConf.formMargin ?? 0}px`,
          backgroundColor: formConf.formBackground || 'var(--el-bg-color)',
          border: formConf.formBorder
            ? '1px solid var(--el-border-color)'
            : 'none',
          borderRadius: formConf.formBorder
            ? `${formConf.formBorderRadius || 12}px`
            : '12px',
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
  </div>
</template>

<style scoped>
.form-page-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.form-page-header {
  flex-shrink: 0;
  padding: 16px 24px;
  background-color: var(--el-bg-color);
  border-bottom: 2px solid var(--el-bg-color-page);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.header-back {
  flex-shrink: 0;
}

.header-center {
  flex: 1;
  min-width: 0;
  text-align: center;
}

.header-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.5;
}

.header-description {
  margin: 4px 0 0;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

.header-actions {
  flex-shrink: 0;
}

.form-page-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background-color: var(--el-bg-color-page);
}

/* .form-container 的所有样式通过动态绑定设置 */

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

/* 滚动条样式 */
.form-page-content {
  scrollbar-width: thin;
  scrollbar-color: var(--el-border-color) transparent;
}

.form-page-content::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.form-page-content::-webkit-scrollbar-thumb {
  background-color: var(--el-border-color);
  border-radius: 3px;
}

.form-page-content::-webkit-scrollbar-thumb:hover {
  background-color: var(--el-border-color-dark);
}

.form-page-content::-webkit-scrollbar-track {
  background-color: transparent;
}
</style>
