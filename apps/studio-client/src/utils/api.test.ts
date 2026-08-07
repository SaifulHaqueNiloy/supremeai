import { describe, it, expect, beforeEach } from 'vitest';
import { RENDER_BACKENDS, switchActiveBackend, getApiBaseUrl, getWebSocketBaseUrl } from './api';

// বাংলা মন্তব্য: import.meta.env টাইপ-লেভেলে readonly, তাই টেস্টে mutable ভিউ ব্যবহার করা হচ্ছে
const env = import.meta.env as unknown as Record<string, unknown>;

describe('api.ts', () => {
  beforeEach(() => {
    sessionStorage.clear();
    delete env.VITE_API_BASE;
    delete env.VITE_API_URL;
    delete env.VITE_WS_BASE_URL;
    delete env.VITE_PRIMARY_BACKEND;
    delete env.VITE_SECONDARY_BACKEND;
    delete env.PROD;
  });

  describe('switchActiveBackend', () => {
    it('toggles between backends', () => {
      const first = switchActiveBackend();
      const second = switchActiveBackend();
      expect(first).not.toBe(second);
    });

    it('returns same backend after two toggles', () => {
      const first = switchActiveBackend();
      switchActiveBackend();
      const third = switchActiveBackend();
      expect(first).toBe(third);
    });
  });

  describe('getApiBaseUrl', () => {
    it('returns primary backend in production when no env vars set', () => {
      env.PROD = true;
      expect(getApiBaseUrl()).toBe(RENDER_BACKENDS[0]);
    });

    it('returns default primary backend when no env and not production', () => {
      expect(getApiBaseUrl()).toBe(RENDER_BACKENDS[0]);
    });

    it('prefers VITE_API_BASE over VITE_API_URL', () => {
      env.VITE_API_BASE = 'https://api.example.com';
      env.VITE_API_URL = 'https://fallback.example.com';
      expect(getApiBaseUrl()).toBe('https://api.example.com');
    });

    it('returns VITE_API_URL when VITE_API_BASE is not set', () => {
      env.VITE_API_URL = 'https://fallback.example.com';
      expect(getApiBaseUrl()).toBe('https://fallback.example.com');
    });

    it('returns cached backend from sessionStorage', () => {
      sessionStorage.setItem('supremeai_active_backend', 'https://cached.example.com');
      expect(getApiBaseUrl()).toBe('https://cached.example.com');
    });
  });

  describe('getWebSocketBaseUrl', () => {
    it('returns env var when set', () => {
      env.VITE_WS_BASE_URL = 'wss://ws.example.com';
      expect(getWebSocketBaseUrl()).toBe('wss://ws.example.com');
    });

    it('converts cached https backend to wss in production', () => {
      env.PROD = true;
      sessionStorage.setItem('supremeai_active_backend', 'https://api.example.com');
      expect(getWebSocketBaseUrl()).toBe('wss://api.example.com');
    });

    it('falls back to default render backend wss protocol when no env and not production', () => {
      expect(getWebSocketBaseUrl()).toBe('wss://supremeai-backend.onrender.com');
    });
  });
});
