// Chat API Service for SupremeAI 2.0
// বাংলা মонтаব্য: চ্যাট ইন্টারফেস ও স্ট্রিমিং এপিআই এর সাথে যোগাযোগের জন্য ব্যবহৃত সার্ভিস। Prompt-to-Action সাপোর্ট সহ।

import { apiClient, getAuthHeaders } from './apiClient';
import { getApiBaseUrl } from '../utils/api';

import type { UnifiedChatMessage } from '../types/chat';

export type ChatMessage = UnifiedChatMessage;

export interface ChatResponse {
  response: string;
  tokens_used?: number;
  provider?: string;
  duration?: number;
  action?: {
    type: string;
    target?: string;
    label?: string;
    icon?: string;
    confidence?: number;
    requires_confirmation?: boolean;
    payload?: Record<string, unknown>;
  };
}

// বাংলা মন্তব্য: ফাংশন ডিক্লেয়ারেশন সিনট্যাক্স এরর ঠিক করা হলো
export async function sendMessageStream(
  message: string,
  onToken: (token: string) => void,
  onDone: (action?: ChatResponse['action']) => void,
  onError: (error: string) => void,
  abortSignal?: AbortSignal,
): Promise<void> {
  const API_BASE = getApiBaseUrl();
  const authHeaders = await getAuthHeaders();  // 🔒 Get JWT/CSRF/Fingerprint headers

  // Issue #1680 (streaming cold-start retry): the stream endpoint had no
  // retry — a single 502/503/504 (Render free-tier cold start) or transient
  // network blip killed the chat. Before the stream starts, we now retry
  // connection-level failures up to 4 attempts with exponential backoff +
  // jitter (mirrors apiClient.throttledFetch #1679). Once the reader is
  // obtained, no retry happens — duplicate tokens would corrupt the UI.
  // বাংলা: স্ট্রিম শুরু হওয়ার আগে 50x/নেটওয়ার্ক ত্রুটিতে সূচকীয় ব্যাকঅফসহ
  // রিট্রাই; স্ট্রিম শুরু হওয়ার পর কোনো রিট্রাই নেই (ডুপ্লিকেট টোকেন এড়াতে)।
  const STREAM_MAX_ATTEMPTS = 4;

  try {
    // 🔒 SECURITY FIX: Now includes authentication headers (previously missing)
    // FIX (API-contract audit): migrated to the hardened SSE pipeline
    // (POST /api/v1/stream/chat) — state machine, 15s heartbeat, chunk
    // sanitization. Body sends { message }; backend harmonizes to `prompt`.
    let res: Response | null = null;
    let lastHttpError = '';

    for (let attempt = 1; attempt <= STREAM_MAX_ATTEMPTS; attempt++) {
      let attemptRes: Response;
      try {
        attemptRes = await fetch(`${API_BASE}/api/v1/stream/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...authHeaders,  // Spread auth headers into request
          },
          body: JSON.stringify({ message }),
          signal: abortSignal,
        });
      } catch (err) {
        if (abortSignal?.aborted) throw err;  // user cancelled — not retryable
        if (attempt >= STREAM_MAX_ATTEMPTS) throw err;
        lastHttpError = (err as Error)?.message ?? 'network error';
        const delayMs = Math.round(Math.pow(2, attempt) * 1000 + Math.random() * 1000);
        await new Promise(resolve => setTimeout(resolve, delayMs));
        continue;
      }

      if (attemptRes.ok) {
        res = attemptRes;
        break;
      }

      const retryable = attemptRes.status >= 502 && attemptRes.status <= 504;
      lastHttpError = `HTTP ${attemptRes.status}: ${attemptRes.statusText}`;
      if (!retryable || attempt >= STREAM_MAX_ATTEMPTS) {
        onError(lastHttpError);
        return;
      }
      const delayMs = Math.round(Math.pow(2, attempt) * 1000 + Math.random() * 1000);
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }

    if (!res) {
      onError(lastHttpError || 'Stream connection failed after retries');
      return;
    }

    const reader = res.body?.getReader();
    if (!reader) {
      onError('No stream body available');
      return;
    }

    const decoder = new TextDecoder();
    let _fullText = '';
    let pending = '';

    const consumeLine = (line: string) => {
      const normalized = line.trim();
      if (!normalized) return;
      const payload = normalized.startsWith('data:') ? normalized.slice(5).trim() : normalized;
      if (!payload || payload === '[DONE]') return;
      try {
        const parsed = JSON.parse(payload) as { token?: string; delta?: string; content?: string; response?: string; result?: string };
        const token = parsed.token ?? parsed.delta ?? parsed.content ?? parsed.response ?? parsed.result;
        if (token) {
          _fullText += token;
          onToken(token);
        }
      } catch {
        _fullText += payload;
        onToken(payload);
      }
    };

    while (true) {
      const { value, done } = await reader.read();
      pending += decoder.decode(value ?? new Uint8Array(), { stream: !done });
      const lines = pending.split(/\r?\n/);
      pending = lines.pop() ?? '';
      lines.forEach(consumeLine);
      if (done) break;
    }
    if (pending) consumeLine(pending);
    // Prompt-to-Action metadata fallback (legacy path only)
    try {
      const actionHeaders = await getAuthHeaders();  // 🔒 Auth for action endpoint too
      const actionRes = await fetch(`${API_BASE}/api/chat/prompt-action`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...actionHeaders,  // 🔒 Include auth headers
        },
        body: JSON.stringify({ message }),
      });
      if (actionRes.ok) {
        const actionData = await actionRes.json();
        onDone(actionData.action);
      } else {
        onDone(undefined);
      }
    } catch {
      onDone(undefined);
    }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (err: any) {
    if (err.name !== 'AbortError') {
      onError(err.message);
    }
  }
};

export const chatService = {
  sendMessage: async (message: string, history: ChatMessage[] = []): Promise<ChatResponse> => {
    // FIX (API-contract audit): TaskRequest requires `task`; `history` maps to
    // `messages`. The old {message, history} shape hit Pydantic 422.
    return apiClient.post<ChatResponse>('/api/task/execute', {
      task: message,
      messages: history,
    });
  },

  sendMessageStream,

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getVoices: async (): Promise<any[]> => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return apiClient.get<any[]>('/api/voice/voices');
  },
};

export async function getAethelResponse(message: string, history: ChatMessage[] = []): Promise<string> {
  const response = await apiClient.post<{ result: string }>('/api/task/execute', {
    task: message,
    task_type: 'general',
    messages: history,
  });
  return response.result || 'No response from AI backend.';
}
