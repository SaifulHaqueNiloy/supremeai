// বাংলা মন্তব্য: ইউজারের Action-Dock পার্সোনালাইজেশন — কোন ইন্টিগ্রেশন দেখাবে, সাইডবার কোল্যাপসড কিনা, সবকিছু localStorage-এ persist হয়
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export type IntegrationId = 'github' | 'slack' | 'notion';

export interface IntegrationMeta {
  id: IntegrationId;
  label: string;
  // বাংলা মন্তব্য: lucide-react আইকন নামের রেফারেন্স মাত্র — JSX এখানে রাখা হয়নি যাতে এই ফাইলটি .tsx নির্ভর না হয়
  icon: 'Github' | 'Slack' | 'FileText';
  // বাংলা মন্তব্য: backend MorphicOrchestrator._get_dag_for_intent() এ 'sync_to_<id>' আসলেই wire করা আছে কিনা
  dagSupported: boolean;
}

export const INTEGRATION_REGISTRY: IntegrationMeta[] = [
  { id: 'slack', label: 'Slack', icon: 'Slack', dagSupported: true },
  { id: 'notion', label: 'Notion', icon: 'FileText', dagSupported: true },
  // বাংলা মন্তব্য: backend DAG-তে wire করা হচ্ছে — তাই এখন এটি true হতে পারে, তবে ডিফল্টে অফ
  { id: 'github', label: 'GitHub', icon: 'Github', dagSupported: true },
];

export type SidebarTab = 'sessions' | 'vault' | 'integrations';

interface WorkspaceSettingsState {
  enabledIntegrations: Record<IntegrationId, boolean>;
  toggleIntegration: (id: IntegrationId) => void;

  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;

  activeSidebarTab: SidebarTab;
  setActiveSidebarTab: (tab: SidebarTab) => void;
}

const DEFAULT_ENABLED: Record<IntegrationId, boolean> = {
  slack: true,
  notion: true,
  github: false,
};

export const useWorkspaceSettings = create<WorkspaceSettingsState>()(
  persist(
    (set) => ({
      enabledIntegrations: DEFAULT_ENABLED,
      toggleIntegration: (id) =>
        set((state) => ({
          enabledIntegrations: {
            ...state.enabledIntegrations,
            [id]: !state.enabledIntegrations[id],
          },
        })),

      isSidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),

      activeSidebarTab: 'sessions',
      setActiveSidebarTab: (tab) => set({ activeSidebarTab: tab }),
    }),
    {
      name: 'supremeai-workspace-settings',
      storage: createJSONStorage(() => localStorage),
    }
  )
);

// বাংলা মন্তব্য: Action-Dock শুধু এই ফিল্টার করা লিস্ট রেন্ডার করবে — hardcode করা তালিকা নয়
export function useEnabledIntegrations(): IntegrationMeta[] {
  const enabled = useWorkspaceSettings((s) => s.enabledIntegrations);
  return INTEGRATION_REGISTRY.filter((i) => enabled[i.id]);
}
