import type { StateCreator } from 'zustand';
import { getApiBaseUrl } from '../../utils/api';
import type { SupremeStore } from '../useSupremeStore';
import type { Session } from './types';

export interface SessionCockpitSlice {
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
}

export const createSessionCockpitSlice: StateCreator<SupremeStore, [], [], SessionCockpitSlice> = (set) => ({
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
});
