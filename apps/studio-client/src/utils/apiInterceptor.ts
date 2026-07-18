import { getApiBaseUrl } from './api';

export function setupGlobalFetchInterceptor() {
  if (typeof window === 'undefined') return;

  const originalFetch = window.fetch;

  window.fetch = async function (...args) {
    const url = args[0];
    let options: RequestInit = args[1] || {};
    const apiBase = getApiBaseUrl();

    if (typeof url === 'string' && url.startsWith(apiBase)) {
      // Ensure cookies are sent with every cross-origin API request
      options = { ...options, credentials: 'include' };
      args[1] = options;
    }

    try {
      const response = await originalFetch.apply(this, args);

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          // Handle unauthorized access globally
          import('../store/adminStore').then(({ useAdminStore }) => {
            const store = useAdminStore.getState();
            if (store.adminAuthenticated) {
              store.handleAdminLogout();
            }
          });
        }

        const contentType = response.headers.get('content-type');
        let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
        
        // 🛡️ অডিটর ফিক্স: সাইলেন্ট কমেন্ট রিমুভ করে মালফর্মড বডি ভ্যালিডেশন
        if (contentType && contentType.includes('application/json')) {
          try {
            const clone = response.clone();
            const text = await clone.text();
            if (text) {
              const parsed = JSON.parse(text);
              if (parsed.error) errorMsg = parsed.error;
              else if (parsed.message) errorMsg = parsed.message;
              else if (parsed.detail) errorMsg = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
            }
          } catch (parseError: any) {
            // Structured error logging for malformed JSON
            console.error('🚨 [INTERCEPTOR_PARSING_CRASH]: Body claimed JSON but failed to decode.', parseError);
            errorMsg = 'Malformed JSON response packet received from SupremeAI core backend.';
          }
        } else {
          // Non-JSON response: graceful text handling
          const text = await response.text();
          console.debug('ℹ️ [NON_JSON_STREAM_TRAFFIC]: Handling streaming or text matrix payload.', { length: text.length });
          errorMsg = text.slice(0, 100);
        }

        if ((window as any).showGlobalToast) {
          (window as any).showGlobalToast('error', errorMsg);
        }
      }

      return response;
    } catch (error: any) {
      if ((window as any).showGlobalToast) {
        (window as any).showGlobalToast('error', `Network Error: ${error?.message || 'Unknown'}`);
      }
      throw error;
    }
  };
}
