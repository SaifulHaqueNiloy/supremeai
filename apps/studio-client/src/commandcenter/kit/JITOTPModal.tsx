import React, { useEffect, useRef, useState } from 'react';
import { X, ShieldCheck, Clock } from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Command Center — JIT OTP Modal
// বাংলা মন্তব্য: ডেস্ট্রাক্টিভ অ্যাকশনের আগে OTP ভেরিফিকেশন — ৯০s expiry
// ═══════════════════════════════════════════════════════════════════════════

interface JITOTPModalProps {
  open: boolean;
  action: string;
  reasonRequired?: boolean;
  loading?: boolean;
  error?: string | null;
  onVerify: (otp: string, reason?: string) => void;
  onCancel: () => void;
}

export function JITOTPModal({
  open,
  action,
  reasonRequired = true,
  loading,
  error,
  onVerify,
  onCancel,
}: JITOTPModalProps) {
  const [otp, setOtp] = useState('');
  const [reason, setReason] = useState('');
  const [expiresIn, setExpiresIn] = useState(90);
  const otpRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setOtp('');
      setReason('');
      setExpiresIn(90);
      setTimeout(() => otpRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const timer = setInterval(() => {
      setExpiresIn((s) => {
        if (s <= 1) {
          clearInterval(timer);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [open]);

  if (!open) return null;

  const canSubmit = otp.length >= 6 && (!reasonRequired || reason.trim().length >= 10) && expiresIn > 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-xl border border-[var(--sa-line)] bg-[var(--sa-bg-1)] p-6 shadow-2xl">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <ShieldCheck size={20} className="text-[#bc13fe]" />
            <div>
              <h3 className="text-sm font-mono font-bold text-[var(--sa-text-0)]">JIT OTP ভেরিফিকেশন</h3>
              <p className="text-[10px] font-mono text-[var(--sa-text-2)] mt-0.5">{action}</p>
            </div>
          </div>
          <button onClick={onCancel} className="text-[var(--sa-text-1)] hover:text-[var(--sa-text-0)]">
            <X size={16} />
          </button>
        </div>

        <div className="flex items-center gap-2 mb-4">
          <Clock size={14} className={expiresIn <= 15 ? 'text-[#ef4444]' : 'text-[#f59e0b]'} />
          <span className={`text-xs font-mono ${expiresIn <= 15 ? 'text-[#ef4444]' : 'text-[#f59e0b]'}`}>
            {expiresIn}s
          </span>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-[10px] font-mono uppercase tracking-wider text-[var(--sa-text-2)] mb-1.5">
              OTP কোড
            </label>
            <input
              ref={otpRef}
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/[^0-9]/g, '').slice(0, 6))}
              placeholder="••••••"
              className="w-full px-3 py-2 rounded-lg bg-[var(--sa-bg-2)] border border-[#bc13fe]/30 text-center text-lg font-mono tracking-[0.5em] text-[var(--sa-text-0)] focus:outline-none focus:border-[#bc13fe]"
            />
          </div>

          {reasonRequired && (
            <div>
              <label className="block text-[10px] font-mono uppercase tracking-wider text-[var(--sa-text-2)] mb-1.5">
                কারণ (কমপক্ষে ১০ অক্ষর)
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={2}
                placeholder="কেন এই অ্যাকশনটি করছেন?"
                className="w-full px-3 py-2 rounded-lg bg-[var(--sa-bg-2)] border border-[var(--sa-line)] text-xs font-mono text-[var(--sa-text-0)] focus:outline-none focus:border-[#bc13fe] resize-none"
              />
            </div>
          )}

          {error && (
            <div className="px-3 py-2 rounded-lg bg-[#ef4444]/10 border border-[#ef4444]/30 text-xs font-mono text-[#ef4444]">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={onCancel}
              disabled={loading}
              className="px-4 py-2 rounded-lg border border-[var(--sa-line)] text-xs font-mono text-[var(--sa-text-1)] hover:border-[var(--sa-text-1)] disabled:opacity-50"
            >
              বাতিল
            </button>
            <button
              onClick={() => onVerify(otp, reason)}
              disabled={!canSubmit || loading}
              className="px-4 py-2 rounded-lg bg-[#bc13fe]/20 text-[#bc13fe] border border-[#bc13fe]/40 text-xs font-mono font-bold hover:bg-[#bc13fe]/30 disabled:opacity-50"
            >
              {loading ? 'ভেরিফাই হচ্ছে...' : 'ভেরিফাই করুন'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}