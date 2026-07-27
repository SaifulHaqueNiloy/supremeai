import { create } from 'zustand';
import { persist, subscribeWithSelector } from 'zustand/middleware';
import { getApiBaseUrl } from '../utils/api';

interface AuthState {
  isAuthenticated: boolean;
  user: any | null;
  login: (userData: any) => void;
  logout: () => void;
  updateUser: (userData: any) => void;
}

interface ThemeState {
  theme: 'light' | 'dark' | 'system';
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

interface DashboardState {
  metrics: Record<string, any>;
  recentActivity: any[];
  quickActions: any[];
  setMetrics: (metrics: Record<string, any>) => void;
  setRecentActivity: (activity: any[]) => void;
  refreshMetrics: () => Promise<void>;
}

interface AdminState {
  users: any[];
  roles: any[];
  permissions: any[];
  addUser: (user: any) => void;
  removeUser: (userId: string) => void;
  updateUser: (user: any) => void;
  fetchUsers: () => Promise<void>;
  fetchRoles: () => Promise<void>;
  fetchPermissions: () => Promise<void>;
}

interface WorkspaceState {
  activeWorkspace: string | null;
  workspaces: any[];
  setActiveWorkspace: (workspaceId: string) => void;
  createWorkspace: (workspaceData: any) => Promise<void>;
  updateWorkspace: (workspaceId: string, data: any) => Promise<void>;
  deleteWorkspace: (workspaceId: string) => Promise<void>;
  fetchWorkspaces: () => Promise<void>;
}

interface WorkspaceSettingsState {
  settings: Record<string, any>;
  updateSetting: (key: string, value: any) => void;
  resetSettings: () => void;
  saveSettings: () => Promise<void>;
  loadSettings: () => Promise<void>;
}

interface SessionCockpitState {
  sessions: any[];
  activeSession: any | null;
  createSession: (sessionData: any) => void;
  closeSession: (sessionId: string) => void;
  setActiveSession: (session: any) => void;
  updateSession: (sessionId: string, updates: any) => void;
  fetchSessions: () => Promise<void>;
}

interface IdeState {
  activeFile: string | null;
  openFiles: string[];
  editorContent: Record<string, string>;
  addOpenFile: (filePath: string) => void;
  removeOpenFile: (filePath: string) => void;
  setActiveFile: (filePath: string) => void;
  updateEditorContent: (filePath: string, content: string) => void;
  saveFile: (filePath: string) => Promise<void>;
}

interface CustomerState {
  customers: any[];
  selectedCustomer: any | null;
  addCustomer: (customer: any) => void;
  updateCustomer: (customerId: string, customer: any) => void;
  removeCustomer: (customerId: string) => void;
  selectCustomer: (customer: any) => void;
  fetchCustomers: () => Promise<void>;
}

export interface SupremeStore
  extends AuthState,
    ThemeState,
    DashboardState,
    AdminState,
    WorkspaceState,
    WorkspaceSettingsState,
    SessionCockpitState,
    IdeState,
    CustomerState {
  // Initialization
  initialize: () => Promise<void>;
  // Reset all state
  reset: () => void;
  // General loading/error states
  loading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

const useSupremeStore = create<SupremeStore>()(
  persist(
    subscribeWithSelector((set, get) => ({
      // Auth state
      isAuthenticated: false,
      user: null,

      // Theme state
      theme: 'system',

      // Dashboard state
      metrics: {},
      recentActivity: [],
      quickActions: [],

      // Admin state
      users: [],
      roles: [],
      permissions: [],

      // Workspace state
      activeWorkspace: null,
      workspaces: [],

      // Workspace Settings state
      settings: {},

      // Session Cockpit state
      sessions: [],
      activeSession: null,

      // IDE state
      activeFile: null,
      openFiles: [],
      editorContent: {},

      // Customer state
      customers: [],
      selectedCustomer: null,

      // General state
      loading: false,
      error: null,

      // Auth actions
      login: (userData) => set({ isAuthenticated: true, user: userData }),
      logout: () => set({ isAuthenticated: false, user: null }),
      updateUser: (userData) => set({ user: { ...get().user, ...userData } }),

      // Theme actions
      toggleTheme: () => {
        const currentTheme = get().theme;
        const newTheme = currentTheme === 'light' ? 'dark' : currentTheme === 'dark' ? 'system' : 'light';
        set({ theme: newTheme });
      },
      setTheme: (theme) => set({ theme }),

      // Dashboard actions
      setMetrics: (metrics) => set({ metrics }),
      setRecentActivity: (activity) => set({ recentActivity: activity }),
      refreshMetrics: async () => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${getApiBaseUrl()}/admin-api/metrics`);
          if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          const data = await response.json();
          set({ metrics: data, recentActivity: [] });
        } catch (err) {
          console.error("Failed to refresh metrics:", err);
          set({ error: 'Failed to refresh metrics' });
        } finally {
          set({ loading: false });
        }
      },

      // Admin actions
      addUser: (user) => set(state => ({ users: [...state.users, user] })),
      removeUser: (userId) => set(state => ({
        users: state.users.filter(user => user.id !== userId)
      })),
      updateUser: (user) => set(state => ({
        users: state.users.map(u => u.id === user.id ? { ...u, ...user } : u)
      })),
      fetchUsers: async () => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${getApiBaseUrl()}/admin-api/users`);
          if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          const users = await response.json();
          set({ users });
        } catch (err) {
          console.error("Failed to fetch users:", err);
          set({ error: 'Failed to fetch users' });
        } finally {
          set({ loading: false });
        }
      },
      fetchRoles: async () => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${getApiBaseUrl()}/admin-api/roles`);
          if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          const roles = await response.json();
          set({ roles });
        } catch (err) {
          console.error("Failed to fetch roles:", err);
          set({ error: 'Failed to fetch roles' });
        } finally {
          set({ loading: false });
        }
      },
      fetchPermissions: async () => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${getApiBaseUrl()}/admin-api/permissions`);
          if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          const permissions = await response.json();
          set({ permissions });
        } catch (err) {
          console.error("Failed to fetch permissions:", err);
          set({ error: 'Failed to fetch permissions' });
        } finally {
          set({ loading: false });
        }
      },

      // Workspace actions
      setActiveWorkspace: (workspaceId) => set({ activeWorkspace: workspaceId }),
      createWorkspace: async (workspaceData) => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${getApiBaseUrl()}/admin-api/workspaces`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(workspaceData)
          });
          const newWorkspace = await response.json();
          set(state => ({ workspaces: [...state.workspaces, newWorkspace] }));
        } catch (err) {
          set({ error: 'Failed to create workspace' });
        } finally {
          set({ loading: false });
        }
      },
      updateWorkspace: async (workspaceId, data) => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${getApiBaseUrl()}/admin-api/workspaces/${workspaceId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          const updatedWorkspace = await response.json();
          set(state => ({
            workspaces: state.workspaces.map(ws =>
              ws.id === workspaceId ? { ...ws, ...updatedWorkspace } : ws
            )
          }));
        } catch (err) {
          set({ error: 'Failed to update workspace' });
        } finally {
          set({ loading: false });
        }
      },
      deleteWorkspace: async (workspaceId) => {
        set({ loading: true, error: null });
        try {
          await fetch(`${getApiBaseUrl()}/admin-api/workspaces/${workspaceId}`, { method: 'DELETE' });
          set(state => ({
            workspaces: state.workspaces.filter(ws => ws.id !== workspaceId)
          }));
        } catch (err) {
          set({ error: 'Failed to delete workspace' });
        } finally {
          set({ loading: false });
        }
      },
      fetchWorkspaces: async () => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${getApiBaseUrl()}/admin-api/workspaces`);
          const workspaces = await response.json();
          set({ workspaces });
        } catch (err) {
          set({ error: 'Failed to fetch workspaces' });
        } finally {
          set({ loading: false });
        }
      },

      // Workspace Settings actions
      updateSetting: (key, value) => set(state => ({
        settings: { ...state.settings, [key]: value }
      })),
      resetSettings: () => set({ settings: {} }),
      saveSettings: async () => {
        set({ loading: true, error: null });
        try {
          await fetch(`${getApiBaseUrl()}/admin-api/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(get().settings)
          });
        } catch (err) {
          set({ error: 'Failed to save settings' });
        } finally {
          set({ loading: false });
        }
      },
      loadSettings: async () => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${getApiBaseUrl()}/admin-api/settings`);
          const settings = await response.json();
          set({ settings });
        } catch (err) {
          set({ error: 'Failed to load settings' });
        } finally {
          set({ loading: false });
        }
      },

      // Session Cockpit actions
      createSession: (sessionData) => set(state => ({
        sessions: [...state.sessions, { id: Date.now().toString(), ...sessionData }]
      })),
      closeSession: (sessionId) => set(state => ({
        sessions: state.sessions.filter(session => session.id !== sessionId),
        activeSession: state.activeSession?.id === sessionId ? null : state.activeSession
      })),
      setActiveSession: (session) => set({ activeSession: session }),
      updateSession: (sessionId, updates) => set(state => ({
        sessions: state.sessions.map(session =>
          session.id === sessionId ? { ...session, ...updates } : session
        )
      })),
      fetchSessions: async () => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${getApiBaseUrl()}/admin-api/sessions`);
          const sessions = await response.json();
          set({ sessions });
        } catch (err) {
          set({ error: 'Failed to fetch sessions' });
        } finally {
          set({ loading: false });
        }
      },

      // IDE actions
      addOpenFile: (filePath) => set(state => {
        if (!state.openFiles.includes(filePath)) {
          return { openFiles: [...state.openFiles, filePath] };
        }
        return state;
      }),
      removeOpenFile: (filePath) => set(state => ({
        openFiles: state.openFiles.filter(file => file !== filePath),
        activeFile: state.activeFile === filePath ?
          state.openFiles.find(file => file !== filePath) || null :
          state.activeFile
      })),
      setActiveFile: (filePath) => set({ activeFile: filePath }),
      updateEditorContent: (filePath, content) => set(state => ({
        editorContent: { ...state.editorContent, [filePath]: content }
      })),
      saveFile: async (filePath) => {
        set({ loading: true, error: null });
        try {
          await fetch(`${getApiBaseUrl()}/api/files/${encodeURIComponent(filePath)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: get().editorContent[filePath] })
          });
        } catch (err) {
          set({ error: 'Failed to save file' });
        } finally {
          set({ loading: false });
        }
      },

      // Customer actions
      addCustomer: (customer) => set(state => ({ customers: [...state.customers, customer] })),
      updateCustomer: (customerId, customer) => set(state => ({
        customers: state.customers.map(c =>
          c.id === customerId ? { ...c, ...customer } : c
        )
      })),
      removeCustomer: (customerId) => set(state => ({
        customers: state.customers.filter(c => c.id !== customerId)
      })),
      selectCustomer: (customer) => set({ selectedCustomer: customer }),
      fetchCustomers: async () => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${getApiBaseUrl()}/admin-api/customers`);
          const customers = await response.json();
          set({ customers });
        } catch (err) {
          set({ error: 'Failed to fetch customers' });
        } finally {
          set({ loading: false });
        }
      },

      // Initialization
      initialize: async () => {
        set({ loading: true, error: null });
        try {
          await Promise.all([
            get().fetchWorkspaces(),
            get().fetchUsers(),
            get().loadSettings(),
            get().fetchSessions(),
            get().fetchCustomers()
          ]);
        } catch (err) {
          set({ error: 'Initialization failed' });
        } finally {
          set({ loading: false });
        }
      },

      // Reset all state
      reset: () => set({
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
        error: null
      }),

      // General state helpers
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error })
    })),
    {
      name: 'supreme-storage', // unique name
      partialize: (state) => ({
        // Persist only essential state
        theme: state.theme,
        activeWorkspace: state.activeWorkspace,
        settings: state.settings,
        isAuthenticated: state.isAuthenticated,
        user: state.user
      })
    }
  )
);

export default useSupremeStore;
