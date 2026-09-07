import { useState } from 'react';
import { useApprovalQueue, useApprovalDecision } from '../../../data/hooks';
import type { ApprovalItem } from '../../../types/approval';
import { ConfirmModal, StatusPill, EmptyState } from '../../kit';

type DecisionMode = 'approve' | 'reject' | 'cancel';

export function ApprovalQueue() {
  const { data: approvals, isLoading, isError, error } = useApprovalQueue();
  const decision = useApprovalDecision();
  const [selected, setSelected] = useState<{ item: ApprovalItem; mode: DecisionMode } | null>(null);
  const [reason, setReason] = useState('');
  const [otp, setOtp] = useState('');

  const close = () => {
    setSelected(null);
    setReason('');
    setOtp('');
  };

  const submit = () => {
    if (!selected || (selected.mode === 'reject' && !reason.trim()) || (selected.mode === 'approve' && !otp.trim())) return;
    decision.mutate(
      { id: selected.item.id, action: selected.mode, reason: reason.trim(), otp: otp.trim() },
      { onSuccess: close },
    );
  };

  if (!approvals && isLoading) return <EmptyState title="অ্যাপ্রোভাল লোড হচ্ছে..." message="অ্যাপ্রোভাল কিউ ফেচ করা হচ্ছে..." loading />;

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-mono uppercase tracking-widest text-[var(--sa-text-2)]">Approval Queue</h2>
      {isError && <div role="alert" className="rounded border border-[#ef4444]/40 p-3 text-xs font-mono text-[#ef4444]">অ্যাপ্রোভাল লোড করা যায়নি: {(error as Error)?.message}</div>}
      <div className="rounded-xl border border-[var(--sa-line)] bg-[var(--sa-bg-1)] overflow-hidden">
        <div className="divide-y divide-[var(--sa-line)]">
          {(approvals ?? []).map((item) => (
            <div key={item.id} className="p-4 flex items-center justify-between gap-4">
              <div className="min-w-0 space-y-1">
                <div className="text-[10px] font-mono text-[var(--sa-text-0)]">{item.action}</div>
                <div className="truncate text-[9px] font-mono text-[var(--sa-text-2)]">Target: {item.target ?? '—'} · By: {item.requested_by ?? 'system'}</div>
                <div className="text-[9px] font-mono text-[var(--sa-text-3)]">{item.reason || 'No reason provided'}</div>
                {item.execution_status && item.execution_status !== 'pending' && <div className="text-[9px] font-mono text-[var(--sa-text-2)]">Execution: {item.execution_status}{item.execution_error ? ` — ${item.execution_error}` : ''}</div>}
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <StatusPill status={item.status === 'pending' ? 'busy' : item.status === 'approved' || item.status === 'executed' ? 'healthy' : 'down'} label={item.status.toUpperCase()} size="sm" />
                {item.status === 'pending' && <div className="flex gap-1">
                  <button onClick={() => setSelected({ item, mode: 'approve' })} className="px-2 py-1 rounded border border-[#10b981]/30 text-[#10b981] text-[9px] font-mono hover:bg-[#10b981]/10">APPROVE</button>
                  <button onClick={() => setSelected({ item, mode: 'reject' })} className="px-2 py-1 rounded border border-[#ef4444]/30 text-[#ef4444] text-[9px] font-mono hover:bg-[#ef4444]/10">REJECT</button>
                  <button onClick={() => setSelected({ item, mode: 'cancel' })} className="px-2 py-1 rounded border border-[var(--sa-line)] text-[var(--sa-text-2)] text-[9px] font-mono">CANCEL</button>
                </div>}
              </div>
            </div>
          ))}
          {(approvals ?? []).length === 0 && <div className="p-4 text-center text-[var(--sa-text-2)] text-[10px] font-mono">কোন অ্যাপ্রোভাল নেই</div>}
        </div>
      </div>
      <ConfirmModal
        open={!!selected}
        title={selected?.mode === 'approve' ? 'অ্যাপ্রোভ করুন' : selected?.mode === 'reject' ? 'রিজেক্ট করুন' : 'ক্যানসেল করুন'}
        message={selected?.mode === 'approve' ? 'Execution শুরু করতে OTP দিন' : 'এই সিদ্ধান্তের কারণ দিন'}
        confirmLabel={selected?.mode === 'approve' ? 'APPROVE' : selected?.mode === 'reject' ? 'REJECT' : 'CANCEL'}
        danger={selected?.mode !== 'approve'}
        loading={decision.isPending}
        onCancel={close}
        onConfirm={submit}
      >
        <div className="space-y-3 mb-5">
          {selected?.mode === 'approve' && <label className="block text-[10px] font-mono text-[var(--sa-text-2)]">OTP<input value={otp} onChange={(event) => setOtp(event.target.value)} aria-label="Approval OTP" className="mt-1 w-full rounded border border-[var(--sa-line)] bg-transparent px-3 py-2 text-xs text-[var(--sa-text-0)]" /></label>}
          {selected?.mode !== 'approve' && <label className="block text-[10px] font-mono text-[var(--sa-text-2)]">Reason<textarea value={reason} onChange={(event) => setReason(event.target.value)} aria-label="Decision reason" className="mt-1 w-full rounded border border-[var(--sa-line)] bg-transparent px-3 py-2 text-xs text-[var(--sa-text-0)]" rows={3} /></label>}
          {decision.isError && <div role="alert" className="text-[10px] font-mono text-[#ef4444]">{(decision.error as Error)?.message}</div>}
        </div>
      </ConfirmModal>
    </div>
  );
}
