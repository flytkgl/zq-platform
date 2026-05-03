<script lang="ts" setup>
import type { PageMetaListItem } from '#/api/online-dev/page-manager';

import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import { Page } from '@vben/common-ui';
import {
  Copy,
  Edit,
  Eye,
  FileCode,
  Home,
  MoreVertical,
  Play,
  Plus,
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
  ElPagination,
  ElTag,
  ElTooltip,
} from 'element-plus';

import {
  copyPageApi,
  createPageApi,
  deletePageApi,
  getPageListApi,
  unpublishPageApi,
  updatePageApi,
} from '#/api/online-dev/page-manager';
import {
  getPreferencesConfigApi,
  updatePreferencesConfigApi,
} from '#/api/core/ui-config';
import { ZqDialog } from '#/components/zq-dialog';
import { useAppContextStore } from '#/store/app-context';

import PreviewDialog from './modules/preview-dialog.vue';
import PublishDialog from './modules/publish-dialog.vue';

defineOptions({ name: 'PageManager' });

const router = useRouter();
const appContextStore = useAppContextStore();

// 搜索关键词
const searchKeyword = ref('');

// 列表数据
const loading = ref(false);
const pageList = ref<PageMetaListItem[]>([]);

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
const publishingPage = ref<null | PageMetaListItem>(null);
const showPreviewDialog = ref(false);
const previewingPageId = ref<null | string>(null);
const showSetHomeDialog = ref(false);
const setHomePage = ref<null | PageMetaListItem>(null);
const setHomeLoading = ref(false);

// 基础信息表单
const basicForm = reactive({
  id: '',
  name: '',
  code: '',
  category: '',
  sort: 0,
  description: '',
});

// 获取列表
async function fetchList() {
  loading.value = true;
  try {
    const res = await getPageListApi({
      page: pagination.current,
      pageSize: pagination.pageSize,
      applicationId: appContextStore.currentApp?.id,
      name: searchKeyword.value || undefined,
    });
    pageList.value = res.items;
    pagination.total = res.total;
  } catch (error) {
    console.error('获取页面列表失败:', error);
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

// 创建 - 只显示基础信息弹窗
function handleCreate() {
  isEditMode.value = false;
  basicForm.id = '';
  basicForm.name = '';
  basicForm.code = '';
  basicForm.category = '';
  basicForm.sort = 0;
  basicForm.description = '';
  dialogTitle.value = $t('page-manager.editor.create');
  dialogVisible.value = true;
}

// 编辑基础信息
function handleEditInfo(item: PageMetaListItem) {
  isEditMode.value = true;
  basicForm.id = item.id;
  basicForm.name = item.name;
  basicForm.code = item.code;
  basicForm.category = item.category || '';
  basicForm.sort = item.sort || 0;
  basicForm.description = item.description || '';
  dialogTitle.value = $t('page-manager.editor.edit');
  dialogVisible.value = true;
}

// 进入设计页面
function handleDesign(item: PageMetaListItem) {
  router.push(
    appContextStore.getContextPath(
      `/online-dev/page-manager/editor/${item.id}`,
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
          await updatePageApi(basicForm.id, {
            name: basicForm.name,
            category: basicForm.category,
            description: basicForm.description,
            sort: basicForm.sort,
          });
          ElMessage.success($t('page-manager.saveSuccess'));
          dialogVisible.value = false;
          fetchList();
        } else {
          const res = await createPageApi({
            application_id: appContextStore.currentApp?.id,
            name: basicForm.name,
            code: basicForm.code,
            category: basicForm.category,
            description: basicForm.description,
            sort: basicForm.sort,
          });
          ElMessage.success($t('page-manager.editor.createSuccess'));
          dialogVisible.value = false;
          fetchList();
          // 创建后直接跳转设计页面
          router.push(
            appContextStore.getContextPath(
              `/online-dev/page-manager/editor/${res.id}`,
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

// 预览
function handlePreview(item: PageMetaListItem) {
  previewingPageId.value = item.id;
  showPreviewDialog.value = true;
}

// 删除
async function handleDelete(item: PageMetaListItem) {
  try {
    await ElMessageBox.confirm(
      $t('page-manager.deleteConfirm', { name: item.name }),
      $t('page-manager.deleteConfirmTitle'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        type: 'warning',
      },
    );
    await deletePageApi(item.id);
    ElMessage.success($t('page-manager.deleteSuccess', { name: item.name }));
    fetchList();
  } catch {
    // 用户取消
  }
}

// 发布
function handlePublish(item: PageMetaListItem) {
  publishingPage.value = item;
  showPublishDialog.value = true;
}

// 发布成功回调
function handlePublished() {
  fetchList();
}

// 停用
async function handleUnpublish(item: PageMetaListItem) {
  try {
    await unpublishPageApi(item.id);
    ElMessage.success($t('page-manager.unpublishSuccess', { name: item.name }));
    fetchList();
  } catch {
    ElMessage.error($t('page-manager.unpublishFailed'));
  }
}

// 复制
async function handleCopy(item: PageMetaListItem) {
  try {
    const { value: newCode } = await ElMessageBox.prompt(
      $t('page-manager.copyCodePlaceholder'),
      $t('page-manager.copyTitle'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        inputPattern: /^[\w-]+$/,
        inputErrorMessage: $t('page-manager.copyCodeRule'),
        inputValue: `${item.code}_copy`,
      },
    );
    await copyPageApi(
      item.id,
      newCode,
      `${item.name} (${$t('page-manager.copy')})`,
    );
    ElMessage.success($t('page-manager.copySuccess'));
    fetchList();
  } catch {
    // 用户取消
  }
}

// 设为首页
function handleSetHome(item: PageMetaListItem) {
  setHomePage.value = item;
  showSetHomeDialog.value = true;
}

function getSetHomePath(item: PageMetaListItem): string {
  const basePath = `/page-render/${item.code}`;
  const code = item.application_code || appContextStore.appCode;
  return code ? `/app/${code}${basePath}` : basePath;
}

async function confirmSetHome() {
  if (!setHomePage.value) return;
  setHomeLoading.value = true;
  try {
    const fullPath = getSetHomePath(setHomePage.value);
    const applicationId =
      setHomePage.value.application_id || appContextStore.currentApp?.id;
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
    ElMessage.success($t('page-manager.setHomeSuccess'));
    showSetHomeDialog.value = false;
  } catch {
    ElMessage.error($t('page-manager.setHomeFailed'));
  } finally {
    setHomeLoading.value = false;
  }
}

// 处理更多菜单命令
function handleCommand(command: string, item: PageMetaListItem) {
  switch (command) {
    case 'copy': {
      handleCopy(item);
      break;
    }
    case 'edit': {
      handleEditInfo(item);
      break;
    }
    case 'preview': {
      handlePreview(item);
      break;
    }
    case 'publish': {
      handlePublish(item);
      break;
    }
    case 'unpublish': {
      handleUnpublish(item);
      break;
    }
    case 'setHome': {
      handleSetHome(item);
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
    ? $t('page-manager.statusMap.published')
    : $t('page-manager.statusMap.draft');
}

onMounted(() => {
  fetchList();
});
</script>

<template>
  <div class="page-list-page">
    <Page auto-content-height v-loading="loading">
      <template #title>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <ElInput
              v-model="searchKeyword"
              :placeholder="$t('page-manager.placeholder.name')"
              clearable
              class="w-64"
              @keyup.enter="handleSearch"
            />
            <ElButton @click="handleSearch">{{ $t('common.search') }}</ElButton>
          </div>
          <ElButton type="primary" @click="handleCreate">
            <Plus class="mr-1 h-4 w-4" />
            {{ $t('page-manager.create') }}
          </ElButton>
        </div>
      </template>

      <!-- 页面卡片列表 -->
      <div
        v-if="pageList.length > 0"
        class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
      >
        <ElCard
          v-for="item in pageList"
          :key="item.id"
          class="group page-card cursor-pointer transition-shadow"
          shadow="hover"
          :body-style="{ padding: '0' }"
          style="border: none"
          @click="handleDesign(item)"
        >
          <div class="p-4">
            <!-- 头部：图标 + 右侧信息区 -->
            <div class="mb-4 flex gap-3">
              <div
                class="bg-primary/10 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg"
              >
                <FileCode class="text-primary h-5 w-5" />
              </div>
              <div class="min-w-0 flex-1">
                <!-- name + 操作 -->
                <div class="flex items-center justify-between">
                  <div class="min-w-0 flex-1 whitespace-nowrap text-sm font-medium group-hover:truncate">
                    {{ item.name }}
                  </div>
                  <div
                    class="flex flex-shrink-0 items-center -space-x-1 opacity-0 transition-opacity group-hover:opacity-100"
                    @click.stop
                  >
                    <ElTooltip
                      :content="$t('page-manager.design')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleDesign(item)">
                        <Settings class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip
                      :content="$t('page-manager.editInfo')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleEditInfo(item)">
                        <Edit class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip :content="$t('common.delete')" placement="top">
                      <ElButton text size="small" @click="handleDelete(item)">
                        <Trash2 class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElDropdown
                      trigger="click"
                      @command="(cmd: string) => handleCommand(cmd, item)"
                    >
                      <ElButton text size="small">
                        <MoreVertical class="h-3.5 w-3.5" />
                      </ElButton>
                      <template #dropdown>
                        <ElDropdownMenu>
                          <ElDropdownItem command="preview">
                            <Eye class="mr-2 h-4 w-4" />
                            {{ $t('page-manager.preview') }}
                          </ElDropdownItem>
                          <ElDropdownItem command="copy">
                            <Copy class="mr-2 h-4 w-4" />
                            {{ $t('page-manager.copy') }}
                          </ElDropdownItem>
                          <ElDropdownItem
                            v-if="item.status === 'draft'"
                            command="publish"
                          >
                            <Play class="mr-2 h-4 w-4" />
                            {{ $t('page-manager.publish') }}
                          </ElDropdownItem>
                          <ElDropdownItem
                            v-if="item.status === 'published'"
                            command="unpublish"
                          >
                            <Square class="mr-2 h-4 w-4" />
                            {{ $t('page-manager.unpublish') }}
                          </ElDropdownItem>
                          <ElDropdownItem
                            v-if="item.status === 'published'"
                            command="setHome"
                          >
                            <Home class="mr-2 h-4 w-4" />
                            {{ $t('page-manager.setAsHome') }}
                          </ElDropdownItem>
                        </ElDropdownMenu>
                      </template>
                    </ElDropdown>
                  </div>
                </div>
                <!-- code -->
                <div class="text-muted-foreground font-mono text-xs">
                  {{ item.code }}
                </div>
              </div>
            </div>
            <!-- 描述 -->
            <div
              class="text-muted-foreground mb-4 line-clamp-1 min-h-[18px] text-xs"
            >
              {{ item.description }}
            </div>
            <!-- 标签 -->
            <div class="mb-4 flex items-center justify-between">
              <div class="flex gap-1">
                <ElTag size="small" :type="getStatusType(item.status)">
                  {{ getStatusText(item.status) }}
                </ElTag>
              </div>
            </div>
            <!-- 应用名称 + 创建时间 -->
            <div class="flex items-center justify-between">
              <div class="text-muted-foreground flex gap-1 text-xs">
                <div v-if="item.application_name">
                  {{ item.application_name }}
                </div>
                <div v-else size="small" type="info">
                  {{ $t('common.mainApp') }}
                </div>
              </div>
              <span class="text-muted-foreground text-xs">
                {{ item.sys_create_datetime }}
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
              message: $t('page-manager.placeholder.name'),
              trigger: 'blur',
            },
          ],
          code: [
            {
              required: true,
              message: $t('page-manager.placeholder.code'),
              trigger: 'blur',
            },
            {
              pattern: /^[\w-]+$/,
              message: $t('page-manager.codeFormatError'),
              trigger: 'blur',
            },
          ],
        }"
      >
        <ElFormItem :label="$t('page-manager.name')" prop="name">
          <ElInput
            v-model="basicForm.name"
            :placeholder="$t('page-manager.placeholder.name')"
          />
        </ElFormItem>
        <ElFormItem :label="$t('page-manager.code')" prop="code">
          <ElInput
            v-model="basicForm.code"
            :placeholder="$t('page-manager.placeholder.code')"
            :disabled="isEditMode"
          />
        </ElFormItem>
        <ElFormItem :label="$t('page-manager.category')">
          <ElInput
            v-model="basicForm.category"
            :placeholder="$t('page-manager.placeholder.category')"
          />
        </ElFormItem>
        <ElFormItem :label="$t('common.sort')">
          <ElInput
            v-model.number="basicForm.sort"
            type="number"
            placeholder="0"
          />
        </ElFormItem>
        <ElFormItem :label="$t('page-manager.description')">
          <ElInput
            v-model="basicForm.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('page-manager.placeholder.description')"
          />
        </ElFormItem>
      </ElForm>
    </ZqDialog>

    <!-- 预览弹窗 -->
    <PreviewDialog v-model="showPreviewDialog" :page-id="previewingPageId" />

    <!-- 发布配置弹窗 -->
    <PublishDialog
      v-if="publishingPage"
      v-model="showPublishDialog"
      :page-id="publishingPage.id"
      :page-name="publishingPage.name"
      :page-code="publishingPage.code"
      @published="handlePublished"
    />

    <!-- 设为首页弹窗 -->
    <ZqDialog
      v-model="showSetHomeDialog"
      :title="$t('page-manager.setAsHomeTitle')"
      :confirm-loading="setHomeLoading"
      width="460px"
      @confirm="confirmSetHome"
    >
      <div class="space-y-3 px-2">
        <p class="text-sm">
          {{ $t('page-manager.setAsHomeConfirm', { name: setHomePage?.name }) }}
        </p>
        <div class="bg-secondary rounded p-3">
          <div class="text-muted-foreground text-xs">
            {{ $t('page-manager.setAsHomePath') }}
          </div>
          <div class="mt-1 font-mono text-sm">
            {{ setHomePage ? getSetHomePath(setHomePage) : '' }}
          </div>
        </div>
        <p
          v-if="setHomePage?.application_code"
          class="text-muted-foreground text-xs"
        >
          {{ $t('page-manager.setAsHomeAppTip', { app: setHomePage.application_name || setHomePage.application_code }) }}
        </p>
        <p class="text-muted-foreground text-xs">
          {{ $t('page-manager.setAsHomeTip') }}
        </p>
      </div>
    </ZqDialog>
  </div>
</template>
