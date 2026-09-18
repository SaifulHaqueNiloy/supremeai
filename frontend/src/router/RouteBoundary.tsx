// RouteBoundary — per-route error isolation (Wave 3)
// বাংলা মন্তব্য: আগে non-admin route-এ কোনো কম্পোনেন্ট ক্র্যাশ করলে root-level
// boundary পুরো অ্যাপ আনমাউন্ট করত (nav shell সহ)। admin shell যেমন per-tab
// isolation (AdminSubTabContent) ব্যবহার করে, user route-ও এখন route-scope
// boundary পায় — শুধু ক্র্যাশ করা পেজটাই fallback দেখায়, বাকি অ্যাপ অক্ষত।
//
// GlobalErrorBoundary (main.tsx) এর স্টাইলেই class component + telemetry post;
// তবে fallback কমপ্যাক্ট (WorkspaceLayout-এর ভেতরে বসে) এবং recovery দুইভাবে:
// "Try again" (boundary state reset — একই route remount) + "Go home" (navigate)।
// কোনো ভুয়া status code বা ভুয়া "report sent" দাবি নেই — শুধু সত্যি message।

import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, Home, RefreshCcw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getApiBaseUrl } from '../utils/api';

interface RouteBoundaryProps {
  children?: ReactNode;
}

interface RouteBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/** Compact fallback (function component — useNavigate হুক শুধু এখানেই দরকার)। */
function RouteErrorFallback({
  error,
  onReset,
}: {
  error: Error;
  onReset: () => void;
}) {
  const navigate = useNavigate();
  return (
    <div
      role="alert"
      data-testid="route-error-fallback"
      className="flex min-h-[50vh] items-center justify-center p-6 text-[var(--sa-ink)]"
    >
      <div className="sa-surface-raised w-full max-w-md rounded-[var(--sa-radius-sm)] border border-red-500/30 p-8 text-center">
        <div className="mx-auto mb-5 inline-flex size-12 items-center justify-center rounded-full bg-red-500/10">
          <AlertTriangle className="size-6 text-red-400" aria-hidden="true" />
        </div>
        <h2 className="text-lg font-semibold">This page hit an unexpected error</h2>
        <p className="mt-2 text-sm text-[var(--sa-ink-muted)]">
          The rest of the workspace is still intact. You can retry this page or
          go back home.
        </p>
        {import.meta.env.DEV && (
          <pre className="mt-4 max-h-32 overflow-auto rounded-[var(--sa-radius-sm)] border border-[var(--sa-border)] bg-[var(--sa-canvas)] p-3 text-left font-mono text-xs text-red-400">
            {error.message}
          </pre>
        )}
        <div className="mt-6 flex flex-col items-center justify-center gap-2 sm:flex-row">
          <button
            type="button"
            data-testid="route-error-retry"
            onClick={onReset}
            className="inline-flex items-center justify-center gap-2 rounded-[var(--sa-radius-sm)] bg-[var(--sa-primary)] px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
          >
            <RefreshCcw size={14} />
            Try again
          </button>
          <button
            type="button"
            data-testid="route-error-home"
            onClick={() => navigate('/')}
            className="inline-flex items-center justify-center gap-2 rounded-[var(--sa-radius-sm)] border border-[var(--sa-border)] px-4 py-2.5 text-sm font-semibold transition hover:border-[var(--sa-primary)]"
          >
            <Home size={14} />
            Go home
          </button>
        </div>
      </div>
    </div>
  );
}

export class RouteBoundary extends Component<RouteBoundaryProps, RouteBoundaryState> {
  public state: RouteBoundaryState = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): RouteBoundaryState {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // বাংলা: GlobalErrorBoundary-র মতোই একই telemetry চ্যানেল — শুধু module
    // নাম আলাদা, যাতে route-scope ক্র্যাশ root ক্র্যাশ থেকে আলাদা হয়ে গোনা যায়।
    console.error('[RouteBoundary] Uncaught error:', error, errorInfo);

    try {
      fetch(`${getApiBaseUrl()}/api/telemetry/frontend-error`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          module: 'frontend_route_error_boundary',
          error_type: error.name,
          message: error.message.slice(0, 500),
          stack: (error.stack || '').slice(0, 2000),
          component_stack: (errorInfo.componentStack || '').slice(0, 2000),
          url: window.location.href,
          severity: 'ERROR',
        }),
        keepalive: true,
      }).catch((telemetryError) => {
        console.warn('[telemetry] Failed to report route error:', telemetryError);
      });
    } catch (reportError) {
      console.warn('[RouteBoundary] Error reporting telemetry failed:', reportError);
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError && this.state.error) {
      return (
        <RouteErrorFallback error={this.state.error} onReset={this.handleReset} />
      );
    }
    return this.props.children;
  }
}
