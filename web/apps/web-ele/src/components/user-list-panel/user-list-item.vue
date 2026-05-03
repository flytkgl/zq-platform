<script lang="ts" setup>
import { computed } from 'vue';

import { ElCheckbox } from 'element-plus';

import { UserAvatar } from '../user-avatar';

defineOptions({
  name: 'UserListItem',
});

const props = withDefaults(defineProps<Props>(), {
  selected: false,
  multiple: false,
});

const emit = defineEmits<{
  select: [userId: string];
}>();

interface Props {
  user: {
    avatar?: string;
    email?: string;
    id: string;
    name?: string;
    phone?: string;
    username: string;
  };
  selected?: boolean;
  multiple?: boolean;
}

const handleClick = () => {
  emit('select', props.user.id);
};

const displayName = computed(() => {
  return props.user.name || props.user.username;
});
</script>

<template>
  <div class="user-list-item" :class="{ selected }" @click="handleClick">
    <!-- 选择框（仅多选模式） -->
    <div v-if="multiple" class="user-list-item-checkbox">
      <ElCheckbox :model-value="selected" @click.stop />
    </div>

    <!-- 头像 -->
    <div class="user-list-item-avatar">
      <UserAvatar :user="user" :size="40" :font-size="16" :shadow="false" />
    </div>

    <!-- 用户信息 -->
    <div class="user-list-item-info">
      <div class="user-list-item-main">
        <span class="user-list-item-name">{{ displayName }}</span>
        <span class="user-list-item-username">@{{ user.username }}</span>
      </div>
      <div v-if="user.email || user.phone" class="user-list-item-contact">
        <span v-if="user.email" class="contact-item">{{ user.email }}</span>
        <span v-if="user.phone" class="contact-item">{{ user.phone }}</span>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.user-list-item {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  background-color: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  transition: all 0.2s ease;

  &:hover {
    background-color: hsl(var(--accent));
  }

  &.selected {
    padding-left: 13px;
    background: linear-gradient(
      90deg,
      hsl(var(--primary) / 10%) 0%,
      hsl(var(--primary) / 5%) 100%
    );
    border: 1px solid hsl(var(--primary));

    .user-list-item-name {
      font-weight: 600;
      color: hsl(var(--primary));
    }
  }

  &-checkbox {
    flex-shrink: 0;

    :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
      background-color: hsl(var(--primary));
      border-color: hsl(var(--primary));
    }
  }

  &-avatar {
    flex-shrink: 0;
  }

  &-info {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }

  &-main {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  &-name {
    font-size: 14px;
    font-weight: 500;
    color: hsl(var(--foreground));
    transition: all 0.2s ease;
  }

  &-username {
    font-size: 12px;
    color: hsl(var(--muted-foreground));
  }

  &-contact {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: hsl(var(--muted-foreground));

    .contact-item {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}
</style>
