<script lang="ts" setup>
import { computed } from 'vue';

import { ElCheckbox } from 'element-plus';

import { UserAvatar } from '../user-avatar';

defineOptions({
  name: 'UserCard',
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
    id: string;
    name?: string;
    username: string;
  };
  selected?: boolean;
  multiple?: boolean;
}

const handleClick = () => {
  emit('select', props.user.id);
};

const displayName = computed(() => {
  const name = props.user.name || props.user.username;
  if (name && name.length > 10) {
    return `${name.slice(0, 10)}...`;
  }
  return name;
});
</script>

<template>
  <div class="user-card" :class="{ selected }" @click="handleClick">
    <!-- 选择框（仅多选模式） -->
    <div v-if="multiple" class="user-card-checkbox">
      <ElCheckbox :model-value="selected" @click.stop />
    </div>

    <!-- 内容 -->
    <div class="user-card-content">
      <!-- 头像 -->
      <div class="user-card-avatar">
        <UserAvatar :user="user" :size="56" :font-size="24" :shadow="true" />
      </div>

      <!-- 用户信息 -->
      <div class="user-card-info">
        <!-- 用户名 -->
        <div class="user-card-username">
          {{ displayName }}
        </div>

        <!-- 名称（小号、次要颜色） -->
        <div class="user-card-realname">
          {{ user.username }}
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.user-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  padding: 16px;
  cursor: pointer;
  background-color: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  transition: all 0.3s ease;

  &:hover {
    border-color: hsl(var(--primary));
    box-shadow: 0 2px 12px rgb(0 0 0 / 10%);
    transform: translateY(-2px);
  }

  &.selected {
    background: linear-gradient(
      135deg,
      hsl(var(--primary) / 10%) 0%,
      hsl(var(--primary) / 5%) 100%
    );
    border: 1px solid hsl(var(--primary));
    box-shadow:
      0 0 0 3px hsl(var(--primary) / 15%),
      0 2px 12px hsl(var(--primary) / 20%);

    .user-card-username,
    .user-card-realname {
      font-weight: 500;
      color: hsl(var(--primary));
    }

    .user-card-avatar {
      transform: scale(1.05);
    }
  }

  &-checkbox {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 2;

    :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
      background-color: hsl(var(--primary));
      border-color: hsl(var(--primary));
    }
  }

  &-content {
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: center;
    width: 100%;
    transition: transform 0.3s ease;
  }

  &-avatar {
    display: flex;
    justify-content: center;
    width: 100%;
    transition: transform 0.3s ease;
  }

  &-info {
    width: 100%;
    text-align: center;
  }

  &-username {
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 14px;
    font-weight: 500;
    color: hsl(var(--foreground));
    white-space: nowrap;
    transition:
      color 0.3s ease,
      font-weight 0.3s ease;
  }

  &-realname {
    margin-top: 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 12px;
    color: hsl(var(--muted-foreground));
    white-space: nowrap;
    transition:
      color 0.3s ease,
      font-weight 0.3s ease;
  }
}
</style>
