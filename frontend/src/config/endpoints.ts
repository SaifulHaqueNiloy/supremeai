let userBackend = 'https://supremeai-backend-docker.onrender.com';
let adminBackend = 'https://supremeai-backend-docker.onrender.com';

try {
  // Browser context (Vite statically replaces these)
  userBackend = import.meta.env.VITE_USER_BACKEND || import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_URL || userBackend;
  adminBackend = import.meta.env.VITE_ADMIN_BACKEND || adminBackend;
} catch (e) {
  // Node context (vite.config.ts)
  if (typeof process !== 'undefined' && process.env) {
    userBackend = process.env.VITE_USER_BACKEND || process.env.VITE_API_BASE || process.env.VITE_API_URL || userBackend;
    adminBackend = process.env.VITE_ADMIN_BACKEND || adminBackend;
  }
}

export const ENDPOINTS = {
  userBackend,
  adminBackend,
} as const;
