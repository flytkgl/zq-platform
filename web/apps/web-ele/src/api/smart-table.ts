import { requestClient } from '#/api/request';

const BASE = '/api/smart-table';

// ==================== Types ====================

export interface SmartTableItem {
  id: string;
  name: string;
  icon: string;
  type?: string;
  parent_id?: string | null;
  sort?: number;
  description?: string;
  active_view_id?: string;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
}

export interface SmartFieldItem {
  id: string;
  table_id: string;
  name: string;
  type: string;
  width: number;
  visible: boolean;
  required: boolean;
  description?: string;
  config: Record<string, any>;
  sort: number;
  sys_create_datetime?: string;
}

export interface SmartRecordItem {
  id: string;
  table_id: string;
  values: Record<string, any>;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
  sys_creator_id?: string;
  sys_modifier_id?: string;
}

export interface SmartViewItem {
  id: string;
  table_id: string;
  name: string;
  type: string;
  config: Record<string, any>;
  sort: number;
  sys_create_datetime?: string;
}

export interface SmartTableFull extends SmartTableItem {
  type?: string;
  content?: any;
  fields: SmartFieldItem[];
  records: SmartRecordItem[];
  views: SmartViewItem[];
  record_total: number;
  next_cursor: string | null;
  has_more: boolean;
  sys_creator_id?: string;
  creator_name?: string;
  creator_avatar?: string;
}

export interface CursorPaginatedRecords {
  items: SmartRecordItem[];
  total: number;
  next_cursor: string | null;
  has_more: boolean;
}

export interface RecordFilterParam {
  field_id: string;
  operator: string;
  value?: any;
}

export interface RecordSortParam {
  field_id: string;
  direction: 'asc' | 'desc';
}

export interface RecordQueryParam {
  filters?: RecordFilterParam[];
  filter_logic?: 'and' | 'or';
  sorts?: RecordSortParam[];
  search?: string;
  search_field_ids?: string[];
  group_field_id?: string;
  cursor?: string | null;
  limit?: number;
}

export interface RecordGroupItem {
  key: string;
  label: string;
  records: SmartRecordItem[];
}

export interface GroupedRecordsResponse {
  groups: RecordGroupItem[];
  total: number;
}

// ==================== Table API ====================

export function getTableListApi(wikiSpaceId?: string | null) {
  const params: Record<string, any> = {};
  if (wikiSpaceId) params.wiki_space_id = wikiSpaceId;
  return requestClient.get<SmartTableItem[]>(`${BASE}/tables`, { params });
}

export function getTableFullApi(
  tableId: string,
  opts?: { filters?: RecordFilterParam[]; sorts?: RecordSortParam[]; search?: string; filter_logic?: string },
) {
  const params: Record<string, any> = {};
  if (opts?.filters?.length) params.filters = JSON.stringify(opts.filters);
  if (opts?.sorts?.length) params.sorts = JSON.stringify(opts.sorts);
  if (opts?.search) params.search = opts.search;
  if (opts?.filter_logic) params.filter_logic = opts.filter_logic;
  return requestClient.get<SmartTableFull>(`${BASE}/tables/${tableId}/full`, { params });
}

export function createTableApi(data: { name: string; icon?: string; description?: string; type?: string; content?: any; parent_id?: string | null; wiki_space_id?: string | null }) {
  return requestClient.post<SmartTableItem>(`${BASE}/tables`, data);
}

export function updateTableApi(tableId: string, data: Partial<SmartTableItem>) {
  return requestClient.put<SmartTableItem>(`${BASE}/tables/${tableId}`, data);
}

export function updateDocumentContentApi(tableId: string, content: any) {
  return requestClient.patch(`${BASE}/tables/${tableId}/content`, { content });
}

export function exportDocumentPdfApi(tableId: string, html: string, title: string) {
  return requestClient.post<Blob>(`${BASE}/tables/${tableId}/export-pdf`, { html, title }, {
    responseType: 'blob',
  });
}

export function deleteTableApi(tableId: string) {
  return requestClient.delete(`${BASE}/tables/${tableId}`);
}

export function moveTableApi(tableId: string, parentId: string | null, afterId?: string | null) {
  return requestClient.put<SmartTableItem>(`${BASE}/tables/${tableId}/move`, {
    parent_id: parentId,
    after_id: afterId ?? null,
  });
}

// ==================== Field API ====================

export function getFieldListApi(tableId: string) {
  return requestClient.get<SmartFieldItem[]>(`${BASE}/tables/${tableId}/fields`);
}

export function createFieldApi(tableId: string, data: Omit<SmartFieldItem, 'id' | 'table_id' | 'sys_create_datetime'>) {
  return requestClient.post<SmartFieldItem>(`${BASE}/tables/${tableId}/fields`, data);
}

export function updateFieldApi(fieldId: string, data: Partial<SmartFieldItem>) {
  return requestClient.put<SmartFieldItem>(`${BASE}/fields/${fieldId}`, data);
}

export function deleteFieldApi(fieldId: string) {
  return requestClient.delete(`${BASE}/fields/${fieldId}`);
}

export function reorderFieldsApi(tableId: string, fieldIds: string[]) {
  return requestClient.put(`${BASE}/tables/${tableId}/fields/reorder`, { field_ids: fieldIds });
}

// ==================== Record API ====================

export function getRecordListApi(
  tableId: string,
  cursor?: string | null,
  limit = 200,
  opts?: { filters?: RecordFilterParam[]; sorts?: RecordSortParam[]; search?: string; filter_logic?: string },
) {
  const params: Record<string, any> = { cursor: cursor ?? undefined, limit };
  if (opts?.filters?.length) params.filters = JSON.stringify(opts.filters);
  if (opts?.sorts?.length) params.sorts = JSON.stringify(opts.sorts);
  if (opts?.search) params.search = opts.search;
  if (opts?.filter_logic) params.filter_logic = opts.filter_logic;
  return requestClient.get<CursorPaginatedRecords>(
    `${BASE}/tables/${tableId}/records`,
    { params },
  );
}

export function queryRecordsApi(tableId: string, query: RecordQueryParam) {
  return requestClient.post<CursorPaginatedRecords | GroupedRecordsResponse>(
    `${BASE}/tables/${tableId}/records/query`,
    query,
  );
}

export function reorderRecordsApi(tableId: string, recordIds: string[]) {
  return requestClient.put(`${BASE}/tables/${tableId}/records/reorder`, { record_ids: recordIds });
}

export function createRecordApi(tableId: string, values: Record<string, any> = {}) {
  return requestClient.post<SmartRecordItem>(`${BASE}/tables/${tableId}/records`, { table_id: tableId, values });
}

export function updateRecordApi(recordId: string, values: Record<string, any>) {
  return requestClient.put<SmartRecordItem>(`${BASE}/records/${recordId}`, { values });
}

export function updateCellApi(recordId: string, fieldId: string, value: any) {
  return requestClient.patch<SmartRecordItem>(`${BASE}/records/${recordId}/cells`, {
    field_id: fieldId,
    value,
  });
}

export function batchUpdateCellsApi(recordId: string, cells: Record<string, any>) {
  return requestClient.patch<SmartRecordItem>(`${BASE}/records/${recordId}/cells/batch`, { cells });
}

export function batchUpdateMultiRecordCellsApi(
  tableId: string,
  updates: Array<{ record_id: string; cells: Record<string, any> }>,
) {
  return requestClient.patch(`${BASE}/tables/${tableId}/records/batch-cells`, { updates });
}

export function deleteRecordApi(recordId: string) {
  return requestClient.delete(`${BASE}/records/${recordId}`);
}

export function batchDeleteRecordsApi(tableId: string, ids: string[]) {
  return requestClient.post(`${BASE}/tables/${tableId}/records/batch-delete`, { ids });
}

// ==================== Trash / Recycle Bin ====================

export interface TrashRecordItem {
  id: string;
  table_id: string;
  values: Record<string, any>;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
  sys_creator_id?: string;
}

export function getTrashRecordsApi(tableId: string, page = 1, pageSize = 50) {
  return requestClient.get<{ items: TrashRecordItem[]; total: number }>(
    `${BASE}/tables/${tableId}/trash`,
    { params: { page, page_size: pageSize } },
  );
}

export function restoreTrashRecordsApi(tableId: string, ids: string[]) {
  return requestClient.post(`${BASE}/tables/${tableId}/trash/restore`, { ids });
}

export function permanentDeleteTrashRecordApi(tableId: string, recordId: string) {
  return requestClient.delete(`${BASE}/tables/${tableId}/trash/${recordId}`);
}

export function emptyTrashApi(tableId: string) {
  return requestClient.delete(`${BASE}/tables/${tableId}/trash`);
}

export function exportTableApi(tableId: string, format: 'csv' | 'xlsx' = 'csv') {
  return requestClient.get(`${BASE}/tables/${tableId}/export`, {
    params: { format },
    responseType: 'blob',
  });
}

export function importTableApi(tableId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return requestClient.post(`${BASE}/tables/${tableId}/import`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

export interface RecordSearchResultItem {
  id: string;
  title: string;
}

export function searchRecordsApi(tableId: string, keyword: string = '', limit: number = 20) {
  return requestClient.post<RecordSearchResultItem[]>(
    `${BASE}/tables/${tableId}/records/search`,
    { keyword, limit },
  );
}

// ==================== Summary API ====================

export interface SummaryResult {
  summaries: Record<string, any>;
  total_count: number;
}

export function getSummaryApi(
  tableId: string,
  data: {
    aggregations: Record<string, string>;
    filters?: RecordFilterParam[];
    filter_logic?: string;
    search?: string;
  },
) {
  return requestClient.post<SummaryResult>(`${BASE}/tables/${tableId}/summary`, data);
}

// ==================== Comment API ====================

export interface CommentItem {
  id: string;
  record_id: string;
  user_id: string;
  content: string;
  mentions: string[];
  parent_id: string | null;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
  user_name?: string;
  user_avatar?: string;
  replies: CommentItem[];
}

export function getCommentsApi(recordId: string) {
  return requestClient.get<CommentItem[]>(`${BASE}/records/${recordId}/comments`);
}

export function createCommentApi(recordId: string, data: { content: string; mentions?: string[]; parent_id?: string }) {
  return requestClient.post<CommentItem>(`${BASE}/records/${recordId}/comments`, data);
}

export function updateCommentApi(commentId: string, data: { content: string; mentions?: string[] }) {
  return requestClient.put<CommentItem>(`${BASE}/comments/${commentId}`, data);
}

export function deleteCommentApi(commentId: string) {
  return requestClient.delete(`${BASE}/comments/${commentId}`);
}

// ==================== View API ====================

export function getViewListApi(tableId: string) {
  return requestClient.get<SmartViewItem[]>(`${BASE}/tables/${tableId}/views`);
}

export function createViewApi(tableId: string, data: { name: string; type: string; config?: Record<string, any> }) {
  return requestClient.post<SmartViewItem>(`${BASE}/tables/${tableId}/views`, { ...data, table_id: tableId });
}

export function updateViewApi(viewId: string, data: Partial<SmartViewItem>) {
  return requestClient.put<SmartViewItem>(`${BASE}/views/${viewId}`, data);
}

export function deleteViewApi(viewId: string) {
  return requestClient.delete(`${BASE}/views/${viewId}`);
}

// ==================== Permission API ====================

export interface MyPermission {
  role_type: string;
  role_name: string;
  capabilities: Record<string, boolean>;
  field_permissions: Record<string, string>;
  row_view_mode: string;
  row_edit_mode: string;
}

export interface TableRole {
  id: string;
  table_id: string | null;
  name: string;
  role_type: string;
  capabilities: Record<string, boolean>;
  is_system: boolean;
  sys_create_datetime?: string;
}

export interface Collaborator {
  id: string;
  table_id: string;
  subject_type: string;
  subject_id: string;
  role_id: string;
  role_name?: string;
  role_type?: string;
  subject_name?: string;
  subject_avatar?: string;
  sys_create_datetime?: string;
}

export interface FieldPermItem {
  field_id: string;
  access: string;
}

export interface FieldPermMatrix {
  role_id: string;
  role_name: string;
  role_type: string;
  fields: FieldPermItem[];
}

export interface RowRule {
  id: string;
  table_id: string;
  role_id: string;
  rule_type: string;
  mode: string;
  conditions: Record<string, any>[];
}

export function getMyPermissionApi(tableId: string) {
  return requestClient.get<MyPermission>(`${BASE}/tables/${tableId}/my-permission`);
}

export function getRolesApi(tableId: string) {
  return requestClient.get<TableRole[]>(`${BASE}/tables/${tableId}/roles`);
}

export function createRoleApi(tableId: string, data: { name: string; capabilities: Record<string, boolean> }) {
  return requestClient.post<TableRole>(`${BASE}/tables/${tableId}/roles`, data);
}

export function updateRoleApi(tableId: string, roleId: string, data: { name?: string; capabilities?: Record<string, boolean> }) {
  return requestClient.put<TableRole>(`${BASE}/tables/${tableId}/roles/${roleId}`, data);
}

export function deleteRoleApi(tableId: string, roleId: string) {
  return requestClient.delete(`${BASE}/tables/${tableId}/roles/${roleId}`);
}

export function getCollaboratorsApi(tableId: string) {
  return requestClient.get<Collaborator[]>(`${BASE}/tables/${tableId}/collaborators`);
}

export function addCollaboratorApi(tableId: string, data: { subject_type: string; subject_id: string; role_id: string }) {
  return requestClient.post<Collaborator>(`${BASE}/tables/${tableId}/collaborators`, data);
}

export function updateCollaboratorApi(tableId: string, collabId: string, data: { role_id: string }) {
  return requestClient.put<Collaborator>(`${BASE}/tables/${tableId}/collaborators/${collabId}`, data);
}

export function removeCollaboratorApi(tableId: string, collabId: string) {
  return requestClient.delete(`${BASE}/tables/${tableId}/collaborators/${collabId}`);
}

export function getFieldPermissionsApi(tableId: string) {
  return requestClient.get<FieldPermMatrix[]>(`${BASE}/tables/${tableId}/field-permissions`);
}

export function updateFieldPermissionsApi(tableId: string, data: { role_id: string; permissions: FieldPermItem[] }) {
  return requestClient.put(`${BASE}/tables/${tableId}/field-permissions`, data);
}

export function getRowRulesApi(tableId: string) {
  return requestClient.get<RowRule[]>(`${BASE}/tables/${tableId}/row-rules`);
}

export function updateRowRuleApi(tableId: string, data: { role_id: string; rule_type: string; mode: string; conditions: Record<string, any>[] }) {
  return requestClient.put<RowRule>(`${BASE}/tables/${tableId}/row-rules`, data);
}

// ==================== Document Version API ====================

export interface DocumentVersionItem {
  id: string;
  document_id: string;
  version: number;
  title?: string;
  change_summary?: string;
  content_size: number;
  sys_create_datetime?: string;
  sys_creator_id?: string;
  creator_name?: string;
  creator_avatar?: string;
}

export interface DocumentVersionDetail extends DocumentVersionItem {
  content: Record<string, any>;
}

export interface DocumentVersionCompare {
  version_from: DocumentVersionDetail;
  version_to: DocumentVersionDetail;
}

export function getDocumentVersionsApi(tableId: string, page = 1, pageSize = 20) {
  return requestClient.get<{ items: DocumentVersionItem[]; total: number }>(
    `${BASE}/tables/${tableId}/versions`,
    { params: { page, pageSize } },
  );
}

export function getDocumentVersionDetailApi(versionId: string) {
  return requestClient.get<DocumentVersionDetail>(`${BASE}/versions/${versionId}`);
}

export function createDocumentVersionApi(tableId: string, changeSummary?: string) {
  return requestClient.post<DocumentVersionItem>(
    `${BASE}/tables/${tableId}/versions`,
    { change_summary: changeSummary },
  );
}

export function restoreDocumentVersionApi(tableId: string, versionId: string) {
  return requestClient.post(`${BASE}/tables/${tableId}/versions/${versionId}/restore`);
}

export function compareDocumentVersionsApi(tableId: string, fromId: string, toId: string) {
  return requestClient.get<DocumentVersionCompare>(
    `${BASE}/tables/${tableId}/versions/compare`,
    { params: { from: fromId, to: toId } },
  );
}

export function deleteDocumentVersionApi(versionId: string) {
  return requestClient.delete(`${BASE}/versions/${versionId}`);
}

// ==================== Document Template API ====================

export interface DocumentTemplateItem {
  id: string;
  name: string;
  description?: string;
  icon: string;
  category: string;
  preview_image?: string;
  is_system: boolean;
  use_count: number;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
  sys_creator_id?: string;
  creator_name?: string;
}

export interface DocumentTemplateDetail extends DocumentTemplateItem {
  content: Record<string, any>;
}

export function getDocumentTemplatesApi(params?: { category?: string; keyword?: string; page?: number; pageSize?: number }) {
  return requestClient.get<{ items: DocumentTemplateItem[]; total: number }>(
    `${BASE}/document-templates`,
    { params },
  );
}

export function getDocumentTemplateCategoriesApi() {
  return requestClient.get<string[]>(`${BASE}/document-templates/categories`);
}

export function getDocumentTemplateDetailApi(templateId: string) {
  return requestClient.get<DocumentTemplateDetail>(`${BASE}/document-templates/${templateId}`);
}

export function createDocumentTemplateApi(data: {
  name: string;
  description?: string;
  icon?: string;
  category?: string;
  content: Record<string, any>;
  preview_image?: string;
}) {
  return requestClient.post<DocumentTemplateItem>(`${BASE}/document-templates`, data);
}

export function createTemplateFromDocumentApi(documentId: string, data: {
  name: string;
  description?: string;
  category?: string;
  content: Record<string, any>;
}) {
  return requestClient.post<DocumentTemplateItem>(
    `${BASE}/document-templates/from-document/${documentId}`,
    data,
  );
}

export function updateDocumentTemplateApi(templateId: string, data: {
  name?: string;
  description?: string;
  icon?: string;
  category?: string;
  content?: Record<string, any>;
  preview_image?: string;
}) {
  return requestClient.put<DocumentTemplateItem>(`${BASE}/document-templates/${templateId}`, data);
}

export function deleteDocumentTemplateApi(templateId: string) {
  return requestClient.delete(`${BASE}/document-templates/${templateId}`);
}

export function useDocumentTemplateApi(templateId: string) {
  return requestClient.post(`${BASE}/document-templates/${templateId}/use`);
}

// ==================== Wiki Space API ====================

export interface WikiSpaceItem {
  id: string;
  name: string;
  icon: string;
  avatar?: string | null;
  description?: string;
  cover?: string;
  category: string;
  visibility: string;
  sort: number;
  document_count?: number;
  sys_create_datetime?: string;
  sys_update_datetime?: string;
  sys_creator_id?: string;
  creator_name?: string;
}

export interface WikiSpaceDetail extends WikiSpaceItem {
  documents: SmartTableItem[];
}

export function getWikiSpacesApi() {
  return requestClient.get<WikiSpaceItem[]>(`${BASE}/wiki-spaces`);
}

export function getWikiSpaceDetailApi(spaceId: string) {
  return requestClient.get<WikiSpaceDetail>(`${BASE}/wiki-spaces/${spaceId}`);
}

export function createWikiSpaceApi(data: {
  name: string;
  icon?: string;
  avatar?: string | null;
  description?: string;
  cover?: string;
  category?: string;
  visibility?: string;
}) {
  return requestClient.post<WikiSpaceItem>(`${BASE}/wiki-spaces`, data);
}

export function updateWikiSpaceApi(spaceId: string, data: Partial<WikiSpaceItem>) {
  return requestClient.put<WikiSpaceItem>(`${BASE}/wiki-spaces/${spaceId}`, data);
}

export function deleteWikiSpaceApi(spaceId: string) {
  return requestClient.delete(`${BASE}/wiki-spaces/${spaceId}`);
}

export function getWikiSpaceDocumentsApi(spaceId: string) {
  return requestClient.get<SmartTableItem[]>(`${BASE}/wiki-spaces/${spaceId}/documents`);
}

export function createWikiDocumentApi(spaceId: string, data: {
  name: string;
  parent_id?: string | null;
  content?: any;
}) {
  return requestClient.post<SmartTableItem>(
    `${BASE}/wiki-spaces/${spaceId}/documents`,
    { ...data, type: 'document', icon: 'FileText' },
  );
}
