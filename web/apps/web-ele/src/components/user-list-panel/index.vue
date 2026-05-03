<script lang="ts" setup>
import type { User } from '#/api/core/user';

import {
  computed,
  defineAsyncComponent,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue';

import { ElRefreshRight, IconifyIcon, Search } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElButtonGroup,
  ElCard,
  ElEmpty,
  ElInput,
  ElMessage,
  ElScrollbar,
  ElSkeleton,
  ElSkeletonItem,
  ElTag,
  ElTooltip,
} from 'element-plus';

import { getPostUsersApi } from '#/api/core/post';
import { getRoleUsersApi } from '#/api/core/role';
import { getUserListApi } from '#/api/core/user';

defineOptions({
  name: 'UserListPanel',
});
const props = withDefaults(defineProps<Props>(), {
  dataSource: 'all',
  sourceId: undefined,
  tempSelectedUsers: () => new Set(),
  filterable: true,
  multiple: false,
  selectable: true,
  title: '',
  showBorder: false,
  autoLoad: false,
  showSelectedTags: true,
});
const emit = defineEmits<{
  removeUser: [userId: string];
  'update:tempSelectedUsers': [value: Set<string>];
  userSelect: [userId: string, user: User];
}>();
// @ts-ignore
const UserCard = defineAsyncComponent(() => import('./user-card.vue'));
// @ts-ignore
const UserListItem = defineAsyncComponent(() => import('./user-list-item.vue'));

type DataSource = 'all' | 'dept' | 'post' | 'role';

interface Props {
  dataSource?: DataSource; // 数据源类型：all-所有用户, dept-部门用户, post-岗位用户, role-角色用户
  sourceId?: string; // 数据源ID（部门ID或岗位ID）
  tempSelectedUsers?: Set<string>;
  filterable?: boolean;
  multiple?: boolean;
  selectable?: boolean;
  title?: string;
  showBorder?: boolean;
  autoLoad?: boolean; // 是否自动加载
  showSelectedTags?: boolean; // 是否显示已选中的标签
}

// 内部状态
const users = ref<User[]>([]);
const searchText = ref('');
const userLoading = ref(false);
const isLoadingMore = ref(false);
const currentPage = ref(1);
const pageSize = ref(60);
const totalUsers = ref(0);
const hasLoadedMore = ref(false);
const viewMode = ref<'grid' | 'list'>('grid'); // 视图模式：grid-方块，list-列表

// 是否还有更多数据
const hasMoreData = computed(() => {
  const totalLoaded = currentPage.value * pageSize.value;
  return totalLoaded < totalUsers.value;
});

/**
 * 加载用户列表
 */
async function loadUsers(isLoadMore = false) {
  if (isLoadMore) {
    isLoadingMore.value = true;
  } else {
    userLoading.value = true;
  }

  try {
    let result;
    const params: any = {
      page: currentPage.value,
      pageSize: pageSize.value,
      name: searchText.value || undefined,
    };

    // 根据数据源类型调用不同的API
    if (props.dataSource === 'dept' && props.sourceId) {
      // 使用 getUserListApi 并传入 dept_ids
      params.dept_ids = [props.sourceId];
      result = await getUserListApi(params);
    } else if (props.dataSource === 'post' && props.sourceId) {
      params.search = params.name;
      delete params.name;
      result = await getPostUsersApi(props.sourceId, params);
    } else if (props.dataSource === 'role' && props.sourceId) {
      params.username = params.name;
      delete params.name;
      result = await getRoleUsersApi(props.sourceId, params);
    } else {
      // 默认加载所有用户
      result = await getUserListApi(params);
    }

    if (result) {
      users.value =
        currentPage.value === 1
          ? result.items || []
          : [...users.value, ...(result.items || [])];
      totalUsers.value = result.total || 0;
    }
  } catch (error) {
    console.error('Failed to load users:', error);
    ElMessage.error($t('system.user.loadFailed'));
    if (currentPage.value === 1) {
      users.value = [];
    }
    totalUsers.value = 0;
  } finally {
    if (isLoadMore) {
      isLoadingMore.value = false;
    } else {
      userLoading.value = false;
    }
  }
}

/**
 * 重置并重新加载
 */
function reload() {
  currentPage.value = 1;
  hasLoadedMore.value = false;
  loadUsers();
}

// 获取临时选择用户的完整信息
const tempSelectedUsersList = computed(() => {
  const userMap = new Map();
  users.value.forEach((user) => {
    userMap.set(user.id, user);
  });

  const result = [];
  const seenIds = new Set<string>();

  for (const userId of props.tempSelectedUsers) {
    if (seenIds.has(userId)) continue;

    const user = userMap.get(userId);
    if (user) {
      seenIds.add(userId);
      result.push({
        id: user.id,
        display: `${user.name}/${user.username}`,
      });
    }
  }
  return result;
});

// 处理搜索文本更新
const handleSearchUpdate = (value: string) => {
  searchText.value = value;
};

// 处理用户选择
const handleUserSelect = (userId: string) => {
  if (!props.selectable) {
    return;
  }
  // 查找完整的用户对象
  const user = users.value.find((u) => u.id === userId);
  if (user) {
    emit('userSelect', userId, user);
  }
};

// 处理移除用户
const handleRemoveUser = (userId: string) => {
  emit('removeUser', userId);
};

// 处理滚动到底部
const handleScrollToBottom = async () => {
  if (isLoadingMore.value || !hasMoreData.value || userLoading.value) {
    return;
  }

  hasLoadedMore.value = true;
  currentPage.value += 1;
  await loadUsers(true);
};

// 监听搜索文本变化
watch(searchText, () => {
  currentPage.value = 1;
  hasLoadedMore.value = false;
  loadUsers();
});

// 监听数据源变化
watch(
  () => [props.dataSource, props.sourceId],
  () => {
    reload();
  },
);

// 初始化加载
onMounted(() => {
  if (props.autoLoad) {
    userLoading.value = true;
    loadUsers();
  }
});

onBeforeUnmount(() => {
  userLoading.value = false;
});

// 暴露方法给父组件
defineExpose({
  reload,
  loadUsers,
});
</script>

<template>
  <ElCard
    class="h-full"
    :class="{ 'border-none': !showBorder }"
    shadow="never"
    :body-style="{
      display: 'flex',
      flexDirection: 'column',
      flex: 1,
      padding: '12px',
      overflow: 'hidden',
      minHeight: 0,
    }"
  >
    <!-- 头部：标题/已选用户 + 搜索框 -->
    <template #header>
      <div class="flex flex-shrink-0 flex-row items-start gap-3">
        <!-- 标题或已选用户 -->
        <div class="flex min-h-[32px] min-w-0 flex-1 items-center">
          <!-- 不可选时显示标题 -->
          <div
            v-if="!selectable && title"
            class="text-base font-medium text-[var(--el-text-color-primary)]"
          >
            {{ title }}
          </div>
          <!-- 可选时显示已选用户标签 -->
          <template v-else-if="selectable">
            <div>
              <slot name="title"> </slot>
            </div>

            <div
              v-if="showSelectedTags && tempSelectedUsersList.length > 0"
              class="ml-2.5 flex w-full flex-wrap gap-2"
            >
              <ElTag
                v-for="item of tempSelectedUsersList"
                :key="item.id"
                closable
                type="info"
                @close="handleRemoveUser(item.id)"
              >
                {{ item.display }}
              </ElTag>
            </div>
            <span
              v-else-if="showSelectedTags && tempSelectedUsersList.length === 0"
              class="text-sm text-[var(--el-text-color-placeholder)]"
            ></span>
          </template>
        </div>

        <!-- 搜索框和视图切换 -->
        <div v-if="filterable" class="flex flex-shrink-0 items-center gap-2">
          <ElInput
            :model-value="searchText"
            :placeholder="$t('common.ui.placeholder.search') || 'Search'"
            clearable
            :prefix-icon="Search"
            class="w-60"
            @update:model-value="handleSearchUpdate"
          >
            <template #suffix>
              <span>{{ totalUsers }}</span>
            </template>
          </ElInput>

          <!-- 视图模式切换按钮 -->
          <ElButtonGroup class="flex-shrink-0">
            <ElTooltip content="方块视图" placement="bottom">
              <ElButton
                :type="viewMode === 'grid' ? 'primary' : 'default'"
                @click="viewMode = 'grid'"
              >
                <IconifyIcon icon="lucide:layout-grid" class="h-4 w-4" />
              </ElButton>
            </ElTooltip>
            <ElTooltip content="列表视图" placement="bottom">
              <ElButton
                :type="viewMode === 'list' ? 'primary' : 'default'"
                @click="viewMode = 'list'"
              >
                <IconifyIcon icon="lucide:list" class="h-4 w-4" />
              </ElButton>
            </ElTooltip>
          </ElButtonGroup>

          <!-- 刷新按钮 -->
          <ElTooltip content="刷新" placement="bottom">
            <ElButton circle @click="reload">
              <ElRefreshRight
                class="h-4 w-4"
                :class="{ 'animate-spin': userLoading }"
              />
            </ElButton>
          </ElTooltip>
        </div>
      </div>
    </template>

    <!-- 用户卡片网格 -->
    <ElScrollbar
      class="min-h-0 flex-1 overflow-hidden"
      :distance="60"
      @end-reached="handleScrollToBottom"
    >
      <div class="p-2.5 pb-16">
        <ElSkeleton :loading="userLoading" animated :count="1">
          <template #template>
            <div
              class="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-2.5"
            >
              <div
                v-for="i in 60"
                :key="i"
                class="flex flex-col items-center rounded-lg border border-[var(--el-border-color-lighter)] bg-[var(--el-fill-color-blank)] p-2.5"
              >
                <ElSkeletonItem
                  variant="circle"
                  style="width: 56px; height: 56px"
                />
                <ElSkeletonItem
                  variant="text"
                  style="width: 80%; height: 14px; margin-top: 12px"
                />
                <ElSkeletonItem
                  variant="text"
                  style="width: 60%; height: 12px; margin-top: 8px"
                />
              </div>
            </div>
          </template>
          <template #default>
            <div class="flex min-h-full flex-col">
              <ElEmpty
                v-if="users.length === 0"
                :description="$t('common.noData') || 'No Data'"
              />
              <!-- 方块视图 -->
              <div
                v-else-if="viewMode === 'grid'"
                class="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-2.5"
              >
                <UserCard
                  v-for="user in users"
                  :key="user.id"
                  :user="user"
                  :selected="selectable && tempSelectedUsers.has(user.id)"
                  :multiple="selectable && multiple"
                  @select="handleUserSelect"
                />
              </div>
              <!-- 列表视图 -->
              <div v-else class="flex flex-col gap-2">
                <UserListItem
                  v-for="user in users"
                  :key="user.id"
                  :user="user"
                  :selected="selectable && tempSelectedUsers.has(user.id)"
                  :multiple="selectable && multiple"
                  @select="handleUserSelect"
                />
              </div>

              <!-- 底部加载提示 -->
              <div
                v-if="isLoadingMore"
                class="flex items-center justify-center gap-2 py-5"
              >
                <div
                  class="h-4 w-4 animate-spin rounded-full border-2 border-[var(--el-color-primary)] border-t-transparent"
                ></div>
                <span class="text-sm text-[var(--el-text-color-secondary)]"
                  >正在加载，请稍后...</span
                >
              </div>

              <!-- 无更多数据提示 - 只在已经加载过更多数据时显示 -->
              <div
                v-else-if="users.length > 0 && !hasMoreData && hasLoadedMore"
                class="py-5 text-center text-sm text-[var(--el-text-color-secondary)]"
              >
                {{ $t('common.noMore') || 'No more data' }}
              </div>
            </div>
          </template>
        </ElSkeleton>
      </div>
    </ElScrollbar>
  </ElCard>
</template>

<style scoped>
/* 保留必要的 deep 样式用于修改 Element Plus 组件 */
:deep(.el-card__body) {
  height: 100%;
}

.border-none {
  border: none;
}
</style>
