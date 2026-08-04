import { getWebSocketBaseUrl } from '../../utils/api';

// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Command Center — WebSocket Manager
// বাংলা মন্তব্য: heartbeat, reconnect, exponential backoff — একটিই WS connection
// ═══════════════════════════════════════════════════════════════════════════

export type WsStatus = 'connecting' | 'open' | 'closed' | 'error';

interface WsManagerOptions {
  onStatusChange: (status: WsStatus) => void;
  onEvent: (type: string, payload: unknown) => void;
  onError: (error: Error) => void;
}

const HEARTBEAT_INTERVAL = 30_000;
const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY = 1_000;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private status: WsStatus = 'closed';
  private reconnectAttempts = 0;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;
  private options: WsManagerOptions;

  constructor(options: WsManagerOptions) {
    this.options = options;
  }

  connect() {
    this.shouldReconnect = true;
    this.open();
  }

  disconnect() {
    this.shouldReconnect = false;
    this.clearTimers();
    this.ws?.close();
    this.ws = null;
    this.setStatus('closed');
  }

  private open() {
    try {
      const rawToken = localStorage.getItem('supreme_admin_jwt');
      if (!rawToken) {
        this.setStatus('error');
        this.options.onError(new Error('No admin token available for WS connection'));
        return;
      }

      const baseUrl = getWebSocketBaseUrl();
      const wsUrl = `${baseUrl}/ws/dashboard?token=${encodeURIComponent(rawToken)}`;
      this.ws = new WebSocket(wsUrl);
      this.setStatus('connecting');

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.setStatus('open');
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type) {
            this.options.onEvent(data.type, data.payload ?? data);
          }
        } catch (err) {
          this.options.onError(new Error(`Failed to parse WS message: ${err}`));
        }
      };

      this.ws.onclose = () => {
        this.stopHeartbeat();
        this.setStatus('closed');
        if (this.shouldReconnect) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (event) => {
        this.setStatus('error');
        this.options.onError(new Error('WebSocket connection error'));
      };
    } catch (err) {
      this.setStatus('error');
      this.options.onError(err instanceof Error ? err : new Error(String(err)));
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      this.options.onError(new Error('Max WS reconnect attempts reached'));
      return;
    }

    const delay = BASE_RECONNECT_DELAY * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    this.options.onError(new Error(`WS reconnect attempt ${this.reconnectAttempts} in ${delay}ms`));

    this.reconnectTimer = setTimeout(() => {
      this.open();
    }, delay);
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, HEARTBEAT_INTERVAL);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private clearTimers() {
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private setStatus(status: WsStatus) {
    if (this.status !== status) {
      this.status = status;
      this.options.onStatusChange(status);
    }
  }

  getStatus(): WsStatus {
    return this.status;
  }
}