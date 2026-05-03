/**
 * 聊天消息桌面通知 + 应用内 Toast 通知
 */
import type { ChatMessage } from '#/api/core/chat';

import { h, render } from 'vue';

import { $t } from '@vben/locales';

import ChatToast from '../components/ChatToast.vue';

// 通知队列
const MAX_TOASTS = 3;
const activeToasts: Array<{
  el: HTMLDivElement;
  timer: ReturnType<typeof setTimeout>;
}> = [];

function getMessagePreview(msg: ChatMessage): string {
  if (msg.msg_type === 'text') return msg.content || '';
  if (msg.msg_type === 'image') return `[${$t('chat.image')}]`;
  if (msg.msg_type === 'file')
    return `[${$t('chat.file')}] ${msg.file_name || ''}`;
  if (msg.msg_type === 'voice') return `[${$t('chat.voice')}]`;
  return `[${$t(`chat.${msg.msg_type}`) || msg.msg_type}]`;
}

function removeToast(container: HTMLDivElement) {
  container.classList.add('chat-toast-exit');
  setTimeout(() => {
    render(null, container);
    container.remove();
    const idx = activeToasts.findIndex((t) => t.el === container);
    if (idx !== -1) activeToasts.splice(idx, 1);
    repositionToasts();
  }, 300);
}

function repositionToasts() {
  activeToasts.forEach((toast, index) => {
    toast.el.style.top = `${16 + index * 88}px`;
  });
}

/**
 * 显示应用内 Toast 通知
 */
export function showChatToast(msg: ChatMessage, onClick?: () => void) {
  // 超出最大数量，移除最早的
  while (activeToasts.length >= MAX_TOASTS) {
    const oldest = activeToasts.shift();
    if (oldest) {
      clearTimeout(oldest.timer);
      removeToast(oldest.el);
    }
  }

  const container = document.createElement('div');
  document.body.append(container);

  const preview = getMessagePreview(msg);

  const vnode = h(ChatToast, {
    senderName: msg.sender_name || '',
    senderId: msg.sender_id || '',
    senderAvatar: msg.sender_avatar || '',
    content: preview,
    onClose: () => removeToast(container),
    onClick: () => {
      removeToast(container);
      onClick?.();
    },
  });

  render(vnode, container);

  const topOffset = 16 + activeToasts.length * 88;
  container.style.position = 'fixed';
  container.style.top = `${topOffset}px`;
  container.style.right = '16px';
  container.style.zIndex = '9999';
  container.style.transition = 'top 0.3s ease, opacity 0.3s ease';

  const timer = setTimeout(() => {
    removeToast(container);
  }, 5000);

  activeToasts.push({ el: container, timer });
}

/**
 * 尝试发送浏览器原生通知（页面不在前台时）
 */
export function showBrowserNotification(msg: ChatMessage) {
  if (!('Notification' in window)) return;
  if (document.visibilityState === 'visible') return;

  if (Notification.permission === 'granted') {
    const preview = getMessagePreview(msg);
    const notification = new Notification(
      msg.sender_name || $t('chat.newMessage'),
      {
        body: preview,
        tag: `chat-${msg.id || Date.now()}`,
        ...({ renotify: true } as any),
      },
    );
    notification.addEventListener('click', () => {
      window.focus();
      import('#/router').then(({ router }) => {
        router.push('/chat');
      });
      notification.close();
    });
  } else if (Notification.permission !== 'denied') {
    Notification.requestPermission();
  }
}
