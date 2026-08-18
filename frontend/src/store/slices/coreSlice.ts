import type { StateCreator } from 'zustand';
import type { SupremeStore } from '../useSupremeStore';
import { apiClient } from '../../services/apiClient';
import { AppDefaults } from '../../config/constants';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface DeployGateInfo {
  status: 'LOCKED' | 'UNLOCKED';
  reason: string;
  updated_at?: string;
}

export interface CoreSlice {
  loading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  initialize: () => Promise<void>;
  reset: () => void;

  // System Config
  systemConfig: typeof AppDefaults;
  isConfigLoaded: boolean;
  setConfig: (config: Partial<typeof AppDefaults>) => void;

  // Server & Session
  isServerOnline: boolean;
  sessionId: string | null;
  currentIdempotencyKey: string | null;
  isOrchestrating: boolean;
  chatHistory: ChatMessage[];
  coreChatHistory: ChatMessage[];
  activeTaskType: string;
  executionError: string | null;
  streamLogs: string[];

  // Autonomous Gate
  deployGate: DeployGateInfo | null;
  isGateLoading: boolean;

  // Evolution Forge
  isForging: boolean;
  forgeFeedback: string | null;
  forgeSuccessCode: string | null;

  setServerStatus: (online: boolean) => void;
  initializeSession: (id: string) => void;
  generateIdempotencyKey: () => string;
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  addCoreMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  clearHistory: () => void;
  triggerOrchestration: (active: boolean, error?: string | null) => void;
  fetchGateStatus: () => Promise<void>;
  executeGateOverride: (targetStatus: string, reason: string, secret: string) => Promise<{ success: boolean; message: string }>;
  forgeNewSkill: (skillName: string, userDemand: string) => Promise<void>;
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

  systemConfig: AppDefaults,
  isConfigLoaded: false,
  setConfig: (config) =>
    set((state) => ({
      systemConfig: { ...state.systemConfig, ...config },
      isConfigLoaded: true,
    })),

  isServerOnline: false,
  sessionId: null,
  currentIdempotencyKey: null,
  isOrchestrating: false,
  chatHistory: [],
  coreChatHistory: [],
  activeTaskType: 'general',
  executionError: null,
  streamLogs: [],

  deployGate: null,
  isGateLoading: false,

  isForging: false,
  forgeFeedback: null,
  forgeSuccessCode: null,

  setServerStatus: (online) => set({ isServerOnline: online }),
  initializeSession: (id) => set({ sessionId: id }),
  generateIdempotencyKey: () => {
    const uniqueKey = crypto.randomUUID();
    set({ currentIdempotencyKey: uniqueKey });
    return uniqueKey;
  },
  addMessage: (message) =>
    set((state) => {
      const newMsg = { ...message, id: crypto.randomUUID(), timestamp: Date.now() };
      return {
        chatHistory: [...state.chatHistory, newMsg],
        coreChatHistory: [...state.coreChatHistory, newMsg],
      };
    }),
  addCoreMessage: (message) =>
    set((state) => {
      const newMsg = { ...message, id: crypto.randomUUID(), timestamp: Date.now() };
      return {
        chatHistory: [...state.chatHistory, newMsg],
        coreChatHistory: [...state.coreChatHistory, newMsg],
      };
    }),
  clearHistory: () => set({ chatHistory: [], coreChatHistory: [], executionError: null }),
  triggerOrchestration: (active, error = null) =>
    set({ isOrchestrating: active, executionError: error }),

  fetchGateStatus: async () => {
    const adminToken = localStorage.getItem('supreme_admin_jwt');
    if (!adminToken) {
      return;
    }
    set({ isGateLoading: true });
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data = await apiClient.get<any>('/api/admin/metrics/dashboard');
      set({
        deployGate: {
          status: data.status === 'HEALTHY' ? 'UNLOCKED' : 'LOCKED',
          reason: data.error || 'System operating within safe deployment thresholds.',
        },
      });
    } catch (err) {
      console.error('Failed to sync deploy gate telemetry:', err);
    } finally {
      set({ isGateLoading: false });
    }
  },

  executeGateOverride: async (targetStatus, reason, secret) => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data = await apiClient.post<any>('/api/admin/gate/override', {
        target_status: targetStatus,
        reason,
        admin_secret: secret,
      });
      if (data.success) {
        set({ deployGate: { status: data.forced_status, reason: `👑 Forced: ${reason}` } });
        return { success: true, message: data.message };
      }
      return { success: false, message: data.detail || 'Override verification rejected.' };
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      return { success: false, message: err.message || 'Network isolation error.' };
    }
  },

  forgeNewSkill: async (skillName, userDemand) => {
    set({
      isForging: true,
      forgeFeedback: '🧠 Self-Evolution Core is structuring your request...',
      forgeSuccessCode: null,
    });
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data = await apiClient.post<any>('/api/evolution/forge', {
        skill_name: skillName,
        user_demand: userDemand,
      });
      if (data.success) {
        set({
          isForging: false,
          forgeFeedback: `🏆 Success! Skill '${data.skill_name}' is fully deployed to Firestore.`,
          forgeSuccessCode: data.generated_code,
        });
      } else {
        set({
          isForging: false,
          forgeFeedback: `🚨 Evolution Blocked: ${data.detail || data.error || 'Sandbox Verification Failed.'}`,
        });
      }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      set({
        isForging: false,
        forgeFeedback: `❌ Infrastructure Error: ${err.message || 'Network Failure.'}`,
      });
    }
  },
});
