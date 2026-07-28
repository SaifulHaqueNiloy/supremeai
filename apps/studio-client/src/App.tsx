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

// বাংলা মন্তব্য: ক্লায়েন্ট বান্ডেল সাইজ অপ্টিমাইজ করার জন্য হেভি ওয়ার্কস্পেস পেজগুলো ডাইনামিকভাবে অলস লোড (lazy load) করা হলো।
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

primeDeviceFingerprint(); // বাংলা মন্তব্য: অ্যাপ বুট হওয়ার সাথে সাথে ব্যাকগ্রাউন্ডে ফিঙ্গারপ্রিন্ট হ্যাশ প্রিলোড হচ্ছে

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

import { TranslationProvider } from './i18n/I18nProvider';

export const App: React.FC = () => {
  return (
    <ThemeSyncProvider>
      <ToastProvider>
        <TranslationProvider locale="en">
          <AppContent />
        </TranslationProvider>
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
                  {/* বাংলা মন্তব্য: ড্যাশবোর্ড এবং লাইভ ওয়ার্কস্পেস রাউট সুরক্ষিত করার জন্য ProtectedRoute ব্যবহার করা হলো */}
                  <Route path="/workspace" element={
                    <ProtectedRoute>
                      <DashboardShell
                        theme={theme}
                        toggleTheme={toggleTheme}
                        isServerOnline={isServerOnline}
                        workspace={legacyWorkspace}
                      />
                    </ProtectedRoute>
                  } />
                  <Route path="/workspace/*" element={
                    <ProtectedRoute>
                      <DashboardShell
                        theme={theme}
                        toggleTheme={toggleTheme}
                        isServerOnline={isServerOnline}
                        workspace={legacyWorkspace}
                      />
                    </ProtectedRoute>
                  } />
                  <Route path="/workspace/live" element={
                    <ProtectedRoute>
                      <LivingDashboardShell chatPanel={legacyWorkspace} resolveDraggedContent={(id) => ({ content: id })} />
                    </ProtectedRoute>
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