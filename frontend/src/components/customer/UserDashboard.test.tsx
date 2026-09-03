import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UserDashboard } from './UserDashboard';

const mockedUseNavigate = vi.fn();
const mockUseAuthStore = vi.fn();

vi.mock('react-router-dom', () => ({
  MemoryRouter: ({ children }: { children: React.ReactNode }) => children,
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to} data-testid="link">{children}</a>
  ),
  useNavigate: () => mockedUseNavigate,
}));

vi.mock('../../store/authStore', () => ({
  useAuthStore: () => mockUseAuthStore(),
}));

const renderDashboard = (user: { name: string } | null = { name: 'TestUser' }) => {
  mockUseAuthStore.mockReturnValue({ user });
  mockedUseNavigate.mockClear();
  return render(
    <MemoryRouter initialEntries={['/']}>
      <UserDashboard />
    </MemoryRouter>
  );
};

describe('UserDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders greeting with username', () => {
    renderDashboard({ name: 'TestUser' });
    expect(screen.getByText('Good morning, TestUser.')).toBeInTheDocument();
  });

  it('renders greeting without username when user has no username', () => {
    renderDashboard({ name: '' });
    expect(screen.getByText('Good morning.')).toBeInTheDocument();
  });

  it('renders greeting without username when user is null', () => {
    renderDashboard(null);
    expect(screen.getByText('Good morning.')).toBeInTheDocument();
  });

  it('renders subtitle text', () => {
    renderDashboard();
    expect(screen.getByText('What would you like to build today?')).toBeInTheDocument();
  });

  it('renders primary input with correct placeholder', () => {
    renderDashboard();
    expect(
      screen.getByPlaceholderText('Ask SupremeAI to generate, analyze, or deploy...')
    ).toBeInTheDocument();
  });

  it('navigates to workspace/live on Enter key in input', () => {
    renderDashboard();
    const input = screen.getByPlaceholderText('Ask SupremeAI to generate, analyze, or deploy...');
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(mockedUseNavigate).toHaveBeenCalledWith('/workspace/live');
  });

  it('does not navigate on non-Enter keys', () => {
    renderDashboard();
    const input = screen.getByPlaceholderText('Ask SupremeAI to generate, analyze, or deploy...');
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(mockedUseNavigate).not.toHaveBeenCalled();
  });

  it('renders the arrow right button', () => {
    renderDashboard();
    const inputContainer = screen.getByPlaceholderText('Ask SupremeAI to generate, analyze, or deploy...').closest('div');
    const arrowButton = inputContainer?.querySelector('button');
    expect(arrowButton).toBeInTheDocument();
  });

  it('renders all three quick action buttons', () => {
    renderDashboard();
    expect(screen.getByRole('button', { name: /New Project/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Generate App/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Deploy Service/i })).toBeInTheDocument();
  });

  it('renders the Continue Working section header', () => {
    renderDashboard();
    expect(screen.getByText('Continue Working')).toBeInTheDocument();
  });

  it('renders the View All link in Continue Working', () => {
    renderDashboard();
    const links = screen.getAllByTestId('link');
    const viewAllLink = links.find((l) => l.getAttribute('href') === '/projects');
    expect(viewAllLink).toBeInTheDocument();
    expect(viewAllLink).toHaveTextContent('View All');
  });

  it('renders both project cards in Continue Working', () => {
    renderDashboard();
    expect(screen.getByText('Ecommerce NextJS Agent')).toBeInTheDocument();
    expect(screen.getByText('Internal Analytics Dashboard')).toBeInTheDocument();
  });

  it('renders project card descriptions', () => {
    renderDashboard();
    expect(
      screen.getByText('Working on generating product catalog schema and API routes.')
    ).toBeInTheDocument();
    expect(screen.getByText('Data visualization components setup.')).toBeInTheDocument();
  });

  it('renders project card timestamps', () => {
    renderDashboard();
    expect(screen.getByText('2 hrs ago')).toBeInTheDocument();
    expect(screen.getByText('Yesterday')).toBeInTheDocument();
  });

  it('renders the Recent Conversations section header', () => {
    renderDashboard();
    expect(screen.getByText('Recent Conversations')).toBeInTheDocument();
  });

  it('renders the Go to Studio link in Recent Conversations', () => {
    renderDashboard();
    const links = screen.getAllByTestId('link');
    const studioLink = links.find((l) => l.getAttribute('href') === '/workspace/live');
    expect(studioLink).toBeInTheDocument();
    expect(studioLink).toHaveTextContent('Go to Studio');
  });

  it('renders all three recent conversation items', () => {
    renderDashboard();
    const conversationText = 'How to configure CI/CD pipeline for SupremeAI agent?';
    const items = screen.getAllByText(conversationText);
    expect(items).toHaveLength(3);
  });

  it('renders conversation timestamps', () => {
    renderDashboard();
    const oct24Elements = screen.getAllByText('Oct 24');
    expect(oct24Elements).toHaveLength(3);
  });

  it('renders the Active Agents section header', () => {
    renderDashboard();
    expect(screen.getByText('Active Agents')).toBeInTheDocument();
  });

  it('renders Code Generator agent as Running', () => {
    renderDashboard();
    expect(screen.getByText('Code Generator')).toBeInTheDocument();
    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('renders QA Tester agent as Idle', () => {
    renderDashboard();
    expect(screen.getByText('QA Tester')).toBeInTheDocument();
    expect(screen.getByText('Idle')).toBeInTheDocument();
  });

  it('renders the Usage (Pro Plan) section header', () => {
    renderDashboard();
    expect(screen.getByText('Usage (Pro Plan)')).toBeInTheDocument();
  });

  it('renders GPT-4 Tokens usage', () => {
    renderDashboard();
    expect(screen.getByText('GPT-4 Tokens')).toBeInTheDocument();
    expect(screen.getByText('42k / 100k')).toBeInTheDocument();
  });

  it('renders Agent Compute usage', () => {
    renderDashboard();
    expect(screen.getByText('Agent Compute')).toBeInTheDocument();
    expect(screen.getByText('12h / 50h')).toBeInTheDocument();
  });

  it('renders both View All and Go to Studio links', () => {
    renderDashboard();
    const links = screen.getAllByTestId('link');
    expect(links.find((l) => l.getAttribute('href') === '/projects')).toBeInTheDocument();
    expect(links.find((l) => l.getAttribute('href') === '/workspace/live')).toBeInTheDocument();
  });
});
