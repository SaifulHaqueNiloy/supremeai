import type { StateCreator } from 'zustand';
import type { SupremeStore } from '../useSupremeStore';

export interface CoreSlice {
  loading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  initialize: () => Promise<void>;
  reset: () => void;
}

export const createCoreSlice: StateCreator<SupremeStore, [], [], CoreSlice> = (set, get) => ({
  loading: false,
  error: null,
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  initialize: async () => {
    set({ loading: true, error: null });
    try {
      await Promise.all([
        get().fetchWorkspaces(),
        get().fetchUsers(),
        get().loadSettings(),
        get().fetchSessions(),
        get().fetchCustomers(),
      ]);
    } catch {
      set({ error: 'Initialization failed' });
    } finally {
      set({ loading: false });
    }
  },
  reset: () =>
    set({
      isAuthenticated: false,
      user: null,
      theme: 'system',
      metrics: {},
      recentActivity: [],
      quickActions: [],
      users: [],
      roles: [],
      permissions: [],
      activeWorkspace: null,
      workspaces: [],
      settings: {},
      sessions: [],
      activeSession: null,
      activeFile: null,
      openFiles: [],
      editorContent: {},
      customers: [],
      selectedCustomer: null,
      loading: false,
      error: null,
    }),
});
