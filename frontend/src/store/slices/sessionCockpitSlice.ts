import type { StateCreator } from 'zustand';
import { getApiBaseUrl, getWebSocketBaseUrl } from '../../utils/api';
import { getRawToken } from '../../services/apiClient';
import type { SupremeStore } from '../useSupremeStore';
import type { Session } from './types';

export type SujonState =
  | 'idle'
  | 'scanning'
  | 'executing'
  | 'circuit_open'
  | 'self_healing'
  | 'awaiting_human'
  | 'success'
  | 'failed'
  | 'processing';

export interface LogEntry {
  id: string;
  ts: string;
  log_type: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload: any;
}

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  status: 'new' | 'modified' | 'deleted' | 'unchanged';
}

export interface ReasoningEntry {
  id: string;
  ts: string;
  token: string;
}

export interface SessionCockpitSlice {
  // Admin Session CRUD
  sessions: Session[];
  activeSession: Session | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  createSession: (sessionData: any) => void;
  closeSession: (sessionId: string) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setActiveSession: (session: any) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  updateSession: (sessionId: string, updates: any) => void;
  fetchSessions: () => Promise<void>;

  // Real-time agent cockpit execution state
  cockpitSessionId: string | null;
  logBuffer: LogEntry[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fileTreeData: any;
  reasoningChain: ReasoningEntry[];
  agentState: SujonState;
  controlMode: 'agent' | 'human';
  sseRef: EventSource | null;
  wsRef: WebSocket | null;

  resetSessionState: () => void;
  connectSSE: (sessionId: string) => void;
  disconnectSSE: () => void;
  connectTakeoverWS: (sessionId: string, token: string) => void;
  disconnectTakeoverWS: () => void;
  addLog: (log: LogEntry) => void;
}

const MAX_LOGS = 10000;

export const createSessionCockpitSlice: StateCreator<SupremeStore, [], [], SessionCockpitSlice> = (set, get) => ({
  sessions: [],
  activeSession: null,
  createSession: (sessionData) =>
    set((state) => ({ sessions: [...state.sessions, { id: Date.now().toString(), ...sessionData }] })),
  closeSession: (sessionId) =>
    set((state) => ({
      sessions: state.sessions.filter((session) => session.id !== sessionId),
      activeSession: state.activeSession?.id === sessionId ? null : state.activeSession,
    })),
  setActiveSession: (session) => set({ activeSession: session }),
  updateSession: (sessionId, updates) =>
    set((state) => ({
      sessions: state.sessions.map((session) =>
        session.id === sessionId ? { ...session, ...updates } : session,
      ),
    })),
  fetchSessions: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${getApiBaseUrl()}/admin-api/sessions`);
      const sessions = await response.json();
      set({ sessions });
    } catch {
      set({ error: 'Failed to fetch sessions' });
    } finally {
      set({ loading: false });
    }
  },

  cockpitSessionId: null,
  logBuffer: [],
  fileTreeData: null,
  reasoningChain: [],
  agentState: 'idle',
  controlMode: 'agent',
  sseRef: null,
  wsRef: null,

  resetSessionState: () => {
    const { sseRef, wsRef } = get();
    if (sseRef) {
      sseRef.close();
    }
    if (wsRef) {
      wsRef.close();
    }
    set({
      cockpitSessionId: null,
      logBuffer: [],
      fileTreeData: null,
      reasoningChain: [],
      agentState: 'idle',
      controlMode: 'agent',
      sseRef: null,
      wsRef: null,
    });
  },

  connectSSE: (sessionId: string) => {
    get().disconnectSSE();
    const token = getRawToken();
    const sse = new EventSource(`${getApiBaseUrl()}/api/session/${sessionId}/stream${token ? `?token=${encodeURIComponent(token)}` : ''}`);
    sse.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        if (parsed.channel === 'logs') {
          get().addLog(parsed.data);
        } else if (parsed.channel === 'state') {
          set({ agentState: parsed.data.current_state });
        }
      } catch (err) {
        console.error('SSE parse error', err);
      }
    };
    set({ sseRef: sse, cockpitSessionId: sessionId });
  },

  disconnectSSE: () => {
    const { sseRef } = get();
    if (sseRef) {
      sseRef.close();
      set({ sseRef: null });
    }
  },

  connectTakeoverWS: (sessionId: string, token: string) => {
    get().disconnectTakeoverWS();
    const baseUrl = getWebSocketBaseUrl();
    const ws = new WebSocket(`${baseUrl}/ws/session/${sessionId}/takeover?token=${token}`);

    ws.onopen = () => {
      set({ controlMode: 'human' });
    };
    ws.onclose = () => {
      set({ controlMode: 'agent' });
    };
    set({ wsRef: ws });
  },

  disconnectTakeoverWS: () => {
    const { wsRef } = get();
    if (wsRef) {
      wsRef.close();
      set({ wsRef: null });
    }
  },

  addLog: (log: LogEntry) => {
    set((state) => {
      const newBuffer = [...state.logBuffer, log];
      if (newBuffer.length > MAX_LOGS) {
        return { logBuffer: newBuffer.slice(newBuffer.length - MAX_LOGS) };
      }
      return { logBuffer: newBuffer };
    });
  },
});
