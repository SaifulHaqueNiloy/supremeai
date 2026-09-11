import React, { useState } from 'react';
import { ArrowRight, Bot, FileText, FolderKanban, Plus, Settings2, Sparkles, Terminal, X, Zap } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useWorkspaceSettings, WORKSPACE_MODULES } from '../../hooks/useWorkspaceSettings';
import TaskAutomationCard from './TaskAutomationCard';

const quickStarts = [
  { label: 'Research a topic', detail: 'Get a clear answer with useful context.', icon: Sparkles, href: '/workspace/live' },
  { label: 'Analyze a file', detail: 'Bring a document into a focused workspace.', icon: FileText, href: '/files' },
  { label: 'Build a workflow', detail: 'Turn a repeatable task into a helper.', icon: Zap, href: '/agents' },
];

const icons = { ask: Sparkles, projects: FolderKanban, files: FileText, activity: Zap, agents: Bot, integrations: Settings2, usage: FileText, code: Terminal };

export const UserDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [showTools, setShowTools] = useState(false);
  const { enabledModules, toggleModule } = useWorkspaceSettings();
  const name = user?.name?.split(' ')[0] || 'there';
  const tools = WORKSPACE_MODULES.filter((module) => enabledModules.includes(module.id));

  return (
    <main className="min-h-full bg-[var(--sa-canvas)] text-[var(--sa-ink)]">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-5 py-8 sm:px-8 lg:py-10">
        <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div><p className="sa-eyebrow mb-3">Your workspace</p><h1 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl">Good morning, {name}.</h1><p className="mt-2 max-w-xl text-[var(--sa-ink-muted)]">A simple place to think, make progress, and keep your work moving.</p></div>
          <Link to="/settings" className="inline-flex items-center gap-2 self-start rounded-[var(--sa-radius-sm)] border border-[var(--sa-border)] px-4 py-2.5 text-sm font-medium transition hover:border-[var(--sa-primary)] hover:text-[var(--sa-primary)]"><Settings2 size={16} /> Personalize</Link>
        </header>

        <TaskAutomationCard />

        <section className="sa-surface-raised p-5 sm:p-7" aria-labelledby="intent-heading">
          <p className="sa-eyebrow mb-2">Start anywhere</p><h2 id="intent-heading" className="text-xl font-semibold">What would you like to do?</h2>
          <div className="mt-5 flex rounded-[var(--sa-radius-sm)] border border-[var(--sa-border)] bg-[var(--sa-canvas)] p-1.5 focus-within:border-[var(--sa-primary)] focus-within:ring-4 focus-within:ring-[var(--sa-primary-soft)]"><input type="text" aria-label="Ask SupremeAI what to accomplish" placeholder="Ask a question, describe a task, or share an idea..." className="min-w-0 flex-1 bg-transparent px-3 py-3 text-sm outline-none placeholder:text-[var(--sa-ink-muted)]" onKeyDown={(event) => { if (event.key === 'Enter' && !event.nativeEvent.isComposing && event.keyCode !== 229) navigate('/workspace/live'); }} /><button type="button" aria-label="Open SupremeAI Studio" onClick={() => navigate('/workspace/live')} className="flex size-11 shrink-0 items-center justify-center rounded-[var(--sa-radius-sm)] bg-[var(--sa-primary)] text-white transition hover:opacity-90"><ArrowRight size={17} /></button></div>
          <div className="mt-4 flex flex-wrap gap-2">{quickStarts.map(({ label, icon: Icon, href }) => <Link key={label} to={href} className="inline-flex items-center gap-2 rounded-full border border-[var(--sa-border)] px-3 py-2 text-xs text-[var(--sa-ink-muted)] transition hover:border-[var(--sa-primary)] hover:bg-[var(--sa-primary-soft)] hover:text-[var(--sa-primary)]"><Icon size={13} />{label}</Link>)}</div>
        </section>

        <section aria-labelledby="tools-heading"><div className="mb-4 flex items-center justify-between"><div><p className="sa-eyebrow">Your tools</p><h2 id="tools-heading" className="mt-1 text-xl font-semibold">Only what you need</h2></div><button type="button" onClick={() => setShowTools(true)} className="inline-flex items-center gap-2 rounded-[var(--sa-radius-sm)] border border-[var(--sa-border)] px-3 py-2 text-xs font-medium hover:border-[var(--sa-primary)] hover:text-[var(--sa-primary)]"><Plus size={14} /> Add tools</button></div><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{tools.map((module) => { const Icon = icons[module.id]; return <Link key={module.id} to={module.href} className="group sa-surface-raised flex min-h-32 flex-col justify-between p-5 transition hover:-translate-y-0.5 hover:border-[var(--sa-primary)]"><div className="flex items-start justify-between"><span className="flex size-9 items-center justify-center rounded-lg bg-[var(--sa-primary-soft)] text-[var(--sa-primary)]"><Icon size={17} /></span><ArrowRight size={15} className="text-[var(--sa-ink-muted)] transition group-hover:text-[var(--sa-primary)]" /></div><div><h3 className="mt-4 text-sm font-semibold">{module.label}</h3><p className="mt-1 text-xs leading-5 text-[var(--sa-ink-muted)]">{module.description}</p></div></Link> })}</div></section>

        <section className="grid gap-4 lg:grid-cols-2"><div className="sa-surface-raised p-5"><p className="sa-eyebrow">Recent work</p><h2 className="mt-2 text-lg font-semibold">Nothing here yet</h2><p className="mt-2 text-sm text-[var(--sa-ink-muted)]">Your conversations, projects, and completed tasks will appear here.</p></div><div className="sa-surface-raised p-5"><p className="sa-eyebrow">Need a starting point?</p><h2 className="mt-2 text-lg font-semibold">Begin with a small task</h2><p className="mt-2 text-sm text-[var(--sa-ink-muted)]">You can always add more tools later from Settings.</p></div></section>
      </div>
      {showTools && <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/30 p-4 sm:items-center" role="dialog" aria-modal="true" aria-labelledby="tools-dialog-title"><div className="w-full max-w-lg rounded-2xl border border-[var(--sa-border)] bg-[var(--sa-surface)] p-5 shadow-2xl"><div className="flex items-start justify-between"><div><p className="sa-eyebrow">Personalize</p><h2 id="tools-dialog-title" className="mt-1 text-xl font-semibold">Choose your tools</h2><p className="mt-1 text-sm text-[var(--sa-ink-muted)]">Keep the workspace focused. You can change this any time.</p></div><button type="button" aria-label="Close tool picker" onClick={() => setShowTools(false)} className="rounded-lg p-2 text-[var(--sa-ink-muted)] hover:bg-[var(--sa-canvas)]"><X size={17} /></button></div><div className="mt-5 flex flex-col gap-2">{WORKSPACE_MODULES.map((module) => <label key={module.id} className="flex cursor-pointer items-center gap-3 rounded-xl border border-[var(--sa-border)] p-3 transition hover:border-[var(--sa-primary)]"><input type="checkbox" checked={enabledModules.includes(module.id)} onChange={() => toggleModule(module.id)} className="size-4 accent-[var(--sa-primary)]" /><span className="flex-1"><span className="block text-sm font-medium">{module.label}{module.advanced && <span className="ml-2 rounded-full bg-[var(--sa-primary-soft)] px-2 py-0.5 text-[10px] text-[var(--sa-primary)]">Optional developer tool</span>}</span><span className="mt-0.5 block text-xs text-[var(--sa-ink-muted)]">{module.description}</span></span></label>)}</div><button type="button" onClick={() => setShowTools(false)} className="mt-5 w-full rounded-[var(--sa-radius-sm)] bg-[var(--sa-primary)] px-4 py-2.5 text-sm font-semibold text-white">Done</button></div></div>}
    </main>
  );
};

export default UserDashboard;
