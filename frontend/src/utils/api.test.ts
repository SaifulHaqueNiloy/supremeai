import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// বাংলা মন্তব্য: api.ts এখন build-time constants (USER_BACKEND_URL ইত্যাদি) module-load-এ
// resolve করে। তাই প্রতিটি টেস্টে env সেট করার পর vi.resetModules() দিয়ে module পুনরায়
// import করা হচ্ছে।
// বাংলা (single-frontend migration): backend নির্বাচন এখন RUNTIME context-based —
// VITE_PORTAL_TYPE আর নেই। '/admin-api' path বা /admin/* location → admin backend;
// বাকি সব → user backend।
const env = import.meta.env as unknown as Record<string, unknown>;

const loadApi = async () => {
  vi.resetModules();
  return await import('./api');
};

const setLocation = (hostname: string, pathname = '/') => {
  // বাংলা মন্তব্য: jsdom-এ window.location রিডঅনলি, তাই defineProperty দিয়ে ওভাররাইড
  Object.defineProperty(window, 'location', {
    configurable: true,
    writable: true,
    value: { hostname, host: `${hostname}`, protocol: 'https:', pathname },
  });
};

const ORIGINAL_LOCATION = window.location;

describe('api.ts — runtime context-based backend resolution', () => {
  beforeEach(() => {
    delete env.VITE_API_BASE;
    delete env.VITE_API_URL;
    delete env.VITE_WS_BASE_URL;
    delete env.PROD;

    // বাংলা মন্তব্য: api.ts থেকে ডিফল্ট URL fallback মুছে ফেলায়, টেস্টের জন্য ডিফল্ট ভ্যালু সেট করতে হবে
    env.VITE_USER_BACKEND = 'https://api.test-domain.com';
    env.VITE_ADMIN_BACKEND = 'https://admin.test-domain.com';

    setLocation('localhost');
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      writable: true,
      value: ORIGINAL_LOCATION,
    });
  });

  describe('BACKEND_URL (deprecated alias)', () => {
    it('user backend-ই alias হিসেবে রিটার্ন করে', async () => {
      const { BACKEND_URL } = await loadApi();
      expect(BACKEND_URL).toBe('https://api.test-domain.com');
    });

    it('VITE_USER_BACKEND override সম্মান করে', async () => {
      env.VITE_USER_BACKEND = 'https://user-override.example.com';
      const { BACKEND_URL } = await loadApi();
      expect(BACKEND_URL).toBe('https://user-override.example.com');
    });

    it('VITE_API_BASE কে VITE_API_URL-এর চেয়ে অগ্রাধিকার দেয়', async () => {
      delete env.VITE_USER_BACKEND;
      env.VITE_API_BASE = 'https://api.example.com';
      env.VITE_API_URL = 'https://fallback.example.com';
      const { BACKEND_URL } = await loadApi();
      expect(BACKEND_URL).toBe('https://api.example.com');
    });
  });

  describe('getBackendUrl — runtime context selection', () => {
    it('user context (/workspace) এ user backend রিটার্ন করে', async () => {
      setLocation('localhost', '/workspace');
      const { getBackendUrl } = await loadApi();
      expect(getBackendUrl()).toBe('https://api.test-domain.com');
    });

    it('admin route context (/admin/*) এ admin backend রিটার্ন করে', async () => {
      setLocation('localhost', '/admin/overview');
      const { getBackendUrl } = await loadApi();
      expect(getBackendUrl()).toBe('https://admin.test-domain.com');
    });

    it('/admin-api path হলে per-call admin backend রিটার্ন করে (location যা-ই হোক)', async () => {
      setLocation('localhost', '/workspace');
      const { getBackendUrl } = await loadApi();
      expect(getBackendUrl('/admin-api/deploy')).toBe('https://admin.test-domain.com');
    });

    it('/api/admin path-ও admin backend-এ যায়', async () => {
      setLocation('localhost', '/workspace');
      const { getBackendUrl } = await loadApi();
      expect(getBackendUrl('/api/admin/firebase-login')).toBe('https://admin.test-domain.com');
    });

    it('admin backend unset হলে admin-context calls user backend-এ fall back করে', async () => {
      delete env.VITE_ADMIN_BACKEND;
      setLocation('localhost', '/admin/overview');
      const { getBackendUrl } = await loadApi();
      expect(getBackendUrl()).toBe('https://api.test-domain.com');
    });

    it('admin backend unset হলে user-context calls user backend রিটার্ন করে', async () => {
      delete env.VITE_ADMIN_BACKEND;
      setLocation('localhost', '/workspace');
      const { getBackendUrl } = await loadApi();
      expect(getBackendUrl()).toBe('https://api.test-domain.com');
    });

    it('VITE_ADMIN_BACKEND override সম্মান করে', async () => {
      env.VITE_ADMIN_BACKEND = 'https://admin-override.example.com';
      const { getBackendUrl } = await loadApi();
      expect(getBackendUrl('/admin-api/health-map')).toBe('https://admin-override.example.com');
    });
  });

  describe('cross-portal isolation', () => {
    it('switchActiveBackend export আর নেই (cross-portal failover সরানো হয়েছে)', async () => {
      const api = await loadApi();
      expect((api as Record<string, unknown>).switchActiveBackend).toBeUndefined();
    });
  });

  describe('getApiBaseUrl', () => {
    it('Firebase hosting (web.app)-এ সরাসরি backend URL রিটার্ন করে', async () => {
      setLocation('supremeai-a.web.app');
      const { getApiBaseUrl } = await loadApi();
      expect(getApiBaseUrl()).toBe('https://api.test-domain.com');
    });

    it('firebaseapp.com ডোমেইনেও সরাসরি backend URL রিটার্ন করে', async () => {
      setLocation('supremeai-a.firebaseapp.com');
      const { getApiBaseUrl } = await loadApi();
      expect(getApiBaseUrl()).toBe('https://api.test-domain.com');
    });

    it('Vercel ডোমেইনে relative path ("") রিটার্ন করে', async () => {
      setLocation('supremeai-lac.vercel.app');
      const { getApiBaseUrl } = await loadApi();
      expect(getApiBaseUrl()).toBe('');
    });
  });

  describe('getWebSocketBaseUrl', () => {
    it('VITE_WS_BASE_URL সেট থাকলে সেটিই রিটার্ন করে', async () => {
      env.VITE_WS_BASE_URL = 'wss://ws.example.com';
      const { getWebSocketBaseUrl } = await loadApi();
      expect(getWebSocketBaseUrl()).toBe('wss://ws.example.com');
    });

    it('Firebase hosting-এ user backend-এর direct wss রিটার্ন করে', async () => {
      setLocation('supremeai-a.web.app');
      const { getWebSocketBaseUrl } = await loadApi();
      expect(getWebSocketBaseUrl()).toBe('wss://api.test-domain.com');
    });

    it('Vercel ডোমেইনে relative path থেকে wss backend URL এ রূপান্তর করে', async () => {
      setLocation('supremeai-lac.vercel.app');
      const { getWebSocketBaseUrl } = await loadApi();
      expect(getWebSocketBaseUrl()).toBe('wss://api.test-domain.com');
    });
  });
});
