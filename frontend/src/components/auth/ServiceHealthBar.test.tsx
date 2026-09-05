import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { ServiceHealthBar } from './ServiceHealthBar';

vi.mock('../../utils/api', () => ({
  getApiBaseUrl: vi.fn(() => 'http://localhost:8080'),
}));

describe('ServiceHealthBar component', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    vi.clearAllMocks();
  });

  const renderComponent = (customClient?: QueryClient) =>
    render(
      <QueryClientProvider client={customClient || queryClient}>
        <ServiceHealthBar />
      </QueryClientProvider>
    );

  it('renders loading state initially', () => {
    global.fetch = vi.fn(() => new Promise(() => {})) as any;
    renderComponent();
    expect(screen.getByText('Connecting to Node...')).toBeInTheDocument();
  });

  it('renders healthy state when API succeeds', async () => {
    const mockData = {
      status: 'healthy',
      timestamp: Date.now(),
      total_response_time_ms: 35,
      checks: {
        application: { status: 'healthy', message: 'OK', response_time_ms: 12 },
        database: { status: 'healthy', message: 'OK', response_time_ms: 23 },
      },
      summary: {
        total_checks: 2,
        healthy: 2,
        degraded: 0,
        unhealthy: 0,
        unknown: 0,
      },
    };

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        headers: { get: () => 'application/json' },
        text: async () => JSON.stringify(mockData),
      })
    ) as any;

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Network Optimal')).toBeInTheDocument();
    });

    expect(screen.getByText('2/2')).toBeInTheDocument();

    // Click to toggle diagnostics modal
    const button = screen.getByTitle('Diagnostic Matrix (Click to toggle)');
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('System Telemetry')).toBeInTheDocument();
      expect(screen.getByText('Backend Core')).toBeInTheDocument();
      expect(screen.getByText('Data Store (Postgres)')).toBeInTheDocument();
    });
  });

  it('renders fallback label on error', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        url: 'http://localhost:8080/api/health-aggregation',
        headers: { get: () => 'application/json' },
        text: async () => 'Internal Error',
      })
    ) as any;

    const errorClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: 0,
        },
      },
    });

    renderComponent(errorClient);

    await waitFor(() => {
      expect(screen.getByText('Sync Pending')).toBeInTheDocument();
    });
  });
});

