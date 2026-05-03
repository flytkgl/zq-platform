import type { Editor } from '@tiptap/vue-3';

import { exportDocumentPdfApi } from '#/api/smart-table';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.append(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function sanitizeFilename(name: string): string {
  return name.replaceAll(/[<>:"/\\|?*]/g, '_').trim() || 'document';
}

const WORD_STYLES = `
  body {
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    font-size: 14px; line-height: 1.8; color: #333; padding: 20px;
  }
  h1 { font-size: 28px; font-weight: 700; margin-bottom: 16px; }
  h2 { font-size: 22px; font-weight: 600; margin-top: 24px; margin-bottom: 12px; }
  h3 { font-size: 18px; font-weight: 600; margin-top: 20px; margin-bottom: 8px; }
  p { margin: 8px 0; }
  ul, ol { padding-left: 24px; }
  blockquote { border-left: 3px solid #ddd; padding-left: 12px; margin-left: 0; color: #666; }
  pre { background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; }
  code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-size: 13px; }
  pre code { background: none; padding: 0; }
  table { border-collapse: collapse; width: 100%; margin: 12px 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
  th { background: #f5f5f5; font-weight: 600; }
  img { max-width: 100%; }
  a { color: #1a73e8; }
`;

export function useDocExport() {
  function exportMarkdown(editor: Editor, title: string) {
    const md = (editor.storage as any)?.markdown?.getMarkdown() || '';
    const content = `# ${title}\n\n${md}`;
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    downloadBlob(blob, `${sanitizeFilename(title)}.md`);
  }

  async function exportPdf(editor: Editor, title: string, tableId: string) {
    const html = editor.getHTML();
    const blob = await exportDocumentPdfApi(tableId, html, title);
    downloadBlob(blob as Blob, `${sanitizeFilename(title)}.pdf`);
  }

  async function exportWord(editor: Editor, title: string) {
    const { asBlob } = await import('html-docx-js-typescript');
    const html = editor.getHTML();
    const fullHtml = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>${WORD_STYLES}</style></head><body><h1>${title}</h1>${html}</body></html>`;
    const blob = (await asBlob(fullHtml)) as Blob;
    downloadBlob(blob, `${sanitizeFilename(title)}.docx`);
  }

  return { exportMarkdown, exportPdf, exportWord };
}
