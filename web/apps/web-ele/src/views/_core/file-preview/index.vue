<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { ArrowLeft, Download } from '@vben/icons';
import { $t } from '@vben/locales';

import VueOfficeDocx from '@vue-office/docx';
import VueOfficeExcel from '@vue-office/excel';
import VueOfficePdf from '@vue-office/pdf';
import VueOfficePptx from '@vue-office/pptx';
import { ElButton, ElMessage } from 'element-plus';

import { getFileTypeIcon } from '#/assets/file-icons';
import { getFileUrl } from '#/composables/useFileUrl';

import '@vue-office/docx/lib/index.css';
import '@vue-office/excel/lib/index.css';

const route = useRoute();

const fileId = computed(() => route.params.id as string);
const fileName = computed(() => (route.query.name as string) || '');
const fileExt = computed(() => (route.query.ext as string) || '');

const loading = ref(false);
const fileBuffer = ref<ArrayBuffer | null>(null);
const textContent = ref('');
const fileUrl = ref('');
const errorMsg = ref('');

// 文件类型分类
const EXT_PDF = new Set(['pdf']);
const EXT_WORD = new Set(['doc', 'docx']);
const EXT_EXCEL = new Set(['xls', 'xlsx']);
const EXT_PPT = new Set(['ppt', 'pptx']);
const EXT_TEXT = new Set([
  'bash',
  'bat',
  'c',
  'cfg',
  'cmake',
  'cmd',
  'conf',
  'cpp',
  'cs',
  'css',
  'csv',
  'dockerfile',
  'editorconfig',
  'env',
  'fish',
  'gitignore',
  'go',
  'graphql',
  'h',
  'hpp',
  'htm',
  'html',
  'ini',
  'java',
  'js',
  'json',
  'jsx',
  'kt',
  'less',
  'log',
  'lua',
  'makefile',
  'md',
  'php',
  'pl',
  'prettierrc',
  'proto',
  'ps1',
  'py',
  'r',
  'rb',
  'rs',
  'sass',
  'scala',
  'scss',
  'sh',
  'sql',
  'styl',
  'svelte',
  'swift',
  'toml',
  'ts',
  'tsx',
  'txt',
  'vue',
  'xml',
  'yaml',
  'yml',
  'zsh',
]);

const normalizedExt = computed(() => {
  return fileExt.value.toLowerCase().replace('.', '');
});

const previewType = computed<
  'excel' | 'none' | 'pdf' | 'ppt' | 'text' | 'word'
>(() => {
  const ext = normalizedExt.value;
  if (!ext) return 'none';
  if (EXT_PDF.has(ext)) return 'pdf';
  if (EXT_WORD.has(ext)) return 'word';
  if (EXT_EXCEL.has(ext)) return 'excel';
  if (EXT_PPT.has(ext)) return 'ppt';
  if (EXT_TEXT.has(ext)) return 'text';
  return 'none';
});

const canPreview = computed(() => previewType.value !== 'none');

async function loadFile() {
  if (!fileId.value) return;

  loading.value = true;
  errorMsg.value = '';
  fileBuffer.value = null;
  textContent.value = '';
  fileUrl.value = '';

  try {
    const url = await getFileUrl(fileId.value);
    fileUrl.value = url;

    if (previewType.value === 'text') {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      textContent.value = await resp.text();
    } else if (previewType.value !== 'none') {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      fileBuffer.value = await resp.arrayBuffer();
    }
  } catch (error: any) {
    console.error('File preview load error:', error);
    errorMsg.value = error?.message || String(error);
  } finally {
    loading.value = false;
  }
}

async function handleDownload() {
  if (!fileUrl.value) return;
  try {
    const resp = await fetch(fileUrl.value);
    const blob = await resp.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = fileName.value || 'download';
    document.body.append(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  } catch {
    ElMessage.error($t('file-manager.downloadFailed'));
  }
}

function handleBack() {
  window.close();
}

function onRenderError(err: any) {
  console.error('vue-office render error:', err);
  errorMsg.value = $t('file-manager.previewRenderError');
}

onMounted(() => {
  document.title = fileName.value || $t('file-manager.filePreview');
  loadFile();
});
</script>

<template>
  <div class="flex h-screen w-screen flex-col bg-[var(--el-bg-color)]">
    <!-- 顶部工具栏 -->
    <div
      class="flex h-12 flex-shrink-0 items-center justify-between border-b border-[var(--el-border-color)] px-4"
    >
      <div class="flex items-center gap-3">
        <ElButton text circle size="small" @click="handleBack">
          <ArrowLeft class="size-4" />
        </ElButton>
        <img :src="getFileTypeIcon(fileExt)" class="size-5" />
        <span
          class="max-w-[50vw] truncate text-sm font-medium text-[var(--el-text-color-primary)]"
        >
          {{ fileName }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <ElButton v-if="fileUrl" size="small" @click="handleDownload">
          <Download class="mr-1 size-4" />
          {{ $t('file-manager.download') }}
        </ElButton>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="flex flex-1 items-center justify-center overflow-hidden">
      <!-- Loading -->
      <div v-if="loading" class="text-[var(--el-text-color-secondary)]">
        {{ $t('common.loading') }}...
      </div>

      <!-- Error -->
      <div v-else-if="errorMsg" class="max-w-md text-center">
        <p class="mb-2 text-lg text-[var(--el-color-danger)]">
          {{ $t('file-manager.previewFailed') }}
        </p>
        <p class="text-sm text-[var(--el-text-color-secondary)]">
          {{ errorMsg }}
        </p>
      </div>

      <!-- 不支持预览 -->
      <div v-else-if="!canPreview" class="text-center">
        <img :src="getFileTypeIcon(fileExt)" class="mx-auto mb-4 size-20" />
        <p class="mb-4 text-lg text-[var(--el-text-color-secondary)]">
          {{ $t('file-manager.previewNotSupported') }}
        </p>
        <ElButton v-if="fileUrl" type="primary" @click="handleDownload">
          <Download class="mr-1 size-4" />
          {{ $t('file-manager.download') }}
        </ElButton>
      </div>

      <!-- PDF -->
      <div
        v-else-if="previewType === 'pdf' && fileBuffer"
        class="h-full w-full overflow-auto"
      >
        <VueOfficePdf :src="fileBuffer" @error="onRenderError" />
      </div>

      <!-- Word -->
      <div
        v-else-if="previewType === 'word' && fileBuffer"
        class="h-full w-full overflow-auto bg-white p-4 dark:bg-[var(--el-bg-color)]"
      >
        <VueOfficeDocx :src="fileBuffer" @error="onRenderError" />
      </div>

      <!-- Excel -->
      <div
        v-else-if="previewType === 'excel' && fileBuffer"
        class="h-full w-full overflow-auto"
      >
        <VueOfficeExcel :src="fileBuffer" @error="onRenderError" />
      </div>

      <!-- PPT -->
      <div
        v-else-if="previewType === 'ppt' && fileBuffer"
        class="h-full w-full overflow-auto"
      >
        <VueOfficePptx
          :src="fileBuffer"
          style="height: 100%"
          @error="onRenderError"
        />
      </div>

      <!-- 文本/代码 -->
      <div
        v-else-if="previewType === 'text'"
        class="h-full w-full overflow-auto p-6"
      >
        <pre
          class="whitespace-pre-wrap break-words font-mono text-sm text-[var(--el-text-color-primary)]"
          >{{ textContent }}</pre>
      </div>
    </div>
  </div>
</template>
