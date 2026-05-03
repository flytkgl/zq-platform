<script lang="ts" setup>
import type { Post } from '#/api/core/post';
import type { CardListOptions } from '#/components/card-list';

import { onMounted, ref } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElMessage,
  ElMessageBox,
  ElPopover,
  ElTooltip,
} from 'element-plus';

import { deletePostApi, getPostListApi } from '#/api/core/post';
import { CardList } from '#/components/card-list';

import PostFormModal from './post-form-modal.vue';

const emit = defineEmits<{
  select: [postId: string | undefined];
}>();

const postList = ref<Post[]>([]);
const loading = ref(false);
const selectedPostId = ref<string>();
const searchKeyword = ref<string>('');
const hoveredPostId = ref<string>();
const postFormModalRef = ref<InstanceType<typeof PostFormModal>>();

// 卡片列表配置
const cardListOptions: CardListOptions<Post> = {
  searchFields: [{ field: 'name' }, { field: 'code' }],
  titleField: 'name',
};

async function fetchPostList() {
  try {
    loading.value = true;
    const response = await getPostListApi({ page: 1, pageSize: 100 });
    postList.value = response.items || [];

    // 自动选中第一个岗位
    if (postList.value.length > 0 && !selectedPostId.value) {
      const firstPost = postList.value.at(0);
      if (firstPost) {
        selectedPostId.value = firstPost.id;
        emit('select', firstPost.id);
      }
    }
  } finally {
    loading.value = false;
  }
}

/**
 * 处理岗位选择
 */
function onPostSelect(postId: string | undefined) {
  selectedPostId.value = postId;
  emit('select', postId);
}

/**
 * 打开添加岗位对话框
 */
function onAddPost() {
  postFormModalRef.value?.open();
}

/**
 * 打开编辑岗位对话框
 */
function onEditPost(post: Post, e?: Event) {
  e?.stopPropagation();
  postFormModalRef.value?.open(post);
}

/**
 * 删除岗位
 */
async function onDeletePost(post: Post, e?: Event) {
  e?.stopPropagation();

  ElMessageBox.confirm(
    $t('ui.actionMessage.deleteConfirm', [post.name]),
    $t('common.delete'),
    {
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
      type: 'warning',
      showClose: false,
    },
  )
    .then(async () => {
      try {
        await deletePostApi(post.id);
        ElMessage.success($t('ui.actionMessage.deleteSuccess', [post.name]));

        // 如果删除的是当前选中的岗位，清除选中状态
        if (selectedPostId.value === post.id) {
          selectedPostId.value = undefined;
          emit('select', undefined);
        }

        await fetchPostList();
      } catch {
        ElMessage.error($t('ui.actionMessage.deleteError'));
      }
    })
    .catch(() => {
      // 用户取消了操作
    });
}

/**
 * 添加岗位成功后的回调
 */
async function onPostFormSuccess() {
  ElMessage.success($t('ui.actionMessage.createSuccess', [$t('post.name')]));
  await fetchPostList();
}

onMounted(() => {
  fetchPostList();
});
</script>

<template>
  <CardList
    :items="postList"
    :loading="loading"
    :selected-id="selectedPostId"
    :hovered-id="hoveredPostId"
    :search-keyword="searchKeyword"
    :options="cardListOptions"
    @select="onPostSelect"
    @update:search-keyword="(v) => (searchKeyword = v)"
    @update:hovered-id="(v) => (hoveredPostId = v)"
    @add="onAddPost"
    @edit="onEditPost"
    @delete="onDeletePost"
  >
    <!-- 自定义项目渲染 -->
    <template #item="{ item }">
      <div class="truncate text-sm" :title="item.name">
        {{ item.name }}
      </div>
    </template>

    <!-- 详细信息 -->
    <template #details="{ item }">
      <div class="flex items-center gap-2 text-xs opacity-70">
        <!-- 岗位编码 -->
        <span class="truncate" :title="item.code">
          {{ item.code }}
        </span>

        <!-- 分隔符 -->
        <span class="text-gray-400">|</span>

        <!-- 岗位类型 -->
        <span v-if="item.post_type_display" class="flex-shrink-0">
          {{ item.post_type_display }}
        </span>

        <!-- 部门 -->
        <span
          v-if="item.dept_name"
          class="flex-1 truncate"
          :title="item.dept_name"
        >
          {{ item.dept_name }}
        </span>
      </div>
    </template>

    <!-- 操作按钮 -->
    <template #actions="{ item }">
      <div class="flex flex-shrink-0" @click.stop>
        <!-- 编辑按钮 -->
        <ElTooltip :content="$t('post.edit')" placement="top">
          <ElButton
            type="primary"
            text
            size="small"
            circle
            @click="onEditPost(item, $event)"
          >
            <IconifyIcon icon="ep:edit" class="size-4" />
          </ElButton>
        </ElTooltip>

        <!-- 删除按钮 -->
        <ElButton
          type="danger"
          text
          size="small"
          circle
          style="margin-left: 0"
          :title="$t('common.delete')"
          @click="onDeletePost(item, $event)"
        >
          <IconifyIcon icon="ep:delete" class="size-4" />
        </ElButton>
        <!-- 详情按钮 -->
        <ElPopover placement="right" :width="300">
          <template #reference>
            <ElButton
              type="info"
              text
              size="small"
              style="margin-left: 0"
              circle
            >
              <IconifyIcon icon="ep:info-filled" class="size-4" />
            </ElButton>
          </template>
          <!-- Popover 内容：详细信息 -->
          <div class="space-y-2 p-3 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">岗位名称:</span>
              <span class="font-medium">{{ item.name || '-' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">岗位编码:</span>
              <span class="font-medium">{{ item.code || '-' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">岗位类型:</span>
              <span class="font-medium">{{
                item.post_type_display || '-'
              }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">岗位级别:</span>
              <span class="font-medium">{{
                item.post_level_display || '-'
              }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">所属部门:</span>
              <span class="font-medium">{{ item.dept_name || '-' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">状态:</span>
              <span class="font-medium">{{
                item.status ? '启用' : '禁用'
              }}</span>
            </div>
            <div
              v-if="item.description"
              class="border-t border-gray-200 pt-2 dark:border-gray-700"
            >
              <span class="text-gray-600 dark:text-gray-400">描述:</span>
              <div
                class="mt-1 max-h-32 overflow-y-auto break-words rounded bg-gray-100 p-2 text-xs dark:bg-gray-800"
              >
                {{ item.description }}
              </div>
            </div>
          </div>
        </ElPopover>
      </div>
    </template>

    <!-- Modal 组件 -->
    <template #modal>
      <PostFormModal ref="postFormModalRef" @success="onPostFormSuccess" />
    </template>
  </CardList>
</template>

<style scoped>
/* 输入框前置图标样式 */
:deep(.el-input__icon) {
  cursor: pointer;
}

/* 文本按钮样式 */
:deep(.el-button--text) {
  padding: 0 4px;
}

:deep(.el-popover__reference) {
  padding: 0;
}
</style>
