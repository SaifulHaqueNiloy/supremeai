import { fetchEventSource } from '@microsoft/fetch-event-source';

export interface SecureSseOptions {
  onMessage?: (event: { data: string, type: string }) => void;
  onOpen?: () => void;
  onError?: (err: any) => void;
  onClose?: () => void;
}

export function createSecureEventSource(
  url: string,
  token: string | null | undefined,
  options: SecureSseOptions
) {
  const controller = new AbortController();

  fetchEventSource(url, {
    method: 'GET',
    headers: {
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    signal: controller.signal,
    onopen: async (response) => {
      if (response.ok) {
        options.onOpen?.();
      } else {
        const err = new Error(`Failed to connect to SSE: ${response.status}`);
        options.onError?.(err);
        throw err;
      }
    },
    onmessage: (msg) => {
      // Mock Event structure to match native EventSource signature
      options.onMessage?.({ data: msg.data, type: msg.event || 'message' });
    },
    onclose: () => {
      options.onClose?.();
    },
    onerror: (err) => {
      options.onError?.(err);
      // throw err will cause it to retry, return will stop
    },
  });

  return {
    close: () => {
      controller.abort();
    },
  };
}
