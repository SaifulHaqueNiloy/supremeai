import { useMemo, useState } from 'react';
import { ArrowRight, Check, Link2, Plus, Search, X } from 'lucide-react';
import { ADD_INTENTS, type AddIntent, type UserCapability } from '../../types/contracts/capability';

interface AddNewWizardProps {
  capabilities: UserCapability[];
  onClose: () => void;
  onAdd: (capability: UserCapability) => void;
}

export function AddNewWizard({ capabilities, onClose, onAdd }: AddNewWizardProps) {
  const [intent, setIntent] = useState<AddIntent>('service');
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<UserCapability | null>(null);
  const matches = useMemo(() => capabilities.filter((item) =>
    `${item.label} ${item.description}`.toLowerCase().includes(query.toLowerCase())
  ), [capabilities, query]);

  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-labelledby="add-capability-title">
    <div className="w-full max-w-2xl rounded-2xl border border-[var(--sa-border)] bg-[var(--sa-surface)] p-6 text-[var(--sa-ink)] shadow-2xl">
      <div className="flex items-start justify-between gap-4"><div><p className="sa-eyebrow">Workspace control plane</p><h2 id="add-capability-title" className="mt-2 text-xl font-semibold">Add something useful</h2><p className="mt-1 font-sans text-sm text-[var(--sa-ink-muted)]">Choose the outcome first. We will only show capabilities your workspace can use.</p></div><button className="rounded-lg p-2 hover:bg-[var(--sa-surface-raised)]" onClick={onClose} aria-label="Close"><X size={18} /></button></div>
      <div className="mt-6 grid gap-2 sm:grid-cols-2">{ADD_INTENTS.map((item) => <button key={item.id} onClick={() => setIntent(item.id)} className={`rounded-xl border p-3 text-left transition ${intent === item.id ? 'border-[var(--sa-primary)] bg-[var(--sa-primary)]/10' : 'border-[var(--sa-border)] hover:bg-[var(--sa-surface-raised)]'}`}><span className="text-sm font-medium">{item.label}</span><span className="mt-1 block font-sans text-xs text-[var(--sa-ink-muted)]">{item.description}</span></button>)}</div>
      <div className="mt-6 flex items-center gap-2 rounded-xl border border-[var(--sa-border)] bg-[var(--sa-surface-raised)] px-3"><Search size={16} className="text-[var(--sa-ink-muted)]" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Search ${intent} capabilities`} className="w-full bg-transparent py-3 font-sans text-sm outline-none" /></div>
      <div className="mt-3 grid max-h-56 gap-2 overflow-y-auto">{matches.map((item) => <button key={item.id} onClick={() => setSelected(item)} className={`flex items-center justify-between rounded-xl border p-3 text-left ${selected?.id === item.id ? 'border-[var(--sa-primary)]' : 'border-[var(--sa-border)] hover:bg-[var(--sa-surface-raised)]'}`}><span><span className="block text-sm font-medium">{item.label}</span><span className="font-sans text-xs text-[var(--sa-ink-muted)]">{item.description}</span></span>{selected?.id === item.id ? <Check size={17} /> : <ArrowRight size={17} className="text-[var(--sa-ink-muted)]" />}</button>)}{matches.length === 0 && <p className="rounded-xl border border-dashed border-[var(--sa-border)] p-5 text-center font-sans text-sm text-[var(--sa-ink-muted)]">No available capability matches this request.</p>}</div>
      <div className="mt-6 flex justify-end gap-2"><button onClick={onClose} className="rounded-lg px-4 py-2 font-sans text-sm text-[var(--sa-ink-muted)]">Cancel</button><button disabled={!selected} onClick={() => selected && onAdd(selected)} className="flex items-center gap-2 rounded-lg bg-[var(--sa-primary)] px-4 py-2 font-sans text-sm text-[var(--sa-primary-foreground)] disabled:cursor-not-allowed disabled:opacity-40"><Plus size={16} />Add capability</button></div>
    </div>
  </div>;
}

export default AddNewWizard;
