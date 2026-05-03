/**
 * Cron Selector Props and Types
 */
export interface CronSelectorProps {
  /**
   * Cron 表达式
   */
  modelValue?: string;

  /**
   * 是否禁用
   * @default false
   */
  disabled?: boolean;

  /**
   * 是否隐藏秒
   * @default true
   */
  hideSecond?: boolean;

  /**
   * 是否隐藏年
   * @default true
   */
  hideYear?: boolean;

  /**
   * 占位符文本
   * @default 'Cron表达式'
   */
  placeholder?: string;

  /**
   * 远程获取执行时间列表的函数
   */
  remote?: (
    cron: string,
    timestamp: number,
    callback: (result: string) => void,
  ) => void;
}

export interface CronSelectorEmits {
  /**
   * 当 Cron 表达式变化时触发
   */
  'update:modelValue': [value: string];

  /**
   * 当 Cron 表达式变化时触发
   */
  change: [value: string];
}

/**
 * Tab 类型枚举
 */
export enum TypeEnum {
  every = 'EVERY',
  last = 'LAST',
  loop = 'LOOP',
  range = 'RANGE',
  specify = 'SPECIFY',
  unset = 'UNSET',
  work = 'WORK',
}
