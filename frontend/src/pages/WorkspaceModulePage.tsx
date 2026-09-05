import React from 'react';
import { ArrowRight, CircleCheck, Construction } from 'lucide-react';
import { Link } from 'react-router-dom';
import { WorkspaceLayout } from '../components/layout/WorkspaceLayout';

const modules: Record<string, { eyebrow: string; title: string; description: string; actions: string[] }> = {
  projects: { eyebrow: 'Build / Projects', title: 'Keep active work visible.', description: 'Projects give every agent, conversation, and artifact a durable home.', actions: ['Create a project space', 'Attach an existing conversation', 'Invite a collaborator'] },
  activity: { eyebrow: 'Build / Activity', title: 'See what changed.', description: 'A focused activity feed for workspace events, approvals, and completed actions.', actions: ['Review recent events', 'Filter by agent', 'Export an audit view'] },
  marketplace: { eyebrow: 'Extend / Marketplace', title: 'Extend the command center.', description: 'Discover reusable skills and integrations without losing permission boundaries.', actions: ['Browse skills', 'Review permissions', 'Install an integration'] },
  runs: { eyebrow: 'Observe / Runs', title: 'Follow work from trigger to outcome.', description: 'Track running and completed agent executions in one operational timeline.', actions: ['Inspect a run', 'Retry a failed step', 'Open the related conversation'] },
  usage: { eyebrow: 'Govern / Usage', title: 'Know where capacity goes.', description: 'Understand model, agent, and workspace usage before it becomes a surprise.', actions: ['Review current period', 'Compare agents', 'Open billing'] },
  settings: { eyebrow: 'Account / Settings', title: 'Make the workspace yours.', description: 'Configure workspace behavior, theme, and notification preferences.', actions: ['Configure preferences', 'Review notifications', 'Manage sessions'] },
};

export function WorkspaceModulePage({ module }: { module: keyof typeof modules }) {
  const content = modules[module];
  return <WorkspaceLayout><main className="min-h-full bg-[var(--sa-canvas)] px-5 py-8 text-[var(--sa-ink)] sm:px-8"><div className="mx-auto max-w-5xl"><p className="sa-eyebrow">{content.eyebrow}</p><h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">{content.title}</h1><p className="mt-3 max-w-2xl text-[var(--sa-ink-muted)]">{content.description}</p><section className="mt-10 grid gap-4 md:grid-cols-3" aria-label={`${content.title} actions`}>{content.actions.map((action) => <article key={action} className="sa-surface-raised flex min-h-44 flex-col justify-between p-5"><CircleCheck className="text-[var(--sa-primary)]" size={18} aria-hidden="true" /><div><h2 className="mt-8 font-medium">{action}</h2><p className="mt-2 text-sm text-[var(--sa-ink-muted)]">This module is connected to the shared workspace shell.</p></div></article>)}</section><div className="mt-8 flex items-center gap-3 border border-[var(--sa-border)] bg-[var(--sa-surface)] p-4 text-sm text-[var(--sa-ink-muted)]"><Construction size={17} aria-hidden="true" /><span>Foundation route ready for the next backend-backed workflow.</span><Link to="/workspace/live" className="ml-auto inline-flex items-center gap-2 font-medium text-[var(--sa-primary)]">Open Studio <ArrowRight size={15} /></Link></div></div></main></WorkspaceLayout>;
}

export default WorkspaceModulePage;
