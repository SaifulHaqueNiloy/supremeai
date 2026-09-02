// SupremeAI — WorkspaceLayout (single-frontend migration, roadmap Phase 3)
// বাংলা মন্তব্য: User context এখন UnifiedAppShell-এর ভেতরে রেন্ডার হয়। শুধুমাত্র
// user-specific business অংশ (DnD dock, HITL modal) এখানে থাকে — shell/header/nav
// infra unified shell থেকে আসে। পুরোনো NAV_GROUPS + UserSidebar navigationRegistry.ts-
// তে সরানো হয়েছে (একক nav registry; এখানে দ্বিতীয় definition নেই)।

import { UnifiedAppShell } from '../shell/UnifiedAppShell';
import { useEnabledIntegrations } from '../../hooks/useWorkspaceSettings';
import { useDynamicDock } from '../../hooks/useDynamicDock';
import { DndContext } from '@dnd-kit/core';
import { AnimatePresence } from 'framer-motion';
import { LivingActionDock } from '../dashboard/LivingActionDock';
import { HITLModal } from '../dashboard/HITLModal';

export function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const enabledIntegrations = useEnabledIntegrations();

  const { nodeStatus, handleDragEnd, pendingAction, confirmAction, cancelAction } = useDynamicDock({
    resolveContent: (id) => ({ content: id }),
    unsupportedPlatforms: [],
  });

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <HITLModal pendingAction={pendingAction} onConfirm={confirmAction} onCancel={cancelAction} />
      <UnifiedAppShell context="user">
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
      </UnifiedAppShell>
    </DndContext>
  );
}
