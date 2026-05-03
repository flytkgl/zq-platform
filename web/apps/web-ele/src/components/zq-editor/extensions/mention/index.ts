import type { Instance as TippyInstance } from 'tippy.js';

import Mention from '@tiptap/extension-mention';
import { VueRenderer } from '@tiptap/vue-3';
import tippy from 'tippy.js';

import { getUserListApi } from '#/api/core/user';

import MentionSuggestionMenu from './MentionSuggestionMenu.vue';

export function createMentionSuggestion() {
  return {
    char: '@',
    allowSpaces: false,

    items: async ({ query }: { query: string }) => {
      try {
        const res = await getUserListApi({
          name: query || undefined,
          page: 1,
          pageSize: 10,
        });
        return res.items || [];
      } catch {
        return [];
      }
    },

    render: () => {
      let component: VueRenderer | null = null;
      let popup: TippyInstance[] | null = null;

      return {
        onStart: (props: any) => {
          component = new VueRenderer(MentionSuggestionMenu, {
            props,
            editor: props.editor,
          });

          if (!props.clientRect) return;

          const ref = document.createElement('div');
          const instances = tippy(ref, {
            getReferenceClientRect: props.clientRect,
            appendTo: () => document.body,
            content: component.element as HTMLElement,
            showOnCreate: true,
            interactive: true,
            trigger: 'manual',
            placement: 'bottom-start',
            theme: 'zq-mention',
          });
          popup = Array.isArray(instances) ? instances : [instances];
        },

        onUpdate(props: any) {
          component?.updateProps(props);
          if (props.clientRect && popup) {
            popup[0]?.setProps({
              getReferenceClientRect: props.clientRect,
            });
          }
        },

        onKeyDown(props: any) {
          if (props.event.key === 'Escape') {
            popup?.[0]?.hide();
            return true;
          }
          return (component?.ref as any)?.onKeyDown(props.event);
        },

        onExit() {
          popup?.[0]?.destroy();
          component?.destroy();
        },
      };
    },
  };
}

export const MentionExtension = Mention.configure({
  HTMLAttributes: {
    class: 'zq-mention',
  },
  renderLabel({ node }) {
    return `@${node.attrs.label ?? ''}`;
  },
  suggestion: createMentionSuggestion(),
});

export default MentionExtension;
