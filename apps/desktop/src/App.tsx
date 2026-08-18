import React, { useState } from 'react';
import { Sparkles, Layers, Cpu } from 'lucide-react';
import { DashboardShell, SupremeHeader } from '@supremeai/ui-components';
import { FloatingAssistantBar } from './components/FloatingAssistantBar';
import { MultiWorkspaceCanvas } from './components/MultiWorkspaceCanvas';
import { LocalLlmManager } from './components/LocalLlmManager';
import { BackendStatus } from './components/BackendStatus';

// ═══════════════════════════════════════════════════════════════
// SupremeAI 2.0 — Native Desktop Studio App ("AETHEL Studio")
// বাংলা মন্তব্য: সুপ্রিমএআই ডেক্সটপ স্টুডিও অ্যাপ মূল ইন্টারফেস
// (M4.1: shared DashboardShell + SupremeHeader reuse from @supremeai/ui-components)
// ═══════════════════════════════════════════════════════════════

export default function App() {
  const [showFloatingBar, setShowFloatingBar] = useState(false);

  return (
    <DashboardShell isServerOnline={true}>
      <div className="flex flex-col h-full">
        {/* Top Header & Brand Bar */}
        <header className="h-14 bg-[#080b14]/80 backdrop-blur-md border-b border-white/10 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#00f3ff] to-[#bc13fe] p-[2px] shadow-[0_0_15px_rgba(0,243,255,0.4)]">
              <div className="w-full h-full bg-[#030611] rounded-[10px] flex items-center justify-center">
                <Sparkles size={16} className="text-[#00f3ff]" />
              </div>
            </div>
            <div>
              <h1 className="text-sm font-mono font-bold uppercase tracking-wider text-white flex items-center gap-2">
                SupremeAI Studio <span className="text-[10px] text-[#00f3ff] bg-[#00f3ff]/10 px-2 py-0.5 rounded border border-[#00f3ff]/30">v6.0 Native</span>
              </h1>
            </div>
          </div>

          {/* Global Action Trigger Button */}
          <div className="flex items-center gap-3">
            <BackendStatus />
            <button
              onClick={() => setShowFloatingBar(!showFloatingBar)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#00f3ff]/10 text-[#00f3ff] border border-[#00f3ff]/30 hover:bg-[#00f3ff]/20 text-xs font-mono font-bold transition-all shadow-[0_0_10px_rgba(0,243,255,0.2)]"
            >
              <Sparkles size={14} />
              <span>Floating Assistant (Alt + Space)</span>
            </button>
          </div>
        </header>

        {/* Main Workspace Body */}
        <div className="flex-1 p-6 flex flex-col gap-6 overflow-y-auto">
          <SupremeHeader subtitle="Native desktop thin client — wired to the live SupremeAI backend">
            Studio Workspace
          </SupremeHeader>

          {/* Fleet Canvas Module */}
          <MultiWorkspaceCanvas />

          {/* Local LLM Core Manager */}
          <LocalLlmManager />
        </div>
      </div>

      {showFloatingBar && (
        <FloatingAssistantBar onClose={() => setShowFloatingBar(false)} />
      )}
    </DashboardShell>
  );
}
