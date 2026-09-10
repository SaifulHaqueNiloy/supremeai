import Dexie, { type Table } from 'dexie';

export interface ChatMessage {
  id?: number;
  scope: string;
  conversationId: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  createdAt: number;
  syncedAt?: number | null;
}

export interface Conversation {
  id?: number;
  scope: string;
  externalId?: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  syncedAt?: number | null;
}

export interface UserPreference {
  key: string;
  scope: string;
  value: unknown;
  updatedAt: number;
  syncedAt?: number | null;
}

export interface SyncQueueItem {
  id?: number;
  scope: string;
  table: 'chats' | 'conversations' | 'preferences';
  recordId: string | number;
  operation: 'create' | 'update' | 'delete';
  payload: unknown;
  queuedAt: number;
  attempts: number;
  nextAttemptAt: number;
  lastError?: string;
}

let activeScope: string | null = null;
let syncTimer: ReturnType<typeof setInterval> | null = null;
let syncInFlight = false;

export const setLocalDataScope = (scope: string | null): void => {
  activeScope = scope?.trim() || null;
};

export const getLocalDataScope = (): string | null => activeScope;

export const clearLocalDataScope = async (): Promise<void> => {
  const scope = activeScope;
  activeScope = null;
  if (!scope || typeof indexedDB === 'undefined') return;
  await localDb.transaction('rw', localDb.chats, localDb.conversations, localDb.preferences, localDb.syncQueue, async () => {
    await Promise.all([
      localDb.chats.where('scope').equals(scope).delete(),
      localDb.conversations.where('scope').equals(scope).delete(),
      localDb.preferences.where('scope').equals(scope).delete(),
      localDb.syncQueue.where('scope').equals(scope).delete(),
    ]);
  });
};

class SupremeAILocalDB extends Dexie {
  conversations!: Table<Conversation, number>;
  chats!: Table<ChatMessage, number>;
  preferences!: Table<UserPreference, string>;
  syncQueue!: Table<SyncQueueItem, number>;

  constructor() {
    super('SupremeAI');
    this.version(1).stores({
      conversations: '++id, externalId, updatedAt, syncedAt',
      chats: '++id, conversationId, createdAt, syncedAt',
      preferences: 'key, updatedAt, syncedAt',
      syncQueue: '++id, table, recordId, queuedAt, attempts',
    });
    this.version(2).stores({
      conversations: '++id, [scope+id], [scope+externalId], scope, updatedAt, syncedAt',
      chats: '++id, [scope+conversationId], scope, createdAt, syncedAt',
      preferences: '[scope+key], scope, updatedAt, syncedAt',
      syncQueue: '++id, [scope+table], [scope+recordId], scope, queuedAt, attempts, nextAttemptAt',
    }).upgrade(async (tx) => {
      for (const table of [tx.table('conversations'), tx.table('chats'), tx.table('preferences'), tx.table('syncQueue')]) {
        await table.toCollection().modify((record) => { record.scope = 'legacy:unscoped'; });
      }
    });
  }
}

export const localDb = new SupremeAILocalDB();

const MAX_ATTEMPTS = 8;
const BASE_RETRY_MS = 5_000;

const getAuthToken = (): string | null => {
  try {
    return localStorage.getItem('supremeai_auth_token');
  } catch {
    return null;
  }
};

const syncPending = async (): Promise<void> => {
  if (syncInFlight || !navigator.onLine || !activeScope) return;
  syncInFlight = true;
  try {
    const pending = await localDb.syncQueue
      .where('[scope+table]')
      .between([activeScope, Dexie.minKey], [activeScope, Dexie.maxKey])
      .filter((item) => item.nextAttemptAt <= Date.now() && item.attempts < MAX_ATTEMPTS)
      .limit(10)
      .toArray();

    for (const item of pending) {
      try {
        const method = item.operation === 'create' ? 'POST' : item.operation === 'update' ? 'PUT' : 'DELETE';
        const token = getAuthToken();
        const response = await fetch(`/api/v1/sync/${item.table}`, {
          method,
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            'X-SupremeAI-Scope': item.scope,
          },
          body: JSON.stringify({ scope: item.scope, ...(item.payload as Record<string, unknown>) }),
          credentials: 'include',
        });
        if (!response.ok) throw new Error(`Sync failed with status ${response.status}`);
        await localDb.syncQueue.delete(item.id!);
      } catch (error) {
        const attempts = item.attempts + 1;
        await localDb.syncQueue.update(item.id!, {
          attempts,
          lastError: error instanceof Error ? error.message : 'Unknown sync error',
          nextAttemptAt: Date.now() + Math.min(BASE_RETRY_MS * 2 ** item.attempts, 5 * 60_000),
        });
      }
    }
  } finally {
    syncInFlight = false;
  }
};

export const startBackgroundSync = (): (() => void) => {
  if (typeof window === 'undefined' || syncTimer) return () => undefined;
  syncTimer = setInterval(() => { void syncPending(); }, 30_000);
  window.addEventListener('online', syncPending);
  void syncPending();
  return () => {
    if (syncTimer) clearInterval(syncTimer);
    syncTimer = null;
    window.removeEventListener('online', syncPending);
  };
};

export const syncNow = syncPending;
export const MAX_SYNC_ATTEMPTS = MAX_ATTEMPTS;

export function createSyncQueueItem(input: Omit<SyncQueueItem, 'scope' | 'attempts' | 'nextAttemptAt'>): SyncQueueItem {
  if (!activeScope) throw new Error('Cannot queue offline data without an authenticated scope');
  return { ...input, scope: activeScope, attempts: 0, nextAttemptAt: Date.now() };
}
