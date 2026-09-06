import React from 'react';
import { ArrowRight, Bot, FileText, FolderKanban, Plus, Sparkles, Zap } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

const quickStarts = [
  { label: 'Research a topic', detail: 'Synthesize sources and surface a clear answer.', icon: Sparkles, href: '/workspace/live' },
  { label: 'Build a workflow', detail: 'Turn a repeatable task into an agent run.', icon: Zap, href: '/agents' },
  { label: 'Analyze a file', detail: 'Bring context into a focused workspace.', icon: FileText, href: '/files' },
];

export const UserDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const name = user?.name?.split(' ')[0] || 'there';

  return (
    <main className="min-h-full bg-[var(--sa-canvas)] text-[var(--sa-ink)]">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-5 py-8 sm:px-8 lg:gap-10 lg:py-10">
        <header className="flex flex-col gap-5 border-b border-[var(--sa-border)] pb-7 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-4 flex items-center gap-2 text-xs font-medium text-[var(--sa-primary)]"><span className="size-2 rounded-full bg-[var(--sa-primary)] shadow-[0_0_14px_var(--sa-primary)]" />Workspace ready</div>
            <h1 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl">Good morning, {name}.</h1>
            <p className="mt-2 max-w-xl text-[var(--sa-ink-muted)]">Bring an intention. SupremeAI will help you choose the right model, context, and next step.</p>
          </div>
          <button type="button" onClick={() => navigate('/workspace/live')} className="inline-flex items-center justify-center gap-2 rounded-[var(--sa-radius-sm)] bg-[var(--sa-primary)] px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"><Plus size={16} /> New conversation</button>
        </header>

        <section className="relative overflow-hidden rounded-[var(--sa-radius)] border border-[var(--sa-border)] bg-[var(--sa-surface)] p-5 shadow-[0_18px_80px_rgba(16,185,241,0.08)] sm:p-7" aria-labelledby="intent-heading">
          <div className="pointer-events-none absolute -right-16 -top-20 size-64 rounded-full bg-cyan-400/10 blur-3xl" aria-hidden="true" />
          <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div><p className="sa-eyebrow mb-2">Start with an intention</p><h2 id="intent-heading" className="text-xl font-semibold">What should SupremeAI accomplish?</h2><p className="mt-2 text-sm text-[var(--sa-ink-muted)]">Chat, research, build, or automate from one calm workspace.</p></div>
            <span className="text-xs text-[var(--sa-ink-muted)]">Enter to open Studio</span>
          </div>
          <div className="relative mt-5 flex rounded-[var(--sa-radius-sm)] border border-[var(--sa-border)] bg-[var(--sa-canvas)] p-1.5 focus-within:border-[var(--sa-primary)] focus-within:ring-4 focus-within:ring-[var(--sa-primary-soft)]">
            <input type="text" aria-label="Ask SupremeAI what to accomplish" placeholder="Research, automate, analyze, or build..." className="min-w-0 flex-1 bg-transparent px-3 py-3 text-sm text-[var(--sa-ink)] outline-none placeholder:text-[var(--sa-ink-muted)]" onKeyDown={(e) => { if (e.key === 'Enter' && !e.nativeEvent.isComposing && e.keyCode !== 229) navigate('/workspace/live'); }} />
            <button type="button" aria-label="Open SupremeAI Studio" onClick={() => navigate('/workspace/live')} className="flex size-11 shrink-0 items-center justify-center rounded-[var(--sa-radius-sm)] bg-[var(--sa-primary)] text-white transition hover:opacity-90"><ArrowRight size={17} /></button>
          </div>
          <div className="relative mt-4 flex flex-wrap gap-2" aria-label="Suggested tasks">{quickStarts.map(({ label, icon: Icon, href }) => <Link key={label} to={href} className="inline-flex items-center gap-2 rounded-full border border-[var(--sa-border)] px-3 py-2 text-xs text-[var(--sa-ink-muted)] transition hover:border-[var(--sa-primary)] hover:bg-[var(--sa-primary-soft)] hover:text-[var(--sa-primary)]"><Icon size={13} />{label}</Link>)}</div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[1.35fr_0.65fr]">
          <div className="sa-surface-raised p-5 sm:p-6"><div className="mb-5 flex items-center justify-between"><div><p className="sa-eyebrow">Continue working</p><h2 className="mt-2 text-lg font-semibold">Recent work</h2></div><Link to="/activity" className="text-xs font-medium text-[var(--sa-primary)]">View activity</Link></div><div className="rounded-[var(--sa-radius-sm)] border border-dashed border-[var(--sa-border)] p-5 text-sm text-[var(--sa-ink-muted)]"><p>No recent work yet.</p><Link to="/workspace/live" className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-[var(--sa-primary)]">Start your first conversation <ArrowRight size={13} /></Link></div></div>
          <div className="flex flex-col gap-5"><div className="sa-surface-raised p-5"><div className="flex items-center gap-3"><div className="flex size-9 items-center justify-center rounded-lg bg-[var(--sa-primary-soft)] text-[var(--sa-primary)]"><Bot size={17} /></div><div><p className="sa-eyebrow">Active agents</p><h2 className="mt-1 text-lg font-semibold">No agents yet</h2></div></div><Link to="/agents" className="mt-5 inline-flex text-xs font-medium text-[var(--sa-primary)]">Create an agent <ArrowRight size={13} className="ml-1" /></Link></div><div className="sa-surface-raised p-5"><div className="flex items-center gap-3"><FolderKanban size={17} className="text-[var(--sa-primary)]" /><div><p className="sa-eyebrow">Workspace usage</p><h2 className="mt-1 text-lg font-semibold">No usage yet</h2></div></div><p className="mt-4 text-xs text-[var(--sa-ink-muted)]">Usage will appear after your first run.</p><Link to="/usage" className="mt-4 inline-flex text-xs font-medium text-[var(--sa-primary)]">Review usage <ArrowRight size={13} className="ml-1" /></Link></div></div>
        </section>
      </div>
    </main>
  );
};

export default UserDashboard;
