// apps/studio-client/src/lib/apiClient.ts
// Resilient API Gateway with Axios Interceptor Pattern
// বাংলা মন্তব্য: এই এপিআই ক্লায়েন্ট ফ্রন্টএন্ডকে আমাদের ব্যাকএন্ডের ErrorEventBus এবং Middleware-এর সাথে সুরক্ষিতভাবে কানেক্ট করে।

import axios, { AxiosError } from 'axios';
import { useWorkspaceStore } from '../store/useWorkspaceStore';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://api.supremeai.com/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Inject Auth & Traceability
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('supreme_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Create a unique trace ID for frontend-backend correlation
  const traceId = crypto.randomUUID();
  config.headers['X-Frontend-Trace-ID'] = traceId;

  return config;
});

// Response Interceptor: Autonomous Error Handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // Auto-logout on token expiration
    if (error.response?.status === 401) {
      useWorkspaceStore.getState().logout();
      window.location.href = '/login';
      return Promise.reject(error);
    }

    // Capture backend correlation ID for debugging
    const correlationId = error.response?.headers['x-correlation-id'] || 'unknown';

    console.error(`[API Failure] Trace: ${correlationId}`, error.response?.data);

    // Trigger global UI error state without crashing the app
    useWorkspaceStore.getState().addNotification({
      type: 'error',
      message: (error.response?.data as any)?.detail || 'An autonomous system error occurred.',
      correlationId
    });

    return Promise.reject(error);
  }
);
