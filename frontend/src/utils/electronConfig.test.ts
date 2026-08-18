import { describe, it, expect, beforeEach, afterEach } from 'vitest';

// বাংলা: main process-এর portal-aware backend resolution — vite.config.ts / api.ts-এর
// সাথে zero-drift নিশ্চিত করার unit test (pure module, electron import নেই)।
import {
  DEFAULT_ADMIN_BACKEND_URL,
  DEFAULT_USER_BACKEND_URL,
  DEV_SERVER_URL,
  resolvePortalType,
  resolveBackendUrl,
  resolveRuntimeConfig,
  toWebSocketBaseUrl,
} from '../../electron/electron-config.mjs';

const ORIGINAL_ENV = { ...process.env };

describe('electron-config.mjs — desktop live backend resolution', () => {
  beforeEach(() => {
    for (const k of Object.keys(process.env)) {
      if (k.startsWith('VITE_')) delete process.env[k];
    }
  });

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  describe('resolvePortalType', () => {
    it("'admin' হলে admin, অন্য সব user", () => {
      expect(resolvePortalType({ VITE_PORTAL_TYPE: 'admin' })).toBe('admin');
      expect(resolvePortalType({ VITE_PORTAL_TYPE: 'user' })).toBe('user');
      expect(resolvePortalType({})).toBe('user');
      expect(resolvePortalType(undefined)).toBe('user');
    });
  });

  describe('resolveBackendUrl', () => {
    it('user portal-এ default user backend ব্যবহার করে', () => {
      process.env.VITE_PORTAL_TYPE = 'user';
      expect(resolveBackendUrl(process.env)).toBe(DEFAULT_USER_BACKEND_URL);
    });

    it('admin portal-এ default admin backend ব্যবহার করে', () => {
      process.env.VITE_PORTAL_TYPE = 'admin';
      expect(resolveBackendUrl(process.env)).toBe(DEFAULT_ADMIN_BACKEND_URL);
    });

    it('VITE_ADMIN_BACKEND override admin portal-এ সম্মানিত হয়', () => {
      process.env.VITE_PORTAL_TYPE = 'admin';
      process.env.VITE_ADMIN_BACKEND = 'https://admin-override.example.com';
      expect(resolveBackendUrl(process.env)).toBe('https://admin-override.example.com');
    });

    it('VITE_USER_BACKEND override user portal-এ সম্মানিত হয়', () => {
      process.env.VITE_PORTAL_TYPE = 'user';
      process.env.VITE_USER_BACKEND = 'https://user-override.example.com';
      expect(resolveBackendUrl(process.env)).toBe('https://user-override.example.com');
    });

    it('user portal-এ VITE_API_BASE কে VITE_API_URL-এর আগে অগ্রাধিকার দেয় (api.ts-এর মতো)', () => {
      process.env.VITE_PORTAL_TYPE = 'user';
      process.env.VITE_API_BASE = 'https://base.example.com';
      process.env.VITE_API_URL = 'https://fallback.example.com';
      expect(resolveBackendUrl(process.env)).toBe('https://base.example.com');
    });

    it('trailing slash strip করে — vite proxy কনভেনশন', () => {
      process.env.VITE_PORTAL_TYPE = 'user';
      process.env.VITE_USER_BACKEND = 'https://user.example.com/';
      expect(resolveBackendUrl(process.env)).toBe('https://user.example.com');
    });
  });

  describe('toWebSocketBaseUrl', () => {
    it('https → wss রূপান্তর করে', () => {
      expect(toWebSocketBaseUrl('https://api.example.com')).toBe('wss://api.example.com');
    });
    it('http → ws রূপান্তর করে', () => {
      expect(toWebSocketBaseUrl('http://localhost:8000')).toBe('ws://localhost:8000');
    });
  });

  describe('resolveRuntimeConfig', () => {
    it('admin portal-এ REST + WS উভয় target রিটার্ন করে', () => {
      process.env.VITE_PORTAL_TYPE = 'admin';
      process.env.VITE_ADMIN_BACKEND = 'https://admin.example.com';
      const cfg = resolveRuntimeConfig(process.env);
      expect(cfg.portalType).toBe('admin');
      expect(cfg.apiBaseUrl).toBe('https://admin.example.com');
      expect(cfg.wsBaseUrl).toBe('wss://admin.example.com');
    });

    it('user portal-এ WS base WSS-এ রূপান্তরিত হয়', () => {
      process.env.VITE_PORTAL_TYPE = 'user';
      process.env.VITE_USER_BACKEND = 'https://user.example.com';
      const cfg = resolveRuntimeConfig(process.env);
      expect(cfg.wsBaseUrl).toBe('wss://user.example.com');
    });
  });

  describe('DEV_SERVER_URL', () => {
    it('electron:dev target হিসেবে localhost:5173 নির্দেশ করে', () => {
      expect(DEV_SERVER_URL).toBe('http://127.0.0.1:5173');
    });
  });
});