import React from 'react';
import { motion } from 'framer-motion';

export interface DashboardLayoutProps {
  header?: React.ReactNode;
  sidebar?: React.ReactNode;
  children: React.ReactNode;
  isSidebarCollapsed?: boolean;
}

const SIDEBAR_SPRING = { type: 'spring', stiffness: 320, damping: 32 } as const;

export function DashboardLayout({ header, sidebar, children, isSidebarCollapsed = false }: DashboardLayoutProps) {
  return (
    <div className="dashboard-live-shell surface-0 h-screen w-screen flex flex-col overflow-hidden text-text font-sans">
      <div className="dashboard-live-orb dashboard-live-orb-one" aria-hidden="true" />
      <div className="dashboard-live-orb dashboard-live-orb-two" aria-hidden="true" />
      {header && (
        <header className="surface-1 z-30 shrink-0">
          {header}
        </header>
      )}
      
      <div className="flex-1 flex overflow-hidden relative">
        {sidebar && (
          <motion.aside
            initial={false}
            animate={{ width: isSidebarCollapsed ? 64 : 256 }}
            transition={SIDEBAR_SPRING}
            className="surface-1 border-r border-border flex flex-col z-20 shrink-0 overflow-hidden"
          >
            {sidebar}
          </motion.aside>
        )}
        
        <main className="flex-1 min-w-0 overflow-hidden relative z-10 flex flex-col">
          {children}
        </main>
      </div>
    </div>
  );
}
