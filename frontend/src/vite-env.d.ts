/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  readonly VITE_API_URL?: string;
  readonly VITE_BACKEND_URL?: string;
  readonly VITE_USER_BACKEND?: string;
  readonly VITE_WORKER_URL?: string;
  readonly VITE_ECOSYSTEM_API_URL?: string;
  readonly NEXT_PUBLIC_API_URL?: string;
  readonly NEXT_PUBLIC_DASHBOARD_WS_URL?: string;
  readonly VITE_DASHBOARD_WS_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare const __APP_BUILD_TIME__: string;
