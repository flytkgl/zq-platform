<script lang="ts" setup>
import type { FormMeta, FormSubTable } from '#/api/online-dev/form-manager';

import { computed, ref, watch } from 'vue';

import { Code, Copy, Lock } from '@vben/icons';
import { $t } from '@vben/locales';

import {
  ElButton,
  ElDivider,
  ElMessage,
  ElScrollbar,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTooltip,
} from 'element-plus';

import { getFormDetailApi } from '#/api/online-dev/form-manager';
import { ZqDialog } from '#/components/zq-dialog';

interface Props {
  formId: string;
  formCode: string;
  formName: string;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>({ default: false });

const loading = ref(false);
const formDetail = ref<FormMeta | null>(null);
const selectedApiIndex = ref(0);

interface FieldInfo {
  field: string;
  label: string;
  type: string;
  required?: boolean;
  subTable?: string;
}

const mainFields = ref<FieldInfo[]>([]);
const subTableFields = ref<Record<string, FieldInfo[]>>({});
const subTables = ref<FormSubTable[]>([]);

function extractFieldsFromItems(items: any[], tableName?: string): FieldInfo[] {
  const fields: FieldInfo[] = [];
  if (!items || !Array.isArray(items)) return fields;

  for (const item of items) {
    if (item.type === 'grid' && item.columns) {
      for (const col of item.columns) {
        fields.push(...extractFieldsFromItems(col.children || [], tableName));
      }
    } else if (item.type === 'tabs' && item.items) {
      for (const tab of item.items) {
        fields.push(...extractFieldsFromItems(tab.children || [], tableName));
      }
    } else if (item.type === 'collapse' && item.items) {
      for (const panel of item.items) {
        fields.push(...extractFieldsFromItems(panel.children || [], tableName));
      }
    } else if (item.type === 'sub-table' && item.field && item.children) {
      const stName = item.field;
      const stFields = extractFieldsFromItems(item.children, stName);
      subTableFields.value[stName] = stFields;
    } else if (item.field) {
      fields.push({
        field: item.field,
        label: item.label || item.field,
        type: item.type || 'input',
        required: item.required || false,
        subTable: tableName,
      });
    }
  }
  return fields;
}

function extractFieldsFromTableConfigs(
  tableConfigs: any[],
): { main: FieldInfo[]; sub: Record<string, FieldInfo[]> } {
  const mainResult: FieldInfo[] = [];
  const subResult: Record<string, FieldInfo[]> = {};
  const systemFieldSet = new Set([
    'id', 'sort', 'is_deleted',
    'sys_create_datetime', 'sys_update_datetime',
    'sys_creator_id', 'sys_modifier_id', 'sys_dept_id',
  ]);

  for (const tc of tableConfigs) {
    if (!tc.fields || !Array.isArray(tc.fields)) continue;
    const fields: FieldInfo[] = tc.fields
      .filter((f: any) => !systemFieldSet.has(f.name))
      .map((f: any) => ({
        field: f.name,
        label: f.comment || f.name,
        type: f.type || 'VARCHAR',
        required: !f.nullable,
      }));

    if (tc.type === 'main') {
      mainResult.push(...fields);
    } else if (tc.type === 'sub') {
      subResult[tc.tableName || tc.alias || 'sub'] = fields;
    }
  }
  return { main: mainResult, sub: subResult };
}

async function loadFormDetail() {
  if (!props.formId) return;
  loading.value = true;
  try {
    const detail = await getFormDetailApi(props.formId);
    formDetail.value = detail;
    subTables.value = detail.sub_tables || [];

    subTableFields.value = {};
    mainFields.value = [];

    // 1) Try form_config.items (form design fields with labels)
    if (detail.form_config?.items?.length) {
      mainFields.value = extractFieldsFromItems(detail.form_config.items);
    }

    // 2) Fallback: use tableConfigs (database table fields)
    if (mainFields.value.length === 0 && detail.form_config?.tableConfigs?.length) {
      const fromDb = extractFieldsFromTableConfigs(detail.form_config.tableConfigs);
      mainFields.value = fromDb.main;
      if (Object.keys(subTableFields.value).length === 0) {
        Object.assign(subTableFields.value, fromDb.sub);
      }
    }

    // 3) Merge sub-table fields from tableConfigs if not already populated from items
    if (detail.form_config?.tableConfigs?.length) {
      const fromDb = extractFieldsFromTableConfigs(detail.form_config.tableConfigs);
      for (const [name, fields] of Object.entries(fromDb.sub)) {
        if (!subTableFields.value[name] || subTableFields.value[name].length === 0) {
          subTableFields.value[name] = fields;
        }
      }
    }
  } catch {
    mainFields.value = [];
  } finally {
    loading.value = false;
  }
}

watch(visible, (val) => {
  if (val) {
    selectedApiIndex.value = 0;
    loadFormDetail();
  }
}, { immediate: true });

const BASE_PREFIX = '/api/online_dev/form-data';
const formDataBase = computed(() => `${BASE_PREFIX}/${props.formCode}`);

function buildMainFieldsJson(indent: number, withValues = true): string {
  const pad = ' '.repeat(indent);
  if (mainFields.value.length === 0) return `${pad}// ...`;
  const lines = mainFields.value.map((f) => {
    const val = withValues ? getSampleValue(f) : `"${f.type}"`;
    return `${pad}"${f.field}": ${val}`;
  });
  return lines.join(',\n');
}

function buildSubTablesJson(indent: number): string {
  const pad = ' '.repeat(indent);
  const innerPad = ' '.repeat(indent + 2);
  const fieldPad = ' '.repeat(indent + 4);
  const entries = Object.entries(subTableFields.value);
  if (entries.length === 0) return `${pad}// ...`;
  const parts = entries.map(([name, fields]) => {
    const fieldLines = fields
      .map((f) => `${fieldPad}"${f.field}": ${getSampleValue(f)}`)
      .join(',\n');
    return `${pad}"${name}": [\n${innerPad}{\n${fieldLines}\n${innerPad}}\n${pad}]`;
  });
  return parts.join(',\n');
}

function getSampleValue(f: FieldInfo): string {
  const t = f.type.toLowerCase();
  // Component types
  if (t.includes('number') || t.includes('slider') || t.includes('rate') || t.includes('money'))
    return '0';
  if (t.includes('switch')) return 'false';
  if (t.includes('date') || t.includes('time'))
    return '"2025-01-01 00:00:00"';
  if (t.includes('select') || t.includes('checkbox') || t.includes('cascader') || t.includes('tree'))
    return '[]';
  if (t.includes('file') || t.includes('image') || t.includes('upload'))
    return '[]';
  // Database column types (fallback from tableConfigs)
  if (t.includes('int') || t.includes('numeric') || t.includes('decimal') || t.includes('float') || t.includes('double') || t.includes('real') || t.includes('bigint') || t.includes('smallint'))
    return '0';
  if (t.includes('bool'))
    return 'false';
  if (t.includes('json') || t.includes('array'))
    return '[]';
  if (t.includes('timestamp') || t.includes('datetime'))
    return '"2025-01-01T00:00:00"';
  return `"string"`;
}

function buildFieldPermissionsJson(): string {
  if (mainFields.value.length === 0) return '  // ...';
  const lines = mainFields.value.slice(0, 5).map((f) => {
    return `  "${f.field}": {\n    "permission_type": "write",\n    "mask_rule": null\n  }`;
  });
  if (mainFields.value.length > 5) lines.push('  // ...');
  return lines.join(',\n');
}

function buildListResponseJson(): string {
  const fieldLines =
    mainFields.value.length > 0
      ? mainFields.value
          .slice(0, 4)
          .map((f) => `"${f.field}": ${getSampleValue(f)}`)
          .join(', ')
      : '...';
  const extra = mainFields.value.length > 4 ? ', ...' : '';
  return `{
  "items": [
    { "id": "abc123", ${fieldLines}${extra} }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}`;
}

function buildDetailResponseJson(): string {
  const hasSubTables = Object.keys(subTableFields.value).length > 0;
  let sub = '{}';
  if (hasSubTables) {
    sub = `{\n${buildSubTablesJson(4)}\n  }`;
  }
  return `{
  "main": {
    "id": "abc123",
${buildMainFieldsJson(4)}
  },
  "sub_tables": ${sub}
}`;
}

function buildCreateRequestJson(): string {
  const hasSubTables = Object.keys(subTableFields.value).length > 0;
  let sub = '{}';
  if (hasSubTables) {
    sub = `{\n${buildSubTablesJson(4)}\n  }`;
  }
  return `{
  "main": {
${buildMainFieldsJson(4)}
  },
  "sub_tables": ${sub}
}`;
}

function buildExportRequestJson(): string {
  const fieldNames =
    mainFields.value.length > 0
      ? mainFields.value
          .slice(0, 4)
          .map((f) => `"${f.field}"`)
          .join(', ')
      : '"field1", "field2"';
  const extra = mainFields.value.length > 4 ? ', ...' : '';
  return `{
  "includeSubTables": false,
  "selectedFields": [${fieldNames}${extra}]
}`;
}

interface ApiItem {
  method: 'DELETE' | 'GET' | 'POST' | 'PUT';
  path: string;
  nameKey: string;
  descKey: string;
  group: string;
  pathParams?: Array<{ name: string; type: string; description: string }>;
  queryParams?: Array<{
    name: string;
    type: string;
    required: boolean;
    description: string;
  }>;
  requestBody?: string;
  requestContentType?: string;
  responseExample: string;
  responseType?: string;
  statusCodes?: Array<{ code: number; description: string }>;
}

const apiList = computed<ApiItem[]>(() => {
  void mainFields.value;
  void subTableFields.value;
  const base = formDataBase.value;
  return [
    {
      method: 'GET',
      path: `${base}/permissions`,
      nameKey: 'form-manager.apiInfo.getPermissions',
      descKey: 'form-manager.apiInfo.getPermissionsDesc',
      group: 'permissions',
      responseExample: `{
  "view": true,
  "add": true,
  "edit": true,
  "delete": false,
  "export": true,
  "import": false
}`,
      statusCodes: [
        { code: 200, description: 'OK' },
        { code: 401, description: 'Unauthorized' },
      ],
    },
    {
      method: 'GET',
      path: `${base}/field-permissions`,
      nameKey: 'form-manager.apiInfo.getFieldPermissions',
      descKey: 'form-manager.apiInfo.getFieldPermissionsDesc',
      group: 'permissions',
      responseExample: `{\n${buildFieldPermissionsJson()}\n}`,
      statusCodes: [
        { code: 200, description: 'OK' },
        { code: 401, description: 'Unauthorized' },
      ],
    },
    {
      method: 'GET',
      path: `${base}/list`,
      nameKey: 'form-manager.apiInfo.getList',
      descKey: 'form-manager.apiInfo.getListDesc',
      group: 'dataOperations',
      queryParams: [
        {
          name: 'page',
          type: 'integer',
          required: false,
          description: 'Page number (default: 1)',
        },
        {
          name: 'pageSize',
          type: 'integer',
          required: false,
          description: 'Items per page (default: 20)',
        },
        {
          name: 'sortFields',
          type: 'string',
          required: false,
          description: 'Sort fields, comma separated',
        },
        {
          name: 'sortOrders',
          type: 'string',
          required: false,
          description: 'Sort orders: asc/desc, comma separated',
        },
        {
          name: 'search',
          type: 'string',
          required: false,
          description: 'Search keyword',
        },
        {
          name: 'search_fields',
          type: 'string',
          required: false,
          description: 'Search fields, comma separated',
        },
        {
          name: '{field}__like',
          type: 'string',
          required: false,
          description: 'Fuzzy match filter',
        },
        {
          name: '{field}__gte',
          type: 'string',
          required: false,
          description: 'Greater than or equal filter',
        },
        {
          name: '{field}__lte',
          type: 'string',
          required: false,
          description: 'Less than or equal filter',
        },
        {
          name: 'filter_{field}',
          type: 'string',
          required: false,
          description: 'Multi-value filter (comma separated)',
        },
      ],
      responseExample: buildListResponseJson(),
      statusCodes: [
        { code: 200, description: 'OK' },
        { code: 400, description: 'Bad Request' },
        { code: 403, description: 'Forbidden' },
      ],
    },
    {
      method: 'GET',
      path: `${base}/detail/{pk}`,
      nameKey: 'form-manager.apiInfo.getDetail',
      descKey: 'form-manager.apiInfo.getDetailDesc',
      group: 'dataOperations',
      pathParams: [
        { name: 'pk', type: 'string', description: 'Record primary key (ID)' },
      ],
      responseExample: buildDetailResponseJson(),
      statusCodes: [
        { code: 200, description: 'OK' },
        { code: 400, description: 'Bad Request' },
        { code: 404, description: 'Not Found' },
      ],
    },
    {
      method: 'POST',
      path: `${base}`,
      nameKey: 'form-manager.apiInfo.createData',
      descKey: 'form-manager.apiInfo.createDataDesc',
      group: 'dataOperations',
      requestContentType: 'application/json',
      requestBody: buildCreateRequestJson(),
      responseExample: `{
  "id": "abc123",
${buildMainFieldsJson(2)}
}`,
      statusCodes: [
        { code: 200, description: 'OK' },
        { code: 400, description: 'Bad Request / Validation Error' },
        { code: 403, description: 'Forbidden' },
      ],
    },
    {
      method: 'PUT',
      path: `${base}/{pk}`,
      nameKey: 'form-manager.apiInfo.updateData',
      descKey: 'form-manager.apiInfo.updateDataDesc',
      group: 'dataOperations',
      pathParams: [
        { name: 'pk', type: 'string', description: 'Record primary key (ID)' },
      ],
      requestContentType: 'application/json',
      requestBody: buildCreateRequestJson(),
      responseExample: `{
  "id": "abc123",
${buildMainFieldsJson(2)}
}`,
      statusCodes: [
        { code: 200, description: 'OK' },
        { code: 400, description: 'Bad Request' },
        { code: 404, description: 'Not Found' },
      ],
    },
    {
      method: 'DELETE',
      path: `${base}/{pk}`,
      nameKey: 'form-manager.apiInfo.deleteData',
      descKey: 'form-manager.apiInfo.deleteDataDesc',
      group: 'dataOperations',
      pathParams: [
        { name: 'pk', type: 'string', description: 'Record primary key (ID)' },
      ],
      responseExample: `{ "success": true }`,
      statusCodes: [
        { code: 200, description: 'OK' },
        { code: 404, description: 'Not Found' },
      ],
    },
    {
      method: 'DELETE',
      path: `${base}/batch/delete`,
      nameKey: 'form-manager.apiInfo.batchDelete',
      descKey: 'form-manager.apiInfo.batchDeleteDesc',
      group: 'dataOperations',
      queryParams: [
        {
          name: 'ids',
          type: 'string[]',
          required: true,
          description: 'List of IDs to delete',
        },
      ],
      responseExample: `{ "count": 3 }`,
      statusCodes: [
        { code: 200, description: 'OK' },
        { code: 403, description: 'Forbidden' },
      ],
    },
    {
      method: 'GET',
      path: `${base}/tree/children`,
      nameKey: 'form-manager.apiInfo.getTreeChildren',
      descKey: 'form-manager.apiInfo.getTreeChildrenDesc',
      group: 'auxiliary',
      queryParams: [
        {
          name: 'parentId',
          type: 'string',
          required: false,
          description: 'Parent node ID (empty for root)',
        },
        {
          name: 'parentField',
          type: 'string',
          required: false,
          description: 'Parent field name (default: parent_id)',
        },
      ],
      responseExample: `[
  {
    "id": "abc123",
    "has_children": true,
${buildMainFieldsJson(4)}
  }
]`,
      statusCodes: [{ code: 200, description: 'OK' }],
    },
    {
      method: 'GET',
      path: `${base}/field-values/{field_name}`,
      nameKey: 'form-manager.apiInfo.getFieldValues',
      descKey: 'form-manager.apiInfo.getFieldValuesDesc',
      group: 'auxiliary',
      pathParams: [
        {
          name: 'field_name',
          type: 'string',
          description: 'Field name to get values for',
        },
      ],
      queryParams: [
        {
          name: 'page',
          type: 'integer',
          required: false,
          description: 'Page number',
        },
        {
          name: 'pageSize',
          type: 'integer',
          required: false,
          description: 'Items per page',
        },
        {
          name: 'search',
          type: 'string',
          required: false,
          description: 'Search keyword',
        },
      ],
      responseExample: `{
  "items": [
    { "value": "val1", "label": "val1", "count": 5 }
  ],
  "total": 10,
  "hasMore": false
}`,
      statusCodes: [{ code: 200, description: 'OK' }],
    },
    {
      method: 'GET',
      path: `${base}/check-unique`,
      nameKey: 'form-manager.apiInfo.checkUnique',
      descKey: 'form-manager.apiInfo.checkUniqueDesc',
      group: 'auxiliary',
      queryParams: [
        {
          name: 'field',
          type: 'string',
          required: true,
          description: 'Field name',
        },
        {
          name: 'value',
          type: 'string',
          required: true,
          description: 'Field value to check',
        },
        {
          name: 'excludeId',
          type: 'string',
          required: false,
          description: 'Exclude record ID (for edit)',
        },
      ],
      responseExample: `{ "unique": true }`,
      statusCodes: [{ code: 200, description: 'OK' }],
    },
    {
      method: 'POST',
      path: `${base}/export/task`,
      nameKey: 'form-manager.apiInfo.exportExcel',
      descKey: 'form-manager.apiInfo.exportExcelDesc',
      group: 'importExport',
      requestContentType: 'application/json',
      requestBody: buildExportRequestJson(),
      responseExample: 'Binary (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)',
      responseType: 'file',
      statusCodes: [
        { code: 200, description: 'OK (Excel stream)' },
        { code: 403, description: 'Forbidden' },
      ],
    },
    {
      method: 'GET',
      path: `${base}/import/template`,
      nameKey: 'form-manager.apiInfo.importTemplate',
      descKey: 'form-manager.apiInfo.importTemplateDesc',
      group: 'importExport',
      responseExample: 'Binary (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)',
      responseType: 'file',
      statusCodes: [{ code: 200, description: 'OK (Excel stream)' }],
    },
    {
      method: 'POST',
      path: `${base}/import/excel`,
      nameKey: 'form-manager.apiInfo.importExcel',
      descKey: 'form-manager.apiInfo.importExcelDesc',
      group: 'importExport',
      requestContentType: 'multipart/form-data',
      requestBody: `file: File (.xlsx)       // required
mode: "append" | "overwrite"  // default: "append"
validate_only: boolean        // default: false`,
      responseExample: `{
  "success": 100,
  "fail": 2,
  "message": "...",
  "errors": [
    { "row": 3, "error": "field 'xxx' is required" }
  ]
}`,
      statusCodes: [
        { code: 200, description: 'OK' },
        { code: 400, description: 'Bad Request' },
      ],
    },
  ];
});

const selectedApi = computed(() => apiList.value[selectedApiIndex.value]);

const groupLabels: Record<string, string> = {
  permissions: 'form-manager.apiInfo.permissions',
  dataOperations: 'form-manager.apiInfo.dataOperations',
  auxiliary: 'form-manager.apiInfo.auxiliary',
  importExport: 'form-manager.apiInfo.importExport',
};

const groupOrder = ['permissions', 'dataOperations', 'auxiliary', 'importExport'];

interface GroupedApis {
  key: string;
  labelKey: string;
  apis: Array<{ api: ApiItem; globalIndex: number }>;
}

const groupedApis = computed<GroupedApis[]>(() => {
  const map = new Map<string, Array<{ api: ApiItem; globalIndex: number }>>();
  apiList.value.forEach((api, idx) => {
    if (!map.has(api.group)) map.set(api.group, []);
    map.get(api.group)!.push({ api, globalIndex: idx });
  });
  return groupOrder
    .filter((key) => map.has(key))
    .map((key) => ({
      key,
      labelKey: groupLabels[key] || key,
      apis: map.get(key)!,
    }));
});

function getMethodColor(
  method: string,
): '' | 'danger' | 'info' | 'success' | 'warning' {
  const map: Record<string, '' | 'danger' | 'info' | 'success' | 'warning'> = {
    DELETE: 'danger',
    GET: 'success',
    POST: 'warning',
    PUT: '',
  };
  return map[method] || 'info';
}

async function handleCopyPath(path: string) {
  try {
    await navigator.clipboard.writeText(path);
    ElMessage.success($t('form-manager.apiInfo.copiedSuccess'));
  } catch {
    const textarea = document.createElement('textarea');
    textarea.value = path;
    document.body.append(textarea);
    textarea.select();
    document.execCommand('copy');
    textarea.remove();
    ElMessage.success($t('form-manager.apiInfo.copiedSuccess'));
  }
}
</script>

<template>
  <ZqDialog
    v-model="visible"
    :title="$t('form-manager.apiInfo.title')"
    default-fullscreen
    :show-footer="false"
  >
    <div v-loading="loading" class="api-info-container flex h-full gap-0">
      <!-- Left: API list -->
      <div
        class="api-sidebar border-r flex w-64 flex-shrink-0 flex-col"
      >
        <!-- Header -->
        <div class="border-b p-3">
          <div class="text-foreground mb-1 text-sm font-semibold">
            {{ props.formName }}
          </div>
          <div class="text-muted-foreground flex items-center gap-1 font-mono text-xs">
            <Code class="h-3 w-3" />
            {{ props.formCode }}
          </div>
          <div class="text-muted-foreground mt-1 flex items-center gap-1 text-xs">
            <Lock class="h-3 w-3" />
            Bearer Token
          </div>
        </div>

        <!-- API list grouped -->
        <ElScrollbar class="flex-1">
          <div class="py-1">
            <template v-for="group in groupedApis" :key="group.key">
              <div
                class="text-muted-foreground px-3 pb-1 pt-3 text-xs font-semibold uppercase tracking-wider"
              >
                {{ $t(group.labelKey) }}
              </div>
              <div
                v-for="item in group.apis"
                :key="item.globalIndex"
                class="api-nav-item mx-2 mb-0.5 flex cursor-pointer items-center gap-2 rounded px-2 py-1.5"
                :class="{
                  'bg-primary/10 text-primary': selectedApiIndex === item.globalIndex,
                  'hover:bg-muted/50': selectedApiIndex !== item.globalIndex,
                }"
                @click="selectedApiIndex = item.globalIndex"
              >
                <ElTag
                  :type="getMethodColor(item.api.method)"
                  size="small"
                  class="method-tag font-mono text-[10px] font-bold"
                  effect="dark"
                >
                  {{ item.api.method }}
                </ElTag>
                <span class="flex-1 truncate text-xs">
                  {{ $t(item.api.nameKey) }}
                </span>
              </div>
            </template>
          </div>
        </ElScrollbar>
      </div>

      <!-- Right: API detail -->
      <div class="flex flex-1 flex-col overflow-hidden">
        <ElScrollbar v-if="selectedApi" class="flex-1">
          <div class="p-5">
            <!-- API title -->
            <div class="mb-1 flex items-center gap-3">
              <ElTag
                :type="getMethodColor(selectedApi.method)"
                size="default"
                class="font-mono font-bold"
                effect="dark"
              >
                {{ selectedApi.method }}
              </ElTag>
              <span class="text-lg font-semibold">
                {{ $t(selectedApi.nameKey) }}
              </span>
            </div>
            <p class="text-muted-foreground mb-4 text-sm">
              {{ $t(selectedApi.descKey) }}
            </p>

            <!-- URL -->
            <div
              class="bg-muted/40 mb-5 flex items-center gap-2 rounded-lg border px-4 py-2.5"
            >
              <ElTag
                :type="getMethodColor(selectedApi.method)"
                size="small"
                effect="dark"
                class="font-mono text-xs font-bold"
              >
                {{ selectedApi.method }}
              </ElTag>
              <code class="text-foreground flex-1 text-sm">
                {{ selectedApi.path }}
              </code>
              <ElTooltip
                :content="$t('form-manager.apiInfo.copyPath')"
                placement="top"
              >
                <ElButton
                  text
                  size="small"
                  @click="handleCopyPath(selectedApi.path)"
                >
                  <Copy class="h-4 w-4" />
                </ElButton>
              </ElTooltip>
            </div>

            <!-- Path Parameters -->
            <template
              v-if="selectedApi.pathParams && selectedApi.pathParams.length > 0"
            >
              <ElDivider content-position="left">
                <span class="text-sm font-semibold">
                  {{ $t('form-manager.apiInfo.pathParams') }}
                </span>
              </ElDivider>
              <ElTable
                :data="selectedApi.pathParams"
                border
                size="small"
                class="mb-4"
              >
                <ElTableColumn prop="name" label="Name" width="180">
                  <template #default="{ row }">
                    <code class="text-primary text-xs font-medium">
                      {{ row.name }}
                    </code>
                  </template>
                </ElTableColumn>
                <ElTableColumn prop="type" label="Type" width="120">
                  <template #default="{ row }">
                    <ElTag size="small" type="info">{{ row.type }}</ElTag>
                  </template>
                </ElTableColumn>
                <ElTableColumn label="Required" width="100">
                  <template #default>
                    <ElTag size="small" type="danger">required</ElTag>
                  </template>
                </ElTableColumn>
                <ElTableColumn
                  prop="description"
                  label="Description"
                />
              </ElTable>
            </template>

            <!-- Query Parameters -->
            <template
              v-if="
                selectedApi.queryParams && selectedApi.queryParams.length > 0
              "
            >
              <ElDivider content-position="left">
                <span class="text-sm font-semibold">
                  {{ $t('form-manager.apiInfo.queryParams') }}
                </span>
              </ElDivider>
              <ElTable
                :data="selectedApi.queryParams"
                border
                size="small"
                class="mb-4"
              >
                <ElTableColumn prop="name" label="Name" width="180">
                  <template #default="{ row }">
                    <code class="text-primary text-xs font-medium">
                      {{ row.name }}
                    </code>
                  </template>
                </ElTableColumn>
                <ElTableColumn prop="type" label="Type" width="120">
                  <template #default="{ row }">
                    <ElTag size="small" type="info">{{ row.type }}</ElTag>
                  </template>
                </ElTableColumn>
                <ElTableColumn label="Required" width="100">
                  <template #default="{ row }">
                    <ElTag
                      size="small"
                      :type="row.required ? 'danger' : 'info'"
                    >
                      {{ row.required ? 'required' : 'optional' }}
                    </ElTag>
                  </template>
                </ElTableColumn>
                <ElTableColumn
                  prop="description"
                  label="Description"
                />
              </ElTable>
            </template>

            <!-- Request Body -->
            <template v-if="selectedApi.requestBody">
              <ElDivider content-position="left">
                <span class="text-sm font-semibold">
                  {{ $t('form-manager.apiInfo.requestBody') }}
                </span>
                <ElTag
                  v-if="selectedApi.requestContentType"
                  size="small"
                  class="ml-2"
                  type="info"
                >
                  {{ selectedApi.requestContentType }}
                </ElTag>
              </ElDivider>
              <pre class="code-block mb-4">{{ selectedApi.requestBody }}</pre>
            </template>

            <!-- Response -->
            <ElDivider content-position="left">
              <span class="text-sm font-semibold">
                {{ $t('form-manager.apiInfo.response') }}
              </span>
              <ElTag
                v-if="selectedApi.responseType === 'file'"
                size="small"
                class="ml-2"
                type="warning"
              >
                File Stream
              </ElTag>
            </ElDivider>

            <!-- Status codes -->
            <div
              v-if="selectedApi.statusCodes"
              class="mb-3 flex flex-wrap gap-2"
            >
              <ElTag
                v-for="sc in selectedApi.statusCodes"
                :key="sc.code"
                size="small"
                :type="sc.code >= 400 ? 'danger' : 'success'"
              >
                {{ sc.code }} {{ sc.description }}
              </ElTag>
            </div>

            <pre class="code-block mb-4">{{ selectedApi.responseExample }}</pre>

            <!-- Form Fields Reference -->
            <template v-if="mainFields.length > 0">
              <ElDivider content-position="left">
                <span class="text-sm font-semibold">
                  {{ $t('form-manager.apiInfo.formFields') }}
                </span>
              </ElDivider>
              <ElTable
                :data="mainFields"
                border
                size="small"
                class="mb-4"
                max-height="300"
              >
                <ElTableColumn prop="field" label="Field" width="200">
                  <template #default="{ row }">
                    <code class="text-primary text-xs font-medium">
                      {{ row.field }}
                    </code>
                  </template>
                </ElTableColumn>
                <ElTableColumn prop="label" label="Label" width="200" />
                <ElTableColumn prop="type" label="Component" width="160">
                  <template #default="{ row }">
                    <ElTag size="small" type="info">{{ row.type }}</ElTag>
                  </template>
                </ElTableColumn>
                <ElTableColumn label="Required" width="100">
                  <template #default="{ row }">
                    <ElTag
                      v-if="row.required"
                      size="small"
                      type="danger"
                    >
                      required
                    </ElTag>
                    <span v-else class="text-muted-foreground text-xs">
                      optional
                    </span>
                  </template>
                </ElTableColumn>
              </ElTable>

              <!-- Sub-table fields -->
              <template
                v-for="(fields, tableName) in subTableFields"
                :key="tableName"
              >
                <div class="text-foreground mb-2 text-sm font-medium">
                  {{ $t('form-manager.dataSource.subTable') }}: {{ tableName }}
                </div>
                <ElTable
                  :data="fields"
                  border
                  size="small"
                  class="mb-4"
                  max-height="200"
                >
                  <ElTableColumn prop="field" label="Field" width="200">
                    <template #default="{ row }">
                      <code class="text-primary text-xs font-medium">
                        {{ row.field }}
                      </code>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn prop="label" label="Label" width="200" />
                  <ElTableColumn prop="type" label="Component" width="160">
                    <template #default="{ row }">
                      <ElTag size="small" type="info">{{ row.type }}</ElTag>
                    </template>
                  </ElTableColumn>
                </ElTable>
              </template>
            </template>
          </div>
        </ElScrollbar>
      </div>
    </div>
  </ZqDialog>
</template>

<style scoped>
.api-sidebar {
  min-width: 256px;
}

.method-tag {
  min-width: 52px;
  text-align: center;
}

.code-block {
  margin: 0;
  padding: 12px 16px;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-primary);
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  overflow-x: auto;
}
</style>
