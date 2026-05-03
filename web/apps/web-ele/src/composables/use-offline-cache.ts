import { ref, onMounted, onUnmounted } from 'vue'

const DB_NAME = 'zq-smart-table-offline'
const DB_VERSION = 1
const STORE_TABLE_DATA = 'tableData'
const STORE_PENDING_OPS = 'pendingOps'

export interface PendingOperation {
  id: string
  type: 'updateCell' | 'createRecord' | 'deleteRecord'
  tableId: string
  recordId: string
  payload: Record<string, any>
  timestamp: number
}

let _db: IDBDatabase | null = null

function openDB(): Promise<IDBDatabase> {
  if (_db) return Promise.resolve(_db)

  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)

    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(STORE_TABLE_DATA)) {
        db.createObjectStore(STORE_TABLE_DATA, { keyPath: 'id' })
      }
      if (!db.objectStoreNames.contains(STORE_PENDING_OPS)) {
        const store = db.createObjectStore(STORE_PENDING_OPS, { keyPath: 'id' })
        store.createIndex('byTable', 'tableId', { unique: false })
        store.createIndex('byTimestamp', 'timestamp', { unique: false })
      }
    }

    req.onsuccess = () => {
      _db = req.result
      resolve(_db)
    }

    req.onerror = () => reject(req.error)
  })
}

function promisify<T>(req: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

function waitTx(tx: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}

function genId(): string {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

// ==================== Module-level exports (no Vue dependency) ====================

export async function cacheTableData(tableId: string, data: any) {
  try {
    const db = await openDB()
    const store = db.transaction(STORE_TABLE_DATA, 'readwrite').objectStore(STORE_TABLE_DATA)
    await promisify(store.put({ id: tableId, data, cachedAt: Date.now() }))
  } catch {
    // silently fail
  }
}

export async function getCachedTableData(tableId: string): Promise<any | null> {
  try {
    const db = await openDB()
    const store = db.transaction(STORE_TABLE_DATA, 'readonly').objectStore(STORE_TABLE_DATA)
    const result = await promisify(store.get(tableId))
    if (!result) return null
    const maxAge = 24 * 60 * 60 * 1000
    if (Date.now() - result.cachedAt > maxAge) return null
    return result.data
  } catch {
    return null
  }
}

export async function addPendingOp(op: Omit<PendingOperation, 'id' | 'timestamp'>) {
  try {
    const db = await openDB()

    if (op.type === 'updateCell') {
      const readTx = db.transaction(STORE_PENDING_OPS, 'readonly')
      const readStore = readTx.objectStore(STORE_PENDING_OPS)
      const existing: PendingOperation[] = await promisify(
        readStore.index('byTable').getAll(op.tableId),
      )
      const toRemove = existing
        .filter(
          (prev) =>
            prev.type === 'updateCell' &&
            prev.recordId === op.recordId &&
            prev.payload.fieldId === op.payload.fieldId,
        )
        .map((prev) => prev.id)

      const writeTx = db.transaction(STORE_PENDING_OPS, 'readwrite')
      const writeStore = writeTx.objectStore(STORE_PENDING_OPS)
      for (const id of toRemove) {
        writeStore.delete(id)
      }
      writeStore.put({ ...op, id: genId(), timestamp: Date.now() })
      await waitTx(writeTx)
    } else {
      const tx = db.transaction(STORE_PENDING_OPS, 'readwrite')
      const store = tx.objectStore(STORE_PENDING_OPS)
      store.put({ ...op, id: genId(), timestamp: Date.now() })
      await waitTx(tx)
    }
  } catch {
    // silently fail
  }
}

export async function getPendingOps(): Promise<PendingOperation[]> {
  try {
    const db = await openDB()
    const store = db.transaction(STORE_PENDING_OPS, 'readonly').objectStore(STORE_PENDING_OPS)
    return await promisify(store.index('byTimestamp').getAll())
  } catch {
    return []
  }
}

export async function getPendingCount(): Promise<number> {
  try {
    const db = await openDB()
    const store = db.transaction(STORE_PENDING_OPS, 'readonly').objectStore(STORE_PENDING_OPS)
    return await promisify(store.count())
  } catch {
    return 0
  }
}

export async function removePendingOps(ids: string[]) {
  if (ids.length === 0) return
  try {
    const db = await openDB()
    const tx = db.transaction(STORE_PENDING_OPS, 'readwrite')
    const store = tx.objectStore(STORE_PENDING_OPS)
    for (const id of ids) {
      store.delete(id)
    }
    await waitTx(tx)
  } catch {
    // silently fail
  }
}

export async function syncAllPendingOps(): Promise<number> {
  const ops = await getPendingOps()
  if (ops.length === 0) return 0

  const {
    updateCellApi,
    batchUpdateCellsApi,
    createRecordApi,
    deleteRecordApi,
    batchUpdateMultiRecordCellsApi,
  } = await import('#/api/smart-table')

  const cellOpsByTable: Record<string, { recordId: string; fieldId: string; value: unknown; opId: string }[]> = {}
  const otherOps: PendingOperation[] = []

  for (const op of ops) {
    if (op.type === 'updateCell') {
      if (!cellOpsByTable[op.tableId]) cellOpsByTable[op.tableId] = []
      cellOpsByTable[op.tableId]!.push({
        recordId: op.recordId,
        fieldId: op.payload.fieldId as string,
        value: op.payload.value,
        opId: op.id,
      })
    } else {
      otherOps.push(op)
    }
  }

  let synced = 0

  for (const [tableId, cellOps] of Object.entries(cellOpsByTable)) {
    const byRecord: Record<string, Record<string, unknown>> = {}
    for (const cop of cellOps) {
      if (!byRecord[cop.recordId]) byRecord[cop.recordId] = {}
      byRecord[cop.recordId]![cop.fieldId] = cop.value
    }

    const recordIds = Object.keys(byRecord)
    try {
      if (recordIds.length > 1) {
        await batchUpdateMultiRecordCellsApi(
          tableId,
          recordIds.map((rid) => ({ record_id: rid, cells: byRecord[rid]! })),
        )
      } else if (recordIds.length === 1) {
        const rid = recordIds[0]!
        const cells = byRecord[rid]!
        const fieldIds = Object.keys(cells)
        if (fieldIds.length === 1) {
          await updateCellApi(rid, fieldIds[0]!, cells[fieldIds[0]!])
        } else {
          await batchUpdateCellsApi(rid, cells)
        }
      }
      await removePendingOps(cellOps.map((c) => c.opId))
      synced += cellOps.length
    } catch {
      // keep pending ops for retry
    }
  }

  for (const op of otherOps) {
    try {
      if (op.type === 'createRecord') {
        await createRecordApi(op.tableId, op.payload.values)
      } else if (op.type === 'deleteRecord') {
        await deleteRecordApi(op.recordId)
      }
      await removePendingOps([op.id])
      synced++
    } catch {
      // keep for retry
    }
  }

  return synced
}

export async function clearOfflineCache(tableId?: string) {
  try {
    const db = await openDB()
    const store = db.transaction(STORE_TABLE_DATA, 'readwrite').objectStore(STORE_TABLE_DATA)
    if (tableId) {
      await promisify(store.delete(tableId))
    } else {
      await promisify(store.clear())
    }
  } catch {
    // silently fail
  }
}

// ==================== Vue Composable (for component usage with lifecycle) ====================

export function useOfflineCache() {
  const isOnline = ref(navigator.onLine)
  const pendingCount = ref(0)
  const syncing = ref(false)

  async function handleOnline() {
    isOnline.value = true
    await doSync()
  }

  function handleOffline() {
    isOnline.value = false
  }

  async function refreshCount() {
    pendingCount.value = await getPendingCount()
  }

  async function doSync() {
    if (syncing.value || !isOnline.value) return
    syncing.value = true
    try {
      await syncAllPendingOps()
    } finally {
      syncing.value = false
      await refreshCount()
    }
  }

  onMounted(async () => {
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    try {
      await openDB()
      await refreshCount()
    } catch {
      // IndexedDB not available
    }
  })

  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })

  return {
    isOnline,
    pendingCount,
    syncing,
    cacheTableData,
    getCachedTableData,
    addPendingOp,
    syncPendingOps: doSync,
    clearCache: clearOfflineCache,
    refreshCount,
  }
}
