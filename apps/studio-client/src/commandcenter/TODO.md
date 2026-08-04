# AETHEL Command Center — Implementation TODO

## P0: Data Contracts
- [ ] `data/types.ts` — all domain types (Metrics, HealthMap, CIReport, Event, Tenant, User, Provider, RouterConfig, CostReport, Backup, FeatureFlag, SecurityScan, Traffic, Usage, ROI)
- [ ] `data/hooks.ts` — React Query hooks (reuse existing `useDashboardData` where possible, add missing domains)

## P1: Design System
- [x] `styles/tokens.css` — design tokens (colors, fonts, glow, spacing)
- [x] `kit/KpiTile.tsx` — KPI display tile
- [x] `kit/StatusPill.tsx` — status indicator pill
- [x] `kit/Sparkline.tsx` — pure SVG sparkline
- [x] `kit/GaugeRing.tsx` — circular gauge
- [x] `kit/LogStream.tsx` — live log stream viewer
- [x] `kit/DataTable.tsx` — virtualized data table
- [ ] `kit/CommandPalette.tsx` — ⌘K fuzzy search palette
- [ ] `kit/JITOTPModal.tsx` — just-in-time OTP confirmation modal
- [ ] `kit/HealthStrip.tsx` — health status strip
- [ ] `kit/Timeline.tsx` — event timeline
- [ ] `kit/JsonViewer.tsx` — JSON data viewer
- [ ] `kit/ConfigForm.tsx` — masked config form
- [ ] `kit/ConfirmModal.tsx` — confirmation modal
- [ ] `kit/ToastStack.tsx` — toast notification stack
- [ ] `kit/EmptyState.tsx` — degraded state placeholder
- [ ] `kit/MetricStrip.tsx` — metrics strip
- [ ] `kit/index.ts` — barrel export

## P1: Shell
- [ ] `shell/CommandBar.tsx` — global top command bar
- [ ] `shell/LeftRail.tsx` — grouped navigation rail
- [ ] `shell/BottomDeck.tsx` — real-time KPI status deck
- [ ] `shell/WorkspaceViewport.tsx` — module viewport
- [ ] `shell/index.ts` — barrel export

## P2: Realtime Core
- [ ] `realtime/channelRegistry.ts` — channel → React Query key mapping
- [ ] `realtime/websocketManager.ts` — WS manager (heartbeat, reconnect, backoff)
- [ ] `realtime/sseBridges.ts` — SSE bridges for logs/events
- [ ] `realtime/CommandCenterRealtimeProvider.tsx` — provider that bridges WS → queryClient

## State
- [x] `state/useCommandCenterStore.ts` — zustand slice (active module, WS status, palette)

## Entry
- [ ] `main.tsx` — CommandCenterApp entry component (provider chain)

## P3: Command Deck
- [ ] `modules/deck/CommandDeck.tsx` — home module
  - [ ] KPI strip (6 tiles: Active Agents, Active Tasks, RPS, P95 Latency, Error Rate, Cost/hr)
  - [ ] System Health Ring (GCP/Railway/Render + core services)
  - [ ] Live Event Feed (latest 20 events, color-coded severity)
  - [ ] Alert Banner Zone (critical/high alerts + ACKNOWLEDGE button)
  - [ ] Provider Load Donut (request distribution)
  - [ ] Traffic Sparkline (last 30 min RPS)
  - [ ] Quick Action Grid (Deploy, Backup, Security Scan, Gate Lock/Unlock, New Tenant)
  - [ ] Mini Infra Topology (visual node graph)

## P4: Observe Suite
- [ ] `modules/observe/LiveMetrics.tsx` — Mini-Grafana metrics dashboard
  - [ ] Compute group (CPU/GPU/MEM)
  - [ ] Throughput group (RPS, total_requests_24h)
  - [ ] Latency group (P50/P95/P99 sparklines)
  - [ ] Reliability group (error_rate)
  - [ ] Time-range selector (5m/1h/24h)
- [ ] `modules/observe/LiveLogs.tsx` — SSE log stream viewer
  - [ ] Auto-scroll toggle
  - [ ] Level/source/keyword filters
  - [ ] Jump to event
  - [ ] Export logs
- [ ] `modules/observe/EventsExplorer.tsx` — event timeline
- [ ] `modules/observe/CICDPipelines.tsx` — CI/CD pipeline visualizer
- [ ] `modules/observe/HealthMap.tsx` — infra health map
- [ ] `modules/observe/TrafficMonitor.tsx` — live traffic monitor

## P5: Operate Suite
- [ ] `modules/operate/Agents.tsx` — agent registry
  - [ ] Agent table (name, role, status, task, queue, heartbeat, memory)
  - [ ] Row actions (inspect, restart, throttle, kill with OTP)
  - [ ] Agent timeline
- [ ] `modules/operate/Swarm.tsx` — swarm graph (ReactFlow)
  - [ ] Node status (color/glow)
  - [ ] Edge load visualization
  - [ ] Broadcast controls (pause/resume/sync with OTP)
- [ ] `modules/operate/TasksQueues.tsx` — tasks & queues
- [ ] `modules/operate/Sessions.tsx` — session management
- [ ] `modules/operate/TenantsUsers.tsx` — tenants & users
  - [ ] Tenant table with quota bars
  - [ ] User CRUD + impersonate (OTP)
  - [ ] Tier matrix editor

## P6: Build Suite
- [ ] `modules/build/ModelRouter.tsx` — model router panel
  - [ ] Provider cards (status, latency, rate limits, models)
  - [ ] Router controls (override, A/B split, cost-quality slider)
  - [ ] Override modal (OTP)
  - [ ] Traffic donut
- [ ] `modules/build/Providers.tsx` — provider management
- [ ] `modules/build/Skills.tsx` — skills marketplace
- [ ] `modules/build/MemoryKnowledge.tsx` — memory & knowledge base
  - [ ] Memory banks stats
  - [ ] Semantic cache hit-rate
  - [ ] Knowledge base index status

## P7: Secure Suite
- [ ] `modules/secure/Threats.tsx` — security scan card
  - [ ] Last scan time, findings by severity
  - [ ] Expandable findings list
  - [ ] Re-scan button
- [ ] `modules/secure/AuditExplorer.tsx` — audit log explorer
  - [ ] Filterable table (timestamp, admin, action, target, result, IP)
- [ ] `modules/secure/ApprovalQueue.tsx` — approval queue
  - [ ] Pending sensitive ops list
  - [ ] Approve/reject with OTP + reason
- [ ] `modules/secure/RulesPolicy.tsx` — rules & policies editor
- [ ] `modules/secure/SecretsHealth.tsx` — secrets health check
- [ ] `modules/secure/RateLimits.tsx` — rate limits monitor

## P8: Money Suite
- [ ] `modules/money/CostAuditor.tsx` — cost auditor report
- [ ] `modules/money/UsageBilling.tsx` — usage & billing
  - [ ] Daily spend chart (30 days)
  - [ ] Forecast card
  - [ ] Budget caps editor (OTP)
- [ ] `modules/money/ROISavings.tsx` — ROI savings strip
  - [ ] Semantic cache hits
  - [ ] Estimated USD saved
  - [ ] API cost reduction ratio

## P9: System + Polish
- [ ] `modules/system/ConfigEditor.tsx` — config editor (masked, OTP save)
- [ ] `modules/system/FeatureFlags.tsx` — feature flags manager
  - [ ] Toggle + rollout % slider
  - [ ] Environment selector
- [ ] `modules/system/Workspaces.tsx` — workspace admin CRUD
- [ ] `modules/system/Backups.tsx` — backup center
  - [ ] Backup list (timestamp, size, type, status)
  - [ ] Create backup (progress toast)
  - [ ] Restore (OTP, dual confirm)
- [ ] `modules/system/DeployGate.tsx` — deploy gate control
  - [ ] Lock/unlock with OTP + reason
  - [ ] Status card
- [ ] Performance optimization
  - [ ] Code splitting (React.lazy per module)
  - [ ] Virtualized tables (>50 rows)
  - [ ] WS payload diffing (2s delta, 30s full snapshot)
  - [ ] Bundle check (initial <250KB gz, total <900KB gz)
- [ ] Quality gates
  - [ ] axe-core scan (0 known issues)
  - [ ] Playwright smoke tests (login→OTP→Deck→each module)
  - [ ] No hardcoded values grep check
  - [ ] WS/SSE error → degraded state test

## Backend (Python)
- [ ] `backend/api/routes/commandcenter/` — aggregate endpoints
  - [ ] `overview.py` — P3 Command Deck aggregation
  - [ ] `operate.py` — agents, swarm, tasks, sessions, tenants
  - [ ] `build.py` — router, providers, skills, memory
  - [ ] `observe.py` — metrics, logs, events, CI/CD, health, traffic
  - [ ] `secure.py` — threats, audit, approvals, rules, secrets, rate limits
  - [ ] `money.py` — cost, usage, billing, ROI
  - [ ] `system.py` — config, flags, workspaces, backups, deploy gate
- [ ] `backend/ws/command_center.py` — extended dashboard manager
  - [ ] Channel registry
  - [ ] Event broadcasting
  - [ ] JIT OTP verification endpoint