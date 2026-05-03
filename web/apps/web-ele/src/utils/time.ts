import { $t } from '@vben/locales';

/**
 * 格式化相对时间
 * 显示：刚刚、X分钟前、X小时前、昨天、X天前、具体日期
 * @param dateStr 日期字符串
 * @returns 格式化后的时间字符串
 */
export function formatRelativeTime(dateStr?: string): string {
  if (!dateStr) return '';

  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '';

  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // 刚刚（1分钟内）
  if (diff < 60_000) {
    return $t('common.justNow');
  }

  // X分钟前（1小时内）
  if (diff < 3_600_000) {
    const minutes = Math.floor(diff / 60_000);
    return `${minutes} ${$t('common.minutesAgo')}`;
  }

  // X小时前（24小时内）
  if (diff < 86_400_000) {
    const hours = Math.floor(diff / 3_600_000);
    return `${hours} ${$t('common.hoursAgo')}`;
  }

  // 昨天
  const days = Math.floor(diff / 86_400_000);
  if (days === 1) {
    return $t('common.yesterday');
  }

  // X天前（7天内）
  if (days < 7) {
    return `${days} ${$t('common.daysAgo')}`;
  }

  // 超过7天显示具体日期
  return date.toLocaleDateString();
}
