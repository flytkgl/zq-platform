import { requestClient } from '#/api/request';

export interface FieldPermission {
  field_name: string;
  permission_type: 'hidden' | 'masked' | 'read' | 'write';
  mask_rule?: 'default' | 'email' | 'id_card' | 'name' | 'phone';
}

export interface FieldPermissionConfig extends FieldPermission {
  id: string;
  role_id: string;
  resource_type: string;
  sort: number;
  is_deleted: boolean;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface FieldPermissionBatchUpdate {
  role_id: string;
  resource_type: string;
  configs: FieldPermission[];
}

export interface ResourceFieldMetadata {
  field_name: string;
  label: string;
  field_type: string;
  required?: boolean;
  sensitive: boolean;
  maskable: boolean;
  default_permission: string;
}

export interface ResourceFieldsMetadata {
  resource_type: string;
  display_name: string;
  fields: ResourceFieldMetadata[];
}

/**
 * 获取所有资源的字段元数据
 * @param applicationId 应用ID，子应用访问时只显示该应用的资源
 */
export async function getAllResourceFieldsApi(applicationId?: string) {
  return requestClient.get<ResourceFieldsMetadata[]>(
    '/api/core/field-permissions/resource-fields',
    {
      params: applicationId ? { applicationId } : undefined,
    },
  );
}

/**
 * 获取指定资源的字段元数据
 */
export async function getResourceFieldsApi(resourceType: string) {
  return requestClient.get<ResourceFieldsMetadata>(
    `/api/core/field-permissions/resource-fields/${resourceType}`,
  );
}

/**
 * 获取角色的字段权限配置
 */
export async function getRoleFieldPermissionsApi(
  roleId: string,
  resourceType: string,
) {
  return requestClient.get<FieldPermissionConfig[]>(
    `/api/core/field-permissions/${roleId}`,
    {
      params: { resource_type: resourceType },
    },
  );
}

/**
 * 批量更新字段权限配置
 */
export async function batchUpdateFieldPermissionsApi(
  data: FieldPermissionBatchUpdate,
) {
  return requestClient.post('/api/core/field-permissions/batch', data);
}

/**
 * 删除角色的字段权限配置
 */
export async function deleteRoleFieldPermissionsApi(
  roleId: string,
  resourceType: string,
) {
  return requestClient.delete(`/api/core/field-permissions/${roleId}`, {
    params: { resource_type: resourceType },
  });
}

/**
 * 权限类型选项
 */
export const PERMISSION_TYPE_OPTIONS = [
  { label: '可读', value: 'read' },
  { label: '可写', value: 'write' },
  { label: '隐藏', value: 'hidden' },
  { label: '脱敏', value: 'masked' },
];

/**
 * 脱敏规则选项
 */
export const MASK_RULE_OPTIONS = [
  { label: '手机号', value: 'phone' },
  { label: '邮箱', value: 'email' },
  { label: '身份证', value: 'id_card' },
  { label: '姓名', value: 'name' },
  { label: '默认', value: 'default' },
];
