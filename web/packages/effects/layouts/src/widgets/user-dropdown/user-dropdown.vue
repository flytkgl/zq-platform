<script setup lang="ts">
import type { Component } from 'vue';

import type { AnyFunction } from '@vben/types';

import { type CSSProperties, computed, useTemplateRef, watch } from 'vue';

import { useHoverToggle } from '@vben/hooks';
import { LockKeyhole, LogOut } from '@vben/icons';
import { $t } from '@vben/locales';
import { preferences, usePreferences } from '@vben/preferences';
import { useAccessStore } from '@vben/stores';
import { isWindowsOs } from '@vben/utils';

import { useVbenModal } from '@vben-core/popup-ui';
import {
  Badge,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
  VbenAvatar,
  VbenIcon,
} from '@vben-core/shadcn-ui';

import { useMagicKeys, whenever } from '@vueuse/core';

import { LockScreenModal } from '../lock-screen';

interface Props {
  /**
   * 头像
   */
  avatar?: string;
  /**
   * @zh_CN 描述
   */
  description?: string;
  /**
   * 是否启用快捷键
   */
  enableShortcutKey?: boolean;
  /**
   * 菜单数组
   */
  menus?: Array<{
    handler: AnyFunction;
    icon?: Component | Function | string;
    text: string;
  }>;

  /**
   * 标签文本
   */
  tagText?: string;
  /**
   * 文本
   */
  text?: string;
  /** 触发方式 */
  trigger?: 'both' | 'click' | 'hover';
  /** hover触发时，延迟响应的时间 */
  hoverDelay?: number;
}

defineOptions({
  name: 'UserDropdown',
});

const props = withDefaults(defineProps<Props>(), {
  avatar: '',
  description: '',
  enableShortcutKey: true,
  menus: () => [],
  showShortcutKey: true,
  tagText: '',
  text: '',
  trigger: 'click',
  hoverDelay: 500,
});

const emit = defineEmits<{ logout: [] }>();

// --- Avatar fallback: gradient + initials ---
function isChinese(char: string): boolean {
  const code = char.charCodeAt(0);
  return code >= 0x4e00 && code <= 0x9fff;
}

function getAvatarText(name?: string): string {
  if (!name) return '?';
  const t = name.trim();
  if (t.length === 0) return '?';
  const first = t.charAt(0);
  if (isChinese(first)) return first;
  if (/[a-z]/i.test(first)) {
    let r = '';
    for (let i = 0; i < t.length && r.length < 2; i++) {
      const c = t.charAt(i);
      if (/[a-z]/i.test(c)) r += c.toUpperCase();
    }
    return r || first.toUpperCase();
  }
  return first;
}

function getAvatarGradient(name?: string): string {
  if (!name) return 'linear-gradient(135deg, #8b9dff 0%, #a78bfa 100%)';
  const gradients = [
    'linear-gradient(135deg, #8b9dff 0%, #a78bfa 100%)',
    'linear-gradient(135deg, #f59dba 0%, #fa709a 100%)',
    'linear-gradient(135deg, #60c5ff 0%, #7dd3fc 100%)',
    'linear-gradient(135deg, #6ee7b7 0%, #5eead4 100%)',
    'linear-gradient(135deg, #fb923c 0%, #fbbf24 100%)',
    'linear-gradient(135deg, #a78bfa 0%, #f472b6 100%)',
    'linear-gradient(135deg, #f472b6 0%, #fb923c 100%)',
    'linear-gradient(135deg, #818cf8 0%, #c084fc 100%)',
    'linear-gradient(135deg, #38bdf8 0%, #7dd3fc 100%)',
    'linear-gradient(135deg, #34d399 0%, #a3e635 100%)',
    'linear-gradient(135deg, #fb7185 0%, #fda4af 100%)',
    'linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%)',
    'linear-gradient(135deg, #d946ef 0%, #f0abfc 100%)',
    'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)',
    'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
    'linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%)',
    'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)',
    'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
    'linear-gradient(135deg, #a855f7 0%, #c084fc 100%)',
    'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)',
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = (hash << 5) - hash + name.charCodeAt(i);
    hash = hash & hash;
  }
  return gradients[Math.abs(hash) % gradients.length]!;
}

const avatarInitials = computed(() => getAvatarText(props.text));
const avatarGradient = computed(() => getAvatarGradient(props.text));

const fallbackAvatarStyle = computed<CSSProperties>(() => ({
  background: avatarGradient.value,
  color: '#ffffff',
  fontWeight: 600,
}));

const { globalLockScreenShortcutKey, globalLogoutShortcutKey } =
  usePreferences();
const accessStore = useAccessStore();
const [LockModal, lockModalApi] = useVbenModal({
  connectedComponent: LockScreenModal,
});
const [LogoutModal, logoutModalApi] = useVbenModal({
  onConfirm() {
    handleSubmitLogout();
  },
});

const refTrigger = useTemplateRef('refTrigger');
const refContent = useTemplateRef('refContent');
const [openPopover, hoverWatcher] = useHoverToggle(
  [refTrigger, refContent],
  () => props.hoverDelay,
);

watch(
  () => props.trigger === 'hover' || props.trigger === 'both',
  (val) => {
    if (val) {
      hoverWatcher.enable();
    } else {
      hoverWatcher.disable();
    }
  },
  {
    immediate: true,
  },
);

const altView = computed(() => (isWindowsOs() ? 'Alt' : '⌥'));

const enableLogoutShortcutKey = computed(() => {
  return props.enableShortcutKey && globalLogoutShortcutKey.value;
});

const enableLockScreenShortcutKey = computed(() => {
  return props.enableShortcutKey && globalLockScreenShortcutKey.value;
});

const enableShortcutKey = computed(() => {
  return props.enableShortcutKey && preferences.shortcutKeys.enable;
});

function handleOpenLock() {
  lockModalApi.open();
}

function handleSubmitLock(lockScreenPassword: string) {
  lockModalApi.close();
  accessStore.lockScreen(lockScreenPassword);
}

function handleLogout() {
  // emit
  logoutModalApi.open();
  openPopover.value = false;
}

function handleSubmitLogout() {
  emit('logout');
  logoutModalApi.close();
}

if (enableShortcutKey.value) {
  const keys = useMagicKeys();
  whenever(keys['Alt+KeyQ']!, () => {
    if (enableLogoutShortcutKey.value) {
      handleLogout();
    }
  });

  whenever(keys['Alt+KeyL']!, () => {
    if (enableLockScreenShortcutKey.value) {
      handleOpenLock();
    }
  });
}
</script>

<template>
  <LockModal
    v-if="preferences.widget.lockScreen"
    :avatar="avatar"
    :text="text"
    @submit="handleSubmitLock"
  />

  <LogoutModal
    :cancel-text="$t('common.cancel')"
    :confirm-text="$t('common.confirm')"
    :fullscreen-button="false"
    :title="$t('common.prompt')"
    centered
    content-class="px-8 min-h-10"
    footer-class="border-none mb-3 mr-3"
    header-class="border-none"
  >
    {{ $t('ui.widgets.logoutTip') }}
  </LogoutModal>

  <DropdownMenu v-model:open="openPopover">
    <DropdownMenuTrigger ref="refTrigger" :disabled="props.trigger === 'hover'">
      <div class="hover:bg-accent ml-1 mr-2 cursor-pointer rounded-full p-1.5">
        <div class="hover:text-accent-foreground flex-center">
          <div v-if="!avatar" class="relative flex flex-shrink-0 items-center size-8">
            <div
              class="size-full rounded-full flex items-center justify-center text-xs"
              :style="fallbackAvatarStyle"
            >
              {{ avatarInitials }}
            </div>
            <span class="border-background bg-green-500 absolute bottom-0 right-0 size-3 rounded-full border-2" />
          </div>
          <VbenAvatar v-else :alt="text" :src="avatar" class="size-8" dot />
        </div>
      </div>
    </DropdownMenuTrigger>
    <DropdownMenuContent class="mr-2 min-w-[240px] p-0 pb-1">
      <div ref="refContent">
        <DropdownMenuLabel class="flex items-center p-3">
          <div v-if="!avatar" class="relative flex flex-shrink-0 items-center size-12">
            <div
              class="size-full rounded-full flex items-center justify-center text-lg"
              :style="fallbackAvatarStyle"
            >
              {{ avatarInitials }}
            </div>
            <span class="border-background bg-green-500 absolute bottom-0 right-1 size-4 rounded-full border-2" />
          </div>
          <VbenAvatar
            v-else
            :alt="text"
            :src="avatar"
            class="size-12"
            dot
            dot-class="bottom-0 right-1 border-2 size-4 bg-green-500"
          />
          <div class="ml-2 w-full">
            <div
              v-if="tagText || text || $slots.tagText"
              class="text-foreground mb-1 flex items-center text-sm font-medium"
            >
              {{ text }}
              <slot name="tagText">
                <Badge v-if="tagText" class="ml-2 text-green-400">
                  {{ tagText }}
                </Badge>
              </slot>
            </div>
            <div class="text-muted-foreground text-xs font-normal">
              {{ description }}
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator v-if="menus?.length" />
        <DropdownMenuItem
          v-for="menu in menus"
          :key="menu.text"
          class="mx-1 flex cursor-pointer items-center rounded-sm py-1 leading-8"
          @click="menu.handler"
        >
          <VbenIcon :icon="menu.icon" class="mr-2 size-4" />
          {{ menu.text }}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          v-if="preferences.widget.lockScreen"
          class="mx-1 flex cursor-pointer items-center rounded-sm py-1 leading-8"
          @click="handleOpenLock"
        >
          <LockKeyhole class="mr-2 size-4" />
          {{ $t('ui.widgets.lockScreen.title') }}
          <DropdownMenuShortcut v-if="enableLockScreenShortcutKey">
            {{ altView }} L
          </DropdownMenuShortcut>
        </DropdownMenuItem>
        <!-- <DropdownMenuSeparator v-if="preferences.widget.lockScreen" /> -->
        <DropdownMenuItem
          class="mx-1 flex cursor-pointer items-center rounded-sm py-1 leading-8"
          @click="handleLogout"
        >
          <LogOut class="mr-2 size-4" />
          {{ $t('common.logout') }}
          <DropdownMenuShortcut v-if="enableLogoutShortcutKey">
            {{ altView }} Q
          </DropdownMenuShortcut>
        </DropdownMenuItem>
      </div>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
