/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react-refresh/only-export-components */
/**
 * SuperAI Error Boundary Component
 * ==================================
 * Catches JavaScript errors anywhere in child component tree,
 * displays fallback UI instead of crashing whole app.
 *
 * @version 3.0.0 (SuperAI Patch)
 */

import React, { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorId: string;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = {
    hasError: false,
    error: null,
    errorId: '',
  };

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so next render shows fallback UI
    return {
      hasError: true,
      error,
      errorId: `err-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to reporting service
    console.error('🔥 ErrorBoundary caught:', error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Send to error tracking service (if configured)
    if (typeof window !== 'undefined' && (window as any).__SENTRY__) {
      (window as any).__SENTRY__.captureException(error, {
        contexts: { react: errorInfo },
      });
    }
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorId: '',
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div style={{
          padding: '2rem',
          textAlign: 'center',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚡</div>
          <h2>Something went wrong</h2>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            We apologize for the inconvenience. Our team has been notified.
          </p>
          {import.meta.env.DEV && (
            <details style={{
              textAlign: 'left',
              backgroundColor: '#f5f5f5',
              padding: '1rem',
              borderRadius: '8px',
              marginBottom: '1rem',
            }}>
              <summary style={{ cursor: 'pointer' }}>Error Details (Dev Only)</summary>
              <pre style={{
                fontSize: '0.85rem',
                overflow: 'auto',
                marginTop: '0.5rem',
              }}>
                {this.state.error?.stack || this.state.error?.message}
              </pre>
            </details>
          )}
          <p style={{ fontSize: '0.8rem', color: '#999', marginTop: '0.5rem' }}>
            Error ID: {this.state.errorId}
          </p>
          <button
            onClick={this.handleReset}
            style={{
              padding: '0.75rem 1.5rem',
              fontSize: '1rem',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook version for functional components
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    if (error) throw error;
  }, [error]);

  return setError;
}


