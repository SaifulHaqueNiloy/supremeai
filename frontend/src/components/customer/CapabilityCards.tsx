import { AlertCircle, CheckCircle2, ExternalLink, Settings2 } from 'lucide-react';
import type { UnavailableCapability, UserCapability } from '../../types/contracts/capability';

export function ManageItem({ item, onManage }: { item: UserCapability; onManage?: () => void }) {
  return <article className="rounded-xl border border-[var(--sa-border)] bg-[var(--sa-surface)] p-4"><div className="flex items-start justify-between gap-3"><div><h3 className="text-sm font-semibold">{item.label}</h3><p className="mt-1 font-sans text-sm leading-6 text-[var(--sa-ink-muted)]">{item.description}</p></div><span className="flex items-center gap-1 text-[11px] uppercase tracking-wider text-emerald-400"><CheckCircle2 size={14} /> ready</span></div><div className="mt-4 flex gap-2">{item.href && <a href={item.href} className="flex items-center gap-1 rounded-lg border border-[var(--sa-border)] px-3 py-2 font-sans text-xs hover:bg-[var(--sa-surface-raised)]">Open <ExternalLink size={13} /></a>}<button onClick={onManage} className="flex items-center gap-1 rounded-lg border border-[var(--sa-border)] px-3 py-2 font-sans text-xs hover:bg-[var(--sa-surface-raised)]"><Settings2 size={13} /> Manage</button></div></article>;
}

export function CapabilityUnavailableExplainer({ item, onRequest }: { item: UnavailableCapability; onRequest?: () => void }) {
  return <article className="rounded-xl border border-dashed border-amber-400/40 bg-amber-400/5 p-4"><div className="flex gap-3"><AlertCircle className="mt-0.5 text-amber-300" size={18} /><div><h3 className="text-sm font-semibold">{item.label} is unavailable</h3><p className="mt-1 font-sans text-sm leading-6 text-[var(--sa-ink-muted)]">{item.reason}</p>{item.requestable && <button onClick={onRequest} className="mt-3 rounded-lg border border-amber-300/40 px-3 py-2 font-sans text-xs text-amber-200 hover:bg-amber-300/10">Request access</button>}</div></div></article>;
}
