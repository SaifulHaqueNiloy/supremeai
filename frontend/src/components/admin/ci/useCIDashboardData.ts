// ══════════════════════════════════════════════════════════════════════════════
// CI Dashboard — Data Hook (REST fetch + WebSocket + auto-refresh polling)
// Extracted from CIDashboard.tsx (maintainability refactor — no behavior change).
// Effect order, dependency arrays and state transitions are preserved 1:1.
// ══════════════════════════════════════════════════════════════════════════════

import { useCallback, useEffect, useState } from 'react';
import type { CISummaryData, ConnectionStatus } from './CIDashboard.types';

interface UseCIDashboardDataOptions {
  apiUrl?: string;
  wsUrl?: string;
  refreshInterval: number;
}

export function useCIDashboardData({ apiUrl, wsUrl, refreshInterval }: UseCIDashboardDataOptions) {
  // State
  const [data, setData] = useState<CISummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      const url = apiUrl || `${import.meta.env.VITE_API_URL || import.meta.env.VITE_BACKEND_URL || ''}/api/ci/latest-summary`;
      const response = await fetch(url);

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const result: CISummaryData = await response.json();
      setData(result);
      setError(null);
      setLastUpdated(new Date());
      setConnectionStatus('connected');
    } catch (err) {
      console.error('Failed to fetch CI data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch');
      setConnectionStatus('error');
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const wsEndpoint = wsUrl || import.meta.env.VITE_DASHBOARD_WS_URL;

    if (!wsEndpoint) {
      // Fallback to polling
      fetchData();
      return;
    }

    let reconnectAttempt = 0;
    const MAX_RECONNECT = 8;
    let destroyed = false;
    let ws: WebSocket | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | undefined;

    const connect = () => {
      if (destroyed) return;
      setConnectionStatus('connecting');

      try {
        // SECURITY FIX (audit S-2): token must NOT be in the URL.
        // Strip any ?token= that the caller might have embedded in wsEndpoint.
        const cleanWsEndpoint = wsEndpoint.replace(/([?&])token=[^&]*/g, '$1').replace(/[?&]$/, '');
        const socket = new WebSocket(cleanWsEndpoint);
        ws = socket;

        socket.onopen = () => {
          // First-message auth frame — token never appears in URL or logs.
          const token = localStorage.getItem('supremeai_auth_token') || localStorage.getItem('supreme_admin_jwt');
          if (token) socket.send(JSON.stringify({ type: 'auth', token }));
          reconnectAttempt = 0;
          setConnectionStatus('connected');
        };

        socket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);

            if (message.channel === 'ci.summary' || message.type === 'ci_update') {
              setData(message.data);
              setLastUpdated(new Date());
            }
          } catch (err) {
            console.error('WebSocket parse error:', err);
          }
        };

        socket.onclose = () => {
          setConnectionStatus('disconnected');
          if (destroyed || reconnectAttempt >= MAX_RECONNECT) return;
          // Exponential backoff with jitter
          const delay = Math.min(1_000 * Math.pow(2, reconnectAttempt) + Math.random() * 1_000, 30_000);
          reconnectAttempt++;
          reconnectTimeout = setTimeout(connect, delay);
        };

        socket.onerror = () => {
          setConnectionStatus('error');
          socket.close();
        };

      } catch (err) {
        console.error('WebSocket connection failed:', err);
        setConnectionStatus('error');
        // Fall back to polling
        fetchData();
      }
    };

    connect();

    return () => {
      destroyed = true;
      clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  }, [wsUrl, fetchData]);


  // Auto-refresh polling
  useEffect(() => {
    if (!autoRefresh || !apiUrl) return;

    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchData, apiUrl]);

  // Initial fetch
  useEffect(() => {
    if (!wsUrl) fetchData();
  }, [fetchData, wsUrl]);

  // Handler (formerly handleRefresh)
  const refresh = () => {
    setLoading(true);
    fetchData();
  };

  return {
    data,
    loading,
    error,
    connectionStatus,
    lastUpdated,
    autoRefresh,
    setAutoRefresh,
    refresh,
  };
}
