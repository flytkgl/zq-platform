<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { useI18n } from '@vben/locales';

import { ZqDialog } from '#/components/zq-dialog';
import {
  AlertCircle,
  CheckCircle,
  Download,
  FileSpreadsheet,
  Layers,
  RefreshCw,
  Upload,
  XCircle,
} from '@vben/icons';

import {
  ElAlert,
  ElButton,
  ElMessageBox,
  ElOption,
  ElProgress,
  ElRadio,
  ElRadioGroup,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTooltip,
  ElUpload,
} from 'element-plus';

import type {
  ImportCompletedData,
  ImportOptions,
  ImportProgressData,
  ImportResult,
  ValidateCompletedData,
  ValidateProgressData,
} from '#/api/online-dev/form-data-api';

import {
  downloadImportTemplate,
  getImportExportConfigApi,
  importFormDataSSE,
  validateFormDataSSE,
} from '#/api/online-dev/form-data-api';

const props = defineProps<{
  formCode: string;
  formFields?: Array<{ field: string; label: string }>; // 表单字段列表（用于匹配字段选择）
}>();

const emit = defineEmits<{
  success: [];
}>();

const { t } = useI18n();

// 服务器导入导出配置
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

// 对话框状态
const visible = defineModel<boolean>('visible', { default: false });

// 导入模式
const importMode = ref<'append' | 'overwrite'>('append');
// 数据处理方式（追加模式下有效）
const dataHandling = ref<'insert_only' | 'update_only' | 'upsert'>('insert_only');
// 匹配字段（更新/upsert 模式下需要）
const matchField = ref<string>('');

// 是否需要匹配字段
const needMatchField = computed(() => {
  return importMode.value === 'append' && (dataHandling.value === 'update_only' || dataHandling.value === 'upsert');
});

// 步骤状态
type Step = 'select' | 'validating' | 'result' | 'importing';
const currentStep = ref<Step>('select');

// 文件
const selectedFile = ref<File | null>(null);

// 验证/导入结果
const validationResult = ref<ImportResult | null>(null);
const importResult = ref<ImportResult | null>(null);

// 加载状态
const loading = ref(false);

// 验证进度状态（SSE）
const validateProgress = ref(0);
const validateProcessed = ref(0);
const validateTotal = ref(0);

// 导入进度状态（SSE）
// 当前 SSE 任务的 abort 函数
let currentAbort: (() => void) | null = null;

type ImportStage = 'importing' | 'parsing' | 'validating';
const importProgress = ref(0);
const importStage = ref<ImportStage>('parsing');
const importProcessed = ref(0);
const importTotal = ref(0);
const importSuccessCount = ref(0);
const importFailCount = ref(0);

// 计算属性
const hasErrors = computed(() => {
  return (validationResult.value?.errors?.length ?? 0) > 0;
});

const canImport = computed(() => {
  return (
    validationResult.value &&
    validationResult.value.success > 0 &&
    !loading.value
  );
});

const validateProgressText = computed(() => {
  if (validateProgress.value > 60) {
    return t('common.importValidatingData');
  }
  if (validateTotal.value > 0) {
    return t('common.importValidating', [validateProcessed.value, validateTotal.value]);
  }
  return t('common.validatePreparing');
});

const importProgressText = computed(() => {
  if (importStage.value === 'parsing') {
    if (importTotal.value > 0) {
      return t('common.importParsing', [importProcessed.value, importTotal.value]);
    }
    return t('common.importPreparing');
  }
  if (importStage.value === 'validating') {
    return t('common.importValidatingData');
  }
  if (importTotal.value > 0) {
    return t('common.importImporting', [importProcessed.value, importTotal.value]);
  }
  return t('common.importImporting', [0, 0]);
});

const isProcessing = computed(() => {
  return currentStep.value === 'validating' || currentStep.value === 'importing';
});

function abortCurrentTask() {
  if (currentAbort) {
    currentAbort();
    currentAbort = null;
  }
}

function handleBeforeClose(done: () => void) {
  if (isProcessing.value) {
    ElMessageBox.confirm(
      t('common.closeConfirmMessage'),
      t('common.closeConfirmTitle'),
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

// 方法
function handleClose() {
  if (isProcessing.value) {
    ElMessageBox.confirm(
      t('common.closeConfirmMessage'),
      t('common.closeConfirmTitle'),
      { type: 'warning' },
    ).then(() => {
      abortCurrentTask();
      visible.value = false;
      resetState();
    }).catch(() => {});
  } else {
    visible.value = false;
    resetState();
  }
}

function resetState() {
  currentAbort = null;
  currentStep.value = 'select';
  selectedFile.value = null;
  validationResult.value = null;
  importResult.value = null;
  loading.value = false;
  importMode.value = 'append';
  dataHandling.value = 'insert_only';
  matchField.value = '';
  validateProgress.value = 0;
  validateProcessed.value = 0;
  validateTotal.value = 0;
  importProgress.value = 0;
  importStage.value = 'parsing';
  importProcessed.value = 0;
  importTotal.value = 0;
  importSuccessCount.value = 0;
  importFailCount.value = 0;
}

function handleFileChange(file: any) {
  selectedFile.value = file.raw;
  return false; // 阻止自动上传
}

async function handleDownloadTemplate() {
  try {
    await downloadImportTemplate(props.formCode);
  } catch {
    // 错误已在 API 层处理
  }
}

function buildImportOptions(validateOnly: boolean): ImportOptions {
  const options: ImportOptions = {
    mode: importMode.value,
    validateOnly,
  };
  if (importMode.value === 'append') {
    options.dataHandling = dataHandling.value;
    if (needMatchField.value && matchField.value) {
      options.matchField = matchField.value;
    }
  }
  return options;
}

async function handleValidate() {
  if (!selectedFile.value) return;
  if (needMatchField.value && !matchField.value) return;

  loading.value = true;
  currentStep.value = 'validating';
  validateProgress.value = 0;
  validateProcessed.value = 0;
  validateTotal.value = 0;

  const options = buildImportOptions(true);

  try {
    const { abort, promise } = validateFormDataSSE(
      props.formCode,
      selectedFile.value,
      options,
      {
        onProgress(data: ValidateProgressData) {
          validateProgress.value = data.percent;
          validateProcessed.value = data.processed;
          validateTotal.value = data.total;
        },
        onCompleted(data: ValidateCompletedData) {
          validateProgress.value = 100;
          validationResult.value = {
            success: data.success,
            fail: data.fail,
            errors: data.errors,
            message: data.message,
            will_insert: data.will_insert,
            will_update: data.will_update,
            action: data.action,
          };
          currentStep.value = 'result';
          loading.value = false;
        },
        onError(message: string) {
          validationResult.value = {
            errors: [{ error: message, row: 0 }],
            fail: 1,
            message,
            success: 0,
          };
          currentStep.value = 'result';
          loading.value = false;
        },
      },
    );
    currentAbort = abort;
    await promise;
  } catch (error: any) {
    validationResult.value = {
      errors: [{ error: error.message || '验证失败', row: 0 }],
      fail: 1,
      message: error.message || '验证失败',
      success: 0,
    };
    currentStep.value = 'result';
  } finally {
    loading.value = false;
  }
}

async function handleImport() {
  if (!selectedFile.value) return;

  loading.value = true;
  currentStep.value = 'importing';
  importProgress.value = 0;
  importStage.value = 'parsing';
  importProcessed.value = 0;
  importTotal.value = 0;
  importSuccessCount.value = 0;
  importFailCount.value = 0;

  const options = buildImportOptions(false);

  try {
    const { abort, promise } = importFormDataSSE(
      props.formCode,
      selectedFile.value,
      options,
      {
        onProgress(data: ImportProgressData) {
          importProgress.value = data.percent;
          importStage.value = data.stage;
          importProcessed.value = data.processed;
          importTotal.value = data.total;
          importSuccessCount.value = data.success;
          importFailCount.value = data.fail;
        },
        onCompleted(data: ImportCompletedData) {
          importProgress.value = 100;
          importResult.value = {
            success: data.success,
            fail: data.fail,
            errors: data.errors,
            message: data.message,
          };
          currentStep.value = 'result';
          loading.value = false;
          if (data.success > 0) {
            emit('success');
          }
        },
        onError(message: string) {
          importResult.value = {
            errors: [{ error: message, row: 0 }],
            fail: 1,
            message,
            success: 0,
          };
          currentStep.value = 'result';
          loading.value = false;
        },
      },
    );
    currentAbort = abort;
    await promise;
  } catch (error: any) {
    if (currentStep.value === 'importing') {
      importResult.value = {
        errors: [{ error: error.message || t('common.importFailed'), row: 0 }],
        fail: 1,
        message: error.message || t('common.importFailed'),
        success: 0,
      };
      currentStep.value = 'result';
    }
  } finally {
    loading.value = false;
  }
}

function handleBack() {
  currentStep.value = 'select';
  validationResult.value = null;
  importResult.value = null;
}

// 暴露方法
function open() {
  resetState();
  visible.value = true;
}

defineExpose({ open });
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="t('form-manager.formData.import.title')"
    width="600px"
    :close-on-click-modal="false"
    :before-close="handleBeforeClose"
    :showFullscreenButton="false"
  >
    <!-- 步骤1：选择模式和文件 -->
    <div v-if="currentStep === 'select'" class="import-select">
      <!-- 第一行：导入模式选择（追加/覆盖） -->
      <div class="mode-section">
        <ElRadioGroup v-model="importMode" class="mode-row-group">
          <div
            class="mode-card-inline"
            :class="{ active: importMode === 'append' }"
            @click="importMode = 'append'"
          >
            <ElRadio value="append" class="mode-radio">
              <div class="mode-content-inline">
                <div class="mode-icon-small append-icon">
                  <Layers class="icon" />
                </div>
                <div class="mode-info-inline">
                  <div class="mode-name">{{ t('form-manager.formData.import.appendMode') }}</div>
                  <div class="mode-desc">{{ t('form-manager.formData.import.appendModeDesc') }}</div>
                </div>
              </div>
            </ElRadio>
          </div>
          <div
            class="mode-card-inline"
            :class="{ active: importMode === 'overwrite' }"
            @click="importMode = 'overwrite'"
          >
            <ElRadio value="overwrite" class="mode-radio">
              <div class="mode-content-inline">
                <div class="mode-icon-small overwrite-icon">
                  <RefreshCw class="icon" />
                </div>
                <div class="mode-info-inline">
                  <div class="mode-name">{{ t('form-manager.formData.import.overwriteMode') }}</div>
                  <div class="mode-desc">{{ t('form-manager.formData.import.overwriteModeDesc') }}</div>
                </div>
              </div>
            </ElRadio>
          </div>
        </ElRadioGroup>
      </div>

      <!-- 第二行：数据处理方式（仅追加模式下显示） -->
      <div v-if="importMode === 'append'" class="handling-section">
        <div class="section-title">{{ t('form-manager.formData.import.dataHandling') }}</div>
        <ElRadioGroup v-model="dataHandling" class="handling-radio-group">
          <ElTooltip :content="t('form-manager.formData.import.insertOnlyDesc')" placement="top" :show-after="300" :disabled="false">
            <div
              class="handling-card"
              :class="{ active: dataHandling === 'insert_only' }"
              @click="dataHandling = 'insert_only'"
            >
              <ElRadio value="insert_only" class="handling-radio">
                <div class="handling-info">
                  <div class="handling-name">{{ t('form-manager.formData.import.insertOnly') }}</div>
                  <div class="handling-desc">{{ t('form-manager.formData.import.insertOnlyDesc') }}</div>
                </div>
              </ElRadio>
            </div>
          </ElTooltip>
          <ElTooltip :content="t('form-manager.formData.import.updateOnlyDesc')" placement="top" :show-after="300" :disabled="false">
            <div
              class="handling-card"
              :class="{ active: dataHandling === 'update_only' }"
              @click="dataHandling = 'update_only'"
            >
              <ElRadio value="update_only" class="handling-radio">
                <div class="handling-info">
                  <div class="handling-name">{{ t('form-manager.formData.import.updateOnly') }}</div>
                  <div class="handling-desc">{{ t('form-manager.formData.import.updateOnlyDesc') }}</div>
                </div>
              </ElRadio>
            </div>
          </ElTooltip>
          <ElTooltip :content="t('form-manager.formData.import.upsertDesc')" placement="top" :show-after="300" :disabled="false">
            <div
              class="handling-card"
              :class="{ active: dataHandling === 'upsert' }"
              @click="dataHandling = 'upsert'"
            >
              <ElRadio value="upsert" class="handling-radio">
                <div class="handling-info">
                  <div class="handling-name">{{ t('form-manager.formData.import.upsert') }}</div>
                  <div class="handling-desc">{{ t('form-manager.formData.import.upsertDesc') }}</div>
                </div>
              </ElRadio>
            </div>
          </ElTooltip>
        </ElRadioGroup>

        <!-- 匹配字段选择（更新/upsert 模式下显示） -->
        <div v-if="needMatchField" class="match-field-section">
          <div class="match-field-label">{{ t('form-manager.formData.import.matchField') }}</div>
          <ElSelect
            v-model="matchField"
            :placeholder="t('form-manager.formData.import.matchFieldPlaceholder')"
            filterable
            class="match-field-select"
          >
            <ElOption
              v-for="field in formFields"
              :key="field.field"
              :label="field.label"
              :value="field.field"
            />
          </ElSelect>
        </div>
      </div>

      <!-- 覆盖模式警告 -->
      <ElAlert
        v-if="importMode === 'overwrite'"
        type="warning"
        :closable="false"
        show-icon
        class="overwrite-warning"
      >
        <template #title>
          {{ t('form-manager.formData.import.overwriteWarning') }}
        </template>
      </ElAlert>

      <!-- 文件上传 -->
      <div class="upload-section">
        <ElUpload
          class="file-upload"
          drag
          :auto-upload="false"
          :show-file-list="false"
          accept=".xlsx"
          :on-change="handleFileChange"
        >
          <div class="upload-content">
            <FileSpreadsheet class="upload-icon" />
            <div class="upload-text">
              <span v-if="selectedFile">{{ selectedFile.name }}</span>
              <span v-else>{{ t('form-manager.formData.import.dragOrClick') }}</span>
            </div>
            <div class="upload-hint">{{ t('form-manager.formData.import.onlyXlsx') }}</div>
          </div>
        </ElUpload>

        <!-- 下载模板 -->
        <div class="template-link">
          <ElButton link type="primary" @click="handleDownloadTemplate">
            <Download class="mr-1 size-4" />
            {{ t('form-manager.formData.import.downloadTemplate') }}
          </ElButton>
        </div>

        <div v-if="maxRows > 0" class="max-rows-hint">
          <AlertCircle class="hint-icon" />
          <span>{{ t('common.maxImportRows', [maxRowsText]) }}</span>
        </div>
      </div>
    </div>

    <!-- 步骤2：验证中 -->
    <div v-else-if="currentStep === 'validating'" class="import-validating">
      <div class="validating-content">
        <div class="validating-status-text">{{ validateProgressText }}</div>
        <ElProgress :percentage="validateProgress" :stroke-width="16" :text-inside="true" class="validating-progress-bar" />
        <div v-if="validateTotal > 0" class="validating-detail">
          <span>{{ validateProcessed }} / {{ validateTotal }} {{ t('common.records') }}</span>
        </div>
      </div>
    </div>

    <!-- 步骤3：导入中 -->
    <div v-else-if="currentStep === 'importing'" class="import-importing">
      <div class="importing-content">
        <div class="importing-status-text">{{ importProgressText }}</div>
        <ElProgress
          :percentage="importProgress"
          :stroke-width="16"
          :text-inside="true"
          class="importing-progress-bar"
        />
        <div v-if="importTotal > 0" class="importing-detail">
          <span>{{ importProcessed }} / {{ importTotal }} {{ t('common.records') }}</span>
          <span class="importing-stats">
            <span class="stat-success">{{ t('common.success') }}: {{ importSuccessCount }}</span>
            <span class="stat-fail">{{ t('common.importFailed') }}: {{ importFailCount }}</span>
          </span>
        </div>
      </div>
    </div>

    <!-- 步骤4：结果展示 -->
    <div v-else-if="currentStep === 'result'" class="import-result">
      <!-- 验证结果 -->
      <template v-if="validationResult && !importResult">
        <div class="result-summary">
          <div class="result-item success">
            <CheckCircle class="result-icon" />
            <span class="result-count">{{ validationResult.success }}</span>
            <span class="result-label">{{
              t('form-manager.formData.import.passCount')
            }}</span>
          </div>
          <div class="result-item error">
            <XCircle class="result-icon" />
            <span class="result-count">{{ validationResult.fail }}</span>
            <span class="result-label">{{
              t('form-manager.formData.import.failCount')
            }}</span>
          </div>
        </div>

        <!-- 操作预估 -->
        <div v-if="validationResult.success > 0" class="action-preview">
          <Layers class="mr-1 size-4" />
          <span v-if="validationResult.action === 'overwrite'">
            {{ t('common.willOverwrite', [validationResult.will_insert]) }}
          </span>
          <span v-else-if="validationResult.action === 'insert_only'">
            {{ t('common.willInsert', [validationResult.will_insert]) }}
          </span>
          <span v-else-if="validationResult.action === 'update_only'">
            {{ t('common.willUpdate', [validationResult.will_update]) }}
          </span>
          <span v-else-if="validationResult.action === 'upsert'">
            {{ t('common.willInsert', [validationResult.will_insert]) }}{{ t('common.comma') }}{{ t('common.willUpdate', [validationResult.will_update]) }}
          </span>
        </div>

        <!-- 错误列表 -->
        <div v-if="hasErrors" class="error-list">
          <div class="error-title">
            <AlertCircle class="mr-1 size-4" />
            {{ t('form-manager.formData.import.errorList') }}
          </div>
          <ElTable
            :data="validationResult.errors"
            max-height="300"
            size="small"
          >
            <ElTableColumn
              prop="row"
              :label="t('form-manager.formData.import.rowNumber')"
              width="80"
            />
            <ElTableColumn prop="error" :label="t('form-manager.formData.import.errorMsg')">
              <template #default="{ row }">
                <span class="error-text">{{ row.error }}</span>
              </template>
            </ElTableColumn>
          </ElTable>
        </div>

        <!-- 无错误提示 -->
        <ElAlert
          v-else
          type="success"
          :closable="false"
          show-icon
          class="success-alert"
        >
          <template #title>
            {{ t('form-manager.formData.import.allPassed') }}
          </template>
        </ElAlert>
      </template>

      <!-- 导入结果 -->
      <template v-if="importResult">
        <div class="result-summary">
          <div class="result-item success">
            <CheckCircle class="result-icon" />
            <span class="result-count">{{ importResult.success }}</span>
            <span class="result-label">{{
              t('form-manager.formData.import.importedCount')
            }}</span>
          </div>
          <div class="result-item error">
            <XCircle class="result-icon" />
            <span class="result-count">{{ importResult.fail }}</span>
            <span class="result-label">{{
              t('form-manager.formData.import.failCount')
            }}</span>
          </div>
        </div>

        <!-- 导入错误列表 -->
        <div v-if="importResult.errors?.length" class="error-list">
          <div class="error-title">
            <AlertCircle class="mr-1 size-4" />
            {{ t('form-manager.formData.import.errorList') }}
          </div>
          <ElTable :data="importResult.errors" max-height="300" size="small">
            <ElTableColumn
              prop="row"
              :label="t('form-manager.formData.import.rowNumber')"
              width="80"
            />
            <ElTableColumn prop="error" :label="t('form-manager.formData.import.errorMsg')">
              <template #default="{ row }">
                <span class="error-text">{{ row.error }}</span>
              </template>
            </ElTableColumn>
          </ElTable>
        </div>

        <!-- 导入成功提示 -->
        <ElAlert
          v-else
          type="success"
          :closable="false"
          show-icon
          class="success-alert"
        >
          <template #title>
            {{ t('form-manager.formData.import.importSuccess') }}
          </template>
        </ElAlert>
      </template>
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <div class="dialog-footer">
        <!-- 选择步骤 -->
        <template v-if="currentStep === 'select'">
          <ElButton @click="handleClose">{{ t('common.cancel') }}</ElButton>
          <ElButton
            type="primary"
            :disabled="!selectedFile || (needMatchField && !matchField)"
            @click="handleValidate"
          >
            <Upload class="mr-1 size-4" />
            {{ t('form-manager.formData.import.validateAndUpload') }}
          </ElButton>
        </template>

        <!-- 验证结果步骤 -->
        <template v-else-if="currentStep === 'result' && !importResult">
          <ElButton @click="handleBack">{{
            t('form-manager.formData.import.reselect')
          }}</ElButton>
          <ElButton type="primary" :disabled="!canImport" @click="handleImport">
            {{ t('form-manager.formData.import.confirmImport') }}
          </ElButton>
        </template>

        <!-- 导入结果步骤 -->
        <template v-else-if="currentStep === 'result' && importResult">
          <ElButton type="primary" @click="handleClose">{{
            t('common.close')
          }}</ElButton>
        </template>
      </div>
    </template>
  </ZqDialog>
</template>

<style scoped lang="scss">
.import-select {
  .section-title {
    margin-bottom: 12px;
    font-size: 14px;
    font-weight: 500;
    color: var(--el-text-color-primary);
  }

  .mode-section {
    margin-bottom: 16px;
  }

  .mode-row-group {
    display: flex;
    flex-direction: row;
    gap: 12px;
    width: 100%;
  }

  .mode-card-inline {
    flex: 1;
    padding: 14px;
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      border-color: var(--el-color-primary-light-5);
    }

    &.active {
      border-color: var(--el-color-primary);
      background-color: var(--el-color-primary-light-9);
    }

    .mode-radio {
      width: 100%;
      height: auto;

      :deep(.el-radio__label) {
        width: 100%;
        padding-left: 8px;
      }
    }

    .mode-content-inline {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .mode-icon-small {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      border-radius: 8px;
      flex-shrink: 0;

      .icon {
        width: 18px;
        height: 18px;
        color: #fff;
      }

      &.append-icon {
        background: linear-gradient(135deg, #67c23a, #85ce61);
      }

      &.overwrite-icon {
        background: linear-gradient(135deg, #e6a23c, #f0c78a);
      }
    }

    .mode-info-inline {
      flex: 1;
      min-width: 0;

      .mode-name {
        font-size: 14px;
        font-weight: 500;
        color: var(--el-text-color-primary);
      }

      .mode-desc {
        margin-top: 2px;
        font-size: 12px;
        color: var(--el-text-color-secondary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }

  .handling-section {
    margin-bottom: 16px;
  }

  .handling-radio-group {
    display: flex;
    flex-direction: row;
    gap: 8px;
    width: 100%;

    > :deep(.el-tooltip__trigger) {
      flex: 1;
      min-width: 0;
    }
  }

  .handling-card {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      border-color: var(--el-color-primary-light-5);
    }

    &.active {
      border-color: var(--el-color-primary);
      background-color: var(--el-color-primary-light-9);
    }

    .handling-radio {
      width: 100%;
      height: auto;

      :deep(.el-radio__label) {
        padding-left: 6px;
        width: calc(100% - 20px);
      }
    }

    .handling-info {
      .handling-name {
        font-size: 13px;
        font-weight: 500;
        color: var(--el-text-color-primary);
      }

      .handling-desc {
        margin-top: 2px;
        font-size: 11px;
        color: var(--el-text-color-secondary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }

  .match-field-section {
    margin-top: 12px;
    padding: 12px 16px;
    background-color: var(--el-fill-color-light);
    border-radius: 8px;

    .match-field-label {
      margin-bottom: 8px;
      font-size: 13px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }

    .match-field-select {
      width: 100%;
    }
  }

  .overwrite-warning {
    margin-bottom: 16px;
  }

  .upload-section {
    .file-upload {
      width: 100%;

      :deep(.el-upload) {
        width: 100%;
      }

      :deep(.el-upload-dragger) {
        width: 100%;
        padding: 24px 20px;
      }
    }

    .upload-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;

      .upload-icon {
        width: 40px;
        height: 40px;
        color: var(--el-color-primary);
      }

      .upload-text {
        font-size: 14px;
        color: var(--el-text-color-primary);
      }

      .upload-hint {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }

    .template-link {
      margin-top: 12px;
      text-align: center;
    }

    .max-rows-hint {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      margin-top: 8px;
      font-size: 12px;
      color: var(--el-color-warning);

      .hint-icon {
        width: 14px;
        height: 14px;
        flex-shrink: 0;
      }
    }
  }
}

.import-validating {
  padding: 24px 20px;

  .validating-content {
    display: flex;
    flex-direction: column;
    gap: 16px;

    .validating-status-text {
      font-size: 15px;
      font-weight: 500;
      text-align: center;
      color: var(--el-text-color-primary);
    }

    .validating-progress-bar {
      width: 100%;
    }

    .validating-detail {
      display: flex;
      justify-content: center;
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }
  }
}

.import-importing {
  padding: 24px 20px;

  .importing-content {
    display: flex;
    flex-direction: column;
    gap: 16px;

    .importing-status-text {
      font-size: 15px;
      font-weight: 500;
      text-align: center;
      color: var(--el-text-color-primary);
    }

    .importing-progress-bar {
      margin: 4px 0;
    }

    .importing-detail {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 13px;
      color: var(--el-text-color-secondary);

      .importing-stats {
        display: flex;
        gap: 12px;

        .stat-success {
          color: var(--el-color-success);
        }

        .stat-fail {
          color: var(--el-color-danger);
        }
      }
    }
  }
}

.import-result {
  .result-summary {
    display: flex;
    justify-content: center;
    gap: 48px;
    padding: 24px 0;
    margin-bottom: 20px;
    background-color: var(--el-fill-color-light);
    border-radius: 8px;

    .result-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;

      .result-icon {
        width: 32px;
        height: 32px;
      }

      .result-count {
        font-size: 28px;
        font-weight: 600;
      }

      .result-label {
        font-size: 13px;
        color: var(--el-text-color-secondary);
      }

      &.success {
        .result-icon,
        .result-count {
          color: var(--el-color-success);
        }
      }

      &.error {
        .result-icon,
        .result-count {
          color: var(--el-color-danger);
        }
      }
    }
  }

  .action-preview {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px 16px;
    margin-bottom: 16px;
    font-size: 14px;
    color: var(--el-color-primary);
    background-color: var(--el-color-primary-light-9);
    border-radius: 6px;
  }

  .error-list {
    .error-title {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      font-size: 14px;
      font-weight: 500;
      color: var(--el-color-danger);
    }

    .error-text {
      color: var(--el-color-danger);
    }
  }

  .success-alert {
    margin-top: 20px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
