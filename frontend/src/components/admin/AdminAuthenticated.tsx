import React, { useEffect, useState } from 'react';
import type { AdminSubTab, GcpHealth, CloudStats, Skill, Checkpoint, ChatMessage, AdminUser, HealthMap } from '../../types';
import { SubTabContent } from './AdminSubTabContent';
import { AdminTopNav } from './AdminTopNav';
import {
  Search,
  LayoutDashboard,
  GitMerge,
  Server,
  BarChart3,
  Users,
  Settings,
  Terminal,
  Shield,
  BrainCircuit,
  HardDrive,
  Bell,
  Globe
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

export function AuthenticatedView(props: AuthenticatedViewProps) {
  const { adminSubTab, setAdminSubTab, handleAdminLogout } = props;
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLeftSidebarCollapsed, setIsLeftSidebarCollapsed] = useState(false);

  // Cmd+K to open Command Palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsPaletteOpen(prev => !prev);
      }
      if (e.key === 'Escape' && isPaletteOpen) {
        setIsPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPaletteOpen]);

  const sidebarItems = [
    { id: 'dashboard', label: 'DASHBOARD', icon: <LayoutDashboard size={16} /> },
    { id: 'browser-studio', label: 'BROWSER STUDIO', icon: <Globe size={16} /> },
    { id: 'alerts', label: 'SYSTEM ALERTS', icon: <Bell size={16} /> },
    { id: 'model-router', label: 'AI CORE', icon: <BrainCircuit size={16} /> },
    { id: 'skills', label: 'SKILLS & AGENTS', icon: <Users size={16} /> },
    { id: 'memory', label: 'MEMORY', icon: <HardDrive size={16} /> },
    { id: 'cloud', label: 'INFRASTRUCTURE', icon: <Server size={16} /> },
    { id: 'cicd', label: 'DEPLOYMENTS', icon: <GitMerge size={16} /> },
    { id: 'observability', label: 'OBSERVABILITY', icon: <BarChart3 size={16} /> },
    { id: 'threats', label: 'SECURITY', icon: <Shield size={16} /> },
    { id: 'config', label: 'SETTINGS', icon: <Settings size={16} /> },
    { id: 'interactive-chat', label: 'TERMINAL', icon: <Terminal size={16} /> },
  ];

  const navigationOptions = [
    { id: 'dashboard', label: 'Dashboard Overview' },
    { id: 'browser-studio', label: '🌐 AI Browser Automation Studio' },
    { id: 'alerts', label: 'System Alerts & Diagnostics' },
    { id: 'interactive-chat', label: 'Interactive Chat (Browser & Terminal)' },
    { id: 'command-center', label: 'SupremeAI Nexus (Canvas)' },
    { id: 'logs', label: 'Real-time Logs' },
    { id: 'costs', label: 'Cost Auditor' },
    { id: 'health', label: 'Health Map' },
    { id: 'users', label: 'User Manager / Agents' },
    { id: 'config', label: 'Config Editor' },
    { id: 'model-router', label: 'Model Router' },
    { id: 'skills', label: 'Skill Marketplace' },
    { id: 'memory', label: 'Memory Browser' },
    { id: 'cloud', label: 'Cloud Orchestrator' },
    { id: 'observability', label: 'Observability' },
    { id: 'threats', label: 'Threat Detection' },
    { id: 'rules', label: 'Rules Builder' },
    { id: 'cicd', label: 'CI/CD Pipelines' },
    { id: 'github', label: 'GitHub Integration' },
    { id: 'backups', label: 'Backup & Restore' },
    { id: 'rate-limits', label: 'Rate Limits' },
    { id: 'security-dashboard', label: '🧠 Security & Memory Dashboard' }
  ];

  const filteredOptions = navigationOptions.filter(opt =>
    opt.label.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* ১. টপ নেভিগেশন বার */}
      <AdminTopNav onLogout={handleAdminLogout} />

      {/* নিচের অংশ: সাইডবার + মূল কন্টেন্ট */}
      <div className="flex-1 flex overflow-hidden relative">

        {/* ২. বাম পাশের নেভিগেশন সাইডবার (Hide/Unhide Middle Button সহ) */}
        <aside className={`relative ${isLeftSidebarCollapsed ? 'w-16' : 'w-56'} transition-all duration-300 bg-[#040814]/55 backdrop-blur-xl border-r border-white/5 flex flex-col justify-between py-6 font-sans text-slate-400 select-none z-20`}>
          
          {/* Middle Toggle Button for Left Sidebar */}
          <button
            onClick={() => setIsLeftSidebarCollapsed(!isLeftSidebarCollapsed)}
            title={isLeftSidebarCollapsed ? "Expand Left Sidebar" : "Collapse Left Sidebar"}
            className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-10 bg-[#091124] hover:bg-[#00f3ff] text-slate-400 hover:text-black border border-[#00f3ff]/30 rounded-r-md flex items-center justify-center shadow-[0_0_10px_rgba(0,243,255,0.2)] transition-all z-30 group cursor-pointer"
          >
            {isLeftSidebarCollapsed ? (
              <span className="text-xs group-hover:scale-125 transition-transform">▶</span>
            ) : (
              <span className="text-xs group-hover:scale-125 transition-transform">◀</span>
            )}
          </button>

          <div className="space-y-1 px-2">
            {sidebarItems.map(item => {
              const isActive = adminSubTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setAdminSubTab(item.id as AdminSubTab)}
                  title={isLeftSidebarCollapsed ? item.label : undefined}
                  className={`w-full flex items-center ${isLeftSidebarCollapsed ? 'justify-center px-0' : 'gap-3 px-4'} py-3 rounded-lg text-xs font-semibold tracking-wider transition-all duration-300 ${isActive
                      ? 'bg-[#00f3ff]/10 text-[#00f3ff] border-l-2 border-[#00f3ff] shadow-[inset_0_0_12px_rgba(0,243,255,0.05)]'
                      : 'hover:bg-slate-900/50 hover:text-slate-200'
                    }`}
                >
                  <span className={isActive ? 'text-[#00f3ff]' : 'text-slate-400'}>
                    {item.icon}
                  </span>
                  {!isLeftSidebarCollapsed && <span>{item.label}</span>}
                </button>
              );
            })}
          </div>

          {/* অতিরিক্ত অ্যাডমিন টুলস */}
          <div className={`${isLeftSidebarCollapsed ? 'px-2' : 'px-6'} border-t border-slate-900 pt-4`}>
            <button
              onClick={() => setAdminSubTab('command-center')}
              title={isLeftSidebarCollapsed ? "Core Canvas" : undefined}
              className={`w-full flex items-center justify-center gap-2 ${isLeftSidebarCollapsed ? 'px-1' : 'px-3'} py-2 rounded border border-[#00f3ff]/30 text-[#00f3ff] hover:bg-[#00f3ff]/10 text-xs font-mono font-bold tracking-widest uppercase transition-all duration-300 ${adminSubTab === 'command-center' ? 'bg-[#00f3ff]/20' : ''
                }`}
            >
              <Terminal size={14} />
              {!isLeftSidebarCollapsed && <span>Core Canvas</span>}
            </button>
            {!isLeftSidebarCollapsed && (
              <div className="text-[9px] text-slate-600 text-center mt-3 font-mono">
                CTRL+K for command menu
              </div>
            )}
          </div>
        </aside>

        {/* ৩. মূল কন্টেন্ট প্যানেল */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <SubTabContent {...props} />
        </main>
      </div>

      {/* ৪. কমান্ড প্যালেট ওভারলে (Cmd+K) */}
      {isPaletteOpen && (
        <div className="absolute inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-[#050917] border border-[#00f3ff]/30 rounded-xl shadow-[0_0_40px_rgba(0,243,255,0.15)] flex flex-col overflow-hidden">
            <div className="flex items-center gap-3 px-4 py-3 border-b border-[#00f3ff]/20">
              <Search className="text-[#00f3ff] w-5 h-5" />
              <input
                autoFocus
                type="text"
                placeholder="Navigate to... (e.g. Browser Studio)"
                className="flex-1 bg-transparent border-none outline-none text-white font-mono placeholder:text-slate-400"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <span className="text-xs text-slate-400 font-mono">ESC to close</span>
            </div>
            <div className="max-h-[60vh] overflow-y-auto p-2">
              {filteredOptions.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => {
                    setAdminSubTab(opt.id as AdminSubTab);
                    setIsPaletteOpen(false);
                    setSearchQuery('');
                  }}
                  className="w-full text-left px-3 py-2.5 rounded-lg text-sm text-slate-300 hover:bg-[#00f3ff]/10 hover:text-[#00f3ff] transition-all font-mono flex items-center justify-between group"
                >
                  <span>{opt.label}</span>
                  <span className="text-xs text-slate-600 group-hover:text-[#00f3ff]/60">Jump &rarr;</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
