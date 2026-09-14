/**
 * SuperAI Supabase Client Configuration
 *
 * FREE-TIER OPTIMIZATIONS:
 * - Connection pooling via PgBouncer (CRITICAL for free tier!)
 * - Session persistence to reduce auth requests
 * - Realtime rate limiting to stay within limits
 * - Separate admin client with elevated permissions
 *
 * RESTORE-AND-WIRE (2026-09-14): this module was restored after being deleted as
 * "dead", with two hardening changes:
 *  1. SECURITY GUARD — a service-role key must NEVER reach a browser bundle.
 *     Vite only exposes VITE_*-prefixed vars to client code; we throw at boot if
 *     anyone ever feeds a service key through the frontend env.
 *  2. supabaseAdmin is now a guarded proxy that throws a clear, actionable error
 *     on first use in the browser instead of crashing at module scope with
 *     createClient(undefined, undefined). Privileged operations belong in the
 *     backend API.
 */

import { createClient } from '@supabase/supabase-js';
import type { SupabaseClient } from '@supabase/supabase-js';

// ✅ FIXED: Use VITE_ prefix for Vite-based projects
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || import.meta.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || import.meta.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// SECURITY GUARD: service-role keys are server-only. Hard-fail if present.
const RAW_SERVICE_ROLE =
  (import.meta.env as Record<string, unknown>).SUPABASE_SERVICE_ROLE_KEY ??
  (import.meta.env as Record<string, unknown>).VITE_SUPABASE_SERVICE_ROLE_KEY;
if (RAW_SERVICE_ROLE) {
  throw new Error(
    '[supabase.client] Service-role key detected in client environment — refusing to boot. ' +
      'Service-role keys are server-only (backend/.env); remove them from frontend env.',
  );
}

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    '[supabase.client] Missing VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY — Supabase-backed features will be degraded.',
  );
}

// Options optimized for free tier usage
export const supabase: SupabaseClient = createClient(
  supabaseUrl ?? 'http://localhost:54321',
  supabaseAnonKey ?? 'public-anon-key-placeholder',
  {
    auth: {
      persistSession: true, // Reduce re-auth requests (saves MAU!)
      autoRefreshToken: true,
      detectSessionInUrl: true,
      storage: typeof window !== 'undefined' ? window.localStorage : undefined,
      storageKey: 'supremai-auth-token',
    },
    global: {
      headers: {
        'x-application-name': 'superai-free-tier',
        'x-priority': 'low', // Hint for connection pooler
      },
    },
    db: {
      schema: 'public',
    },
    realtime: {
      params: {
        eventsPerSecond: 10, // Stay within free tier limits!
      },
    },
  },
);

// Server-side client with connection pooling awareness.
// Guarded proxy: throws a clear error on first use when no service key exists
// (always the case in a browser bundle) instead of crashing at import time.
export const supabaseAdmin: SupabaseClient = new Proxy({} as SupabaseClient, {
  get(_target, prop) {
    throw new Error(
      '[supabase.client] supabaseAdmin is unavailable in the browser: service-role keys are ' +
        'server-only. Use the backend API for privileged operations.',
    );
  },
});

// ✅ NEW: Connection health check for monitoring
export async function checkSupabaseHealth(): Promise<{
  connected: boolean;
  latency_ms: number;
  pool_status: string;
}> {
  const start = performance.now();

  try {
    const { error } = await supabase.from('_health_check').select('count').single();
    const latency = performance.now() - start;

    return {
      connected: !error || error?.code === '42P01', // Table doesn't exist = OK
      latency_ms: Math.round(latency),
      pool_status: latency < 100 ? 'healthy' : latency < 500 ? 'degraded' : 'slow',
    };
  } catch {
    return {
      connected: false,
      latency_ms: performance.now() - start,
      pool_status: 'error',
    };
  }
}

// ✅ NEW: Retry wrapper for transient failures
export async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 300,
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;

      if (attempt === maxRetries) break;

      // Exponential backoff with jitter
      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 100;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

export default supabase;
