import type { ChatMessage, Conversation } from '#/api/core/chat';

const DB_NAME = 'zq_chat_cache';
const DB_VERSION = 1;
const STORE_CONVERSATIONS = 'conversations';
const STORE_MESSAGES = 'messages';
const STORE_META = 'meta';

// 每个会话最多缓存的消息数量
const MAX_MESSAGES_PER_CONVERSATION = 200;

let dbPromise: null | Promise<IDBDatabase> = null;

function openDB(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise;

  dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      // 会话表: 按 userId 分区存储
      if (!db.objectStoreNames.contains(STORE_CONVERSATIONS)) {
        const convStore = db.createObjectStore(STORE_CONVERSATIONS, {
          keyPath: ['userId', 'id'],
        });
        convStore.createIndex('by_user', 'userId', { unique: false });
      }

      // 消息表: 按 conversationId 索引
      if (!db.objectStoreNames.contains(STORE_MESSAGES)) {
        const msgStore = db.createObjectStore(STORE_MESSAGES, {
          keyPath: ['conversationId', 'id'],
        });
        msgStore.createIndex('by_conversation', 'conversationId', {
          unique: false,
        });
        msgStore.createIndex(
          'by_conv_time',
          ['conversationId', 'sys_create_datetime'],
          {
            unique: false,
          },
        );
      }

      // 元数据表: 存储同步时间戳等
      if (!db.objectStoreNames.contains(STORE_META)) {
        db.createObjectStore(STORE_META, { keyPath: 'key' });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => {
      dbPromise = null;
      reject(request.error);
    };
  });

  return dbPromise;
}

// ============ 通用事务辅助 ============

function withStore<T>(
  storeName: string,
  mode: IDBTransactionMode,
  fn: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  return openDB().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, mode);
        const store = tx.objectStore(storeName);
        const req = fn(store);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      }),
  );
}

// ============ 会话操作 ============

export async function getCachedConversations(
  userId: string,
): Promise<Conversation[]> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_CONVERSATIONS, 'readonly');
      const store = tx.objectStore(STORE_CONVERSATIONS);
      const index = store.index('by_user');
      const req = index.getAll(userId);
      req.onsuccess = () => {
        const items = (req.result || []).map((item: any) => {
          const { userId: _uid, ...conv } = item;
          return conv as Conversation;
        });
        // 按 last_message_time 降序，置顶优先
        items.sort((a: Conversation, b: Conversation) => {
          if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1;
          const ta = a.last_message_time || a.sys_create_datetime || '';
          const tb = b.last_message_time || b.sys_create_datetime || '';
          return tb.localeCompare(ta);
        });
        resolve(items);
      };
      req.onerror = () => reject(req.error);
    });
  } catch {
    return [];
  }
}

export async function setCachedConversations(
  userId: string,
  conversations: Conversation[],
): Promise<void> {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_CONVERSATIONS, 'readwrite');
    const store = tx.objectStore(STORE_CONVERSATIONS);

    // 先清除该用户的旧数据
    const index = store.index('by_user');
    const cursorReq = index.openCursor(userId);
    await new Promise<void>((resolve, reject) => {
      cursorReq.onsuccess = () => {
        const cursor = cursorReq.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          resolve();
        }
      };
      cursorReq.onerror = () => reject(cursorReq.error);
    });

    // 写入新数据
    for (const conv of conversations) {
      store.put({ ...conv, userId });
    }

    await new Promise<void>((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (error) {
    console.warn('[ChatStorage] Failed to cache conversations:', error);
  }
}

export async function updateCachedConversation(
  userId: string,
  conversation: Conversation,
): Promise<void> {
  try {
    await withStore(STORE_CONVERSATIONS, 'readwrite', (store) =>
      store.put({ ...conversation, userId }),
    );
  } catch (error) {
    console.warn('[ChatStorage] Failed to update conversation:', error);
  }
}

// ============ 消息操作 ============

export async function getCachedMessages(
  conversationId: string,
  limit = 30,
  beforeId?: string,
): Promise<{ has_more: boolean; items: ChatMessage[] }> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_MESSAGES, 'readonly');
      const store = tx.objectStore(STORE_MESSAGES);
      const index = store.index('by_conversation');
      const req = index.getAll(conversationId);
      req.onsuccess = () => {
        let items: ChatMessage[] = (req.result || []).map((item: any) => {
          const { conversationId: _cid, ...msg } = item;
          return msg as ChatMessage;
        });

        // 按时间排序
        items.sort((a, b) => {
          const ta = a.sys_create_datetime || '';
          const tb = b.sys_create_datetime || '';
          return ta.localeCompare(tb);
        });

        // 如果有 beforeId，截取之前的消息
        if (beforeId) {
          const idx = items.findIndex((m) => m.id === beforeId);
          if (idx > 0) {
            items = items.slice(0, idx);
          } else if (idx === 0) {
            items = [];
          }
        }

        const hasMore = items.length > limit;
        if (hasMore) {
          items = items.slice(items.length - limit);
        }

        resolve({ items, has_more: hasMore });
      };
      req.onerror = () => reject(req.error);
    });
  } catch {
    return { items: [], has_more: false };
  }
}

async function _doSetCachedMessages(
  conversationId: string,
  msgs: ChatMessage[],
): Promise<void> {
  const db = await openDB();
  const tx = db.transaction(STORE_MESSAGES, 'readwrite');
  const store = tx.objectStore(STORE_MESSAGES);

  for (const msg of msgs) {
    if (msg._sending || msg._tempId) continue;
    store.put({
      ...msg,
      conversationId,
      _sending: undefined,
      _tempId: undefined,
      _localUrl: undefined,
    });
  }

  await new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function setCachedMessages(
  conversationId: string,
  msgs: ChatMessage[],
): Promise<void> {
  try {
    await _doSetCachedMessages(conversationId, msgs);
    // 主动裁剪，保持每个会话消息数在限制内
    await trimOldMessages(conversationId);
  } catch (error) {
    if (await handleQuotaError(error)) {
      try {
        await _doSetCachedMessages(conversationId, msgs);
      } catch {
        console.warn('[ChatStorage] Retry failed after pruning:', error);
      }
    } else {
      console.warn('[ChatStorage] Failed to cache messages:', error);
    }
  }
}

export async function addCachedMessage(msg: ChatMessage): Promise<void> {
  if (msg._sending || msg._tempId) return;
  const data = {
    ...msg,
    conversationId: msg.conversation_id,
    _sending: undefined,
    _tempId: undefined,
    _localUrl: undefined,
  };
  try {
    await withStore(STORE_MESSAGES, 'readwrite', (store) => store.put(data));
  } catch (error) {
    if (await handleQuotaError(error)) {
      try {
        await withStore(STORE_MESSAGES, 'readwrite', (store) =>
          store.put(data),
        );
      } catch {
        console.warn('[ChatStorage] Retry failed after pruning:', error);
      }
    } else {
      console.warn('[ChatStorage] Failed to add message:', error);
    }
  }
}

export async function updateCachedMessage(msg: ChatMessage): Promise<void> {
  const data = {
    ...msg,
    conversationId: msg.conversation_id,
    _sending: undefined,
    _tempId: undefined,
    _localUrl: undefined,
  };
  try {
    await withStore(STORE_MESSAGES, 'readwrite', (store) => store.put(data));
  } catch (error) {
    console.warn('[ChatStorage] Failed to update message:', error);
  }
}

// ============ 元数据操作 ============

export async function getLastSyncTime(userId: string): Promise<null | string> {
  try {
    const result = await withStore<any>(STORE_META, 'readonly', (store) =>
      store.get(`sync_${userId}`),
    );
    return result?.value || null;
  } catch {
    return null;
  }
}

export async function setLastSyncTime(userId: string): Promise<void> {
  try {
    await withStore(STORE_META, 'readwrite', (store) =>
      store.put({ key: `sync_${userId}`, value: new Date().toISOString() }),
    );
  } catch (error) {
    console.warn('[ChatStorage] Failed to set sync time:', error);
  }
}

// ============ 容量管理 ============

/**
 * 裁剪指定会话的旧消息，只保留最近 MAX_MESSAGES_PER_CONVERSATION 条
 */
async function trimOldMessages(conversationId: string): Promise<void> {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_MESSAGES, 'readwrite');
    const store = tx.objectStore(STORE_MESSAGES);
    const index = store.index('by_conversation');

    const allMsgs: any[] = await new Promise((resolve, reject) => {
      const req = index.getAll(conversationId);
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });

    if (allMsgs.length <= MAX_MESSAGES_PER_CONVERSATION) return;

    // 按时间排序，删除最旧的
    allMsgs.sort((a, b) => {
      const ta = a.sys_create_datetime || '';
      const tb = b.sys_create_datetime || '';
      return ta.localeCompare(tb);
    });

    const toDelete = allMsgs.slice(
      0,
      allMsgs.length - MAX_MESSAGES_PER_CONVERSATION,
    );
    for (const msg of toDelete) {
      store.delete([msg.conversationId, msg.id]);
    }

    await new Promise<void>((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (error) {
    console.warn('[ChatStorage] Failed to trim messages:', error);
  }
}

/**
 * 全局清理：删除所有会话中超出限制的旧消息
 */
export async function pruneAllOldMessages(): Promise<void> {
  try {
    const db = await openDB();
    const tx = db.transaction(STORE_MESSAGES, 'readonly');
    const store = tx.objectStore(STORE_MESSAGES);
    const index = store.index('by_conversation');

    // 收集所有 conversationId
    const convIds = new Set<string>();
    await new Promise<void>((resolve, reject) => {
      const req = index.openKeyCursor();
      req.onsuccess = () => {
        const cursor = req.result;
        if (cursor) {
          convIds.add(cursor.key as string);
          cursor.continue();
        } else {
          resolve();
        }
      };
      req.onerror = () => reject(req.error);
    });

    for (const convId of convIds) {
      await trimOldMessages(convId);
    }
  } catch (error) {
    console.warn('[ChatStorage] Failed to prune messages:', error);
  }
}

/**
 * 处理存储配额超限：清理旧消息后重试
 * 返回 true 表示已处理，调用方可重试
 */
async function handleQuotaError(error: unknown): Promise<boolean> {
  if (
    error instanceof DOMException &&
    (error.name === 'QuotaExceededError' || error.code === 22)
  ) {
    console.warn('[ChatStorage] Storage quota exceeded, pruning old data...');
    await pruneAllOldMessages();
    return true;
  }
  return false;
}

// ============ 清理 ============

export async function clearChatCache(): Promise<void> {
  try {
    const db = await openDB();
    const tx = db.transaction(
      [STORE_CONVERSATIONS, STORE_MESSAGES, STORE_META],
      'readwrite',
    );
    tx.objectStore(STORE_CONVERSATIONS).clear();
    tx.objectStore(STORE_MESSAGES).clear();
    tx.objectStore(STORE_META).clear();
    await new Promise<void>((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (error) {
    console.warn('[ChatStorage] Failed to clear cache:', error);
  }
}
