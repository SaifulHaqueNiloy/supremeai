import React, { useEffect } from 'react';
import type { AdminSubTab, GcpHealth, CloudStats, Skill, Checkpoint, ChatMessage, AdminUser, HealthMap } from '../../../types';
import { SubTabContent } from '../shared/AdminSubTabContent';
import { AdminTopNav } from '../shared/AdminTopNav';
import { DashboardLayout } from '../../layout/DashboardLayout';
import { ADMIN_SUBTAB_EVENT } from '../../../config/commandRegistry';
import {
  GitMerge,
  Users,
  Terminal,
  Shield,
  BrainCircuit,
  Network,
  Activity,
  ServerCog,
  FileCheck2,
  AlertTriangle,
  Zap,
  RefreshCcw,
  DollarSign,
  Search,
  Wrench
} from 'lucide-react';

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
  theme: 'dark' | 'light';
  toggleTheme: () => void;
}

/**
 * Supreme God Mode - Authenticated Layout (Redesigned)
 * This component implements the vision from the SUPREMEAI_GOD_CONTROL_CENTER_PLAN.md,
 * featuring a top navigation bar, a multi-module sidebar, and a main content panel.
 * It also integrates a command palette for quick navigation.
 *
 * বাংলা মন্তব্য: সুপ্রিম গড মোড অথেনটিকেটেড লেআউট (পুনঃডিজাইনকৃত)
 * এই কম্পোনেন্টটি SUPREMEAI_GOD_CONTROL_CENTER_PLAN.md-এর পরিকল্পনাকে বাস্তবায়ন করে।
 * এতে একটি টপ নেভিগেশন বার, একাধিক মডিউলসহ সাইডবার এবং মূল কন্টেন্ট প্যানেল রয়েছে।
 * দ্রুত নেভিগেশনের জন্য একটি কমান্ড প্যালেটও যুক্ত করা হয়েছে।
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

  // As per SUPREMEAI_GOD_CONTROL_CENTER_PLAN.md, the sidebar is module-driven.
  const sidebarItems = [
    { id: 'overview', label: 'OVERVIEW', icon: <Activity size={16} /> },
    { id: 'topology', label: 'TOPOLOGY', icon: <Network size={16} /> },
    { id: 'service-explorer', label: 'SERVICE EXPLORER', icon: <ServerCog size={16} /> },
    { id: 'agents-swarm', label: 'AGENTS / SWARM', icon: <BrainCircuit size={16} /> },
    { id: 'security', label: 'SECURITY', icon: <Shield size={16} /> },
    { id: 'audit', label: 'AUDIT', icon: <FileCheck2 size={16} /> },
    { id: 'incidents', label: 'INCIDENTS', icon: <AlertTriangle size={16} /> },
    { id: 'deployments', label: 'DEPLOYMENTS', icon: <GitMerge size={16} /> },
    { id: 'reliability', label: 'RELIABILITY', icon: <Zap size={16} /> },
    { id: 'recovery', label: 'RECOVERY', icon: <RefreshCcw size={16} /> },
    { id: 'tenants-rbac', label: 'TENANTS / RBAC', icon: <Users size={16} /> },
    { id: 'finops', label: 'FINOPS', icon: <DollarSign size={16} /> },
    { id: 'rca-intelligence', label: 'RCA / INTELLIGENCE', icon: <Search size={16} /> },
    { id: 'configuration', label: 'CONFIGURATION', icon: <Wrench size={16} /> },
  ];

  // বাংলা মন্তব্য: কমান্ড প্যালেট অপশন এখন src/config/commandRegistry.ts-এ (unified registry)।

  return (
    <DashboardLayout
      header={<AdminTopNav onLogout={handleAdminLogout} />}
      sidebar={
        <>
          <div className="space-y-1 px-3 mt-6">
            {sidebarItems.map(item => {
              const isActive = adminSubTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setAdminSubTab(item.id as AdminSubTab)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-xs font-semibold tracking-wider transition-all duration-300 ${isActive
                      ? 'surface-3 text-accent-primary border-l-2 border-accent-primary'
                      : 'hover:surface-2 hover:text-text'
                    }`}
                >
                  <span className={isActive ? 'text-accent-primary' : 'text-secondary'}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>

          <div className="px-6 border-t border-border pt-4 mb-6">
            <button
              onClick={() => setAdminSubTab('command-center')}
              className={`w-full flex items-center justify-center gap-2 px-3 py-2 rounded border border-accent-primary/30 text-accent-primary hover:surface-2 text-xs font-mono font-bold tracking-widest uppercase transition-all duration-300 ${adminSubTab === 'command-center' ? 'surface-3' : ''
                }`}
            >
              <Terminal size={14} />
              <span>Core Canvas</span>
            </button>
            <div className="text-[9px] text-muted text-center mt-3 font-mono">
              CTRL+K for command menu
            </div>
          </div>
        </>
      }
    >
      <SubTabContent {...props} />
    </DashboardLayout>
  );
}
