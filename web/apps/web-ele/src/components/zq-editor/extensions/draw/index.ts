import { mergeAttributes, Node } from '@tiptap/core';
import { VueNodeViewRenderer } from '@tiptap/vue-3';

import DrawBlockComponent from './DrawBlockComponent.vue';

export interface DrawBlockAttributes {
  data: string;
  width: number;
  height: number;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    drawBlock: {
      setDrawBlock: (options?: Partial<DrawBlockAttributes>) => ReturnType;
    };
  }
}

export const DrawBlock = Node.create({
  name: 'drawBlock',
  group: 'block',
  atom: true,
  draggable: true,

  addAttributes() {
    return {
      data: { default: null },
      width: { default: 800 },
      height: { default: 450 },
    };
  },

  parseHTML() {
    return [{ tag: 'div[data-type="draw"]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-type': 'draw',
        class: 'draw-node',
      }),
      ['span', { class: 'draw-node__placeholder' }, 'Draw'],
    ];
  },

  addNodeView() {
    return VueNodeViewRenderer(DrawBlockComponent as any);
  },

  addCommands() {
    return {
      setDrawBlock:
        (options?: Partial<DrawBlockAttributes>) =>
        ({ commands }: any) => {
          return commands.insertContent({
            type: this.name,
            attrs: options || {},
          });
        },
    };
  },
});

export default DrawBlock;
