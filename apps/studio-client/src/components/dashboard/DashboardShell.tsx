// বাংলা মন্তব্য: Devin-স্টাইল ড্যাশবোর্ড শেল — "Living Workspace" রিফ্যাক্টর
// হ্যাশ-ভিত্তিক রাউটিং অপরিবর্তিত রাখা হয়েছে (কোনো নতুন রুট তৈরি হয়নি, শুধু লেআউট ও মোশন যোগ হয়েছে)।
// নতুন যোগ হয়েছে: (1) ডান পাশে সবসময়-দৃশ্যমান LiveSimulator, (2) নিচে ড্র্যাগেবল ActionDock,
// (3) Sessions/Vault/Settings-এর জন্য একটি কোলাপসিবল SidebarSettings হাব।
import { type ReactNode, useMemo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  LayoutList,
  Boxes,
  BookOpen,
  KeyRound,
  BarChart3,
  Settings,
  Vault,
  ListChecks,
  Table2,
  Cpu,
  Shield,
  Wifi,
  WifiOff,
  Activity,
} from 'lucide-react';
import { useHashRoute, type DashboardRoute } from './useHashRoute';
import { SessionsPage } from './SessionsPage';
import { SessionDetailPage } from './SessionDetailPage';
import { KnowledgePage } from './KnowledgePage';
import { SecretsPage } from './SecretsPage';
import { UsagePage } from './UsagePage';
import { SettingsPage } from './SettingsPage';
import { VaultPage } from './VaultPage';
import { AutomationQueuePage } from './AutomationQueuePage';
import { SiteActionsPage } from './SiteActionsPage';
import { LlmGatewayPage } from './LlmGatewayPage';
import { LiveSujonBackground } from '../LiveSujonBackground';
import { setSujonState, type SujonState } from '../sujon-utils';
import { MockSwarmProvider } from '../../providers/MockSwarmProvider';
import { SwarmHealthDashboard } from '../swarm/SwarmHealthDashboard';
import { LiveSimulator } from './LiveSimulator';
import { ActionDock } from './ActionDock';
import { SidebarSettings } from './SidebarSettings';

interface NavItem {
  id: DashboardRoute;
  label: string;
  icon: ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'sessions', label: 'Sessions', icon: <LayoutList size={15} /> },
  { id: 'workspace', label: 'Workspace', icon: <Boxes size={15} /> },
  { id: 'vault', label: 'Auth Vault', icon: <Vault size={15} /> },
  { id: 'automation', label: 'Automation', icon: <ListChecks size={15} /> },
  { id: 'knowledge', label: 'Knowledge', icon: <BookOpen size={15} /> },
  { id: 'secrets', label: 'Secrets', icon: <KeyRound size={15} /> },
  { id: 'usage', label: 'Usage', icon: <BarChart3 size={15} /> },
  { id: 'settings', label: 'Settings', icon: <Settings size={15} /> },
];

// বাংলা মন্তব্য: সুপার-অ্যাডমিন কন্ট্রোল লেয়ার — সাইট অ্যাকশন রেজিস্ট্রি ও LLM গেটওয়ে
const ADMIN_NAV_ITEMS: NavItem[] = [
  { id: 'site-actions', label: 'Site Actions', icon: <Table2 size={15} /> },
  { id: 'llm-gateway', label: 'LLM Gateway', icon: <Cpu size={15} /> },
  { id: 'swarm-health', label: 'Swarm Health', icon: <Activity size={15} /> },
  { id: 'admin', label: 'Admin Console', icon: <Shield size={15} /> },
];

interface DashboardShellProps {
  theme: 'dark' | 'light';
  toggleTheme: () => void;
  isServerOnline: boolean;
  // বাংলা মন্তব্য: লিগ্যাসি SupremeAI ওয়ার্কস্পেস (চ্যাট, প্রিসেট, ব্রাউজার প্রিভিউ ইত্যাদি) Workspace ট্যাবে রেন্ডার হয়
  workspace: ReactNode;
}

export function DashboardShell(props: DashboardShellProps) {
  const [route, navigate] = useHashRoute();

  // বাংলা মন্তব্য: রাউটের ভিত্তিতে Sujon স্টেট সেট করা — টাস্ক এক্সিকিউশন আরম্ভ হলে processing, সেশন শেষে idle
  useMemo(() => {
    const sujonState: Record<DashboardRoute, SujonState> = {
      sessions: 'idle',
      session: 'processing',
      workspace: 'idle',
      vault: 'idle',
      automation: 'processing',
      'site-actions': 'idle',
      'llm-gateway': 'idle',
      'swarm-health': 'idle',
      knowledge: 'idle',
      secrets: 'idle',
      usage: 'idle',
      settings: 'idle',
      admin: 'idle',
      guardrails: 'idle',
      'healing-log': 'idle',
    };
    setSujonState(sujonState[route.page] || 'idle');
  }, [route.page]);

  const handleOpenSession = (id: string) => {
    navigate('session', id);
  };

  // বাংলা মন্তব্য: হ্যাশ রাউটের ভিত্তিতে সংশ্লিষ্ট পেজ রেন্ডার করা হয় — লজিক অপরিবর্তিত
  const renderPage = () => {
    switch (route.page) {
      case 'session':
        return <SessionDetailPage sessionId={route.param || ''} />;
      case 'workspace':
        return <>{props.workspace}</>;
      case 'vault':
        return <VaultPage />;
      case 'automation':
        return <AutomationQueuePage />;
      case 'site-actions':
        return <SiteActionsPage />;
      case 'llm-gateway':
        return <LlmGatewayPage />;
      case 'swarm-health':
        return <SwarmHealthDashboard />;
      case 'knowledge':
        return <KnowledgePage />;
      case 'secrets':
        return <SecretsPage />;
      case 'usage':
        return <UsagePage />;
      case 'settings':
        return <SettingsPage />;
      case 'admin':
        return <div className="p-6 text-text-secondary text-xs">Admin console (use /admin subdomain)</div>;
      case 'sessions':
      default:
        return <SessionsPage onOpenSession={handleOpenSession} />;
    }
  };

  const navItems = [...NAV_ITEMS, ...ADMIN_NAV_ITEMS];

  return (
    <MockSwarmProvider>
      <div className="relative flex h-screen overflow-hidden bg-[var(--supremeai-color-bg-void-light)] text-foreground dark:bg-[var(--supremeai-color-bg-void-dark)]">
        {/* বাংলা মন্তব্য: Sujon অ্যাম্বিয়েন্ট ব্যাকগ্রাউন্ড — matte ash canvas এর উপর হালকা light-reactive লেয়ার */}
        <LiveSujonBackground />

        {/* প্রাইমারি নেভিগেশন — অপরিবর্তিত হ্যাশ-রাউট নেভ */}
        <aside
          data-testid="dashboard-sidebar"
          className="relative z-10 flex w-64 shrink-0 flex-col border-r border-[var(--supremeai-color-border-accent-light)] bg-[var(--supremeai-color-bg-elevated-light)] transition-colors dark:border-[var(--supremeai-color-border-accent-dark)] dark:bg-[var(--supremeai-color-bg-elevated-dark)]"
        >
          <div className="flex items-center gap-2 border-b border-[var(--supremeai-color-border-accent-light)] px-6 py-4 dark:border-[var(--supremeai-color-border-accent-dark)]">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--supremeai-color-brand-500)]">
              <span className="text-xs font-bold text-white">SAI</span>
            </div>
            <span className="text-xl font-bold tracking-tight">SupremeAI</span>
          </div>

          <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-4">
            {navItems.map((item) => {
              const isActive = route.page === item.id;
              return (
                <button
                  key={item.id}
                  data-testid={`nav-${item.id}`}
                  onClick={() => navigate(item.id)}
                  className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-[var(--supremeai-color-brand-50)] text-[var(--supremeai-color-brand-600)] dark:bg-[var(--supremeai-color-brand-500)]/10 dark:text-[var(--supremeai-color-brand-500)]'
                      : 'text-[var(--supremeai-color-neutral-500)] hover:bg-[var(--supremeai-color-neutral-100)] hover:text-foreground dark:hover:bg-[var(--supremeai-color-neutral-900)]'
                  }`}
                >
                  {item.icon}
                  {item.label}
                </button>
              );
            })}
          </nav>

          <div className="space-y-3 border-t border-[var(--supremeai-color-border-accent-light)] px-4 py-4 dark:border-[var(--supremeai-color-border-accent-dark)]">
            <div data-testid="sidebar-server-status" className="flex items-center gap-2 text-xs">
              {props.isServerOnline ? (
                <>
                  <Wifi size={14} className="text-[var(--supremeai-color-brand-success-light)] dark:text-[var(--supremeai-color-brand-success-dark)]" />
                  <span className="font-medium text-[var(--supremeai-color-brand-success-light)] dark:text-[var(--supremeai-color-brand-success-dark)]">
                    Online
                  </span>
                </>
              ) : (
                <>
                  <WifiOff size={14} className="text-[var(--supremeai-color-brand-danger-light)] dark:text-[var(--supremeai-color-brand-danger-dark)]" />
                  <span className="font-medium text-[var(--supremeai-color-brand-danger-light)] dark:text-[var(--supremeai-color-brand-danger-dark)]">
                    Offline
                  </span>
                </>
              )}
            </div>
            <button
              onClick={props.toggleTheme}
              className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-[var(--supremeai-color-neutral-500)] transition-colors hover:bg-[var(--supremeai-color-neutral-100)] hover:text-foreground dark:hover:bg-[var(--supremeai-color-neutral-900)]"
            >
              <Shield size={14} />
              {props.theme === 'dark' ? 'Dark' : 'Light'} mode
            </button>
          </div>
        </aside>

        {/* Sessions/Vault/Settings কুইক-অ্যাক্সেস হাব — কোলাপসিবল, বিদ্যমান পেজ কম্পোনেন্ট পুনর্ব্যবহার করে */}
        <SidebarSettings onOpenSession={handleOpenSession} navigate={navigate} />

        {/* মূল কন্টেন্ট এলাকা — Control Hub (কেন্দ্র) + Live Simulator (ডান, সবসময় দৃশ্যমান) */}
        <div className="relative z-10 flex min-w-0 flex-1 flex-col overflow-hidden">
          <div className="flex min-h-0 flex-1">
            <main className="min-w-0 flex-1 overflow-y-auto bg-[var(--supremeai-color-bg-void-light)] dark:bg-[var(--supremeai-color-bg-void-dark)]">
              <AnimatePresence mode="wait">
                <motion.div
                  key={route.page + (route.param ?? '')}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.22, ease: 'easeOut' }}
                  className="h-full"
                >
                  {renderPage()}
                </motion.div>
              </AnimatePresence>
            </main>

            {/* বাংলা মন্তব্য: "Magic Window" — মেন্ডেটরি, ফিক্সড-সাইজ, সব রাউটে সবসময় দৃশ্যমান */}
            <LiveSimulator />
          </div>

          {/* Bottom Action-Dock — ড্র্যাগ-অ্যান্ড-ড্রপ, ইউজার-কনফিগারযোগ্য */}
          <ActionDock />
        </div>
      </div>
    </MockSwarmProvider>
  );
}
