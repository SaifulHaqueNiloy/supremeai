// SupremeAI — Realtime Telemetry Dashboard Components
// ====================================================
// Realtime telemetry metrics widgets and hooks

import React, { useEffect, useState } from 'react';
import { getApiBaseUrl } from '../../utils/api';
import { getAuthHeaders } from '../../services/apiClient';

export interface TelemetryWidgetProps {
  title: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
  icon?: string;
}

export interface MetricData {
  id: string;
  label: string;
  value: number;
  unit?: string;
}

// Core hook for real-time telemetry metrics
/* eslint-disable-next-line react-refresh/only-export-components */
export function useRealtimeTelemetryMetrics() {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/admin/metrics/realtime`, {
          method: 'GET',
          headers: await getAuthHeaders(),
        });
        const data = await response.json();
        setMetrics(data.metrics || []);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    const interval = setInterval(fetchMetrics, 5000);
    fetchMetrics();

    return () => clearInterval(interval);
  }, []);

  return { metrics, loading };
}

// Health indicator component
export function TelemetryHealthIndicator({ status }: { status: 'healthy' | 'warning' | 'critical' }) {
  const colors = {
    healthy: 'bg-green-500',
    warning: 'bg-yellow-500',
    critical: 'bg-red-500',
  };

  return (
    <div className={`w-3 h-3 rounded-full ${colors[status]} animate-pulse`} />
  );
}

// Dashboard grid layout
export function TelemetryDashboardGrid({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4">
      {children}
    </div>
  );
}

// Backward compatibility exports
export type SujonWidgetProps = TelemetryWidgetProps;
export const useSujonMetrics = useRealtimeTelemetryMetrics;
export const SujonHealthIndicator = TelemetryHealthIndicator;
export const SujonDashboardGrid = TelemetryDashboardGrid;
