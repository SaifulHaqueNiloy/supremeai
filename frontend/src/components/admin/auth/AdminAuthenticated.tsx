import React, { useEffect } from 'react';
import type { AdminSubTab, GcpHealth, CloudStats, Skill, Checkpoint, ChatMessage, AdminUser, HealthMap } from '../../../types';
import { SubTabContent } from '../shared/AdminSubTabContent';
import { UnifiedAppShell } from '../../shell/UnifiedAppShell';
import { ADMIN_SUBTAB_EVENT } from '../../../config/commandRegistry';

interface AuthenticatedViewProps {
  gcpHealth?: GcpHealth | null;
  cloudStats?: CloudStats | null;
  skillQuery: string;
  setSkillQuery: (val: string) => void;
  skills: Skill[];
  handleInstallSkill: (name: string) => void;
  checkpoints: Checkpoint[];
  handleDeleteCheckpoint: (taskId: string) => void;
  adminSubTab: AdminSubTab;
  setAdminSubTab: (tab: AdminSubTab) => void;
  handleTriggerDeploy: () => void;
  adminMessages: ChatMessage[];
  loading: boolean;
  adminInput: string;
  setAdminInput: (val: string) => void;
  handleSendAdmin: () => void;
  rulesJson: string;
  setRulesJson: (val: string) => void;
  saveStatus: string;
  handleSaveRules: () => void;
  liveLogs: string[];
  setLiveLogs: (logs: string[]) => void;
  costReport: string;
  healthMap: HealthMap;
  newUsername: string;
  setNewUsername: (val: string) => void;
  newUserRole: string;
  setNewUserRole: (val: string) => void;
  newUserPerms: string;
  setNewUserPerms: (val: string) => void;
  handleSaveUser?: () => void;
  adminUsers?: AdminUser[];
  envConfig?: Record<string, string>;
  setEnvConfig?: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  handleSaveConfig?: () => void;
  actionStatus: string;
  handleAdminLogout: () => void;
  /** বাংলা: আর ব্যবহৃত হয় না — theme এখন shared ThemeProvider মালিকানায় (নিচের নোট দেখুন)। */
  theme?: 'dark' | 'light';
  toggleTheme?: () => void;
}

/**
 * Supreme God Mode - Authenticated Layout (unified shell edition)
 *
 * বাংলা মন্তব্য (single-frontend migration, roadmap Phase 5): shell responsibility
 * UnifiedAppShell-এ উঠে গেছে — header (GlobalHeader), sidebar (RoleAwareNavRail,
 * NAVIGATION_REGISTRY থেকে generate) এবং collapse সব shared infra। এখানে শুধুমাত্র
 * admin business অংশ (SubTabContent modules) রাখা হয়েছে। AdminConsole-এর
 * business functionality অপরিবর্তিত।
 *
 * পুরোনো AdminTopNav + inline 14-item sidebar সরানো হয়েছে — একই আইটেমগুলো এখন
 * navigationRegistry-র 'admin' context থেকে আসে (kind: 'action', actionId = subtab id)।
 */
export function AuthenticatedView(props: AuthenticatedViewProps) {
  const { adminSubTab, setAdminSubTab, handleAdminLogout } = props;

  // বাংলা মন্তব্য: Palette এখন global CommandBar (unified registry) — admin subtab navigation
  // 'supremeai-admin-subtab' custom event-এর মাধ্যমে আসে। Double-palette conflict এড়াতে
  // এখানে আলাদা Ctrl+K handler রাখা হয়নি।
  useEffect(() => {
    const handleSubtabEvent = (e: Event) => {
      const tabId = (e as CustomEvent<string>).detail;
      setAdminSubTab(tabId as AdminSubTab);
    };
    window.addEventListener(ADMIN_SUBTAB_EVENT, handleSubtabEvent);
    return () => window.removeEventListener(ADMIN_SUBTAB_EVENT, handleSubtabEvent);
  }, [setAdminSubTab]);

  return (
    <UnifiedAppShell
      context="admin"
      activeActionId={adminSubTab}
      onAction={(actionId) => setAdminSubTab(actionId as AdminSubTab)}
      onLogout={handleAdminLogout}
    >
      <div className="flex-1 min-h-0 overflow-hidden">
        <SubTabContent {...props} />
      </div>
    </UnifiedAppShell>
  );
}
