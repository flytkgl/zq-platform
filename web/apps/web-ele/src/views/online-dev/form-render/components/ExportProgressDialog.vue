<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';

import { $t } from '@vben/locales';

import { AlertCircle } from '@vben/icons';

import { ElButton, ElMessage, ElMessageBox, ElProgress } from 'element-plus';

import {
  downloadBlob,
  getImportExportConfigApi,
} from '#/api/online-dev/form-data-api';
import { requestClient } from '#/api/request';
import { ZqDialog } from '#/components/zq-dialog';

interface Props {
  modelValue: boolean;
  formCode: string;
  exportConfig: null | {
    includeSubTables: boolean;
    queryParams: Record<string, any>;
    selectedFields: string[];
  };
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

type ExportStatus = 'completed' | 'error' | 'exporting' | 'idle';
type ExportStage = 'generating' | 'querying';

const status = ref<ExportStatus>('idle');
const stage = ref<ExportStage>('querying');
const processed = ref(0);
const total = ref(0);
const percent = ref(0);
const errorMessage = ref('');
const fileId = ref('');

const maxRows = ref(0);

onMounted(async () => {
  try {
    const config = await getImportExportConfigApi();
    maxRows.value = config.maxRows;
  } catch {
    maxRows.value = 0;
  }
});

const maxRowsText = computed(() => {
  if (!maxRows.value) return '';
  if (maxRows.value >= 10000) {
    return `${Math.floor(maxRows.value / 10000)}`;
  }
  return `${maxRows.value}`;
});

const statusText = computed(() => {
  switch (status.value) {
    case 'completed': {
      return $t('common.exportCompleted', [total.value]);
    }
    case 'error': {
      return $t('common.exportFailed');
    }
    case 'exporting': {
      if (stage.value === 'generating') {
        return $t('common.exportGeneratingExcel');
      }
      if (total.value > 0) {
        return $t('common.exportQuerying', [processed.value, total.value]);
      }
      return $t('common.exportPreparing');
    }
    default: {
      return $t('common.exportReady');
    }
  }
});

const progressStatus = computed(() => {
  switch (status.value) {
    case 'completed': {
      return 'success';
    }
    case 'error': {
      return 'exception';
    }
    default: {
      return undefined;
    }
  }
});

let currentAbort: (() => void) | null = null;

function resetState() {
  currentAbort = null;
  status.value = 'idle';
  stage.value = 'querying';
  processed.value = 0;
  total.value = 0;
  percent.value = 0;
  errorMessage.value = '';
  fileId.value = '';
}

async function startExport() {
  if (!props.exportConfig) return;

  status.value = 'exporting';
  stage.value = 'querying';
  processed.value = 0;
  total.value = 0;
  percent.value = 0;
  errorMessage.value = '';
  fileId.value = '';

  let sseBuffer = '';
  let pendingEvent = '';
  let pendingData = '';

  function flushPending() {
    if (pendingEvent && pendingData) {
      handleSSEEvent(pendingEvent, pendingData);
    }
    pendingEvent = '';
    pendingData = '';
  }

  function parseSseLines(text: string) {
    const lines = text.split('\n');
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        if (pendingEvent && pendingData) {
          flushPending();
        }
        pendingEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        pendingData = line.slice(6);
      } else if (line.trim() === '') {
        flushPending();
      }
    }
  }

  const controller = new AbortController();
  currentAbort = () => controller.abort();

  try {
    await requestClient.postSSE(
      `/api/online_dev/form-data/${props.formCode}/export/sse`,
      {
        selectedFields: props.exportConfig.selectedFields,
        includeSubTables: props.exportConfig.includeSubTables,
        queryParams: props.exportConfig.queryParams,
      },
      {
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
        onMessage(content: string) {
          sseBuffer += content;
          const lastDoubleNewline = sseBuffer.lastIndexOf('\n\n');
          if (lastDoubleNewline !== -1) {
            const completePart = sseBuffer.slice(0, lastDoubleNewline + 2);
            sseBuffer = sseBuffer.slice(lastDoubleNewline + 2);
            parseSseLines(completePart);
          }
        },
        onEnd() {
          if (sseBuffer.trim()) {
            parseSseLines(sseBuffer);
            flushPending();
          }
          sseBuffer = '';
        },
      },
    );
  } catch (error: any) {
    if ((status.value as ExportStatus) !== 'completed') {
      status.value = 'error';
      errorMessage.value = error?.message || $t('common.exportFailed');
    }
  }
}

function handleSSEEvent(event: string, dataStr: string) {
  try {
    const data = JSON.parse(dataStr);

    switch (event) {
      case 'completed': {
        fileId.value = data.fileId || '';
        percent.value = 100;
        status.value = 'completed';
        handleDownload();
        break;
      }
      case 'error': {
        status.value = 'error';
        errorMessage.value = data.message || $t('common.exportFailed');
        break;
      }
      case 'progress': {
        processed.value = data.processed || 0;
        total.value = data.total || 0;
        percent.value = data.percent || 0;
        if (data.stage) {
          stage.value = data.stage;
        }
        break;
      }
    }
  } catch {
    // ignore parse errors
  }
}

async function handleDownload() {
  if (!fileId.value) return;
  try {
    const blob = await requestClient.download<Blob>(
      `/api/online_dev/form-data/${props.formCode}/export/download/${fileId.value}`,
    );
    downloadBlob(blob, `${props.formCode}_export.xlsx`);
    ElMessage.success($t('common.exportSuccess'));
  } catch {
    ElMessage.error($t('common.fileDownloadFailed'));
  }
}

const isExporting = computed(() => status.value === 'exporting');

function abortCurrentTask() {
  if (currentAbort) {
    currentAbort();
    currentAbort = null;
  }
}

function handleBeforeClose(done: () => void) {
  if (isExporting.value) {
    ElMessageBox.confirm(
      $t('common.closeConfirmMessage'),
      $t('common.closeConfirmTitle'),
      { type: 'warning' },
    ).then(() => {
      abortCurrentTask();
      resetState();
      done();
    }).catch(() => {});
  } else {
    resetState();
    done();
  }
}

function handleClose() {
  if (isExporting.value) {
    ElMessageBox.confirm(
      $t('common.closeConfirmMessage'),
      $t('common.closeConfirmTitle'),
      { type: 'warning' },
    ).then(() => {
      abortCurrentTask();
      resetState();
      visible.value = false;
    }).catch(() => {});
  } else {
    resetState();
    visible.value = false;
  }
}

watch(
  () => props.modelValue,
  (val) => {
    if (val && props.exportConfig) {
      startExport();
    } else if (!val) {
      resetState();
    }
  },
);
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="$t('common.exportData')"
    width="480px"
    :show-footer="status === 'completed' || status === 'error'"
    :before-close="handleBeforeClose"
    :showFullscreenButton="false"
  >
    <div class="export-progress">
      <div class="progress-info">
        <div class="status-text">{{ statusText }}</div>
        <div v-if="errorMessage" class="error-text">{{ errorMessage }}</div>
      </div>

      <ElProgress
        :percentage="percent"
        :status="progressStatus"
        :stroke-width="16"
        :text-inside="true"
        class="progress-bar"
      />

      <div v-if="total > 0" class="detail-text">
        <span>{{ processed }} / {{ total }} {{ $t('common.records') }}</span>
        <span v-if="status === 'exporting'" class="processing-hint">
          {{
            stage === 'generating'
              ? $t('common.exportGeneratingExcelShort')
              : $t('common.querying')
          }}
        </span>
      </div>

      <div v-if="maxRows > 0" class="max-rows-hint">
        <AlertCircle class="hint-icon" />
        <span>{{ $t('common.maxExportRows', [maxRowsText]) }}</span>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <ElButton v-if="status === 'error'" type="primary" @click="startExport">
          {{ $t('common.retryExport') }}
        </ElButton>
        <!--        <ElButton-->
        <!--          v-if="status === 'completed'"-->
        <!--          type="primary"-->
        <!--          @click="handleDownload"-->
        <!--        >-->
        <!--          再次下载-->
        <!--        </ElButton>-->
        <ElButton @click="handleClose">{{ $t('common.close') }}</ElButton>
      </div>
    </template>
  </ZqDialog>
</template>

<style scoped lang="scss">
.export-progress {
  padding: 16px 0;

  .progress-info {
    margin-bottom: 20px;
    text-align: center;

    .status-text {
      font-size: 15px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }

    .error-text {
      margin-top: 8px;
      font-size: 13px;
      color: var(--el-color-danger);
    }
  }

  .progress-bar {
    margin-bottom: 12px;
  }

  .detail-text {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 13px;
    color: var(--el-text-color-secondary);

    .processing-hint {
      animation: blink 1.2s ease-in-out infinite;
    }
  }

  .max-rows-hint {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    margin-top: 12px;
    font-size: 12px;
    color: var(--el-color-warning);

    .hint-icon {
      width: 14px;
      height: 14px;
      flex-shrink: 0;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.4;
  }
}
</style>
