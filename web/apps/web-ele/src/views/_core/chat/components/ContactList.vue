<script setup lang="ts">
import type { User } from '#/api/core/user';

import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import { Building2, Loader2, MessageSquare, Search } from '@vben/icons';
import { $t } from '@vben/locales';

import { ElEmpty, ElInput, ElScrollbar, ElSkeletonItem } from 'element-plus';

import { getUserListApi } from '#/api/core/user';
import UserAvatar from '#/components/user-avatar/index.vue';

const props = defineProps<{
  onlineUsers?: Set<string>;
}>();

const emit = defineEmits<{
  startChat: [user: User];
  viewOrg: [user: User];
}>();

const PAGE_SIZE = 50;

const loading = ref(false);
const loadingMore = ref(false);
const users = ref<User[]>([]);
const searchKeyword = ref('');
const currentPage = ref(1);
const hasMore = ref(true);
const scrollbarRef = ref<InstanceType<typeof ElScrollbar>>();

const filteredUsers = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase();
  if (!kw) return users.value;
  return users.value.filter((u) => {
    const name = (u.name || u.username || '').toLowerCase();
    const dept = (u.dept_name || '').toLowerCase();
    return name.includes(kw) || dept.includes(kw);
  });
});

// 按部门分组
const groupedUsers = computed(() => {
  const groups: Record<string, User[]> = {};
  for (const u of filteredUsers.value) {
    const dept = u.dept_name || $t('chat.noContacts');
    if (!groups[dept]) groups[dept] = [];
    groups[dept].push(u);
  }
  return groups;
});

async function loadUsers(page = 1) {
  if (page === 1) {
    loading.value = true;
  } else {
    loadingMore.value = true;
  }
  try {
    const res = await getUserListApi({
      page,
      pageSize: PAGE_SIZE,
      user_status: 1,
    });
    const items = res?.items || [];
    users.value = page === 1 ? items : [...users.value, ...items];
    currentPage.value = page;
    hasMore.value = items.length >= PAGE_SIZE;
  } catch (error) {
    console.error('加载联系人失败:', error);
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

function handleScroll() {
  const wrap = scrollbarRef.value?.$el?.querySelector('.el-scrollbar__wrap');
  if (!wrap) return;
  if (
    wrap.scrollHeight - wrap.scrollTop - wrap.clientHeight < 50 &&
    hasMore.value &&
    !loadingMore.value &&
    !loading.value &&
    !searchKeyword.value.trim()
  ) {
    loadUsers(currentPage.value + 1);
  }
}

// 搜索时重置
watch(searchKeyword, () => {
  // 搜索仅在已加载数据中过滤，不重新请求
});

onMounted(() => {
  loadUsers(1);
  document.addEventListener('click', onDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick);
});

// ---- 右键菜单 ----
const contextMenu = ref<{
  user: null | User;
  visible: boolean;
  x: number;
  y: number;
}>({
  visible: false,
  x: 0,
  y: 0,
  user: null,
});

function handleContextMenu(e: MouseEvent, user: User) {
  e.preventDefault();
  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    user,
  };
}

function closeContextMenu() {
  contextMenu.value.visible = false;
  contextMenu.value.user = null;
}

function onDocumentClick() {
  if (contextMenu.value.visible) {
    closeContextMenu();
  }
}
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 搜索 -->
    <div class="shrink-0 px-3 pb-2 pt-3">
      <ElInput
        v-model="searchKeyword"
        :placeholder="$t('chat.searchContacts')"
        clearable
        size="small"
      >
        <template #prefix>
          <Search class="h-3.5 w-3.5 text-[var(--el-text-color-placeholder)]" />
        </template>
      </ElInput>
    </div>

    <!-- 列表 -->
    <ElScrollbar ref="scrollbarRef" class="flex-1" @scroll="handleScroll">
      <!-- 骨架屏 -->
      <template v-if="loading">
        <div v-for="i in 8" :key="i" class="flex items-center gap-3 px-3 py-2">
          <ElSkeletonItem variant="circle" style="width: 36px; height: 36px" />
          <div class="flex-1">
            <ElSkeletonItem variant="text" style="width: 50%" />
            <ElSkeletonItem
              variant="text"
              style="width: 30%; margin-top: 4px"
            />
          </div>
        </div>
      </template>

      <!-- 空状态 -->
      <ElEmpty
        v-else-if="filteredUsers.length === 0"
        :description="$t('chat.noContacts')"
        :image-size="80"
        class="mt-10"
      />

      <!-- 按部门分组的联系人列表 -->
      <template v-else>
        <div
          v-for="(groupUsers, deptName) in groupedUsers"
          :key="deptName"
          class="mb-1"
        >
          <!-- 部门标题 -->
          <div class="sticky top-0 z-10 bg-[var(--el-bg-color)] px-3 py-1.5">
            <span
              class="text-xs font-medium text-[var(--el-text-color-secondary)]"
            >
              {{ deptName }} ({{ groupUsers.length }})
            </span>
          </div>

          <!-- 用户列表 -->
          <div
            v-for="user in groupUsers"
            :key="user.id"
            class="flex cursor-pointer items-center gap-3 px-3 py-2 transition-colors hover:bg-[var(--el-fill-color-light)]"
            @click="emit('startChat', user)"
            @contextmenu="handleContextMenu($event, user)"
          >
            <!-- 头像 -->
            <div class="relative shrink-0">
              <UserAvatar
                :user-id="user.id"
                :name="user.name || user.username"
                :avatar="user.avatar"
                :size="36"
                :font-size="14"
                :shadow="false"
                :show-popover="false"
              />
              <span
                class="absolute bottom-0 right-0 h-2 w-2 rounded-full border-[1.5px] border-[var(--el-bg-color)]"
                :class="
                  props.onlineUsers?.has(user.id)
                    ? 'bg-[var(--el-color-success)]'
                    : 'bg-[var(--el-text-color-placeholder)]'
                "
              ></span>
            </div>

            <!-- 信息 -->
            <div class="min-w-0 flex-1">
              <div class="truncate text-sm text-[var(--el-text-color-primary)]">
                {{ user.name || user.username }}
              </div>
              <div
                v-if="user.dept_name"
                class="mt-0.5 truncate text-xs text-[var(--el-text-color-placeholder)]"
              >
                {{ user.dept_name }}
              </div>
            </div>
          </div>
        </div>

        <!-- 加载更多提示 -->
        <div
          v-if="loadingMore"
          class="flex items-center justify-center gap-1 py-3 text-xs text-[var(--el-text-color-placeholder)]"
        >
          <Loader2 class="h-3 w-3 animate-spin" />
          {{ $t('chat.loading') }}
        </div>
        <div
          v-else-if="!hasMore && users.length > 0"
          class="py-3 text-center text-xs text-[var(--el-text-color-placeholder)]"
        >
          -- {{ $t('chat.noContacts') }} --
        </div>
      </template>
    </ElScrollbar>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <Transition name="ctx-menu">
        <div
          v-if="contextMenu.visible && contextMenu.user"
          class="contact-context-menu"
          :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }"
          @contextmenu.prevent
        >
          <div
            class="contact-context-menu-item"
            @click="
              emit('startChat', contextMenu.user!);
              closeContextMenu();
            "
          >
            <MessageSquare class="h-4 w-4" />
            <span>{{ $t('chat.startChat') }}</span>
          </div>
          <div
            class="contact-context-menu-item"
            @click="
              emit('viewOrg', contextMenu.user!);
              closeContextMenu();
            "
          >
            <Building2 class="h-4 w-4" />
            <span>{{ $t('chat.orgStructure') }}</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.contact-context-menu {
  position: fixed;
  z-index: 9999;
  min-width: 140px;
  padding: 4px 0;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  box-shadow: var(--el-box-shadow-light);
}

.contact-context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: background-color 0.15s;
}

.contact-context-menu-item:hover {
  background: var(--el-fill-color-light);
}

.ctx-menu-enter-active {
  transition: all 0.15s ease-out;
}

.ctx-menu-leave-active {
  transition: all 0.1s ease-in;
}

.ctx-menu-enter-from,
.ctx-menu-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
