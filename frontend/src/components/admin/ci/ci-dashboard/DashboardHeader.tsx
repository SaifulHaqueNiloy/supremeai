// ══════════════════════════════════════════════════════════════════════════════
// CI Dashboard — full-dashboard header (gradient banner + quick stats)
// (extracted verbatim from CIDashboard.tsx — mechanical split, no behavior change)
// ══════════════════════════════════════════════════════════════════════════════

import { RefreshCw, Rocket } from 'lucide-react';
import { ConnectionBadge } from './primitives';
import { formatDuration } from './utils';
import type { CISummaryData, ConnectionStatus } from './types';

interface DashboardHeaderProps {
  data: CISummaryData | null;
  connectionStatus: ConnectionStatus;
  autoRefresh: boolean;
  onToggleAutoRefresh: () => void;
  onRefresh: () => void;
}

export function DashboardHeader({
  data,
  connectionStatus,
  autoRefresh,
  onToggleAutoRefresh,
  onRefresh,
}: DashboardHeaderProps) {
  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-5 text-white">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Rocket className="w-6 h-6" />
            CI/CD Pipeline Status
          </h2>
          {data?.repository && (
            <p className="text-blue-100 text-sm mt-1">{data.repository}</p>
          )}
        </div>

        <div className="flex items-center gap-3">
          <ConnectionBadge status={connectionStatus} />

          <button
            onClick={onToggleAutoRefresh}
            className={`p-2 rounded-lg transition-colors ${
              autoRefresh ? 'bg-white/20 text-white' : 'bg-white/10 text-white/60'
            }`}
            title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin-slow' : ''}`} />
          </button>

          <button
            onClick={onRefresh}
            className="px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg transition-colors text-sm font-medium flex items-center gap-1"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      {data && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">
          <div className="bg-white/10 rounded-lg p-3 backdrop-blur">
            <p className="text-xs text-blue-100">Total Jobs</p>
            <p className="text-2xl font-bold">{data.metrics.total_jobs}</p>
          </div>
          <div className="bg-white/10 rounded-lg p-3 backdrop-blur">
            <p className="text-xs text-blue-100">Passed</p>
            <p className="text-2xl font-bold text-green-300">{data.metrics.passed}</p>
          </div>
          <div className="bg-white/10 rounded-lg p-3 backdrop-blur">
            <p className="text-xs text-blue-100">Failed</p>
            <p className="text-2xl font-bold text-red-300">{data.metrics.failed}</p>
          </div>
          <div className="bg-white/10 rounded-lg p-3 backdrop-blur">
            <p className="text-xs text-blue-100">Success Rate</p>
            <p className="text-2xl font-bold">{data.metrics.success_rate.toFixed(0)}%</p>
          </div>
          <div className="bg-white/10 rounded-lg p-3 backdrop-blur">
            <p className="text-xs text-blue-100">Duration</p>
            <p className="text-2xl font-bold">{formatDuration(data.run.duration_seconds)}</p>
          </div>
        </div>
      )}
    </div>
  );
}
