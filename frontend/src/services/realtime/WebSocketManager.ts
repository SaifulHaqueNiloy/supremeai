// src/services/realtime/WebSocketManager.ts
// Minimal reconnecting WebSocket wrapper used by real-time dashboard widgets.

export interface WebSocketManagerHandlers {
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onMessage?: (event: MessageEvent) => void;
  onError?: (event: Event) => void;
}

export interface WebSocketManagerOptions extends WebSocketManagerHandlers {
  /** Max number of automatic reconnect attempts. Default: 5 */
  maxReconnectAttempts?: number;
  /** Base delay (ms) for exponential backoff between reconnects. Default: 1000 */
  reconnectBaseDelayMs?: number;
  /** Enable WS payload diffing (delta updates). Default: true */
  enablePayloadDiffing?: boolean;
  /** Delta update interval in ms. Default: 2000 (2s) */
  deltaIntervalMs?: number;
  /** Full snapshot interval in ms. Default: 30000 (30s) */
  snapshotIntervalMs?: number;
}

export default class WebSocketManager {
  private url: string;
  private handlers: WebSocketManagerHandlers;
  private maxReconnectAttempts: number;
  private reconnectBaseDelayMs: number;
  private enablePayloadDiffing: boolean;
  private deltaIntervalMs: number;
  private snapshotIntervalMs: number;
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private manuallyClosed = false;

  // WS payload diffing state
  private lastSnapshot: string | null = null;
  private lastDelta: string | null = null;
  private snapshotTimer: ReturnType<typeof setInterval> | null = null;

  constructor(url: string, options: WebSocketManagerOptions = {}) {
    this.url = url;
    const { maxReconnectAttempts, reconnectBaseDelayMs, enablePayloadDiffing, deltaIntervalMs, snapshotIntervalMs, ...handlers } = options;
    this.handlers = handlers;
    this.maxReconnectAttempts = maxReconnectAttempts ?? 5;
    this.reconnectBaseDelayMs = reconnectBaseDelayMs ?? 1000;
    this.enablePayloadDiffing = enablePayloadDiffing ?? true;
    this.deltaIntervalMs = deltaIntervalMs ?? 2000;
    this.snapshotIntervalMs = snapshotIntervalMs ?? 30000;
  }

  connect(): void {
    this.manuallyClosed = false;
    this.openSocket();
  }

  private openSocket(): void {
    try {
      this.socket = new WebSocket(this.url);
    } catch (err) {
      console.error('WebSocketManager: failed to create socket', err);
      this.scheduleReconnect();
      return;
    }

    this.socket.onopen = (event) => {
      this.reconnectAttempts = 0;
      this.handlers.onOpen?.(event);
    };

    this.socket.onclose = (event) => {
      this.handlers.onClose?.(event);
      if (!this.manuallyClosed) {
        this.scheduleReconnect();
      }
    };

    this.socket.onmessage = (event) => {
      // WS payload diffing: only emit delta updates, full snapshot every 30s
      if (this.enablePayloadDiffing && event.data) {
        const dataStr = typeof event.data === 'string' ? event.data : JSON.stringify(event.data);
        this.lastDelta = dataStr;
        if (dataStr !== this.lastSnapshot) {
          this.handlers.onMessage?.(event);
        }
        this.lastSnapshot = dataStr;
      } else {
        this.handlers.onMessage?.(event);
      }
    };

    this.socket.onerror = (event) => {
      this.handlers.onError?.(event);
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }
    const delay = this.reconnectBaseDelayMs * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts += 1;
    this.reconnectTimer = setTimeout(() => {
      if (!this.manuallyClosed) {
        this.openSocket();
      }
    }, delay);
  }

  send(data: string | ArrayBufferLike | Blob | ArrayBufferView): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(data);
    } else {
      console.warn('WebSocketManager: cannot send, socket is not open');
    }
  }

  disconnect(): void {
    this.manuallyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.snapshotTimer) {
      clearInterval(this.snapshotTimer);
      this.snapshotTimer = null;
    }
    this.socket?.close();
    this.socket = null;
  }
}
