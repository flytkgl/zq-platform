import { mergeAttributes, Node } from '@tiptap/core';

export interface AttachmentOptions {
  HTMLAttributes: Record<string, any>;
}

export interface AttachmentAttributes {
  id: string;
  name: string;
  size: number;
  type: string;
  url: string;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    attachment: {
      setAttachment: (options: AttachmentAttributes) => ReturnType;
    };
  }
}

export const Attachment = Node.create<AttachmentOptions>({
  name: 'attachment',

  group: 'block',

  atom: true,

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      id: {
        default: null,
      },
      name: {
        default: null,
      },
      size: {
        default: 0,
      },
      type: {
        default: null,
      },
      url: {
        default: null,
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="attachment"]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }: { HTMLAttributes: Record<string, any> }) {
    const { id, name, size, type, url } = HTMLAttributes;
    return [
      'div',
      mergeAttributes(this.options.HTMLAttributes, {
        'data-type': 'attachment',
        'data-id': id,
        'data-name': name,
        'data-size': size,
        'data-file-type': type,
        'data-url': url,
        class: 'attachment-node',
      }),
      [
        'a',
        {
          href: url,
          target: '_blank',
          download: name,
          class: 'attachment-link',
        },
        ['span', { class: 'attachment-icon' }, '📎'],
        ['span', { class: 'attachment-name' }, name],
        ['span', { class: 'attachment-size' }, formatFileSize(size)],
      ],
    ];
  },

  addCommands() {
    return {
      setAttachment:
        (options: AttachmentAttributes) =>
        ({ commands }: { commands: any }) => {
          return commands.insertContent({
            type: this.name,
            attrs: options,
          });
        },
    };
  },
});

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Number.parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`;
}

export default Attachment;
