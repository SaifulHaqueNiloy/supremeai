/**
 * SuperAI Shared Configuration
 * ==============================
 * Secure environment-based configuration with type safety.
 * 
 * @version 3.0.0 (SuperAI Patch)
 */

type EnvConfig = {
  BACKEND_URL: string;
  WS_URL: string;
  APP_NAME: string;
  ENABLE_ANALYTICS: boolean;
  CACHE_ENABLED: boolean;
  RATE_LIMIT_DISPLAY: boolean;
};

/**
 * Get environment variable with validation and fallback.
 * Throws descriptive error in development if required vars missing.
 */
function getEnvVar(key: string, fallback?: string): string {
  const value = import.meta.env[`VITE_${key}`];
  if (!value && !fallback && import.meta.env.DEV) {
    console.warn(`⚠️ Missing VITE_${key} in .env file`);
  }
  return value || fallback || '';
}

const getProdBackendUrl = () => {
  const url = import.meta.env.VITE_BACKEND_URL || import.meta.env.VITE_API_URL || import.meta.env.VITE_USER_BACKEND;
  if (import.meta.env.PROD && !url) {
    throw new Error('❌ VITE_BACKEND_URL or VITE_API_URL must be set in production.');
  }
  return url || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://localhost:8000');
};

export const CONFIG: EnvConfig = {
  // Backend API URL - use env var or detect automatically
  BACKEND_URL: getEnvVar('BACKEND_URL', getProdBackendUrl()),
  
  // WebSocket URL - derive from backend URL
  WS_URL: getEnvVar('WS_URL', getProdBackendUrl().replace(/^http/, 'ws') + '/ws'),
  
  // Application identity
  APP_NAME: getEnvVar('APP_NAME', 'SuperAI'),
  
  // Feature flags
  ENABLE_ANALYTICS: getEnvVar('ENABLE_ANALYTICS', 'false') === 'true',
  CACHE_ENABLED: getEnvVar('CACHE_ENABLED', 'true') === 'true',
  RATE_LIMIT_DISPLAY: getEnvVar('RATE_LIMIT_DISPLAY', 'true') === 'true',
};

// Backward compatibility exports
export const BACKEND_URL = CONFIG.BACKEND_URL;
export const WS_URL = CONFIG.WS_URL;
export const APP_NAME = CONFIG.APP_NAME;

/**
 * Validate configuration on import
 */
if (import.meta.env.DEV) {
  console.warn('🔧 SuperAI Config:', {
    backend: CONFIG.BACKEND_URL,
    ws: CONFIG.WS_URL,
    features: {
      analytics: CONFIG.ENABLE_ANALYTICS,
      cache: CONFIG.CACHE_ENABLED,
    }
  });
}
