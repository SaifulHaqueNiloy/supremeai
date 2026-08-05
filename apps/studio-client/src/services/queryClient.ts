import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: unknown) => {
        const err = error as Record<string, unknown>;
        const msg = (err.message as string) || '';
        const status = err.status as number | undefined;
        if (
          status === 401 || status === 403 || status === 429 ||
          msg.includes('401') || msg.includes('403') || msg.includes('429') ||
          msg.includes('Rate limit') || msg.includes('Unauthorized')
        ) return false;
        return failureCount < 2;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex + Math.random() * 500, 15000),
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});
