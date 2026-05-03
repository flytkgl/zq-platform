<script setup lang="ts">
import type { ApplicationListItem } from '#/api/core/application';

import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';
import {
  AppWindow,
  Copy,
  Edit,
  IconifyIcon,
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
  ElEmpty,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElPagination,
  ElTag,
  ElTooltip,
} from 'element-plus';

import {
  deleteApplicationApi,
  disableApplicationApi,
  getApplicationListApi,
  publishApplicationApi,
} from '#/api/core/application';
import ZqDialog from '#/components/zq-dialog/zq-dialog.vue';

import ApplicationFormModal from './modules/application-form-modal.vue';

defineOptions({ name: 'ApplicationList' });

// 搜索关键词
const searchKeyword = ref('');

// 应用列表
const applicationList = ref<ApplicationListItem[]>([]);

// 分页
const pagination = ref({
  current: 1,
  pageSize: 12,
  total: 0,
});

// 加载状态
const loading = ref(false);

// 弹窗状态
const showFormModal = ref(false);
const editingApp = ref<ApplicationListItem | null>(null);

// 发布/停用对话框状态
const showPublishDialog = ref(false);
const showDisableDialog = ref(false);
const currentApp = ref<ApplicationListItem | null>(null);
const appUrl = ref('');

// Element Plus Tag 类型
type TagType =
  | 'danger'
  | 'info'
  | 'primary'
  | 'success'
  | 'warning'
  | undefined;

// 应用类型映射
const appTypeMap: Record<string, { color: TagType; labelKey: string }> = {
  ai: { labelKey: 'application.appTypes.ai', color: 'info' },
  dashboard: { labelKey: 'application.appTypes.dashboard', color: 'success' },
  form: { labelKey: 'application.appTypes.form', color: 'primary' },
  mixed: { labelKey: 'application.appTypes.mixed', color: undefined },
  screen: { labelKey: 'application.appTypes.screen', color: 'danger' },
  workflow: { labelKey: 'application.appTypes.workflow', color: 'warning' },
};

// 状态映射
const statusMap: Record<string, { color: TagType; labelKey: string }> = {
  disabled: { labelKey: 'application.appStatus.disabled', color: 'danger' },
  draft: { labelKey: 'application.appStatus.draft', color: 'info' },
  published: { labelKey: 'application.appStatus.published', color: 'success' },
};

// 加载应用列表
const loadApplications = async () => {
  loading.value = true;
  try {
    const res = await getApplicationListApi({
      page: pagination.value.current,
      pageSize: pagination.value.pageSize,
      keyword: searchKeyword.value || undefined,
    });
    applicationList.value = res.items || [];
    pagination.value.total = res.total || 0;
  } catch (error) {
    console.error('Failed to load applications:', error);
    ElMessage.error($t('application.loadFailed'));
  } finally {
    loading.value = false;
  }
};

// 创建新应用
const handleCreate = () => {
  editingApp.value = null;
  showFormModal.value = true;
};

// 编辑应用
const handleEdit = (app: ApplicationListItem) => {
  editingApp.value = app;
  showFormModal.value = true;
};

// 进入应用（在新 tab 打开子应用）
const handleEnter = (app: ApplicationListItem) => {
  const subAppUrl = `${window.location.origin}/app/${app.code}`;
  window.open(subAppUrl, '_blank');
};

// 设置开发（跳转到表单管理）
const handleDevelop = (app: ApplicationListItem) => {
  const devUrl = `${window.location.origin}/app-dev/${app.code}/form-manager`;
  window.open(devUrl, '_blank');
};

// 发布应用
const handlePublish = (app: ApplicationListItem) => {
  currentApp.value = app;
  appUrl.value = `${window.location.origin}/app/${app.code}`;
  showPublishDialog.value = true;
};

// 确认发布
const confirmPublish = async () => {
  if (!currentApp.value) return;
  try {
    await publishApplicationApi(currentApp.value.id);
    const isReEnable = currentApp.value.status === 'disabled';
    ElMessage.success(
      isReEnable ? $t('application.enableSuccess') : $t('application.publishSuccess'),
    );
    showPublishDialog.value = false;
    loadApplications();
  } catch {
    const wasDisabled = currentApp.value?.status === 'disabled';
    ElMessage.error(
      wasDisabled ? $t('application.enableFailed') : $t('application.publishFailed'),
    );
  }
};

// 停用应用
const handleDisable = (app: ApplicationListItem) => {
  currentApp.value = app;
  appUrl.value = `${window.location.origin}/app/${app.code}`;
  showDisableDialog.value = true;
};

// 确认停用
const confirmDisable = async () => {
  if (!currentApp.value) return;
  try {
    await disableApplicationApi(currentApp.value.id);
    ElMessage.success($t('application.disableSuccess'));
    showDisableDialog.value = false;
    loadApplications();
  } catch {
    ElMessage.error($t('application.disableFailed'));
  }
};

// 删除应用
const handleDelete = async (app: ApplicationListItem) => {
  try {
    await ElMessageBox.confirm(
      $t('application.deleteConfirmMsg', { name: app.name }),
      $t('application.deleteConfirm'),
      {
        confirmButtonText: $t('application.confirm'),
        cancelButtonText: $t('application.cancel'),
        type: 'warning',
      },
    );
    await deleteApplicationApi(app.id);
    ElMessage.success($t('application.deleteSuccess'));
    loadApplications();
  } catch {
    // 取消操作
  }
};

// 搜索
const handleSearch = () => {
  pagination.value.current = 1;
  loadApplications();
};

// 分页变化
const handlePageChange = (page: number) => {
  pagination.value.current = page;
  loadApplications();
};

// 每页条数变化
const handleSizeChange = (size: number) => {
  pagination.value.pageSize = size;
  pagination.value.current = 1;
  loadApplications();
};

// 保存成功回调
const handleSaveSuccess = () => {
  loadApplications();
};

// 复制链接
const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(appUrl.value);
    ElMessage.success($t('application.copySuccess'));
  } catch {
    ElMessage.error($t('application.copyFailed'));
  }
};

onMounted(() => {
  loadApplications();
});
</script>

<template>
  <div class="application-list">
    <Page auto-content-height v-loading="loading">
      <template #title>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <ElButton type="primary" @click="handleCreate">
              <Plus class="mr-1 h-4 w-4" />
              {{ $t('application.createApp') }}
            </ElButton>
          </div>
          <div class="flex items-center gap-2">
            <ElInput
              v-model="searchKeyword"
              :placeholder="$t('application.searchPlaceholder')"
              class="!w-64"
              clearable
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            />
            <ElButton type="primary" @click="handleSearch">
              {{ $t('application.search') }}
            </ElButton>
          </div>
        </div>
      </template>

      <!-- 应用列表 -->
      <div
        v-if="applicationList.length > 0"
        class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5"
      >
        <ElCard
          v-for="app in applicationList"
          shadow="hover"
          :key="app.id"
          class="group application-card cursor-pointer transition-shadow"
          :body-style="{ padding: '0' }"
          style="border: none"
          @click="handleEnter(app)"
        >
          <div class="p-4">
            <!-- 头部：图标 + 右侧信息区 -->
            <div class="mb-4 flex gap-3">
              <div class="app-icon flex-shrink-0">
                <IconifyIcon
                  v-if="app.icon"
                  :icon="app.icon"
                  class="h-5 w-5 text-white"
                />
                <AppWindow v-else class="h-5 w-5 text-white" />
              </div>
              <div class="min-w-0 flex-1">
                <!-- name + 操作 -->
                <div class="flex items-center justify-between">
                  <div class="min-w-0 flex-1 whitespace-nowrap text-sm font-medium group-hover:truncate">
                    {{ app.name }}
                  </div>
                  <div
                    class="flex flex-shrink-0 items-center -space-x-1 opacity-0 transition-opacity group-hover:opacity-100"
                    @click.stop
                  >
                    <ElTooltip
                      :content="$t('application.develop')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleDevelop(app)">
                        <Settings class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip
                      :content="$t('application.edit')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleEdit(app)">
                        <Edit class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip
                      v-if="app.status === 'draft' || app.status === 'disabled'"
                      :content="
                        app.status === 'disabled'
                          ? $t('application.enable')
                          : $t('application.publish')
                      "
                      placement="top"
                    >
                      <ElButton text size="small" @click="handlePublish(app)">
                        <Play class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip
                      v-if="app.status === 'published'"
                      :content="$t('application.disable')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleDisable(app)">
                        <Square class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                    <ElTooltip
                      :content="$t('application.delete')"
                      placement="top"
                    >
                      <ElButton text size="small" @click="handleDelete(app)">
                        <Trash2 class="h-3.5 w-3.5" />
                      </ElButton>
                    </ElTooltip>
                  </div>
                </div>
                <!-- code -->
                <div class="text-muted-foreground font-mono text-xs">
                  {{ app.code }}
                </div>
              </div>
            </div>
            <!-- 描述 -->
            <div
              v-if="app.description"
              class="text-muted-foreground mb-4 line-clamp-1 text-xs"
            >
              {{ app.description }}
            </div>
            <!-- 第三行：标签 + 创建时间 -->
            <div class="flex items-center justify-between">
              <div class="flex gap-1">
                <ElTag size="small" :type="appTypeMap[app.app_type]?.color">
                  {{
                    appTypeMap[app.app_type]?.labelKey
                      ? $t(appTypeMap[app.app_type]!.labelKey)
                      : app.app_type
                  }}
                </ElTag>
                <ElTag
                  size="small"
                  :type="statusMap[app.status]?.color ?? 'info'"
                >
                  {{
                    statusMap[app.status]?.labelKey
                      ? $t(statusMap[app.status]!.labelKey)
                      : app.status
                  }}
                </ElTag>
              </div>
              <span class="text-muted-foreground text-xs">
                {{ app.sys_create_datetime }}
              </span>
            </div>
          </div>
        </ElCard>
      </div>

      <!-- 空状态 -->
      <ElEmpty v-else :description="$t('application.noApps')" />

      <!-- 分页 -->
      <template #footer>
        <div class="flex w-full items-center justify-end">
          <ElPagination
            v-model:current-page="pagination.current"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[12, 24, 36, 48]"
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

    <!-- 创建/编辑弹窗 -->
    <ApplicationFormModal
      v-model="showFormModal"
      :application="editingApp"
      @success="handleSaveSuccess"
    />

    <!-- 发布对话框 -->
    <ZqDialog
      v-model="showPublishDialog"
      :title="
        currentApp?.status === 'disabled'
          ? $t('application.enableApp')
          : $t('application.publishApp')
      "
      width="500px"
      :confirm-text="
        currentApp?.status === 'disabled'
          ? $t('application.confirmEnable')
          : $t('application.confirmPublish')
      "
      @confirm="confirmPublish"
      @cancel="showPublishDialog = false"
    >
      <div class="mx-4 space-y-4">
        <div>
          <p class="mb-2 text-sm">
            {{
              currentApp?.status === 'disabled'
                ? $t('application.enableConfirmMsg', {
                    name: currentApp?.name,
                  })
                : $t('application.publishConfirmMsg', {
                    name: currentApp?.name,
                  })
            }}
          </p>
          <p class="text-muted-foreground text-xs">
            {{
              currentApp?.status === 'disabled'
                ? $t('application.enableSuccessMsg')
                : $t('application.publishSuccessMsg')
            }}
          </p>
        </div>
        <div class="bg-secondary flex items-center justify-between rounded p-3">
          <span class="mr-2 flex-1 truncate text-sm">{{ appUrl }}</span>
          <ElButton text size="small" @click="copyLink">
            <Copy class="h-4 w-4" />
          </ElButton>
        </div>
      </div>
    </ZqDialog>

    <!-- 停用对话框 -->
    <ZqDialog
      v-model="showDisableDialog"
      :title="$t('application.disableApp')"
      width="500px"
      :confirm-text="$t('application.confirmDisable')"
      @confirm="confirmDisable"
      @cancel="showDisableDialog = false"
    >
      <div class="mx-4 space-y-4">
        <div>
          <p class="mb-2 text-sm">
            {{
              $t('application.disableConfirmMsg', { name: currentApp?.name })
            }}
          </p>
          <p class="text-muted-foreground text-xs">
            {{ $t('application.appLink') }}
          </p>
        </div>
        <div class="bg-secondary flex items-center justify-between rounded p-3">
          <span class="mr-2 flex-1 truncate text-sm">{{ appUrl }}</span>
          <ElButton text size="small" @click="copyLink">
            <Copy class="h-4 w-4" />
          </ElButton>
        </div>
      </div>
    </ZqDialog>
  </div>
</template>

<style scoped>
.application-card :deep(.el-card__body) {
  padding: 0;
}

.app-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(
    135deg,
    var(--el-color-primary-light-3),
    var(--el-color-primary)
  );
  border-radius: 8px;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
