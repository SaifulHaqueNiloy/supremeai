import type { StateCreator } from 'zustand';
import { getApiBaseUrl } from '../../utils/api';
import type { SupremeStore } from '../useSupremeStore';

export interface DashboardSlice {
  metrics: Record<string, unknown>;
  recentActivity: Record<string, unknown>[];
  quickActions: Record<string, unknown>[];
  setMetrics: (metrics: Record<string, unknown>) => void;
  setRecentActivity: (activity: Record<string, unknown>[]) => void;
  refreshMetrics: () => Promise<void>;
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
});
