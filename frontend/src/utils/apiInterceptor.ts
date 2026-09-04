// apps/studio-client/src/utils/apiInterceptor.ts
// 🛡️ Production-ready API interceptor with structured error handling

export const apiInterceptor = async <T = unknown>(response: Response): Promise<T> => {
  const contentType = response.headers.get("content-type");

  if (!response.ok) {
    throw new Error(`API Transport Failed. Status: ${response.status}`);
  }

  // 🛡️ অডিটর ফিক্স: সাইলেন্ট কমেন্ট রিমুভ করে মালফর্মড বডি ভ্যালিডেশন
  if (contentType && contentType.includes("application/json")) {
    try {
      return (await response.json()) as T;
    } catch (parseError: unknown) {
      const errorMsg = parseError instanceof Error ? parseError.message : String(parseError);
      console.error("🚨 [INTERCEPTOR_PARSING_CRASH]: Body claimed JSON but failed to decode.", errorMsg);
      throw new Error("Malformed JSON response packet received from SupremeAI core backend.");
    }
  }

  // স্ট্রিম বা প্লেইন টেক্সট মেসেজের জন্য সেফ গ্রেসফুল ফলব্যাক
  const rawText = await response.text();
  console.warn("ℹ️ [NON_JSON_STREAM_TRAFFIC]: Handling streaming or text matrix payload.", { length: rawText.length });
  return rawText as unknown as T;
};

// Legacy support: Keep existing fetch interceptor for backward compatibility
export function setupGlobalFetchInterceptor() {
  if (typeof window === 'undefined') return;

  const originalFetch = window.fetch;

  window.fetch = async function (...args) {
    const url = args[0];
    let options: RequestInit | undefined = args[1] as RequestInit;
    const apiBase = (await import('./api')).getApiBaseUrl();

    if (typeof url === 'string' && url.startsWith(apiBase)) {
      options = options || {};
      options.credentials = 'include';
      args[1] = options;
    }

    try {
      const response = await originalFetch.apply(this, args);

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          // 🔥 ফিক্স: logout endpoint নিজে 401 দিলে recursive loop এ না যেতে guard
          // 🔥 ROOT-CAUSE FIX: এই wrapper গ্লোবালি সব fetch (background queries, SSE stream
          // সহ) ইন্টারসেপ্ট করে। আগে যেকোনো একটা non-critical/background রিকোয়েস্ট
          // (যেমন /api/memory/checkpoints, /api/skills/search, /api/task/stream — SSE)
          // থেকে ক্ষণস্থায়ী 401 (cold start, Redis blip, রেসিং রিকোয়েস্ট) আসলেই পুরো
          // অ্যাডমিন সেশন logout হয়ে যেত — এই কারণেই TOTP verify সফল হওয়ার পরপরই
          // ড্যাশবোর্ড auto-refresh হয়ে লগআউট হয়ে যাচ্ছিল। এখন শুধুমাত্র "critical" এন্ডপয়েন্ট
          // (সরাসরি ইউজার-উদ্যোগে করা অ্যাডমিন অ্যাকশন কল) থেকে 401/403 এলেই logout ট্রিগার হবে;
          // ব্যাকগ্রাউন্ড/নন-ক্রিটিক্যাল কলগুলো নিজেরাই তাদের error handle করবে।
          const NON_CRITICAL_401_PATHS = [
            '/api/memory/checkpoints',
            '/api/skills/search',
            '/api/task/stream',
          ];
          const isNonCritical =
            typeof url === 'string' && NON_CRITICAL_401_PATHS.some((p) => url.includes(p));

          if (typeof url === 'string' && url.includes('/api/admin/logout')) {
            console.warn('[Interceptor] Logout endpoint returned 401 — user already logged out, skipping auto-logout.');
          } else if (isNonCritical) {
            console.warn(`[Interceptor] Non-critical endpoint returned ${response.status} — ignoring for session state:`, url);
          } else {
            import('../store/adminStore').then(({ useAdminStore }) => {
              const store = useAdminStore.getState();
              if (store.adminAuthenticated) {
                store.handleAdminLogout();
              }
            });
          }
        }

        let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
        try {
          const clone = response.clone();
          const text = await clone.text();
          if (text) {
            const parsed = JSON.parse(text);
            // বাংলা মন্তব্য: React #31 crash রোধ — backend/Google-স্টাইল `{code,message,errors}` envelope
            // যদি object হয় তাহলে সেটাকে সর্বদা string-এ রূপান্তর করবো, যেন toast/render-এ
            // "Objects are not valid as a React child (found: object with keys {code,message,errors})" না ঘটে।
            const toMsgString = (v: unknown): string | null =>
              typeof v === 'string'
                ? v
                : v && typeof v === 'object'
                  ? JSON.stringify(v)
                  : v === undefined || v === null
                    ? null
                    : String(v);
            errorMsg =
              toMsgString(parsed.error) ??
              toMsgString(parsed.message) ??
              toMsgString(parsed.detail) ??
              text.slice(0, 50);
          }
        } catch (e) {
          console.error('🚨 [INTERCEPTOR_ERROR]: Failed to parse error response', e);
        }

        const isPublicHealthProbe = typeof url === 'string' && url.includes('/api/health-aggregation');
        const isBackgroundRequest = typeof url === 'string' && (
          isPublicHealthProbe ||
          url.includes('/api/config') ||
          url.includes('/api/health')
        );
        const win = window as unknown as { showGlobalToast?: (type: string, msg: string) => void };
        if (win.showGlobalToast && !isBackgroundRequest) {
          win.showGlobalToast('error', errorMsg);
        }
      }

      return response;
    } catch (error) {
      const win = window as unknown as { showGlobalToast?: (type: string, msg: string) => void };
      // বাংলা মন্তব্য: AbortError (timeout বা signal abort) হলে raw মেসেজ ("signal is aborted without reason")
      // ইউজারকে না দেখিয়ে নীরবে caller-কে throw করব; GlobalConfigInitializer নিজেই fallback দেখাবে।
      const isAbort = error instanceof Error &&
        (error.name === 'AbortError' || error.message.includes('aborted') || error.message.includes('aborted without reason'));
      const isBackgroundRequest = typeof url === 'string' && (
        url.includes('/api/health-aggregation') ||
        url.includes('/api/config') ||
        url.includes('/api/health')
      );
      if (!isAbort && win.showGlobalToast && !isBackgroundRequest) {
        win.showGlobalToast('error', `Network Error: ${error instanceof Error ? error.message : 'Unknown'}`);
      }
      throw error;
    }
  };
}
