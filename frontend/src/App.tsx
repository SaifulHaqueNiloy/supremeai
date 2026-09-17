import React from "react";
import { Routes, Route } from "react-router-dom";
// FINAL-TEST FIX: the QueryClientProvider that used to live here was removed —
// main.tsx already wraps the whole tree in <SharedProviders> (packages/
// ui-components), so this second provider created a *nested duplicate cache* and
// silently won over the outer one. The smart retry policy now lives in
// SharedProviders so the entire app shares exactly one QueryClient.

import { ThemeSyncProvider } from './providers/ThemeSyncProvider';
import { GlobalConfigInitializer } from "./components/core/GlobalConfigInitializer";
import { ProtectedRoute, GuestRoute } from "./components/core/AuthGuards";
import { RoleGuard, PermissionGuard } from "./components/core/guards/RoleGuard";

// Pages (Core Layouts & Auth)
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { WorkspaceLayout } from "./components/layout/WorkspaceLayout";
import { UserDashboard } from "./components/customer/UserDashboard";

// বাংলা মন্তব্য: ক্লায়েন্ট বান্ডেল সাইজ অপ্টিমাইজ করার জন্য হেভি ওয়ার্কস্পেস পেজগুলো ডাইনামিকভাবে অলস লোড (lazy load) করা হলো।
const AdminShell = React.lazy(() => import("./pages/admin/AdminShell").then(m => ({ default: m.AdminShell })));
const AgentWorkspace = React.lazy(() => import("./pages/user/AgentWorkspace").then(m => ({ default: m.AgentWorkspace })));
const AIStudio = React.lazy(() => import("./pages/user/AIStudio").then(m => ({ default: m.AIStudio })));
const IdeWorkspace = React.lazy(() => import("./pages/user/IdeWorkspace").then(m => ({ default: m.IdeWorkspace })));
const IntegrationsManager = React.lazy(() => import("./pages/user/IntegrationsManager").then(m => ({ default: m.IntegrationsManager })));
const SystemHealthDashboard = React.lazy(() => import("./pages/user/SystemHealthDashboard").then(m => ({ default: m.SystemHealthDashboard })));
const SkillCatalog = React.lazy(() => import("./pages/user/SkillCatalog").then(m => ({ default: m.SkillCatalog })));
const SwarmMap = React.lazy(() => import("./components/SwarmMap"));
const SwarmArchitect = React.lazy(() => import("./pages/user/SwarmArchitect/SwarmArchitect").then(m => ({ default: m.default })));
const BillingPage = React.lazy(() => import("./pages/BillingPage"));
const CostDashboard = React.lazy(() => import("./pages/user/CostDashboard").then(m => ({ default: m.CostDashboard })));
const ProfilePage = React.lazy(() => import("./pages/ProfilePage"));
const ErrorPage = React.lazy(() => import("./pages/ErrorPage"));
const DeepResearchPanel = React.lazy(() => import("./components/research/DeepResearchPanel"));
const ScheduledTasksPanel = React.lazy(() => import("./components/schedule/ScheduledTasksPanel"));
const MemoryPanel = React.lazy(() => import("./components/memory/MemoryPanel"));
const SecretsPage = React.lazy(() => import("./components/dashboard/SecretsPage").then(m => ({ default: m.SecretsPage })));

// RESTORE-AND-WIRE (2026-09-14): previously-deleted capability pages are restored
// AND routed again — per repo doctrine ("near-ready = wire it"; deletion without
// admin approval is forbidden). Lazy-loaded to keep the main bundle lean.
const RealSettingsPage = React.lazy(() => import("./pages/user/WorkspaceSettingsPage"));
const VaultPage = React.lazy(() => import("./components/dashboard/VaultPage").then(m => ({ default: m.VaultPage })));
const ConnectedPlatformsVault = React.lazy(() => import("./components/dashboard/ConnectedPlatformsVault"));
const AutomationQueuePage = React.lazy(() => import("./components/dashboard/AutomationQueuePage").then(m => ({ default: m.AutomationQueuePage })));
const LlmGatewayPage = React.lazy(() => import("./components/dashboard/LlmGatewayPage").then(m => ({ default: m.LlmGatewayPage })));
// বাংলা মন্তব্য: Task-12 ghost activation — KnowledgePage ও Session Cockpit আগে
// কোনো route-এ mounted ছিল না (dead files), এখন প্রকৃত backend endpoint-এর সাথে
// wire করে reachable করা হলো (RESTORE-AND-WIRE প্যাটার্নের মতোই)।
const KnowledgePage = React.lazy(() => import("./components/dashboard/KnowledgePage").then(m => ({ default: m.KnowledgePage })));
const SessionDetailRoute = React.lazy(() => import("./pages/user/SessionDetailRoute").then(m => ({ default: m.SessionDetailRoute })));
const TelemetryCockpitPage = React.lazy(() => import("./pages/user/TelemetryCockpitPage"));
// AETHEL Command Center shell (restored sub-app; backend routes + e2e spec exist)
const CommandCenterApp = React.lazy(() => import("./commandcenter/shell/CommandCenterApp").then(m => ({ default: m.CommandCenterApp })));

import { workspaceFeatureRoutes } from './routes/workspaceFeatureRoutes';

// বাংলা মন্তব্য: SSE স্ট্রিম হুক মাউন্ট করে ব্যাকএন্ডের রিয়েল অনলাইন স্ট্যাটাস (isServerOnline) সেট করা হচ্ছে
import ErrorBoundary from './components/admin/DashboardErrorBoundary';
import { RouteBoundary } from './router/RouteBoundary';

// বাংলা মন্তব্য (Wave 3): বাকি ১০টি eager page import-ও React.lazy করা হলো —
// ২৬টি lazy page-এর মতোই একই top-level Suspense-এর নিচে চলে, main chunk ছোট থাকে।
const GuestChatPage = React.lazy(() => import("./pages/PublicPages"));
const ModelsPage = React.lazy(() => import("./pages/PublicPages").then(m => ({ default: m.ModelsPage })));
const PublicInfoPage = React.lazy(() => import("./pages/PublicPages").then(m => ({ default: m.PublicInfoPage })));
const PricingPage = React.lazy(() => import("./pages/PublicPages").then(m => ({ default: m.PricingPage })));
const RunsPage = React.lazy(() => import("./pages/RunsPage"));
const MarketplacePage = React.lazy(() => import("./pages/MarketplacePage"));
const ActivityPage = React.lazy(() => import("./pages/ActivityPage"));
const FilesPage = React.lazy(() => import("./pages/FilesPage"));
const ProjectsPage = React.lazy(() => import("./pages/ProjectsPage"));
const MCPConnector = React.lazy(() => import("./components/plugins/MCPConnector").then(m => ({ default: m.MCPConnector })));

// The public viewer is intentionally available before authentication: a shared URL is
// enough to read data. Authentication and role checks remain for private workspaces;
// admin step-up security stays isolated to /admin and must not leak into viewer routes.

import { TranslationProvider } from './i18n/I18nProvider';

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
  // Basic viewer pages render without a global realtime connection. Live updates
  // should be opted into by the one page that actually displays live data.
  const legacyWorkspace = (
    <UserDashboard />
  );

  return (
    <ErrorBoundary>
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
                  <RouteBoundary>
                    <LoginPage />
                  </RouteBoundary>
                </GuestRoute>
              } />
              <Route path="/register" element={
                <GuestRoute>
                  <RouteBoundary>
                    <RegisterPage />
                  </RouteBoundary>
                </GuestRoute>
              } />
              {/* Public funnel: guest chat first, then progressive auth when value is clear. */}
              <Route path="/" element={<RouteBoundary><GuestChatPage /></RouteBoundary>} />
              {/* Public viewer path: shared URLs should work without forcing a normal viewer through login. */}
              <Route path="/viewer" element={<RouteBoundary><MCPConnector /></RouteBoundary>} />
              <Route path="/features" element={<RouteBoundary><PublicInfoPage kind="/features" /></RouteBoundary>} />
              <Route path="/models" element={<RouteBoundary><ModelsPage /></RouteBoundary>} />
              <Route path="/pricing" element={<RouteBoundary><PricingPage /></RouteBoundary>} />
              <Route path="/docs" element={<RouteBoundary><PublicInfoPage kind="/docs" /></RouteBoundary>} />
              <Route path="/about" element={<RouteBoundary><PublicInfoPage kind="/about" /></RouteBoundary>} />
              <Route path="/contact" element={<RouteBoundary><PublicInfoPage kind="/contact" /></RouteBoundary>} />

              {/* AUTHENTICATED USER STATE */}
              <Route path="/workspace/agent" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <RouteBoundary><AgentWorkspace /></RouteBoundary>
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/workspace/ide" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <RouteBoundary><IdeWorkspace /></RouteBoundary>
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/integrations" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <RouteBoundary><IntegrationsManager /></RouteBoundary>
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/architect-tower" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <RouteBoundary><SystemHealthDashboard /></RouteBoundary>
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/swarm" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <RouteBoundary><SwarmMap /></RouteBoundary>
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/evolution-forge" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <RouteBoundary><SwarmArchitect /></RouteBoundary>
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              {/* বাংলা: /skills-catalog রাউট — রোল-ফিল্টারড ডাইনামিক ক্যাটালগ পেজ */}
              <Route path="/skills-catalog" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <RouteBoundary><SkillCatalog /></RouteBoundary>
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              <Route path="/billing" element={
                <ProtectedRoute>
                  <RoleGuard requiredRole="user">
                    <PermissionGuard requiredPermission="billing.read">
                      <RouteBoundary>
                        <BillingPage />
                      </RouteBoundary>
                    </PermissionGuard>
                  </RoleGuard>
                </ProtectedRoute>
              } />
              <Route path="/profile" element={
                <ProtectedRoute>
                  <RouteBoundary><ProfilePage /></RouteBoundary>
                </ProtectedRoute>
              } />
  <Route path="/projects" element={<ProtectedRoute><RouteBoundary><ProjectsPage /></RouteBoundary></ProtectedRoute>} />
  <Route path="/files" element={<ProtectedRoute><RouteBoundary><FilesPage /></RouteBoundary></ProtectedRoute>} />
  <Route path="/agents" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><AgentWorkspace /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/activity" element={<ProtectedRoute><RouteBoundary><ActivityPage /></RouteBoundary></ProtectedRoute>} />
  <Route path="/marketplace" element={<ProtectedRoute><RouteBoundary><MarketplacePage /></RouteBoundary></ProtectedRoute>} />
  <Route path="/runs" element={<ProtectedRoute><RouteBoundary><RunsPage /></RouteBoundary></ProtectedRoute>} />
  <Route path="/usage" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><CostDashboard /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/research" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><DeepResearchPanel /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/scheduled-tasks" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><ScheduledTasksPanel /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/memory" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><MemoryPanel /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/settings" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><RealSettingsPage /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/settings/api-keys" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><SecretsPage /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  {/* RESTORE-AND-WIRE (2026-09-14): restored capability pages, now reachable */}
  <Route path="/vault" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><VaultPage /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/platform-vault" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><ConnectedPlatformsVault /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/automation-queue" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><AutomationQueuePage /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/llm-gateway" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><LlmGatewayPage /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/telemetry" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><TelemetryCockpitPage /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  {/* বাংলা মন্তব্য: Task-12 activation — /knowledge পেজটি ব্যাকএন্ড POST /api/knowledge/search +
      /api/knowledge/seed (দুটিই আগে orphan) ব্যবহার করে; /sessions/:sessionId ককপিটটি
      ব্যাকএন্ডের প্রকৃত SSE স্ট্রিম GET /api/session/{id}/stream-এর সাথে wire করা। */}
  <Route path="/knowledge" element={<ProtectedRoute><WorkspaceLayout><RouteBoundary><KnowledgePage /></RouteBoundary></WorkspaceLayout></ProtectedRoute>} />
  <Route path="/sessions/:sessionId" element={<ProtectedRoute><RouteBoundary><SessionDetailRoute /></RouteBoundary></ProtectedRoute>} />
  <Route path="/commandcenter" element={<ProtectedRoute><React.Suspense fallback={null}><RouteBoundary><CommandCenterApp /></RouteBoundary></React.Suspense></ProtectedRoute>} />
  {/* বাংলা মন্তব্য: ড্যাশবোর্ড এবং লাইভ ওয়ার্কস্পেস রাউট সুরক্ষিত করার জন্য ProtectedRoute ব্যবহার করা হলো */}
  <Route path="/workspace" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <RouteBoundary>
                      {legacyWorkspace}
                    </RouteBoundary>
                  </WorkspaceLayout>
                </ProtectedRoute>
              } />
              {/* Removed duplicate route to avoid duplicate rendering */}
              <Route path="/workspace/live" element={
                <ProtectedRoute>
                  <WorkspaceLayout>
                    <RouteBoundary><AIStudio /></RouteBoundary>
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
                    <RouteBoundary>
                      <AdminShell />
                    </RouteBoundary>
                  </RoleGuard>
                </ProtectedRoute>
              } />

                {/* ═══ Tier-S Feature Routes ═══ */}
                {workspaceFeatureRoutes.map((r, i) => (
                  <Route key={`tier-s-${i}`} path={r.path!} element={<RouteBoundary>{r.element}</RouteBoundary>} />
                ))}

              {/* Catch-all 404 Route */}
              <Route path="*" element={<RouteBoundary><ErrorPage code={404} /></RouteBoundary>} />
            </Routes>
          </React.Suspense>
      </GlobalConfigInitializer>
    </ErrorBoundary>
  );
};
