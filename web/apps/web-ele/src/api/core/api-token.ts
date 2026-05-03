/**
 * API Token (Personal Access Token) 管理
 */
import { requestClient } from '#/api/request';

export namespace ApiTokenApi {
  export interface TokenItem {
    id: string;
    name: string;
    token_prefix: string;
    expires_at?: null | string;
    last_used_at?: null | string;
    description?: null | string;
    is_active: boolean;
    sys_create_datetime?: null | string;
  }

  export interface CreateTokenRequest {
    name: string;
    expires_at?: null | string;
    description?: string;
  }

  export interface CreateTokenResponse {
    id: string;
    name: string;
    token: string;
    token_prefix: string;
    expires_at?: null | string;
    description?: null | string;
    sys_create_datetime?: null | string;
  }
}

export async function getApiTokenListApi() {
  return requestClient.get<ApiTokenApi.TokenItem[]>('/api/core/api-tokens');
}

export async function createApiTokenApi(data: ApiTokenApi.CreateTokenRequest) {
  return requestClient.post<ApiTokenApi.CreateTokenResponse>(
    '/api/core/api-tokens',
    data,
  );
}

export async function revokeApiTokenApi(tokenId: string) {
  return requestClient.delete(`/api/core/api-tokens/${tokenId}`);
}
