import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { axe } from 'vitest-axe';
import * as matchers from 'vitest-axe/matchers';
import type { AxeMatchers } from 'vitest-axe';
import { BrowserRouter } from 'react-router-dom';
import { LoginPage } from '../pages/auth/LoginPage';
import { RegisterPage } from '../pages/auth/RegisterPage';
import { QuickPresets } from '../components/customer/QuickPresets';
import { DashboardShell } from '../components/dashboard/DashboardShell';
import { ChatPanel } from '../components/customer/ChatPanel';
import type { ChatMessage } from '../types';

declare module 'vitest' {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-empty-object-type
  export interface Assertion<_T = any> extends AxeMatchers {}
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  export interface AsymmetricMatchersContaining extends AxeMatchers {}
}

expect.extend(matchers);

// Mock dependencies
vi.mock('../store/authStore', () => ({
  useAuthStore: vi.fn((selector) => {
    const state = {
      user: { uid: 'test-123', email: 'test@supremeai.test', name: 'Test User' },
      isAuthenticated: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    };
    return selector ? selector(state) : state;
  }),
}));

vi.mock('../store/slices/chatSlice', () => ({
  useChatSlice: vi.fn(() => ({
    messages: [
      { id: 'm1', sender: 'assistant', text: 'Hello! How can I assist you?', timestamp: Date.now() },
    ],
    isLoading: false,
    sendMessage: vi.fn(),
  })),
}));

vi.mock('../store/slices/uiSlice', () => ({
  useUiSlice: vi.fn(() => ({
    isSidebarOpen: true,
    toggleSidebar: vi.fn(),
    activeTab: 'dashboard',
    setActiveTab: vi.fn(),
  })),
}));

describe('Phase 3 M3.5: axe-core Automated Accessibility Audits', () => {
  it('LoginPage should have zero accessibility violations', async () => {
    const { container } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('RegisterPage should have zero accessibility violations', async () => {
    const { container } = render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('QuickPresets should have zero accessibility violations', async () => {
    const { container } = render(
      <QuickPresets onSelectPreset={vi.fn()} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('DashboardShell navigation should have zero accessibility violations', async () => {
    const { container } = render(
      <BrowserRouter>
        <DashboardShell
          theme="dark"
          toggleTheme={vi.fn()}
          isServerOnline={true}
          workspace={<div><h2>Workspace Active</h2><p>Operational overview</p></div>}
        />
      </BrowserRouter>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('ChatPanel interface should have zero accessibility violations', async () => {
    const mockMessages: ChatMessage[] = [
      { id: '1', sender: 'ai', text: 'Hello! How can I assist you?', timestamp: '12:00' },
      { id: '2', sender: 'user', text: 'Run synthetic benchmark', timestamp: '12:01' },
    ];
    const { container } = render(
      <ChatPanel
        messages={mockMessages}
        input="test input"
        onInputChange={vi.fn()}
        onSend={vi.fn()}
        loading={false}
      />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
