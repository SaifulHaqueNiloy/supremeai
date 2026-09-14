/**
 * chatSlice — Chat state for unified store migration (Phase 2).
 *
 * Maps the legacy chatStore to the unified store's `chat` slice.
 * This is the missing piece referenced by migration_map.ts line 22:
 *   chatStore: 'chat', // new chatSlice (TODO: create in Phase 2)
 *
 * Phase 1 (current): Slice created, UNIFIED_STORE flag remains off.
 * Phase 2 (next): Flag toggled in staging, legacy chatStore becomes shim.
 * Phase 3 (N+1):    Delete shim files, sweep importers to unifiedStore.
 */

import type { UnifiedChatMessage } from '../../types/chat';

export interface ChatSliceState {
  /** Unread message count across all conversations */
  unreadCount: number;
  /** Currently active conversation ID (if any) */
  activeConversationId: string | null;
  /** Locally cached recent messages for the active conversation */
  cachedMessages: UnifiedChatMessage[];
  /** Whether the chat panel is expanded */
  chatPanelExpanded: boolean;
}

export type ChatSlice = ChatSliceState;

export const createChatSlice = (..._args: unknown[]): ChatSlice => ({
  unreadCount: 0,
  activeConversationId: null,
  cachedMessages: [],
  chatPanelExpanded: true,
});

/** Increment unread count — safe setter for use in components */
export const incrementUnread = (state: ChatSliceState): void => {
  state.unreadCount += 1;
};

/** Clear unread count after user views messages */
export const clearUnread = (state: ChatSliceState): void => {
  state.unreadCount = 0;
};

/** Set the active conversation */
export const setActiveConversation = (
  state: ChatSliceState,
  conversationId: string | null,
): void => {
  state.activeConversationId = conversationId;
  if (conversationId === null) {
    state.cachedMessages = [];
  }
};

/** Append a message to the local cache */
export const appendMessage = (
  state: ChatSliceState,
  message: UnifiedChatMessage,
): void => {
  state.cachedMessages = [...state.cachedMessages, message].slice(-200);
};
