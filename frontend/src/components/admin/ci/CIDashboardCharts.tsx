// ══════════════════════════════════════════════════════════════════════════════
// CI Dashboard — Tab Panels (Errors & Trends)
// Extracted from CIDashboard.tsx (maintainability refactor — no behavior change).
// ══════════════════════════════════════════════════════════════════════════════

import {
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Minus,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { CISummaryData, SeveritySlice, TrendPoint } from './CIDashboard.types';
import { COLORS } from './CIDashboard.constants';
import { Badge, EmptyState } from './CIDashboardWidgets';

export function ErrorsTab({ data, severityPieData }: { data: CISummaryData; severityPieData: SeveritySlice[] }) {
  const hasErrors = data.errors.total > 0;

  return (
    <div>
      {hasErrors ? (
        <>
          {/* Severity Breakdown */}
          {severityPieData.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">Error Severity Distribution</h3>
              <div className="flex items-center gap-6">
                <ResponsiveContainer width={200} height={200}>
                  <PieChart>
                    <Pie
                      data={severityPieData}
                      cx="100"
                      cy="100"
                      innerRadius={40}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {severityPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>

                <div className="flex-1 space-y-2">
                  {severityPieData.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm font-medium text-gray-700">{item.name}</span>
                      <span className="text-sm text-gray-500 ml-auto">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Category Breakdown */}
          {Object.keys(data.errors.by_category).length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">By Category</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(data.errors.by_category).map(([cat, count], idx) => (
                  <div key={idx} className="p-3 bg-red-50 rounded-lg border border-red-100">
                    <p className="text-sm font-medium text-red-900">{cat}</p>
                    <p className="text-2xl font-bold text-red-700">{count}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error List */}
          <details className="group">
            <summary className="cursor-pointer list-none flex items-center gap-2 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <ChevronRight className="w-4 h-4 transform group-open:rotate-90 transition-transform" />
              <span className="font-medium text-gray-900">View All Errors ({data.errors.total})</span>
            </summary>

            <div className="mt-3 space-y-2 max-h-[400px] overflow-y-auto">
              {data.errors.items.map((err, idx) => (
                <div key={idx} className="p-3 bg-white rounded-lg border border-gray-200 text-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{err.severity_icon}</span>
                    <span className="font-medium text-gray-900">{err.category}</span>
                    <Badge variant={err.severity === 'P0' || err.severity === 'P1' ? 'failure' : 'warning'}>
                      {err.severity}
                    </Badge>
                  </div>
                  <p className="text-gray-600 font-mono text-xs break-all mt-1">
                    {err.message}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Job: {err.job} • Line: {err.line_number}
                  </p>
                </div>
              ))}
            </div>
          </details>
        </>
      ) : (
        <EmptyState message="No errors detected! 🎉" icon={CheckCircle2} />
      )}
    </div>
  );
}

export function TrendsTab({ data, showTrends, trendChartData }: { data: CISummaryData; showTrends: boolean; trendChartData: TrendPoint[] }) {
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
