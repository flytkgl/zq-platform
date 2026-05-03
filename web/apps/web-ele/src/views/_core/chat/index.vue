<script setup lang="ts">
import type { ChatMessage, Conversation } from '#/api/core/chat';
import type { User } from '#/api/core/user';

import { computed, nextTick, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import {
  CirclePlus,
  Contact,
  MessageSquare,
  PanelRight,
  Users,
} from '@vben/icons';
import { $t } from '@vben/locales';
import { useUserStore } from '@vben/stores';

import {
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElMessage,
  ElMessageBox,
} from 'element-plus';

import {
  addMembersApi,
  deleteConversationApi,
  removeMemberApi,
} from '#/api/core/chat';
import { UserAvatar } from '#/components/user-avatar';

import AddMemberDialog from './components/AddMemberDialog.vue';
import ChatInput from './components/ChatInput.vue';
import ContactDetail from './components/ContactDetail.vue';
import ContactList from './components/ContactList.vue';
import ConversationInfo from './components/ConversationInfo.vue';
import ConversationList from './components/ConversationList.vue';
import CreateGroupDialog from './components/CreateGroupDialog.vue';
import MessageList from './components/MessageList.vue';
import { useChat } from './composables/useChat';

const {
  conversations,
  currentConversation,
  messages,
  members,
  hasMoreMessages,
  loadingConversations,
  loadingMessages,
  loadingMembers,
  sending,
  typingUsers,
  pendingConversationId,
  connectChat,
  loadConversations,
  selectConversation,
  loadMessages,
  loadMembers,
  sendMessage,
  sendTyping,
  recallMessage,
  createPrivateChat,
  createGroupChat,
  togglePin,
  toggleMute,
  onlineUsers,
  loadOnlineUsers,
} = useChat();

const router = useRouter();
const userStore = useUserStore();

// 左侧菜单 Tab: chats / contacts
const activeTab = ref<'chats' | 'contacts'>('chats');
const showInfo = ref(false);
const selectedContactId = ref<string>();
const showCreateGroup = ref(false);
const showAddMember = ref(false);
const messageListRef = ref<InstanceType<typeof MessageList>>();
const replyTo = ref<ChatMessage | null>(null);

const typingText = computed(() => {
  if (typingUsers.value.size === 0) return '';
  const names = [...typingUsers.value.values()];
  if (names.length === 1) return `${names[0]} ${$t('chat.typing')}`;
  return `${names.length} ${$t('chat.typing')}`;
});

const conversationTitle = computed(() => {
  const conv = currentConversation.value;
  if (!conv) return '';
  if (conv.type === 'private') return conv.peer_user_name || $t('chat.private');
  return conv.name || $t('chat.group');
});

// 未读消息总数
const totalUnread = computed(() => {
  return conversations.value.reduce((sum, c) => sum + (c.unread_count || 0), 0);
});

const route = useRoute();

onMounted(async () => {
  // noBasicLayout 模式下 basic.vue 不会挂载，需要在此建立 Chat WebSocket
  connectChat();
  // 加载在线用户状态
  loadOnlineUsers();
  // 会话列表已在 BasicLayout 全局加载，但进入聊天页时刷新一下
  await loadConversations();

  // 优先从 URL query 参数获取会话ID
  const queryConversationId = route.query.conversationId as string | undefined;
  const targetConversationId =
    queryConversationId || pendingConversationId.value;

  // 如果有待跳转的会话（从通知点击进入），自动选中
  if (targetConversationId) {
    const conv = conversations.value.find((c) => c.id === targetConversationId);
    if (conv) {
      await handleSelectConversation(conv);
    }
    pendingConversationId.value = null;
  }
});

async function handleSend(
  content: string,
  msgType: string,
  fileId?: string,
  fileName?: string,
  localUrl?: string,
  extra?: Record<string, any>,
) {
  try {
    await sendMessage(
      content,
      msgType,
      fileId,
      replyTo.value?.id,
      fileName,
      localUrl,
      extra,
    );
    replyTo.value = null;
  } catch {
    ElMessage.error($t('chat.recallFailed'));
  }
}

async function handleRecall(messageId: string) {
  try {
    await recallMessage(messageId);
    ElMessage.success($t('chat.recallSuccess'));
  } catch {
    ElMessage.error($t('chat.recallFailed'));
  }
}

function handleReply(msg: ChatMessage) {
  replyTo.value = msg;
}

async function handleSelectConversation(conv: Conversation) {
  await selectConversation(conv);
  // 双重确保滚到底部：nextTick 处理 DOM 更新，setTimeout 处理虚拟列表延迟渲染
  nextTick(() => {
    messageListRef.value?.scrollToBottom(false);
  });
  setTimeout(() => {
    messageListRef.value?.scrollToBottom(false);
  }, 100);
}

function handleSelectContact(user: User) {
  selectedContactId.value = user.id;
}

async function handleStartChat(user: User) {
  activeTab.value = 'chats';
  selectedContactId.value = undefined;
  try {
    await createPrivateChat(user.id);
  } catch (error) {
    console.error('发起聊天失败:', error);
  }
}

async function handleCreateGroup(name: string, memberIds: string[]) {
  try {
    await createGroupChat(name, memberIds);
    ElMessage.success($t('chat.createGroupSuccess'));
  } catch (error) {
    console.error('创建群聊失败:', error);
  }
}

async function handleTogglePin(value: boolean) {
  if (!currentConversation.value) return;
  await togglePin(currentConversation.value.id, value);
}

async function handleToggleMute(value: boolean) {
  if (!currentConversation.value) return;
  await toggleMute(currentConversation.value.id, value);
}

function handleAddMember() {
  showAddMember.value = true;
}

async function handleAddMemberConfirm(memberIds: string[]) {
  if (!currentConversation.value) return;
  try {
    await addMembersApi(currentConversation.value.id, memberIds);
    await loadMembers();
    ElMessage.success($t('chat.addMemberSuccess'));
  } catch (error) {
    console.error('添加成员失败:', error);
  }
}

async function handleRemoveMember(userId: string) {
  if (!currentConversation.value) return;
  try {
    await removeMemberApi(currentConversation.value.id, userId);
    await loadMembers();
  } catch (error) {
    console.error('移除成员失败:', error);
  }
}

async function handleDissolve() {
  if (!currentConversation.value) return;
  try {
    await deleteConversationApi(currentConversation.value.id);
    ElMessage.success($t('chat.dissolveSuccess'));
    currentConversation.value = null;
    await loadConversations();
  } catch (error) {
    console.error('解散群聊失败:', error);
  }
}

// ---- 会话列表右键菜单处理 ----
async function handleConvTogglePin(conv: Conversation, value: boolean) {
  await togglePin(conv.id, value);
}

async function handleConvToggleMute(conv: Conversation, value: boolean) {
  await toggleMute(conv.id, value);
}

function handleConvMarkUnread(conv: Conversation) {
  const target = conversations.value.find((c) => c.id === conv.id);
  if (target && target.unread_count === 0) {
    target.unread_count = 1;
  }
}

async function handleConvDelete(conv: Conversation) {
  try {
    await ElMessageBox.confirm($t('chat.deleteConversationConfirm'), {
      type: 'warning',
      confirmButtonText: $t('common.confirm'),
      cancelButtonText: $t('common.cancel'),
    });
    if (conv.type === 'group') {
      await deleteConversationApi(conv.id);
    }
    // 单聊：前端移除（后端无删除单聊 API）
    conversations.value = conversations.value.filter((c) => c.id !== conv.id);
    if (currentConversation.value?.id === conv.id) {
      currentConversation.value = null;
    }
    ElMessage.success($t('chat.deleteSuccess'));
  } catch {
    // cancelled
  }
}

function handleViewOrg(user: User) {
  router.push({ path: '/dept', query: { userId: user.id } });
}
</script>

<template>
  <div class="bg-background-deep h-full py-4 pr-4">
    <div class="chat-container flex h-full overflow-hidden">
      <!-- 第1栏：左侧窄菜单栏 -->
      <div
        class="flex w-[68px] shrink-0 flex-col items-center bg-[var(--el-bg-color-page)] py-4"
      >
        <!-- 当前用户头像 -->
        <UserAvatar
          :user-id="userStore.userInfo?.userId"
          :name="userStore.userInfo?.realName || userStore.userInfo?.username"
          :avatar="userStore.userInfo?.avatar"
          :size="40"
          :font-size="14"
          :shadow="false"
          class="mb-4"
        />

        <!-- 菜单图标 -->
        <!-- <ElTooltip :content="$t('chat.recentChats')" placement="right"> -->
        <div
          class="chat-nav-item"
          :class="{ 'chat-nav-item--active': activeTab === 'chats' }"
          @click="activeTab = 'chats'"
        >
          <MessageSquare class="h-6 w-6" />
          <!-- 未读徽标 -->
          <span
            v-if="totalUnread > 0"
            class="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--el-color-danger)] px-1 text-[10px] font-medium text-white"
          >
            {{ totalUnread > 99 ? '99+' : totalUnread }}
          </span>
        </div>
        <!-- </ElTooltip> -->

        <!-- <ElTooltip :content="$t('chat.contacts')" placement="right"> -->
        <div
          class="chat-nav-item"
          :class="{ 'chat-nav-item--active': activeTab === 'contacts' }"
          @click="activeTab = 'contacts'"
        >
          <Contact class="h-6 w-6" />
        </div>
        <!-- </ElTooltip> -->

        <!-- 底部操作 -->
        <div class="mt-auto flex flex-col items-center gap-2">
          <ElDropdown trigger="click" placement="right-start">
            <div class="chat-nav-item">
              <CirclePlus class="h-5 w-5" />
            </div>
            <template #dropdown>
              <ElDropdownMenu>
                <ElDropdownItem @click="showCreateGroup = true">
                  <Users class="mr-2 h-4 w-4" />
                  {{ $t('chat.newGroup') }}
                </ElDropdownItem>
              </ElDropdownMenu>
            </template>
          </ElDropdown>
        </div>
      </div>

      <!-- 第2栏：会话列表 / 联系人列表 -->
      <div
        class="bg-background mr-3 flex w-[260px] shrink-0 flex-col rounded-[8px] pt-1"
      >
        <!-- 标题栏 -->
        <!-- <div class="flex shrink-0 items-center justify-between border-b border-[var(--el-border-color-lighter)] px-3 py-2.5">
          <span class="text-sm font-medium text-[var(--el-text-color-primary)]">
            {{ activeTab === 'chats' ? $t('chat.recentChats') : $t('chat.contacts') }}
          </span>
        </div> -->

        <!-- 会话列表 -->
        <ConversationList
          v-show="activeTab === 'chats'"
          :conversations="conversations"
          :current-id="currentConversation?.id"
          :loading="loadingConversations"
          :online-users="onlineUsers"
          @select="handleSelectConversation"
          @toggle-pin="handleConvTogglePin"
          @toggle-mute="handleConvToggleMute"
          @mark-unread="handleConvMarkUnread"
          @delete="handleConvDelete"
        />

        <!-- 联系人列表 -->
        <ContactList
          v-show="activeTab === 'contacts'"
          :online-users="onlineUsers"
          @start-chat="handleSelectContact"
          @view-org="handleViewOrg"
        />
      </div>

      <!-- 第3栏：聊天区域 / 联系人详情 -->
      <div class="bg-background flex min-w-0 flex-1 flex-col rounded-[8px]">
        <!-- 联系人 Tab：显示联系人详情 -->
        <template v-if="activeTab === 'contacts'">
          <template v-if="selectedContactId">
            <ContactDetail
              :user-id="selectedContactId"
              :online-users="onlineUsers"
              @start-chat="handleStartChat"
            />
          </template>
          <div v-else class="flex h-full items-center justify-center">
            <ElEmpty
              :description="$t('chat.selectContactHint')"
              :image-size="120"
            >
              <template #image>
                <Contact
                  class="h-16 w-16 text-[var(--el-text-color-placeholder)]"
                />
              </template>
            </ElEmpty>
          </div>
        </template>

        <!-- 聊天 Tab：显示聊天窗口 -->
        <template v-else>
          <template v-if="currentConversation">
            <!-- 聊天头部 -->
            <div
              class="flex min-h-[45px] shrink-0 items-center justify-between border-b border-[var(--el-border-color-lighter)] px-4 py-2.5"
            >
              <div class="flex items-center gap-2">
                <span
                  class="text-sm font-medium text-[var(--el-text-color-primary)]"
                >
                  {{ conversationTitle }}
                </span>
                <span
                  v-if="
                    currentConversation.type === 'private' &&
                    currentConversation.peer_user_id
                  "
                  class="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[11px] leading-none"
                  :class="
                    onlineUsers.has(currentConversation.peer_user_id)
                      ? 'bg-[var(--el-color-success-light-9)] text-[var(--el-color-success)]'
                      : 'bg-[var(--el-fill-color)] text-[var(--el-text-color-placeholder)]'
                  "
                >
                  <span
                    class="inline-block h-1.5 w-1.5 rounded-full"
                    :class="
                      onlineUsers.has(currentConversation.peer_user_id)
                        ? 'bg-[var(--el-color-success)]'
                        : 'bg-[var(--el-text-color-placeholder)]'
                    "
                  ></span>
                  {{
                    onlineUsers.has(currentConversation.peer_user_id)
                      ? $t('chat.online')
                      : $t('chat.offline')
                  }}
                </span>
                <span
                  v-if="currentConversation.type === 'group'"
                  class="text-xs text-[var(--el-text-color-placeholder)]"
                >
                  ({{ currentConversation.member_count }})
                </span>
              </div>
              <div class="flex items-center gap-2">
                <!-- <ElDropdown trigger="click">
                  <MoreVertical class="h-4 w-4 cursor-pointer text-[var(--el-text-color-secondary)] transition-colors hover:text-[var(--el-color-primary)]" />
                  <template #dropdown>
                    <ElDropdownMenu>
                      <ElDropdownItem @click="showInfo = !showInfo">
                        {{ $t('chat.conversationInfo') }}
                      </ElDropdownItem>
                    </ElDropdownMenu>
                  </template>
                </ElDropdown> -->
                <PanelRight
                  class="h-4 w-4 cursor-pointer text-[var(--el-text-color-secondary)] transition-colors hover:text-[var(--el-color-primary)]"
                  :class="{ 'text-[var(--el-color-primary)]': showInfo }"
                  @click="showInfo = !showInfo"
                />
              </div>
            </div>

            <!-- 消息列表 -->
            <MessageList
              :key="currentConversation?.id || 'empty'"
              ref="messageListRef"
              :messages="messages"
              :has-more="hasMoreMessages"
              :loading="loadingMessages"
              :typing-text="typingText"
              @load-more="loadMessages(true)"
              @recall="handleRecall"
              @reply="handleReply"
            />

            <!-- 输入框 -->
            <ChatInput
              :sending="sending"
              :reply-to="replyTo"
              @send="handleSend"
              @typing="sendTyping"
              @cancel-reply="replyTo = null"
            />
          </template>

          <!-- 未选择会话 -->
          <div v-else class="flex h-full items-center justify-center">
            <ElEmpty :description="$t('chat.selectHint')" :image-size="120">
              <template #image>
                <MessageSquare
                  class="h-16 w-16 text-[var(--el-text-color-placeholder)]"
                />
              </template>
            </ElEmpty>
          </div>
        </template>
      </div>

      <!-- 第4栏：会话信息面板（仅聊天 Tab 时显示） -->
      <transition name="slide-right">
        <div
          v-if="showInfo && currentConversation && activeTab === 'chats'"
          class="bg-background ml-3 w-[260px] shrink-0 rounded-[8px]"
        >
          <ConversationInfo
            :conversation="currentConversation"
            :members="members"
            :online-users="onlineUsers"
            :loading="loadingMembers"
            @toggle-pin="handleTogglePin"
            @toggle-mute="handleToggleMute"
            @add-member="handleAddMember"
            @remove-member="handleRemoveMember"
            @dissolve="handleDissolve"
          />
        </div>
      </transition>
    </div>

    <!-- 建群弹窗 -->
    <CreateGroupDialog v-model="showCreateGroup" @confirm="handleCreateGroup" />

    <!-- 添加成员弹窗 -->
    <AddMemberDialog
      v-model="showAddMember"
      :existing-member-ids="members.map((m) => m.user_id)"
      @confirm="handleAddMemberConfirm"
    />
  </div>
</template>

<style scoped>
.chat-container {
  border-radius: 8px;
  /* border: 1px solid var(--el-border-color-lighter); */
}

/* 左侧导航项 */
.chat-nav-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  transition: all 0.2s ease;
}

.chat-nav-item:hover {
  background-color: var(--el-fill-color);
  color: var(--el-text-color-primary);
}

.chat-nav-item--active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.chat-nav-item--active:hover {
  background-color: var(--el-color-primary-light-8);
}

/* 右侧面板滑入动画 */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.2s ease;
}

.slide-right-enter-from,
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
