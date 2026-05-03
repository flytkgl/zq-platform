import { requestClient } from '#/api/request';

export interface LinkPreviewData {
  url: string;
  title?: string;
  description?: string;
  image?: string;
  favicon?: string;
  site_name?: string;
}

export async function getLinkPreview(url: string): Promise<LinkPreviewData> {
  return requestClient.get<LinkPreviewData>('/api/core/link-preview', {
    params: { url },
  });
}
