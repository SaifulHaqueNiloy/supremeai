import type { StateCreator } from 'zustand';
import { getApiBaseUrl } from '../../utils/api';
import type { SupremeStore } from '../useSupremeStore';
import type { Workspace, DockIntegration, Notification } from './types';

const DEFAULT_INTEGRATIONS: DockIntegration[] = [
  { id: 'github', icon: 'Github', label: 'GitHub', enabled: true },
  { id: 'slack', icon: 'MessagesSquare', label: 'Slack', enabled: true },
  { id: 'linear', icon: 'NotebookText', label: 'Linear', enabled: false },
  { id: 'jira', icon: 'HardDrive', label: 'Jira', enabled: false },
  { id: 'email', icon: 'Mail', label: 'Email', enabled: false },
  { id: 'facebook', icon: 'Facebook', label: 'Facebook', enabled: false },
];

export interface WorkspaceSlice {
  activeWorkspace: string | null;
  workspaces: Workspace[];
  activeIntegrations: string[];
  integrations: DockIntegration[];
  notifications: Notification[];
  isSimulatorActive: boolean;

  setActiveWorkspace: (workspaceId: string) => void;
  createWorkspace: (workspaceData: Partial<Workspace>) => Promise<void>;
  updateWorkspace: (workspaceId: string, data: Partial<Workspace>) => Promise<void>;
  deleteWorkspace: (workspaceId: string) => Promise<void>;
  fetchWorkspaces: () => Promise<void>;

  toggleIntegration: (toolId: string) => void;
  reorderIntegrations: (ids: string[]) => void;
  addNotification: (notif: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  setSimulatorState: (isActive: boolean) => void;
  logout: () => void;
}

export const createWorkspaceSlice: StateCreator<SupremeStore, [], [], WorkspaceSlice> = (set) => ({
  activeWorkspace: null,
  workspaces: [],
  activeIntegrations: ['github', 'slack'],
  integrations: DEFAULT_INTEGRATIONS,
  notifications: [],
  isSimulatorActive: false,

  setActiveWorkspace: (workspaceId) => set({ activeWorkspace: workspaceId }),

  createWorkspace: async (workspaceData) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${getApiBaseUrl()}/admin-api/workspaces`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workspaceData),
      });
      const newWorkspace = await response.json();
      set((state) => ({ workspaces: [...state.workspaces, newWorkspace] }));
    } catch {
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
        body: JSON.stringify(data),
      });
      const updatedWorkspace = await response.json();
      set((state) => ({
        workspaces: state.workspaces.map((ws) => (ws.id === workspaceId ? { ...ws, ...updatedWorkspace } : ws)),
      }));
    } catch {
      set({ error: 'Failed to update workspace' });
    } finally {
      set({ loading: false });
    }
  },
  deleteWorkspace: async (workspaceId) => {
    set({ loading: true, error: null });
    try {
      await fetch(`${getApiBaseUrl()}/admin-api/workspaces/${workspaceId}`, { method: 'DELETE' });
      set((state) => ({ workspaces: state.workspaces.filter((ws) => ws.id !== workspaceId) }));
    } catch {
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
    } catch {
      set({ error: 'Failed to fetch workspaces' });
    } finally {
      set({ loading: false });
    }
  },

  toggleIntegration: (toolId) =>
    set((state) => {
      const isActive = state.activeIntegrations.includes(toolId);
      return {
        activeIntegrations: isActive
          ? state.activeIntegrations.filter((id) => id !== toolId)
          : [...state.activeIntegrations, toolId],
        integrations: state.integrations.map((i) =>
          i.id === toolId ? { ...i, enabled: !i.enabled } : i,
        ),
      };
    }),

  reorderIntegrations: (ids) =>
    set((state) => {
      const newIntegrations = [...state.integrations].sort((a, b) => {
        const indexA = ids.indexOf(a.id);
        const indexB = ids.indexOf(b.id);
        if (indexA === -1 && indexB === -1) return 0;
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        return indexA - indexB;
      });
      return { integrations: newIntegrations };
    }),

  addNotification: (notif) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { ...notif, id: crypto.randomUUID() },
      ].slice(-5),
    })),

  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  setSimulatorState: (isActive) => set({ isSimulatorActive: isActive }),

  logout: () => {
    localStorage.removeItem('supreme_auth_token');
    localStorage.removeItem('adminToken');
    localStorage.removeItem('supreme_admin_jwt');
    set({ activeIntegrations: [], notifications: [], isSimulatorActive: false });
  },
});

export { DEFAULT_INTEGRATIONS };
