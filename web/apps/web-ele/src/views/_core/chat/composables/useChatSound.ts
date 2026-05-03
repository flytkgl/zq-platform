/**
 * 聊天消息提示音
 */
import notificationSound from '#/assets/sounds/message-notification.mp3';

let audio: HTMLAudioElement | null = null;
let lastPlayTime = 0;

// 最小播放间隔（毫秒），避免短时间内大量消息导致音效叠加
const MIN_INTERVAL = 500;

/**
 * 播放消息提示音
 */
export function playMessageSound() {
  const now = Date.now();
  if (now - lastPlayTime < MIN_INTERVAL) return;
  lastPlayTime = now;

  try {
    if (!audio) {
      audio = new Audio(notificationSound);
      audio.volume = 0.5;
    }
    // 如果正在播放，重置到开头
    audio.currentTime = 0;
    audio.play().catch(() => {
      // 浏览器可能阻止自动播放，静默忽略
    });
  } catch {
    // 静默降级
  }
}
