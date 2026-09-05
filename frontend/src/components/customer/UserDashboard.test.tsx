import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UserDashboard } from './UserDashboard';

const mockedUseNavigate = vi.fn();
const mockUseAuthStore = vi.fn();

vi.mock('react-router-dom', () => ({
  MemoryRouter: ({ children }: { children: React.ReactNode }) => children,
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => <a href={to}>{children}</a>,
  useNavigate: () => mockedUseNavigate,
}));

vi.mock('../../store/authStore', () => ({
  useAuthStore: () => mockUseAuthStore(),
}));

describe('UserDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuthStore.mockReturnValue({ user: { name: 'TestUser' } });
  });

  it('renders the calm intent-first workspace', () => {
    render(<MemoryRouter><UserDashboard /></MemoryRouter>);
    expect(screen.getByText('Good morning, TestUser.')).toBeInTheDocument();
    expect(screen.getByText('What should SupremeAI accomplish?')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Research, automate, analyze, or build...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /New conversation/i })).toBeInTheDocument();
  });

  it('uses a neutral greeting when no user name is available', () => {
    mockUseAuthStore.mockReturnValue({ user: null });
    render(<MemoryRouter><UserDashboard /></MemoryRouter>);
    expect(screen.getByText('Good morning, there.')).toBeInTheDocument();
  });

  it('opens Studio from the intent input', () => {
    render(<MemoryRouter><UserDashboard /></MemoryRouter>);
    const input = screen.getByPlaceholderText('Research, automate, analyze, or build...');
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(mockedUseNavigate).toHaveBeenCalledWith('/workspace/live');
  });

  it('does not open Studio for composing or unrelated keys', () => {
    render(<MemoryRouter><UserDashboard /></MemoryRouter>);
    const input = screen.getByPlaceholderText('Research, automate, analyze, or build...');
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(mockedUseNavigate).not.toHaveBeenCalled();
  });

  it('renders the main workspace sections and actions', () => {
    render(<MemoryRouter><UserDashboard /></MemoryRouter>);
    expect(screen.getByText('Recent work')).toBeInTheDocument();
    expect(screen.getByText('Active agents')).toBeInTheDocument();
    expect(screen.getByText('Workspace usage')).toBeInTheDocument();
    expect(screen.getByText('Support intelligence brief')).toBeInTheDocument();
    expect(screen.getByText('Review usage')).toBeInTheDocument();
  });
});
