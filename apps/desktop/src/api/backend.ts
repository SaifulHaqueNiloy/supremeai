// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Desktop Studio — Backend API client (thin client)
// বাংলা মন্তব্য: থিন ক্লায়েন্ট — শুধু /health REST + /dashboard WebSocket
// (endpoint গুলো backend/api/routes/health.py ও realtime_dashboard.py থেকে নেওয়া)
// ═══════════════════════════════════════════════════════════════════════════

import { BACKEND_URL, getWebSocketBaseUrl } from '../config';

export interface HealthStatus {
  status?: string;
  service?: string;
  version?: string;
  [key: string]: unknown;
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthStatus> {
  const res = await fetch(`${BACKEND_URL}/api/v1/health`, { signal });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return (await res.json()) as HealthStatus;
}

export type WsStatus = 'connecting' | 'open' | 'closed' | 'error';

export interface DashboardWsHandlers {
  onStatus?: (status: WsStatus) => void;
  onEvent?: (type: string, payload: unknown) => void;
  onError?: (err: Error) => void;
}

// বাংলা: ব্যাকএন্ড /dashboard WebSocket-এ কানেক্ট (token query param)
export function connectDashboardWs(token: string, handlers: DashboardWsHandlers): () => void {
  const ws = new WebSocket(`${getWebSocketBaseUrl()}/ws/dashboard?token=${encodeURIComponent(token)}`);
  ws.onopen = () => handlers.onStatus?.('open');
  ws.onclose = () => handlers.onStatus?.('closed');
  ws.onerror = () => handlers.onError?.(new Error('Dashboard WebSocket error'));
  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data as string);
      if (data && data.type) handlers.onEvent?.(data.type, data.payload ?? data);
    } catch {
      handlers.onError?.(new Error('Failed to parse dashboard WS message'));
    }
  };
  return () => ws.close();
}
