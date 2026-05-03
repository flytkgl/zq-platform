import Image from '@tiptap/extension-image';
import { VueNodeViewRenderer } from '@tiptap/vue-3';

import ResizableImageComponent from './ResizableImageComponent.vue';

export const ResizableImage = Image.extend({
  name: 'resizableImage',

  addAttributes() {
    return {
      ...this.parent?.(),
      width: {
        default: null,
        parseHTML: (element) =>
          element.getAttribute('width') ||
          element.style.width?.replace('px', ''),
        renderHTML: (attributes) => {
          if (!attributes.width) return {};
          return { width: attributes.width };
        },
      },
      height: {
        default: null,
        parseHTML: (element) =>
          element.getAttribute('height') ||
          element.style.height?.replace('px', ''),
        renderHTML: (attributes) => {
          if (!attributes.height) return {};
          return { height: attributes.height };
        },
      },
      alignment: {
        default: 'center',
        parseHTML: (element) => element.dataset.alignment || 'center',
        renderHTML: (attributes) => {
          const alignment = attributes.alignment || 'center';
          // 同时输出 data-alignment 和 style
          const styleMap: Record<string, string> = {
            left: 'display: block; margin-left: 0; margin-right: auto;',
            center: 'display: block; margin-left: auto; margin-right: auto;',
            right: 'display: block; margin-left: auto; margin-right: 0;',
          };
          return {
            'data-alignment': alignment,
            style: styleMap[alignment] || styleMap.center,
          };
        },
      },
    };
  },

  addNodeView() {
    return VueNodeViewRenderer(ResizableImageComponent as any);
  },
});

export default ResizableImage;
