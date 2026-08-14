import React from 'react';

interface Props {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class DashboardErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('Dashboard Error Boundary caught an error:', error, errorInfo);
  }

  resetError = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): React.ReactNode {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultFallback;
      return <FallbackComponent error={this.state.error!} resetError={this.resetError} />;
    }

    return this.props.children;
  }
}

interface FallbackProps {
  error: Error;
  resetError: () => void;
}

const DefaultFallback: React.FC<FallbackProps> = ({ error, resetError }) => {
  return (
    <div className="error-boundary-container" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '200px',
      padding: '2rem',
      backgroundColor: '#fff5f5',
      borderRadius: '0.5rem',
      border: '1px solid #fecaca',
      textAlign: 'center'
    }}>
      <h2 style={{ color: '#dc2626', marginBottom: '1rem' }}>Something went wrong</h2>
      <p style={{ color: '#6b7280', marginBottom: '1rem' }}>{error?.message || 'An unexpected error occurred'}</p>
      <button
        onClick={resetError}
        style={{
          backgroundColor: '#3b82f6',
          color: 'white',
          border: 'none',
          padding: '0.5rem 1rem',
          borderRadius: '0.375rem',
          cursor: 'pointer'
        }}
      >
        Try Again
      </button>
    </div>
  );
};

export default DashboardErrorBoundary;
