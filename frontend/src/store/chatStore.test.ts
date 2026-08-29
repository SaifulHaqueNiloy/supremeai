import { describe, it, expect, vi, beforeEach } from 'vitest';

const getMock = vi.fn();
const postMock = vi.fn();

vi.mock('../services/apiClient', () => ({
  apiClient: {
    get: (...args: unknown[]) => getMock(...args),
    post: (...args: unknown[]) => postMock(...args),
  },
}));

import { useChatStore } from './chatStore';
import { eventBus, Events } from '../lib/componentEventBus';

describe('chatStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    eventBus.clear();
    useChatStore.setState({
      conversations: [],
      activeConversationId: null,
      messages: [],
      input: '',
      isLoading: false,
      isStreaming: false,
      error: null,
    });
  });

  it('sets the input text', () => {
    useChatStore.getState().setInput('hello');
    expect(useChatStore.getState().input).toBe('hello');
  });

  it('adds a user message and emits CHAT_MESSAGE_SENT', () => {
    const handler = vi.fn();
    eventBus.on(Events.CHAT_MESSAGE_SENT, handler);
    useChatStore.getState().addMessage({ role: 'user', content: 'hi' });
    expect(useChatStore.getState().messages).toHaveLength(1);
    expect(useChatStore.getState().messages[0].content).toBe('hi');
    expect(handler).toHaveBeenCalled();
  });

  it('adds an assistant message and emits CHAT_MESSAGE_RECEIVED', () => {
    const handler = vi.fn();
    eventBus.on(Events.CHAT_MESSAGE_RECEIVED, handler);
    useChatStore.getState().addMessage({ role: 'assistant', content: 'yo' });
    expect(useChatStore.getState().messages).toHaveLength(1);
    expect(handler).toHaveBeenCalled();
  });

  it('persists added messages to the backend', async () => {
    postMock.mockResolvedValue({});
    useChatStore.getState().addMessage({ role: 'user', content: 'hi' });
    await new Promise((r) => setTimeout(r, 0));
    expect(postMock).toHaveBeenCalled();
  });

  it('caps stored messages at MAX_MESSAGES by keeping the most recent', () => {
    const long = Array.from({ length: 1001 }, (_, i) => ({
      role: 'user' as const,
      content: `m${i}`,
    }));
    long.forEach((m) => useChatStore.getState().addMessage(m));
    const msgs = useChatStore.getState().messages;
    expect(msgs).toHaveLength(1000);
    expect(msgs[0].content).toBe('m1');
  });

  it('clears messages', () => {
    useChatStore.getState().addMessage({ role: 'user', content: 'hi' });
    useChatStore.getState().clearMessages();
    expect(useChatStore.getState().messages).toHaveLength(0);
  });

  it('loads conversations from the backend', async () => {
    getMock.mockResolvedValue({ data: [{ id: 'c1' }] });
    const handler = vi.fn();
    eventBus.on(Events.METRICS_UPDATE_AVAILABLE, handler);
    await useChatStore.getState().loadConversations();
    expect(useChatStore.getState().conversations).toHaveLength(1);
    expect(useChatStore.getState().isLoading).toBe(false);
    expect(handler).toHaveBeenCalled();
  });

  it('falls back to local-only when loading fails', async () => {
    getMock.mockRejectedValue(new Error('network'));
    await useChatStore.getState().loadConversations();
    expect(useChatStore.getState().conversations).toHaveLength(0);
    expect(useChatStore.getState().isLoading).toBe(false);
  });
});
