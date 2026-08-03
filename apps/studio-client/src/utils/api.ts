// বাংলা মন্তব্য: প্রধান অ্যাকাউন্টের লিমিট শেষ হওয়ায় ব্যাকআপ ইউআরএলটি এখন প্রাইমারি হিসেবে ব্যবহার করা হচ্ছে।
export const RENDER_BACKENDS = [
  import.meta.env.VITE_PRIMARY_BACKEND || 'https://supremeai-backend.onrender.com', // Primary (Backup account active service)
  import.meta.env.VITE_SECONDARY_BACKEND || 'https://supremeai-backend-65hl.onrender.com' // Fallback (New image service)
];

export const switchActiveBackend = (): string => {
  const current = sessionStorage.getItem('supremeai_active_backend') || RENDER_BACKENDS[0];
  const next = current === RENDER_BACKENDS[0] ? RENDER_BACKENDS[1] : RENDER_BACKENDS[0];
  sessionStorage.setItem('supremeai_active_backend', next);
  console.error(`[Failover] Switched backend to: ${next}`);
  return next;
};

export const getApiBaseUrl = (): string => {
  if (typeof window === 'undefined') {
    const url = import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_URL;
    if (!url && import.meta.env.PROD) throw new Error("API URL missing in production");
    return url || RENDER_BACKENDS[0];
  }

  const cached = sessionStorage.getItem('supremeai_active_backend');
  if (cached) return cached;

  if (import.meta.env.VITE_API_BASE) {
    return import.meta.env.VITE_API_BASE;
  }

  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  if (import.meta.env.PROD) {
    return RENDER_BACKENDS[0];
  }
  return window.location.origin;
};

export const getWebSocketBaseUrl = (): string => {
  if (typeof window === 'undefined') {
    const url = import.meta.env.VITE_WS_BASE_URL;
    if (!url && import.meta.env.PROD) throw new Error("WS URL missing in production");
    return url || RENDER_BACKENDS[0].replace(/^http/, 'ws');
  }

  if (import.meta.env.VITE_WS_BASE_URL) {
    return import.meta.env.VITE_WS_BASE_URL;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

  // If in production, use the active backend domain for WebSockets
  if (import.meta.env.PROD) {
    const apiBase = getApiBaseUrl();
    if (apiBase.startsWith('http')) {
      return apiBase.replace(/^http/, 'ws');
    }
  }

  return `${protocol}//${window.location.host}`;
};
