import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { ThemeSyncProvider } from './providers/ThemeSyncProvider';
import { GlobalConfigInitializer } from "./components/core/GlobalConfigInitializer";
import { ProtectedRoute, GuestRoute, useAuthStatus, AuthLoadingSpinner } from "./components/core/AuthGuards";
import { RoleGuard, PermissionGuard } from "./components/core/guards/RoleGuard";
import { resolveLandingPath } from './auth/identity';

// Pages (Core Layouts & Auth)
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { WorkspaceLayout } from "./components/layout/WorkspaceLayout";
import { LivingDashboardShell } from "./components/dashboard/LivingDashboardShell";
import { UserDashboard } from "./components/customer/UserDashboard";

// বাংলা মন্তব্য: ক্লায়েন্ট বান্ডেল সাইজ অপ্টিমাইজ করার জন্য হেভি ওয়ার্কস্পেস পেজগুলো ডাইনামিকভাবে অলস লোড (lazy load) করা হলো।
const AdminShell = React.lazy(() => import("./pages/admin/AdminShell").then(m => ({ default: m.AdminShell })));
const AgentWorkspace = React.lazy(() => import("./pages/user/AgentWorkspace").then(m => ({ default: m.AgentWorkspace })));
const AIStudio = React.lazy(() => import("./pages/user/AIStudio").then(m => ({ default: m.AIStudio })));
const IdeWorkspace = React.lazy(() => import("./pages/user/IdeWorkspace").then(m => ({ default: m.IdeWorkspace })));
const IntegrationsManager = React.lazy(() => import("./pages/user/IntegrationsManager").then(m => ({ default: m.IntegrationsManager })));
const ArchitectTower = React.lazy(() => import("./pages/user/ArchitectTower").then(m => ({ default: m.ArchitectTower })));
const SkillCatalog = React.lazy(() => import("./pages/user/SkillCatalog").then(m => ({ default: m.SkillCatalog })));
const SwarmMap = React.lazy(() => import("./components/SwarmMap"));
const EvolutionForge = React.lazy(() => import("./pages/user/EvolutionForge/EvolutionForge"));
const BillingPage = React.lazy(() => import("./pages/BillingPage"));
const ProfilePage = React.lazy(() => import("./pages/ProfilePage"));
const ErrorPage = React.lazy(() => import("./pages/ErrorPage"));

import { tierSUserRoutes } from './routes/tierSRoutes';

// বাংলা মন্তব্য: SSE স্ট্রিম হুক মাউন্ট করে ব্যাকএন্ডের রিয়েল অনলাইন স্ট্যাটাস (isServerOnline) সেট করা হচ্ছে
import { useServerStream } from './hooks/useServerStream';
import ErrorBoundary from './components/admin/DashboardErrorBoundary';
import { primeDeviceFingerprint } from "./utils/deviceFingerprint";
import { CommandBar } from './components/layout/CommandBar';

primeDeviceFingerprint(); // বাংলা মন্তব্য: অ্যাপ বুট হওয়ার সাথে সাথে ব্যাকগ্রাউন্ডে ফিঙ্গারপ্রিন্ট হ্যাশ প্রিলোড হচ্ছে

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: unknown) => {
        const err = error as Record<string, unknown>;
        const msg = (err.message as string) || '';
        const status = err.status as number | undefined;
        if (
          status === 401 || status === 403 || status === 429 ||
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

// বাংলা (single-frontend migration, roadmap Phase 1): VITE_PORTAL_TYPE সম্পূর্ণ সরানো হয়েছে।
// এখন একটাই build, একটাই route graph — User (/workspace/*) ও Admin (/admin/*) দুই-ই এই
// অ্যাপের ভেতরে runtime auth + role দিয়ে serve হয়। Landing logic roadmap §6.3 অনুযায়ী:
// Guest → /login · Authenticated User → /workspace · Authenticated Admin → /admin।

import { TranslationProvider } from './i18n/I18nProvider';

/**
 * বাংলা: `/` route-এর runtime landing redirect — কোনো env var নয়, শুধুই trusted
 * auth state থেকে resolve হয় (roadmap §6.3)। Deep link (/admin/overview ইত্যাদি)
 * এই component-এর কাজ নয় — সেগুলো সরাসরি তাদের route-এ যায়।
 */
const LandingRedirect: React.FC = () => {
  const { isChecking, isAuthenticated } = useAuthStatus();
  if (isChecking) return <AuthLoadingSpinner />;
  return <Navigate to={resolveLandingPath(isAuthenticated)} replace />;
};

export const App: React.FC = () => {
  return (
    <ThemeSyncProvider>
      {/* ROOT-CAUSE FIX: main.tsx ইতিমধ্যেই contexts/ToastProvider দিয়ে
          <App /> কে wrap করে রেখেছে (root-level toast system)। এখানে
          components/ui/Toast.tsx-এর আলাদা, incompatible-API (message, type
          বনাম contexts-এর type, message) দ্বিতীয় ToastProvider নেস্ট করা
          ছিল — duplicate_detector.py-তে 97% file-level duplicate হিসেবে
          ধরা পড়েছিল। এটা redundant, তাই সরিয়ে দেওয়া হলো। */}
      <TranslationProvider locale="en">
        <AppContent />
      </TranslationProvider>
    </ThemeSyncProvider>
  );
};

const AppContent: React.FC = () => {
  // বাংলা মন্তব্য: SSE স্ট্রিম কানেক্ট করে সার্ভার অনলাইন স্ট্যাটাস ট্র্যাক করা হচ্ছে
  useServerStream();

  const legacyWorkspace = (
    <UserDashboard />
  );

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <GlobalConfigInitializer>
          <React.Suspense fallback={
            <div className="flex min-h-screen items-center justify-center bg-[var(--sa-canvas)] text-[var(--sa-ink)]">
              <div className="flex items-center gap-3 text-sm font-medium">
                <span className="h-2 w-2 animate-pulse rounded-full bg-[var(--sa-primary)]" aria-hidden="true" />
                <span>Preparing your workspace</span>
              </div>
            </div>
          }>
            <Routes>
              {/* =========================================
                  ONE ROUTE GRAPH — User + Admin in one build
                  (single-frontend migration, roadmap Phase 1)
             ========================================= */}
              {/* GUEST STATE */}
              <Route path="/login" element={
                <GuestRoute>
                  <LoginPage />
                </GuestRoute>
              } />
              <Route path="/register" element={
                <GuestRoute>
                  <RegisterPage />
                </GuestRoute>
              } />
              {/* Runtime landing: Guest → /login · User → /workspace · Admin → /admin */}
              <Route path="/" element={<LandingRedirect />} />

              {/* AUTHENTICATED USER STATE */}
              <Route path="/workspace/agent" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <AgentWorkspace />
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/workspace/ide" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <IdeWorkspace />
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/integrations" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <IntegrationsManager />
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/architect-tower" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <ArchitectTower />
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/swarm" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <SwarmMap />
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/evolution-forge" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <EvolutionForge />
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              {/* বাংলা: /skills-catalog রাউট — রোল-ফিল্টারড ডাইনামিক ক্যাটালগ পেজ */}
              <Route path="/skills-catalog" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <SkillCatalog />
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/billing" element={
                <ProtectedRoute>
                  <RoleGuard requiredRole="user">
                    <PermissionGuard requiredPermission="billing.read">
                      <BillingPage />
                    </PermissionGuard>
                  </RoleGuard>
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
                  <WorkspaceLayout>
                    {legacyWorkspace}
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              {/* Removed duplicate route to avoid duplicate rendering */}
              <Route path="/workspace/live" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <LivingDashboardShell chatPanel={<AIStudio />} />
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />

              {/* বাংলা (Phase 4): /admin/* এর সম্পূর্ণ guard hierarchy —
                  ProtectedRoute (authenticated) → RoleGuard (admin identity — server-signed
                  JWT claim বা backend role) → AdminShell (step-up: Firebase → OTP/TOTP →
                  RBAC)। Backend RBAC প্রতিটি /admin-api ও /api/admin call-এ আবার এনফোর্স করে। */}
              <Route path="/admin/*" element={
                <ProtectedRoute>
                  <RoleGuard requiredRole="admin">
                    <AdminShell />
                  </RoleGuard>
                </ProtectedRoute>
              } />

                {/* ═══ Tier-S Feature Routes ═══ */}
                {tierSUserRoutes.map((r, i) => (
                  <Route key={`tier-s-${i}`} path={r.path!} element={r.element} />
                ))}

              {/* Catch-all 404 Route */}
              <Route path="*" element={<ErrorPage code={404} />} />
            </Routes>
          </React.Suspense>
          {/* বাংলা মন্তব্য: Global Command Palette — সব route-এ Header search / ⌘K triggered; বন্ধ থাকলে UI রেন্ডার হয় না */}
          <CommandBar />
        </GlobalConfigInitializer>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};
