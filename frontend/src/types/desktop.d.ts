/**
 * Desktop (Electron) bridge types — preload.cjs-তে expose করা window.supremeDesktopAPI-র
 * TypeScript contract। Renderer-এর desktop-only কোড এগুলো typedভাবে ব্যবহার করতে পারে।
 */

export interface DesktopRuntimeConfig {
  /** VITE_PORTAL_TYPE — 'admin' ছাড়া সব user ('user') */
  portalType: 'admin' | 'user';
  /** Main process-এর resolved live REST backend (trailing slash ছাড়া) */
  apiBaseUrl: string;
  /** Main process-এর resolved live WebSocket base (wss://) */
  wsBaseUrl: string;
  version: string;
  platform: string;
  isDev: boolean;
}

export interface DesktopAppInfo {
  name: string;
  version: string;
  platform: string;
  isDev: boolean;
}

export interface DesktopApiCallResult {
  status: number;
  ok: boolean;
  data: unknown;
}

export interface SupremeDesktopAPI {
  minimizeWindow(): Promise<void>;
  maximizeWindow(): Promise<void>;
  closeWindow(): Promise<void>;
  getAppInfo(): Promise<DesktopAppInfo>;
  /** main process-এর runtime truth (portal-aware backend + WS target) */
  getRuntimeConfig(): Promise<DesktopRuntimeConfig>;
  getCurrentVersion(): Promise<string>;
  getSystemTheme(): Promise<'light' | 'dark'>;
  setTheme(theme: string): Promise<void>;
  apiCall(options: {
    endpoint: string;
    method?: string;
    body?: unknown;
    headers?: Record<string, string>;
  }): Promise<DesktopApiCallResult>;
  onMenuAction(callback: (action: string) => void): () => void;
}

declare global {
  interface Window {
    /** শুধুমাত্র Electron desktop রানটাইমে উপস্থিত; web build-এ absent (optional) */
    supremeDesktopAPI?: SupremeDesktopAPI;
  }
}

export {};