import { mergeAttributes, Node } from '@tiptap/core';
import { VueNodeViewRenderer } from '@tiptap/vue-3';

import EmbedComponent from './EmbedComponent.vue';

export interface EmbedBlockAttributes {
  url: string;
  title?: string;
  description?: string;
  image?: string;
  favicon?: string;
  siteName?: string;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    embedBlock: {
      setEmbedBlock: (options?: Partial<EmbedBlockAttributes>) => ReturnType;
    };
  }
}

export const EmbedBlock = Node.create({
  name: 'embedBlock',
  group: 'block',
  atom: true,
  draggable: true,

  addAttributes() {
    return {
      url: { default: null },
      title: { default: null },
      description: { default: null },
      image: { default: null },
      favicon: { default: null },
      siteName: { default: null },
    };
  },

  parseHTML() {
    return [{ tag: 'div[data-type="embed"]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-type': 'embed',
        class: 'embed-node',
      }),
      ['a', { href: HTMLAttributes.url, target: '_blank', rel: 'noopener' }, HTMLAttributes.title || HTMLAttributes.url || ''],
    ];
  },

  addNodeView() {
    return VueNodeViewRenderer(EmbedComponent as any);
  },

  addCommands() {
    return {
      setEmbedBlock:
        (options?: Partial<EmbedBlockAttributes>) =>
        ({ commands }: any) => {
          return commands.insertContent({
            type: this.name,
            attrs: options || {},
          });
        },
    };
  },
});

export default EmbedBlock;
