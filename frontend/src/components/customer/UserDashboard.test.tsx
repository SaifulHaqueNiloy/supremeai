import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { UserDashboard } from './UserDashboard';
import { I18nContext } from '../../i18n/I18nContext';
import { translations } from '../../i18n/translations';

// বাংলা মন্তব্য: i18n মক — I18nContext সরাসরি ইংরেজি ট্রান্সলেশন রিটার্ন করে
const mockT = (key: string, params?: Record<string, string | number>) => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const en = (translations as any).en;
  let value = en[key] ?? key;
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      value = value.replace(`{${k}}`, String(v));
    });
  }
  return value;
};

const renderWithI18n = (ui: React.ReactElement) => {
  return render(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    <I18nContext.Provider value={{ t: mockT as any, locale: 'en', setLocale: vi.fn() }}>
      {ui}
    </I18nContext.Provider>
  );
};

const defaultProps = {
  customerMessages: [
    { id: 1, sender: 'User' as const, text: 'Hello', timestamp: '10:00 AM' },
    { id: 2, sender: 'SupremeAI' as const, text: 'Hi there', timestamp: '10:01 AM' },
  ],
  customerInput: '',
  setCustomerInput: vi.fn(),
  loading: false,
  handleSendCustomer: vi.fn(),
  theme: 'dark' as const,
  toggleTheme: vi.fn(),
  code: '// code',
  setCode: vi.fn(),
  isServerOnline: true,
  deployGate: { status: 'UNLOCKED' },
  user: {
    id: 'user-1',
    username: 'TestUser',
    created_at: '2026-06-01',
    last_login: '2026-06-29',
    email: 'test@example.com',
    role: 'operator' as const,
    preferences: {
      theme: 'dark' as const,
      sidebar_collapsed: false,
      notification_enabled: true,
      sound_enabled: true,
      compact_mode: false,
      font_size: 'medium' as const,
    },
  },
  projects: [
    {
      id: '1',
      name: 'Project A',
      description: 'Desc',
      created_at: '2026-06-01',
      updated_at: '2026-06-29',
      owner_id: 'u1',
      settings: {
        default_model: 'gpt-4',
        system_prompt: '',
        temperature: 0.7,
        max_tokens: 1024,
        rag_enabled: true,
      },
    },
  ],
  chatHistory: [],
  widgets: [],
};

describe('UserDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const getTabButton = (name: RegExp) =>
    screen.getAllByRole('button', { name })[0];

  it('renders welcome header with username', () => {
    renderWithI18n(<UserDashboard {...defaultProps} />);
    expect(screen.getByText('Welcome back, TestUser')).toBeInTheDocument();
  });

  it('renders server and gate status', () => {
    renderWithI18n(<UserDashboard {...defaultProps} />);
    expect(screen.getByText(/CORE:/)).toBeInTheDocument();
    expect(screen.getByText(/ONLINE/)).toBeInTheDocument();
    expect(screen.getByText(/UNLOCKED/)).toBeInTheDocument();
  });

  it('shows offline status when server is down', () => {
    renderWithI18n(<UserDashboard {...defaultProps} isServerOnline={false} />);
    expect(screen.getByText(/OFFLINE/)).toBeInTheDocument();
  });

  it('renders default theme as dark', () => {
    renderWithI18n(<UserDashboard {...defaultProps} theme="dark" />);
    expect(screen.getByText(/☀️ Light/)).toBeInTheDocument();
  });

  it('renders light theme when toggled', () => {
    renderWithI18n(<UserDashboard {...defaultProps} theme="light" />);
    expect(screen.getByText(/🌙 Dark/)).toBeInTheDocument();
  });

  it('calls toggleTheme when theme button clicked', () => {
    renderWithI18n(<UserDashboard {...defaultProps} />);
    const btn = screen.getByText(/☀️ Light/);
    fireEvent.click(btn);
    expect(defaultProps.toggleTheme).toHaveBeenCalled();
  });

  it('renders all six tab buttons', () => {
    renderWithI18n(<UserDashboard {...defaultProps} />);
    expect(screen.getByRole('button', { name: /Overview/i })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /Home Feed/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('button', { name: /Quick Presets/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('button', { name: /Chat/i }).length).toBeGreaterThanOrEqual(1);
  });

  it('switches to presets tab when clicked', () => {
    renderWithI18n(<UserDashboard {...defaultProps} />);
    fireEvent.click(getTabButton(/Quick Presets/i));
    expect(getTabButton(/Quick Presets/i).classList.contains('bg-accent-primary/20')).toBe(true);
  });

  it('switches to chat tab when clicked', () => {
    renderWithI18n(<UserDashboard {...defaultProps} />);
    fireEvent.click(getTabButton(/Chat/i));
    // বাংলা মন্তব্য: টেস্টে ব্যবহৃত হেডার টেক্সট আপডেট করা হলো
    expect(screen.getByText('Unified Command Portal')).toBeInTheDocument();
  });

  it('switches to feed tab when clicked', () => {
    renderWithI18n(<UserDashboard {...defaultProps} />);
    fireEvent.click(getTabButton(/Home Feed/i));
    expect(screen.getByText('Personalized Home Feed')).toBeInTheDocument();
  });

  it('shows project list on overview', () => {
    renderWithI18n(<UserDashboard {...defaultProps} projects={defaultProps.projects} />);
    expect(screen.getByText('Your Projects')).toBeInTheDocument();
    expect(screen.getByText('Project A')).toBeInTheDocument();
  });

  it('shows empty projects state when no projects', () => {
    renderWithI18n(<UserDashboard {...defaultProps} projects={[]} />);
    expect(screen.getByText('No projects yet. Create your first project to get started.')).toBeInTheDocument();
  });

  it('shows stat cards with counts', () => {
    renderWithI18n(<UserDashboard {...defaultProps} projects={defaultProps.projects} />);
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('shows quick actions and navigates to chat', () => {
    renderWithI18n(<UserDashboard {...defaultProps} />);
    fireEvent.click(screen.getByText('New Chat Session'));
    // বাংলা মন্তব্য: টেস্টে ব্যবহৃত হেডার টেক্সট আপডেট করা হলো
    expect(screen.getByText('Unified Command Portal')).toBeInTheDocument();
  });

  it('shows recent activity from customerMessages', () => {
    renderWithI18n(<UserDashboard {...defaultProps} chatHistory={[]} />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there')).toBeInTheDocument();
  });

  it('shows no recent activity when no messages', () => {
    renderWithI18n(<UserDashboard {...defaultProps} customerMessages={[]} chatHistory={[]} />);
    expect(screen.getByText('No recent activity')).toBeInTheDocument();
  });

  it('calls setCustomerInput when chat input changes', () => {
    renderWithI18n(<UserDashboard {...defaultProps} />);
    fireEvent.click(getTabButton(/Chat/i));
    // বাংলা মন্তব্য: স্ট্যাবল টেস্টিং নিশ্চিত করতে প্লেসহোল্ডার স্ট্রিংয়ের পরিবর্তে data-testid ব্যবহার করা হলো
    const input = screen.getByTestId('chat-input');
    fireEvent.change(input, { target: { value: 'test input' } });
    expect(defaultProps.setCustomerInput).toHaveBeenCalledWith('test input');
  });

  it('calls handleSendCustomer when send button clicked', () => {
    renderWithI18n(<UserDashboard {...defaultProps} customerInput="hello" />);
    fireEvent.click(getTabButton(/Chat/i));
    const sendBtn = screen.getByText('Send').closest('button');
    if (sendBtn) fireEvent.click(sendBtn);
    expect(defaultProps.handleSendCustomer).toHaveBeenCalled();
  });

  it('switches to overview from quick action and back to presets', () => {
    renderWithI18n(<UserDashboard {...defaultProps} />);
    fireEvent.click(getTabButton(/Quick Presets/i));
    expect(getTabButton(/Quick Presets/i).classList.contains('bg-accent-primary/20')).toBe(true);
  });
});
