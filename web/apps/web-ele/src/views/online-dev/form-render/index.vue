<script lang="ts" setup>
import type { FieldPermissions } from '#/api/online-dev/form-data-api';
import type { FormMeta } from '#/api/online-dev/form-manager';

import { computed, reactive, ref } from 'vue';
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
import PreviewItem from '#/components/form-design/components/PreviewItem.vue';
import { useFormData } from '#/views/online-dev/form-manager/composables/useFormData';

import FormDataList from './components/FormDataList.vue';

defineOptions({ name: 'FormRender' });

const route = useRoute();
const router = useRouter();

// 从路由获取 formCode
const formCode = computed((): string => {
  // 优先从 query 获取
  if (route.query.formCode) {
    return route.query.formCode as string;
  }

  // 其次从 params 获取
  if (route.params.code) {
    return route.params.code as string;
  }

  // 最后从路径中提取（路径格式：/form-render/xxx）
  const pathParts = route.path.split('/').filter(Boolean);
  const length = pathParts.length;
  if (length >= 2 && pathParts[length - 2] === 'form-render') {
    return pathParts[length - 1] || '';
  }

  return '';
});

// 表单元数据（从 FormDataList 加载后获取）
const formMeta = ref<FormMeta | null>(null);

// 列表配置（用于 page/layout 模式跳转）
const listConfig = computed(() => {
  const config = formMeta.value?.list_config || {};
  return {
    containerType: config.containerType || 'drawer',
    afterSaveAction:
      config.afterSaveAction ||
      (config.closeAfterSave === false ? 'editMode' : 'close'),
    page: {
      showBackButton: config.page?.showBackButton ?? true,
      openInNewTab: config.page?.openInNewTab ?? true,
    },
    layout: {
      showBackButton: config.layout?.showBackButton ?? true,
      renderMode: config.layout?.renderMode || 'condition',
    },
  };
});

// FormDataList 加载完成后的回调
function handleFormLoaded(meta: FormMeta) {
  formMeta.value = meta;
}

// ========== Layout 模式相关状态 ==========
const layoutMode = ref<'add' | 'edit' | 'list' | 'view'>('list');
const layoutEditId = ref<null | string>(null);
const layoutLoading = ref(false);
const layoutSaving = ref(false);
const layoutFormRef = ref();
const layoutFormData = reactive<Record<string, any>>({});
const layoutFieldPermissions = ref<FieldPermissions>({});
const formDataListRef = ref();

const { initFormData, extractMainData, extractSubTables, resetFormData } =
  useFormData(layoutFormData);

// Layout 模式页面标题
const layoutPageTitle = computed(() => {
  const formName = formMeta.value?.name || '';
  const titles = {
    list: formName,
    add: `新增${formName}`,
    edit: `编辑${formName}`,
    view: `查看${formName}`,
  };
  return titles[layoutMode.value];
});

// Layout 模式是否只读
const layoutIsReadonly = computed(() => layoutMode.value === 'view');

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

// 加载 Layout 模式字段权限
async function loadLayoutFieldPermissions() {
  if (!formCode.value) return;
  try {
    layoutFieldPermissions.value = await getFieldPermissionsApi(formCode.value);
  } catch (error) {
    console.error('加载字段权限失败:', error);
    layoutFieldPermissions.value = {};
  }
}

// 加载 Layout 模式编辑数据
async function loadLayoutEditData() {
  if (!layoutEditId.value) return;

  layoutLoading.value = true;
  try {
    await loadLayoutFieldPermissions();

    // 初始化表单数据
    if (formMeta.value?.form_config?.items) {
      initFormData(formMeta.value.form_config.items);
    }

    const detail = await getFormDataDetailApi(
      formCode.value,
      layoutEditId.value,
    );

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
      Object.assign(layoutFormData, trimmedData);
    }

    const subTables = detail.sub_tables;
    if (subTables) {
      Object.keys(subTables).forEach((key) => {
        if (Array.isArray(subTables[key])) {
          layoutFormData[key] = subTables[key].map((row: any) => ({
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
  } finally {
    layoutLoading.value = false;
  }
}

// Layout 模式保存表单
async function handleLayoutSave() {
  if (!layoutFormRef.value) return;

  try {
    await layoutFormRef.value.validate();
  } catch {
    ElMessage.warning('请检查表单填写是否正确');
    return;
  }

  layoutSaving.value = true;
  try {
    const mainData = extractMainData(formMeta.value!.form_config.items);
    const subTables = extractSubTables(formMeta.value!.form_config.items);

    const payload = {
      main: mainData,
      sub_tables: subTables,
    };

    const action = listConfig.value.afterSaveAction || 'close';

    if (layoutMode.value === 'add') {
      const result = await createFormDataApi(formCode.value, payload);
      ElMessage.success('创建成功');

      if (action === 'editMode' && result?.id) {
        layoutEditId.value = result.id;
        layoutMode.value = 'edit';
        formDataListRef.value?.reload();
        return;
      } else if (action === 'continueAdd') {
        resetFormData();
        if (formMeta.value?.form_config?.items) {
          initFormData(formMeta.value.form_config.items);
        }
        formDataListRef.value?.reload();
        return;
      }
    } else if (layoutMode.value === 'edit') {
      await updateFormDataApi(formCode.value, layoutEditId.value!, payload);
      ElMessage.success('更新成功');
      if (action !== 'close') {
        formDataListRef.value?.reload();
        return;
      }
    }

    handleLayoutBack();
  } catch (error: any) {
    console.error('Failed to save form data:', error);
    ElMessage.error(error.message || '保存失败');
  } finally {
    layoutSaving.value = false;
  }
}

// Layout 模式返回列表
function handleLayoutBack() {
  layoutMode.value = 'list';
  layoutEditId.value = null;
  resetFormData();
  // 刷新列表数据
  formDataListRef.value?.reload();
}

// 构建路径的辅助函数
function buildPath(action: string, id?: string, useLayout = false) {
  const match = route.path.match(/^\/app\/([^/]+)/);
  const devMatch = route.path.match(/^\/app-dev\/([^/]+)/);
  const pathType = useLayout ? 'form-layout' : 'form-render';

  let basePath: string;
  if (match && match[1]) {
    basePath = `/app/${match[1]}/${pathType}/${formCode.value}`;
  } else if (devMatch && devMatch[1]) {
    basePath = `/app-dev/${devMatch[1]}/${pathType}/${formCode.value}`;
  } else {
    basePath = `/${pathType}/${formCode.value}`;
  }
  return id ? `${basePath}/${action}/${id}` : `${basePath}/${action}`;
}

// 导航的辅助函数（仅用于 page 模式）
function navigateTo(path: string) {
  if (listConfig.value.page.openInNewTab) {
    window.open(path, '_blank');
  } else {
    router.push(path);
  }
}

// page/layout 模式跳转处理
function handleAdd() {
  const containerType = listConfig.value.containerType;
  if (containerType === 'page') {
    navigateTo(buildPath('add'));
  } else if (containerType === 'layout') {
    const renderMode = listConfig.value.layout.renderMode;
    if (renderMode === 'route') {
      // Layout 路由渲染模式：跳转到 form-layout 路由
      router.push(buildPath('add', undefined, true));
    } else {
      // Layout 条件渲染模式：使用 v-if 切换
      layoutMode.value = 'add';
      layoutEditId.value = null;
      resetFormData();
      loadLayoutFieldPermissions().then(() => {
        if (formMeta.value?.form_config?.items) {
          initFormData(formMeta.value.form_config.items);
        }
      });
    }
  }
}

function handleView(row: any) {
  const containerType = listConfig.value.containerType;
  if (containerType === 'page') {
    navigateTo(buildPath('view', row.id));
  } else if (containerType === 'layout') {
    const renderMode = listConfig.value.layout.renderMode;
    if (renderMode === 'route') {
      // Layout 路由渲染模式：跳转到 form-layout 路由
      router.push(buildPath('view', row.id, true));
    } else {
      // Layout 条件渲染模式：使用 v-if 切换
      layoutMode.value = 'view';
      layoutEditId.value = row.id;
      loadLayoutEditData();
    }
  }
}

function handleEdit(row: any) {
  const containerType = listConfig.value.containerType;
  if (containerType === 'page') {
    navigateTo(buildPath('edit', row.id));
  } else if (containerType === 'layout') {
    const renderMode = listConfig.value.layout.renderMode;
    if (renderMode === 'route') {
      // Layout 路由渲染模式：跳转到 form-layout 路由
      router.push(buildPath('edit', row.id, true));
    } else {
      // Layout 条件渲染模式：使用 v-if 切换
      layoutMode.value = 'edit';
      layoutEditId.value = row.id;
      loadLayoutEditData();
    }
  }
}

// 判断是否需要使用自定义处理（page/layout 模式）
const isPageMode = computed(
  () =>
    listConfig.value.containerType === 'page' ||
    listConfig.value.containerType === 'layout',
);

// 是否为 Layout 容器模式（条件渲染）
const isLayoutContainer = computed(
  () =>
    listConfig.value.containerType === 'layout' &&
    listConfig.value.layout.renderMode === 'condition',
);
</script>

<template>
  <div class="h-full">
    <!-- Layout 模式：表单视图 -->
    <Page
      v-if="isLayoutContainer && layoutMode !== 'list'"
      :title="layoutPageTitle"
      :height-offset="36"
      auto-content-height
    >
      <template #title>
        <div class="header-back flex items-center gap-2">
          <ElButton
            v-if="listConfig.layout.showBackButton"
            :icon="ArrowLeft"
            text
            @click="handleLayoutBack"
          >
            返回
          </ElButton>
          <h1 class="header-title">{{ layoutPageTitle }}</h1>
        </div>
      </template>
      <template #extra>
        <div class="flex items-center gap-2">
          <ElButton
            v-if="!layoutIsReadonly"
            type="primary"
            :icon="Save"
            :loading="layoutSaving"
            @click="handleLayoutSave"
          >
            保存
          </ElButton>
        </div>
      </template>

      <div v-loading="layoutLoading" class="h-full">
        <div
          v-if="!layoutLoading && formMeta"
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
            ref="layoutFormRef"
            :model="layoutFormData"
            :label-width="`${formConf.labelWidth || 100}px`"
            :label-position="formConf.labelPosition || 'right'"
            :size="formConf.size || 'default'"
            :disabled="layoutIsReadonly"
            :style="{
              '--el-form-item-margin-bottom': `${formConf.itemSpacing || 18}px`,
            }"
          >
            <PreviewItem
              v-for="item in formConf.items"
              :key="item.id"
              :item="item"
              :model-value="layoutFormData"
              :is-edit="layoutMode !== 'add'"
              :field-permissions="layoutFieldPermissions"
              :form-code="formCode"
              :edit-id="layoutEditId ?? undefined"
            />
          </ElForm>
        </div>

        <div v-else-if="!layoutLoading && !formMeta" class="empty-state">
          <p class="text-muted-foreground">表单配置不存在</p>
        </div>
      </div>
    </Page>

    <!-- 列表视图 -->
    <FormDataList
      v-show="!isLayoutContainer || layoutMode === 'list'"
      ref="formDataListRef"
      :form-code="formCode"
      :use-export-config="true"
      :on-add="isPageMode ? handleAdd : undefined"
      :on-view="isPageMode ? handleView : undefined"
      :on-edit="isPageMode ? handleEdit : undefined"
      @loaded="handleFormLoaded"
    />
  </div>
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
</style>
