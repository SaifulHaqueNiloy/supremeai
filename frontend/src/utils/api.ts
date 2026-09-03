// 🔧 DYNAMIC CONFIG: No fallback hardcoded URLs - Fail-Fast in production

// 🔬 Evolution v3.0: Enhanced API client with Retry + Circuit Breaker
// বাংলা মন্ত্য: Portal-ভিত্তিক একক backend নির্ধারণ — কোনো cross-portal failover নয়।

/**
 * 🔬 Circuit Breaker States for Frontend
 * CLOSED → Normal, OPEN → Failing, HALF_OPEN → Testing
 */
type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

interface CircuitBreakerConfig {
  name: string;
  failureThreshold: number;   // Failures before OPEN
  recoveryTimeoutMs: number;  // ms before HALF_OPEN attempt
}

class FrontendCircuitBreaker {
  private state: CircuitState = 'CLOSED';
  private failures = 0;
  private lastFailureTime = 0;
  private readonly config: CircuitBreakerConfig;

  constructor(config: CircuitBreakerConfig) {
    this.config = config;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    // Check if we should try recovery
    if (this.state === 'OPEN') {
      const elapsed = Date.now() - this.lastFailureTime;
      if (elapsed >= this.config.recoveryTimeoutMs) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error(`Circuit '${this.config.name}' is OPEN. Retry in ~${Math.ceil((this.config.recoveryTimeoutMs - elapsed) / 1000)}s`);
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    if (this.state === 'HALF_OPEN') {
      this.state = 'CLOSED';
    }
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();
    if (this.failures >= this.config.failureThreshold) {
      this.state = 'OPEN';
      console.warn(`⚡ Circuit '${this.config.name}' opened after ${this.failures} failures`);
    }
  }

  getState(): CircuitState { return this.state; }
  getRecoveryTimeMs(): number {
    if (this.state !== 'OPEN') return 0;
    return Math.max(0, this.config.recoveryTimeoutMs - (Date.now() - this.lastFailureTime));
  }
}

// Pre-configured circuits
const apiCircuit = new FrontendCircuitBreaker({
  name: 'api_backend',
  failureThreshold: parseInt(import.meta.env.VITE_CIRCUIT_FAILURE_THRESHOLD || '5'),
  recoveryTimeoutMs: parseInt(import.meta.env.VITE_CIRCUIT_RECOVERY_MS || '30000'),
});

const wsCircuit = new FrontendCircuitBreaker({
  name: 'websocket',
  failureThreshold: 3,
  recoveryTimeoutMs: 15000,
});

/**
 * 🔬 Retry Configuration
 */
interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryableStatuses: number[];
}

const DEFAULT_RETRY: RetryConfig = {
  maxRetries: parseInt(import.meta.env.VITE_MAX_RETRIES || '3'),
  baseDelayMs: 500,
  maxDelayMs: 5000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function calculateBackoff(attempt: number, config: RetryConfig): number {
  // Exponential backoff with jitter
  const delay = Math.min(config.baseDelayMs * Math.pow(2, attempt), config.maxDelayMs);
  return delay + Math.random() * 200; // Jitter
}

/**
 * 🔬 Enhanced fetchWithRetry with Circuit Breaker integration
 */
export async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retryConfig: Partial<RetryConfig> = {}
): Promise<Response> {
  const config = { ...DEFAULT_RETRY, ...retryConfig };
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      // Circuit breaker protection
      const response = await apiCircuit.execute(() => fetch(url, options));

      // Don't retry on success or non-retryable codes
      if (!config.retryableStatuses.includes(response.status)) {
        return response;
      }

      // Retry on rate-limit or server errors
      console.warn(`⚠️ Attempt ${attempt + 1}/${config.maxRetries + 1}: ${response.status} ${url}`);
      lastError = new Error(`HTTP ${response.status}`);

    } catch (error) {
      lastError = error as Error;
      console.warn(`⚠️ Attempt ${attempt + 1}/${config.maxRetries + 1}:`, error);
    }

    // Wait before retry (except after last attempt)
    if (attempt < config.maxRetries) {
      const delay = calculateBackoff(attempt, config);
      await sleep(delay);
    }
  }

  throw lastError || new Error('All retries exhausted');
}// বাংলা (single-frontend migration, roadmap Phase 1/7): VITE_PORTAL_TYPE সরানো হয়েছে।
// এক বিল্ডে User + Admin দুই context-ই থাকে, তাই backend নির্বাচন এখন RUNTIME সিদ্ধান্ত:
//  - '/admin-api' path অথবা /admin/* route context → admin backend (থাকলে)
//  - বাকি সব → user backend
// Firebase hosting external rewrite proxy সাপোর্ট করে না, তাই Firebase-এ সরাসরি backend URL ব্যবহার হয় (CORS allow)।
// Vercel-এ relative path ('') রাখা হয় কারণ Vercel external rewrite proxy সাপোর্ট করে।

/** User-context API calls-এর canonical backend URL (build-time resolved, runtime-picked) */
export const USER_BACKEND_URL: string =
  import.meta.env.VITE_USER_BACKEND ||
  import.meta.env.VITE_API_BASE ||
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_BACKEND_URL || '';

/** Admin-context API calls-এর canonical backend URL (build-time resolved, runtime-picked) */
export const ADMIN_BACKEND_URL: string =
  import.meta.env.VITE_ADMIN_BACKEND || USER_BACKEND_URL;

// 🔬 Export circuits for monitoring
export const circuits = { api: apiCircuit, websocket: wsCircuit };
export type { CircuitState };

// 🔒 RUNTIME VALIDATION - Missing backend = Error in production.
if ((import.meta.env.PROD) && !USER_BACKEND_URL) {
  throw new Error('❌ VITE_API_URL or VITE_BACKEND_URL is required in production. Set it in .env');
}

/**
 * বাংলা: এই call টি admin-context কিনা — path prefix (per-call) অথবা
 * current route context (/admin/*) দেখে নির্ধারিত হয়। Env var দিয়ে নয়।
 */
export function isAdminContextPath(path?: string): boolean {
  if (path && (path.startsWith('/admin-api') || path.startsWith('/api/admin'))) return true;
  if (typeof window !== 'undefined' && window.location.pathname.startsWith('/admin')) return true;
  return false;
}

/**
 * বাংলা: runtime backend URL নির্বাচন — কোনো build-time portal identity নেই।
 * @param path API call-এর path (যেমন '/admin-api/deploy') — থাকলে per-call precision
 */
export function getBackendUrl(path?: string): string {
  if (isAdminContextPath(path) && ADMIN_BACKEND_URL) return ADMIN_BACKEND_URL;
  return USER_BACKEND_URL || ADMIN_BACKEND_URL;
}

/**
 * @deprecated বাংলা: পুরোনো portal-pinned constant — শুধু backward compatibility।
 * নতুন কোডে getBackendUrl(path) / getApiBaseUrl(path) ব্যবহার করুন।
 */
export const BACKEND_URL: string = USER_BACKEND_URL;

export const getApiBaseUrl = (path?: string): string => {
  if (typeof window === 'undefined') {
    // বাংলা মন্তব্য: SSR/Node.js কনটেক্সটে সরাসরি backend URL
    const backend = getBackendUrl(path);
    if (!backend && import.meta.env.PROD) throw new Error('API URL missing in production');
    return backend;
  }

  // 🔧 DYNAMIC: Configure via explicit VITE_USE_RELATIVE_PATH boolean flag
  if (import.meta.env.VITE_USE_RELATIVE_PATH === 'true') {
    return '';
  }

  // Firebase, Vercel ও বাকি সব হোস্টে সরাসর��� backend URL — runtime context অনুযায়ী

  // Firebase ও বাকি হোস্টে (local dev ইত্যাদি) সরাসররি backend URL — runtime context অনুযায়ী
  return getBackendUrl(path);
};

/**
 * 🔬 Evolution v3.0: Health check for backend connectivity
 */
export async function checkBackendHealth(): Promise<{
  healthy: boolean;
  latency?: number;
  error?: string;
}> {
  const start = performance.now();
  try {
    const response = await fetchWithRetry(`${getApiBaseUrl()}/api/v1/health/live`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    return {
      healthy: response.ok,
      latency: Math.round(performance.now() - start),
    };
  } catch (error) {
    return {
      healthy: false,
      latency: Math.round(performance.now() - start),
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

export const getWsBaseUrl = (): string => getWebSocketBaseUrl();

export const getWebSocketBaseUrl = (): string => {
  // বাংলা মন্তব্য: এক্সপ্লিসিট override সবার আগে
  if (import.meta.env.VITE_WS_BASE_URL) {
    return import.meta.env.VITE_WS_BASE_URL;
  }

  // বাংলা (single-frontend migration): runtime context-aware backend
  const backendUrl = getBackendUrl();
  const apiBase = getApiBaseUrl();

  // 🔥 ফিক্স: Firebase hosting-এ apiBase === '' (relative path)।
  // WebSocket Firebase rewrite proxy দিয়ে যায় না — সরাসরি Render-এর wss:// URL ব্যবহার করতে হবে।
  if (apiBase === '') {
    return backendUrl.replace(/^https:\/\//, 'wss://');
  }

  if (apiBase.startsWith('https://')) {
    return apiBase.replace(/^https:\/\//, 'wss://');
  }
  if (apiBase.startsWith('http://')) {
    return apiBase.replace(/^http:\/\//, 'ws://');
  }

  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = typeof window !== 'undefined' ? window.location.host : (backendUrl ? backendUrl.replace(/^https?:\/\//, '') : 'localhost:8000');
  if (typeof window === 'undefined' && import.meta.env.PROD && !backendUrl) {
    throw new Error('❌ Backend URL is required in production SSR.');
  }
  return `${protocol}//${host}`;
};
