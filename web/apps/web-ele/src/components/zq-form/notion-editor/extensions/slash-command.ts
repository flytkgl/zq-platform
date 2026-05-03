import type { Instance as TippyInstance } from 'tippy.js';

import { Extension } from '@tiptap/core';
import Suggestion from '@tiptap/suggestion';
import { VueRenderer } from '@tiptap/vue-3';
import tippy from 'tippy.js';

import SlashCommandMenu from '../components/SlashCommandMenu.vue';

export const SlashCommand = Extension.create({
  name: 'slashCommand',

  addOptions() {
    return {
      suggestion: {
        char: '/',
        startOfLine: false,
        command: ({ editor, range, props }: any) => {
          props.command({ editor, range });
        },
      },
    };
  },

  addProseMirrorPlugins() {
    return [
      Suggestion({
        editor: this.editor,
        ...this.options.suggestion,
      }),
    ];
  },
});

export function createSlashCommandSuggestion() {
  return {
    items: ({ query }: { query: string }) => {
      const commands = [
        {
          title: '正文',
          description: '普通段落文本',
          icon: 'Text',
          command: ({ editor, range }: any) => {
            editor.chain().focus().deleteRange(range).setParagraph().run();
          },
        },
        {
          title: '标题 1',
          description: '大标题',
          icon: 'Heading1',
          command: ({ editor, range }: any) => {
            editor
              .chain()
              .focus()
              .deleteRange(range)
              .setNode('heading', { level: 1 })
              .run();
          },
        },
        {
          title: '标题 2',
          description: '中标题',
          icon: 'Heading2',
          command: ({ editor, range }: any) => {
            editor
              .chain()
              .focus()
              .deleteRange(range)
              .setNode('heading', { level: 2 })
              .run();
          },
        },
        {
          title: '标题 3',
          description: '小标题',
          icon: 'Heading3',
          command: ({ editor, range }: any) => {
            editor
              .chain()
              .focus()
              .deleteRange(range)
              .setNode('heading', { level: 3 })
              .run();
          },
        },
        {
          title: '无序列表',
          description: '创建无序列表',
          icon: 'List',
          command: ({ editor, range }: any) => {
            editor.chain().focus().deleteRange(range).toggleBulletList().run();
          },
        },
        {
          title: '有序列表',
          description: '创建有序列表',
          icon: 'ListOrdered',
          command: ({ editor, range }: any) => {
            editor.chain().focus().deleteRange(range).toggleOrderedList().run();
          },
        },
        {
          title: '引用',
          description: '创建引用块',
          icon: 'Quote',
          command: ({ editor, range }: any) => {
            editor.chain().focus().deleteRange(range).toggleBlockquote().run();
          },
        },
        {
          title: '代码块',
          description: '创建代码块',
          icon: 'Code',
          command: ({ editor, range }: any) => {
            editor.chain().focus().deleteRange(range).toggleCodeBlock().run();
          },
        },
        {
          title: '分割线',
          description: '插入分割线',
          icon: 'Minus',
          command: ({ editor, range }: any) => {
            editor.chain().focus().deleteRange(range).setHorizontalRule().run();
          },
        },
        {
          title: '表格',
          description: '插入表格',
          icon: 'Table',
          command: ({ editor, range }: any) => {
            editor
              .chain()
              .focus()
              .deleteRange(range)
              .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
              .run();
          },
        },
        {
          title: '加粗',
          description: '加粗文本',
          icon: 'Bold',
          command: ({ editor, range }: any) => {
            editor.chain().focus().deleteRange(range).toggleBold().run();
          },
        },
        {
          title: '斜体',
          description: '斜体文本',
          icon: 'Italic',
          command: ({ editor, range }: any) => {
            editor.chain().focus().deleteRange(range).toggleItalic().run();
          },
        },
        {
          title: '高亮',
          description: '高亮文本',
          icon: 'Highlighter',
          command: ({ editor, range }: any) => {
            editor
              .chain()
              .focus()
              .deleteRange(range)
              .toggleHighlight({ color: '#fef08a' })
              .run();
          },
        },
      ];

      return commands.filter((item) =>
        item.title.toLowerCase().includes(query.toLowerCase()),
      );
    },

    render: () => {
      let component: null | VueRenderer = null;
      let popup: null | TippyInstance[] = null;

      return {
        onStart: (props: any) => {
          component = new VueRenderer(SlashCommandMenu, {
            props,
            editor: props.editor,
          });

          if (!props.clientRect) {
            return;
          }

          const referenceElement = document.createElement('div');
          const instances = tippy(referenceElement, {
            getReferenceClientRect: props.clientRect,
            appendTo: () => document.body,
            content: component.element as HTMLElement,
            showOnCreate: true,
            interactive: true,
            trigger: 'manual',
            placement: 'bottom-start',
          });
          popup = Array.isArray(instances) ? instances : [instances];
        },

        onUpdate(props: any) {
          if (!component) return;

          component.updateProps(props);

          if (!props.clientRect || !popup) {
            return;
          }

          popup[0]?.setProps({
            getReferenceClientRect: props.clientRect,
          });
        },

        onKeyDown(props: any) {
          if (props.event.key === 'Escape') {
            popup?.[0]?.hide();
            return true;
          }

          return (component?.ref as any)?.onKeyDown(props);
        },

        onExit() {
          if (popup) {
            popup[0]?.destroy();
          }
          if (component) {
            component.destroy();
          }
        },
      };
    },
  };
}
