// ══════════════════════════════════════════════════════════════════════════════
// CI Dashboard — Presentational Sub-Components
// Extracted from CIDashboard.tsx (maintainability refactor — no behavior change).
// ══════════════════════════════════════════════════════════════════════════════

import { useState } from 'react';
import type { ElementType, ReactNode } from 'react';
import {
  Activity,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Clock,
  ExternalLink,
  Loader2,
  Target,
  Wifi,
  WifiOff,
} from 'lucide-react';
import type { CIInsight, ConnectionStatus, JobResult } from './CIDashboard.types';
import { COLORS, STATUS_CONFIG, formatDuration, getGradeColor } from './CIDashboard.constants';

export function Badge({ children, variant = 'default' }: { children: ReactNode; variant?: 'success' | 'warning' | 'failure' | 'default' }) {
  const variants = {
    success: 'bg-green-100 text-green-800 border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    failure: 'bg-red-100 text-red-800 border-red-200',
    default: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${variants[variant]}`}>
      {children}
    </span>
  );
}

export function ScoreCircle({ score, grade, size = 80 }: { score: number; grade: string; size?: number }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const color = getGradeColor(grade);

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#e5e7eb" strokeWidth="6" />
        <circle
          cx={size/2}
          cy={size/2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold" style={{ color }}>{score}</span>
        <span className="text-xs font-semibold" style={{ color }}>{grade}</span>
      </div>
    </div>
  );
}

export function AnimatedStatus({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.skipped;
  const Icon = config.icon;
  const isAnimating = status === 'in_progress';

  return (
    <div
      className={`p-2 rounded-lg ${config.bgColor}`}
      style={{ color: config.color }}
    >
      <Icon className={`w-5 h-5 ${isAnimating ? 'animate-spin' : ''}`} />
    </div>
  );
}

export function ProgressBar({ value, max = 100, color, showLabel = false }: { value: number; max?: number; color?: string; showLabel?: boolean }) {
  const percentage = Math.min((value / max) * 100, 100);
  const barColor = color || (percentage >= 90 ? COLORS.success : percentage >= 70 ? COLORS.warning : COLORS.failure);

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-1">
        {showLabel && <span className="text-xs text-gray-600">{percentage.toFixed(0)}%</span>}
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percentage}%`, backgroundColor: barColor }}
        />
      </div>
    </div>
  );
}

export function InsightCard({ insight }: { insight: CIInsight }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <span className="text-2xl">{insight.icon}</span>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-gray-900 text-sm">{insight.title}</h4>
          <p className="text-xs text-gray-600 mt-1">{insight.description}</p>

          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 mt-2 text-xs text-blue-600 hover:text-blue-800"
          >
            {expanded ? 'Less' : 'More'}
            {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </button>

          {expanded && (
            <div className="mt-3 p-3 bg-gray-50 rounded-lg space-y-2">
              <div className="flex items-start gap-2">
                <Target className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-medium text-gray-700">Action Item</p>
                  <p className="text-xs text-gray-600">{insight.action_item}</p>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Category: {insight.category}</span>
                <span>Confidence: {(insight.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function JobRow({ job, onClick, compact = false }: { job: JobResult; onClick?: () => void; compact?: boolean }) {
  const config = STATUS_CONFIG[job.status];
  const Icon = config.icon;

  if (compact) {
    return (
      <button
        onClick={onClick}
        className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50 transition-colors text-left"
      >
        <Icon className="w-4 h-4 flex-shrink-0" style={{ color: config.color }} />
        <span className="truncate text-sm flex-1">{job.name}</span>
        <span className="text-xs text-gray-500">{formatDuration(job.duration)}</span>
      </button>
    );
  }

  return (
    <div
      onClick={onClick}
      className="flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all cursor-pointer group"
    >
      <AnimatedStatus status={job.status} />

      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors truncate">
          {job.name}
        </h4>
        <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatDuration(job.duration)}
          </span>
          {job.runner_name && (
            <span className="flex items-center gap-1">
              <Activity className="w-3 h-3" />
              {job.runner_name}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {(job.error_count > 0 || job.warning_count > 0) && (
          <div className="flex gap-1">
            {job.error_count > 0 && (
              <Badge variant="failure">{job.error_count} errors</Badge>
            )}
            {job.warning_count > 0 && (
              <Badge variant="warning">{job.warning_count} warnings</Badge>
            )}
          </div>
        )}

        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="p-1.5 rounded-lg hover:bg-gray-100 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <ExternalLink className="w-4 h-4 text-gray-400" />
          </a>
        )}
      </div>
    </div>
  );
}

export function EmptyState({ message, icon: Icon }: { message: string; icon: ElementType }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-gray-500">
      <Icon className="w-12 h-12 mb-4 text-gray-300" />
      <p className="text-lg font-medium">{message}</p>
      <p className="text-sm mt-1">Check back soon or try refreshing</p>
    </div>
  );
}

export function ConnectionBadge({ status }: { status: ConnectionStatus }) {
  const configs = {
    connected: { icon: Wifi, color: 'text-green-600', bg: 'bg-green-100', label: 'Live' },
    disconnected: { icon: WifiOff, color: 'text-gray-400', bg: 'bg-gray-100', label: 'Offline' },
    connecting: { icon: Loader2, color: 'text-blue-600', bg: 'bg-blue-100', label: 'Connecting...' },
    error: { icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-100', label: 'Error' },
  };

  const config = configs[status];
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
      <Icon className={`w-3 h-3 ${status === 'connecting' ? 'animate-spin' : ''}`} />
      {config.label}
    </span>
  );
}
