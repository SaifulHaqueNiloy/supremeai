import { getWebSocketBaseUrl } from '../../utils/api';
import { BaseWebSocketManager, BaseWebSocketManagerOptions, WsStatus } from '@supremeai/shared-services';

// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Command Center — WebSocket Manager
// বাংলা মন্তব্য: heartbeat, reconnect, exponential backoff — একটিই WS connection
// ═══════════════════════════════════════════════════════════════════════════

export { WsStatus };

interface WsManagerOptions extends BaseWebSocketManagerOptions {
  onStatusChange: (status: WsStatus) => void;
  onEvent: (type: string, payload: unknown) => void;
  onError: (error: Error) => void;
}

export class WebSocketManager extends BaseWebSocketManager {
  private options: WsManagerOptions;

  // বাংলা: পেলোড ডিফিং — ২s ডেল্টা, ৩০s ফুল স্ন্যাপশট
  private snapshotCache = new Map<string, unknown>();
  private lastSnapshotTime = new Map<string, number>();
  private STALE_THRESHOLD_MS = 35_000;
  private queryInvalidate?: () => void;

  constructor(options: WsManagerOptions) {
    super({
      ...options,
      heartbeatIntervalMs: 30_000,
      maxReconnectAttempts: 5,
      reconnectBaseDelayMs: 1_000,
    });
    this.options = options;
  }

  setQueryInvalidate(fn: () => void) {
    this.queryInvalidate = fn;
  }

  protected getUrl(): string {
    const rawToken = localStorage.getItem('supreme_admin_jwt');
    if (!rawToken) {
      throw new Error('No admin token available for WS connection');
    }
    const baseUrl = getWebSocketBaseUrl();
    return `${baseUrl}/ws/dashboard?token=${encodeURIComponent(rawToken)}`;
  }

  protected setStatus(status: WsStatus) {
    if (this.status !== status) {
      super.setStatus(status);
      this.options.onStatusChange(status);
    }
  }

  protected onOpen(event: Event): void {
    super.onOpen(event);
  }

  protected onMessage(event: MessageEvent): void {
    super.onMessage(event);
    try {
      const data = JSON.parse(event.data);
      if (data.type) {
        this.applyPayload(data.type, data.payload ?? data);
      }
    } catch (err) {
      this.options.onError(new Error(`Failed to parse WS message: ${err}`));
    }
  }

  protected onClose(event: CloseEvent): void {
    super.onClose(event);
  }

  protected onError(event: Event): void {
    super.onError(event);
    this.options.onError(new Error('WebSocket connection error'));
  }

  protected scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.options.onError(new Error('Max WS reconnect attempts reached'));
      return;
    }
    const delay = this.reconnectBaseDelayMs * Math.pow(2, this.reconnectAttempts);
    this.options.onError(new Error(`WS reconnect attempt ${this.reconnectAttempts + 1} in ${delay}ms`));
    super.scheduleReconnect();
  }

  protected openSocket(): void {
    try {
      super.openSocket();
    } catch (err) {
      this.options.onError(err instanceof Error ? err : new Error(String(err)));
    }
  }

  private applyPayload(type: string, payload: unknown) {
    const p = payload as { channel?: string; patch?: Record<string, unknown>; data?: unknown; mode?: 'delta' | 'snapshot' };
    if (!p?.channel) {
      this.options.onEvent(type, payload);
      return;
    }

    if (p.mode === 'delta' && p.patch) {
      const existing = (this.snapshotCache.get(p.channel) ?? {}) as Record<string, unknown>;
      const merged = { ...existing, ...p.patch };
      this.snapshotCache.set(p.channel, merged);
      this.options.onEvent(type, merged);
    } else {
      // full snapshot
      this.snapshotCache.set(p.channel, p.data ?? payload);
      this.lastSnapshotTime.set(p.channel, Date.now());
      this.options.onEvent(type, p.data ?? payload);
    }

    // stale guard
    this.guardStale(p.channel);
  }

  private guardStale(channel: string) {
    const last = this.lastSnapshotTime.get(channel);
    if (!last) return;
    if (Date.now() - last > this.STALE_THRESHOLD_MS) {
      this.queryInvalidate?.();
    }
  }
}
