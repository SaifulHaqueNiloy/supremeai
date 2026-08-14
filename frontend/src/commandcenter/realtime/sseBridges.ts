import { getApiBaseUrl } from '../../utils/api';

// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Command Center — SSE Bridges
// বাংলা মন্তব্য: logs/stream ও dashboard_events — WS-এ না এনে আলাদা EventSource
// ═══════════════════════════════════════════════════════════════════════════

export interface SseBridgeOptions {
  onLog: (log: unknown) => void;
  onEvent: (event: unknown) => void;
  onError: (error: Error) => void;
}

export class SseBridges {
  private logSource: EventSource | null = null;
  private eventSource: EventSource | null = null;
  private options: SseBridgeOptions;

  constructor(options: SseBridgeOptions) {
    this.options = options;
  }

  connect() {
    const rawToken = localStorage.getItem('supreme_admin_jwt');
    if (!rawToken) return;

    const baseUrl = getApiBaseUrl();
    const tokenParam = encodeURIComponent(rawToken);

    // Logs stream (high frequency)
    this.logSource = new EventSource(`${baseUrl}/admin-api/logs/stream?token=${tokenParam}`);
    this.logSource.onmessage = (e) => {
      try {
        this.options.onLog(JSON.parse(e.data));
      } catch (err) {
        this.options.onError(new Error(`Failed to parse log stream: ${err}`));
      }
    };
    this.logSource.onerror = () => {
      this.options.onError(new Error('Log stream SSE connection error'));
    };

    // Dashboard events
    this.eventSource = new EventSource(`${baseUrl}/admin-api/events/stream?token=${tokenParam}`);
    this.eventSource.addEventListener('dashboard_events', (e) => {
      try {
        this.options.onEvent(JSON.parse(e.data));
      } catch (err) {
        this.options.onError(new Error(`Failed to parse dashboard events: ${err}`));
      }
    });
    this.eventSource.onerror = () => {
      this.options.onError(new Error('Dashboard events SSE connection error'));
    };
  }

  disconnect() {
    this.logSource?.close();
    this.logSource = null;
    this.eventSource?.close();
    this.eventSource = null;
  }
}