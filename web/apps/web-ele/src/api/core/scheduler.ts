import { requestClient } from '#/api/request';
import { streamRequestClient } from '#/api/stream-request';

/**
 * 定时任务相关类型定义
 */
export interface SchedulerJob {
  id: string;
  application_id?: string;
  name: string;
  code: string;
  description?: string;
  group: string;
  trigger_type: 'cron' | 'date' | 'interval';
  cron_expression?: string;
  interval_seconds?: number;
  run_date?: string;
  task_func: string;
  task_args?: string;
  task_kwargs?: string;
  status: number; // 0-禁用，1-启用，2-暂停
  priority: number;
  max_instances: number;
  max_retries: number;
  timeout?: number;
  coalesce: boolean;
  allow_concurrent: boolean;
  total_run_count: number;
  success_count: number;
  failure_count: number;
  last_run_time?: string;
  next_run_time?: string;
  last_run_status?: string;
  last_run_result?: string;
  remark?: string;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
  sort: number;
}

export interface SchedulerLog {
  id: string;
  job_id: string;
  job_name: string;
  job_code: string;
  status: 'failed' | 'pending' | 'running' | 'skipped' | 'success' | 'timeout';
  start_time: string;
  end_time?: string;
  duration?: number;
  result?: string;
  exception?: string;
  traceback?: string;
  hostname?: string;
  process_id?: number;
  retry_count: number;
  sys_create_datetime?: string;
}

export interface SchedulerJobCreateInput {
  application_id?: string;
  name: string;
  code: string;
  description?: string;
  group?: string;
  trigger_type: 'cron' | 'date' | 'interval';
  cron_expression?: string;
  interval_seconds?: number;
  run_date?: string;
  task_func: string;
  task_args?: string;
  task_kwargs?: string;
  status?: number;
  priority?: number;
  max_instances?: number;
  max_retries?: number;
  timeout?: number;
  coalesce?: boolean;
  allow_concurrent?: boolean;
  remark?: string;
}

export type SchedulerJobUpdateInput = Partial<SchedulerJobCreateInput>;

export interface SchedulerJobListParams {
  page?: number;
  pageSize?: number;
  applicationId?: string;
  name?: string;
  code?: string;
  group?: string;
  trigger_type?: string;
  status?: number;
}

export interface SchedulerLogListParams {
  page?: number;
  pageSize?: number;
  job_id?: string;
  job_code?: string;
  job_name?: string;
  status?: string;
  start_time__gte?: string;
  start_time__lte?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface SchedulerJobStatistics {
  total_jobs: number;
  enabled_jobs: number;
  disabled_jobs: number;
  paused_jobs: number;
  total_executions: number;
  success_executions: number;
  failed_executions: number;
  success_rate: number;
}

export interface SchedulerJobBatchDeleteInput {
  ids: string[];
}

export interface SchedulerJobBatchUpdateStatusInput {
  ids: string[];
  status: number;
}

export interface SchedulerJobExecuteInput {
  job_id: string;
}

export interface SchedulerLogBatchDeleteInput {
  ids: string[];
}

export interface SchedulerLogCleanInput {
  days: number;
  status?: string;
}

export interface SchedulerStatus {
  is_running: boolean;
  job_count: number;
  jobs: any[];
}

/**
 * 创建定时任务
 */
export async function createSchedulerJobApi(data: SchedulerJobCreateInput) {
  return requestClient.post<SchedulerJob>('/api/scheduler/job', data);
}

/**
 * 获取定时任务列表（分页）
 */
export async function getSchedulerJobListApi(params?: SchedulerJobListParams) {
  return requestClient.get<PaginatedResponse<SchedulerJob>>(
    '/api/scheduler/job',
    {
      params,
    },
  );
}

/**
 * 获取所有定时任务（不分页）
 */
export async function getAllSchedulerJobsApi(applicationId?: string) {
  return requestClient.get<SchedulerJob[]>('/api/scheduler/job/all', {
    params: { applicationId },
  });
}

/**
 * 获取定时任务详情
 */
export async function getSchedulerJobDetailApi(jobId: string) {
  return requestClient.get<SchedulerJob>(`/api/scheduler/job/${jobId}`);
}

/**
 * 更新定时任务
 */
export async function updateSchedulerJobApi(
  jobId: string,
  data: SchedulerJobUpdateInput,
) {
  return requestClient.put<SchedulerJob>(`/api/scheduler/job/${jobId}`, data);
}

/**
 * 删除定时任务
 */
export async function deleteSchedulerJobApi(jobId: string) {
  return requestClient.delete<SchedulerJob>(`/api/scheduler/job/${jobId}`);
}

/**
 * 批量删除定时任务
 */
export async function batchDeleteSchedulerJobApi(
  data: SchedulerJobBatchDeleteInput,
) {
  return requestClient.delete('/api/scheduler/job/batch/delete', {
    data,
  });
}

/**
 * 批量更新定时任务状态
 */
export async function batchUpdateSchedulerJobStatusApi(
  data: SchedulerJobBatchUpdateStatusInput,
) {
  return requestClient.post('/api/scheduler/job/batch/update-status', data);
}

/**
 * 立即执行定时任务
 */
export async function executeSchedulerJobApi(data: SchedulerJobExecuteInput) {
  return requestClient.post('/api/scheduler/job/execute', data);
}

/**
 * 搜索定时任务
 */
export async function searchSchedulerJobApi(params?: {
  keyword?: string;
  page?: number;
  pageSize?: number;
}) {
  return requestClient.get<PaginatedResponse<SchedulerJob>>(
    '/api/scheduler/job/search',
    {
      params,
    },
  );
}

/**
 * 获取定时任务统计
 */
export async function getSchedulerJobStatisticsApi() {
  return requestClient.get<SchedulerJobStatistics>(
    '/api/scheduler/job/statistics/data',
  );
}

/**
 * 获取定时任务执行日志列表
 */
export async function getSchedulerLogListApi(params?: SchedulerLogListParams) {
  return requestClient.get<PaginatedResponse<SchedulerLog>>(
    '/api/scheduler/log',
    {
      params,
    },
  );
}

/**
 * 获取定时任务执行日志详情
 */
export async function getSchedulerLogDetailApi(logId: string) {
  return requestClient.get<SchedulerLog>(`/api/scheduler/log/${logId}`);
}

/**
 * 删除定时任务执行日志
 */
export async function deleteSchedulerLogApi(logId: string) {
  return requestClient.delete<SchedulerLog>(`/api/scheduler/log/${logId}`);
}

/**
 * 批量删除定时任务执行日志
 */
export async function batchDeleteSchedulerLogApi(
  data: SchedulerLogBatchDeleteInput,
) {
  return requestClient.delete('/api/scheduler/log/batch/delete', {
    data,
  });
}

/**
 * 清理旧日志
 */
export async function cleanSchedulerLogApi(data: SchedulerLogCleanInput) {
  return requestClient.post('/api/scheduler/log/clean', data);
}

/**
 * 获取指定任务的执行日志
 */
export async function getSchedulerLogByJobApi(
  jobId: string,
  params?: { page?: number; pageSize?: number },
) {
  return requestClient.get<PaginatedResponse<SchedulerLog>>(
    `/api/scheduler/log/by/job/${jobId}`,
    {
      params,
    },
  );
}

/**
 * 启动调度器
 */
export async function startSchedulerApi() {
  return requestClient.post('/api/scheduler/start', {});
}

/**
 * 关闭调度器
 */
export async function shutdownSchedulerApi() {
  return requestClient.post('/api/scheduler/shutdown', {});
}

/**
 * 暂停调度器
 */
export async function pauseSchedulerApi() {
  return requestClient.post('/api/scheduler/pause', {});
}

/**
 * 恢复调度器
 */
export async function resumeSchedulerApi() {
  return requestClient.post('/api/scheduler/resume', {});
}

/**
 * 获取调度器状态
 */
export async function getSchedulerStatusApi() {
  return requestClient.get<SchedulerStatus>('/api/scheduler/status');
}

/**
 * 任务执行日志条目
 */
export interface TaskLogEntry {
  timestamp: string;
  level: 'debug' | 'error' | 'info' | 'success' | 'warning';
  message: string;
  step?: string;
  progress?: number;
  data?: Record<string, any>;
}

/**
 * 订阅任务执行实时日志
 * @param logId 日志记录 ID
 * @param onMessage 消息回调
 * @param onError 错误回调
 * @param onComplete 完成回调
 * @returns 取消订阅函数
 */
export function subscribeTaskLogStream(
  logId: string,
  onMessage: (entry: TaskLogEntry) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void,
): () => void {
  return streamRequestClient<TaskLogEntry>(
    `/api/scheduler/log/${logId}/stream`,
    null,
    {
      onData: (entry) => {
        onMessage(entry);

        // 如果是完成或错误事件，触发完成回调
        if (entry.step === 'complete' || entry.step === 'error') {
          onComplete?.();
        }
      },
      onError: (error) => {
        console.error('Task log stream error:', error);
        onError?.(error);
      },
      onComplete,
    },
  );
}

export { type OnActionClickParams } from '#/adapter/vxe-table';
