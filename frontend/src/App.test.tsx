import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
// বাংলা মন্তব্য (ROOT-CAUSE FIX): main.tsx App-কে ToastProvider দিয়ে wrap করে,
// কিন্তু এই টেস্ট ফাইল সরাসরি <App /> render করত ToastProvider ছাড়া। App-এর
// ভেতরের কম্পোনেন্টগুলো useToast() কল করায় "useToast must be used within a
// ToastProvider" থ্রো হয়ে ErrorBoundary পুরো অ্যাপ ক্র্যাশ হিসেবে দেখাত এবং
// এই ফাইলের সব টেস্ট ব্যর্থ হতো।
import { ToastProvider } from './contexts/ToastProvider';

vi.mock('./services/chatService', () => ({
  getAethelResponse: vi.fn().mockImplementation(() => new Promise(() => {})),
}));

vi.mock('./services/apiClient', () => ({
  getRawToken: vi.fn().mockReturnValue(null),
  AUTH_CHANGED_EVENT: 'AUTH_CHANGED_EVENT',
  apiClient: {
    get: vi.fn().mockImplementation((path: string) => {
      if (path === '/api/browser/sessions') return new Promise(() => {}); // never resolves
      return Promise.resolve({ items: [], keys: [], total: 0 });
    }),
    post: vi.fn().mockResolvedValue({}),
    put: vi.fn().mockResolvedValue({}),
    delete: vi.fn().mockResolvedValue({}),
  },
}));

import { App } from './App';

vi.mock('./components/core/AuthGuards', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  GuestRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock ResizeObserver for ReactFlow in JSDOM
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;

// Mock the EvolutionForgeWidget subcomponent to simplify App tests
vi.mock('./App', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./App')>();
  return {
    ...actual,
    EvolutionForgeWidget: () => <div data-testid="evolution-forge">// AI Evolution Forge Mock</div>,
  };
});

const mockFetchGateStatus = vi.fn();
const mockExecuteGateOverride = vi.fn();
const mockSetServerStatus = vi.fn();
const mockForgeNewSkill = vi.fn();

const storeState = {
  isServerOnline: true,
  setServerStatus: mockSetServerStatus,
  streamLogs: ['log 1', 'log 2'],
  deployGate: {
    status: 'UNLOCKED',
    reason: 'Initial deploy clean',
  },
  fetchGateStatus: mockFetchGateStatus,
  executeGateOverride: mockExecuteGateOverride,
  isForging: false,
  forgeFeedback: null,
  forgeSuccessCode: null,
  forgeNewSkill: mockForgeNewSkill,
  isConfigLoaded: true,
  setConfig: vi.fn(),
};

vi.mock('./store/useStore', () => ({
  useStore: () => storeState,
}));

// Mock EventSource globally
class MockEventSource {
  url: string;
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  close = vi.fn();
  constructor(url: string) {
    this.url = url;
    if (this.onopen) {
      this.onopen();
    }
  }
}

global.EventSource = MockEventSource as unknown as typeof EventSource;

vi.mock('./hooks/useServerStream', () => ({
  useServerStream: () => ({ streamStatus: 'connected' }),
}));

// Mock InteractiveChatTab to simplify chat tab tests
// বাংলা মন্তব্য: চ্যাট ট্যাবের মেসেজ এবং ইনপুট অ্যাকশনগুলো যাতে টেস্ট করতে সুবিধা হয়, সে জন্য mock প্রপস ওয়্যার আপ করা হলো
interface MockChatMessage {
  id: string | number;
  sender: string;
  text: string;
}

interface MockInteractiveChatTabProps {
  messages?: MockChatMessage[];
  input?: string;
  onInputChange?: (value: string) => void;
  onSend?: () => void;
}

vi.mock('./components/admin/InteractiveChatTab', () => ({
  InteractiveChatTab: ({ messages, input, onInputChange, onSend }: MockInteractiveChatTabProps) => (
    <div>
      <div data-testid="chat-header">Chat</div>
      <div data-testid="chat-messages">
        {messages?.map((msg) => (
          <div key={msg.id}>
            <span>{msg.sender}</span>
            <span>{msg.text}</span>
          </div>
        ))}
      </div>
      <input
        data-testid="chat-input"
        value={input || ''}
        onChange={(e) => onInputChange?.(e.target.value)}
      />
      <button data-testid="chat-submit" onClick={onSend}>Send</button>
    </div>
  ),
}));

vi.mock('./services/adminTokenStore', () => ({
  adminTokenStore: {
    getDecodedToken: vi.fn().mockReturnValue(null),
    isAuthenticated: vi.fn().mockReturnValue(false),
  },
}));

// Mock getApiBaseUrl used by InteractiveChatTab and other components
vi.mock('./utils/api', () => ({
  getApiBaseUrl: vi.fn().mockReturnValue('<backend-url>'),
}));

// Mock useDashboardStore used by InteractiveChatTab
vi.mock('./store/dashboardStore', () => ({
  useDashboardStore: () => ({
    dashboardMode: 'simple',
    chatTabTerminalOpen: false,
    chatTabBrowserOpen: false,
    toggleTerminal: vi.fn(),
    toggleBrowser: vi.fn(),
  }),
}));

// Mock useAuthStore (used by the new props-free UserDashboard) so the
// greeting stays deterministic in tests.
vi.mock('./store/authStore', () => ({
  useAuthStore: () => ({ user: null }),
}));

describe('App component', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    storeState.isServerOnline = true;
    storeState.deployGate.status = 'UNLOCKED';
    storeState.deployGate.reason = 'Initial deploy clean';
    window.location.hash = '#/workspace';
  });

  // The /workspace route renders the WorkspaceLayout shell wrapping the new
  // props-free customer UserDashboard. We assert on the real rendered content.
  it('renders the workspace shell with the customer dashboard at /workspace', () => {
    render(
      <ToastProvider>
        <MemoryRouter initialEntries={['/workspace']}>
          <App />
        </MemoryRouter>
      </ToastProvider>
    );

    // Customer dashboard greeting
    expect(screen.getByText('What would you like to build today?')).toBeInTheDocument();
    // Sidebar navigation
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('AI Studio')).toBeInTheDocument();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    // Dashboard sections
    expect(screen.getByText('Recent Conversations')).toBeInTheDocument();
  });

  it('renders the customer dashboard prompt input', () => {
    render(
      <ToastProvider>
        <MemoryRouter initialEntries={['/workspace']}>
          <App />
        </MemoryRouter>
      </ToastProvider>
    );

    expect(
      screen.getByPlaceholderText('Ask SupremeAI to generate, analyze, or deploy...')
    ).toBeInTheDocument();
  });

  it('renders the active agents and usage summary in the dashboard', () => {
    render(
      <ToastProvider>
        <MemoryRouter initialEntries={['/workspace']}>
          <App />
        </MemoryRouter>
      </ToastProvider>
    );

    expect(screen.getByText('Active Agents')).toBeInTheDocument();
    expect(screen.getByText('Usage (Pro Plan)')).toBeInTheDocument();
  });
});
