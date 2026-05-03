<script setup lang="ts">
import type { Extension } from '@codemirror/state';

import type {
  CodeEditorEmits,
  CodeEditorExpose,
  CodeEditorProps,
} from './types';

import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
  shallowRef,
  watch,
} from 'vue';

import { usePreferences } from '@vben/preferences';

import { autocompletion } from '@codemirror/autocomplete';
import {
  defaultKeymap,
  history,
  historyKeymap,
  indentWithTab,
} from '@codemirror/commands';
import {
  bracketMatching,
  defaultHighlightStyle,
  foldGutter,
  indentOnInput,
  syntaxHighlighting,
} from '@codemirror/language';
import { Compartment, EditorState } from '@codemirror/state';
import { oneDark } from '@codemirror/theme-one-dark';
import {
  crosshairCursor,
  drawSelection,
  dropCursor,
  EditorView,
  highlightActiveLine,
  highlightActiveLineGutter,
  highlightSpecialChars,
  keymap,
  lineNumbers,
  placeholder as placeholderExt,
  rectangularSelection,
} from '@codemirror/view';

import { getLanguageExtension } from './languages';

const props = withDefaults(defineProps<CodeEditorProps>(), {
  modelValue: '',
  language: 'javascript',
  theme: 'auto',
  readonly: false,
  disabled: false,
  height: 'auto',
  minHeight: '100px',
  tabSize: 2,
  lineNumbers: true,
  lineWrapping: false,
  foldGutter: true,
  highlightActiveLine: true,
  bracketMatching: true,
  autocompletion: true,
  indentGuide: true,
});

const emit = defineEmits<CodeEditorEmits>();

const editorRef = ref<HTMLDivElement>();
const view = shallowRef<EditorView | null>(null);

// 主题跟随系统
const { isDark } = usePreferences();

// Compartments 用于动态更新配置
const languageCompartment = new Compartment();
const themeCompartment = new Compartment();
const readonlyCompartment = new Compartment();
const lineNumbersCompartment = new Compartment();
const lineWrappingCompartment = new Compartment();
const foldGutterCompartment = new Compartment();
const highlightActiveLineCompartment = new Compartment();
const bracketMatchingCompartment = new Compartment();
const autocompletionCompartment = new Compartment();
const placeholderCompartment = new Compartment();

// 计算当前主题
const currentTheme = computed(() => {
  if (props.theme === 'auto') {
    return isDark.value ? 'dark' : 'light';
  }
  return props.theme;
});

// 计算样式
const editorStyle = computed(() => {
  const style: Record<string, string> = {};

  if (props.height !== 'auto') {
    style.height =
      typeof props.height === 'number' ? `${props.height}px` : props.height;
  }

  if (props.minHeight) {
    style.minHeight =
      typeof props.minHeight === 'number'
        ? `${props.minHeight}px`
        : props.minHeight;
  }

  if (props.maxHeight) {
    style.maxHeight =
      typeof props.maxHeight === 'number'
        ? `${props.maxHeight}px`
        : props.maxHeight;
  }

  return style;
});

// 获取主题扩展
function getThemeExtension(): Extension {
  return currentTheme.value === 'dark' ? oneDark : [];
}

// 创建基础扩展
function createBaseExtensions(): Extension[] {
  return [
    highlightSpecialChars(),
    history(),
    drawSelection(),
    dropCursor(),
    crosshairCursor(),
    rectangularSelection(),
    indentOnInput(),
    syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
    keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
    EditorState.tabSize.of(props.tabSize),
    EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        const value = update.state.doc.toString();
        emit('update:modelValue', value);
        emit('change', value);
      }
      if (update.focusChanged) {
        if (update.view.hasFocus) {
          emit('focus');
        } else {
          emit('blur');
        }
      }
    }),
  ];
}

// 初始化编辑器
async function initEditor() {
  if (!editorRef.value) return;

  const languageExt = await getLanguageExtension(props.language);

  const extensions: Extension[] = [
    ...createBaseExtensions(),
    languageCompartment.of(languageExt || []),
    themeCompartment.of(getThemeExtension()),
    readonlyCompartment.of(
      EditorState.readOnly.of(props.readonly || props.disabled),
    ),
    lineNumbersCompartment.of(
      props.lineNumbers ? [lineNumbers(), highlightActiveLineGutter()] : [],
    ),
    lineWrappingCompartment.of(
      props.lineWrapping ? EditorView.lineWrapping : [],
    ),
    foldGutterCompartment.of(props.foldGutter ? foldGutter() : []),
    highlightActiveLineCompartment.of(
      props.highlightActiveLine ? highlightActiveLine() : [],
    ),
    bracketMatchingCompartment.of(
      props.bracketMatching ? bracketMatching() : [],
    ),
    autocompletionCompartment.of(props.autocompletion ? autocompletion() : []),
    placeholderCompartment.of(
      props.placeholder ? placeholderExt(props.placeholder) : [],
    ),
  ];

  const state = EditorState.create({
    doc: props.modelValue,
    extensions,
  });

  view.value = new EditorView({
    state,
    parent: editorRef.value,
  });

  emit('ready', view.value);
}

// 更新编辑器内容
function updateContent(value: string) {
  if (!view.value) return;
  const currentValue = view.value.state.doc.toString();
  if (currentValue !== value) {
    view.value.dispatch({
      changes: {
        from: 0,
        to: currentValue.length,
        insert: value,
      },
    });
  }
}

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  (value) => {
    updateContent(value);
  },
);

// 监听语言变化
watch(
  () => props.language,
  async (language) => {
    if (!view.value) return;
    const languageExt = await getLanguageExtension(language);
    view.value.dispatch({
      effects: languageCompartment.reconfigure(languageExt || []),
    });
  },
);

// 监听主题变化
watch(currentTheme, () => {
  if (!view.value) return;
  view.value.dispatch({
    effects: themeCompartment.reconfigure(getThemeExtension()),
  });
});

// 监听只读状态变化
watch(
  () => [props.readonly, props.disabled],
  ([readonly, disabled]) => {
    if (!view.value) return;
    view.value.dispatch({
      effects: readonlyCompartment.reconfigure(
        EditorState.readOnly.of(Boolean(readonly || disabled)),
      ),
    });
  },
);

// 监听行号显示变化
watch(
  () => props.lineNumbers,
  (show) => {
    if (!view.value) return;
    view.value.dispatch({
      effects: lineNumbersCompartment.reconfigure(
        show ? [lineNumbers(), highlightActiveLineGutter()] : [],
      ),
    });
  },
);

// 监听自动换行变化
watch(
  () => props.lineWrapping,
  (wrap) => {
    if (!view.value) return;
    view.value.dispatch({
      effects: lineWrappingCompartment.reconfigure(
        wrap ? EditorView.lineWrapping : [],
      ),
    });
  },
);

// 监听占位符变化
watch(
  () => props.placeholder,
  (text) => {
    if (!view.value) return;
    view.value.dispatch({
      effects: placeholderCompartment.reconfigure(
        text ? placeholderExt(text) : [],
      ),
    });
  },
);

// 暴露方法
const expose: CodeEditorExpose = {
  getView: () => view.value,
  focus: () => view.value?.focus(),
  getValue: () => view.value?.state.doc.toString() || '',
  setValue: (value: string) => updateContent(value),
  format: () => {
    if (!view.value || props.language !== 'json') return;
    try {
      const content = view.value.state.doc.toString();
      const formatted = JSON.stringify(
        JSON.parse(content),
        null,
        props.tabSize,
      );
      updateContent(formatted);
    } catch {
      // JSON 解析失败，忽略
    }
  },
};

defineExpose(expose);

onMounted(() => {
  initEditor();
});

onBeforeUnmount(() => {
  view.value?.destroy();
  view.value = null;
});
</script>

<template>
  <div
    ref="editorRef"
    class="code-editor"
    :class="{
      'code-editor--disabled': disabled,
      'code-editor--readonly': readonly,
      'code-editor--dark': currentTheme === 'dark',
    }"
    :style="editorStyle"
  ></div>
</template>

<style scoped>
.code-editor {
  width: 100%;
  overflow: auto;
  background-color: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: var(--el-border-radius-base);
}

.code-editor :deep(.cm-editor) {
  width: 100%;
  height: 100%;
  outline: none;
}

.code-editor :deep(.cm-content) {
  width: 99%;
}

.code-editor :deep(.cm-scroller) {
  font-family: 'Fira Code', Monaco, Menlo, 'Ubuntu Mono', Consolas, monospace;
  font-size: 14px;
  line-height: 1.5;
}

.code-editor :deep(.cm-focused) {
  outline: none;
}

.code-editor:focus-within {
  border-color: var(--el-color-primary);
}

.code-editor--disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.code-editor--disabled :deep(.cm-editor) {
  pointer-events: none;
}

.code-editor :deep(.cm-gutters) {
  background-color: var(--el-fill-color-light);
  border-right: 1px solid var(--el-border-color-lighter);
}

.code-editor--dark :deep(.cm-gutters) {
  background-color: var(--el-fill-color-darker);
  border-right-color: var(--el-border-color-darker);
}

.code-editor :deep(.cm-activeLineGutter) {
  background-color: var(--el-fill-color);
}

.code-editor :deep(.cm-placeholder) {
  color: var(--el-text-color-placeholder);
}
</style>
