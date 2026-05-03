import type { Editor } from '@tiptap/vue-3';

import type { FileUploadOptions } from '../types';

import { $t } from '@vben/locales';

import { ElMessage } from 'element-plus';

import { uploadFile } from '#/api/core/file';
import { getFileUrl } from '#/composables/useFileUrl';

const IMAGE_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'image/svg+xml',
];
const VIDEO_TYPES = [
  'video/mp4',
  'video/webm',
  'video/ogg',
  'video/quicktime',
];
const DEFAULT_MAX_SIZE = 50 * 1024 * 1024; // 50MB

export function useFileUpload(
  editor: () => Editor | undefined,
  options?: FileUploadOptions,
) {
  const maxSize = options?.maxSize || DEFAULT_MAX_SIZE;

  async function handleFile(file: File): Promise<void> {
    const e = editor();
    if (!e) return;

    if (file.size > maxSize) {
      ElMessage.warning($t('zq-editor.upload.fileSizeExceeds'));
      return;
    }

    if (IMAGE_TYPES.includes(file.type)) {
      await uploadImage(e, file);
    } else if (VIDEO_TYPES.includes(file.type)) {
      await uploadVideo(e, file);
    } else {
      await uploadAttachment(e, file);
    }
  }

  async function uploadImage(e: Editor, file: File) {
    const placeholderSrc = URL.createObjectURL(file);
    e.chain()
      .focus()
      .setImageBlock({ src: placeholderSrc, alt: file.name })
      .run();

    try {
      const result = await uploadFile(file, {
        parentId: options?.parentId,
        source: options?.source || 'editor',
      });

      const fileData = result as any;
      const fileId = fileData.id || fileData.file_id;
      const url = await getFileUrl(fileId);

      const { state } = e;
      const { doc } = state;
      let targetPos = -1;

      doc.descendants((node, pos) => {
        if (
          node.type.name === 'imageBlock' &&
          node.attrs.src === placeholderSrc
        ) {
          targetPos = pos;
          return false;
        }
        return true;
      });

      if (targetPos >= 0) {
        e.chain()
          .setNodeSelection(targetPos)
          .updateAttributes('imageBlock', {
            src: url,
            fileId,
          })
          .run();
      }
    } catch {
      ElMessage.error($t('zq-editor.upload.imageUploadFailed'));
      removePlaceholderNode(e, placeholderSrc);
    } finally {
      URL.revokeObjectURL(placeholderSrc);
    }
  }

  function removePlaceholderNode(e: Editor, placeholderSrc: string) {
    const { doc } = e.state;
    let targetPos = -1;
    doc.descendants((node, pos) => {
      if (
        node.type.name === 'imageBlock' &&
        node.attrs.src === placeholderSrc
      ) {
        targetPos = pos;
        return false;
      }
      return true;
    });
    if (targetPos >= 0) {
      e.chain().setNodeSelection(targetPos).deleteSelection().run();
    }
  }

  async function uploadVideo(e: Editor, file: File) {
    try {
      const result = await uploadFile(file, {
        parentId: options?.parentId,
        source: options?.source || 'editor',
      });

      const fileData = result as any;
      const fileId = fileData.id || fileData.file_id;
      const url = await getFileUrl(fileId);

      e.chain().focus().setVideoBlock({ src: url, id: fileId }).run();
    } catch {
      ElMessage.error($t('zq-editor.upload.videoUploadFailed'));
    }
  }

  async function uploadAttachment(e: Editor, file: File) {
    try {
      const result = await uploadFile(file, {
        parentId: options?.parentId,
        source: options?.source || 'editor',
      });

      const fileData = result as any;
      const fileId = fileData.id || fileData.file_id;
      const url = await getFileUrl(fileId);

      e.chain()
        .focus()
        .setAttachmentBlock({
          id: fileId,
          name: file.name,
          size: file.size,
          type: file.type,
          url,
        })
        .run();
    } catch {
      ElMessage.error($t('zq-editor.upload.attachmentUploadFailed'));
    }
  }

  function handleDrop(event: DragEvent) {
    const files = event.dataTransfer?.files;
    if (!files?.length) return;

    event.preventDefault();
    const fileArray = Array.from(files);
    (async () => {
      for (const file of fileArray) {
        await handleFile(file);
      }
    })();
  }

  function handlePaste(event: ClipboardEvent) {
    const items = event.clipboardData?.items;
    if (!items) return;

    for (const item of items) {
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) {
          event.preventDefault();
          handleFile(file);
          return;
        }
      }
    }
  }

  return {
    handleFile,
    handleDrop,
    handlePaste,
  };
}
