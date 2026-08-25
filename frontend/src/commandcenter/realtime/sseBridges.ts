import { getApiBaseUrl } from '../../utils/api';
import { createSecureEventSource } from '../../lib/secureSse';

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
  private logSource: { close: () => void } | null = null;
  private eventSource: { close: () => void } | null = null;
  private options: SseBridgeOptions;

  constructor(options: SseBridgeOptions) {
    this.options = options;
  }

  connect() {
    const rawToken = localStorage.getItem('supreme_admin_jwt');
    if (!rawToken) return;

    const baseUrl = getApiBaseUrl();

    // Logs stream (high frequency)
    this.logSource = createSecureEventSource(`${baseUrl}/admin-api/logs/stream`, rawToken, {
      onMessage: (e) => {
        try {
          this.options.onLog(JSON.parse(e.data));
        } catch (err) {
          this.options.onError(new Error(`Failed to parse log stream: ${err}`));
        }
      },
      onError: (err) => {
        this.options.onError(new Error(`Log stream SSE connection error: ${err}`));
      }
    });

    // Dashboard events
    this.eventSource = createSecureEventSource(`${baseUrl}/admin-api/events/stream`, rawToken, {
      onMessage: (e) => {
        if (e.type === 'dashboard_events') {
          try {
            this.options.onEvent(JSON.parse(e.data));
          } catch (err) {
            this.options.onError(new Error(`Failed to parse dashboard events: ${err}`));
          }
        }
      },
      onError: (err) => {
        this.options.onError(new Error(`Dashboard events SSE connection error: ${err}`));
      }
    });
  }

  disconnect() {
    this.logSource?.close();
    this.logSource = null;
    this.eventSource?.close();
    this.eventSource = null;
  }
}
