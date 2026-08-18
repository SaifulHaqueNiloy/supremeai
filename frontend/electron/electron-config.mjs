/**
 * electron-config.mjs — SupremeAI Desktop (Electron) Live Backend Resolution
 * ============================================================================
 * বাংলা: এই মডিউলটি main process-এর জন্য portal-aware লাইভ backend URL নির্ধারণ করে।
 * এটি `frontend/vite.config.ts` ও `frontend/src/utils/api.ts`-এ ব্যবহৃত একই precedence
 * মিরর করে, যাতে Desktop (main process + IPC) এবং Renderer (React app) কখনোই
 * ভিন্ন backend টার্গেটে কথা না বলে (zero architectural drift)।
 */

/** Admin portal-এর default backend (api.ts:8-এর সাথে অভিন্ন)। */
export const DEFAULT_ADMIN_BACKEND_URL = 'https://supremeai-backend-docker.onrender.com';

/** User portal-এর default backend (api.ts:15-এর সাথে অভিন্ন)। */
export const DEFAULT_USER_BACKEND_URL = 'https://supremeai-backend-docker.onrender.com';

/** Local Vite dev server (electron:dev)। */
export const DEV_SERVER_URL = 'http://127.0.0.1:5173';

/**
 * VITE_PORTAL_TYPE-এর ভিত্তিতে portal type নির্ধারণ — 'admin' ছাড়া সবকিছু user।
 * api.ts: `VITE_PORTAL_TYPE === 'admin' ? ADMIN : USER` — identical।
 */
export function resolvePortalType(env = process.env) {
  return env?.VITE_PORTAL_TYPE === 'admin' ? 'admin' : 'user';
}

/**
 * Portal-specific canonical backend URL (trailing slash stripped)।
 * Precedence (api.ts ও vite.config.ts-এর সাথে identical):
 *   admin: VITE_ADMIN_BACKEND                          → DEFAULT_ADMIN_BACKEND_URL
 *   user:  VITE_USER_BACKEND → VITE_API_BASE → VITE_API_URL → DEFAULT_USER_BACKEND_URL
 */
export function resolveBackendUrl(env = process.env, portalType = resolvePortalType(env)) {
  let url;
  if (portalType === 'admin') {
    url = env?.VITE_ADMIN_BACKEND || DEFAULT_ADMIN_BACKEND_URL;
  } else {
    url = env?.VITE_USER_BACKEND || env?.VITE_API_BASE || env?.VITE_API_URL || DEFAULT_USER_BACKEND_URL;
  }
  return String(url).replace(/\/+$/, '');
}

/**
 * HTTPS API base-কে WSS base-এ রূপান্তর (api.ts getWebSocketBaseUrl-এর mirror)।
 */
export function toWebSocketBaseUrl(apiBaseUrl) {
  if (apiBaseUrl.startsWith('https://')) return apiBaseUrl.replace(/^https:\/\//, 'wss://');
  if (apiBaseUrl.startsWith('http://')) return apiBaseUrl.replace(/^http:\/\//, 'ws://');
  return `wss://${apiBaseUrl}`;
}

/**
 * এক কলেই পুরো runtime config: portalType + apiBaseUrl + wsBaseUrl।
 * main.js-এর বাইরে এই pure ফাংশন unit-testable (vitest/node --test)।
 */
export function resolveRuntimeConfig(env = process.env) {
  const portalType = resolvePortalType(env);
  const apiBaseUrl = resolveBackendUrl(env, portalType);
  const wsBaseUrl = toWebSocketBaseUrl(apiBaseUrl);
  return { portalType, apiBaseUrl, wsBaseUrl };
}