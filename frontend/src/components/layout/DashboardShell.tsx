// apps/studio-client/src/components/layout/DashboardShell.tsx
// Living Workspace Shell - Fast, Fluid, and Framer Motion driven
// বাংলা মন্তব্য: ফাস্ট, ফ্লুইড এবং Framer Motion দ্বারা চালিত ড্যাশবোর্ড শেল। এটি অ্যাকশন-ডক এবং লাইভ সিমুলেটরকে একসাথে যুক্ত করে।

import React, { Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSupremeStore } from '../../store/useSupremeStore';
import { NavRail } from './NavRail';
import { CommandBar } from './CommandBar';
import { WorkspaceSkeleton } from '../common/Skeleton';

// Lazy load heavy components for zero-idle cost initial render
const DynamicActionDock = React.lazy(() => import('../dock/DynamicActionDock'));
const LiveSimulator = React.lazy(() => import('../simulator/LiveSimulator'));
const ChatInterface = React.lazy(() => import('../chat/ChatInterface'));

export const DashboardShell: React.FC = () => {
  const { notifications, isSimulatorActive, removeNotification } = useSupremeStore();

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-900 text-white">

      {/* Left Navigation Rail */}
      <NavRail />

      {/* Universal Command Palette (Ctrl+K) */}
      <CommandBar />

      {/* Center: Primary Agent Chat Interface */}
      <main className="flex-grow relative flex flex-col transition-all duration-300">
        <Suspense fallback={<WorkspaceSkeleton />}>
          <ChatInterface />
        </Suspense>

        {/* Bottom: Dynamic Action-Dock (dnd-kit integrated inside) */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-3/4 max-w-3xl">
          <Suspense fallback={null}>
            <DynamicActionDock />
          </Suspense>
        </div>
      </main>

      {/* Right: Live Simulator Panel (Transformation Map) */}
      <AnimatePresence>
        {isSimulatorActive && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 400, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="h-full border-l border-slate-800 bg-slate-950 shadow-2xl overflow-y-auto"
          >
            <Suspense fallback={null}>
              <LiveSimulator />
            </Suspense>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Autonomous Notification Toasts */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
        <AnimatePresence>
          {notifications.map((notif) => (
            <motion.div
              key={notif.id}
              initial={{ opacity: 0, y: -20, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className={`p-4 rounded shadow-lg border-l-4 min-w-[300px] ${
                notif.type === 'error' ? 'bg-red-950 border-red-500 text-red-200' :
                notif.type === 'success' ? 'bg-emerald-950 border-emerald-500 text-emerald-200' :
                'bg-slate-800 border-blue-500 text-blue-200'
              }`}
              onClick={() => removeNotification(notif.id)}
            >
              <p className="text-sm">{notif.message}</p>
              {notif.correlationId && (
                <span className="text-[10px] opacity-50 mt-1 block font-mono">
                  Trace: {notif.correlationId}
                </span>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

    </div>
  );
};
