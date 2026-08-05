import React, { Suspense, lazy } from 'react';
import { useCommandCenterStore } from '../state/useCommandCenterStore';
import { EmptyState } from '../kit';

// ═══════════════════════════════════════════════════════════════════════════
// AETHEL Command Center — Workspace Viewport
// বাংলা মন্তব্য: অ্যাক্টিভ মডিউল ভিউপোর্ট — React.lazy code-splitting
// ═══════════════════════════════════════════════════════════════════════════

// Lazy-loaded module components (code-splitting per module)
const CommandDeck = lazy(() => import('../modules/deck/CommandDeck'));
const LiveMetrics = lazy(() => import('../modules/observe/LiveMetrics'));
const LiveLogs = lazy(() => import('../modules/observe/LiveLogs'));
const EventsExplorer = lazy(() => import('../modules/observe/EventsExplorer'));
const CICDPipelines = lazy(() => import('../modules/observe/CICDPipelines'));
const HealthMap = lazy(() => import('../modules/observe/HealthMap'));
const TrafficMonitor = lazy(() => import('../modules/observe/TrafficMonitor'));
const Agents = lazy(() => import('../modules/operate/Agents'));
const Swarm = lazy(() => import('../modules/operate/Swarm'));
const TasksQueues = lazy(() => import('../modules/operate/TasksQueues'));
const Sessions = lazy(() => import('../modules/operate/Sessions'));
const TenantsUsers = lazy(() => import('../modules/operate/TenantsUsers'));
const ModelRouter = lazy(() => import('../modules/build/ModelRouter'));
const Providers = lazy(() => import('../modules/build/Providers'));
const Skills = lazy(() => import('../modules/build/Skills'));
const MemoryKnowledge = lazy(() => import('../modules/build/MemoryKnowledge'));
const Threats = lazy(() => import('../modules/secure/Threats'));
const AuditExplorer = lazy(() => import('../modules/secure/AuditExplorer'));
const ApprovalQueue = lazy(() => import('../modules/secure/ApprovalQueue'));
const RulesPolicy = lazy(() => import('../modules/secure/RulesPolicy'));
const SecretsHealth = lazy(() => import('../modules/secure/SecretsHealth'));
const RateLimits = lazy(() => import('../modules/secure/RateLimits'));
const CostAuditor = lazy(() => import('../modules/money/CostAuditor'));
const UsageBilling = lazy(() => import('../modules/money/UsageBilling'));
const ROISavings = lazy(() => import('../modules/money/ROISavings'));
const ConfigEditor = lazy(() => import('../modules/system/ConfigEditor'));
const FeatureFlags = lazy(() => import('../modules/system/FeatureFlags'));
const Workspaces = lazy(() => import('../modules/system/Workspaces'));
const Backups = lazy(() => import('../modules/system/Backups'));
const DeployGate = lazy(() => import('../modules/system/DeployGate'));

const MODULE_MAP: Record<string, React.LazyExoticComponent<React.ComponentType>> = {
  deck: CommandDeck,
  metrics: LiveMetrics,
  logs: LiveLogs,
  events: EventsExplorer,
  ci: CICDPipelines,
  health: HealthMap,
  traffic: TrafficMonitor,
  agents: Agents,
  swarm: Swarm,
  tasks: TasksQueues,
  sessions: Sessions,
  tenants: TenantsUsers,
  router: ModelRouter,
  providers: Providers,
  skills: Skills,
  memory: MemoryKnowledge,
  threats: Threats,
  audit: AuditExplorer,
  approvals: ApprovalQueue,
  rules: RulesPolicy,
  secrets: SecretsHealth,
  ratelimits: RateLimits,
  cost: CostAuditor,
  usage: UsageBilling,
  roi: ROISavings,
  config: ConfigEditor,
  flags: FeatureFlags,
  workspaces: Workspaces,
  backups: Backups,
  deploy: DeployGate,
};

export function WorkspaceViewport() {
  const { activeModule } = useCommandCenterStore();
  const ModuleComponent = MODULE_MAP[activeModule];

  return (
    <main className="flex-1 overflow-y-auto p-4">
      <Suspense
        fallback={
          <div className="flex items-center justify-center h-full">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#00f3ff]/30 border-t-[#00f3ff]" />
          </div>
        }
      >
        {ModuleComponent ? (
          <ModuleComponent />
        ) : (
          <EmptyState title="মডিউল পাওয়া যায়নি" message="এই মডিউলটি এখনো তৈরি হয়নি।" />
        )}
      </Suspense>
    </main>
  );
}