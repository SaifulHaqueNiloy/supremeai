import { useLocation, Link } from 'react-router-dom';
import { DashboardLayout } from './DashboardLayout';
import { useWorkspaceSettings, useEnabledIntegrations } from '../../hooks/useWorkspaceSettings';
import { useDynamicDock } from '../../hooks/useDynamicDock';
import { DndContext } from '@dnd-kit/core';
import { AnimatePresence } from 'framer-motion';
import { LivingActionDock } from '../dashboard/LivingActionDock';
import { HITLModal } from '../dashboard/HITLModal';
import { 
  Home, 
  MessageSquare, 
  FolderOpen, 
  Cpu, 
  Activity,
  Box,
  Plug,
  ShoppingBag,
  Zap,
  BarChart3,
  CreditCard,
  Settings
} from 'lucide-react';

interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  path: string;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Workspace',
    items: [
      { id: 'home', label: 'Home', icon: Home, path: '/workspace' },
      { id: 'ai-studio', label: 'AI Studio', icon: MessageSquare, path: '/workspace/live' },
      { id: 'projects', label: 'Projects', icon: FolderOpen, path: '/projects' },
      { id: 'agents', label: 'Agents', icon: Cpu, path: '/workspace/agent' },
      { id: 'activity', label: 'Activity', icon: Activity, path: '/activity' },
    ]
  },
  {
    label: 'Discover',
    items: [
      { id: 'skills', label: 'Skills', icon: Box, path: '/skills-catalog' },
      { id: 'integrations', label: 'Integrations', icon: Plug, path: '/integrations' },
      { id: 'marketplace', label: 'Marketplace', icon: ShoppingBag, path: '/marketplace' },
    ]
  },
  {
    label: 'Automation',
    items: [
      { id: 'runs', label: 'Runs', icon: Zap, path: '/runs' },
    ]
  },
  {
    label: 'Insights',
    items: [
      { id: 'usage', label: 'Usage', icon: BarChart3, path: '/usage' },
      { id: 'billing', label: 'Billing', icon: CreditCard, path: '/billing' },
    ]
  },
  {
    label: 'Settings',
    items: [
      { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
    ]
  }
];

export function UserSidebar() {
  const location = useLocation();
  const isSidebarCollapsed = useWorkspaceSettings(s => s.isSidebarCollapsed);

  return (
    <div className="flex flex-col h-full py-6 bg-surface-1 overflow-y-auto w-full">
      <div className="px-6 mb-6 flex items-center gap-2">
        <div className="w-6 h-6 rounded-md bg-accent-primary flex items-center justify-center shadow-[0_0_12px_rgba(168,85,247,0.4)]">
          <span className="text-black font-black text-xs">S</span>
        </div>
        {!isSidebarCollapsed && (
          <span className="font-sans font-bold tracking-wider text-text">
            Supreme<span className="text-accent-primary">AI</span>
          </span>
        )}
      </div>

      <div className="flex-1 px-3 space-y-6">
        {NAV_GROUPS.map((group, idx) => (
          <div key={idx} className="space-y-1">
            {!isSidebarCollapsed && (
              <div className="px-3 mb-2 text-[10px] font-bold text-muted uppercase tracking-widest">
                {group.label}
              </div>
            )}
            {group.items.map(item => {
              const isActive = location.pathname === item.path || (item.path !== '/workspace' && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.id}
                  to={item.path}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive 
                      ? 'surface-3 text-accent-primary border-l-2 border-accent-primary' 
                      : 'text-secondary hover:surface-2 hover:text-text'
                  }`}
                  title={isSidebarCollapsed ? item.label : undefined}
                >
                  <item.icon size={18} className={isActive ? 'text-accent-primary' : 'text-secondary'} />
                  {!isSidebarCollapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

export function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const isSidebarCollapsed = useWorkspaceSettings(s => s.isSidebarCollapsed);
  const enabledIntegrations = useEnabledIntegrations();
  
  const { nodeStatus, handleDragEnd, pendingAction, confirmAction, cancelAction } = useDynamicDock({
    resolveContent: (id) => ({ content: id }),
    unsupportedPlatforms: [],
  });
  
  return (
    <DndContext onDragEnd={handleDragEnd}>
      <HITLModal pendingAction={pendingAction} onConfirm={confirmAction} onCancel={cancelAction} />
      <DashboardLayout sidebar={<UserSidebar />} isSidebarCollapsed={isSidebarCollapsed}>
        <div className="flex-1 w-full h-full relative overflow-hidden flex flex-col min-w-0 pb-20">
          <div className="flex-1 overflow-y-auto">
            {children}
          </div>
          <div className="absolute bottom-0 left-0 right-0 z-50 pointer-events-none">
            <AnimatePresence>
              {enabledIntegrations.length > 0 && (
                <div className="pointer-events-auto">
                  <LivingActionDock enabledIntegrations={enabledIntegrations} nodeStatus={nodeStatus} />
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </DashboardLayout>
    </DndContext>
  );
}
