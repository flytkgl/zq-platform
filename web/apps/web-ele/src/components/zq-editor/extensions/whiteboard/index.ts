import { mergeAttributes, Node } from '@tiptap/core';
import { VueNodeViewRenderer } from '@tiptap/vue-3';

import WhiteboardBlockComponent from './WhiteboardBlockComponent.vue';

export interface WhiteboardBlockAttributes {
  data: string;
  thumbnail: string;
  width: number;
  height: number;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    whiteboardBlock: {
      setWhiteboardBlock: (
        options?: Partial<WhiteboardBlockAttributes>,
      ) => ReturnType;
    };
  }
}

export const WhiteboardBlock = Node.create({
  name: 'whiteboardBlock',
  group: 'block',
  atom: true,
  draggable: true,

  addAttributes() {
    return {
      data: { default: null },
      thumbnail: { default: null },
      width: { default: 800 },
      height: { default: 450 },
    };
  },

  parseHTML() {
    return [{ tag: 'div[data-type="whiteboard"]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-type': 'whiteboard',
        class: 'whiteboard-node',
      }),
      HTMLAttributes.thumbnail
        ? [
            'img',
            {
              src: HTMLAttributes.thumbnail,
              alt: 'Whiteboard',
              style: `max-width: 100%; height: auto;`,
            },
          ]
        : ['span', {}, 'Whiteboard'],
    ];
  },

  addNodeView() {
    return VueNodeViewRenderer(WhiteboardBlockComponent as any);
  },

  addCommands() {
    return {
      setWhiteboardBlock:
        (options?: Partial<WhiteboardBlockAttributes>) =>
        ({ commands }: any) => {
          return commands.insertContent({
            type: this.name,
            attrs: options || {},
          });
        },
    };
  },
});

export default WhiteboardBlock;
