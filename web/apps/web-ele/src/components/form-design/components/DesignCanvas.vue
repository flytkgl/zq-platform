<script setup lang="ts">
import { $t } from '@vben/locales';
import { onMounted, onUnmounted, ref } from 'vue';
import { CircleHelp } from '@vben/icons';
import { ZqDialog } from '#/components/zq-dialog';

import {
  Back,
  Collection,
  Delete,
  Document,
  Download,
  Memo,
  Monitor,
  Plus,
  ReadingLamp,
  Right,
  Upload,
} from '@element-plus/icons-vue';
import {
  ElButton,
  ElDialog,
  ElForm,
  ElIcon,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElScrollbar,
  ElTag,
  ElTooltip,
} from 'element-plus';
import { storeToRefs } from 'pinia';
import draggable from 'vuedraggable';

import { useFormDesignStore } from '../store/formDesignStore';
import CodeModal from './CodeModal.vue';
import FormItemWrapper from './FormItemWrapper.vue';
import MobileFormPreview from './MobileFormPreview.vue';
import PreviewModal from './PreviewModal.vue';

const props = withDefaults(
  defineProps<{
    toolbars?: string[];
  }>(),
  {
    toolbars: () => [
      'undo',
      'redo',
      'import',
      'preview',
      'clear',
      'json',
      'saveTemplate',
    ],
  },
);

const store = useFormDesignStore();
const { formConf, activeId, isDragging, previewMode } = storeToRefs(store);
const previewRef = ref();
const codeModalRef = ref();

const importVisible = ref(false);
const importJson = ref('');
const jsonVisible = ref(false);
const saveTemplateVisible = ref(false);
const templateName = ref('');

const handleSelect = (item: any) => store.setActive(item.id);
const handleDelete = (id: string) => store.deleteItem(id);
const handleCanvasClick = () => store.setActive(null);

const handleAdd = (evt: any) => {
  const newIndex = evt.newIndex;
  const newItem = formConf.value.items[newIndex];
  if (newItem) {
    store.setActive(newItem.id);
  }
};

const handleImport = () => {
  importJson.value = '';
  importVisible.value = true;
};

const handleViewJson = () => {
  jsonVisible.value = true;
};

const handleSaveTemplate = () => {
  if (formConf.value.items.length === 0) {
    ElMessage.warning($t('form-design.material.noComponents'));
    return;
  }
  templateName.value = '';
  saveTemplateVisible.value = true;
};

const confirmSaveTemplate = () => {
  if (!templateName.value) {
    ElMessage.warning($t('form-design.message.importEmpty'));
    return;
  }
  store.addTemplate({
    title: templateName.value,
    icon: 'Document',
    items: JSON.parse(JSON.stringify(formConf.value.items)),
  });
  saveTemplateVisible.value = false;
  ElMessage.success($t('form-design.message.saveSuccess'));
};

const handleGenerateCode = () => {
  codeModalRef.value?.open(formConf.value);
};

const confirmImport = () => {
  try {
    const parsed = JSON.parse(importJson.value);
    if (typeof parsed !== 'object' || !parsed.items) {
      ElMessage.error($t('form-design.message.importError'));
      return;
    }
    // 简单的校验通过
    formConf.value = parsed;
    store.setActive(null);
    importVisible.value = false;
    ElMessage.success($t('form-design.message.importSuccess'));
  } catch {
    ElMessage.error($t('form-design.message.importError'));
  }
};

const handleClear = () => {
  ElMessageBox.confirm($t('form-design.message.clearConfirm'), $t('common.tips'), {
    type: 'warning',
  }).then(() => {
    formConf.value.items = [];
    store.setActive(null);
  });
};

const handlePreview = () => {
  previewRef.value?.open();
};

const handleSave = () => {
  ElMessage.success($t('form-design.message.exportSuccess'));
};

// 快捷键处理
const handleKeydown = (event: KeyboardEvent) => {
  // 如果焦点在输入框中，不处理快捷键
  const target = event.target as HTMLElement;
  if (
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.isContentEditable
  ) {
    return;
  }

  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const ctrlKey = isMac ? event.metaKey : event.ctrlKey;
  
  // Delete: 删除选中组件
  if (event.key === 'Delete' || event.key === 'Backspace') {
    if (activeId.value) {
      event.preventDefault();
      store.deleteSelected();
    }
    return;
  }
  
  // Ctrl+Z: 撤销
  if (ctrlKey && event.key === 'z' && !event.shiftKey) {
    event.preventDefault();
    store.undo();
    return;
  }
  
  // Ctrl+Y 或 Ctrl+Shift+Z: 重做
  if ((ctrlKey && event.key === 'y') || (ctrlKey && event.shiftKey && event.key === 'z')) {
    event.preventDefault();
    store.redo();
    return;
  }
  
  // Ctrl+C: 复制
  if (ctrlKey && event.key === 'c') {
    if (activeId.value) {
      event.preventDefault();
      store.copyToClipboard();
      ElMessage.success($t('form-design.message.copySuccess'));
    }
    return;
  }
  
  // Ctrl+V: 粘贴
  if (ctrlKey && event.key === 'v') {
    event.preventDefault();
    store.pasteFromClipboard();
    return;
  }
  
  // ↑: 上移组件
  if (event.key === 'ArrowUp' && activeId.value) {
    event.preventDefault();
    store.moveItem(activeId.value, 'up');
    return;
  }
  
  // ↓: 下移组件
  if (event.key === 'ArrowDown' && activeId.value) {
    event.preventDefault();
    store.moveItem(activeId.value, 'down');
    return;
  }
  
  // Escape: 取消选择
  if (event.key === 'Escape') {
    store.clearSelection();
    
  }
};

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});

const mobileHelpVisible = ref(false);
</script>

<template>
  <div
    class="design-canvas flex h-full flex-col bg-[var(--el-fill-color-light)]"
  >
    <div
      class="canvas-toolbar flex items-center justify-between rounded border-b border-[var(--el-border-color)] bg-[var(--el-bg-color)] px-4 py-2"
    >
      <div class="flex items-center space-x-2">
        <ElTooltip
          :content="$t('form-design.undo')"
          placement="bottom"
          v-if="toolbars.includes('undo')"
        >
          <ElButton
            size="small"
            link
            :disabled="!store.canUndo"
            @click="store.undo"
          >
            <ElIcon :size="16"><Back /></ElIcon>
          </ElButton>
        </ElTooltip>
        <ElTooltip
          :content="$t('form-design.redo')"
          placement="bottom"
          v-if="toolbars.includes('redo')"
        >
          <ElButton
            size="small"
            link
            :disabled="!store.canRedo"
            @click="store.redo"
          >
            <ElIcon :size="16"><Right /></ElIcon>
          </ElButton>
        </ElTooltip>
        <!-- PC / 移动端切换（移到左侧） -->
        <ElTooltip
          :content="previewMode === 'pc' ? $t('form-design.mobilePreview') : $t('form-design.pcPreview')"
          placement="bottom"
        >
          <ElButton size="small" link @click="store.togglePreviewMode">
            <ElIcon :size="16">
              <Monitor v-if="previewMode === 'mobile'" />
              <!-- 手机轮廓 SVG -->
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                <line x1="12" y1="18" x2="12.01" y2="18"/>
              </svg>
            </ElIcon>
          </ElButton>
        </ElTooltip>
        <template v-if="previewMode === 'mobile'">
          <span class="ml-2 text-xs text-[var(--el-text-color-secondary)]">{{ $t('form-design.mobilePreviewTip') }}</span>
          <ElTooltip :content="$t('form-design.mobileHelpLearnMore')" placement="bottom">
            <ElButton size="small" link class="ml-1" @click="mobileHelpVisible = true">
              <CircleHelp class="size-4 text-[var(--el-color-primary)]" />
            </ElButton>
          </ElTooltip>
        </template>
      </div>
      <div class="flex items-center space-x-1">
        <ElTooltip
          :content="$t('form-design.import')"
          placement="bottom"
          v-if="toolbars.includes('import')"
        >
          <ElButton size="small" text @click="handleImport">
            <ElIcon :size="16"><Upload /></ElIcon>
          </ElButton>
        </ElTooltip>
        <ElTooltip
          :content="$t('form-design.viewCode')"
          placement="bottom"
          v-if="toolbars.includes('json')"
        >
          <ElButton size="small" text @click="handleViewJson">
            <ElIcon :size="16"><Memo /></ElIcon>
          </ElButton>
        </ElTooltip>
        <ElTooltip
          :content="$t('form-design.attribute.layout.addPanel')"
          placement="bottom"
          v-if="toolbars.includes('saveTemplate')"
        >
          <ElButton size="small" text @click="handleSaveTemplate">
            <ElIcon :size="16"><Collection /></ElIcon>
          </ElButton>
        </ElTooltip>
        <ElTooltip
          :content="$t('form-design.viewCode')"
          placement="bottom"
          v-if="toolbars.includes('code')"
        >
          <ElButton size="small" text @click="handleGenerateCode">
            <ElIcon :size="16"><Document /></ElIcon>
          </ElButton>
        </ElTooltip>
        <ElTooltip
          :content="$t('form-design.previewLabel')"
          placement="bottom"
          v-if="toolbars.includes('preview')"
        >
          <ElButton size="small" text @click="handlePreview">
            <ElIcon :size="16"><ReadingLamp /></ElIcon>
          </ElButton>
        </ElTooltip>
        <ElTooltip
          :content="$t('form-design.save')"
          placement="bottom"
          v-if="toolbars.includes('save')"
        >
          <ElButton size="small" text @click="handleSave">
            <ElIcon :size="16"><Download /></ElIcon>
          </ElButton>
        </ElTooltip>
        <ElTooltip
          :content="$t('form-design.clear')"
          placement="bottom"
          v-if="toolbars.includes('clear')"
        >
          <ElButton size="small" text @click="handleClear">
            <ElIcon :size="16"><Delete /></ElIcon>
          </ElButton>
        </ElTooltip>
      </div>
    </div>

    <ElScrollbar class="canvas-body flex-1" view-class="h-full">
      <div
        class="flex min-h-full justify-center"
        :class="previewMode === 'mobile' ? 'items-start py-8' : ''"
        @click.self="handleCanvasClick"
      >
        <!-- 移动端手机外框 -->
        <div
          v-if="previewMode === 'mobile'"
          class="mobile-phone-frame relative flex-shrink-0"
        >
          <!-- 手机顶部刘海 -->
          <div class="mobile-phone-notch" />
          <!-- 手机顶部状态栏 -->
          <div class="mobile-phone-statusbar flex items-center justify-between px-5">
            <span class="text-xs font-semibold">9:41</span>
            <div class="flex items-center gap-1.5">
              <!-- 信号格 -->
              <svg width="16" height="12" viewBox="0 0 16 12" fill="currentColor">
                <rect x="0" y="8" width="3" height="4" rx="0.5"/>
                <rect x="4.5" y="5" width="3" height="7" rx="0.5"/>
                <rect x="9" y="2" width="3" height="10" rx="0.5"/>
                <rect x="13.5" y="0" width="2.5" height="12" rx="0.5"/>
              </svg>
              <!-- WiFi -->
              <svg width="14" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
                <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
                <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
                <circle cx="12" cy="20" r="1" fill="currentColor" stroke="none"/>
              </svg>
              <!-- 电池 -->
              <svg width="22" height="12" viewBox="0 0 22 12" fill="currentColor">
                <rect x="0" y="1" width="18" height="10" rx="2" fill="none" stroke="currentColor" stroke-width="1.2"/>
                <rect x="18.5" y="3.5" width="2" height="5" rx="1"/>
                <rect x="1.5" y="2.5" width="13" height="7" rx="1"/>
              </svg>
            </div>
          </div>
          <!-- 表单内容区（overflow-y-auto 实现真实滚动） -->
          <div class="mobile-phone-body">
            <!-- 移动端：仅预览，不支持拖拽 -->
            <MobileFormPreview v-if="formConf.items.length > 0" :items="formConf.items" />
            <div
              v-else
              class="flex flex-col items-center justify-center py-16"
            >
              <div
                class="flex h-[180px] w-[180px] flex-col items-center justify-center rounded-lg border-2 border-dashed p-8"
                :class="'border-[var(--el-border-color)] text-[var(--el-text-color-placeholder)]'"
              >
                <ElIcon :size="28" class="mb-2"><Plus /></ElIcon>
                <span class="text-xs">{{ $t('dashboard-design.dragTip') }}</span>
              </div>
            </div>
          </div>
          <!-- 手机底部安全区 -->
          <div class="mobile-phone-home" />
        </div>

        <!-- PC 模式（原有画布） -->
        <div v-else class="canvas-wrapper min-h-full w-full rounded-b p-8">
          <div
            :style="{
              padding: `${formConf.formPaddingTop ?? formConf.formPadding ?? 20}px ${formConf.formPaddingRight ?? formConf.formPadding ?? 20}px ${formConf.formPaddingBottom ?? formConf.formPadding ?? 20}px ${formConf.formPaddingLeft ?? formConf.formPadding ?? 20}px`,
              margin: `${formConf.formMarginTop ?? formConf.formMargin ?? 0}px ${formConf.formMarginRight ?? formConf.formMargin ?? 0}px ${formConf.formMarginBottom ?? formConf.formMargin ?? 0}px ${formConf.formMarginLeft ?? formConf.formMargin ?? 0}px`,
              width: formConf.formWidth || '100%',
              maxWidth: formConf.formMaxWidth || 'none',
              backgroundColor: formConf.formBackground || 'var(--el-bg-color)',
              border: formConf.formBorder ? '1px solid var(--el-border-color)' : 'none',
              borderRadius: formConf.formBorder ? `${formConf.formBorderRadius || 4}px` : '0',
              boxShadow: formConf.formShadow ? '0 2px 12px 0 rgba(0, 0, 0, 0.1)' : 'none',
              minHeight: '100%',
            }"
          >
            <ElForm
              :label-width="`${formConf.labelWidth}px`"
              :label-position="formConf.labelPosition"
              :size="formConf.size"
              :disabled="formConf.disabled || false"
              :style="{
                '--el-form-item-margin-bottom': `${formConf.itemSpacing || 18}px`,
              }"
              class="relative h-full"
            >
              <draggable
                v-model="formConf.items"
                group="form-design"
                item-key="id"
                class="canvas-area relative h-full min-h-[200px]"
                ghost-class="ghost"
                :animation="200"
                @add="handleAdd"
              >
                <template #item="{ element }">
                  <FormItemWrapper
                    :schema="element"
                    :active="activeId === element.id"
                    :preview-mode="previewMode"
                    @click="handleSelect(element)"
                    @delete="handleDelete"
                  />
                </template>
              </draggable>

              <div
                v-if="formConf.items.length === 0"
                class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center"
              >
                <div
                  class="flex h-[300px] w-[300px] flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors duration-300"
                  :class="[
                    isDragging
                      ? 'border-[var(--el-color-primary)] bg-[var(--el-color-primary-light-9)] text-[var(--el-color-primary)]'
                      : 'border-[var(--el-border-color)] text-[var(--el-text-color-placeholder)]',
                  ]"
                >
                  <ElIcon :size="40" class="mb-2"><Plus /></ElIcon>
                  <span>{{
                    isDragging ? $t('form-design.message.clearConfirm') : $t('dashboard-design.dragTip')
                  }}</span>
                </div>
              </div>
            </ElForm>
          </div>
        </div>
      </div>
    </ElScrollbar>

    <!-- 预览弹窗 -->
    <PreviewModal ref="previewRef" :conf="formConf" />

    <!-- 代码生成弹窗 -->
    <CodeModal ref="codeModalRef" />

    <!-- 导入弹窗 -->
    <ElDialog
      v-model="importVisible"
      :title="$t('form-design.message.importTitle')"
      width="600px"
      append-to-body
    >
      <div class="mb-2 text-xs text-gray-500">
        {{ $t('form-design.message.importPlaceholder') }}
      </div>
      <ElInput
        v-model="importJson"
        type="textarea"
        :rows="10"
        :placeholder="$t('form-design.message.importPlaceholder')"
      />
      <template #footer>
        <ElButton @click="importVisible = false">{{ $t('common.cancel') }}</ElButton>
        <ElButton type="primary" @click="confirmImport">{{ $t('form-design.import') }}</ElButton>
      </template>
    </ElDialog>

    <!-- 查看 JSON 弹窗 -->
    <ElDialog
      v-model="jsonVisible"
      :title="$t('form-design.viewCode')"
      width="600px"
      append-to-body
    >
      <ElInput
        :model-value="JSON.stringify(formConf, null, 2)"
        type="textarea"
        :rows="15"
        readonly
      />
      <template #footer>
        <ElButton type="primary" @click="jsonVisible = false">{{ $t('common.close') }}</ElButton>
      </template>
    </ElDialog>

    <!-- 保存模板弹窗 -->
    <ElDialog
      v-model="saveTemplateVisible"
      :title="$t('form-design.templateLabel')"
      width="400px"
      append-to-body
    >
      <div class="mb-2 text-xs text-gray-500">
        {{ $t('form-design.template.applyConfirm') }}
      </div>
      <ElInput
        v-model="templateName"
        :placeholder="$t('form-design.attribute.nodeLabel')"
        @keyup.enter="confirmSaveTemplate"
      />
      <template #footer>
        <ElButton @click="saveTemplateVisible = false">{{ $t('common.cancel') }}</ElButton>
        <ElButton type="primary" @click="confirmSaveTemplate">{{ $t('common.ok') }}</ElButton>
      </template>
    </ElDialog>

    <!-- 手机端渲染差异帮助弹窗 -->
    <ZqDialog
      v-model="mobileHelpVisible"
      :title="$t('form-design.mobileHelpTitle')"
      width="820px"
      :show-footer="false"
    >
      <div class="space-y-4 text-sm">
        <!-- 提示横幅 -->
        <div class="rounded-lg bg-[var(--el-color-primary-light-9)] px-4 py-3 text-[var(--el-color-primary)]">
          {{ $t('form-design.mobileHelp.previewOnlyTip') }}
        </div>

        <!-- 差异列表 -->
        <div
          v-for="item in (([
            { title: $t('form-design.mobileHelp.layoutTitle'), desc: $t('form-design.mobileHelp.layoutDesc'), tag: 'warning' },
            { title: $t('form-design.mobileHelp.selectTitle'), desc: $t('form-design.mobileHelp.selectDesc'), tag: 'info' },
            { title: $t('form-design.mobileHelp.dateTitle'), desc: $t('form-design.mobileHelp.dateDesc'), tag: 'info' },
            { title: $t('form-design.mobileHelp.numberTitle'), desc: $t('form-design.mobileHelp.numberDesc'), tag: 'info' },
            { title: $t('form-design.mobileHelp.radioCheckboxTitle'), desc: $t('form-design.mobileHelp.radioCheckboxDesc'), tag: 'info' },
            { title: $t('form-design.mobileHelp.richTextTitle'), desc: $t('form-design.mobileHelp.richTextDesc'), tag: 'warning' },
            { title: $t('form-design.mobileHelp.layoutDecorTitle'), desc: $t('form-design.mobileHelp.layoutDecorDesc'), tag: 'danger' },
            { title: $t('form-design.mobileHelp.subTableTitle'), desc: $t('form-design.mobileHelp.subTableDesc'), tag: 'info' },
            { title: $t('form-design.mobileHelp.selectorTitle'), desc: $t('form-design.mobileHelp.selectorDesc'), tag: 'success' },
            { title: $t('form-design.mobileHelp.tabsStepsTitle'), desc: $t('form-design.mobileHelp.tabsStepsDesc'), tag: 'success' },
          ] as Array<{ title: string; desc: string; tag: 'warning' | 'info' | 'danger' | 'success' }>))"
          :key="item.title"
          class="flex flex-col gap-3 rounded-lg border border-[var(--el-border-color-lighter)] p-3"
        >
          <div class="flex-shrink-0 pt-0.5">
            <ElTag :type="item.tag" size="small" effect="light">{{ item.title }}</ElTag>
          </div>
          <div class="text-[var(--el-text-color-regular)] leading-relaxed">{{ item.desc }}</div>
        </div>
      </div>
    </ZqDialog>
  </div>
</template>

<style scoped>
.ghost {
  position: relative;
  height: 4px;
  overflow: hidden;
  background: var(--el-color-primary-light-9);
  border-top: 2px solid var(--el-color-primary);
}

.ghost::after {
  display: block;
  content: '';
  background: var(--el-bg-color);
}

/* iPhone 手机外框 */
.mobile-phone-frame {
  width: 393px;
  background: var(--el-bg-color);
  border-radius: 54px;
  border: 10px solid #1c1c1e;
  box-shadow:
    0 0 0 1px #3a3a3c,
    0 30px 80px rgba(0, 0, 0, 0.4),
    inset 0 0 0 1px #3a3a3c;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: calc(100vh - 120px);
  max-height: 820px;
  min-height: 600px;
  flex-shrink: 0;
  position: relative;
}

/* 刘海 */
.mobile-phone-notch {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 126px;
  height: 34px;
  background: #1c1c1e;
  border-radius: 0 0 20px 20px;
  z-index: 10;
}

.mobile-phone-statusbar {
  background: var(--el-bg-color);
  font-size: 12px;
  color: var(--el-text-color-primary);
  flex-shrink: 0;
  height: 44px;
  padding-top: 10px;
}

/* 内容区：真实 overflow-y-auto 滚动，隐藏滚动条 */
.mobile-phone-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--el-fill-color-light);
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.mobile-phone-body::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.mobile-phone-home {
  height: 34px;
  background: var(--el-bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.mobile-phone-home::after {
  content: '';
  width: 134px;
  height: 5px;
  background: #1c1c1e;
  border-radius: 3px;
}

/* 移动端拖拽区域 */
.mobile-drop-zone {
  min-height: 200px;
  width: 100%;
}

.mobile-drop-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
}

/* 移动端模式下栅格强制单列 */
.mobile-phone-body :deep(.el-row) {
  display: block !important;
}

.mobile-phone-body :deep(.el-col) {
  width: 100% !important;
  max-width: 100% !important;
  flex: 0 0 100% !important;
}
</style>
