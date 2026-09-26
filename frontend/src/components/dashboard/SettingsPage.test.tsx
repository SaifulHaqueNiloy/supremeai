import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { SettingsPage } from './SettingsPage';
import { connectionsApi } from '../../services/connectionsApi';
import { apiClient } from '../../services/apiClient';

vi.mock('../../services/apiClient', () => ({
  apiClient: {
    get: vi.fn().mockImplementation((path: string) => {
      if (path.includes('/preferences/')) {
        return Promise.resolve({
          theme: 'dark',
          default_model: 'gpt-4o',
          max_tokens: 4096,
          auto_save: true,
          verbosity: 'normal',
        });
      }
      if (path.includes('/admin/trusted-browsers')) {
        return Promise.resolve({ browsers: [] });
      }
      return Promise.resolve({});
    }),
    post: vi.fn().mockResolvedValue({}),
    delete: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock('../../services/connectionsApi', () => ({
  connectionsApi: {
    getMyWorkspace: vi.fn().mockResolvedValue({
      userId: 'test-user',
      executionMode: 'ask_before_acting',
      capabilities: [],
      connections: [],
      authorizedContexts: [],
      recentActivity: [],
    }),
    setExecutionMode: vi.fn().mockResolvedValue({
      user_id: 'test-user',
      mode: 'autonomous',
      persisted: true,
      message: 'Execution mode updated to autonomous',
    }),
  },
}));

describe('SettingsPage - Execution Mode integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all three execution modes with labels', async () => {
    render(<SettingsPage theme="dark" toggleTheme={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Execution Mode')).toBeInTheDocument();
    });

    expect(screen.getByTestId('execution-mode-read_only')).toBeInTheDocument();
    expect(screen.getByTestId('execution-mode-ask_before_acting')).toBeInTheDocument();
    expect(screen.getByTestId('execution-mode-autonomous')).toBeInTheDocument();
  });

  it('loads the active execution mode from workspace', async () => {
    vi.mocked(connectionsApi.getMyWorkspace).mockResolvedValueOnce({
      userId: 'test-user',
      executionMode: 'read_only',
      capabilities: [],
      connections: [],
      authorizedContexts: [],
      recentActivity: [],
    });

    render(<SettingsPage theme="dark" toggleTheme={vi.fn()} />);

    await waitFor(() => {
      const readOnlyRadio = screen.getByRole('radio', { name: /read only/i });
      expect(readOnlyRadio).toBeChecked();
    });
  });

  it('calls setExecutionMode when a new mode is selected', async () => {
    render(<SettingsPage theme="dark" toggleTheme={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Execution Mode')).toBeInTheDocument();
    });

    const autonomousRadio = screen.getByRole('radio', { name: /autonomous/i });
    fireEvent.click(autonomousRadio);

    await waitFor(() => {
      expect(connectionsApi.setExecutionMode).toHaveBeenCalledWith('autonomous');
    });

    await waitFor(() => {
      expect(screen.getByTestId('execution-mode-status')).toHaveTextContent(
        'Execution mode updated to autonomous',
      );
    });
  });
});

// Issue #1819: the backend serves trusted-browser management at BOTH
// '/api/admin/trusted-browsers' (alias added for the frontend) and the legacy
// '/admin/trusted-browsers'. Before #1819 only the unprefixed path existed, so
// the Settings card was silently dead (the 404 was swallowed into an empty
// list). These tests lock the exact frontend contract so the coupling to the
// backend alias cannot regress in either direction.
describe('SettingsPage - trusted-browsers API contract (#1819)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path.includes('/preferences/')) {
        return Promise.resolve({
          theme: 'dark',
          default_model: 'gpt-4o',
          max_tokens: 4096,
          auto_save: true,
          verbosity: 'normal',
        });
      }
      if (path.includes('/admin/trusted-browsers')) {
        return Promise.resolve({
          browsers: [{ id: 'browser-abc', created_at: 1758840000 }],
        });
      }
      return Promise.resolve({});
    });
    vi.mocked(apiClient.delete).mockResolvedValue({ ok: true } as never);
  });

  it('loads the list from the /api-prefixed alias path (not the unprefixed one)', async () => {
    render(<SettingsPage theme="dark" toggleTheme={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Browser authorized/)).toBeInTheDocument();
    });

    const loadPaths = vi
      .mocked(apiClient.get)
      .mock.calls.map((call) => call[0] as string)
      .filter((p) => p.includes('/admin/trusted-browsers'));
    expect(loadPaths).toEqual(['/api/admin/trusted-browsers']);
  });

  it('revokes a single browser via the aliased path with the encoded id', async () => {
    render(<SettingsPage theme="dark" toggleTheme={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Browser authorized/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Revoke browser' }));

    await waitFor(() => {
      expect(apiClient.delete).toHaveBeenCalledWith('/api/admin/trusted-browsers/browser-abc');
    });
    expect(screen.getByTestId('trusted-browsers-status')).toHaveTextContent('Browser revoked.');
  });

  it('revokes all browsers via the aliased collection path', async () => {
    render(<SettingsPage theme="dark" toggleTheme={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('Revoke all')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Revoke all'));

    await waitFor(() => {
      expect(apiClient.delete).toHaveBeenCalledWith('/api/admin/trusted-browsers');
    });
    expect(screen.getByTestId('trusted-browsers-status')).toHaveTextContent(
      'All trusted browsers revoked.',
    );
  });
});
