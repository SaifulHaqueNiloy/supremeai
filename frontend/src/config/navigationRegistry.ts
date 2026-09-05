// SupremeAI — Navigation Registry (single-frontend migration, roadmap Phase 6)
// বাংলা মন্তব্য: এটিই একমাত্র navigation source of truth। User sidebar, Admin sidebar
// এবং command registry — সবাই এখান থেকে generate হয়। দ্বিতীয় কোনো nav definition লেখা
// যাবে না (roadmap Rule 8/§11)।
//
// নিয়ম:
// - প্রতিটি visible item অবশ্যই implemented route/action নির্দেশ করবে — মৃত লিংক নিষিদ্ধ।
// - status: 'planned' আইটেম registry-তে থাকে কিন্তু রেন্ডার হয় না (roadmap §11:
//   "Do not silently leave dead navigation" + unauthorized/planned UI available
//   functionality হিসেবে দেখানো যাবে না)।
// - roles field শুধু কোন context-এ দেখানো হবে তা ঠিক করে — privilege দেয় না।

import {
  Home,
  MessageSquare,
  Cpu,
  Box,
  Plug,
  Zap,
  CreditCard,
  Activity,
  Network,
  ServerCog,
  BrainCircuit,
  Shield,
  FileCheck2,
  AlertTriangle,
  GitMerge,
  RefreshCcw,
  Users,
  DollarSign,
  Search,
  Wrench,
  Terminal,
  type LucideIcon,
} from 'lucide-react';
import type { Role } from './permissions';

export type NavContext = 'user' | 'admin';

export type NavItemStatus = 'implemented' | 'planned' | 'deprecated';

export interface NavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  /** Route-target item — must match a real route in App.tsx. */
  kind: 'route';
  path: string;
  /** Which contexts may SEE this item (UX only; backend remains authoritative). */
  contexts: NavContext[];
  /** Admin step-up is enforced separately inside AdminShell. */
  requiredRole?: Role;
  requiredPermission?: string;
  status: NavItemStatus;
  /** Lower renders first within its group. */
  priority?: number;
}

export interface NavActionItem {
  id: string;
  label: string;
  icon: LucideIcon;
  /** In-context action (e.g. admin subtab switch) — no navigation. */
  kind: 'action';
  /** Event/action id dispatched to the owning context (admin subtab id). */
  actionId: string;
  contexts: NavContext[];
  requiredRole?: Role;
  requiredPermission?: string;
  status: NavItemStatus;
  priority?: number;
}

export type NavEntry = NavItem | NavActionItem;

export interface NavGroup {
  id: string;
  label: string;
  contexts: NavContext[];
  items: NavEntry[];
}

// ─────────────────────────────────────────────────────────────────────────
// Registry
// ─────────────────────────────────────────────────────────────────────────

export const NAVIGATION_REGISTRY: NavGroup[] = [
  {
    id: 'build',
    label: 'Build',
    contexts: ['user'],
    items: [
      { id: 'nav-home', label: 'Home', icon: Home, kind: 'route', path: '/workspace', contexts: ['user'], status: 'implemented', priority: 10 },
      { id: 'nav-ai-studio', label: 'AI Studio', icon: MessageSquare, kind: 'route', path: '/workspace/live', contexts: ['user'], status: 'implemented', priority: 20 },
      { id: 'nav-agents', label: 'Agents', icon: Cpu, kind: 'route', path: '/workspace/agent', contexts: ['user'], status: 'implemented', priority: 30 },
      // Planned features — routes not yet implemented; rendered হয় না (dead-link prevention)।
      { id: 'nav-projects', label: 'Projects', icon: Box, kind: 'route', path: '/projects', contexts: ['user'], status: 'planned', priority: 40 },
      { id: 'nav-activity', label: 'Activity', icon: Activity, kind: 'route', path: '/activity', contexts: ['user'], status: 'planned', priority: 50 },
    ],
  },
  {
    id: 'extend',
    label: 'Extend',
    contexts: ['user'],
    items: [
      { id: 'nav-skills', label: 'Skills', icon: Box, kind: 'route', path: '/skills-catalog', contexts: ['user'], status: 'implemented', priority: 10 },
      { id: 'nav-integrations', label: 'Integrations', icon: Plug, kind: 'route', path: '/integrations', contexts: ['user'], status: 'implemented', priority: 20 },
      { id: 'nav-marketplace', label: 'Marketplace', icon: Plug, kind: 'route', path: '/marketplace', contexts: ['user'], status: 'planned', priority: 30 },
    ],
  },
  {
    id: 'observe',
    label: 'Observe',
    contexts: ['user'],
    items: [
      { id: 'nav-swarm', label: 'Swarm Map', icon: Network, kind: 'route', path: '/swarm', contexts: ['user'], status: 'implemented', priority: 10 },
      { id: 'nav-evolution-forge', label: 'Evolution Forge', icon: Zap, kind: 'route', path: '/evolution-forge', contexts: ['user'], status: 'implemented', priority: 20 },
      { id: 'nav-architect-tower', label: 'Architect Tower', icon: BrainCircuit, kind: 'route', path: '/architect-tower', contexts: ['user'], status: 'implemented', priority: 30 },
      { id: 'nav-runs', label: 'Runs', icon: Zap, kind: 'route', path: '/runs', contexts: ['user'], status: 'planned', priority: 40 },
    ],
  },
  {
    id: 'govern',
    label: 'Govern',
    contexts: ['user'],
    items: [
      { id: 'nav-usage', label: 'Usage', icon: Activity, kind: 'route', path: '/usage', contexts: ['user'], status: 'planned', priority: 10 },
      { id: 'nav-billing', label: 'Billing', icon: CreditCard, kind: 'route', path: '/billing', contexts: ['user'], status: 'implemented', priority: 20 },
    ],
  },
  {
    id: 'account',
    label: 'Account',
    contexts: ['user'],
    items: [
      { id: 'nav-profile', label: 'Profile', icon: Users, kind: 'route', path: '/profile', contexts: ['user'], status: 'implemented', priority: 10 },
      { id: 'nav-ide', label: 'Code Editor', icon: Wrench, kind: 'route', path: '/workspace/ide', contexts: ['user'], status: 'implemented', priority: 20 },
      { id: 'nav-settings', label: 'Settings', icon: Wrench, kind: 'route', path: '/settings', contexts: ['user'], status: 'planned', priority: 30 },
    ],
  },
  {
    id: 'admin-operations',
    label: 'Operations',
    contexts: ['admin'],
    items: [
      { id: 'admin-nav-overview', label: 'Overview', icon: Activity, kind: 'action', actionId: 'overview', contexts: ['admin'], status: 'implemented', priority: 10 },
      { id: 'admin-nav-topology', label: 'Topology', icon: Network, kind: 'action', actionId: 'topology', contexts: ['admin'], status: 'implemented', priority: 20 },
      { id: 'admin-nav-service-explorer', label: 'Service Explorer', icon: ServerCog, kind: 'action', actionId: 'service-explorer', contexts: ['admin'], status: 'implemented', priority: 30 },
      { id: 'admin-nav-agents-swarm', label: 'Agents / Swarm', icon: BrainCircuit, kind: 'action', actionId: 'agents-swarm', contexts: ['admin'], status: 'implemented', priority: 40 },
      { id: 'admin-nav-deployments', label: 'Deployments', icon: GitMerge, kind: 'action', actionId: 'deployments', contexts: ['admin'], status: 'implemented', priority: 50 },
    ],
  },
  {
    id: 'admin-security',
    label: 'Security',
    contexts: ['admin'],
    items: [
      { id: 'admin-nav-security', label: 'Security', icon: Shield, kind: 'action', actionId: 'security', contexts: ['admin'], status: 'implemented', priority: 10 },
      { id: 'admin-nav-audit', label: 'Audit', icon: FileCheck2, kind: 'action', actionId: 'audit', contexts: ['admin'], status: 'implemented', priority: 20 },
      { id: 'admin-nav-incidents', label: 'Incidents', icon: AlertTriangle, kind: 'action', actionId: 'incidents', contexts: ['admin'], status: 'implemented', priority: 30 },
      { id: 'admin-nav-reliability', label: 'Reliability', icon: Zap, kind: 'action', actionId: 'reliability', contexts: ['admin'], status: 'implemented', priority: 40 },
      { id: 'admin-nav-recovery', label: 'Recovery', icon: RefreshCcw, kind: 'action', actionId: 'recovery', contexts: ['admin'], status: 'implemented', priority: 50 },
    ],
  },
  {
    id: 'admin-governance',
    label: 'Governance',
    contexts: ['admin'],
    items: [
      { id: 'admin-nav-tenants-rbac', label: 'Tenants / RBAC', icon: Users, kind: 'action', actionId: 'tenants-rbac', contexts: ['admin'], status: 'implemented', priority: 10 },
      { id: 'admin-nav-finops', label: 'FinOps', icon: DollarSign, kind: 'action', actionId: 'finops', contexts: ['admin'], status: 'implemented', priority: 20 },
      { id: 'admin-nav-rca-intelligence', label: 'RCA / Intelligence', icon: Search, kind: 'action', actionId: 'rca-intelligence', contexts: ['admin'], status: 'implemented', priority: 30 },
      { id: 'admin-nav-configuration', label: 'Configuration', icon: Wrench, kind: 'action', actionId: 'configuration', contexts: ['admin'], status: 'implemented', priority: 40 },
    ],
  },
  {
    id: 'admin-core',
    label: 'Core',
    contexts: ['admin'],
    items: [
      { id: 'admin-nav-command-center', label: 'Core Canvas', icon: Terminal, kind: 'action', actionId: 'command-center', contexts: ['admin'], status: 'implemented', priority: 10 },
    ],
  },
];

// ─────────────────────────────────────────────────────────────────────────
// Selectors
// ─────────────────────────────────────────────────────────────────────────

export interface NavFilterOptions {
  /** Extra permission strings the viewer holds (backend-resolved). */
  permissions?: string[];
  /** Include non-implemented items (defaults to false — never render dead nav). */
  includePlanned?: boolean;
}

/**
 * বাংলা: context অনুযায়ী registry filter — শুধু implemented + context-valid +
 * permission-valid আইটেম রিটার্ন করে। Role/permission এখানে শুধু visibility —
 * আসল authorization backend-এ হয়।
 */
export function getNavigationForContext(
  context: NavContext,
  options: NavFilterOptions = {}
): NavGroup[] {
  const { permissions, includePlanned = false } = options;
  return NAVIGATION_REGISTRY
    .filter((group) => group.contexts.includes(context))
    .map((group) => ({
      ...group,
      items: group.items
        .filter((item) => {
          if (!item.contexts.includes(context)) return false;
          if (!includePlanned && item.status !== 'implemented') return false;
          if (item.requiredPermission && permissions && permissions.length > 0) {
            if (!permissions.includes(item.requiredPermission)) return false;
          }
          return true;
        })
        .sort((a, b) => (a.priority ?? 100) - (b.priority ?? 100)),
    }))
    .filter((group) => group.items.length > 0);
}

/** Registry entry lookup by id (guards against duplicate ids at dev time). */
export function getNavEntryById(id: string): NavEntry | undefined {
  for (const group of NAVIGATION_REGISTRY) {
    const hit = group.items.find((item) => item.id === id);
    if (hit) return hit;
  }
  return undefined;
}

/** All route paths referenced by implemented route items (used by CI nav gate). */
export function getImplementedRoutePaths(): string[] {
  return NAVIGATION_REGISTRY
    .flatMap((g) => g.items)
    .filter((i): i is NavItem => i.kind === 'route' && i.status === 'implemented')
    .map((i) => i.path);
}
