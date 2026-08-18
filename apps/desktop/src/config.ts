// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Desktop Studio — Backend connection config
// বাংলা মন্তব্য: ব্যাকএন্ড বেস URL — build-time/env override সাপোর্ট করে
// (ওয়েব client-এর VITE_ADMIN_BACKEND-এর সাথে সামঞ্জস্যপূর্ণ default)
// ═══════════════════════════════════════════════════════════════════════════

export const BACKEND_URL: string =
  import.meta.env.VITE_BACKEND_URL || 'https://supremeai-backend-docker.onrender.com';

export const getApiBaseUrl = (): string => BACKEND_URL;

export const getWebSocketBaseUrl = (): string => {
  if (BACKEND_URL.startsWith('https://')) return 'wss://' + BACKEND_URL.slice('https://'.length);
  if (BACKEND_URL.startsWith('http://')) return 'ws://' + BACKEND_URL.slice('http://'.length);
  return BACKEND_URL;
};
