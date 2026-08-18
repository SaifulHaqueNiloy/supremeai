import React, { useEffect, useState } from 'react';
import { fetchHealth } from '../api/backend';

// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Desktop Studio — Live Backend Status indicator
// বাংলা মন্তব্য: ব্যাকএন্ড /health পোল করে লাইভ স্ট্যাটাস দেখায় (১৫s interval)
// ═══════════════════════════════════════════════════════════════════════════

export const BackendStatus: React.FC = () => {
  const [ok, setOk] = useState<boolean | null>(null);
  const [label, setLabel] = useState('connecting…');

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const h = await fetchHealth();
        if (!alive) return;
        setOk(true);
        setLabel((h.status as string) || 'ok');
      } catch {
        if (!alive) return;
        setOk(false);
        setLabel('offline');
      }
    };
    tick();
    const id = setInterval(tick, 15_000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const color = ok === null ? '#fbbf24' : ok ? '#10b981' : '#ef4444';
  return (
    <span
      className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-1 rounded-md border border-white/10 bg-white/5"
      title="Live backend health"
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ background: color, boxShadow: `0 0 8px ${color}` }}
      />
      BACKEND: {label}
    </span>
  );
};
