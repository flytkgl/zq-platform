<script lang="ts" setup>
import type { FormInstance, FormRules } from 'element-plus';

import type { Message } from '#/api/core/message';

import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';

import {
  ExternalLink,
  Loader2,
  MailCheck,
  RotateCw,
  Send,
  Trash2,
} from '@vben/icons';
import { $t } from '@vben/locales';

import dayjs from 'dayjs';
import {
  ElBadge,
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElSelect,
  ElSkeleton,
  ElSkeletonItem,
  ElTag,
} from 'element-plus';

import {
  clearReadMessagesApi,
  deleteMessageApi,
  getMessageListApi,
  getUnreadCountApi,
  markAllAsReadApi,
  markAsReadApi,
  sendMessageApi,
} from '#/api/core/message';
import { FuPage } from '#/components/fu-page';
import { ZqDialog } from '#/components/zq-dialog';
import { UserSelector } from '#/components/zq-form/user-selector';

defineOptions({ name: 'MessageList' });

// ============ 消息类型映射 ============
type TagType = 'danger' | 'info' | 'primary' | 'success' | 'warning';
const typeMap: Record<string, { label: string; type: TagType }> = {
  system: { label: $t('message.typeMap.system'), type: 'info' },
  workflow: { label: $t('message.typeMap.workflow'), type: 'primary' },
  todo: { label: $t('message.typeMap.todo'), type: 'warning' },
  announcement: { label: $t('message.typeMap.announcement'), type: 'success' },
};

// ============ 列表相关 ============
const searchKeyword = ref('');
const statusFilter = ref('');
const list = ref<Message[]>([]);
const loading = ref(false);
const loadingMore = ref(false);
const refreshing = ref(false);
const pagination = ref({ current: 1, pageSize: 20, total: 0 });
const hasMore = computed(() => list.value.length < pagination.value.total);
const reachedEnd = ref(false);

// 列表根元素引用（用于查找滚动容器）
const listRootRef = ref<HTMLElement>();
let scrollEl: HTMLElement | null = null;

// 选中的消息
const selectedItem = ref<Message | null>(null);
const detailLoading = ref(false);

// 未读数量
const unreadCount = ref(0);

// ============ 发送消息 ============
const sendDialogVisible = ref(false);
const sendFormRef = ref<FormInstance>();
const sending = ref(false);
const sendForm = ref({
  recipient_ids: [] as string[],
  title: '',
  content: '',
  msg_type: 'system',
  channels: ['site'] as string[],
});

const sendFormRules = computed<FormRules>(() => ({
  recipient_ids: [
    {
      required: true,
      message: $t('message.send.recipientRequired'),
      trigger: 'change',
    },
  ],
  title: [
    {
      required: true,
      message: $t('message.send.titleRequired'),
      trigger: 'blur',
    },
  ],
  content: [
    {
      required: true,
      message: $t('message.send.contentRequired'),
      trigger: 'blur',
    },
  ],
}));

const channelOptions = computed(() => [
  { label: $t('message.send.channelSite'), value: 'site' },
  { label: $t('message.send.channelEmail'), value: 'email' },
  { label: $t('message.send.channelDingtalk'), value: 'dingtalk' },
  { label: $t('message.send.channelFeishu'), value: 'feishu' },
  { label: $t('message.send.channelWechat'), value: 'wechat' },
  { label: $t('message.send.channelWechatMp'), value: 'wechat_mp' },
]);

function openSendDialog() {
  sendForm.value = {
    recipient_ids: [],
    title: '',
    content: '',
    msg_type: 'system',
    channels: ['site'],
  };
  sendDialogVisible.value = true;
}

async function handleSend() {
  if (!sendFormRef.value) return;
  try {
    await sendFormRef.value.validate();
  } catch {
    return;
  }
  sending.value = true;
  try {
    await sendMessageApi(sendForm.value);
    ElMessage.success($t('message.send.success'));
    sendDialogVisible.value = false;
    await loadList();
  } catch (error) {
    console.error('发送消息失败:', error);
    ElMessage.error($t('message.send.failed'));
  } finally {
    sending.value = false;
  }
}

// ============ 数据加载 ============

async function loadUnreadCount() {
  try {
    const res = await getUnreadCountApi();
    unreadCount.value = res.total;
  } catch (error) {
    console.error('加载未读数量失败:', error);
  }
}

async function loadList() {
  list.value = [];
  loading.value = true;
  pagination.value.current = 1;
  reachedEnd.value = false;
  try {
    const res = await getMessageListApi({
      page: 1,
      pageSize: pagination.value.pageSize,
      status: statusFilter.value || undefined,
    });
    list.value = res.items || [];
    pagination.value.total = res.total || 0;

    if (list.value.length > 0 && !selectedItem.value) {
      handleSelect(list.value[0]!);
    }
  } catch (error: any) {
    console.error('加载列表失败:', error);
  } finally {
    loading.value = false;
  }
}

async function loadMore() {
  if (loadingMore.value || loading.value || !hasMore.value) return;
  loadingMore.value = true;
  const nextPage = pagination.value.current + 1;
  try {
    const res = await getMessageListApi({
      page: nextPage,
      pageSize: pagination.value.pageSize,
      status: statusFilter.value || undefined,
    });
    list.value = [...list.value, ...(res.items || [])];
    pagination.value.current = nextPage;
    pagination.value.total = res.total || 0;
    if (list.value.length >= pagination.value.total) {
      reachedEnd.value = true;
    }
  } catch (error: any) {
    console.error('加载更多失败:', error);
  } finally {
    loadingMore.value = false;
  }
}

// ============ 操作 ============

async function handleRefresh() {
  refreshing.value = true;
  await loadList();
  await loadUnreadCount();
  refreshing.value = false;
}

function handleSearch() {
  selectedItem.value = null;
  loadList();
}

async function handleSelect(item: Message) {
  selectedItem.value = item;
  detailLoading.value = true;

  if (item.status === 'unread') {
    try {
      await markAsReadApi(item.id);
      item.status = 'read';
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    } catch (error) {
      console.error('标记已读失败:', error);
    }
  }

  // 短暂延迟让骨架屏展示
  setTimeout(() => {
    detailLoading.value = false;
  }, 300);
}

async function handleMarkAllRead() {
  try {
    await ElMessageBox.confirm(
      $t('message.markAllReadConfirm'),
      $t('message.markAllReadConfirmTitle'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        type: 'warning',
      },
    );
    await markAllAsReadApi();
    ElMessage.success($t('message.markAllReadSuccess'));
    list.value.forEach((item) => {
      item.status = 'read';
    });
    unreadCount.value = 0;
  } catch {
    // 用户取消
  }
}

async function handleDelete(item: Message, event: Event) {
  event.stopPropagation();
  try {
    await ElMessageBox.confirm(
      $t('message.deleteConfirm'),
      $t('message.deleteConfirmTitle'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        type: 'warning',
      },
    );
    await deleteMessageApi(item.id);
    ElMessage.success($t('message.deleteSuccess'));
    if (selectedItem.value?.id === item.id) {
      selectedItem.value = null;
    }
    await loadList();
  } catch {
    // 用户取消
  }
}

async function handleClearRead() {
  try {
    await ElMessageBox.confirm(
      $t('message.clearReadConfirm'),
      $t('message.clearReadConfirmTitle'),
      {
        confirmButtonText: $t('common.confirm'),
        cancelButtonText: $t('common.cancel'),
        type: 'warning',
      },
    );
    await clearReadMessagesApi();
    ElMessage.success($t('message.clearReadSuccess'));
    selectedItem.value = null;
    await loadList();
  } catch {
    // 用户取消
  }
}

function formatTime(time: null | string | undefined) {
  if (!time) return '-';
  return dayjs(time).format('MM-DD HH:mm');
}

function handleGoToLink(message: Message) {
  if (!message.link_type || !message.link_id) return;

  // 根据 link_type 跳转到不同页面
  let url = '';
  if (message.link_type === 'workflow_task') {
    // 跳转到待办任务页面，带上任务ID
    url = `/app/workflow_center/workflow/pending?id=${message.link_id}`;
  } else if (message.link_type === 'workflow_instance') {
    // 跳转到我发起的页面，带上实例ID
    url = `/app/workflow_center/workflow/initiated?id=${message.link_id}`;
  }

  if (url) {
    window.open(url, '_blank');
  }
}

// ============ 滚动加载 ============

function handleScroll() {
  if (!scrollEl || loading.value || loadingMore.value || !hasMore.value) return;
  const { scrollTop, scrollHeight, clientHeight } = scrollEl;
  if (scrollHeight - scrollTop - clientHeight < 100) {
    loadMore();
  }
}

function initScrollListener() {
  let el: HTMLElement | null = listRootRef.value ?? null;
  while (el) {
    if (el.classList.contains('el-scrollbar__wrap')) {
      scrollEl = el;
      break;
    }
    el = el.parentElement;
  }
  scrollEl?.addEventListener('scroll', handleScroll);
}

function destroyScrollListener() {
  scrollEl?.removeEventListener('scroll', handleScroll);
  scrollEl = null;
}

onMounted(async () => {
  await Promise.all([loadList(), loadUnreadCount()]);
  await nextTick();
  initScrollListener();
});

onBeforeUnmount(() => {
  destroyScrollListener();
});
</script>

<template>
  <div>
    <FuPage
      left-width="320px"
      :left-min-width="280"
      :left-max-width="450"
      :left-padding="false"
      :right-padding="false"
    >
      <!-- 左侧头部 -->
      <template #left-header>
        <div class="flex w-full items-center justify-between gap-2 pt-3">
          <ElSelect
            v-model="statusFilter"
            :placeholder="$t('message.status')"
            clearable
            size="default"
            style="width: 85px"
            @change="handleSearch"
          >
            <ElOption value="" :label="$t('message.statusMap.all')" />
            <ElOption value="unread" :label="$t('message.statusMap.unread')" />
            <ElOption value="read" :label="$t('message.statusMap.read')" />
          </ElSelect>
          <div class="flex items-center gap-3">
            <Send
              class="h-4 w-4 shrink-0 cursor-pointer text-[var(--el-text-color-secondary)] transition-colors hover:text-[var(--el-color-primary)]"
              :title="$t('message.send.button')"
              @click="openSendDialog"
            />
            <RotateCw
              class="h-4 w-4 shrink-0 cursor-pointer text-[var(--el-text-color-secondary)] transition-colors hover:text-[var(--el-color-primary)]"
              :class="{ 'animate-spin': refreshing }"
              @click="handleRefresh"
            />
            <MailCheck
              class="h-4 w-4 shrink-0 cursor-pointer text-[var(--el-text-color-secondary)] transition-colors hover:text-[var(--el-color-primary)]"
              :class="{ 'pointer-events-none opacity-50': unreadCount === 0 }"
              :title="$t('message.markAllRead')"
              @click="handleMarkAllRead"
            />
            <Trash2
              class="h-4 w-4 shrink-0 cursor-pointer text-[var(--el-text-color-secondary)] transition-colors hover:text-[var(--el-color-danger)]"
              :title="$t('message.clearRead')"
              @click="handleClearRead"
            />
            <ElBadge
              v-if="unreadCount > 0"
              :value="unreadCount"
              :max="99"
              class="shrink-0"
            >
              <ElTag type="danger" size="small">
                {{ $t('message.statusMap.unread') }}
              </ElTag>
            </ElBadge>
          </div>
        </div>
      </template>

      <!-- 左侧列表 -->
      <template #left>
        <div ref="listRootRef" class="px-4">
          <!-- 骨架屏 -->
          <template v-if="loading && list.length === 0">
            <div
              v-for="i in 8"
              :key="i"
              class="mb-2 rounded-lg border border-transparent p-3"
            >
              <ElSkeleton :rows="0" animated>
                <template #template>
                  <div class="mb-2 flex items-center justify-between">
                    <ElSkeletonItem variant="text" style="width: 60%" />
                    <ElSkeletonItem
                      variant="text"
                      style="width: 50px; height: 14px"
                    />
                  </div>
                  <div class="flex items-center justify-between">
                    <ElSkeletonItem
                      variant="text"
                      style="width: 80px; height: 14px"
                    />
                    <ElSkeletonItem
                      variant="text"
                      style="width: 60px; height: 14px"
                    />
                  </div>
                </template>
              </ElSkeleton>
            </div>
          </template>

          <!-- 列表内容 -->
          <template v-else-if="list.length > 0">
            <div
              v-for="item in list"
              :key="item.id"
              class="mb-2 cursor-pointer rounded-[8px] p-3 transition-colors"
              :class="[
                selectedItem?.id === item.id
                  ? 'bg-primary/15 dark:bg-accent text-primary'
                  : 'hover:bg-[var(--el-fill-color-light)]',
              ]"
              @click="handleSelect(item)"
            >
              <!-- 标题行 -->
              <div class="mb-1 flex items-start justify-between gap-2 text-sm">
                <div class="flex flex-1 items-center gap-1.5 truncate">
                  <span
                    v-if="item.status === 'unread'"
                    class="h-2 w-2 shrink-0 rounded-full bg-[var(--el-color-danger)]"
                  ></span>
                  <span
                    class="truncate"
                    :class="{ 'font-medium': item.status === 'unread' }"
                    :title="item.title"
                  >
                    {{ item.title }}
                  </span>
                </div>
                <ElTag
                  :type="typeMap[item.msg_type]?.type || 'info'"
                  size="small"
                  class="shrink-0"
                >
                  {{ typeMap[item.msg_type]?.label || item.msg_type }}
                </ElTag>
              </div>
              <!-- 底部信息 -->
              <div class="mt-2 flex items-center justify-between">
                <span class="text-muted-foreground text-xs">
                  {{ item.sender_name || '-' }}
                </span>
                <span class="text-muted-foreground text-xs">
                  {{ formatTime(item.created_at) }}
                </span>
              </div>
            </div>

            <!-- 加载更多 / 没有更多 -->
            <div class="py-4 text-center">
              <div
                v-if="loadingMore"
                class="text-muted-foreground flex items-center justify-center gap-2 text-xs"
              >
                <Loader2 class="h-4 w-4 animate-spin" />
                {{ $t('message.loadingMore') }}
              </div>
              <span
                v-else-if="reachedEnd"
                class="text-muted-foreground text-xs"
              >
                {{ $t('message.noMore') }}
              </span>
            </div>
          </template>

          <!-- 空状态 -->
          <ElEmpty v-else :description="$t('message.emptyList')" />
        </div>
      </template>

      <!-- 右侧头部 -->
      <template #right-header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">
            {{ selectedItem?.title || $t('message.detailTitle') }}
          </span>
          <div
            v-if="selectedItem"
            class="flex items-center gap-2 text-xs text-[var(--el-text-color-secondary)]"
          >
            <ElTag
              :type="typeMap[selectedItem.msg_type]?.type || 'info'"
              size="small"
            >
              {{
                typeMap[selectedItem.msg_type]?.label || selectedItem.msg_type
              }}
            </ElTag>
            <span>{{ formatTime(selectedItem.created_at) }}</span>
            <ElButton
              link
              type="danger"
              size="small"
              @click="handleDelete(selectedItem, $event)"
            >
              <Trash2 class="h-3.5 w-3.5" />
            </ElButton>
          </div>
        </div>
      </template>

      <!-- 右侧内容 -->
      <template #right>
        <!-- 未选中 -->
        <div
          v-if="!selectedItem"
          class="flex h-full items-center justify-center"
        >
          <ElEmpty :description="$t('message.selectHint')" />
        </div>

        <!-- 骨架屏 -->
        <div v-else-if="detailLoading" class="p-5">
          <ElSkeleton :rows="0" animated>
            <template #template>
              <!-- 标题骨架 -->
              <ElSkeletonItem variant="h1" style="width: 45%; height: 22px" />
              <div class="mt-3 flex items-center gap-3">
                <ElSkeletonItem
                  variant="text"
                  style="width: 60px; height: 20px; border-radius: 4px"
                />
                <ElSkeletonItem
                  variant="text"
                  style="width: 100px; height: 14px"
                />
              </div>
              <!-- 正文骨架 -->
              <div class="mt-6 flex flex-col gap-3">
                <ElSkeletonItem
                  variant="text"
                  style="width: 100%; height: 14px"
                />
                <ElSkeletonItem
                  variant="text"
                  style="width: 95%; height: 14px"
                />
                <ElSkeletonItem
                  variant="text"
                  style="width: 88%; height: 14px"
                />
                <ElSkeletonItem
                  variant="text"
                  style="width: 100%; height: 14px"
                />
                <ElSkeletonItem
                  variant="text"
                  style="width: 72%; height: 14px"
                />
              </div>
              <!-- 图片占位 -->
              <ElSkeletonItem
                variant="image"
                style="
                  width: 100%;
                  height: 160px;
                  margin-top: 20px;
                  border-radius: 8px;
                "
              />
              <!-- 更多正文 -->
              <div class="mt-5 flex flex-col gap-3">
                <ElSkeletonItem
                  variant="text"
                  style="width: 100%; height: 14px"
                />
                <ElSkeletonItem
                  variant="text"
                  style="width: 90%; height: 14px"
                />
                <ElSkeletonItem
                  variant="text"
                  style="width: 82%; height: 14px"
                />
                <ElSkeletonItem
                  variant="text"
                  style="width: 55%; height: 14px"
                />
              </div>
            </template>
          </ElSkeleton>
        </div>

        <!-- 详情内容 -->
        <div v-else class="h-full overflow-y-auto p-5">
          <div
            class="message-content prose max-w-none text-sm leading-relaxed"
            v-html="selectedItem.content"
          ></div>

          <!-- 审批链接按钮 -->
          <div
            v-if="selectedItem.link_type && selectedItem.link_id"
            class="mt-6"
          >
            <ElButton type="text" @click="handleGoToLink(selectedItem)">
              <ExternalLink class="mr-1 h-4 w-4" />
              查看详情
            </ElButton>
          </div>
        </div>
      </template>
    </FuPage>

    <!-- 发送消息弹窗 -->
    <ZqDialog
      v-model="sendDialogVisible"
      :title="$t('message.send.title')"
      width="600px"
    >
      <ElForm
        ref="sendFormRef"
        :model="sendForm"
        :rules="sendFormRules"
        label-width="90px"
        label-position="left"
      >
        <ElFormItem :label="$t('message.send.recipient')" prop="recipient_ids">
          <UserSelector
            v-model="sendForm.recipient_ids"
            multiple
            :placeholder="$t('message.send.recipientPlaceholder')"
          />
        </ElFormItem>
        <ElFormItem :label="$t('message.send.msgTitle')" prop="title">
          <ElInput
            v-model="sendForm.title"
            :placeholder="$t('message.send.msgTitlePlaceholder')"
            maxlength="200"
            show-word-limit
          />
        </ElFormItem>
        <ElFormItem :label="$t('message.send.msgType')" prop="msg_type">
          <ElSelect v-model="sendForm.msg_type" style="width: 100%">
            <ElOption value="system" :label="$t('message.typeMap.system')" />
            <ElOption
              value="workflow"
              :label="$t('message.typeMap.workflow')"
            />
            <ElOption value="todo" :label="$t('message.typeMap.todo')" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem :label="$t('message.send.channels')" prop="channels">
          <ElCheckboxGroup v-model="sendForm.channels">
            <ElCheckbox
              v-for="ch in channelOptions"
              :key="ch.value"
              :label="ch.label"
              :value="ch.value"
            />
          </ElCheckboxGroup>
        </ElFormItem>
        <ElFormItem :label="$t('message.send.content')" prop="content">
          <ElInput
            v-model="sendForm.content"
            type="textarea"
            :rows="6"
            :placeholder="$t('message.send.contentPlaceholder')"
          />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="sendDialogVisible = false">
          {{ $t('common.cancel') }}
        </ElButton>
        <ElButton type="primary" :loading="sending" @click="handleSend">
          {{ $t('message.send.button') }}
        </ElButton>
      </template>
    </ZqDialog>
  </div>
</template>
