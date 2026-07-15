import { getApiBaseUrl } from './api';

export function setupGlobalFetchInterceptor() {
  if (typeof window === 'undefined') return;

  const originalFetch = window.fetch;

  window.fetch = async function (...args) {
    const url = args[0];
    let options: any = args[1];
    const apiBase = getApiBaseUrl();

    if (typeof url === 'string' && url.startsWith(apiBase)) {
      options = options || {};
      // Ensure cookies are sent with every cross-origin API request
      options.credentials = 'include';
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

         let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
         try {
           const clone = response.clone();
           const text = await clone.text();
           if (text) {
              const parsed = JSON.parse(text);
              if (parsed.error) errorMsg = parsed.error;
              else if (parsed.message) errorMsg = parsed.message;
              else if (parsed.detail) errorMsg = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
              else errorMsg = text.slice(0, 50);
           }
         } catch (e) {
           // ignore parsing error
         }

         if ((window as any).showGlobalToast) {
           (window as any).showGlobalToast('error', errorMsg);
         }
       }

       return response;
     } catch (error) {
      if ((window as any).showGlobalToast) {
        (window as any).showGlobalToast('error', `Network Error: ${error instanceof Error ? error.message : 'Unknown'}`);
      }
      throw error;
    }
  };
}
