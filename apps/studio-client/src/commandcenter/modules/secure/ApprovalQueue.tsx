import { useState } from 'react';
import { useApprovalQueue, useApproveAction } from '../../data/hooks';
import { ConfirmModal, StatusPill, EmptyState } from '../../kit';

export function ApprovalQueue() {
  const { data: approvals, isLoading } = useApprovalQueue();
  const approve = useApproveAction();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [reason, setReason] = useState('');
  const [otp, setOtp] = useState('');

  const handleAction = (approveAction: boolean) => {
    if (selectedId) {
      approve.mutate({ id: selectedId, approve: approveAction, reason, otp });
      setSelectedId(null);
      setReason('');
      setOtp('');
    }
  };

  if (!approvals && isLoading) {
    return <EmptyState title="অ্যাপ্রোভাল লোড হচ্ছে..." message="অ্যাপ্রোভাল কিউ ফেচ করা হচ্ছে..." loading />;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-mono uppercase tracking-widest text-[var(--sa-text-2)]">Approval Queue</h2>
      <div className="rounded-xl border border-[var(--sa-line)] bg-[var(--sa-bg-1)] overflow-hidden">
        <div className="divide-y divide-[var(--sa-line)]">
          {(approvals ?? []).map((item) => (
            <div key={item.id} className="p-4 flex items-center justify-between">
              <div className="space-y-1">
                <div className="text-[10px] font-mono text-[var(--sa-text-0)]">{item.action}</div>
                <div className="text-[9px] font-mono text-[var(--sa-text-2)]">Target: {item.target} · By: {item.requested_by}</div>
                <div className="text-[9px] font-mono text-[var(--sa-text-3)]">{item.reason}</div>
              </div>
              <div className="flex items-center gap-2">
                <StatusPill status={item.status === 'pending' ? 'busy' : item.status === 'approved' ? 'healthy' : 'down'} label={item.status.toUpperCase()} size="sm" />
                {item.status === 'pending' && (
                  <div className="flex gap-1">
                    <button
                      onClick={() => { setSelectedId(item.id); setReason(''); setOtp(''); }}
                      className="px-2 py-1 rounded border border-[#10b981]/30 text-[#10b981] text-[9px] font-mono hover:bg-[#10b981]/10"
                    >
                      APPROVE
                    </button>
                    <button
                      onClick={() => { setSelectedId(item.id); setReason(''); setOtp(''); }}
                      className="px-2 py-1 rounded border border-[#ef4444]/30 text-[#ef4444] text-[9px] font-mono hover:bg-[#ef4444]/10"
                    >
                      REJECT
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {(approvals ?? []).length === 0 && (
            <div className="p-4 text-center text-[var(--sa-text-2)] text-[10px] font-mono">কোন পেন্ডিং অ্যাপ্রোভাল নেই</div>
          )}
        </div>
      </div>
      <ConfirmModal
        open={!!selectedId}
        title={approvals?.find(a => a.id === selectedId)?.status === 'pending' ? 'অ্যাপ্রোভ করুন' : 'রিজেক্ট করুন'}
        message="নিশ্চিত করতে OTP দিন"
        onCancel={() => { setSelectedId(null); setReason(''); setOtp(''); }}
        onConfirm={() => handleAction(approvals?.find(a => a.id === selectedId)?.status !== 'rejected')}
      />
    </div>
  );
}
