import { mergeAttributes, Node } from '@tiptap/core';
import { VueNodeViewRenderer } from '@tiptap/vue-3';

import ResizableVideoComponent from './ResizableVideoComponent.vue';

export interface VideoOptions {
  HTMLAttributes: Record<string, any>;
  allowFullscreen: boolean;
}

export interface VideoAttributes {
  id?: string;
  src: string;
  width?: number | string;
  height?: number | string;
  alignment?: 'center' | 'left' | 'right';
  poster?: string;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    video: {
      setVideo: (options: VideoAttributes) => ReturnType;
    };
  }
}

export const Video = Node.create<VideoOptions>({
  name: 'video',

  group: 'block',

  atom: true,

  draggable: true,

  addOptions() {
    return {
      HTMLAttributes: {},
      allowFullscreen: true,
    };
  },

  addAttributes() {
    return {
      id: {
        default: null,
      },
      src: {
        default: null,
      },
      width: {
        default: '100%',
      },
      height: {
        default: 'auto',
      },
      alignment: {
        default: 'center',
      },
      poster: {
        default: null,
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="video"]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }: { HTMLAttributes: Record<string, any> }) {
    const { id, src, width, poster, alignment } = HTMLAttributes;

    let marginStyle = 'margin-left: auto; margin-right: auto;';
    if (alignment === 'left') {
      marginStyle = 'margin-right: auto;';
    } else if (alignment === 'right') {
      marginStyle = 'margin-left: auto;';
    }

    return [
      'div',
      mergeAttributes(this.options.HTMLAttributes, {
        'data-type': 'video',
        'data-id': id,
        class: 'video-node',
        style: `max-width: ${typeof width === 'number' ? `${width}px` : width}; ${marginStyle}`,
      }),
      [
        'video',
        {
          src,
          controls: true,
          poster,
          style: 'width: 100%; height: auto; border-radius: 8px;',
        },
        '您的浏览器不支持视频播放',
      ],
    ];
  },

  addNodeView() {
    return VueNodeViewRenderer(ResizableVideoComponent as any);
  },

  addCommands() {
    return {
      setVideo:
        (options: VideoAttributes) =>
        ({ commands }: { commands: any }) => {
          return commands.insertContent({
            type: this.name,
            attrs: options,
          });
        },
    };
  },
});

export default Video;
