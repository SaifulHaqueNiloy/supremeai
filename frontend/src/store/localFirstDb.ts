/**
 * R13 FIX Phase 3: Local-First Database (Dexie / IndexedDB)
 *
 * Persists user data (chat history, agent sessions, preferences) locally
 * in the browser, so the cloud Supabase DB is not hit on every read.
 * Cloud sync happens in the background via the `syncQueue` table.
 *
 * Add to package.json dependencies:
 *   "dexie": "^4.0.10",
 *   "dexie-react-hooks": "^1.1.7"
 */
import Dexie, { type Table } from 'dexie';

export interface ChatMessage {
  id?: number;
  conversationId: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  createdAt: number;
  syncedAt?: number | null; // null = pending sync
}

export interface Conversation {
  id?: number;
  externalId?: string; // Supabase UUID when synced
  title: string;
  createdAt: number;
  updatedAt: number;
  syncedAt?: number | null;
}

export interface UserPreference {
  key: string;
  value: unknown;
  updatedAt: number;
  syncedAt?: number | null;
}

export interface SyncQueueItem {
  id?: number;
  table: 'chats' | 'conversations' | 'preferences';
  recordId: string | number;
  operation: 'create' | 'update' | 'delete';
  payload: unknown;
  queuedAt: number;
  attempts: number;
}

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
  }
}

export const localDb = new SupremeAILocalDB();

/**
 * Background sync — runs every 30s while online. Drains syncQueue into
 * Supabase via the /api/v1/sync endpoints.
 *
 * Call this once at app boot from main.tsx:
 *   import { startBackgroundSync } from '@/store/localFirstDb';
 *   startBackgroundSync();
 */
export const startBackgroundSync = (): void => {
  if (typeof window === 'undefined') return;

  setInterval(async () => {
    if (!navigator.onLine) return;
    const pending = await localDb.syncQueue
      .where('queuedAt')
      .below(Date.now())
      .limit(10)
      .toArray();

    for (const item of pending) {
      try {
        const method =
          item.operation === 'create'
            ? 'POST'
            : item.operation === 'update'
              ? 'PUT'
              : 'DELETE';

        const resp = await fetch(`/api/v1/sync/${item.table}`, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item.payload),
        });

        if (resp.ok) {
          await localDb.syncQueue.delete(item.id!);
        } else {
          await localDb.syncQueue.update(item.id!, {
            attempts: item.attempts + 1,
          });
        }
      } catch {
        await localDb.syncQueue.update(item.id!, {
          attempts: item.attempts + 1,
        });
      }
    }
  }, 30_000);
};
