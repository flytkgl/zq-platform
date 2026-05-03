<script lang="ts" setup>
import type { FormMetaListItem } from '#/api/online-dev/form-manager';

import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import {
  CirclePlus,
  Code,
  Copy,
  Edit,
  ExternalLink,
  Eye,
  FileText,
  Home,
  MoreVertical,
  Play,
  Settings,
  Square,
  Trash2,
} from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElCard,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElPagination,
  ElSelect,
  ElTag,
  ElTooltip,
} from 'element-plus';

import {
  copyFormApi,
  createFormApi,
  deleteFormApi,
  getFormListApi,
  unpublishFormApi,
  updateFormApi,
} from '#/api/online-dev/form-manager';
import {
  getPreferencesConfigApi,
  updatePreferencesConfigApi,
} from '#/api/core/ui-config';
import { ZqDialog } from '#/components/zq-dialog';
import { useAppContextStore } from '#/store/app-context';

import ApiInfoDialog from './modules/api-info-dialog.vue';
import PreviewDialog from './modules/preview-dialog.vue';
import PublishDialog from './modules/publish-dialog.vue';

defineOptions({ name: 'FormManager' });

const router = useRouter();
const appContextStore = useAppContextStore();

// 搜索关键词
const searchKeyword = ref('');

// 列表数据
const loading = ref(false);
const formList = ref<FormMetaListItem[]>([]);

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 36,
  total: 0,
});

// 弹窗状态
const dialogVisible = ref(false);
const dialogTitle = ref('');
const isEditMode = ref(false);
const formLoading = ref(false);
const formRef = ref();
const showPublishDialog = ref(false);
const publishingForm = ref<FormMetaListItem | null>(null);
const showPreviewDialog = ref(false);
const previewingFormId = ref<null | string>(null);
const showApiInfoDialog = ref(false);
const apiInfoForm = ref<FormMetaListItem | null>(null);
const showSetHomeDialog = ref(false);
const setHomeForm = ref<FormMetaListItem | null>(null);
const setHomeLoading = ref(false);

// 基础信息表单
const basicForm = reactive({
  id: '',
  name: '',
  code: '',
  form_type: 'normal' as 'normal' | 'workflow',
  sort: 0,
  description: '',
});

// 获取列表
async function fetchList() {
  loading.value = true;
  try {
    const res = await getFormListApi({
      page: pagination.current,
      pageSize: pagination.pageSize,
      applicationId: appContextStore.currentApp?.id,
      name: searchKeyword.value || undefined,
    });
    formList.value = res.items;
    pagination.total = res.total;
  } catch (error) {
    console.error('获取表单列表失败:', error);
  } finally {
    loading.value = false;
  }
}

// 搜索
function handleSearch() {
  pagination.current = 1;
  fetchList();
}

// 分页变化
function handlePageChange(page: number) {
  pagination.current = page;
  fetchList();
}

// 每页条数变化
function handleSizeChange(size: number) {
  pagination.pageSize = size;
  pagination.current = 1;
  fetchList();
}

// 创建表单 - 只显示基础信息弹窗
function handleCreate() {
  isEditMode.value = false;
  basicForm.id = '';
  basicForm.name = '';
  basicForm.code = '';
  basicForm.form_type = 'normal';
  basicForm.sort = 0;
  basicForm.description = '';
  dialogTitle.value = $t('form-manager.editor.create');
  dialogVisible.value = true;
}

// 编辑基础信息
async function handleEditInfo(item: FormMetaListItem) {
  isEditMode.value = true;
  basicForm.id = item.id;
  basicForm.name = item.name;
  basicForm.code = item.code;
  basicForm.form_type = item.form_type || 'normal';
  basicForm.sort = item.sort || 0;
  basicForm.description = item.description || '';
  dialogTitle.value = $t('form-manager.editor.edit');
  dialogVisible.value = true;
}

// 进入设计页面
function handleDesign(item: FormMetaListItem) {
  router.push(
    appContextStore.getContextPath(
      `/online-dev/form-manager/editor/${item.id}`,
    ),
  );
}

// 确认创建/编辑基础信息
async function handleConfirm() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      formLoading.value = true;
      try {
        if (isEditMode.value) {
          await updateFormApi(basicForm.id, {
            name: basicForm.name,
            form_type: basicForm.form_type,
            description: basicForm.description,
            sort: basicForm.sort,
          });
          ElMessage.success($t('form-manager.saveSuccess'));
          dialogVisible.value = false;
          fetchList();
        } else {
          const res = await createFormApi({
            application_id: appContextStore.currentApp?.id,
            name: basicForm.name,
            code: basicForm.code,
            form_type: basicForm.form_type,
            description: basicForm.description,
            sort: basicForm.sort,
            db_config: 'default',
            main_table: '',
          });
          ElMessage.success($t('form-manager.editor.createSuccess'));
          dialogVisible.value = false;
          fetchList();
          // 创建后直接跳转设计页面
          router.push(
            appContextStore.getContextPath(
              `/online-dev/form-manager/editor/${res.id}`,
            ),
          );
        }
      } catch {
        // error handled by request interceptor
      } finally {
        formLoading.value = false;
      }
    }
  });
}

// 预览表单
function handlePreview(item: FormMetaListItem) {
  previewingFormId.value = item.id;
  showPreviewDialog.value = true;
}

// 删除表单
async function handleDelete(item: FormMetaListItem) {
  try {
    await ElMessageBox.confirm(
      $t('form-manager.deleteConfirm', { name: item.name }),
      $t('form-manager.deleteConfirmTitle'),
      { type: 'warning' },
    );
    await deleteFormApi(item.id);
    ElMessage.success($t('form-manager.deleteSuccess', { name: item.name }));
    fetchList();
  } catch {
    // 用户取消
  }
}

// 发布表单
function handlePublish(item: FormMetaListItem) {
  publishingForm.value = item;
  showPublishDialog.value = true;
}

// 发布成功回调
function handlePublished() {
  fetchList();
}

// 停用表单
async function handleUnpublish(item: FormMetaListItem) {
  try {
    await ElMessageBox.confirm(
      $t('form-manager.unpublishConfirmMessage'),
      $t('form-manager.unpublishConfirmTitle'),
      { type: 'warning', dangerouslyUseHTMLString: true },
    );
    await unpublishFormApi(item.id);
    ElMessage.success($t('form-manager.unpublishSuccess', { name: item.name }));
    fetchList();
  } catch {
    // 用户取消
  }
}

// 复制表单
async function handleCopy(item: FormMetaListItem) {
  try {
    const { value: newCode } = await ElMessageBox.prompt(
      $t('form-manager.copyCodePlaceholder'),
      $t('form-manager.copyTitle'),
      {
        inputPattern: /^[\w-]+$/,
        inputErrorMessage: $t('form-manager.copyCodeRule'),
        inputValue: `${item.code}_copy`,
      },
    );
    await copyFormApi(
      item.id,
      newCode,
      `${item.name} (${$t('form-manager.copy')})`,
    );
    ElMessage.success($t('form-manager.copySuccess'));
    fetchList();
  } catch {
    // 用户取消
  }
}

// 访问表单
function handleVisit(item: FormMetaListItem) {
  const appCode = appContextStore.currentApp?.code || '';
  const path = `/app/${appCode}/form-render/${item.code}`;
  const routeData = router.resolve(path);
  window.open(routeData.href, '_blank');
}

// 查看 API 信息
function handleApiInfo(item: FormMetaListItem) {
  apiInfoForm.value = item;
  showApiInfoDialog.value = true;
}

// 设为首页
function handleSetHome(item: FormMetaListItem) {
  setHomeForm.value = item;
  showSetHomeDialog.value = true;
}

function getSetHomePath(item: FormMetaListItem): string {
  const basePath = `/form-render/${item.code}`;
  const code = item.application_code || appContextStore.appCode;
  return code ? `/app/${code}${basePath}` : basePath;
}

async function confirmSetHome() {
  if (!setHomeForm.value) return;
  setHomeLoading.value = true;
  try {
    const fullPath = getSetHomePath(setHomeForm.value);
    const applicationId =
      setHomeForm.value.application_id || appContextStore.currentApp?.id;
    const currentConfig =
      (await getPreferencesConfigApi(applicationId)) ?? {};
    const newConfig = {
      ...currentConfig,
      app: {
        ...currentConfig.app,
        defaultHomePath: fullPath,
      },
    };
    await updatePreferencesConfigApi(newConfig, applicationId);
    ElMessage.success($t('form-manager.setHomeSuccess'));
    showSetHomeDialog.value = false;
  } catch {
    ElMessage.error($t('form-manager.setHomeFailed'));
  } finally {
    setHomeLoading.value = false;
  }
}

// 处理更多菜单命令
function handleCommand(command: string, form: FormMetaListItem) {
  switch (command) {
    case 'visit': {
      handleVisit(form);
      break;
    }
    case 'copy': {
      handleCopy(form);
      break;
    }
    case 'edit': {
      handleEditInfo(form);
      break;
    }
    case 'preview': {
      handlePreview(form);
      break;
    }
    case 'publish': {
      handlePublish(form);
      break;
    }
    case 'unpublish': {
      handleUnpublish(form);
      break;
    }
    case 'api': {
      handleApiInfo(form);
      break;
    }
    case 'setHome': {
      handleSetHome(form);
      break;
    }
  }
}

// 获取状态标签类型
function getStatusType(status: string) {
  return status === 'published' ? 'success' : 'info';
}

// 获取状态文本
function getStatusText(status: string) {
  return status === 'published'
    ? $t('form-manager.statusMap.published')
    : $t('form-manager.statusMap.draft');
}

// 获取类型文本
function getTypeText(formType: string) {
  return formType === 'workflow'
    ? $t('form-manager.typeMap.workflow')
    : $t('form-manager.typeMap.normal');
}

// 获取类型标签类型
function getTypeTagType(formType: string) {
  return formType === 'workflow' ? 'warning' : 'primary';
}

onMounted(() => {
  fetchList();
});
</script>

<template>
  <div class="form-list-page">
    <Page auto-content-height v-loading="loading">
      <template #title>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <ElInput
              v-model="searchKeyword"
              :placeholder="$t('form-manager.placeholder.name')"
              clearable
              class="w-64"
              @keyup.enter="handleSearch"
            />
            <ElButton @click="handleSearch">{{ $t('common.search') }}</ElButton>
          </div>
          <ElButton type="primary" @click="handleCreate">
            <CirclePlus class="mr-1 h-4 w-4" />
            {{ $t('form-manager.create') }}
          </ElButton>
        </div>
      </template>

      <!-- 表单卡片列表 -->
      <div
        v-if="formList.length > 0"
        class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
      >
        <ElCard
          v-for="form in formList"
          :key="form.id"
          class="group form-card cursor-pointer transition-shadow"
          shadow="hover"
          :body-style="{ padding: '0' }"
          style="border: none"
          @click="handleDesign(form)"
        >
          <div class="p-4">
            <!-- 头部：图标 + 右侧信息区 -->
            <div class="mb-4 flex gap-3">
              <div
                class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg"
                :class="
                  form.form_type === 'workflow'
                    ? 'bg-warning/10'
                    : 'bg-primary/10'
                "
              >
                <FileText
                  class="h-5 w-5"
                  :class="
                    form.form_type === 'workflow'
                      ? 'text-warning'
                      : 'text-primary'
                  "
                />
              </div>
              <div class="min-w-0 flex-1">
                <!-- name + 操作 -->
                <div class="flex items-center justify-between">
                  <div class="min-w-0 flex-1 whitespace-nowrap text-sm font-medium group-hover:truncate">
                    {{ form.name }}
                  </div>
                  <div
                    class="flex flex-shrink-0 items-center -space-x-1 opacity-0 transition-opacity group-hover:opacity-100"
                    @click.stop
                  >
                    <ElTooltip
                      :content="$t('form-manager.design')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleDesign(form)">
                        <Settings class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip
                      :content="$t('form-manager.editInfo')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleEditInfo(form)">
                        <Edit class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip :content="$t('common.delete')" placement="top">
                      <ElButton text size="small" @click="handleDelete(form)">
                        <Trash2 class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElDropdown
                      trigger="click"
                      @command="(cmd: string) => handleCommand(cmd, form)"
                    >
                      <ElButton text size="small">
                        <MoreVertical class="h-3.5 w-3.5" />
                      </ElButton>
                      <template #dropdown>
                        <ElDropdownMenu>
                          <ElDropdownItem
                            v-if="form.status === 'published'"
                            command="visit"
                          >
                            <ExternalLink class="mr-2 h-4 w-4" />
                            {{ $t('form-manager.visit') }}
                          </ElDropdownItem>
                          <ElDropdownItem command="preview">
                            <Eye class="mr-2 h-4 w-4" />
                            {{ $t('form-manager.preview') }}
                          </ElDropdownItem>
                          <ElDropdownItem command="copy">
                            <Copy class="mr-2 h-4 w-4" />
                            {{ $t('form-manager.copy') }}
                          </ElDropdownItem>
                          <ElDropdownItem command="api">
                            <Code class="mr-2 h-4 w-4" />
                            API
                          </ElDropdownItem>
                          <ElDropdownItem
                            v-if="form.status === 'draft'"
                            command="publish"
                          >
                            <Play class="mr-2 h-4 w-4" />
                            {{ $t('form-manager.publish') }}
                          </ElDropdownItem>
                          <ElDropdownItem
                            v-if="form.status === 'published'"
                            command="unpublish"
                          >
                            <Square class="mr-2 h-4 w-4" />
                            {{ $t('form-manager.unpublish') }}
                          </ElDropdownItem>
                          <ElDropdownItem
                            v-if="form.status === 'published'"
                            command="setHome"
                          >
                            <Home class="mr-2 h-4 w-4" />
                            {{ $t('form-manager.setAsHome') }}
                          </ElDropdownItem>
                        </ElDropdownMenu>
                      </template>
                    </ElDropdown>
                  </div>
                </div>
                <!-- code -->
                <div class="text-muted-foreground font-mono text-xs">
                  {{ form.code }}
                </div>
              </div>
            </div>
            <!-- 描述 -->
            <div
              class="text-muted-foreground mb-4 line-clamp-1 min-h-[18px] text-xs"
            >
              {{ form.description }}
            </div>
            <!-- 标签 + 创建时间 -->
            <div class="mb-4 flex items-center justify-between">
              <div class="flex gap-1">
                <ElTag size="small" :type="getStatusType(form.status)">
                  {{ getStatusText(form.status) }}
                </ElTag>
                <ElTag size="small" :type="getTypeTagType(form.form_type)">
                  {{ getTypeText(form.form_type) }}
                </ElTag>
              </div>
            </div>
            <!-- 应用名称 + 创建时间 -->
            <div class="flex items-center justify-between">
              <div class="text-muted-foreground flex gap-1 text-xs">
                <div v-if="form.application_name">
                  {{ form.application_name }}
                </div>
                <div v-else size="small">
                  {{ $t('common.mainApp') }}
                </div>
              </div>
              <span class="text-muted-foreground text-xs">
                {{ form.sys_create_datetime }}
              </span>
            </div>
          </div>
        </ElCard>
      </div>

      <!-- 空状态 -->
      <ElEmpty v-else :description="$t('common.noData')" />

      <!-- 分页 -->
      <template #footer>
        <div class="flex w-full items-center justify-end">
          <ElPagination
            v-model:current-page="pagination.current"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[36, 48, 60, 72, 84]"
            :pager-count="7"
            layout="total, sizes, prev, pager, next, jumper"
            background
            size="small"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </div>
      </template>
    </Page>

    <!-- 创建/编辑基础信息弹窗 -->
    <ZqDialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :confirm-loading="formLoading"
      width="500px"
      @confirm="handleConfirm"
    >
      <ElForm
        ref="formRef"
        :model="basicForm"
        label-position="top"
        :rules="{
          name: [
            {
              required: true,
              message: $t('form-manager.placeholder.name'),
              trigger: 'blur',
            },
          ],
          code: [
            {
              required: true,
              message: $t('form-manager.placeholder.code'),
              trigger: 'blur',
            },
            {
              pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/,
              message: $t('form-manager.codeFormatError'),
              trigger: 'blur',
            },
          ],
        }"
      >
        <ElFormItem :label="$t('form-manager.name')" prop="name">
          <ElInput
            v-model="basicForm.name"
            :placeholder="$t('form-manager.placeholder.name')"
          />
        </ElFormItem>
        <ElFormItem :label="$t('form-manager.code')" prop="code">
          <ElInput
            v-model="basicForm.code"
            :placeholder="$t('form-manager.placeholder.code')"
            :disabled="isEditMode"
          />
        </ElFormItem>
        <ElFormItem :label="$t('form-manager.type')" prop="form_type">
          <ElSelect v-model="basicForm.form_type" style="width: 100%">
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
            :rows="3"
            :placeholder="$t('form-manager.editor.placeholder.remark')"
          />
        </ElFormItem>
      </ElForm>
    </ZqDialog>

    <!-- 预览弹窗 -->
    <PreviewDialog v-model="showPreviewDialog" :form-id="previewingFormId" />

    <!-- 发布配置弹窗 -->
    <PublishDialog
      v-if="publishingForm"
      v-model="showPublishDialog"
      :form-id="publishingForm.id"
      :form-name="publishingForm.name"
      :form-code="publishingForm.code"
      @published="handlePublished"
    />

    <!-- API 信息弹窗 -->
    <ApiInfoDialog
      v-if="apiInfoForm"
      v-model="showApiInfoDialog"
      :form-id="apiInfoForm.id"
      :form-code="apiInfoForm.code"
      :form-name="apiInfoForm.name"
    />

    <!-- 设为首页弹窗 -->
    <ZqDialog
      v-model="showSetHomeDialog"
      :title="$t('form-manager.setAsHomeTitle')"
      :confirm-loading="setHomeLoading"
      width="460px"
      @confirm="confirmSetHome"
    >
      <div class="space-y-3 px-2">
        <p class="text-sm">
          {{ $t('form-manager.setAsHomeConfirm', { name: setHomeForm?.name }) }}
        </p>
        <div class="bg-secondary rounded p-3">
          <div class="text-muted-foreground text-xs">
            {{ $t('form-manager.setAsHomePath') }}
          </div>
          <div class="mt-1 font-mono text-sm">
            {{ setHomeForm ? getSetHomePath(setHomeForm) : '' }}
          </div>
        </div>
        <p
          v-if="setHomeForm?.application_code"
          class="text-muted-foreground text-xs"
        >
          {{ $t('form-manager.setAsHomeAppTip', { app: setHomeForm.application_name || setHomeForm.application_code }) }}
        </p>
        <p class="text-muted-foreground text-xs">
          {{ $t('form-manager.setAsHomeTip') }}
        </p>
      </div>
    </ZqDialog>
  </div>
</template>

<style scoped>
.form-card :deep(.el-card__body) {
  padding: 0;
}
</style>
