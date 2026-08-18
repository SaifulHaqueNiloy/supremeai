import type { StateCreator } from 'zustand';
import { getApiBaseUrl } from '../../utils/api';
import type { SupremeStore } from '../useSupremeStore';

export interface DashboardSlice {
  // Metric & activity state
  metrics: Record<string, unknown>;
  recentActivity: Record<string, unknown>[];
  quickActions: Record<string, unknown>[];
  setMetrics: (metrics: Record<string, unknown>) => void;
  setRecentActivity: (activity: Record<string, unknown>[]) => void;
  refreshMetrics: () => Promise<void>;

  // Dashboard modal & navigation state
  isDeploymentModalOpen: boolean;
  systemStatus: 'healthy' | 'degraded' | 'critical';
  activePanel: string | null;
  setDeploymentModal: (isOpen: boolean) => void;
  updateSystemStatus: (status: 'healthy' | 'degraded' | 'critical') => void;
  setActivePanel: (panel: string | null) => void;

  // Mode & interactive panels
  dashboardMode: 'simple' | 'advanced';
  chatTabTerminalOpen: boolean;
  chatTabBrowserOpen: boolean;
  toggleDashboardMode: () => void;
  toggleTerminal: () => void;
  toggleBrowser: () => void;
}

export const createDashboardSlice: StateCreator<SupremeStore, [], [], DashboardSlice> = (set) => ({
  metrics: {},
  recentActivity: [],
  quickActions: [],
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
      console.error('Failed to refresh metrics:', err);
      set({ error: 'Failed to refresh metrics' });
    } finally {
      set({ loading: false });
    }
  },

  isDeploymentModalOpen: false,
  systemStatus: 'healthy',
  activePanel: null,
  setDeploymentModal: (isOpen) => set({ isDeploymentModalOpen: isOpen }),
  updateSystemStatus: (status) => set({ systemStatus: status }),
  setActivePanel: (panel) => set({ activePanel: panel }),

  dashboardMode: 'simple',
  chatTabTerminalOpen: true,
  chatTabBrowserOpen: true,
  toggleDashboardMode: () => set((s) => ({ dashboardMode: s.dashboardMode === 'simple' ? 'advanced' : 'simple' })),
  toggleTerminal: () => set((s) => ({ chatTabTerminalOpen: !s.chatTabTerminalOpen })),
  toggleBrowser: () => set((s) => ({ chatTabBrowserOpen: !s.chatTabBrowserOpen })),
});
