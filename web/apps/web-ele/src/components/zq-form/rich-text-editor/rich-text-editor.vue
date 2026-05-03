<script setup lang="ts">
import type {
  RichTextEditorEmits,
  RichTextEditorProps,
  ToolbarGroup,
} from './types';

import { computed, onBeforeUnmount, ref, watch } from 'vue';

import {
  AlignCenter,
  AlignJustify,
  AlignLeft,
  AlignRight,
  Bold,
  Code,
  Columns2,
  Eraser,
  Heading1,
  Highlighter,
  Image,
  Italic,
  Link,
  List,
  ListOrdered,
  Maximize2,
  Minimize2,
  Minus,
  Palette,
  Paperclip,
  Plus,
  Quote,
  Redo2,
  Rows2,
  Strikethrough,
  Table,
  Trash2,
  Type,
  Underline,
  Undo2,
  Video,
} from '@vben/icons';

import Color from '@tiptap/extension-color';
import Highlight from '@tiptap/extension-highlight';
import LinkExt from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import { Table as TableExt } from '@tiptap/extension-table';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import TableRow from '@tiptap/extension-table-row';
import TextAlign from '@tiptap/extension-text-align';
import { TextStyle } from '@tiptap/extension-text-style';
import UnderlineExt from '@tiptap/extension-underline';
import StarterKit from '@tiptap/starter-kit';
import { EditorContent, useEditor } from '@tiptap/vue-3';
import {
  ElButton,
  ElColorPicker,
  ElDivider,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElInput,
  ElMessage,
  ElPopover,
  ElProgress,
  ElTabPane,
  ElTabs,
} from 'element-plus';
import { Markdown } from 'tiptap-markdown';

import { uploadFile as uploadFileApi } from '#/api/core/file';
import { getFileUrl } from '#/composables/useFileUrl';

import { Attachment } from './extensions/attachment';
import { FontSize } from './extensions/font-size';
import { ResizableImage } from './extensions/resizable-image';
import { Video as VideoExt } from './extensions/video';
import { defaultInsertConfig, defaultToolbarGroups } from './types';

const props = withDefaults(defineProps<RichTextEditorProps>(), {
  modelValue: '',
  placeholder: '请输入内容...',
  disabled: false,
  readonly: false,
  minHeight: 200,
  maxHeight: 500,
  showToolbar: true,
  showWordCount: true,
  maxLength: 0,
  toolbarConfig: () => ({
    groups: defaultToolbarGroups,
    insert: defaultInsertConfig,
  }),
});

const emit = defineEmits<RichTextEditorEmits>();

// 链接弹窗
const linkPopoverVisible = ref(false);
const linkUrl = ref('');
const linkButtonRef = ref<HTMLElement | null>(null);

// 图片弹窗
const imagePopoverVisible = ref(false);
const imageUrl = ref('');
const imageButtonRef = ref<HTMLElement | null>(null);
const imageUploadTab = ref('upload');
const imageUploadInputRef = ref<HTMLInputElement | null>(null);
const imageUploading = ref(false);
const imageUploadProgress = ref(0);

// 附件弹窗
const attachmentPopoverVisible = ref(false);
const attachmentUploadInputRef = ref<HTMLInputElement | null>(null);
const attachmentUploading = ref(false);
const attachmentUploadProgress = ref(0);

// 视频弹窗
const videoPopoverVisible = ref(false);
const videoUploadInputRef = ref<HTMLInputElement | null>(null);
const videoUploading = ref(false);
const videoUploadProgress = ref(0);
const videoUploadTab = ref('upload');
const videoUrl = ref('');

// 全屏状态
const isFullscreen = ref(false);
const fullscreenWidth = ref<'a4' | 'a5' | 'full' | 'letter'>('a4');

// 纸张尺寸选项（宽度，单位px，按96dpi计算）
const paperSizes = {
  full: { label: '全宽', width: '100%' },
  a4: { label: 'A4', width: '794px' }, // 210mm = 794px @96dpi
  a5: { label: 'A5', width: '559px' }, // 148mm = 559px @96dpi
  letter: { label: 'Letter', width: '816px' }, // 8.5in = 816px @96dpi
};

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
  if (!isFullscreen.value) {
    fullscreenWidth.value = 'full';
  }
};

const setFullscreenWidth = (size: 'a4' | 'a5' | 'full' | 'letter') => {
  fullscreenWidth.value = size;
};

// 编辑器实例
const editor = useEditor({
  content: props.modelValue,
  editable: !props.disabled && !props.readonly,
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3],
      },
    }),
    TextAlign.configure({
      types: ['heading', 'paragraph'],
    }),
    UnderlineExt,
    Highlight.configure({
      multicolor: true,
    }),
    TextStyle,
    Color,
    FontSize,
    LinkExt.configure({
      openOnClick: false,
      HTMLAttributes: {
        class: 'text-[var(--el-color-primary)] underline cursor-pointer',
      },
    }),
    ResizableImage.configure({
      inline: false,
      allowBase64: true,
    }),
    TableExt.configure({
      resizable: true,
    }),
    TableRow,
    TableCell,
    TableHeader,
    Attachment,
    VideoExt,
    Placeholder.configure({
      placeholder: props.placeholder,
    }),
    Markdown.configure({
      html: true,
      tightLists: true,
      tightListClass: 'tight',
      bulletListMarker: '-',
      linkify: true,
      breaks: true,
      transformPastedText: true,
      transformCopiedText: true,
    }),
  ],
  onUpdate: ({ editor }) => {
    const html = editor.getHTML();
    emit('update:modelValue', html);
    emit('change', html);
  },
  onFocus: ({ event }) => {
    emit('focus', event);
  },
  onBlur: ({ event }) => {
    emit('blur', event);
  },
  onCreate: ({ editor: editorInstance }) => {
    emit('ready', editorInstance as any);
  },
});

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  (value) => {
    if (editor.value && editor.value.getHTML() !== value) {
      editor.value.commands.setContent(value || '', { emitUpdate: false });
    }
  },
);

// 监听 disabled/readonly 变化
watch(
  () => [props.disabled, props.readonly],
  ([disabled, readonly]) => {
    editor.value?.setEditable(!disabled && !readonly);
  },
);

// 销毁编辑器
onBeforeUnmount(() => {
  editor.value?.destroy();
});

// 工具栏配置
const toolbarGroups = computed(
  () => props.toolbarConfig?.groups || defaultToolbarGroups,
);
const insertConfig = computed(() => ({
  ...defaultInsertConfig,
  ...props.toolbarConfig?.insert,
}));

const hasGroup = (group: ToolbarGroup) => toolbarGroups.value.includes(group);
const hasInsert = (
  type: 'attachment' | 'image' | 'link' | 'table' | 'video',
) => {
  return hasGroup('insert') && insertConfig.value[type];
};

// 字数统计
const wordCount = computed(() => {
  if (!editor.value) return 0;
  return (
    editor.value.storage.characterCount?.characters() ||
    editor.value.getText().length
  );
});

// 样式计算
const editorStyle = computed(() => ({
  minHeight:
    typeof props.minHeight === 'number'
      ? `${props.minHeight}px`
      : props.minHeight,
  maxHeight:
    typeof props.maxHeight === 'number'
      ? `${props.maxHeight}px`
      : props.maxHeight,
}));

// 工具栏操作
const toggleBold = () => editor.value?.chain().focus().toggleBold().run();
const toggleItalic = () => editor.value?.chain().focus().toggleItalic().run();
const toggleUnderline = () =>
  editor.value?.chain().focus().toggleUnderline().run();
const toggleStrike = () => editor.value?.chain().focus().toggleStrike().run();
const toggleCode = () => editor.value?.chain().focus().toggleCode().run();
// const toggleCodeBlock = () => editor.value?.chain().focus().toggleCodeBlock().run();
const toggleBlockquote = () =>
  editor.value?.chain().focus().toggleBlockquote().run();
const toggleBulletList = () =>
  editor.value?.chain().focus().toggleBulletList().run();
const toggleOrderedList = () =>
  editor.value?.chain().focus().toggleOrderedList().run();
const setHorizontalRule = () =>
  editor.value?.chain().focus().setHorizontalRule().run();
const undo = () => editor.value?.chain().focus().undo().run();
const redo = () => editor.value?.chain().focus().redo().run();
const clearFormat = () =>
  editor.value?.chain().focus().clearNodes().unsetAllMarks().run();

const setHeading = (level: 1 | 2 | 3) => {
  editor.value?.chain().focus().toggleHeading({ level }).run();
};

const setTextAlign = (align: 'center' | 'justify' | 'left' | 'right') => {
  editor.value?.chain().focus().setTextAlign(align).run();
};

const setTextColor = (color: null | string) => {
  if (color) {
    editor.value?.chain().focus().setColor(color).run();
  } else {
    editor.value?.chain().focus().unsetColor().run();
  }
};

const setHighlight = (color: null | string) => {
  if (color) {
    editor.value?.chain().focus().setHighlight({ color }).run();
  } else {
    editor.value?.chain().focus().unsetHighlight().run();
  }
};

// 字体大小选项
const fontSizes = [
  { label: '12px', value: '12px' },
  { label: '14px', value: '14px' },
  { label: '16px', value: '16px' },
  { label: '18px', value: '18px' },
  { label: '20px', value: '20px' },
  { label: '24px', value: '24px' },
  { label: '28px', value: '28px' },
  { label: '32px', value: '32px' },
  { label: '36px', value: '36px' },
];

const setFontSize = (size: string) => {
  editor.value?.chain().focus().setFontSize(size).run();
};

const setLink = () => {
  if (linkUrl.value) {
    editor.value?.chain().focus().setLink({ href: linkUrl.value }).run();
  } else {
    editor.value?.chain().focus().unsetLink().run();
  }
  linkPopoverVisible.value = false;
  linkUrl.value = '';
};

const openLinkPopover = () => {
  const previousUrl = editor.value?.getAttributes('link').href;
  linkUrl.value = previousUrl || '';
  linkPopoverVisible.value = true;
};

// 插入图片的通用方法
const insertImage = (src: string) => {
  editor.value
    ?.chain()
    .focus()
    .insertContent({
      type: 'resizableImage',
      attrs: { src },
    })
    .run();
};

const setImage = () => {
  if (!imageUrl.value) {
    ElMessage.warning('请输入图片地址');
    return;
  }
  insertImage(imageUrl.value);
  imagePopoverVisible.value = false;
  imageUrl.value = '';
};

// 触发图片上传
const triggerImageUpload = () => {
  imageUploadInputRef.value?.click();
};

// 处理图片上传
const handleImageUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  if (!files || files.length === 0) return;

  const file = files[0];
  if (!file) return;

  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件');
    target.value = '';
    return;
  }

  // 验证文件大小 (最大 10MB)
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    ElMessage.warning('图片大小不能超过 10MB');
    target.value = '';
    return;
  }

  try {
    imageUploading.value = true;
    imageUploadProgress.value = 0;

    const result = await uploadFileApi(file, {
      source: 'form',
      onProgress: (progress) => {
        imageUploadProgress.value = progress.percentage;
      },
    });

    if (result && result.id) {
      // 使用文件流 URL
      const imgUrl = await getFileUrl(result.id);
      insertImage(imgUrl);
      ElMessage.success('图片上传成功');
      imagePopoverVisible.value = false;
    } else {
      ElMessage.error('上传失败，请重试');
    }
  } catch (error) {
    console.error('图片上传失败:', error);
    ElMessage.error('图片上传失败');
  } finally {
    imageUploading.value = false;
    imageUploadProgress.value = 0;
    target.value = '';
  }
};

// 处理粘贴图片
const handlePaste = async (event: ClipboardEvent) => {
  const items = event.clipboardData?.items;
  if (!items) return;

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      event.preventDefault();
      const file = item.getAsFile();
      if (!file) continue;

      try {
        imageUploading.value = true;
        const result = await uploadFileApi(file, { source: 'form' });
        if (result && result.id) {
          const imgUrl = await getFileUrl(result.id);
          insertImage(imgUrl);
          ElMessage.success('图片粘贴成功');
        }
      } catch (error) {
        console.error('粘贴图片失败:', error);
        ElMessage.error('粘贴图片失败');
      } finally {
        imageUploading.value = false;
      }
      break;
    }
  }
};

// 处理拖拽图片
const handleDrop = async (event: DragEvent) => {
  const files = event.dataTransfer?.files;
  if (!files || files.length === 0) return;

  const file = files[0];
  if (!file || !file.type.startsWith('image/')) return;

  event.preventDefault();

  try {
    imageUploading.value = true;
    const result = await uploadFileApi(file, { source: 'form' });
    if (result && result.id) {
      const imgUrl = await getFileUrl(result.id);
      insertImage(imgUrl);
      ElMessage.success('图片上传成功');
    }
  } catch (error) {
    console.error('拖拽图片上传失败:', error);
    ElMessage.error('图片上传失败');
  } finally {
    imageUploading.value = false;
  }
};

const insertTable = () => {
  editor.value
    ?.chain()
    .focus()
    .insertTable({ rows: 2, cols: 3, withHeaderRow: true })
    .run();
};

// 表格操作
const addRowBefore = () => editor.value?.chain().focus().addRowBefore().run();
const addRowAfter = () => editor.value?.chain().focus().addRowAfter().run();
const deleteRow = () => editor.value?.chain().focus().deleteRow().run();
const addColumnBefore = () =>
  editor.value?.chain().focus().addColumnBefore().run();
const addColumnAfter = () =>
  editor.value?.chain().focus().addColumnAfter().run();
const deleteColumn = () => editor.value?.chain().focus().deleteColumn().run();
const deleteTable = () => editor.value?.chain().focus().deleteTable().run();

// 检查是否在表格中
const isInTable = computed(() => editor.value?.isActive('table') || false);

// 表格命令处理
const handleTableCommand = (command: string) => {
  switch (command) {
    case 'addColumnAfter': {
      addColumnAfter();
      break;
    }
    case 'addColumnBefore': {
      addColumnBefore();
      break;
    }
    case 'addRowAfter': {
      addRowAfter();
      break;
    }
    case 'addRowBefore': {
      addRowBefore();
      break;
    }
    case 'deleteColumn': {
      deleteColumn();
      break;
    }
    case 'deleteRow': {
      deleteRow();
      break;
    }
    case 'deleteTable': {
      deleteTable();
      break;
    }
    case 'insert': {
      insertTable();
      break;
    }
  }
};

// 附件上传
const triggerAttachmentUpload = () => {
  attachmentUploadInputRef.value?.click();
};

const handleAttachmentUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  if (!files || files.length === 0) return;

  const file = files[0];
  if (!file) return;

  // 验证文件大小 (最大 50MB)
  const maxSize = 50 * 1024 * 1024;
  if (file.size > maxSize) {
    ElMessage.warning('附件大小不能超过 50MB');
    target.value = '';
    return;
  }

  try {
    attachmentUploading.value = true;
    attachmentUploadProgress.value = 0;

    const result = await uploadFileApi(file, {
      source: 'form',
      onProgress: (progress) => {
        attachmentUploadProgress.value = progress.percentage;
      },
    });

    if (result && result.id) {
      const fileUrl = await getFileUrl(result.id);
      editor.value
        ?.chain()
        .focus()
        .insertContent({
          type: 'attachment',
          attrs: {
            id: result.id,
            name: file.name,
            size: file.size,
            type: file.type,
            url: fileUrl,
          },
        })
        .run();
      ElMessage.success('附件上传成功');
      attachmentPopoverVisible.value = false;
    } else {
      ElMessage.error('上传失败，请重试');
    }
  } catch (error) {
    console.error('附件上传失败:', error);
    ElMessage.error('附件上传失败');
  } finally {
    attachmentUploading.value = false;
    attachmentUploadProgress.value = 0;
    target.value = '';
  }
};

// 视频上传
const triggerVideoUpload = () => {
  videoUploadInputRef.value?.click();
};

const handleVideoUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  if (!files || files.length === 0) return;

  const file = files[0];
  if (!file) return;

  // 验证文件类型
  const validTypes = [
    'video/mp4',
    'video/webm',
    'video/ogg',
    'video/quicktime',
  ];
  if (!validTypes.includes(file.type)) {
    ElMessage.warning('请上传 MP4、WebM、OGG 或 MOV 格式的视频');
    target.value = '';
    return;
  }

  // 验证文件大小 (最大 100MB)
  const maxSize = 100 * 1024 * 1024;
  if (file.size > maxSize) {
    ElMessage.warning('视频大小不能超过 100MB');
    target.value = '';
    return;
  }

  try {
    videoUploading.value = true;
    videoUploadProgress.value = 0;

    const result = await uploadFileApi(file, {
      source: 'form',
      onProgress: (progress) => {
        videoUploadProgress.value = progress.percentage;
      },
    });

    if (result && result.id) {
      const videoSrc = await getFileUrl(result.id);
      insertVideo(videoSrc, result.id);
      ElMessage.success('视频上传成功');
      videoPopoverVisible.value = false;
    } else {
      ElMessage.error('上传失败，请重试');
    }
  } catch (error) {
    console.error('视频上传失败:', error);
    ElMessage.error('视频上传失败');
  } finally {
    videoUploading.value = false;
    videoUploadProgress.value = 0;
    target.value = '';
  }
};

const insertVideo = (src: string, id?: string) => {
  if (!src) return;
  editor.value
    ?.chain()
    .focus()
    .insertContent({
      type: 'video',
      attrs: {
        id,
        src,
        width: '100%',
      },
    })
    .run();
};

const setVideoFromUrl = () => {
  if (!videoUrl.value) {
    ElMessage.warning('请输入视频地址');
    return;
  }
  insertVideo(videoUrl.value);
  videoUrl.value = '';
  videoPopoverVisible.value = false;
};

// 检查当前状态
const isActive = (name: string, attributes?: Record<string, any>) => {
  return editor.value?.isActive(name, attributes) || false;
};

// 预设颜色
const presetColors = [
  '#000000',
  '#333333',
  '#666666',
  '#999999',
  '#cccccc',
  '#e60000',
  '#ff9900',
  '#ffff00',
  '#008a00',
  '#0066cc',
  '#9933ff',
  '#ff00ff',
  '#ff6666',
  '#ffcc66',
  '#ffff66',
];

// 暴露方法
defineExpose({
  /** 获取编辑器实例 */
  getEditor: () => editor.value,
  /** 获取 HTML 内容 */
  getHTML: () => editor.value?.getHTML() || '',
  /** 获取纯文本内容 */
  getText: () => editor.value?.getText() || '',
  /** 获取 Markdown 内容 */
  getMarkdown: () =>
    (editor.value?.storage as any)?.markdown?.getMarkdown() || '',
  /** 设置内容 */
  setContent: (content: string) => editor.value?.commands.setContent(content),
  /** 清空内容 */
  clear: () => editor.value?.commands.clearContent(),
  /** 聚焦 */
  focus: () => editor.value?.commands.focus(),
  /** 在光标位置插入文本 */
  insertText: (text: string) => {
    editor.value?.chain().focus().insertContent(text).run();
  },
});
</script>

<template>
  <div
    class="rich-text-editor rounded border border-[var(--el-border-color)] bg-[var(--el-bg-color)]"
    :class="{
      'is-disabled': disabled,
      'is-readonly': readonly,
      'is-fullscreen': isFullscreen,
    }"
  >
    <!-- 工具栏 -->
    <div
      v-if="showToolbar && !readonly"
      class="toolbar flex flex-wrap items-center gap-1 border-b border-[var(--el-border-color)] bg-[var(--el-fill-color-light)] px-2 py-1"
    >
      <!-- 撤销/重做 -->
      <template v-if="hasGroup('history')">
        <ElButton
          text
          size="small"
          :disabled="!editor?.can().undo()"
          title="撤销"
          @click="undo"
        >
          <Undo2 class="h-4 w-4" />
        </ElButton>
        <ElButton
          text
          size="small"
          :disabled="!editor?.can().redo()"
          title="重做"
          @click="redo"
        >
          <Redo2 class="h-4 w-4" />
        </ElButton>
        <ElDivider direction="vertical" />
      </template>

      <!-- 标题 -->
      <template v-if="hasGroup('heading')">
        <ElDropdown trigger="click" @command="setHeading">
          <ElButton text size="small" title="标题">
            <Heading1 class="h-4 w-4" />
          </ElButton>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem
                :command="1"
                :class="{ 'is-active': isActive('heading', { level: 1 }) }"
              >
                <span class="text-xl font-bold">标题 1</span>
              </ElDropdownItem>
              <ElDropdownItem
                :command="2"
                :class="{ 'is-active': isActive('heading', { level: 2 }) }"
              >
                <span class="text-lg font-bold">标题 2</span>
              </ElDropdownItem>
              <ElDropdownItem
                :command="3"
                :class="{ 'is-active': isActive('heading', { level: 3 }) }"
              >
                <span class="text-base font-bold">标题 3</span>
              </ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
        <ElDivider direction="vertical" />
      </template>

      <!-- 格式化 -->
      <template v-if="hasGroup('format')">
        <ElDropdown trigger="click" @command="setFontSize">
          <ElButton text size="small" title="字体大小">
            <Type class="h-4 w-4" />
          </ElButton>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem
                v-for="size in fontSizes"
                :key="size.value"
                :command="size.value"
              >
                {{ size.label }}
              </ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
        <ElButton
          text
          size="small"
          :class="{ 'is-active': isActive('bold') }"
          title="加粗"
          @click="toggleBold"
        >
          <Bold class="h-4 w-4" />
        </ElButton>
        <ElButton
          text
          size="small"
          :class="{ 'is-active': isActive('italic') }"
          title="斜体"
          @click="toggleItalic"
        >
          <Italic class="h-4 w-4" />
        </ElButton>
        <ElButton
          text
          size="small"
          :class="{ 'is-active': isActive('underline') }"
          title="下划线"
          @click="toggleUnderline"
        >
          <Underline class="h-4 w-4" />
        </ElButton>
        <ElButton
          text
          size="small"
          :class="{ 'is-active': isActive('strike') }"
          title="删除线"
          @click="toggleStrike"
        >
          <Strikethrough class="h-4 w-4" />
        </ElButton>
        <ElDivider direction="vertical" />
      </template>

      <!-- 颜色 -->
      <template v-if="hasGroup('color')">
        <ElPopover trigger="click" :width="200">
          <template #reference>
            <ElButton text size="small" title="文字颜色">
              <Palette class="h-4 w-4" />
            </ElButton>
          </template>
          <div class="color-picker-panel">
            <div class="mb-2 text-xs text-[var(--el-text-color-secondary)]">
              文字颜色
            </div>
            <div class="grid grid-cols-5 gap-1">
              <div
                v-for="color in presetColors"
                :key="color"
                class="h-6 w-6 cursor-pointer rounded border border-[var(--el-border-color)] transition-transform hover:scale-110"
                :style="{ backgroundColor: color }"
                @click="setTextColor(color)"
              ></div>
            </div>
            <ElColorPicker class="mt-2" size="small" @change="setTextColor" />
          </div>
        </ElPopover>
        <ElPopover trigger="click" :width="200">
          <template #reference>
            <ElButton text size="small" title="背景色">
              <Highlighter class="h-4 w-4" />
            </ElButton>
          </template>
          <div class="color-picker-panel">
            <div class="mb-2 text-xs text-[var(--el-text-color-secondary)]">
              背景色
            </div>
            <div class="grid grid-cols-5 gap-1">
              <div
                v-for="color in presetColors"
                :key="color"
                class="h-6 w-6 cursor-pointer rounded border border-[var(--el-border-color)] transition-transform hover:scale-110"
                :style="{ backgroundColor: color }"
                @click="setHighlight(color)"
              ></div>
            </div>
            <ElColorPicker class="mt-2" size="small" @change="setHighlight" />
          </div>
        </ElPopover>
        <ElDivider direction="vertical" />
      </template>

      <!-- 对齐 -->
      <template v-if="hasGroup('align')">
        <ElButton
          text
          size="small"
          :class="{ 'is-active': editor?.isActive({ textAlign: 'left' }) }"
          title="左对齐"
          @click="setTextAlign('left')"
        >
          <AlignLeft class="h-4 w-4" />
        </ElButton>
        <ElButton
          text
          size="small"
          :class="{ 'is-active': editor?.isActive({ textAlign: 'center' }) }"
          title="居中"
          @click="setTextAlign('center')"
        >
          <AlignCenter class="h-4 w-4" />
        </ElButton>
        <ElButton
          text
          size="small"
          :class="{ 'is-active': editor?.isActive({ textAlign: 'right' }) }"
          title="右对齐"
          @click="setTextAlign('right')"
        >
          <AlignRight class="h-4 w-4" />
        </ElButton>
        <ElButton
          text
          size="small"
          :class="{ 'is-active': editor?.isActive({ textAlign: 'justify' }) }"
          title="两端对齐"
          @click="setTextAlign('justify')"
        >
          <AlignJustify class="h-4 w-4" />
        </ElButton>
        <ElDivider direction="vertical" />
      </template>

      <!-- 列表 -->
      <template v-if="hasGroup('list')">
        <ElButton
          text
          size="small"
          :class="{ 'is-active': isActive('bulletList') }"
          title="无序列表"
          @click="toggleBulletList"
        >
          <List class="h-4 w-4" />
        </ElButton>
        <ElButton
          text
          size="small"
          :class="{ 'is-active': isActive('orderedList') }"
          title="有序列表"
          @click="toggleOrderedList"
        >
          <ListOrdered class="h-4 w-4" />
        </ElButton>
        <ElDivider direction="vertical" />
      </template>

      <!-- 插入 -->
      <template v-if="hasGroup('insert')">
        <ElPopover
          v-if="hasInsert('link')"
          v-model:visible="linkPopoverVisible"
          trigger="click"
          :width="280"
        >
          <template #reference>
            <ElButton
              ref="linkButtonRef"
              text
              size="small"
              :class="{ 'is-active': isActive('link') }"
              title="链接"
              @click="openLinkPopover"
            >
              <Link class="h-4 w-4" />
            </ElButton>
          </template>
          <div class="link-panel">
            <div class="mb-2 text-sm font-medium">插入链接</div>
            <ElInput
              v-model="linkUrl"
              placeholder="请输入链接地址"
              size="small"
              @keyup.enter="setLink"
            />
            <div class="mt-2 flex justify-end gap-2">
              <ElButton size="small" @click="linkPopoverVisible = false">
                取消
              </ElButton>
              <ElButton type="primary" size="small" @click="setLink">
                确定
              </ElButton>
            </div>
          </div>
        </ElPopover>
        <ElPopover
          v-if="hasInsert('image')"
          v-model:visible="imagePopoverVisible"
          trigger="click"
          :width="320"
        >
          <template #reference>
            <ElButton ref="imageButtonRef" text size="small" title="图片">
              <Image class="h-4 w-4" />
            </ElButton>
          </template>
          <div class="image-panel">
            <ElTabs v-model="imageUploadTab" class="image-tabs">
              <ElTabPane label="上传图片" name="upload">
                <div class="py-2">
                  <input
                    ref="imageUploadInputRef"
                    type="file"
                    accept="image/*"
                    class="hidden"
                    @change="handleImageUpload"
                  />
                  <div
                    class="upload-area flex cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed border-[var(--el-border-color)] p-6 transition-colors hover:border-[var(--el-color-primary)] hover:bg-[var(--el-fill-color-light)]"
                    @click="triggerImageUpload"
                  >
                    <Image
                      class="mb-2 h-8 w-8 text-[var(--el-text-color-secondary)]"
                    />
                    <span class="text-sm text-[var(--el-text-color-secondary)]">点击或拖拽图片到此处</span>
                    <span
                      class="mt-1 text-xs text-[var(--el-text-color-placeholder)]"
                      >支持 jpg、png、gif 等格式，最大 10MB</span>
                  </div>
                  <ElProgress
                    v-if="imageUploading"
                    :percentage="imageUploadProgress"
                    :stroke-width="4"
                    class="mt-2"
                  />
                </div>
              </ElTabPane>
              <ElTabPane label="网络图片" name="url">
                <div class="py-2">
                  <ElInput
                    v-model="imageUrl"
                    placeholder="请输入图片地址"
                    size="small"
                    @keyup.enter="setImage"
                  />
                  <div class="mt-3 flex justify-end gap-2">
                    <ElButton size="small" @click="imagePopoverVisible = false">
                      取消
                    </ElButton>
                    <ElButton type="primary" size="small" @click="setImage">
                      插入
                    </ElButton>
                  </div>
                </div>
              </ElTabPane>
            </ElTabs>
          </div>
        </ElPopover>
        <!-- 表格操作 -->
        <ElDropdown
          v-if="hasInsert('table')"
          trigger="click"
          @command="handleTableCommand"
        >
          <ElButton text size="small" title="表格">
            <Table class="h-4 w-4" />
          </ElButton>
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem command="insert" :disabled="isInTable">
                <div class="flex items-center gap-2">
                  <Plus class="h-4 w-4" />
                  <span>插入表格</span>
                </div>
              </ElDropdownItem>
              <ElDropdownItem
                divided
                command="addRowBefore"
                :disabled="!isInTable"
              >
                <div class="flex items-center gap-2">
                  <Rows2 class="h-4 w-4" />
                  <span>在上方插入行</span>
                </div>
              </ElDropdownItem>
              <ElDropdownItem command="addRowAfter" :disabled="!isInTable">
                <div class="flex items-center gap-2">
                  <Rows2 class="h-4 w-4" />
                  <span>在下方插入行</span>
                </div>
              </ElDropdownItem>
              <ElDropdownItem command="deleteRow" :disabled="!isInTable">
                <div
                  class="flex items-center gap-2 text-[var(--el-color-danger)]"
                >
                  <Minus class="h-4 w-4" />
                  <span>删除当前行</span>
                </div>
              </ElDropdownItem>
              <ElDropdownItem
                divided
                command="addColumnBefore"
                :disabled="!isInTable"
              >
                <div class="flex items-center gap-2">
                  <Columns2 class="h-4 w-4" />
                  <span>在左侧插入列</span>
                </div>
              </ElDropdownItem>
              <ElDropdownItem command="addColumnAfter" :disabled="!isInTable">
                <div class="flex items-center gap-2">
                  <Columns2 class="h-4 w-4" />
                  <span>在右侧插入列</span>
                </div>
              </ElDropdownItem>
              <ElDropdownItem command="deleteColumn" :disabled="!isInTable">
                <div
                  class="flex items-center gap-2 text-[var(--el-color-danger)]"
                >
                  <Minus class="h-4 w-4" />
                  <span>删除当前列</span>
                </div>
              </ElDropdownItem>
              <ElDropdownItem
                divided
                command="deleteTable"
                :disabled="!isInTable"
              >
                <div
                  class="flex items-center gap-2 text-[var(--el-color-danger)]"
                >
                  <Trash2 class="h-4 w-4" />
                  <span>删除表格</span>
                </div>
              </ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
        <ElPopover
          v-if="hasInsert('attachment')"
          v-model:visible="attachmentPopoverVisible"
          trigger="click"
          :width="300"
        >
          <template #reference>
            <ElButton text size="small" title="附件">
              <Paperclip class="h-4 w-4" />
            </ElButton>
          </template>
          <div class="attachment-panel">
            <div class="mb-2 text-sm font-medium">上传附件</div>
            <input
              ref="attachmentUploadInputRef"
              type="file"
              class="hidden"
              @change="handleAttachmentUpload"
            />
            <div
              class="upload-area flex cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed border-[var(--el-border-color)] p-6 transition-colors hover:border-[var(--el-color-primary)] hover:bg-[var(--el-fill-color-light)]"
              @click="triggerAttachmentUpload"
            >
              <Paperclip
                class="mb-2 h-8 w-8 text-[var(--el-text-color-secondary)]"
              />
              <span class="text-sm text-[var(--el-text-color-secondary)]">点击选择文件</span>
              <span class="mt-1 text-xs text-[var(--el-text-color-placeholder)]">支持常见文档格式，最大 50MB</span>
            </div>
            <ElProgress
              v-if="attachmentUploading"
              :percentage="attachmentUploadProgress"
              :stroke-width="4"
              class="mt-2"
            />
          </div>
        </ElPopover>
        <ElPopover
          v-if="hasInsert('video')"
          v-model:visible="videoPopoverVisible"
          trigger="click"
          :width="320"
        >
          <template #reference>
            <ElButton text size="small" title="视频">
              <Video class="h-4 w-4" />
            </ElButton>
          </template>
          <div class="video-panel">
            <ElTabs v-model="videoUploadTab">
              <ElTabPane label="上传视频" name="upload">
                <div class="py-2">
                  <input
                    ref="videoUploadInputRef"
                    type="file"
                    accept="video/mp4,video/webm,video/ogg,video/quicktime"
                    class="hidden"
                    @change="handleVideoUpload"
                  />
                  <div
                    class="upload-area flex cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed border-[var(--el-border-color)] p-6 transition-colors hover:border-[var(--el-color-primary)] hover:bg-[var(--el-fill-color-light)]"
                    @click="triggerVideoUpload"
                  >
                    <Video
                      class="mb-2 h-8 w-8 text-[var(--el-text-color-secondary)]"
                    />
                    <span class="text-sm text-[var(--el-text-color-secondary)]">点击选择视频</span>
                    <span
                      class="mt-1 text-xs text-[var(--el-text-color-placeholder)]"
                      >支持 MP4、WebM、OGG，最大 100MB</span>
                  </div>
                  <ElProgress
                    v-if="videoUploading"
                    :percentage="videoUploadProgress"
                    :stroke-width="4"
                    class="mt-2"
                  />
                </div>
              </ElTabPane>
              <ElTabPane label="网络视频" name="url">
                <div class="py-2">
                  <ElInput
                    v-model="videoUrl"
                    placeholder="请输入视频地址"
                    size="small"
                    @keyup.enter="setVideoFromUrl"
                  />
                  <div class="mt-3 flex justify-end gap-2">
                    <ElButton size="small" @click="videoPopoverVisible = false">
                      取消
                    </ElButton>
                    <ElButton
                      type="primary"
                      size="small"
                      @click="setVideoFromUrl"
                    >
                      插入
                    </ElButton>
                  </div>
                </div>
              </ElTabPane>
            </ElTabs>
          </div>
        </ElPopover>
        <ElDivider direction="vertical" />
      </template>

      <!-- 引用 -->
      <template v-if="hasGroup('blockquote')">
        <ElButton
          text
          size="small"
          :class="{ 'is-active': isActive('blockquote') }"
          title="引用"
          @click="toggleBlockquote"
        >
          <Quote class="h-4 w-4" />
        </ElButton>
      </template>

      <!-- 代码 -->
      <template v-if="hasGroup('code')">
        <ElButton
          text
          size="small"
          :class="{ 'is-active': isActive('code') }"
          title="行内代码"
          @click="toggleCode"
        >
          <Code class="h-4 w-4" />
        </ElButton>
      </template>

      <!-- 分割线 -->
      <template v-if="hasGroup('divider')">
        <ElButton text size="small" title="分割线" @click="setHorizontalRule">
          <Minus class="h-4 w-4" />
        </ElButton>
      </template>

      <!-- 清除格式 -->
      <template v-if="hasGroup('clear')">
        <ElDivider direction="vertical" />
        <ElButton text size="small" title="清除格式" @click="clearFormat">
          <Eraser class="h-4 w-4" />
        </ElButton>
      </template>

      <!-- 全屏按钮和纸张尺寸选择 -->
      <div class="ml-auto flex items-center gap-1">
        <!-- 纸张尺寸选择（仅全屏时显示） -->
        <template v-if="isFullscreen">
          <ElButton
            v-for="(config, key) in paperSizes"
            :key="key"
            text
            size="small"
            :class="{ 'is-active': fullscreenWidth === key }"
            @click="setFullscreenWidth(key as 'full' | 'a4' | 'a5' | 'letter')"
          >
            {{ config.label }}
          </ElButton>
          <ElDivider direction="vertical" />
        </template>
        <ElButton
          text
          size="small"
          :title="isFullscreen ? '退出全屏' : '全屏编辑'"
          @click="toggleFullscreen"
        >
          <Minimize2 v-if="isFullscreen" class="h-4 w-4" />
          <Maximize2 v-else class="h-4 w-4" />
        </ElButton>
      </div>
    </div>

    <!-- 编辑器内容区 -->
    <div
      class="editor-content overflow-auto"
      :class="{ 'fullscreen-content': isFullscreen }"
      :style="editorStyle"
      @paste="handlePaste"
      @drop="handleDrop"
      @dragover.prevent
    >
      <div
        v-if="isFullscreen && fullscreenWidth !== 'full'"
        class="editor-paper mx-auto bg-[var(--el-bg-color)] shadow-lg"
        :style="{ width: paperSizes[fullscreenWidth].width }"
      >
        <EditorContent :editor="editor" class="h-full" />
      </div>
      <EditorContent v-else :editor="editor" class="h-full" />
    </div>

    <!-- 底部状态栏 -->
    <div
      v-if="showWordCount"
      class="status-bar flex items-center justify-end border-t border-[var(--el-border-color)] bg-[var(--el-fill-color-light)] px-3 py-1 text-xs text-[var(--el-text-color-secondary)]"
    >
      <span>
        字数: {{ wordCount }}
        <template v-if="maxLength > 0"> / {{ maxLength }}</template>
      </span>
    </div>
  </div>
</template>

<style scoped>
.rich-text-editor {
  &.is-disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  &.is-readonly {
    .toolbar {
      display: none;
    }
  }

  &.is-fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
    border-radius: 0;
    display: flex;
    flex-direction: column;

    .editor-content {
      flex: 1;
      max-height: none !important;
      min-height: 0 !important;
    }

    .fullscreen-content {
      background-color: var(--el-fill-color-light);
      padding: 20px;
    }

    .editor-paper {
      min-height: 100%;
      padding: 40px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    }
  }
}

.toolbar {
  :deep(.el-button) {
    min-width: 28px;
    height: 28px;
    padding: 4px 6px;

    &.is-active {
      color: var(--el-color-primary);
      background-color: var(--el-color-primary-light-9);
    }
  }

  :deep(.el-divider--vertical) {
    height: 16px;
    margin: 0 4px;
  }
}

.editor-content {
  :deep(.tiptap) {
    min-height: 100%;
    padding: 12px 16px;
    outline: none;

    > * + * {
      margin-top: 0.75em;
    }

    p.is-editor-empty:first-child::before {
      float: left;
      height: 0;
      color: var(--el-text-color-placeholder);
      pointer-events: none;
      content: attr(data-placeholder);
    }

    h1 {
      margin: 0.67em 0;
      font-size: 2em;
      font-weight: bold;
    }

    h2 {
      margin: 0.83em 0;
      font-size: 1.5em;
      font-weight: bold;
    }

    h3 {
      margin: 1em 0;
      font-size: 1.17em;
      font-weight: bold;
    }

    ul,
    ol {
      padding-left: 1.5em;
    }

    ul {
      list-style-type: disc;
    }

    ol {
      list-style-type: decimal;
    }

    blockquote {
      padding-left: 1em;
      margin-left: 0;
      color: var(--el-text-color-secondary);
      border-left: 3px solid var(--el-border-color);
    }

    code {
      padding: 0.2em 0.4em;
      font-family: monospace;
      background-color: var(--el-fill-color);
      border-radius: 3px;
    }

    pre {
      padding: 1em;
      overflow-x: auto;
      background-color: var(--el-fill-color-dark);
      border-radius: 4px;

      code {
        padding: 0;
        background: none;
      }
    }

    hr {
      margin: 1em 0;
      border: none;
      border-top: 1px solid var(--el-border-color);
    }

    img {
      max-width: 100%;
      height: auto;
      cursor: pointer;
      border-radius: 4px;
      transition: box-shadow 0.2s;

      &:hover {
        box-shadow: 0 0 0 2px var(--el-color-primary-light-5);
      }

      &.ProseMirror-selectednode {
        box-shadow: 0 0 0 2px var(--el-color-primary);
      }
    }

    /* 附件节点样式 */
    .attachment-node {
      display: inline-block;
      margin: 4px 0;

      .attachment-link {
        display: inline-flex;
        gap: 8px;
        align-items: center;
        padding: 8px 12px;
        color: var(--el-text-color-regular);
        text-decoration: none;
        background-color: var(--el-fill-color-light);
        border: 1px solid var(--el-border-color);
        border-radius: 6px;
        transition: all 0.2s;

        &:hover {
          color: var(--el-color-primary);
          background-color: var(--el-fill-color);
          border-color: var(--el-color-primary-light-5);
        }

        .attachment-icon {
          font-size: 16px;
        }

        .attachment-name {
          max-width: 200px;
          overflow: hidden;
          text-overflow: ellipsis;
          font-size: 13px;
          white-space: nowrap;
        }

        .attachment-size {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
    }

    /* 视频节点样式 */
    .video-node {
      margin: 12px 0;

      video {
        max-width: 100%;
        background-color: var(--el-fill-color-darker);
        border-radius: 8px;
      }
    }

    table {
      width: 100%;
      margin: 1em 0;
      border-collapse: collapse;

      th,
      td {
        padding: 8px 12px;
        text-align: left;
        border: 1px solid var(--el-border-color);
      }

      th {
        font-weight: bold;
        background-color: var(--el-fill-color-light);
      }
    }

    a {
      color: var(--el-color-primary);
      text-decoration: underline;
      cursor: pointer;
    }
  }
}

:deep(.el-dropdown-menu__item.is-active) {
  color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

/* 图片上传弹窗样式 */
.image-panel {
  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }

  :deep(.el-tabs__nav-wrap::after) {
    height: 1px;
  }

  :deep(.el-tabs__item) {
    height: 36px;
    padding: 0 12px;
    font-size: 13px;
    line-height: 36px;
  }
}

.upload-area {
  min-height: 120px;

  &:hover {
    border-color: var(--el-color-primary);
  }
}
</style>
