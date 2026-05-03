<script lang="ts" setup>
/**
 * 应用设计面板
 * 用于展示LLM生成的应用设计方案，使用富文本编辑器显示和编辑
 */
import { computed, ref, watch } from 'vue';

import { $t } from '@vben/locales';
import { Maximize, Minimize } from '@vben/icons';

import { ElButton } from 'element-plus';

import { RichTextEditor } from '#/components/zq-form/rich-text-editor';

// 应用设计数据
export interface AppDesignData {
  type: 'app_design';
  title: string;
  data: {
    title: string;
    content: string;
  };
  nodeId?: string;
}

interface Props {
  visible: boolean;
  design?: AppDesignData;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:visible': [value: boolean];
  'confirm': [data: Record<string, any>];
  'close': [];
}>();

// 全屏状态
const isFullscreen = ref(false);

// 切换全屏
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
});

// 编辑内容（Markdown 格式）
const editContent = ref('');

// 富文本编辑器引用
const editorRef = ref<InstanceType<typeof RichTextEditor>>();

// 面板标题
const panelTitle = computed(() => {
  return props.design?.data?.title || props.design?.title || '应用设计方案';
});

// 监听设计数据变化，直接使用 Markdown 内容
watch(
  () => props.design,
  (newDesign) => {
    if (newDesign && newDesign.data?.content) {
      // 直接使用 Markdown 内容，编辑器会自动渲染
      editContent.value = newDesign.data.content;
    } else {
      editContent.value = '';
    }
  },
  { immediate: true }
);

// 确认并继续
function handleConfirm() {
  // 直接获取编辑器的 Markdown 内容
  const markdownContent = editorRef.value?.getMarkdown() || editContent.value;
  
  emit('confirm', {
    title: panelTitle.value,
    content: markdownContent,
  });
}

// 关闭
function handleClose() {
  dialogVisible.value = false;
  emit('close');
}
</script>

<template>
  <div
    v-if="visible"
    :class="[
      'border-border bg-card flex flex-col rounded-lg',
      isFullscreen ? 'fixed inset-0 z-50 ml-0' : 'ml-3 h-full w-full'
    ]"
  >
    <!-- 头部 -->
    <div
      class="border-border bg-muted/50 flex items-center justify-between border-b px-4 py-3"
    >
      <div class="text-foreground font-medium">
        {{ panelTitle }}
      </div>
      <div class="flex items-center gap-2">
        <ElButton size="small" @click="handleClose">{{ $t('common.cancel') }}</ElButton>
        <ElButton size="small" type="primary" @click="handleConfirm">{{ $t('common.confirmAndContinue') }}</ElButton>
        <ElButton 
          link 
          :icon="isFullscreen ? Minimize : Maximize" 
          :title="isFullscreen ? '退出全屏' : '全屏'"
          @click="toggleFullscreen" 
        />
      </div>
    </div>

    <!-- 内容区域：Notion 风格编辑器 -->
    <div class="flex-1 overflow-hidden">
      <RichTextEditor
        ref="editorRef"
        v-model="editContent"
        :min-height="400"
        :max-height="600"
        placeholder="输入 / 打开命令菜单..."
      />
    </div>
  </div>
</template>
