# Part 9: React/Vite Studio Client Web Application Audit

> **Audit Generation Time:** `2026-07-24 20:09:07 UTC`  
> **Module Description:** React Studio Client frontend app, Admin Console UI components, and state management hooks.  
> **Status:** `SELF_CONTAINED / READY FOR EXTERNAL AI AUDIT`

---

## 1. 📁 Target Subsystems & File Inventory

- `apps/studio-client/src/` (Directory, 273 files)

---

## 2. 🔍 Audit Objectives & Key Checklist

- [ ] **Code Quality & Type Safety:** Check MyPy type hints and Ruff linting rules.
- [ ] **Security & Resilience:** Check exception handling, circuit breakers, and rate limiters.
- [ ] **Zero-Cost & Free-Tier Optimization:** Ensure no paid cloud service dependencies.
- [ ] **Bangla Code Comments:** Verify `// বাংলা মন্তব্য` is present across updated code blocks.

---

## 3. 📦 Complete Subsystem Source Code Dump

Below is the full source code for all target files in this module. Any external AI can audit this single document directly.

### 📄 `apps/studio-client/src/App.css`

```css
.counter {
  font-size: 16px;
  padding: 5px 10px;
  border-radius: 5px;
  color: var(--accent);
  background: var(--accent-bg);
  border: 2px solid transparent;
  transition: border-color 0.3s;
  margin-bottom: 24px;

  &:hover {
    border-color: var(--accent-border);
  }
  &:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
}

.hero {
  position: relative;

  .base,
  .framework,
  .vite {
    inset-inline: 0;
    margin: 0 auto;
  }

  .base {
    width: 170px;
    position: relative;
    z-index: 0;
  }

  .framework,
  .vite {
    position: absolute;
  }

  .framework {
    z-index: 1;
    top: 34px;
    height: 28px;
    transform: perspective(2000px) rotateZ(300deg) rotateX(44deg) rotateY(39deg)
      scale(1.4);
  }

  .vite {
    z-index: 0;
    top: 107px;
    height: 26px;
    width: auto;
    transform: perspective(2000px) rotateZ(300deg) rotateX(40deg) rotateY(39deg)
      scale(0.8);
  }
}

#center {
  display: flex;
  flex-direction: column;
  gap: 25px;
  place-content: center;
  place-items: center;
  flex-grow: 1;

  @media (max-width: 1024px) {
    padding: 32px 20px 24px;
    gap: 18px;
  }
}

#next-steps {
  display: flex;
  border-top: 1px solid var(--border);
  text-align: left;

  & > div {
    flex: 1 1 0;
    padding: 32px;
    @media (max-width: 1024px) {
      padding: 24px 20px;
    }
  }

  .icon {
    margin-bottom: 16px;
    width: 22px;
    height: 22px;
  }

  @media (max-width: 1024px) {
    flex-direction: column;
    text-align: center;
  }
}

#docs {
  border-right: 1px solid var(--border);

  @media (max-width: 1024px) {
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
}

#next-steps ul {
  list-style: none;
  padding: 0;
  display: flex;
  gap: 8px;
  margin: 32px 0 0;

  .logo {
    height: 18px;
  }

  a {
    color: var(--text-h);
    font-size: 16px;
    border-radius: 6px;
    background: var(--social-bg);
    display: flex;
    padding: 6px 12px;
    align-items: center;
    gap: 8px;
    text-decoration: none;
    transition: box-shadow 0.3s;

    &:hover {
      box-shadow: var(--shadow);
    }
    .button-icon {
      height: 18px;
      width: 18px;
    }
  }

  @media (max-width: 1024px) {
    margin-top: 20px;
    flex-wrap: wrap;
    justify-content: center;

    li {
      flex: 1 1 calc(50% - 8px);
    }

    a {
      width: 100%;
      justify-content: center;
      box-sizing: border-box;
    }
  }
}

#spacer {
  height: 88px;
  border-top: 1px solid var(--border);
  @media (max-width: 1024px) {
    height: 48px;
  }
}

.ticks {
  position: relative;
  width: 100%;

  &::before,
  &::after {
    content: '';
    position: absolute;
    top: -4.5px;
    border: 5px solid transparent;
  }

  &::before {
    left: 0;
    border-left-color: var(--border);
  }
  &::after {
    right: 0;
    border-right-color: var(--border);
  }
}

```

### 📄 `apps/studio-client/src/App.test.tsx`

```tsx
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('./services/chatService', () => ({
  getAethelResponse: vi.fn().mockImplementation(() => new Promise(() => {})),
}));

vi.mock('./services/apiClient', () => ({
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
import { getAethelResponse } from './services/chatService';

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
global.ResizeObserver = MockResizeObserver as any;

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

global.EventSource = MockEventSource as any;

describe('App component', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    storeState.isServerOnline = true;
    storeState.deployGate.status = 'UNLOCKED';
    storeState.deployGate.reason = 'Initial deploy clean';
    // বাংলা মন্তব্য: লিগ্যাসি ওয়ার্কস্পেস এখন Devin-স্টাইল শেলের #/workspace রুটে রেন্ডার হয়, তাই টেস্টের আগে hash সেট করা হলো
    window.location.hash = '#/workspace';
  });

  // বাংলা মন্তব্য: UI টেক্সট পরিবর্তন হওয়া সত্ত্বেও টেস্ট যাতে স্ট্যাবল থাকে সে জন্য data-testid ব্যবহার করা হলো
  it('renders header, title, and health status', () => {
    render(
      <MemoryRouter initialEntries={['/workspace']}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId('header-title')).toBeInTheDocument();
    expect(screen.getByTestId('core-status')).toBeInTheDocument();
  });

  // বাংলা মন্তব্য: চ্যাট ট্যাব সক্রিয় করে চ্যাট কনসোল রেন্ডারিং চেক করা হচ্ছে
  it('renders chat console when chat tab is active', () => {
    render(
      <MemoryRouter initialEntries={['/workspace']}>
        <App />
      </MemoryRouter>
    );

    // চ্যাট ট্যাবে ক্লিক করা হচ্ছে
    fireEvent.click(screen.getByTestId('tab-chat'));

    expect(screen.getByTestId('chat-header')).toBeInTheDocument();
  });

  // বাংলা মন্তব্য: চ্যাট প্যানেলে মেসেজ টাইপ ও সাবমিট করে প্রসেসিং সফলভাবে হচ্ছে কিনা টেস্ট করা হচ্ছে
  it('allows user to send messages in the chat console', async () => {
    render(
      <MemoryRouter initialEntries={['/workspace']}>
        <App />
      </MemoryRouter>
    );

    // চ্যাট ট্যাবে ক্লিক করা হচ্ছে
    fireEvent.click(screen.getByTestId('tab-chat'));

    const input = screen.getByTestId('chat-input');
    fireEvent.change(input, { target: { value: 'Test message' } });

    const sendButton = screen.getByTestId('chat-submit');
    fireEvent.click(sendButton);

    expect(screen.getByText('Test message')).toBeInTheDocument();
    expect(screen.getByText('Analyzing request "Test message"... Processing on central core.')).toBeInTheDocument();
    expect(getAethelResponse).toHaveBeenCalledWith('Test message', expect.any(Array));
  });
});

```

### 📄 `apps/studio-client/src/App.tsx`

```tsx
import React, { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useStore } from "./store/useStore";

import { ThemeSyncProvider } from './providers/ThemeSyncProvider';
import { GlobalConfigInitializer } from "./components/core/GlobalConfigInitializer";
import { ProtectedRoute, GuestRoute } from "./components/core/AuthGuards";
import { ToastProvider } from './components/ui/Toast';

// Pages (Core Layouts & Auth)
import { LoginScreen } from './pages/auth/LoginScreen';
import { RegisterScreen } from './pages/auth/RegisterScreen';
import { DashboardShell } from "./components/dashboard/DashboardShell";
import { LivingDashboardShell } from "./components/dashboard/LivingDashboardShell";
import { UserDashboard } from "./components/customer/UserDashboard";

// বাংলা মন্তব্য: ক্লায়েন্ট বান্ডেল সাইজ অপ্টিমাইজ করার জন্য হেভি ওয়ার্কস্পেস পেজগুলো ডাইনামিকভাবে অলস লোড (lazy load) করা হলো।
const AdminShell = React.lazy(() => import("./pages/admin/AdminShell").then(m => ({ default: m.AdminShell })));
const AgentWorkspace = React.lazy(() => import("./pages/user/AgentWorkspace").then(m => ({ default: m.AgentWorkspace })));
const IdeWorkspace = React.lazy(() => import("./pages/user/IdeWorkspace").then(m => ({ default: m.IdeWorkspace })));
const IntegrationsManager = React.lazy(() => import("./pages/user/IntegrationsManager").then(m => ({ default: m.IntegrationsManager })));
const ArchitectTower = React.lazy(() => import("./pages/user/ArchitectTower").then(m => ({ default: m.ArchitectTower })));
const SkillCatalog = React.lazy(() => import("./pages/user/SkillCatalog").then(m => ({ default: m.SkillCatalog })));
const SwarmMap = React.lazy(() => import("./components/SwarmMap"));
const EvolutionForge = React.lazy(() => import("./pages/user/EvolutionForge/EvolutionForge"));
const BillingPage = React.lazy(() => import("./pages/BillingPage"));
const ProfilePage = React.lazy(() => import("./pages/ProfilePage"));
const ErrorPage = React.lazy(() => import("./pages/ErrorPage"));

// Services & Hooks
import { getAethelResponse } from "./services/chatService";
import type { ChatMessage } from "./services/chatService";
import { useServerStream } from "./hooks/useServerStream";
import ErrorBoundary from './components/admin/DashboardErrorBoundary';
import { primeDeviceFingerprint } from "./utils/deviceFingerprint";

primeDeviceFingerprint(); // বাংলা মন্তব্য: অ্যাপ বুট হওয়ার সাথে সাথে ব্যাকগ্রাউন্ডে ফিঙ্গারপ্রিন্ট হ্যাশ প্রিলোড হচ্ছে

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: any) => {
        const msg = error?.message || '';
        if (
          error?.status === 401 || error?.status === 403 || error?.status === 429 ||
          msg.includes('401') || msg.includes('403') || msg.includes('429') ||
          msg.includes('Rate limit') || msg.includes('Unauthorized')
        ) return false;
        return failureCount < 2;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex + Math.random() * 500, 15000),
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

const PORTAL_TYPE = import.meta.env.VITE_PORTAL_TYPE || 'user';

export const App: React.FC = () => {
  return (
    <ThemeSyncProvider>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </ThemeSyncProvider>
  );
};

const AppContent: React.FC = () => {
  const { isServerOnline, deployGate } = useStore();
  const { streamStatus } = useServerStream();

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [code, setCode] = useState('// Click Preview or Save to interact with the workspace code');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');

  const handleSendCustomer = async () => {
    if (!chatInput.trim()) return;
    const now = new Date().toLocaleTimeString();
    const userMessage = { id: Date.now(), sender: 'User', text: chatInput, timestamp: now };
    const responseId = Date.now() + 1;

    setChatMessages(prev => [
      ...prev,
      userMessage,
      { id: responseId, sender: 'Aethel', text: `Analyzing request "${chatInput}"... Processing on central core.`, timestamp: now }
    ]);
    setChatInput('');

    try {
      const history = [...chatMessages, userMessage].map(msg => ({
        role: msg.sender === 'User' ? 'user' : 'assistant',
        content: msg.text,
      }));
      const responseText = await getAethelResponse(chatInput, history as any);
      setChatMessages(prev => prev.map(msg => msg.id === responseId ? { ...msg, text: responseText } : msg));
    } catch (error: any) {
      setChatMessages(prev => prev.map(msg => msg.id === responseId ? { ...msg, text: `AI backend error: ${error?.message || 'Unable to fetch response.'}` } : msg));
    }
  };

  const handleSaveToProject = (code: string) => {
    setCode(code);
  };

  const handlePreview = (code: string) => {
    setCode(code);
  };

  const legacyWorkspace = (
    <UserDashboard
      customerMessages={chatMessages}
      customerInput={chatInput}
      setCustomerInput={setChatInput}
      loading={false}
      handleSendCustomer={handleSendCustomer}
      theme={theme}
      toggleTheme={toggleTheme}
      code={code}
      setCode={setCode}
      isServerOnline={isServerOnline}
      deployGate={deployGate}
      user={null}
      projects={[]}
      chatHistory={chatMessages}
      widgets={[]}
      onSaveToProject={handleSaveToProject}
      onPreview={handlePreview}
    />
  );

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <GlobalConfigInitializer>
          <React.Suspense fallback={
            <div className="flex items-center justify-center min-h-screen bg-slate-950 text-slate-400">
              <div className="animate-pulse">Loading Workspace...</div>
            </div>
          }>
            <Routes>
              {PORTAL_TYPE === 'admin' ? (
                /* =========================================
                   ADMIN PORTAL
                ========================================= */
                <>
                  <Route path="/" element={<Navigate to="/admin" replace />} />
                  <Route path="/admin/*" element={<AdminShell />} />
                  <Route path="*" element={<Navigate to="/admin" replace />} />
                </>
              ) : (
                /* =========================================
                   USER PORTAL (State Machine Routing)
                ========================================= */
                <>
                  {/* GUEST STATE */}
                  <Route path="/login" element={
                    <GuestRoute>
                      <LoginScreen />
                    </GuestRoute>
                  } />
                  <Route path="/register" element={
                    <GuestRoute>
                      <RegisterScreen />
                    </GuestRoute>
                  } />
                  <Route path="/" element={<Navigate to="/workspace" replace />} />

                  {/* AUTHENTICATED STATE */}
                  <Route path="/workspace/agent" element={
                    <ProtectedRoute>
                      <AgentWorkspace />
                    </ProtectedRoute>
                  } />
                  <Route path="/workspace/ide" element={
                    <ProtectedRoute>
                      <IdeWorkspace />
                    </ProtectedRoute>
                  } />
                  <Route path="/integrations" element={
                    <ProtectedRoute>
                      <IntegrationsManager />
                    </ProtectedRoute>
                  } />
                  <Route path="/architect-tower" element={
                    <ProtectedRoute>
                      <ArchitectTower />
                    </ProtectedRoute>
                  } />
                  <Route path="/swarm" element={
                    <ProtectedRoute>
                      <SwarmMap />
                    </ProtectedRoute>
                  } />
                  <Route path="/evolution-forge" element={
                    <ProtectedRoute>
                      <EvolutionForge />
                    </ProtectedRoute>
                  } />
                  {/* বাংলা: /skills-catalog রাউট — রোল-ফিল্টারড ডাইনামিক ক্যাটালগ পেজ */}
                  <Route path="/skills-catalog" element={
                    <ProtectedRoute>
                      <SkillCatalog />
                    </ProtectedRoute>
                  } />
                  <Route path="/billing" element={
                    <ProtectedRoute>
                      <BillingPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/profile" element={
                    <ProtectedRoute>
                      <ProfilePage />
                    </ProtectedRoute>
                  } />
                  <Route path="/workspace/*" element={
                    <DashboardShell
                      theme={theme}
                      toggleTheme={toggleTheme}
                      isServerOnline={isServerOnline}
                      workspace={legacyWorkspace}
                    />
                  } />
                  <Route path="/workspace/live" element={
                    <LivingDashboardShell chatPanel={legacyWorkspace} resolveDraggedContent={(id) => ({ content: id })} />
                  } />

                  {/* Catch-all 404 Route */}
                  <Route path="*" element={<ErrorPage code={404} />} />

                  {/* Users trying to access admin are redirected */}
                  <Route path="/admin/*" element={<Navigate to="/" replace />} />
                </>
              )}
            </Routes>
          </React.Suspense>
        </GlobalConfigInitializer>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

```

### 📄 `apps/studio-client/src/firebase.ts`

```ts
import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// Helper to fetch configuration dynamically or fallback to Vite env vars
const getFirebaseConfig = async () => {
  try {
    const res = await fetch('/__/firebase/init.json');
    if (res.ok) {
      const data = await res.json();
      if (!data.projectId && data.authDomain) {
        data.projectId = data.authDomain.replace('.firebaseapp.com', '');
      }
      return data;
    }
  } catch (e) {
    if (import.meta.env.PROD) {
      console.error("🔥 Failed to fetch Firebase init configuration in production:", e);
      throw new Error("Firebase initialization failed: Configuration endpoint is unreachable.");
    }
  }
  const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;
  if (!apiKey) {
    if (import.meta.env.PROD) {
      console.error("🔥 VITE_FIREBASE_API_KEY is missing in production environment!");
      throw new Error("VITE_FIREBASE_API_KEY missing in production.");
    } else {
      console.warn("⚠️ Using fake Firebase API key for local development. Please copy .env.example to .env and configure Firebase.");
    }
  }
  return {
    apiKey: apiKey || "AIzaSyFakeKeyForDevelopmentOnly",
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "supremeai-a.firebaseapp.com",
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "supremeai-a",
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "supremeai-a.appspot.com",
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "1234567890",
    appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:1234567890:web:fakeappid"
  };
};

// Initialize Firebase app asynchronously or return existing instance
export const initFirebase = async () => {
  if (getApps().length > 0) {
    return getApp();
  }
  const config = await getFirebaseConfig();
  return initializeApp(config);
};

export const getFirebaseAuth = async () => {
  const app = await initFirebase();
  return getAuth(app);
};

```

### 📄 `apps/studio-client/src/index.css`

```css
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@400;700&family=JetBrains+Mono:wght@400;600&family=Hind+Siliguri:wght@400;500;600;700&display=swap');
@import "@supremeai/design-tokens/outputs/tokens.css";
@import "tailwindcss";

@theme {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-neon-blue: var(--neon-blue);
  --color-neon-purple: var(--neon-purple);
  --color-cyber-gray: var(--cyber-gray);
  --color-success: var(--success);
  --color-danger: var(--danger);
  --color-warning: var(--warning);
  --color-card-bg: var(--card-bg);
  --color-card-border: var(--card-border);
  --color-sidebar-bg: var(--sidebar-bg);
  --color-tabbar-bg: var(--tabbar-bg);
  --color-border-color: var(--border-color);
  --color-card-text: var(--card-text);
  --color-card-title-text: var(--card-title-text);
  --color-alert-bg: var(--alert-bg);
  --color-input-bg: var(--input-bg);
  --color-input-border: var(--input-border);
  --color-panel-bg: var(--panel-bg);

  --color-bg-main: var(--bg-main);
  --color-text-main: var(--text-main);
  --color-text-secondary: var(--text-secondary);
  --color-bg-panel: var(--bg-panel);
  --color-bg-cell: var(--bg-cell);
  --color-border-accent: var(--border-accent);
  --color-accent-primary: var(--accent-primary);
  --color-accent-secondary: var(--accent-secondary);
  --color-node-bg: var(--node-bg);
  --color-node-text: var(--node-text);
  --color-node-border: var(--node-border);
  --color-chat-bg: var(--chat-bg);
  --color-chat-input-bg: var(--chat-input-bg);
  --color-waveform-bg: var(--waveform-bg);
}

/* ═══════════════════════════════════════════════════════
   THEME 1: SKY BLUE (Light) — ডিফল্ট :root থিম
   ═══════════════════════════════════════════════════════ */
:root {
  --background: var(--supremeai-color-bg-void-light);
  --foreground: var(--supremeai-color-text-primary-light);
  --neon-blue: var(--supremeai-color-brand-primary-light);
  --neon-purple: var(--supremeai-color-brand-secondary-light);
  --cyber-gray: rgba(0, 0, 0, 0.05);
  --success: var(--supremeai-color-brand-success-light);
  --danger: var(--supremeai-color-brand-danger-light);
  --warning: var(--supremeai-color-brand-warning-light);
  --card-bg: var(--supremeai-color-bg-elevated-light);
  --card-border: var(--supremeai-color-border-accent-light);
  --sidebar-bg: rgba(248, 250, 252, 0.95);
  --tabbar-bg: #e2e8f0;
  --border-color: var(--supremeai-color-border-default-light);
  --card-text: var(--supremeai-color-text-secondary-light);
  --card-title-text: var(--supremeai-color-text-primary-light);
  --alert-bg: rgba(0, 0, 0, 0.02);
  --input-bg: #ffffff;
  --input-border: #cbd5e1;
  --panel-bg: #ffffff;

  /* CommandCenter Semantic Variables */
  --bg-main: var(--supremeai-color-bg-void-light);
  --text-main: var(--supremeai-color-text-primary-light);
  --text-secondary: var(--supremeai-color-text-secondary-light);
  --bg-panel: var(--supremeai-color-bg-elevated-light);
  --bg-cell: rgba(0, 0, 0, 0.04);
  --border-accent: var(--supremeai-color-border-accent-light);
  --accent-primary: var(--supremeai-color-brand-primary-light);
  --accent-secondary: var(--supremeai-color-brand-success-light);
  --node-bg: rgba(255, 255, 255, 0.92);
  --node-text: var(--supremeai-color-text-primary-light);
  --node-border: var(--supremeai-color-border-accent-light);
  --chat-bg: rgba(255, 255, 255, 0.9);
  --chat-input-bg: #f1f5f9;
  --waveform-bg: rgba(255, 255, 255, 0.9);
}

/* ═══════════════════════════════════════════════════════
   THEME 2: DEEP SPACE (Dark) — সায়েন্স-ফিকশন নিয়ন থিম
   ═══════════════════════════════════════════════════════ */
.dark {
  --background: var(--supremeai-color-bg-void-dark);
  --foreground: var(--supremeai-color-text-primary-dark);
  --neon-blue: var(--supremeai-color-brand-primary-dark);
  --neon-purple: var(--supremeai-color-brand-secondary-dark);
  --cyber-gray: rgba(255, 255, 255, 0.02);
  --success: var(--supremeai-color-brand-success-dark);
  --danger: var(--supremeai-color-brand-danger-dark);
  --warning: var(--supremeai-color-brand-warning-dark);
  --card-bg: var(--supremeai-color-bg-elevated-dark);
  --card-border: var(--supremeai-color-border-accent-dark);
  --sidebar-bg: rgba(10, 15, 26, 0.95);
  --tabbar-bg: #111827;
  --border-color: var(--supremeai-color-border-default-dark);
  --card-text: var(--supremeai-color-text-secondary-dark);
  --card-title-text: var(--supremeai-color-text-primary-dark);
  --alert-bg: rgba(255, 255, 255, 0.01);
  --input-bg: #0b0f19;
  --input-border: #1f2937;
  --panel-bg: #090d16;

  --bg-main: var(--supremeai-color-bg-void-dark);
  --text-main: var(--supremeai-color-text-primary-dark);
  --text-secondary: var(--supremeai-color-text-secondary-dark);
  --bg-panel: rgba(5, 9, 23, 0.5);
  --bg-cell: rgba(12, 18, 34, 0.8);
  --border-accent: var(--supremeai-color-border-accent-dark);
  --accent-primary: var(--supremeai-color-brand-primary-dark);
  --accent-secondary: var(--supremeai-color-brand-success-dark);
  --node-bg: rgba(6, 10, 24, 0.9);
  --node-text: var(--supremeai-color-text-primary-dark);
  --node-border: var(--supremeai-color-border-accent-dark);
  --chat-bg: rgba(5, 9, 23, 0.8);
  --chat-input-bg: #030611;
  --waveform-bg: rgba(6, 11, 27, 0.9);
}

/* ═══════════════════════════════════════════════════════
   THEME 3: SUNSET EMBER — উষ্ণ সূর্যাস্তের থিম
   ═══════════════════════════════════════════════════════ */
.sunset {
  --background: #1a0a0a;
  --foreground: #fef2f2;
  --neon-blue: #f97316;
  --neon-purple: #e11d48;
  --cyber-gray: rgba(255, 255, 255, 0.02);
  --success: #10b981;
  --danger: #ef4444;
  --warning: #fbbf24;
  --card-bg: rgba(30, 15, 10, 0.65);
  --card-border: rgba(249, 115, 22, 0.15);
  --sidebar-bg: rgba(20, 8, 5, 0.95);
  --tabbar-bg: #1c0a04;
  --border-color: rgba(255, 255, 255, 0.06);
  --card-text: #fed7aa;
  --card-title-text: #fff7ed;
  --alert-bg: rgba(255, 255, 255, 0.01);
  --input-bg: #140804;
  --input-border: #7c2d12;
  --panel-bg: #120703;

  --bg-main: #0f0503;
  --text-main: #fff7ed;
  --text-secondary: #fdba74;
  --bg-panel: rgba(20, 8, 4, 0.6);
  --bg-cell: rgba(30, 12, 6, 0.8);
  --border-accent: rgba(249, 115, 22, 0.2);
  --accent-primary: #f97316;
  --accent-secondary: #fbbf24;
  --node-bg: rgba(20, 8, 4, 0.9);
  --node-text: #fed7aa;
  --node-border: rgba(249, 115, 22, 0.4);
  --chat-bg: rgba(20, 8, 4, 0.85);
  --chat-input-bg: #0f0503;
  --waveform-bg: rgba(15, 6, 3, 0.9);
}

/* ═══════════════════════════════════════════════════════
   THEME 4: EMERALD MATRIX — সবুজ হ্যাকার ম্যাট্রিক্স থিম
   ═══════════════════════════════════════════════════════ */
.matrix {
  --background: #020a02;
  --foreground: #d1fae5;
  --neon-blue: #10b981;
  --neon-purple: #059669;
  --cyber-gray: rgba(16, 185, 129, 0.02);
  --success: #34d399;
  --danger: #ef4444;
  --warning: #fbbf24;
  --card-bg: rgba(5, 20, 10, 0.65);
  --card-border: rgba(16, 185, 129, 0.15);
  --sidebar-bg: rgba(2, 12, 5, 0.95);
  --tabbar-bg: #041408;
  --border-color: rgba(16, 185, 129, 0.06);
  --card-text: #a7f3d0;
  --card-title-text: #ecfdf5;
  --alert-bg: rgba(16, 185, 129, 0.01);
  --input-bg: #030d05;
  --input-border: #065f46;
  --panel-bg: #020c04;

  --bg-main: #010802;
  --text-main: #ecfdf5;
  --text-secondary: #6ee7b7;
  --bg-panel: rgba(3, 14, 5, 0.5);
  --bg-cell: rgba(5, 20, 8, 0.8);
  --border-accent: rgba(16, 185, 129, 0.2);
  --accent-primary: #10b981;
  --accent-secondary: #34d399;
  --node-bg: rgba(3, 14, 5, 0.9);
  --node-text: #a7f3d0;
  --node-border: rgba(16, 185, 129, 0.4);
  --chat-bg: rgba(3, 14, 5, 0.85);
  --chat-input-bg: #010802;
  --waveform-bg: rgba(2, 10, 3, 0.9);
}

/* ═══════════════════════════════════════════════════════
   BODY STYLES (সব থিমের জন্য)
   ═══════════════════════════════════════════════════════ */
body {
  font-family: 'Outfit', sans-serif;
  background-color: var(--background);
  color: var(--foreground);
  margin: 0;
  overflow: hidden;
  height: 100vh;
  transition: background-color 0.6s ease, color 0.6s ease;
  position: relative;
}

/* Deep Space — নিয়ন গ্র্যাডিয়েন্ট ব্যাকগ্রাউন্ড */
body.dark {
  background-image:
    radial-gradient(circle at 10% 20%, rgba(0, 243, 255, 0.06) 0%, transparent 40%),
    radial-gradient(circle at 90% 80%, rgba(188, 19, 254, 0.05) 0%, transparent 40%);
}

/* Sky Blue — অ্যানিমেটেড ক্লাউড ব্যাকগ্রাউন্ড */
body.light {
  background: linear-gradient(180deg, #60a5fa 0%, #93c5fd 40%, #e0f2fe 100%);
}

body.light::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: -2;
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg width='400' height='200' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M60,140 Q80,80 140,100 Q180,60 220,100 Q280,80 300,140 Z' fill='%23ffffff' opacity='0.7'/%3E%3C/svg%3E");
  background-size: 600px 300px;
  animation: clouds-drift 80s linear infinite;
}

body.light::after {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: -1;
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg width='300' height='150' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M40,100 Q60,50 100,70 Q130,30 170,70 Q210,50 230,100 Z' fill='%23ffffff' opacity='0.5'/%3E%3C/svg%3E");
  background-size: 450px 225px;
  animation: clouds-drift 120s linear infinite reverse;
}

/* Sunset Ember — আগুন-কণা ইফেক্ট */
body.sunset {
  background-image:
    radial-gradient(circle at 20% 80%, rgba(249, 115, 22, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(225, 29, 72, 0.06) 0%, transparent 50%),
    radial-gradient(circle at 50% 50%, rgba(251, 191, 36, 0.04) 0%, transparent 60%);
}

/* Matrix — ডিজিটাল রেইন ইফেক্ট */
body.matrix {
  background-image:
    radial-gradient(circle at 30% 30%, rgba(16, 185, 129, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 70% 70%, rgba(5, 150, 105, 0.06) 0%, transparent 40%);
}

@keyframes clouds-drift {
  from { background-position: 0 0; }
  to { background-position: 1800px 0; }
}

/* ═══════════════════════════════════════════════════════
   SCROLLBAR
   ═══════════════════════════════════════════════════════ */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, var(--neon-blue), var(--neon-purple));
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--neon-blue);
}

/* ═══════════════════════════════════════════════════════
   GLASSMORPHISM & COMPONENTS
   ═══════════════════════════════════════════════════════ */
.glass-card {
  background: var(--card-bg);
  backdrop-filter: blur(16px);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.03);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
  border-color: var(--accent-primary);
  box-shadow: 0 10px 40px color-mix(in srgb, var(--accent-primary) 15%, transparent);
  transform: translateY(-2px);
}

.text-gradient {
  background: linear-gradient(135deg, var(--neon-blue), var(--neon-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
}

/* Cyber Buttons & Inputs */
.cyber-button {
  background: linear-gradient(135deg, color-mix(in srgb, var(--neon-blue) 15%, transparent), color-mix(in srgb, var(--neon-purple) 15%, transparent));
  border: 1px solid var(--neon-blue);
  color: var(--text-main);
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 12px color-mix(in srgb, var(--neon-blue) 20%, transparent);
}

.cyber-button:hover {
  background: linear-gradient(135deg, color-mix(in srgb, var(--neon-blue) 30%, transparent), color-mix(in srgb, var(--neon-purple) 30%, transparent));
  box-shadow: 0 0 20px color-mix(in srgb, var(--neon-blue) 50%, transparent);
  transform: translateY(-1px);
}

.glass-action-button {
  background: var(--bg-cell);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.glass-action-button:hover {
  border-color: var(--neon-blue);
  background: color-mix(in srgb, var(--accent-primary) 8%, transparent);
  color: var(--text-main);
}

.cyber-danger-button {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid var(--danger);
  color: var(--text-main);
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.15);
}

.cyber-danger-button:hover {
  background: rgba(239, 68, 68, 0.25);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.35);
  transform: translateY(-1px);
}

/* Chat Bubbles Animation */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-bubble-animated {
  animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

/* Input Glow */
.glow-input:focus {
  outline: none;
  border-color: var(--neon-blue);
  box-shadow: 0 0 10px color-mix(in srgb, var(--accent-primary) 25%, transparent);
}

.technical-data {
  font-family: 'JetBrains Mono', monospace;
}

.font-bengali {
  font-family: 'Hind Siliguri', sans-serif;
}

.tooltip-enter {
  animation: tooltipFadeIn 0.15s ease-out;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translate(-50%, -4px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0) scale(1);
  }
}

.drag-region {
  -webkit-app-region: drag;
}

.drag-region button,
.drag-region input {
  -webkit-app-region: no-drag;
}

/* CRT Scanlines Effect */
.scanlines {
  background: linear-gradient(
    to bottom,
    transparent 50%,
    rgba(34, 211, 238, 0.03) 50%
  );
  background-size: 100% 4px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 40;
  animation: scanlines-scroll 15s linear infinite;
}

@keyframes scanlines-scroll {
  0% { background-position: 0 0; }
  100% { background-position: 0 600px; }
}

@keyframes pulse-glow-border {
  0%   { box-shadow: 0 0 8px  rgba(188,19,254,0.25),  inset 0 0 6px rgba(188,19,254,0.06); }
  50%  { box-shadow: 0 0 20px rgba(188,19,254,0.55), inset 0 0 14px rgba(188,19,254,0.12); }
  100% { box-shadow: 0 0 8px  rgba(188,19,254,0.25),  inset 0 0 6px rgba(188,19,254,0.06); }
}

.animate-pulse-glow {
  animation: pulse-glow-border 1.6s ease-in-out infinite;
}

/* ═══════════════════════════════════════════════════════
   P2 MICRO-ANIMATIONS & SHIMMER
   ═══════════════════════════════════════════════════════ */
.glass-hover {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 15px var(--neon-blue);
}

.page-transition-enter {
  opacity: 0;
  transform: translateY(10px);
}
.page-transition-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 600ms, transform 600ms;
}

@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}

```

### 📄 `apps/studio-client/src/main.tsx`

```tsx
// SupremeAI Studio Client v0.0.1
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { App } from './App.tsx'
import { GlobalErrorBoundary } from './components/GlobalErrorBoundary';
import { getApiBaseUrl } from './utils/api';
import { setupGlobalFetchInterceptor } from './utils/apiInterceptor';
import { ToastProvider } from './contexts/ToastProvider';

setupGlobalFetchInterceptor();

import { startAntiSleepHeartbeat } from './services/heartbeat';
if (import.meta.env.PROD) {
  startAntiSleepHeartbeat();
}

import { ThemeProvider } from './contexts/ThemeProvider'
// Shared providers (react-query, monaco defaults)
import { SharedProviders } from '@supremeai/ui-components'
import { BrowserRouter } from 'react-router-dom'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ToastProvider>
      <ThemeProvider>
        <SharedProviders>
          <BrowserRouter>
            <GlobalErrorBoundary>
              <App />
            </GlobalErrorBoundary>
          </BrowserRouter>
        </SharedProviders>
      </ThemeProvider>
    </ToastProvider>
  </StrictMode>,
)

```

### 📄 `apps/studio-client/src/types.ts`

```ts
export interface ChatMessage {
  id: string;
  sender: 'ai' | 'user';
  text: string;
  timestamp: string;
}

export interface Skill {
  id: string;
  name: string;
  version: string;
  description: string;
  dependencies?: string;
  installed: boolean;
  source: string;
}

export interface Checkpoint {
  task_id: string;
  step_index: number;
  state: Record<string, any>;
}

export interface CloudStats {
  distribution: Record<string, any>;
  total_requests: number;
  active_providers: number;
  strategy: string;
}

export interface GcpHealth {
  status: string;
  cloud_run: any;
  firestore_mode: string;
  pubsub_mode: string;
  cloud_functions: any;
}

export interface HealthMap {
  gcp: { status: string; latency: string; region: string };
  railway: { status: string; latency: string; region: string };
  render: { status: string; latency: string; region: string };
}

export interface AdminUser {
  username: string;
  role: string;
  permissions: string[];
}

// বাংলা মন্তব্য: অ্যাডমিন সাবট্যাব ইউনিয়নে 'interactive-chat' যোগ করা হলো
export type AdminSubTab = 'dashboard' | 'sandbox' | 'logs' | 'costs' | 'health' | 'users' | 'config' | 'command-center' | 'model-router' | 'skills' | 'memory' | 'cloud' | 'observability' | 'threats' | 'rules' | 'cicd' | 'github' | 'backups' | 'rate-limits' | 'security-dashboard' | 'interactive-chat';

export interface CIReport {
  id: number;
  run_id: number;
  run_number: number;
  event_name: string;
  actor: string;
  workflow_name: string;
  status: string;
  runtime_seconds: number;
  commit_sha: string;
  branch: string;
  jobs_summary: Record<string, any> | null;
  error_logs: string | null;
  created_at: number;
}

```

### 📄 `apps/studio-client/src/vite-env.d.ts`

```ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

```

### 📄 `apps/studio-client/src/assets/hero.png`

```png
PNG

   
IHDR  W  i     PLTE   ~v~vpdudZl}u~v~vw\̀x~wQ}v~vV~vxFRTNZ~g^p|uOHUxIYQ^|v˱}vZ|xxCxa԰\-gm|Ċf4}uBLEQq5ahiׁHǟckV(Xr!ܯo}.m7MO_t۴}[o3qVY%oQQs0fጅE@9FXJh,ähpEH:	BO<=
_ڋ5rOd\j~:g`mË8	H:	w4{O~FmP>
=
TϏS@[LćMI}vQ4
umw]x>{EYΓWw?Kܘ[v@;|q7gaiބBGANU0p}?ԅJ~B_[(_߮tv:RܡfYɡed-j5Dp<LrITp9v1a-^ZS U%KDQmfLeC?bތO_TX"Ì|>ŝce4Vk2k5JoDD΁DƔUNt:]%Pk}v9΄IFP}L
,gG~J_![g,ɔrM̦cp/}+h'u7{n1i ԰0B   |tRNS p# T;é*`YJACd S#20> |cA߻s|uo^Y_]?٤?Ǯ}dkecۢ8¬sТÐ}4  /:IDATx[0a	!DH:mHTQ%f_knݛ 6tV`Eg 00cS٫rl6u-Uvc'nт? 4xPSуx[ .i[DX͏S>\d{Ճ,mnE
HWؘ0x'{bWX`3X7-21`'ԄݪG?"V`
pMB#9J=L5(Z](mW>٬`KYjϱY擂sIϳO"X?T.K+mIOa=CsDy)a8a.1[HJ`F1K
Z`^^{̆)O0|R}[<Z
Q߇[5itt7p|iK@/aIvsJ`-c9٬
׺,I1ـ<6[, :z/V~ѱKt| ]=Uj{>"|fYqz)h@nK|HkR?FXԐ+3#V1(FX[$0}ՈVbxn	{@V1ʹ^G*iѪr4Am"f
g%xfoOz>@:RzXWL
S&q7pM:gU*Z^|+iꍵbsW@o]v[0n1@k!|_BUVRź|
% V`k;fZh5K>{H=/*tEѪ3x{gŬyRxO	STe哮9v{ڏ]:,w*m	cղ^MQچ.hpåXh?r.+T
E6iM."fOT
K<]K1hZ`??b	zD@?1=ʔW}QKa<2mu88Xu%[ěDb3o0O2D@O.`ӫAevMR`T֭p2j]XxfuKz^.8&-cT[Ղ46ÞJSբQGV5!u4a#kڭfJ[WPGb&,jꪺv|)	A2UJvMe|Aᩯ5uhE6_E/bMC%gdqxkX萡-[u!,[nȩYv,;cyP@]U)OzjCîc.Y3aoY։;daLDzUja8n{ׁF*{xJ;:#.N{_)Y3X־r{B蠺7-:?/	}wkw
1,el=$\V9O1NJ5~ r@6b8*յ!ˮr;c#ݿi޹٫fo*ґ[CZklmӞI==ig<Qxg}֕|V+55%Ƕ3c{7;ZDeȩvVX]Ul2)bDDz'T6x1̅k#e寇Ut߭OYD9evɗڛҳ	-+|5n^l`QnO\EI"x`ծ׏eD^D{̝avׇKWab.\aVRo'ؔ Kt1{.F)bJ~4 JT r>E,dSJKW(f,5>kR8
@d.BÈ0{VwS)Z}kɬcY{/u v][wf[ +X+$$3[eEn@2Q|PXUtKcڊ^ڲX&Fs
vy]	I 02 dyB0
!\{]Lmk[`Znǚ}4nI[eӺV9
11x*
40aƤ64aUvucM5
xk[`!i<}CQ1͓#@<Ar,qu@DRZۙWlLX|P3uϩ5\6`dX(MxO	a4ֈ>omf)x]մހ
6x]qЩn6vnrL])2Ҟ0Мs8[&kM0_4ALCgMZQPbiOa=̾іe3z~
:O2m_A䩁yB2kM+nV~MC̏|'̊[[;@uޣum2@
=7$u5=6+y&=:Vq,t$qjtΛ#YV>ih`{{'璝c\ӽilJTXy + `T2{=i+^2['I NZchԴbeb9׶b:%h#KwUU[^w[1#gAzL`pB^KowN5i,pxc:Som1t$QKsIw6IDQ>2|& lp $U2:A	)"FMXʭ+]cO0čw4j`<̝;-򬚒x83V(pe
dm"\6!)6P/m`0QA^ŷϕ_<;9n`|mUuFtTٕV9.Pw
k_4Е	Uw
sw曑U[b6mΑYSAD~d՚yh[.YR CZ]96 SIB~hY8Dƚ
naS-J[s.U-kSpӎdYro=Z9IP3F'Te[ x+SU_`ASZ&ucG6MYz\(%}dÉps}hYLuQj,q#i岼UJ)J~8me?ڳZ̀2nADvm/>,bU$ԬtJj bӬy6[YnN732UR'-pӬ#VGɪdbuIv)A uں@FIΔt/Dr>َ#VE[MFA ;	zmXbX(`q4~#.V7͚ͳV4uOBڦ6ts
_Q#sI?-h8	d
7ja#ֹ3 ЊlڏiV.8m/ƭ,A@4HɴT1b
x~fS.j\\|x (eS'AUa"Wm ?΅o,8V~-su5Cma.Ī/Ѓo~p^{ѓm ?ѫXG TR_wOm[.VVgo*,ޘbI HR  zuAk3abV'jjG%	b+Q }kx5rPVX$;֦d)B:[G%x*uu5P)5b_b/,WQb=nT 8h躮hQ
zuS?r
l`Y7l{{g,||V4EX.V/4Azճ6a9tYc~mo/S	?_?zn޳d1_-u(/ݿkSQV ox>K!:h
QjD$/ĩ8!""dPi#cG#-Bڸ֓\96Հռ;09|b2_2LZvgg<3z5x֙?pz-wWF_9PKkN(|du_q1ݓ쮉LlD3{+y=3fln#T=jh{+@Ļ u8VA%\4tXvn4/֝5k 
C7yj=Xn	磽S[̞ah֠] C12Ҍ58W+fFg1؇#

aow
;9b:HZSw]mu_znboY5s-kxg؝eBf,ѶJv͵ݹHpGQA4rh[5P6֗SqD<,kWz#čFZ*vb4o@}챠^.ק) cuV;HΖ
P
uGt	F1X(o \bنj:HOWrKॱ~]r6(oӻl-y #,זK͕	BDZH%(ٍaniUKO	OjF7`pXAsm<8|v-1M2|Oj	OJpTWq*=N3K])uWWk	,Yku<+XV-@>In4ݡGqOr^"fњxaIki[+JJY|CuƄjubV5]KYT;X8agtaXXI!^HDb#NV[p8s\3c8LcΠ͐zi嶣C^cx4.I~9?kcR0>g
V?/A'^b/1V#,2)^3A}GGR#O;+c<  .9X[==`F`pGAKpx>oB  )$`tC|f3!T0ᧅ0B`㸕8mruSlpg%pPN>ltCzWr\|@(ouz]|V~Z4nx!T`#9C5͎-՜߆!
PP6^Jt:(֠jn{BD>SqG7d>yɵ=&<;E0.01ǲ֘t
	1ZTfM=z2j,])9\k;%v\ʙ5"@ qh!&&ʔJ?:p{^
 PH476eH%7jw0N\tN$6A[NC]L\4
h`gN.0dȎܥK_jιlyQtyA1@G^O5
b:qjQ[Ug68dhdcRӃ;{z_c! @'<˵sŻEcgǀy5\ɣ8=;ؗOآ!iRԷfgȦC.A+ʑ
];פ
Ԙ/x#dbj5W4i~K*
l.xz$Rl6}0'[GYBwJ- nVBM}Np)0?`4+63׈]o
[rn4T
OKlχ忴T(iFhj{QӹOb$}>hNL:J"bJ;:M}cv}.lc%n(m#qQh+T*w?bsq.y )JRUfaLC5sbC2o ڒ"^Ӳ?hݔ |<5͞r"%$bkLl-j1hRU X=wN}&{IЫF2S]*s gAP3r	X"u$-l({{P5MeHI
=wj6wU	iRToYw*p7r)Ҋ
B:g
I	]rv{!r&ŬiL4 F4F޲*T@$$W<{X,τһV$
ؔSm.l̘b7QGUUMڪJuclE5.s6'䤽#{T,<NV}R~A0e<X(ǄV,QMEiﳩ %Ҽ|hRJS{GVxDiH"!_e^Jpǎ/8t*}7K*U5ն9wa.G9CjIɖ[ҊxI9X1[ٽh?N}UAReUz]oW%h/M!_;8>x "8#Dq߄! 5#XuOs[Zt`jK#ovڷ7|v{4յƆL4XtK'w\]ڜ#.nS#$K+RLT:cZ9?A/`vv5`N)Sמ<ִfY!j٘]OzNUl#xb`RKj4[fva<߶'"4Pw
?^֊'ٔ0ȽZyeT T_9pr3`]9d-üW_;׭/?֒QhJ|#X%gw`ɉR+Wt
Nx U:Vz<7
g1nl0ͩk?ya0b^-WOU6Ǩk[&ԯiH[҇~h1 [8n>wЃ}p˗I'B(EJf7\6+ >׉Ui'WAIP.?qoȟ{!;9t&cj5_pub}fQ|E2	Xc:GuH8u}ǎev3W_*?6AEcx1PgoMy!jӮBS3Obr\޽X5+$<!@%d4*$m}j5*lWTa0L/Y%ʼ9şU!>?ؕٻbh)<,bwwuAߤmED0d[:\-Ř0OM=X2ş%/ʥMGEA)8'Gⲱ(j}wYfuW]W	?<i|RBpD`Hbdq;5[n=Jӏ_\,|	pP aJ=Bi[""7VwhFt7O8yhW XK0V_zf	ǇXu(-_{q1YLe!쁡
`5zKH]tzw;kKڪQb(Cu #lY?0 Ph%>OV|"%2W=fH08c\b)C Z[D@,ߣgI*Œz+%Hhy\2.l<zwy`ڵΪsF[HQU	B(X~,n*$dE"P P %U&A;L<D lo0l[qh"6cZvbc-	r#,)U aKSD.}iv]Ugmvge)ۍJ]aTy?Y"ؓEO!J\)8=Г_?;|sӄ7˒yKuv+(eTf2BI= /tYN_q~g6UϙٷfOpՠޓ{$cL犻B*r4y
bb(o|#2{u⟝}ty~kםsܫwa\<?W$Mk<ۣ)I׸x$h	<uի6c߹ۨ޻iWϽo\(y} t.@-7l1%.] AcoOs7رn.?9˨ɫ;w|ͪ~S!>5*Vnl߀y*!-zwyx\''qAXEANy6DhbգU+](Mz
-4V7Nl#'';f>`hiǏp[aFDPg+μ8g\veJ}*!7fKG/[[jjM(5BbYAF\3<u0ȫ{|2g)5gGˆגum=\.U_
qO
Gi^$".sb
fCwE~Y/d+ Y-V2پ URL
(ǈGknˬ\/O]0v|n:N1ixo/_&r'Xjێ*B8sJ\Pf@g^ֿ4I8fѝ6ƓedG.E	ɮXƬbJIdφ.4K"E#1Er"
-GN;{㥪:2]w*bqwj㲯E$[2VpR  [ۜ>{=njkT
4whN5rQjf7hroɄ\|U"bS!B6j6) S-ίeWrpմ0N>OGnZ[` :s7DdIf'IoȥK;J+0AYMSk!,xV'qp=?==ۭ<9_imͦ3=Ej%sݣg$9Q
+6GTT?|y4R-4<]?
ξ@:n3݄BmFfwiz+S %~H<|UBaa
$hZK^ʵ 9Ք[oVo=

d>'
]:]0~@EAPxCguvʐX!i֤/`i>[G5Bil(%g';>A'ͧ^v$(ۼ|
v2z ӬYj3Im[9ĵ :۳wyp5	o#QaDε ZȳFn?z
63$o ~Z 6)A:>b\)6"#uw:5}y<c[%aLޛxRWgXe뷘6C&MH}Q#L&Vr8絆\52`'g`%6Qi54^|>L>fО@[}W-dQʈ*uCj9=b
gc^[a%	X^6pҸ'[
x[-E&
 DfG+ؘB`yѹ[Sz4rQWZ3g5e5tfA<)DVRuNʙN+TELK0As#]$cSxK 8Qǃj|d<=xdغKHxQXFH(f>
S܅jXz cS&ʍV״esKX*q:%N"ZqCE.W97p{Qȕ=}$k&$@{7մdK9zeUfP*OU0e9ϊy]\pqJyѵ{uo=({|vUVʁs5ձ$eU>ˢ,o9,r7'x\w̠,U8~3lMg<^0ީYdUy8^윻08(N 88H $6$J
5K&Gɠ\>.].".<>thׇMe$@A²l){.lo[CCN)VG8o"{s,[۸=Z6-Q~hYr׺j^mUF61PJ%On
2Za'	;?t@9U[C!%'W~#?C/-\l
mB/77	CMF*ց{p9id<Nz]bK[w<yp5گ?ӵ("c:i|pzywg"	9g}adB##	`h괫ܹ!bww7_OYn7Mf[I0鉤wo=ؾ]u|RJ  4FaBvKq"`81l}Nc\5VOZO!O׳C%rpiIav	cy^n6q!4Vhc!$@6(t)j$]}e:WϮ^m9kj9,b>h7yumHVF!`(
JZP@rJV̏xo*ZD<>X-6e*:hsTP' jD@TBE=OSu8'/uBM_Ю.Iϝw߮
LRpiB@%a܋#,'sMaM\g=pRc+vmrLZt.6:챷Ig\0 o&0ƛr.yܭM
`ogUnMWnV_~=4Ć7@q ;U҅s@M:tZN!}~ǿW]jK͚nJmT8 $rBV
-4-sWuYtEm.Gpz-x^m4((Y64 + \9+0
@BU#41yהu뎋~&{Sz
F1aeC$"@VCc ,o`"AES}5mqv.W|8y<N)5p`0~B*ХHJ%-<ۮX '-ms<نF!  ϊV@Ҳe 8-r[PS#`Pw}bPHEimK lc 1؈ @)G?y_m6wǢC'ɉj{:G %tuLp_Vk.ian0Vŭ,9eȁ[FP<efY+ߢc%k`l$@,"H5GoihczhZvb
%1VJ:8IHs"bZh֯=k751RܛCmm 7 (Zv/?Xߵoƨ
1=q2ur nB*u2۩XѠ"(,3n!ʇHGqcRG<k͇
 "$Po
=c!1Bz7{X, y!PA%C葆	s婪z	9i1mv/tcL, ,yj
9%Ie:n%xz,Q5)PkM;i1;߮nwC^lt*7    IENDB`
```

### 📄 `apps/studio-client/src/assets/react.svg`

```svg
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--logos" width="35.93" height="32" preserveAspectRatio="xMidYMid meet" viewBox="0 0 256 228"><path fill="#00D8FF" d="M210.483 73.824a171.49 171.49 0 0 0-8.24-2.597c.465-1.9.893-3.777 1.273-5.621c6.238-30.281 2.16-54.676-11.769-62.708c-13.355-7.7-35.196.329-57.254 19.526a171.23 171.23 0 0 0-6.375 5.848a155.866 155.866 0 0 0-4.241-3.917C100.759 3.829 77.587-4.822 63.673 3.233C50.33 10.957 46.379 33.89 51.995 62.588a170.974 170.974 0 0 0 1.892 8.48c-3.28.932-6.445 1.924-9.474 2.98C17.309 83.498 0 98.307 0 113.668c0 15.865 18.582 31.778 46.812 41.427a145.52 145.52 0 0 0 6.921 2.165a167.467 167.467 0 0 0-2.01 9.138c-5.354 28.2-1.173 50.591 12.134 58.266c13.744 7.926 36.812-.22 59.273-19.855a145.567 145.567 0 0 0 5.342-4.923a168.064 168.064 0 0 0 6.92 6.314c21.758 18.722 43.246 26.282 56.54 18.586c13.731-7.949 18.194-32.003 12.4-61.268a145.016 145.016 0 0 0-1.535-6.842c1.62-.48 3.21-.974 4.76-1.488c29.348-9.723 48.443-25.443 48.443-41.52c0-15.417-17.868-30.326-45.517-39.844Zm-6.365 70.984c-1.4.463-2.836.91-4.3 1.345c-3.24-10.257-7.612-21.163-12.963-32.432c5.106-11 9.31-21.767 12.459-31.957c2.619.758 5.16 1.557 7.61 2.4c23.69 8.156 38.14 20.213 38.14 29.504c0 9.896-15.606 22.743-40.946 31.14Zm-10.514 20.834c2.562 12.94 2.927 24.64 1.23 33.787c-1.524 8.219-4.59 13.698-8.382 15.893c-8.067 4.67-25.32-1.4-43.927-17.412a156.726 156.726 0 0 1-6.437-5.87c7.214-7.889 14.423-17.06 21.459-27.246c12.376-1.098 24.068-2.894 34.671-5.345a134.17 134.17 0 0 1 1.386 6.193ZM87.276 214.515c-7.882 2.783-14.16 2.863-17.955.675c-8.075-4.657-11.432-22.636-6.853-46.752a156.923 156.923 0 0 1 1.869-8.499c10.486 2.32 22.093 3.988 34.498 4.994c7.084 9.967 14.501 19.128 21.976 27.15a134.668 134.668 0 0 1-4.877 4.492c-9.933 8.682-19.886 14.842-28.658 17.94ZM50.35 144.747c-12.483-4.267-22.792-9.812-29.858-15.863c-6.35-5.437-9.555-10.836-9.555-15.216c0-9.322 13.897-21.212 37.076-29.293c2.813-.98 5.757-1.905 8.812-2.773c3.204 10.42 7.406 21.315 12.477 32.332c-5.137 11.18-9.399 22.249-12.634 32.792a134.718 134.718 0 0 1-6.318-1.979Zm12.378-84.26c-4.811-24.587-1.616-43.134 6.425-47.789c8.564-4.958 27.502 2.111 47.463 19.835a144.318 144.318 0 0 1 3.841 3.545c-7.438 7.987-14.787 17.08-21.808 26.988c-12.04 1.116-23.565 2.908-34.161 5.309a160.342 160.342 0 0 1-1.76-7.887Zm110.427 27.268a347.8 347.8 0 0 0-7.785-12.803c8.168 1.033 15.994 2.404 23.343 4.08c-2.206 7.072-4.956 14.465-8.193 22.045a381.151 381.151 0 0 0-7.365-13.322Zm-45.032-43.861c5.044 5.465 10.096 11.566 15.065 18.186a322.04 322.04 0 0 0-30.257-.006c4.974-6.559 10.069-12.652 15.192-18.18ZM82.802 87.83a323.167 323.167 0 0 0-7.227 13.238c-3.184-7.553-5.909-14.98-8.134-22.152c7.304-1.634 15.093-2.97 23.209-3.984a321.524 321.524 0 0 0-7.848 12.897Zm8.081 65.352c-8.385-.936-16.291-2.203-23.593-3.793c2.26-7.3 5.045-14.885 8.298-22.6a321.187 321.187 0 0 0 7.257 13.246c2.594 4.48 5.28 8.868 8.038 13.147Zm37.542 31.03c-5.184-5.592-10.354-11.779-15.403-18.433c4.902.192 9.899.29 14.978.29c5.218 0 10.376-.117 15.453-.343c-4.985 6.774-10.018 12.97-15.028 18.486Zm52.198-57.817c3.422 7.8 6.306 15.345 8.596 22.52c-7.422 1.694-15.436 3.058-23.88 4.071a382.417 382.417 0 0 0 7.859-13.026a347.403 347.403 0 0 0 7.425-13.565Zm-16.898 8.101a358.557 358.557 0 0 1-12.281 19.815a329.4 329.4 0 0 1-23.444.823c-7.967 0-15.716-.248-23.178-.732a310.202 310.202 0 0 1-12.513-19.846h.001a307.41 307.41 0 0 1-10.923-20.627a310.278 310.278 0 0 1 10.89-20.637l-.001.001a307.318 307.318 0 0 1 12.413-19.761c7.613-.576 15.42-.876 23.31-.876H128c7.926 0 15.743.303 23.354.883a329.357 329.357 0 0 1 12.335 19.695a358.489 358.489 0 0 1 11.036 20.54a329.472 329.472 0 0 1-11 20.722Zm22.56-122.124c8.572 4.944 11.906 24.881 6.52 51.026c-.344 1.668-.73 3.367-1.15 5.09c-10.622-2.452-22.155-4.275-34.23-5.408c-7.034-10.017-14.323-19.124-21.64-27.008a160.789 160.789 0 0 1 5.888-5.4c18.9-16.447 36.564-22.941 44.612-18.3ZM128 90.808c12.625 0 22.86 10.235 22.86 22.86s-10.235 22.86-22.86 22.86s-22.86-10.235-22.86-22.86s10.235-22.86 22.86-22.86Z"></path></svg>

```

### 📄 `apps/studio-client/src/assets/vite.svg`

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="77" height="47" fill="none" aria-labelledby="vite-logo-title" viewBox="0 0 77 47"><title id="vite-logo-title">Vite</title><style>.parenthesis{fill:#000}@media (prefers-color-scheme:dark){.parenthesis{fill:#fff}}</style><path fill="#9135ff" d="M40.151 45.71c-.663.844-2.02.374-2.02-.699V34.708a2.26 2.26 0 0 0-2.262-2.262H24.493c-.92 0-1.457-1.04-.92-1.788l7.479-10.471c1.07-1.498 0-3.578-1.842-3.578H15.443c-.92 0-1.456-1.04-.92-1.788l9.696-13.576c.213-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.472c-1.07 1.497 0 3.578 1.842 3.578h11.376c.944 0 1.474 1.087.89 1.83L40.153 45.712z"/><mask id="a" width="48" height="47" x="14" y="0" maskUnits="userSpaceOnUse" style="mask-type:alpha"><path fill="#000" d="M40.047 45.71c-.663.843-2.02.374-2.02-.699V34.708a2.26 2.26 0 0 0-2.262-2.262H24.389c-.92 0-1.457-1.04-.92-1.788l7.479-10.472c1.07-1.497 0-3.578-1.842-3.578H15.34c-.92 0-1.456-1.04-.92-1.788l9.696-13.575c.213-.297.556-.474.92-.474H53.93c.92 0 1.456 1.04.92 1.788L47.37 13.03c-1.07 1.498 0 3.578 1.842 3.578h11.376c.944 0 1.474 1.088.89 1.831L40.049 45.712z"/></mask><g mask="url(#a)"><g filter="url(#b)"><ellipse cx="5.508" cy="14.704" fill="#eee6ff" rx="5.508" ry="14.704" transform="rotate(269.814 20.96 11.29)scale(-1 1)"/></g><g filter="url(#c)"><ellipse cx="10.399" cy="29.851" fill="#eee6ff" rx="10.399" ry="29.851" transform="rotate(89.814 -16.902 -8.275)scale(1 -1)"/></g><g filter="url(#d)"><ellipse cx="5.508" cy="30.487" fill="#8900ff" rx="5.508" ry="30.487" transform="rotate(89.814 -19.197 -7.127)scale(1 -1)"/></g><g filter="url(#e)"><ellipse cx="5.508" cy="30.599" fill="#8900ff" rx="5.508" ry="30.599" transform="rotate(89.814 -25.928 4.177)scale(1 -1)"/></g><g filter="url(#f)"><ellipse cx="5.508" cy="30.599" fill="#8900ff" rx="5.508" ry="30.599" transform="rotate(89.814 -25.738 5.52)scale(1 -1)"/></g><g filter="url(#g)"><ellipse cx="14.072" cy="22.078" fill="#eee6ff" rx="14.072" ry="22.078" transform="rotate(93.35 31.245 55.578)scale(-1 1)"/></g><g filter="url(#h)"><ellipse cx="3.47" cy="21.501" fill="#8900ff" rx="3.47" ry="21.501" transform="rotate(89.009 35.419 55.202)scale(-1 1)"/></g><g filter="url(#i)"><ellipse cx="3.47" cy="21.501" fill="#8900ff" rx="3.47" ry="21.501" transform="rotate(89.009 35.419 55.202)scale(-1 1)"/></g><g filter="url(#j)"><ellipse cx="14.592" cy="9.743" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(39.51 14.592 9.743)"/></g><g filter="url(#k)"><ellipse cx="61.728" cy="-5.321" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 61.728 -5.32)"/></g><g filter="url(#l)"><ellipse cx="55.618" cy="7.104" fill="#00c2ff" rx="5.971" ry="9.665" transform="rotate(37.892 55.618 7.104)"/></g><g filter="url(#m)"><ellipse cx="12.326" cy="39.103" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 12.326 39.103)"/></g><g filter="url(#n)"><ellipse cx="12.326" cy="39.103" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 12.326 39.103)"/></g><g filter="url(#o)"><ellipse cx="49.857" cy="30.678" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 49.857 30.678)"/></g><g filter="url(#p)"><ellipse cx="52.623" cy="33.171" fill="#00c2ff" rx="5.971" ry="15.297" transform="rotate(37.892 52.623 33.17)"/></g></g><path d="M6.919 0c-9.198 13.166-9.252 33.575 0 46.789h6.215c-9.25-13.214-9.196-33.623 0-46.789zm62.424 0h-6.215c9.198 13.166 9.252 33.575 0 46.789h6.215c9.25-13.214 9.196-33.623 0-46.789" class="parenthesis"/><defs><filter id="b" width="60.045" height="41.654" x="-5.564" y="16.92" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="7.659"/></filter><filter id="c" width="90.34" height="51.437" x="-40.407" y="-6.762" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="7.659"/></filter><filter id="d" width="79.355" height="29.4" x="-35.435" y="2.801" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="e" width="79.579" height="29.4" x="-30.84" y="20.8" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="f" width="79.579" height="29.4" x="-29.307" y="21.949" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="g" width="74.749" height="58.852" x="29.961" y="-17.13" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="7.659"/></filter><filter id="h" width="61.377" height="25.362" x="37.754" y="3.055" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="i" width="61.377" height="25.362" x="37.754" y="3.055" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="j" width="56.045" height="63.649" x="-13.43" y="-22.082" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="k" width="54.814" height="64.646" x="34.321" y="-37.644" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="l" width="33.541" height="35.313" x="38.847" y="-10.552" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="m" width="54.814" height="64.646" x="-15.081" y="6.78" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="n" width="54.814" height="64.646" x="-15.081" y="6.78" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="o" width="54.814" height="64.646" x="22.45" y="-1.645" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="p" width="39.409" height="43.623" x="32.919" y="11.36" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter></defs></svg>

```

### 📄 `apps/studio-client/src/components/AdminConsole.tsx`

```tsx
import type { ChatMessage, Skill, Checkpoint, CloudStats, GcpHealth, AdminSubTab } from '../types';
import { useHydrated } from '../store/customerStore';
import { LoginView } from './admin/AdminLogin';
import { AuthenticatedView } from './admin/AdminAuthenticated';

interface AdminConsoleProps {
  adminAuthenticated: boolean;
  adminPassword: string;
  setAdminPassword: (val: string) => void;
  adminEmail: string;
  setAdminEmail: (val: string) => void;

  adminError: string;
  handleAdminLogin: () => void;
  handleAdminLogout: () => void;
  actionStatus: string;
  gcpHealth: GcpHealth | null;
  cloudStats: CloudStats | null;
  skillQuery: string;
  setSkillQuery: (val: string) => void;
  skills: Skill[];
  handleInstallSkill: (name: string) => void;
  checkpoints: Checkpoint[];
  handleDeleteCheckpoint: (taskId: string) => void;
  adminSubTab: AdminSubTab;
  setAdminSubTab: (tab: AdminSubTab) => void;
  handleTriggerDeploy: () => void;
  adminMessages: ChatMessage[];
  loading: boolean;
  adminInput: string;
  setAdminInput: (val: string) => void;
  handleSendAdmin: () => void;
  rulesJson: string;
  setRulesJson: (val: string) => void;
  saveStatus: string;
  handleSaveRules: () => void;
  liveLogs: string[];
  setLiveLogs: (logs: string[]) => void;
  costReport: string;
  healthMap: any;
  newUsername: string;
  setNewUsername: (val: string) => void;
  newUserRole: string;
  setNewUserRole: (val: string) => void;
  newUserPerms: string;
  setNewUserPerms: (val: string) => void;
  handleSaveUser: () => void;
  adminUsers: any[];
  handleDeleteUser: (username: string) => void;
  envConfig: Record<string, string>;
  setEnvConfig: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  handleSaveConfig: () => void;
  otpRequired: boolean;
  adminOtp: string;
  setAdminOtp: (val: string) => void;
  theme: 'dark' | 'light';
  toggleTheme: () => void;
}

export function AdminConsole(props: AdminConsoleProps) {
  return (
    <div className="flex-grow flex flex-col overflow-hidden bg-[var(--background)] text-[var(--foreground)]">
      {!props.adminAuthenticated ? (
        <LoginView {...props} />
      ) : (
        <AuthenticatedView {...props} />
      )}
    </div>
  );
}

```

### 📄 `apps/studio-client/src/components/BanglaHint.tsx`

```tsx
import { useState } from 'react';
import { HelpCircle } from 'lucide-react';

interface BanglaHintProps {
  text: string;
}

export const BanglaHint = ({ text }: BanglaHintProps) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <span className="relative inline-block" onMouseEnter={() => setShowTooltip(true)} onMouseLeave={() => setShowTooltip(false)}>
      <button
        className="inline-flex items-center justify-center rounded-full p-1 text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors"
        aria-label="টিপস"
      >
        <HelpCircle className="w-4 h-4" />
      </button>
      {showTooltip && (
        <div
          className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-3 py-2 bg-slate-900 border border-cyan-500/30 text-slate-200 text-xs rounded-md shadow-lg z-50 whitespace-nowrap tooltip-enter"
          role="tooltip"
        >
          <p className="font-bengali">{text}</p>
        </div>
      )}
    </span>
  );
};

```

### 📄 `apps/studio-client/src/components/FixPreviewModal.tsx`

```tsx
import React from 'react';
import { X, Check, XCircle } from 'lucide-react';

interface FixPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApprove: () => void;
  onReject: () => void;
  fix: any;
  loading: boolean;
}

export const FixPreviewModal: React.FC<FixPreviewModalProps> = ({
  isOpen,
  onClose,
  onApprove,
  onReject,
  fix,
  loading
}) => {
  if (!isOpen || !fix) return null;

  const oldCode = fix.metadata?.original_code || "// Original code not provided";
  const newCode = fix.metadata?.proposed_code || "// Proposed fix not provided";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">

        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-slate-700 bg-slate-800">
          <div>
            <h2 className="text-xl font-bold text-white">Review Fix: {fix.id}</h2>
            <p className="text-slate-400 text-sm mt-1">
              Error Type: <span className="font-mono text-rose-400">{fix.error_type}</span> |
              Impact Score: <span className="font-mono text-emerald-400">{fix.impact_score || 0}</span>
            </p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Diff Viewer */}
        <div className="flex-1 overflow-auto p-4 bg-slate-950 flex gap-4">
          <div className="flex-1 border border-slate-700 rounded bg-slate-900 flex flex-col">
            <div className="p-2 border-b border-slate-700 font-bold text-slate-300">Current Code</div>
            <pre className="p-4 text-sm font-mono text-slate-300 overflow-auto">{oldCode}</pre>
          </div>
          <div className="flex-1 border border-emerald-900/50 rounded bg-slate-900 flex flex-col shadow-[0_0_15px_rgba(16,185,129,0.1)]">
            <div className="p-2 border-b border-emerald-900/50 font-bold text-emerald-400">SelfHealer Proposed Fix</div>
            <pre className="p-4 text-sm font-mono text-emerald-300 overflow-auto">{newCode}</pre>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-700 bg-slate-800 flex justify-end gap-3">
          <button
            onClick={onReject}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-rose-900/50 text-rose-400 rounded-lg transition-colors border border-transparent hover:border-rose-500/50"
          >
            <XCircle size={18} />
            Reject
          </button>

          <button
            onClick={onApprove}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg shadow-lg shadow-emerald-500/20 transition-all font-medium disabled:opacity-50"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            ) : (
              <Check size={18} />
            )}
            Approve & Apply
          </button>
        </div>
      </div>
    </div>
  );
};

```

### 📄 `apps/studio-client/src/components/GlobalErrorBoundary.tsx`

```tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCcw } from 'lucide-react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class GlobalErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900 text-gray-100 p-4 font-sans">
          <div className="max-w-md w-full bg-gray-800 rounded-xl shadow-2xl p-8 text-center border border-gray-700/50">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 mb-6">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>

            <h1 className="text-2xl font-bold text-white mb-3">
              Application Error
            </h1>

            <p className="text-gray-400 mb-6 text-sm leading-relaxed">
              We encountered an unexpected error. This has been logged and our team will investigate.
            </p>

            {this.state.error && (
              <div className="mb-8 text-left bg-gray-900/50 p-4 rounded-lg border border-gray-700 overflow-auto max-h-32 text-xs font-mono text-red-400">
                {this.state.error.message}
              </div>
            )}

            <button
              onClick={this.handleReload}
              className="inline-flex items-center justify-center px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg transition-colors duration-200 gap-2 w-full"
            >
              <RefreshCcw className="w-4 h-4" />
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

```


---

## 4. 🐛 Identified Vulnerabilities & Edge Cases

*Run external AI prompt against Section 3 above to populate.*

---

## 5. 🛠️ Recommended Delta Patches & Actions

*Pending audit execution.*

---
*Generated automatically by SupremeAI 2.0 Audit Generator Script.*
