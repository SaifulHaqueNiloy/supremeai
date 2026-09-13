// ══════════════════════════════════════════════════════════════════════════════
// CI Dashboard — TRENDS TAB
// (extracted verbatim from CIDashboard.tsx — mechanical split, no behavior change)
// ══════════════════════════════════════════════════════════════════════════════

import {
  TrendingUp,
  TrendingDown,
  Minus,
  BarChart3,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { COLORS } from '../constants';
import { EmptyState } from '../primitives';
import type { CISummaryData, TrendChartPoint } from '../types';

interface TrendsTabProps {
  data: CISummaryData;
  showTrends: boolean;
  trendChartData: TrendChartPoint[];
}

export function TrendsTab({ data, showTrends, trendChartData }: TrendsTabProps) {
  return (
    <div>
      {showTrends && data.trends?.available ? (
        <div className="space-y-6">
          {/* Success Rate Over Time */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Success Rate Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis domain={[60, 100]} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="success"
                  stroke={COLORS.success}
                  strokeWidth={3}
                  dot={{ r: 4, fill: COLORS.success }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Duration Trend */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Build Duration Trend</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="duration" fill={COLORS.primary} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Stats Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-xl">
              <p className="text-xs text-blue-600 font-medium">Recent Avg</p>
              <p className="text-2xl font-bold text-blue-900">
                {data.trends.recent_success_rate?.toFixed(0)}%
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-xl">
              <p className="text-xs text-purple-600 font-medium">Overall Avg</p>
              <p className="text-2xl font-bold text-purple-900">
                {data.trends.overall_success_rate?.toFixed(0)}%
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-xl">
              <p className="text-xs text-green-600 font-medium">Trend</p>
              <p className="text-2xl font-bold text-green-900 flex items-center gap-1">
                {data.trends.trend_direction === 'improving' ? <TrendingUp /> :
                 data.trends.trend_direction === 'declining' ? <TrendingDown /> : <Minus />}
                {data.trends.trend_direction}
              </p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-xl">
              <p className="text-xs text-yellow-600 font-medium">Analyzed Runs</p>
              <p className="text-2xl font-bold text-yellow-900">
                {data.trends.total_analyzed}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <EmptyState
          message="Trend analysis requires more historical data"
          icon={BarChart3}
        />
      )}
    </div>
  );
}
