import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bot, FolderOpen, Zap, MessageSquare, Plus, ArrowRight } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

export const UserDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  return (
    <main className="flex-1 flex flex-col min-h-screen overflow-y-auto bg-[var(--sa-canvas)] text-[var(--sa-ink)]">
      <div className="mx-auto w-full max-w-6xl space-y-10 p-5 sm:p-8">
        <section className="flex flex-col gap-6 border-b border-[var(--sa-border)] pb-8 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="sa-operational-pulse mb-4" role="status">System operational</div>
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Good morning{user?.name ? `, ${user.name}` : ''}.
            </h1>
            <p className="mt-2 max-w-xl text-[var(--sa-ink-muted)]">What would you like SupremeAI to accomplish?</p>
          </div>
          <div className="sa-eyebrow">User workspace / Ready</div>
        </section>

        {/* Signature prompt surface */}
        <section className="sa-surface-raised max-w-4xl p-5 sm:p-7" aria-labelledby="prompt-heading">
          <div className="mb-4 flex items-center justify-between gap-4">
            <div>
              <p className="sa-eyebrow mb-2">Start with an intention</p>
              <h2 id="prompt-heading" className="text-lg font-semibold">Ask SupremeAI to plan, build, or execute.</h2>
            </div>
            <span className="hidden text-xs text-[var(--sa-ink-muted)] sm:block">Enter to open Studio</span>
          </div>
          <div className="relative">
            <input
              type="text"
              aria-label="Ask SupremeAI what to accomplish"
              placeholder="Research, automate, analyze, or build..."
              className="w-full rounded-[var(--sa-radius-sm)] border border-[var(--sa-border)] bg-[var(--sa-canvas)] px-4 py-4 pr-14 text-[var(--sa-ink)] placeholder:text-[var(--sa-ink-muted)] outline-none transition focus:border-[var(--sa-primary)] focus:ring-4 focus:ring-[var(--sa-primary-soft)]"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.nativeEvent.isComposing && e.keyCode !== 229) navigate('/workspace/live');
              }}
            />
            <button type="button" aria-label="Open SupremeAI Studio" onClick={() => navigate('/workspace/live')} className="absolute right-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-[var(--sa-radius-sm)] bg-[var(--sa-primary)] text-white transition hover:opacity-90 focus:outline-none focus:ring-4 focus:ring-[var(--sa-primary-soft)]">
              <ArrowRight size={16} />
            </button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2" aria-label="Suggested tasks">
            {['Research a topic', 'Automate a workflow', 'Analyze a file', 'Browse a website'].map((suggestion) => (
              <button key={suggestion} type="button" onClick={() => navigate('/workspace/live')} className="rounded-full border border-[var(--sa-border)] px-3 py-1.5 text-xs text-[var(--sa-ink-muted)] transition hover:border-[var(--sa-primary)] hover:bg-[var(--sa-primary-soft)] hover:text-[var(--sa-primary)]">{suggestion}</button>
            ))}
          </div>
        </section>

          <div className="flex flex-wrap items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-1 border border-border text-sm font-medium hover:surface-2 transition-colors">
              <Plus size={16} className="text-secondary" /> New Project
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-1 border border-border text-sm font-medium hover:surface-2 transition-colors">
              <Bot size={16} className="text-accent-primary" /> Generate App
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-1 border border-border text-sm font-medium hover:surface-2 transition-colors">
              <Zap size={16} className="text-emerald-400" /> Deploy Service
            </button>
          </div>

        {/* Bento Grid layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          
          {/* Main Action Area (Span 8) */}
          <div className="md:col-span-8 space-y-6">
            
            {/* Continue Where You Left Off */}
            <section className="bg-surface-1 rounded-2xl p-6 border border-border">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-medium text-text">Continue Working</h2>
                <Link to="/projects" className="text-xs text-accent-primary hover:underline">View All</Link>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl surface-2 border border-border hover:border-accent-primary/30 cursor-pointer transition-colors group">
                  <div className="flex items-start justify-between mb-3">
                    <FolderOpen size={20} className="text-accent-primary" />
                    <span className="text-[10px] uppercase tracking-wider text-muted font-mono">2 hrs ago</span>
                  </div>
                  <h3 className="font-medium text-text group-hover:text-accent-primary transition-colors">Ecommerce NextJS Agent</h3>
                  <p className="text-xs text-secondary mt-1 line-clamp-2">Working on generating product catalog schema and API routes.</p>
                </div>
                <div className="p-4 rounded-xl surface-2 border border-border hover:border-accent-primary/30 cursor-pointer transition-colors group">
                  <div className="flex items-start justify-between mb-3">
                    <FolderOpen size={20} className="text-secondary" />
                    <span className="text-[10px] uppercase tracking-wider text-muted font-mono">Yesterday</span>
                  </div>
                  <h3 className="font-medium text-text group-hover:text-accent-primary transition-colors">Internal Analytics Dashboard</h3>
                  <p className="text-xs text-secondary mt-1 line-clamp-2">Data visualization components setup.</p>
                </div>
              </div>
            </section>

            {/* Recent Conversations */}
            <section className="bg-surface-1 rounded-2xl p-6 border border-border">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-medium text-text">Recent Conversations</h2>
                <Link to="/workspace/live" className="text-xs text-accent-primary hover:underline">Go to Studio</Link>
              </div>
              <div className="space-y-3">
                {[1, 2, 3].map((_, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:surface-2 cursor-pointer transition-colors">
                    <MessageSquare size={16} className="text-secondary shrink-0" />
                    <div className="flex-1 truncate text-sm text-text">How to configure CI/CD pipeline for SupremeAI agent?</div>
                    <div className="text-[10px] text-muted font-mono shrink-0">Oct 24</div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Sidebar / Status Area (Span 4) */}
          <div className="md:col-span-4 space-y-6">
            
            {/* Active Agents */}
            <section className="bg-surface-1 rounded-2xl p-6 border border-border">
              <h2 className="text-sm font-medium text-text mb-4 uppercase tracking-widest text-muted">Active Agents</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Bot size={16} className="text-accent-primary" />
                      <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    </div>
                    <span className="text-sm font-medium text-text">Code Generator</span>
                  </div>
                  <span className="text-xs text-emerald-400 font-mono">Running</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Bot size={16} className="text-secondary" />
                    </div>
                    <span className="text-sm font-medium text-text">QA Tester</span>
                  </div>
                  <span className="text-xs text-muted font-mono">Idle</span>
                </div>
              </div>
            </section>

            {/* Usage Summary */}
            <section className="bg-surface-1 rounded-2xl p-6 border border-border">
              <h2 className="text-sm font-medium text-text mb-4 uppercase tracking-widest text-muted">Usage (Pro Plan)</h2>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-secondary">GPT-4 Tokens</span>
                    <span className="text-text font-mono">42k / 100k</span>
                  </div>
                  <div className="w-full h-1.5 bg-surface-2 rounded-full overflow-hidden">
                    <div className="h-full bg-accent-primary w-[42%]"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-secondary">Agent Compute</span>
                    <span className="text-text font-mono">12h / 50h</span>
                  </div>
                  <div className="w-full h-1.5 bg-surface-2 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 w-[24%]"></div>
                  </div>
                </div>
              </div>
            </section>
            
          </div>
        </div>

      </div>
    </main>
  );
};
