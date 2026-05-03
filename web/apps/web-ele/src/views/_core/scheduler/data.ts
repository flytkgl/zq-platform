import type { VxeTableGridOptions } from '@vben/plugins/vxe-table';

import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn } from '#/adapter/vxe-table';
import type { SchedulerJob, SchedulerLog } from '#/api/core/scheduler';

import { $t } from '@vben/locales';

import { z } from '#/adapter/form';

/**
 * 获取触发器类型选项
 */
export function getTriggerTypeOptions() {
  return [
    { label: $t('scheduler.cronExpression'), value: 'cron' },
    { label: $t('scheduler.triggerInterval'), value: 'interval' },
    { label: $t('scheduler.triggerDate'), value: 'date' },
  ];
}

/**
 * 获取任务状态选项
 */
export function getJobStatusOptions() {
  return [
    { label: $t('scheduler.status.disabled'), value: 0 },
    { label: $t('scheduler.status.enabled'), value: 1 },
    { label: $t('scheduler.status.paused'), value: 2 },
  ];
}

/**
 * 获取日志执行状态选项
 */
export function getLogStatusOptions() {
  return [
    { label: $t('scheduler.status.pending'), value: 'pending' },
    { label: $t('scheduler.status.running'), value: 'running' },
    { label: $t('scheduler.status.success'), value: 'success' },
    { label: $t('scheduler.status.failed'), value: 'failed' },
    { label: $t('scheduler.status.timeout'), value: 'timeout' },
    { label: $t('scheduler.status.skipped'), value: 'skipped' },
  ];
}

/**
 * 获取间隔执行时间单位选项
 */
export function getIntervalUnitOptions() {
  return [
    { label: $t('scheduler.unit.seconds'), value: 'seconds' },
    { label: $t('scheduler.unit.minutes'), value: 'minutes' },
    { label: $t('scheduler.unit.hours'), value: 'hours' },
    { label: $t('scheduler.unit.days'), value: 'days' },
  ];
}

/**
 * 获取状态标签类型
 */
export function getStatusType(
  status: number,
): 'danger' | 'info' | 'success' | 'warning' {
  switch (status) {
    case 1: {
      return 'success';
    } // 启用
    case 2: {
      return 'warning';
    } // 暂停
    default: {
      return 'danger';
    } // 禁用
  }
}

/**
 * 获取日志状态标签类型
 */
export function getLogStatusType(
  status: string,
): 'danger' | 'info' | 'success' | 'warning' {
  switch (status) {
    case 'failed': {
      return 'danger';
    }
    case 'running': {
      return 'info';
    }
    case 'success': {
      return 'success';
    }
    case 'timeout': {
      return 'warning';
    }
    default: {
      return 'info';
    }
  }
}

/**
 * 获取状态显示名称
 */
export function getStatusName(status: number): string {
  const statusMap = {
    0: $t('scheduler.status.disabled'),
    1: $t('scheduler.status.enabled'),
    2: $t('scheduler.status.paused'),
  };
  return (
    statusMap[status as keyof typeof statusMap] ||
    $t('scheduler.status.unknown')
  );
}

/**
 * 获取日志状态显示名称
 */
export function getLogStatusName(status: string): string {
  const statusMap: Record<string, string> = {
    pending: $t('scheduler.status.pending'),
    running: $t('scheduler.status.running'),
    success: $t('scheduler.status.success'),
    failed: $t('scheduler.status.failed'),
    timeout: $t('scheduler.status.timeout'),
    skipped: $t('scheduler.status.skipped'),
  };
  return statusMap[status] || $t('scheduler.status.unknown');
}

/**
 * 获取创建/编辑任务表单配置
 */
export function useJobFormSchema(): VbenFormSchema[] {
  const formSchema: VbenFormSchema[] = [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('scheduler.jobName'),
      rules: z
        .string()
        .min(1, $t('scheduler.required', { field: $t('scheduler.jobName') }))
        .max(
          128,
          $t('scheduler.maxLength', {
            field: $t('scheduler.jobName'),
            max: 128,
          }),
        ),
    },
    {
      component: 'Input',
      fieldName: 'code',
      label: $t('scheduler.jobCode'),
      rules: z
        .string()
        .min(1, $t('scheduler.required', { field: $t('scheduler.jobCode') }))
        .max(
          128,
          $t('scheduler.maxLength', {
            field: $t('scheduler.jobCode'),
            max: 128,
          }),
        )
        .regex(/^\w+$/, $t('scheduler.codeInvalid')),
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('scheduler.groupPlaceholder'),
      },
      fieldName: 'group',
      label: $t('scheduler.jobGroup'),
    },
    {
      component: 'Select',
      componentProps: {
        options: getTriggerTypeOptions(),
      },
      fieldName: 'trigger_type',
      label: $t('scheduler.triggerType'),
      rules: z
        .string()
        .min(
          1,
          $t('scheduler.required', { field: $t('scheduler.triggerType') }),
        ),
    },
  ];

  // 添加所有字段，通过 dependencies 的 show 控制显示
  formSchema.push(
    // Cron 表达式字段（仅在触发器类型为 cron 时显示）
    {
      component: 'CronSelector',
      componentProps: {
        placeholder: $t('scheduler.cronPlaceholder'),
        hideSecond: true,
        hideYear: true,
      },
      fieldName: 'cron_expression',
      label: $t('scheduler.cronExpression'),
      rules: z.string().optional(),
      dependencies: {
        show: (values: any) => values.trigger_type === 'cron',
        triggerFields: ['trigger_type'],
      },
    },
    // 间隔执行时间单位（仅在触发器类型为 interval 时显示）
    {
      component: 'RadioGroup',
      componentProps: {
        options: getIntervalUnitOptions(),
        isButton: true,
      },
      defaultValue: 'seconds',
      fieldName: 'interval_unit',
      label: $t('scheduler.unit'),
      dependencies: {
        show: (values: any) => values.trigger_type === 'interval',
        triggerFields: ['trigger_type'],
      },
    },
    // 间隔时间字段（仅在触发器类型为 interval 时显示）
    {
      component: 'InputNumber',
      componentProps: {
        min: 1,
        placeholder: $t('scheduler.intervalPlaceholder'),
      },
      fieldName: 'interval_seconds',
      label: $t('scheduler.intervalTime'),
      rules: z.number().positive().optional(),
      dependencies: {
        show: (values: any) => values.trigger_type === 'interval',
        triggerFields: ['trigger_type'],
      },
    },

    // 指定执行时间字段（仅在触发器类型为 date 时显示）
    {
      component: 'DatePicker',
      fieldName: 'run_date',
      label: $t('scheduler.datePlaceholder'),
      rules: z.string().optional(),
      componentProps: {
        placeholder: $t('scheduler.datePlaceholder'),
        type: 'datetime',
        valueFormat: 'YYYY-MM-DD HH:mm:ss',
        showTime: true,
      },
      dependencies: {
        show: (values: any) => values.trigger_type === 'date',
        triggerFields: ['trigger_type'],
      },
    },
    // 任务函数路径
    {
      component: 'Input',
      fieldName: 'task_func',
      label: $t('scheduler.taskFunc'),
      rules: z
        .string()
        .min(1, $t('scheduler.required', { field: $t('scheduler.taskFunc') })),
    },
    // 任务位置参数
    {
      component: 'TaskArgsEditor',
      fieldName: 'task_args',
      label: $t('scheduler.taskArgs'),
    },
    // 任务关键字参数
    {
      component: 'TaskKwargsEditor',
      fieldName: 'task_kwargs',
      label: $t('scheduler.taskKwargs'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        isButton: true,
        options: getJobStatusOptions(),
      },
      defaultValue: 1,
      fieldName: 'status',
      label: $t('scheduler.jobStatus'),
    },
    {
      component: 'InputNumber',
      componentProps: {
        min: 0,
      },
      defaultValue: 0,
      fieldName: 'priority',
      label: $t('scheduler.priority'),
    },
    {
      component: 'InputNumber',
      componentProps: {
        min: 1,
      },
      defaultValue: 1,
      fieldName: 'max_instances',
      label: $t('scheduler.maxInstances'),
    },
    {
      component: 'InputNumber',
      componentProps: {
        min: 0,
      },
      defaultValue: 0,
      fieldName: 'max_retries',
      label: $t('scheduler.maxRetries'),
    },
    {
      component: 'InputNumber',
      componentProps: {
        min: 1,
        placeholder: $t('scheduler.timeoutSeconds'),
      },
      fieldName: 'timeout',
      label: $t('scheduler.timeout'),
    },
    {
      component: 'Checkbox',
      defaultValue: true,
      fieldName: 'coalesce',
      label: $t('scheduler.coalesce'),
    },
    {
      component: 'Checkbox',
      defaultValue: false,
      fieldName: 'allow_concurrent',
      label: $t('scheduler.allowConcurrent'),
    },
    {
      component: 'Textarea',
      componentProps: {
        placeholder: $t('scheduler.remarkPlaceholder'),
        rows: 3,
      },
      fieldName: 'remark',
      label: $t('scheduler.remark'),
    },
  );

  return formSchema;
}

/**
 * 获取定时任务列表表格列配置
 */
export function useJobTableColumns(
  onActionClick?: OnActionClickFn<SchedulerJob>,
): VxeTableGridOptions<SchedulerJob>['columns'] {
  return [
    {
      type: 'checkbox',
      width: 60,
      align: 'center',
      fixed: 'left',
    },
    {
      field: 'name',
      title: $t('scheduler.jobName'),
      minWidth: 150,
    },
    {
      field: 'code',
      title: $t('scheduler.jobCode'),
      minWidth: 130,
    },
    {
      field: 'group',
      title: $t('scheduler.jobGroup'),
      minWidth: 100,
    },
    {
      field: 'trigger_type',
      title: $t('scheduler.triggerType'),
      minWidth: 110,
      cellRender: {
        name: 'CellDict',
        props: {
          dict: getTriggerTypeOptions(),
        },
      },
    },
    {
      field: 'status',
      title: $t('scheduler.jobStatus'),
      minWidth: 100,
      cellRender: {
        name: 'CellStatus',
        attrs: {
          dict: getJobStatusOptions(),
        },
      },
    },
    {
      field: 'priority',
      title: $t('scheduler.priority'),
      minWidth: 80,
      align: 'center',
    },
    {
      field: 'total_run_count',
      title: $t('scheduler.totalRunCount'),
      minWidth: 100,
      align: 'center',
    },
    {
      field: 'success_count',
      title: $t('scheduler.successCount'),
      minWidth: 100,
      align: 'center',
    },
    {
      field: 'failure_count',
      title: $t('scheduler.failureCount'),
      minWidth: 100,
      align: 'center',
    },
    {
      field: 'last_run_time',
      title: $t('scheduler.lastRunTime'),
      minWidth: 180,
      cellRender: {
        name: 'CellDatetime',
      },
    },
    {
      field: 'next_run_time',
      title: $t('scheduler.nextRunTime'),
      minWidth: 180,
      cellRender: {
        name: 'CellDatetime',
      },
    },
    {
      align: 'right',
      cellRender: {
        attrs: {
          nameField: 'name',
          nameTitle: $t('scheduler.jobName'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: ['edit', 'delete'],
      },
      field: 'operation',
      fixed: 'right',
      headerAlign: 'center',
      showOverflow: false,
      title: $t('scheduler.actions'),
      minWidth: 150,
    },
  ];
}

/**
 * 获取执行日志列表表格列配置
 */
export function useLogTableColumns(): VxeTableGridOptions<SchedulerLog>['columns'] {
  return [
    {
      field: 'job_name',
      title: $t('scheduler.jobName'),
      minWidth: 150,
    },
    {
      field: 'job_code',
      title: $t('scheduler.jobCode'),
      minWidth: 130,
    },
    {
      field: 'status',
      title: $t('scheduler.executionLogs'),
      minWidth: 110,
      cellRender: {
        name: 'CellDict',
        props: {
          dict: getLogStatusOptions(),
        },
      },
    },
    {
      field: 'start_time',
      title: $t('scheduler.startTime'),
      minWidth: 180,
      cellRender: {
        name: 'CellDatetime',
      },
    },
    {
      field: 'duration',
      title: $t('scheduler.executionDuration'),
      minWidth: 130,
      align: 'center',
    },
    {
      field: 'retry_count',
      title: $t('scheduler.retryCount'),
      minWidth: 100,
      align: 'center',
    },
    {
      field: 'operation',
      title: $t('scheduler.actions'),
      minWidth: 100,
      align: 'center',
      fixed: 'right',
      cellRender: {
        name: 'CellOperation',
        options: ['view', 'delete'],
      },
    },
  ];
}

/**
 * 获取搜索表单字段配置
 */
export function useSearchFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: $t('scheduler.jobName'),
    },
    {
      component: 'Input',
      fieldName: 'code',
      label: $t('scheduler.jobCode'),
    },
    {
      component: 'Input',
      fieldName: 'group',
      label: $t('scheduler.jobGroup'),
    },
    {
      component: 'Select',
      componentProps: {
        options: getTriggerTypeOptions(),
      },
      fieldName: 'trigger_type',
      label: $t('scheduler.triggerType'),
    },
    {
      component: 'Select',
      componentProps: {
        options: getJobStatusOptions(),
      },
      fieldName: 'status',
      label: $t('scheduler.jobStatus'),
    },
  ];
}
