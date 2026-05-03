import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { FieldType, type FieldConfig } from '#/types/zq-smart-table/field'
import { ViewType, SmartItemType, type Table, type Record as TableRecord, type ViewConfig, type SummaryAggregation } from '#/types/zq-smart-table/table'
import dayjs from 'dayjs'
import {
  getTableListApi, getTableFullApi, createTableApi, updateTableApi, deleteTableApi,
  moveTableApi,
  updateDocumentContentApi,
  createFieldApi, updateFieldApi, deleteFieldApi, reorderFieldsApi,
  createRecordApi, updateCellApi, deleteRecordApi, getRecordListApi,
  batchUpdateCellsApi, batchUpdateMultiRecordCellsApi,
  createViewApi, updateViewApi, deleteViewApi,
  getMyPermissionApi, getSummaryApi,
  type SmartFieldItem, type SmartViewItem, type SmartRecordItem,
  type MyPermission, type RecordFilterParam, type RecordSortParam,
} from '#/api/smart-table'
import {
  cacheTableData,
  getCachedTableData,
  addPendingOp,
  getPendingCount,
  syncAllPendingOps,
  clearOfflineCache,
} from '#/composables/use-offline-cache'

// ==================== Backend <-> Frontend conversion helpers ====================

const FIELD_CONFIG_KEYS = [
  'options', 'precision', 'numberFormat', 'dateFormat',
  'includeTime', 'maxRating', 'currencySymbol', 'formula', 'formulaResultType',
  'multiple', 'regionLevel', 'maxImageCount',
  'linkedTableId', 'symmetricFieldId', 'linkFieldId', 'lookupFieldId',
  'rollupFieldId', 'aggregation', 'validation',
] as const

function fieldFromApi(f: SmartFieldItem): FieldConfig {
  const base: FieldConfig = {
    id: f.id,
    name: f.name,
    type: f.type as FieldType,
    width: f.width,
    visible: f.visible,
    required: f.required,
    description: f.description ?? undefined,
  }
  if (f.config) {
    for (const key of FIELD_CONFIG_KEYS) {
      if (f.config[key] !== undefined) {
        ;(base as any)[key] = f.config[key]
      }
    }
  }
  return base
}

function fieldToApiConfig(field: FieldConfig): Record<string, any> {
  const config: Record<string, any> = {}
  for (const key of FIELD_CONFIG_KEYS) {
    if ((field as any)[key] !== undefined) {
      config[key] = (field as any)[key]
    }
  }
  return config
}

const VIEW_CONFIG_KEYS = [
  'filters', 'filterLogic', 'sorts', 'groups', 'visibleFieldIds',
  'conditionalFormats', 'kanbanFieldId', 'ganttStartFieldId', 'ganttEndFieldId',
  'rowHeight', 'zebra', 'frozenFieldId', 'summaryConfig',
] as const

function viewFromApi(v: SmartViewItem): ViewConfig {
  const base: ViewConfig = {
    id: v.id,
    name: v.name,
    type: (v.type as ViewType) || ViewType.Grid,
    filters: [],
    filterLogic: 'and',
    sorts: [],
    groups: [],
    visibleFieldIds: [],
  }
  if (v.config) {
    for (const key of VIEW_CONFIG_KEYS) {
      if (v.config[key] !== undefined) {
        ;(base as any)[key] = v.config[key]
      }
    }
  }
  return base
}

function viewToApiConfig(view: ViewConfig): Record<string, any> {
  const config: Record<string, any> = {}
  for (const key of VIEW_CONFIG_KEYS) {
    if ((view as any)[key] !== undefined) {
      config[key] = (view as any)[key]
    }
  }
  return config
}

function recordFromApi(r: SmartRecordItem): TableRecord {
  return {
    id: r.id,
    values: r.values || {},
    createdTime: r.sys_create_datetime || '',
    modifiedTime: r.sys_update_datetime || '',
    createdBy: r.sys_creator_id,
    modifiedBy: r.sys_modifier_id,
  }
}

// ==================== Store ====================

interface HistoryEntry {
  recordId: string
  fieldId: string
  oldValue: unknown
  newValue: unknown
}

export const useTableStore = defineStore('smart-table', () => {
  const tables = ref<Table[]>([])
  const activeTableId = ref<string>('')
  const searchText = ref('')
  const loading = ref(false)
  const creatingFromTemplate = ref(false)
  const wikiSpaceId = ref<string | null>(null)
  const loadingMore = ref(false)
  const undoStack = ref<HistoryEntry[]>([])
  const redoStack = ref<HistoryEntry[]>([])
  const maxHistory = 50

  // Pagination state per table: { tableId: { nextCursor, hasMore, total } }
  const paginationMap = ref<Record<string, { nextCursor: string | null; hasMore: boolean; total: number }>>({})

  // Batched cell write queue: accumulate writes per record, flush as single API call
  const cellWriteQueue = ref<Record<string, Record<string, unknown>>>({})
  let _cellFlushTimer: ReturnType<typeof setTimeout> | null = null
  const CELL_WRITE_DELAY = 300
  const CELL_BATCH_MAX = 20

  // ==================== Offline state ====================
  const isOnline = ref(navigator.onLine)
  const offlinePendingCount = ref(0)
  const offlineSyncing = ref(false)

  async function _handleOnline() {
    isOnline.value = true
    await syncOfflineOps()
  }

  function _handleOffline() {
    isOnline.value = false
  }

  function initOfflineListeners() {
    window.addEventListener('online', _handleOnline)
    window.addEventListener('offline', _handleOffline)
    getPendingCount().then((c) => { offlinePendingCount.value = c })
  }

  function destroyOfflineListeners() {
    window.removeEventListener('online', _handleOnline)
    window.removeEventListener('offline', _handleOffline)
  }

  async function syncOfflineOps() {
    if (offlineSyncing.value || !isOnline.value) return
    offlineSyncing.value = true
    try {
      const synced = await syncAllPendingOps()
      offlinePendingCount.value = await getPendingCount()
      if (synced > 0 && activeTableId.value) {
        await reloadRecords()
      }
    } finally {
      offlineSyncing.value = false
    }
  }

  async function _refreshOfflineCount() {
    offlinePendingCount.value = await getPendingCount()
  }

  // ==================== Permission state ====================
  const myPermission = ref<MyPermission | null>(null)

  const canManageTable = computed(() => myPermission.value?.capabilities?.manage_table ?? false)
  const canManagePermission = computed(() => myPermission.value?.capabilities?.manage_permission ?? false)
  const canManageField = computed(() => myPermission.value?.capabilities?.manage_field ?? false)
  const canManageView = computed(() => myPermission.value?.capabilities?.manage_view ?? false)
  const canAddRecord = computed(() => myPermission.value?.capabilities?.add_record ?? false)
  const canEditRecord = computed(() => myPermission.value?.capabilities?.edit_record ?? false)
  const canDeleteRecord = computed(() => myPermission.value?.capabilities?.delete_record ?? false)
  const canExport = computed(() => myPermission.value?.capabilities?.export_data ?? false)
  const canImport = computed(() => myPermission.value?.capabilities?.import_data ?? false)
  const isOwnerOrManager = computed(() => {
    const rt = myPermission.value?.role_type
    return rt === 'owner' || rt === 'manager' || rt === 'superadmin'
  })

  async function loadMyPermission(tableId: string) {
    try {
      const raw = await getMyPermissionApi(tableId)
      const data = (raw as any)?.data ?? raw
      myPermission.value = data
    } catch {
      myPermission.value = null
    }
  }

  // ==================== Summary state ====================
  const summaryData = ref<Record<string, any>>({})
  let _summaryTimer: ReturnType<typeof setTimeout> | null = null
  const SUMMARY_DEBOUNCE = 400

  // ==================== Group collapse state ====================
  const collapsedGroups = ref<Set<string>>(new Set())

  function toggleGroupCollapse(key: string) {
    const s = new Set(collapsedGroups.value)
    if (s.has(key)) s.delete(key)
    else s.add(key)
    collapsedGroups.value = s
  }

  function isGroupCollapsed(key: string): boolean {
    return collapsedGroups.value.has(key)
  }

  function collapseAllGroups() {
    const grouped = getGroupedRecords()
    collapsedGroups.value = new Set(grouped.map((g) => g.key))
  }

  function expandAllGroups() {
    collapsedGroups.value = new Set()
  }

  const activeTable = computed(() => tables.value.find((t) => t.id === activeTableId.value))
  const activeView = computed(() => {
    const t = activeTable.value
    if (!t) return undefined
    return t.views.find((v) => v.id === t.activeViewId)
  })

  async function loadSummary(tableId?: string) {
    const tid = tableId ?? activeTableId.value
    const v = activeView.value
    if (!tid || !v?.summaryConfig || Object.keys(v.summaryConfig).length === 0) {
      summaryData.value = {}
      return
    }
    const queryOpts = _viewToFilterParams(v)
    const searchKw = searchText.value.trim() || undefined
    try {
      const raw = await getSummaryApi(tid, {
        aggregations: v.summaryConfig as Record<string, string>,
        filters: queryOpts.filters,
        filter_logic: queryOpts.filter_logic,
        search: searchKw,
      })
      const data = (raw as any)?.data ?? raw
      summaryData.value = data.summaries || {}
    } catch (e) {
      console.error('[SmartTable] Failed to load summary', e)
      summaryData.value = {}
    }
  }

  function loadSummaryDebounced(tableId?: string) {
    if (_summaryTimer) clearTimeout(_summaryTimer)
    _summaryTimer = setTimeout(() => {
      loadSummary(tableId)
      _summaryTimer = null
    }, SUMMARY_DEBOUNCE)
  }

  function updateSummaryConfig(fieldId: string, agg: SummaryAggregation | null) {
    const v = activeView.value
    if (!v) return
    if (!v.summaryConfig) v.summaryConfig = {}
    if (agg) {
      v.summaryConfig[fieldId] = agg
    } else {
      delete v.summaryConfig[fieldId]
    }
    saveActiveViewConfig()
    loadSummaryDebounced()
  }

  // ==================== Query helpers ====================

  function _viewToFilterParams(v?: ViewConfig): { filters?: RecordFilterParam[]; sorts?: RecordSortParam[]; filter_logic?: string } {
    if (!v) return {}
    const params: { filters?: RecordFilterParam[]; sorts?: RecordSortParam[]; filter_logic?: string } = {}
    if (v.filters.length > 0) {
      params.filters = v.filters.map((f) => ({ field_id: f.fieldId, operator: f.operator, value: f.value }))
      params.filter_logic = v.filterLogic ?? 'and'
    }
    if (v.sorts.length > 0) {
      params.sorts = v.sorts.map((s) => ({ field_id: s.fieldId, direction: s.direction }))
    }
    return params
  }

  let _reloadTimer: ReturnType<typeof setTimeout> | null = null
  const RELOAD_DEBOUNCE = 300

  // ==================== Load from API ====================

  async function loadTableList(spaceId?: string | null) {
    if (spaceId !== undefined) {
      wikiSpaceId.value = spaceId ?? null
    }
    tables.value = []
    activeTableId.value = ''
    loading.value = true
    try {
      const list = await getTableListApi(wikiSpaceId.value)
      const items = Array.isArray(list) ? list : (list as any)?.data ?? []
      tables.value = items.map((t: any) => ({
        id: t.id,
        name: t.name,
        icon: t.icon || (t.type === 'document' ? 'FileText' : 'Grid'),
        type: (t.type as SmartItemType) || SmartItemType.Table,
        parentId: t.parent_id ?? null,
        fields: [],
        records: [],
        views: [],
        activeViewId: '',
      }))
      if (tables.value.length > 0) {
        activeTableId.value = tables.value[0]!.id
      }
    } catch (e) {
      console.error('[SmartTable] Failed to load table list', e)
    } finally {
      loading.value = false
    }
  }

  async function loadTableFull(tableId: string) {
    await flushDocumentSave()
    documentEdited.value = false
    loading.value = true
    try {
      const raw = await getTableFullApi(tableId)
      const data = (raw as any)?.data ?? raw
      const table = _buildTableFromApiData(tableId, data)

      if (table.type === SmartItemType.Document) {
        _upsertTable(tableId, table)
        activeTableId.value = tableId
        await loadMyPermission(tableId)
        cacheTableData(tableId, data).catch(() => {})
        return
      }

      paginationMap.value[tableId] = {
        nextCursor: data.next_cursor ?? null,
        hasMore: data.has_more ?? false,
        total: data.record_total ?? table.records.length,
      }

      _upsertTable(tableId, table)
      activeTableId.value = tableId
      computeFormulaFields(table)
      await loadMyPermission(tableId)
      loadSummaryDebounced(tableId)
      schedulePrefetch(tableId)

      cacheTableData(tableId, data).catch(() => {})
    } catch (e) {
      console.error('[SmartTable] Failed to load table', e)

      if (!isOnline.value) {
        const cached = await getCachedTableData(tableId)
        if (cached) {
          const table = _buildTableFromApiData(tableId, cached)
          paginationMap.value[tableId] = {
            nextCursor: cached.next_cursor ?? null,
            hasMore: cached.has_more ?? false,
            total: cached.record_total ?? table.records.length,
          }
          _upsertTable(tableId, table)
          activeTableId.value = tableId
          computeFormulaFields(table)
        }
      }
    } finally {
      loading.value = false
    }
  }

  function _buildTableFromApiData(tableId: string, data: any): Table {
    const itemType = (data.type as SmartItemType) || SmartItemType.Table
    const table: Table = {
      id: data.id ?? tableId,
      name: data.name,
      icon: data.icon || (itemType === SmartItemType.Document ? 'FileText' : 'Grid'),
      type: itemType,
      parentId: data.parent_id ?? null,
      content: data.content ?? undefined,
      cover: data.cover ?? null,
      emoji: data.emoji ?? null,
      fields: (data.fields || []).map(fieldFromApi),
      records: (data.records || []).map(recordFromApi),
      views: (data.views || []).map(viewFromApi),
      activeViewId: data.active_view_id || '',
      createdAt: data.sys_create_datetime ?? undefined,
      updatedAt: data.sys_update_datetime ?? undefined,
      creatorId: data.sys_creator_id ?? undefined,
      creatorName: data.creator_name ?? undefined,
      creatorAvatar: data.creator_avatar ?? undefined,
    }
    if (!table.activeViewId && table.views.length > 0) {
      table.activeViewId = table.views[0]!.id
    }
    return table
  }

  function _upsertTable(tableId: string, table: Table) {
    const idx = tables.value.findIndex((t) => t.id === tableId)
    if (idx !== -1) {
      tables.value[idx] = table
    } else {
      tables.value.push(table)
    }
  }

  async function reloadRecords(tableId?: string) {
    const tid = tableId ?? activeTableId.value
    if (!tid) return
    const t = tables.value.find((tb) => tb.id === tid)
    if (!t) return
    if (t.type === SmartItemType.Document) return

    const v = t.views.find((vv) => vv.id === t.activeViewId)
    const queryOpts = _viewToFilterParams(v)
    const searchKw = searchText.value.trim() || undefined

    loading.value = true
    try {
      const raw = await getRecordListApi(tid, null, 500, { ...queryOpts, search: searchKw })
      const data = (raw as any)?.data ?? raw
      t.records = (data.items || []).map(recordFromApi)
      paginationMap.value[tid] = {
        nextCursor: data.next_cursor ?? null,
        hasMore: data.has_more ?? false,
        total: data.total ?? t.records.length,
      }
      computeFormulaFields(t)
      loadSummaryDebounced(tid)
      // Clear prefetch cache for this table and schedule new prefetch
      for (const key of Object.keys(prefetchCache.value)) {
        if (key.startsWith(`${tid}:`)) delete prefetchCache.value[key]
      }
      schedulePrefetch(tid)
    } catch (e) {
      console.error('[SmartTable] Failed to reload records', e)
    } finally {
      loading.value = false
    }
  }

  function reloadRecordsDebounced(tableId?: string) {
    if (_reloadTimer) clearTimeout(_reloadTimer)
    _reloadTimer = setTimeout(() => {
      reloadRecords(tableId)
      _reloadTimer = null
    }, RELOAD_DEBOUNCE)
  }

  // Prefetch cache for next page
  const prefetchCache = ref<Record<string, { records: TableRecord[]; nextCursor: string | null; hasMore: boolean }>>({})
  let _prefetchTimer: ReturnType<typeof setTimeout> | null = null
  const PREFETCH_DELAY = 500

  async function loadMoreRecords(tableId?: string) {
    const tid = tableId ?? activeTableId.value
    if (!tid || loadingMore.value) return
    const pag = paginationMap.value[tid]
    if (!pag || !pag.hasMore || !pag.nextCursor) return

    const t = tables.value.find((tb) => tb.id === tid)
    if (!t) return

    loadingMore.value = true
    try {
      const cacheKey = `${tid}:${pag.nextCursor}`
      const cached = prefetchCache.value[cacheKey]

      if (cached) {
        t.records.push(...cached.records)
        paginationMap.value[tid] = {
          nextCursor: cached.nextCursor,
          hasMore: cached.hasMore,
          total: pag.total,
        }
        delete prefetchCache.value[cacheKey]
        computeFormulaFields(t)
      } else {
        const v = t.views.find((vv) => vv.id === t.activeViewId)
        const queryOpts = _viewToFilterParams(v)
        const searchKw = searchText.value.trim() || undefined

        const raw = await getRecordListApi(tid, pag.nextCursor, 200, { ...queryOpts, search: searchKw })
        const data = (raw as any)?.data ?? raw
        const newRecords = (data.items || []).map(recordFromApi)
        t.records.push(...newRecords)
        paginationMap.value[tid] = {
          nextCursor: data.next_cursor ?? null,
          hasMore: data.has_more ?? false,
          total: data.total !== undefined && data.total >= 0 ? data.total : pag.total,
        }
        computeFormulaFields(t)
      }

      schedulePrefetch(tid)
    } catch (e) {
      console.error('[SmartTable] Failed to load more records', e)
    } finally {
      loadingMore.value = false
    }
  }

  function schedulePrefetch(tableId?: string) {
    if (_prefetchTimer) clearTimeout(_prefetchTimer)
    _prefetchTimer = setTimeout(() => {
      prefetchNextPage(tableId)
      _prefetchTimer = null
    }, PREFETCH_DELAY)
  }

  async function prefetchNextPage(tableId?: string) {
    const tid = tableId ?? activeTableId.value
    if (!tid || loadingMore.value) return
    const pag = paginationMap.value[tid]
    if (!pag || !pag.hasMore || !pag.nextCursor) return

    const cacheKey = `${tid}:${pag.nextCursor}`
    if (prefetchCache.value[cacheKey]) return

    const t = tables.value.find((tb) => tb.id === tid)
    if (!t) return
    const v = t.views.find((vv) => vv.id === t.activeViewId)
    const queryOpts = _viewToFilterParams(v)
    const searchKw = searchText.value.trim() || undefined

    try {
      const raw = await getRecordListApi(tid, pag.nextCursor, 200, { ...queryOpts, search: searchKw })
      const data = (raw as any)?.data ?? raw
      const newRecords = (data.items || []).map(recordFromApi)
      prefetchCache.value[cacheKey] = {
        records: newRecords,
        nextCursor: data.next_cursor ?? null,
        hasMore: data.has_more ?? false,
      }
    } catch {
      // prefetch failure is silent
    }
  }

  // ==================== Table CRUD ====================

  async function addTable(name: string) {
    try {
      const payload: any = { name, icon: 'Grid', type: 'table' }
      if (wikiSpaceId.value) payload.wiki_space_id = wikiSpaceId.value
      const raw = await createTableApi(payload)
      const data = (raw as any)?.data ?? raw
      const table: Table = {
        id: data.id,
        name: data.name,
        icon: data.icon || 'Grid',
        type: SmartItemType.Table,
        fields: [],
        records: [],
        views: [],
        activeViewId: '',
      }
      tables.value.push(table)
      activeTableId.value = data.id
      return data.id
    } catch (e) {
      console.error('[SmartTable] Failed to create table', e)
    }
  }

  async function addTableFromTemplate(template: {
    name: string
    fields: Array<{
      name: string
      type: string
      width?: number
      options?: Array<{ label: string; color: string }>
      multiple?: boolean
      currencySymbol?: string
      dateFormat?: string
      includeTime?: boolean
      maxRating?: number
    }>
    viewType: string
    viewName?: string
    kanbanFieldName?: string
    sampleData?: Array<Record<string, any>>
  }) {
    creatingFromTemplate.value = true
    try {
      const tplPayload: any = { name: template.name, icon: 'Grid', type: 'table' }
      if (wikiSpaceId.value) tplPayload.wiki_space_id = wikiSpaceId.value
      const raw = await createTableApi(tplPayload)
      const data = (raw as any)?.data ?? raw
      const tableId = data.id
      const table: Table = {
        id: tableId,
        name: data.name,
        icon: data.icon || 'Grid',
        type: SmartItemType.Table,
        fields: [],
        records: [],
        views: [],
        activeViewId: '',
      }
      tables.value.push(table)
      activeTableId.value = tableId

      const fieldIdMap: Record<string, string> = {}
      const fieldOptionMap: Record<string, Array<{ id: string; label: string; color: string }>> = {}

      for (let i = 0; i < template.fields.length; i++) {
        const tf = template.fields[i]!
        const config: Record<string, any> = {}
        if (tf.options) {
          config.options = tf.options.map((o, idx) => ({
            id: `opt_${Date.now()}_${idx}`,
            label: o.label,
            color: o.color,
          }))
        }
        if (tf.multiple !== undefined) config.multiple = tf.multiple
        if (tf.currencySymbol) config.currencySymbol = tf.currencySymbol
        if (tf.dateFormat) config.dateFormat = tf.dateFormat
        if (tf.includeTime !== undefined) config.includeTime = tf.includeTime
        if (tf.maxRating !== undefined) config.maxRating = tf.maxRating

        const fieldPayload = {
          name: tf.name,
          type: tf.type,
          width: tf.width || 150,
          visible: true,
          required: false,
          config,
          sort: i,
        }
        const fieldRaw = await createFieldApi(tableId, fieldPayload)
        const fieldData = (fieldRaw as any)?.data ?? fieldRaw
        const field: FieldConfig = {
          id: fieldData.id,
          name: tf.name,
          type: tf.type as FieldType,
          width: tf.width || 150,
          visible: true,
          required: false,
          ...config,
        }
        if (config.options) {
          field.options = config.options
          fieldOptionMap[tf.name] = config.options
        }
        table.fields.push(field)
        fieldIdMap[tf.name] = fieldData.id
      }

      const viewConfig: Record<string, any> = {
        visibleFieldIds: table.fields.map((f) => f.id),
        filters: [],
        filterLogic: 'and',
        sorts: [],
        groups: [],
      }

      if (template.kanbanFieldName && fieldIdMap[template.kanbanFieldName]) {
        viewConfig.kanbanFieldId = fieldIdMap[template.kanbanFieldName]
      }

      const viewPayload = {
        name: template.viewName || '默认视图',
        type: template.viewType,
        config: viewConfig,
      }
      const viewRaw = await createViewApi(tableId, viewPayload)
      const viewData = (viewRaw as any)?.data ?? viewRaw
      const view: ViewConfig = {
        id: viewData.id,
        name: viewPayload.name,
        type: template.viewType as ViewType,
        filters: [],
        filterLogic: 'and',
        sorts: [],
        groups: [],
        visibleFieldIds: table.fields.map((f) => f.id),
      }
      if (viewConfig.kanbanFieldId) view.kanbanFieldId = viewConfig.kanbanFieldId
      table.views.push(view)
      table.activeViewId = view.id
      await updateTableApi(tableId, { active_view_id: view.id })

      if (template.sampleData?.length) {
        const fieldTypeMap: Record<string, string> = {}
        for (const tf of template.fields) {
          fieldTypeMap[tf.name] = tf.type
        }

        for (const row of template.sampleData) {
          const values: Record<string, any> = {}
          for (const [fieldName, rawVal] of Object.entries(row)) {
            const fieldId = fieldIdMap[fieldName]
            if (!fieldId) continue
            const fType = fieldTypeMap[fieldName]
            if (fType === FieldType.SingleSelect) {
              const opts = fieldOptionMap[fieldName]
              const matched = opts?.find((o) => o.label === rawVal)
              values[fieldId] = matched ? matched.id : rawVal
            } else {
              values[fieldId] = rawVal
            }
          }
          try {
            const recRaw = await createRecordApi(tableId, values)
            const recData = (recRaw as any)?.data ?? recRaw
            const now = dayjs().format('YYYY-MM-DD HH:mm:ss')
            const record: TableRecord = {
              id: recData.id,
              values,
              createdTime: recData.sys_create_datetime || now,
              modifiedTime: recData.sys_update_datetime || now,
            }
            table.records.push(record)
          } catch (recErr) {
            console.error('[SmartTable] Failed to create sample record', recErr)
          }
        }
      }

      return tableId
    } catch (e) {
      console.error('[SmartTable] Failed to create table from template', e)
    } finally {
      creatingFromTemplate.value = false
    }
  }

  async function renameTable(tableId: string, name: string) {
    const t = tables.value.find((tb) => tb.id === tableId)
    if (t) t.name = name
    try {
      await updateTableApi(tableId, { name })
    } catch (e) {
      console.error('[SmartTable] Failed to rename table', e)
    }
  }

  async function updateTableCover(tableId: string, cover: string | null) {
    const t = tables.value.find((tb) => tb.id === tableId)
    if (t) t.cover = cover
    try {
      await updateTableApi(tableId, { cover })
    } catch (e) {
      console.error('[SmartTable] Failed to update cover', e)
    }
  }

  async function updateTableEmoji(tableId: string, emoji: string | null) {
    const t = tables.value.find((tb) => tb.id === tableId)
    if (t) t.emoji = emoji
    try {
      await updateTableApi(tableId, { emoji })
    } catch (e) {
      console.error('[SmartTable] Failed to update emoji', e)
    }
  }

  async function deleteTable(tableId: string) {
    try {
      await deleteTableApi(tableId)
    } catch (e) {
      console.error('[SmartTable] Failed to delete table', e)
    }
    const idsToRemove = _collectDescendantIds(tableId)
    idsToRemove.add(tableId)
    tables.value = tables.value.filter((t) => !idsToRemove.has(t.id))
    if (idsToRemove.has(activeTableId.value)) {
      activeTableId.value = tables.value[0]?.id || ''
    }
  }

  function _collectDescendantIds(parentId: string): Set<string> {
    const result = new Set<string>()
    const children = tables.value.filter((t) => t.parentId === parentId)
    for (const child of children) {
      result.add(child.id)
      for (const id of _collectDescendantIds(child.id)) {
        result.add(id)
      }
    }
    return result
  }

  // ==================== Document ====================

  const documentSaving = ref(false)
  const documentEdited = ref(false)
  let _docSaveTimer: ReturnType<typeof setTimeout> | null = null
  let _docPendingSave: { tableId: string; content: any } | null = null
  const DOC_SAVE_DEBOUNCE = 1000

  async function addDocument(name: string, parentId?: string | null) {
    try {
      const docPayload: any = { name, icon: 'FileText', type: 'document', parent_id: parentId ?? null }
      if (wikiSpaceId.value) docPayload.wiki_space_id = wikiSpaceId.value
      const raw = await createTableApi(docPayload)
      const data = (raw as any)?.data ?? raw
      const table: Table = {
        id: data.id,
        name: data.name,
        icon: data.icon || 'FileText',
        type: SmartItemType.Document,
        parentId: parentId ?? null,
        content: undefined,
        fields: [],
        records: [],
        views: [],
        activeViewId: '',
      }
      tables.value.push(table)
      activeTableId.value = data.id
      documentEdited.value = false
      return data.id
    } catch (e) {
      console.error('[SmartTable] Failed to create document', e)
    }
  }

  async function addDocumentFromTemplate(name: string, templateContent: Record<string, any>, parentId?: string | null) {
    const docId = await addDocument(name, parentId)
    if (docId && templateContent) {
      try {
        await updateDocumentContentApi(docId, templateContent)
        const t = tables.value.find(x => x.id === docId)
        if (t) t.content = templateContent
      } catch (e) {
        console.error('[SmartTable] Failed to set template content', e)
      }
    }
    return docId
  }

  async function addSubPage(parentId: string, name: string) {
    return addDocument(name, parentId)
  }

  async function moveTable(tableId: string, newParentId: string | null, afterId?: string | null) {
    const item = tables.value.find((t) => t.id === tableId)
    if (!item) return
    if (newParentId === tableId) return
    if (newParentId && _isDescendant(tableId, newParentId)) return

    const snapshot = [...tables.value]
    item.parentId = newParentId

    // Reorder locally: remove, then insert at correct position
    const idx = tables.value.indexOf(item)
    if (idx !== -1) tables.value.splice(idx, 1)

    if (afterId) {
      const afterIdx = tables.value.findIndex((t) => t.id === afterId)
      if (afterIdx !== -1) {
        tables.value.splice(afterIdx + 1, 0, item)
      } else {
        tables.value.push(item)
      }
    } else {
      // Insert before the first sibling at this parent level
      const firstSiblingIdx = tables.value.findIndex(
        (t) => (t.parentId ?? null) === (newParentId ?? null),
      )
      if (firstSiblingIdx !== -1) {
        tables.value.splice(firstSiblingIdx, 0, item)
      } else {
        tables.value.push(item)
      }
    }

    try {
      await moveTableApi(tableId, newParentId, afterId)
    } catch (e) {
      tables.value = snapshot
      console.error('[SmartTable] Failed to move table', e)
    }
  }

  function _isDescendant(ancestorId: string, nodeId: string): boolean {
    let current = tables.value.find((t) => t.id === nodeId)
    while (current?.parentId) {
      if (current.parentId === ancestorId) return true
      current = tables.value.find((t) => t.id === current!.parentId)
    }
    return false
  }

  function updateDocumentContent(content: any) {
    const t = activeTable.value
    if (!t || t.type !== SmartItemType.Document) return
    t.content = content
    documentEdited.value = true

    if (_docSaveTimer) clearTimeout(_docSaveTimer)
    _docPendingSave = { tableId: t.id, content }
    documentSaving.value = true
    _docSaveTimer = setTimeout(() => {
      _executeDocumentSave()
    }, DOC_SAVE_DEBOUNCE)
  }

  async function _executeDocumentSave() {
    const pending = _docPendingSave
    if (!pending) {
      documentSaving.value = false
      return
    }
    _docPendingSave = null
    _docSaveTimer = null
    try {
      await updateDocumentContentApi(pending.tableId, pending.content)
    } catch (e) {
      console.error('[SmartTable] Failed to save document content', e)
    } finally {
      if (!_docPendingSave) {
        documentSaving.value = false
      }
    }
  }

  async function flushDocumentSave() {
    if (_docSaveTimer) {
      clearTimeout(_docSaveTimer)
      _docSaveTimer = null
    }
    if (_docPendingSave) {
      await _executeDocumentSave()
    }
  }

  // ==================== Record CRUD ====================

  const currentUser = ref('当前用户')

  function getNextAutoNumber(table: Table, fieldId: string): number {
    let max = 0
    for (const r of table.records) {
      const v = Number(r.values[fieldId])
      if (!isNaN(v) && v > max) max = v
    }
    return max + 1
  }

  function fillSystemFields(table: Table, record: TableRecord) {
    for (const field of table.fields) {
      if (field.type === FieldType.AutoNumber) {
        record.values[field.id] = getNextAutoNumber(table, field.id)
      }
    }
    record.createdBy = currentUser.value
    record.modifiedBy = currentUser.value
  }

  // Formula values are now computed by the backend and returned in record.values.
  // This function is kept as a no-op for backward compatibility with existing call sites.
  function computeFormulaFields(_table: Table) {
    // no-op: backend handles formula computation
  }

  async function addRecord(tableId?: string) {
    const t = tableId ? tables.value.find((tb) => tb.id === tableId) : activeTable.value
    if (!t) return
    const now = dayjs().format('YYYY-MM-DD HH:mm:ss')
    const record: TableRecord = { id: '', values: {}, createdTime: now, modifiedTime: now }
    fillSystemFields(t, record)

    if (!isOnline.value) {
      record.id = `offline_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
      t.records.push(record)
      computeFormulaFields(t)
      addPendingOp({
        type: 'createRecord',
        tableId: t.id,
        recordId: record.id,
        payload: { values: record.values },
      }).then(() => _refreshOfflineCount())
      return record
    }

    try {
      const raw = await createRecordApi(t.id, record.values)
      const data = (raw as any)?.data ?? raw
      record.id = data.id
      record.createdTime = data.sys_create_datetime || now
      t.records.push(record)
      computeFormulaFields(t)
      return record
    } catch (e) {
      console.error('[SmartTable] Failed to create record', e)
    }
  }

  function insertRecord(anchorRecordId: string, position: 'above' | 'below') {
    const t = activeTable.value
    if (!t) return
    const idx = t.records.findIndex((r) => r.id === anchorRecordId)
    if (idx === -1) return
    const now = dayjs().format('YYYY-MM-DD HH:mm:ss')
    const record: TableRecord = { id: '', values: {}, createdTime: now, modifiedTime: now }
    fillSystemFields(t, record)
    const insertIdx = position === 'above' ? idx : idx + 1

    createRecordApi(t.id, record.values).then((raw) => {
      const data = (raw as any)?.data ?? raw
      record.id = data.id
    }).catch((e) => console.error('[SmartTable] Failed to create record', e))

    record.id = `temp_${Date.now()}`
    t.records.splice(insertIdx, 0, record)
    computeFormulaFields(t)
    return record
  }

  function duplicateRecord(recordId: string) {
    const t = activeTable.value
    if (!t) return
    const src = t.records.find((r) => r.id === recordId)
    if (!src) return
    const idx = t.records.indexOf(src)
    const now = dayjs().format('YYYY-MM-DD HH:mm:ss')
    const values = JSON.parse(JSON.stringify(src.values))
    const record: TableRecord = { id: '', values, createdTime: now, modifiedTime: now }
    fillSystemFields(t, record)

    createRecordApi(t.id, values).then((raw) => {
      const data = (raw as any)?.data ?? raw
      record.id = data.id
    }).catch((e) => console.error('[SmartTable] Failed to duplicate record', e))

    record.id = `temp_${Date.now()}`
    t.records.splice(idx + 1, 0, record)
    computeFormulaFields(t)
    return record
  }

  function flushCellWriteQueue() {
    const queue = { ...cellWriteQueue.value }
    cellWriteQueue.value = {}
    _cellFlushTimer = null

    const recordIds = Object.keys(queue)
    if (recordIds.length === 0) return

    const tid = activeTableId.value
    if (!tid) return

    if (!isOnline.value) {
      for (const recordId of recordIds) {
        const cells = queue[recordId]!
        for (const [fieldId, value] of Object.entries(cells)) {
          addPendingOp({
            type: 'updateCell',
            tableId: tid,
            recordId,
            payload: { fieldId, value },
          }).catch(() => {})
        }
      }
      _refreshOfflineCount()
      return
    }

    if (recordIds.length === 1) {
      const recordId = recordIds[0]!
      const cells = queue[recordId]!
      const fieldIds = Object.keys(cells)
      if (fieldIds.length === 1) {
        updateCellApi(recordId, fieldIds[0]!, cells[fieldIds[0]!]).catch((e) =>
          console.error('[SmartTable] Failed to update cell', e),
        )
      } else {
        batchUpdateCellsApi(recordId, cells).catch((e) =>
          console.error('[SmartTable] Failed to batch update cells', e),
        )
      }
      return
    }

    const updates = recordIds.map((rid) => ({
      record_id: rid,
      cells: queue[rid]!,
    }))
    batchUpdateMultiRecordCellsApi(tid, updates).catch((e) =>
      console.error('[SmartTable] Failed to batch update multi records', e),
    )
  }

  function debouncedCellWrite(recordId: string, fieldId: string, value: unknown) {
    if (!cellWriteQueue.value[recordId]) {
      cellWriteQueue.value[recordId] = {}
    }
    cellWriteQueue.value[recordId]![fieldId] = value

    const totalFields = Object.values(cellWriteQueue.value).reduce(
      (sum, cells) => sum + Object.keys(cells).length, 0,
    )
    if (totalFields >= CELL_BATCH_MAX) {
      if (_cellFlushTimer) clearTimeout(_cellFlushTimer)
      flushCellWriteQueue()
      return
    }

    if (_cellFlushTimer) clearTimeout(_cellFlushTimer)
    _cellFlushTimer = setTimeout(flushCellWriteQueue, CELL_WRITE_DELAY)
  }

  function updateCellValue(recordId: string, fieldId: string, value: unknown) {
    const t = activeTable.value
    if (!t) return
    const record = t.records.find((r) => r.id === recordId)
    if (!record) return
    const oldValue = (record.values as any)[fieldId]
    ;(record.values as any)[fieldId] = value
    record.modifiedTime = dayjs().format('YYYY-MM-DD HH:mm:ss')
    record.modifiedBy = currentUser.value
    undoStack.value.push({ recordId, fieldId, oldValue, newValue: value })
    if (undoStack.value.length > maxHistory) undoStack.value.shift()
    redoStack.value = []
    computeFormulaFields(t)

    debouncedCellWrite(recordId, fieldId, value)
  }

  function undo() {
    const entry = undoStack.value.pop()
    if (!entry) return
    const t = activeTable.value
    if (!t) return
    const record = t.records.find((r) => r.id === entry.recordId)
    if (!record) return
    ;(record.values as any)[entry.fieldId] = entry.oldValue
    record.modifiedTime = dayjs().format('YYYY-MM-DD HH:mm:ss')
    redoStack.value.push(entry)
    debouncedCellWrite(entry.recordId, entry.fieldId, entry.oldValue)
  }

  function redo() {
    const entry = redoStack.value.pop()
    if (!entry) return
    const t = activeTable.value
    if (!t) return
    const record = t.records.find((r) => r.id === entry.recordId)
    if (!record) return
    ;(record.values as any)[entry.fieldId] = entry.newValue
    record.modifiedTime = dayjs().format('YYYY-MM-DD HH:mm:ss')
    undoStack.value.push(entry)
    debouncedCellWrite(entry.recordId, entry.fieldId, entry.newValue)
  }

  async function deleteRecord(recordId: string) {
    const t = activeTable.value
    if (!t) return
    const idx = t.records.findIndex((r) => r.id === recordId)
    if (idx !== -1) t.records.splice(idx, 1)

    if (!isOnline.value) {
      if (!recordId.startsWith('offline_')) {
        addPendingOp({
          type: 'deleteRecord',
          tableId: t.id,
          recordId,
          payload: {},
        }).then(() => _refreshOfflineCount())
      }
      return
    }

    try {
      await deleteRecordApi(recordId)
    } catch (e) {
      console.error('[SmartTable] Failed to delete record', e)
    }
  }

  // ==================== Field CRUD ====================

  async function addField(field: FieldConfig) {
    const t = activeTable.value
    if (!t) return
    try {
      const raw = await createFieldApi(t.id, {
        name: field.name,
        type: field.type,
        width: field.width,
        visible: field.visible,
        required: field.required,
        description: field.description,
        config: fieldToApiConfig(field),
        sort: t.fields.length,
      })
      const data = (raw as any)?.data ?? raw
      field.id = data.id
      t.fields.push(field)
      t.views.forEach((v) => v.visibleFieldIds.push(field.id))

      for (const v of t.views) {
        const cfg = viewToApiConfig(v)
        updateViewApi(v.id, { config: cfg }).catch(() => {})
      }
    } catch (e) {
      console.error('[SmartTable] Failed to add field', e)
    }
  }

  function insertField(field: FieldConfig, anchorFieldId: string, position: 'left' | 'right') {
    const t = activeTable.value
    if (!t) return
    const idx = t.fields.findIndex((f) => f.id === anchorFieldId)
    if (idx === -1) return
    const insertIdx = position === 'left' ? idx : idx + 1

    createFieldApi(t.id, {
      name: field.name, type: field.type, width: field.width,
      visible: field.visible, required: field.required,
      description: field.description,
      config: fieldToApiConfig(field), sort: insertIdx,
    }).then((raw) => {
      const data = (raw as any)?.data ?? raw
      field.id = data.id
      reorderFieldsApi(t.id, t.fields.map((f) => f.id)).catch(() => {})
    }).catch((e) => console.error('[SmartTable] Failed to insert field', e))

    field.id = field.id || `temp_${Date.now()}`
    t.fields.splice(insertIdx, 0, field)
    t.views.forEach((v) => {
      const vi = v.visibleFieldIds.indexOf(anchorFieldId)
      if (vi !== -1) {
        v.visibleFieldIds.splice(position === 'left' ? vi : vi + 1, 0, field.id)
      } else {
        v.visibleFieldIds.push(field.id)
      }
    })
  }

  function duplicateField(fieldId: string) {
    const t = activeTable.value
    if (!t) return
    const srcField = t.fields.find((f) => f.id === fieldId)
    if (!srcField) return
    const newField: FieldConfig = {
      ...JSON.parse(JSON.stringify(srcField)),
      id: `temp_${Date.now()}`,
      name: srcField.name + ' (copy)',
    }
    insertField(newField, fieldId, 'right')
    t.records.forEach((r) => {
      if (r.values[fieldId] !== undefined) {
        r.values[newField.id] = JSON.parse(JSON.stringify(r.values[fieldId]))
      }
    })
  }

  async function renameField(fieldId: string, name: string) {
    const t = activeTable.value
    if (!t) return
    const field = t.fields.find((f) => f.id === fieldId)
    if (field) {
      field.name = name
      try {
        await updateFieldApi(fieldId, { name })
      } catch (e) {
        console.error('[SmartTable] Failed to rename field', e)
      }
    }
  }

  async function updateFieldFull(fieldId: string, updates: Partial<FieldConfig>) {
    const t = activeTable.value
    if (!t) return
    const field = t.fields.find((f) => f.id === fieldId)
    if (!field) return
    Object.assign(field, updates)
    try {
      const apiData: Partial<SmartFieldItem> = {}
      if (updates.name !== undefined) apiData.name = updates.name
      if (updates.type !== undefined) apiData.type = updates.type
      if (updates.description !== undefined) apiData.description = updates.description ?? null
      if (updates.required !== undefined) apiData.required = updates.required
      if (updates.width !== undefined) apiData.width = updates.width
      if (updates.visible !== undefined) apiData.visible = updates.visible
      apiData.config = fieldToApiConfig(field)
      await updateFieldApi(fieldId, apiData)
    } catch (e) {
      console.error('[SmartTable] Failed to update field', e)
    }
  }

  async function deleteField(fieldId: string) {
    const t = activeTable.value
    if (!t) return
    const idx = t.fields.findIndex((f) => f.id === fieldId)
    if (idx !== -1) t.fields.splice(idx, 1)
    t.views.forEach((v) => {
      const vi = v.visibleFieldIds.indexOf(fieldId)
      if (vi !== -1) v.visibleFieldIds.splice(vi, 1)
    })
    t.records.forEach((r) => delete r.values[fieldId])
    try {
      await deleteFieldApi(fieldId)
    } catch (e) {
      console.error('[SmartTable] Failed to delete field', e)
    }
  }

  // ==================== View CRUD ====================

  async function addView(view: ViewConfig) {
    const t = activeTable.value
    if (!t) return
    try {
      const raw = await createViewApi(t.id, {
        name: view.name,
        type: view.type,
        config: viewToApiConfig(view),
      })
      const data = (raw as any)?.data ?? raw
      view.id = data.id
      t.views.push(view)
      t.activeViewId = view.id
      await updateTableApi(t.id, { active_view_id: view.id })
    } catch (e) {
      console.error('[SmartTable] Failed to add view', e)
    }
  }

  async function setActiveView(viewId: string) {
    const t = activeTable.value
    if (!t) return
    const changed = t.activeViewId !== viewId
    t.activeViewId = viewId
    try {
      await updateTableApi(t.id, { active_view_id: viewId })
    } catch (e) {
      console.error('[SmartTable] Failed to set active view', e)
    }
    if (changed) {
      reloadRecords()
    }
  }

  async function deleteView(viewId: string) {
    const t = activeTable.value
    if (!t || t.views.length <= 1) return
    const idx = t.views.findIndex((v) => v.id === viewId)
    if (idx === -1) return
    t.views.splice(idx, 1)
    if (t.activeViewId === viewId) {
      t.activeViewId = t.views[0]!.id
    }
    try {
      await deleteViewApi(viewId)
      await updateTableApi(t.id, { active_view_id: t.activeViewId })
    } catch (e) {
      console.error('[SmartTable] Failed to delete view', e)
    }
  }

  async function duplicateView(viewId: string) {
    const t = activeTable.value
    if (!t) return
    const src = t.views.find((v) => v.id === viewId)
    if (!src) return
    const newView: ViewConfig = {
      ...JSON.parse(JSON.stringify(src)),
      id: '',
      name: src.name + ' (copy)',
    }
    await addView(newView)
  }

  async function renameView(viewId: string, name: string) {
    const t = activeTable.value
    if (!t) return
    const v = t.views.find((vv) => vv.id === viewId)
    if (v) {
      v.name = name
      try {
        await updateViewApi(viewId, { name })
      } catch (e) {
        console.error('[SmartTable] Failed to rename view', e)
      }
    }
  }

  let _saveViewTimer: ReturnType<typeof setTimeout> | null = null
  const SAVE_VIEW_DEBOUNCE = 500

  function saveActiveViewConfig() {
    const v = activeView.value
    if (!v) return
    if (_saveViewTimer) clearTimeout(_saveViewTimer)
    _saveViewTimer = setTimeout(() => {
      updateViewApi(v.id, { config: viewToApiConfig(v) }).catch((e) =>
        console.error('[SmartTable] Failed to save view config', e),
      )
      _saveViewTimer = null
    }, SAVE_VIEW_DEBOUNCE)
  }

  function saveActiveViewConfigAndReload() {
    saveActiveViewConfig()
    reloadRecordsDebounced()
  }

  // ==================== Query (records are already server-filtered) ====================

  function getFilteredRecords(): TableRecord[] {
    const t = activeTable.value
    if (!t) return []
    return [...t.records]
  }

  function computeLocalAggregation(
    records: TableRecord[],
    fieldId: string,
    agg: SummaryAggregation,
  ): number | string | null {
    const vals: number[] = []
    let nonEmpty = 0
    let empty = 0
    for (const r of records) {
      const raw = r.values[fieldId]
      if (raw === null || raw === undefined || raw === '') {
        empty++
      } else {
        nonEmpty++
        const n = Number(raw)
        if (!Number.isNaN(n)) vals.push(n)
      }
    }
    const total = records.length
    switch (agg) {
      case 'COUNT': return total
      case 'COUNTA': return nonEmpty
      case 'COUNT_EMPTY': return empty
      case 'PERCENT_EMPTY': return total ? Math.round((empty / total) * 100) : 0
      case 'PERCENT_FILLED': return total ? Math.round((nonEmpty / total) * 100) : 0
      case 'SUM': return vals.length ? vals.reduce((a, b) => a + b, 0) : null
      case 'AVG': return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null
      case 'MIN': return vals.length ? Math.min(...vals) : null
      case 'MAX': return vals.length ? Math.max(...vals) : null
      default: return null
    }
  }

  function getGroupedRecords(): { key: string; label: string; records: TableRecord[]; subtotals: Record<string, any> }[] {
    const t = activeTable.value
    const v = activeView.value
    if (!t || !v || v.groups.length === 0) return []
    const records = getFilteredRecords()
    const groupField = v.groups[0]!
    const field = t.fields.find((f) => f.id === groupField.fieldId)
    if (!field) return []

    const groups = new Map<string, TableRecord[]>()
    for (const record of records) {
      const val = String(record.values[groupField.fieldId] ?? '')
      if (!groups.has(val)) groups.set(val, [])
      groups.get(val)!.push(record)
    }

    const summaryConfig = v.summaryConfig || {}

    return Array.from(groups.entries()).map(([key, recs]) => {
      let label = key || ''
      if (field.options) {
        const opt = field.options.find((o) => o.id === key)
        if (opt) label = opt.label
      }

      const subtotals: Record<string, any> = {}
      for (const [fid, agg] of Object.entries(summaryConfig)) {
        subtotals[fid] = computeLocalAggregation(recs, fid, agg as SummaryAggregation)
      }

      return { key, label, records: recs, subtotals }
    })
  }

  // ==================== State reset ====================

  function clearStorage() {
    if (_docSaveTimer) {
      clearTimeout(_docSaveTimer)
      _docSaveTimer = null
    }
    _docPendingSave = null
    documentSaving.value = false
    documentEdited.value = false

    tables.value = []
    activeTableId.value = ''
    searchText.value = ''
    loading.value = false
    loadingMore.value = false
    undoStack.value = []
    redoStack.value = []
    paginationMap.value = {}
    cellWriteQueue.value = {}
    prefetchCache.value = {}
    myPermission.value = null
    summaryData.value = {}
    offlinePendingCount.value = 0
    clearOfflineCache().catch(() => {})
  }

  const activePagination = computed(() => paginationMap.value[activeTableId.value])

  /**
   * 前端单元格校验。返回 { rule, params } 错误对象或 null（通过）。
   * 组件层通过 t() 将 rule 翻译为用户可读的消息。
   */
  function validateCell(field: FieldConfig, value: unknown): { rule: string; params: Record<string, any>; message?: string } | null {
    const v = field.validation
    if (!v) {
      if (field.required && (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0))) {
        return { rule: 'required', params: { name: field.name } }
      }
      return null
    }

    if (field.required && (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0))) {
      return { rule: 'required', params: { name: field.name }, message: v.message }
    }
    if (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) {
      return null
    }

    if (v.min != null) {
      const num = Number(value)
      if (!isNaN(num) && num < v.min) return { rule: 'min', params: { name: field.name, min: v.min }, message: v.message }
    }
    if (v.max != null) {
      const num = Number(value)
      if (!isNaN(num) && num > v.max) return { rule: 'max', params: { name: field.name, max: v.max }, message: v.message }
    }
    if (v.minLength != null) {
      if (String(value).length < v.minLength) return { rule: 'minLength', params: { name: field.name, min: v.minLength }, message: v.message }
    }
    if (v.maxLength != null) {
      if (String(value).length > v.maxLength) return { rule: 'maxLength', params: { name: field.name, max: v.maxLength }, message: v.message }
    }
    if (v.pattern) {
      try {
        if (!new RegExp(v.pattern).test(String(value))) return { rule: 'pattern', params: { name: field.name }, message: v.message }
      } catch { /* invalid regex, skip */ }
    }
    return null
  }

  const tableTree = computed(() => {
    const map = new Map<string, Table & { children: Table[] }>()
    const roots: Array<Table & { children: Table[] }> = []
    for (const t of tables.value) {
      map.set(t.id, { ...t, children: [] })
    }
    for (const t of tables.value) {
      const node = map.get(t.id)!
      if (t.parentId && map.has(t.parentId)) {
        map.get(t.parentId)!.children.push(node)
      } else {
        roots.push(node)
      }
    }
    return roots
  })

  return {
    tables,
    tableTree,
    activeTableId,
    wikiSpaceId,
    searchText,
    loading,
    creatingFromTemplate,
    loadingMore,
    currentUser,
    activeTable,
    activeView,
    activePagination,
    paginationMap,
    loadTableList,
    loadTableFull,
    loadMoreRecords,
    prefetchNextPage,
    reloadRecords,
    reloadRecordsDebounced,
    flushCellWriteQueue,
    addTable,
    addTableFromTemplate,
    addDocument,
    addDocumentFromTemplate,
    addSubPage,
    moveTable,
    updateDocumentContent,
    flushDocumentSave,
    documentSaving,
    documentEdited,
    renameTable,
    updateTableCover,
    updateTableEmoji,
    deleteTable,
    addRecord,
    insertRecord,
    duplicateRecord,
    updateCellValue,
    deleteRecord,
    addField,
    insertField,
    duplicateField,
    renameField,
    updateFieldFull,
    deleteField,
    addView,
    setActiveView,
    deleteView,
    duplicateView,
    renameView: renameView as (viewId: string, name: string) => void,
    saveActiveViewConfig,
    saveActiveViewConfigAndReload,
    getFilteredRecords,
    getGroupedRecords,
    computeFormulaFields,
    clearStorage,
    undo,
    redo,
    canUndo: computed(() => undoStack.value.length > 0),
    canRedo: computed(() => redoStack.value.length > 0),
    // Permission
    myPermission,
    loadMyPermission,
    canManageTable,
    canManagePermission,
    canManageField,
    canManageView,
    canAddRecord,
    canEditRecord,
    canDeleteRecord,
    canExport,
    canImport,
    isOwnerOrManager,
    // Summary
    summaryData,
    loadSummary,
    loadSummaryDebounced,
    updateSummaryConfig,
    // Group collapse
    collapsedGroups,
    toggleGroupCollapse,
    isGroupCollapsed,
    collapseAllGroups,
    expandAllGroups,
    // Validation
    validateCell,
    // Offline
    isOnline,
    offlinePendingCount,
    offlineSyncing,
    initOfflineListeners,
    destroyOfflineListeners,
    syncOfflineOps,
  }
})
