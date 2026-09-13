// ══════════════════════════════════════════════════════════════════════════════
// CI Dashboard — Color Constants, Status Config & Utility Functions
// Extracted from CIDashboard.tsx (maintainability refactor — no behavior change).
// ══════════════════════════════════════════════════════════════════════════════

import type { ElementType } from 'react';
import { CheckCircle2, Loader2, Minus, XCircle } from 'lucide-react';

export const COLORS = {
  success: '#22c55e',
  successBg: '#f0fdf4',
  failure: '#ef4444',
  failureBg: '#fef2f2',
  warning: '#f59e0b',
  warningBg: '#fffbeb',
  skipped: '#94a3b8',
  skippedBg: '#f8fafc',
  primary: '#3b82f6',
  primaryBg: '#eff6ff',
  purple: '#8b5cf6',
  pink: '#ec4899',

  gradeColors: {
    'A+': '#22c55e', 'A': '#22c55e', 'A-': '#84cc16',
    'B+': '#84cc16', 'B': '#eab308', 'B-': '#eab308',
    'C+': '#f97316', 'C': '#f97316', 'C-': '#ef4444',
    'D': '#ef4444', 'F': '#dc2626',
  },
};

export const STATUS_CONFIG: Record<string, { icon: ElementType; color: string; bgColor: string; label: string }> = {
  success: { icon: CheckCircle2, color: COLORS.success, bgColor: COLORS.successBg, label: 'Passed' },
  failure: { icon: XCircle, color: COLORS.failure, bgColor: COLORS.failureBg, label: 'Failed' },
  cancelled: { icon: Minus, color: COLORS.skipped, bgColor: COLORS.skippedBg, label: 'Cancelled' },
  skipped: { icon: Minus, color: COLORS.skipped, bgColor: COLORS.skippedBg, label: 'Skipped' },
  in_progress: { icon: Loader2, color: COLORS.primary, bgColor: COLORS.primaryBg, label: 'Running' },
};

// ══════════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ══════════════════════════════════════════════════════════════════════════════

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${Math.floor(seconds / 3600)}h${Math.floor((seconds % 3600) / 60)}m`;
}

export function getGradeColor(grade: string): string {
  return COLORS.gradeColors[grade as keyof typeof COLORS.gradeColors] || COLORS.skipped;
}

export function timeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
