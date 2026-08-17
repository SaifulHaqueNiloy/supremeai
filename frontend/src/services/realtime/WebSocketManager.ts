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
}

export default class WebSocketManager {
  private url: string;
  private handlers: WebSocketManagerHandlers;
  private maxReconnectAttempts: number;
  private reconnectBaseDelayMs: number;
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private manuallyClosed = false;

  constructor(url: string, options: WebSocketManagerOptions = {}) {
    this.url = url;
    const { maxReconnectAttempts, reconnectBaseDelayMs, ...handlers } = options;
    this.handlers = handlers;
    this.maxReconnectAttempts = maxReconnectAttempts ?? 5;
    this.reconnectBaseDelayMs = reconnectBaseDelayMs ?? 1000;
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
      this.handlers.onMessage?.(event);
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
    this.socket?.close();
    this.socket = null;
  }
}
