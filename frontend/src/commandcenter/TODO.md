# AETHEL Command Center — Implementation TODO

## P0: Data Contracts ✅
- [x] `data/types.ts` — all domain types (Metrics, HealthMap, CIReport, Event, Tenant, User, Provider, RouterConfig, CostReport, Backup, FeatureFlag, SecurityScan, Traffic, Usage, ROI)
- [x] `data/hooks.ts` — React Query hooks + `cmdKeys` registry + mutation hooks

## P1: Design System ✅
- [x] `styles/tokens.css` — design tokens (colors, fonts, glow, spacing, 4 themes)
- [x] `kit/KpiTile.tsx` — KPI display tile
- [x] `kit/StatusPill.tsx` — status indicator pill
- [x] `kit/Sparkline.tsx` — pure SVG sparkline
- [x] `kit/GaugeRing.tsx` — circular gauge
- [x] `kit/LogStream.tsx` — live log stream viewer
- [x] `kit/DataTable.tsx` — virtualized data table
- [x] `kit/CommandPalette.tsx` — ⌘K fuzzy search palette
- [x] `kit/JITOTPModal.tsx` — just-in-time OTP confirmation modal
- [x] `kit/HealthStrip.tsx` — health status strip
- [x] `kit/Timeline.tsx` — event timeline
- [x] `kit/JsonViewer.tsx` — JSON data viewer
- [x] `kit/ConfigForm.tsx` — masked config form
- [x] `kit/ConfirmModal.tsx` — confirmation modal
- [x] `kit/ToastStack.tsx` — toast notification stack
- [x] `kit/EmptyState.tsx` — degraded state placeholder
- [x] `kit/MetricStrip.tsx` — metrics strip
- [x] `kit/index.ts` — barrel export

## P1: Shell ✅
- [x] `shell/CommandBar.tsx` — global top command bar
- [x] `shell/LeftRail.tsx` — grouped navigation rail
- [x] `shell/BottomDeck.tsx` — real-time KPI status deck
- [x] `shell/WorkspaceViewport.tsx` — module viewport
- [x] `shell/index.ts` — barrel export

## P2: Realtime Core ✅
- [x] `realtime/channelRegistry.ts` — channel → React Query key mapping (Ripple-Effect Guard)
- [x] `realtime/websocketManager.ts` — WS manager (heartbeat, reconnect, backoff)
- [x] `realtime/sseBridges.ts` — SSE bridges for logs/events
- [x] `realtime/CommandCenterRealtimeProvider.tsx` — provider that bridges WS → queryClient

## State ✅
- [x] `state/useCommandCenterStore.ts` — zustand slice (active module, WS status, palette, theme)

## Entry
- [x] `main.tsx` — CommandCenterApp entry component (provider chain)

## P3: Command Deck ✅
- [x] `modules/deck/CommandDeck.tsx` — home module
  - [x] KPI strip (6 tiles: Active Agents, Active Tasks, RPS, P95 Latency, Error Rate, Cost/hr)
  - [x] System Health Ring (GCP/Railway/Render + core services)
  - [x] Live Event Feed (latest 20 events, color-coded severity)
  - [x] Alert Banner Zone (critical/high alerts + ACKNOWLEDGE button)
  - [x] Provider Load Donut (request distribution)
  - [x] Traffic Sparkline (last 30 min RPS)
  - [x] Quick Action Grid (Deploy, Backup, Security Scan, Gate Lock/Unlock, New Tenant)
  - [ ] Mini Infra Topology (visual node graph)

## P4: Observe Suite ✅
- [x] `modules/observe/LiveMetrics.tsx` — Mini-Grafana metrics dashboard
  - [x] Compute group (CPU/GPU/MEM)
  - [x] Throughput group (RPS, total_requests_24h)
  - [x] Latency group (P50/P95/P99 sparklines)
  - [x] Reliability group (error_rate)
  - [x] Time-range selector (5m/1h/24h)
- [x] `modules/observe/LiveLogs.tsx` — SSE log stream viewer
  - [x] Auto-scroll toggle
  - [x] Level/source/keyword filters
  - [x] Jump to event
  - [x] Export logs
- [x] `modules/observe/EventsExplorer.tsx` — event timeline
- [x] `modules/observe/CICDPipelines.tsx` — CI/CD pipeline visualizer
- [x] `modules/observe/HealthMap.tsx` — infra health map
- [x] `modules/observe/TrafficMonitor.tsx` — live traffic monitor

## P5: Operate Suite ✅
- [x] `modules/operate/Agents.tsx` — agent registry
  - [x] Agent table (name, role, status, task, queue, heartbeat, memory)
  - [x] Row actions (inspect, restart, throttle, kill with OTP)
  - [x] Agent timeline
- [x] `modules/operate/Swarm.tsx` — swarm graph (ReactFlow)
  - [x] Node status (color/glow)
  - [x] Edge load visualization
  - [x] Broadcast controls (pause/resume/sync with OTP)
- [x] `modules/operate/TasksQueues.tsx` — tasks & queues
- [x] `modules/operate/Sessions.tsx` — session management
- [x] `modules/operate/TenantsUsers.tsx` — tenants & users
  - [x] Tenant table with quota bars
  - [x] User CRUD + impersonate (OTP)
  - [x] Tier matrix editor

## P6: Build Suite ✅
- [x] `modules/build/ModelRouter.tsx` — model router panel
  - [x] Provider cards (status, latency, rate limits, models)
  - [x] Router controls (override, A/B split, cost-quality slider)
  - [x] Override modal (OTP)
  - [x] Traffic donut
- [x] `modules/build/Providers.tsx` — provider management
- [x] `modules/build/Skills.tsx` — skills marketplace
- [x] `modules/build/MemoryKnowledge.tsx` — memory & knowledge base
  - [x] Memory banks stats
  - [x] Semantic cache hit-rate
  - [x] Knowledge base index status

## P7: Secure Suite ✅
- [x] `modules/secure/Threats.tsx` — security scan card
  - [x] Last scan time, findings by severity
  - [x] Expandable findings list
  - [x] Re-scan button
- [x] `modules/secure/AuditExplorer.tsx` — audit log explorer
  - [x] Filterable table (timestamp, admin, action, target, result, IP)
- [x] `modules/secure/ApprovalQueue.tsx` — approval queue
  - [x] Pending sensitive ops list
  - [x] Approve/reject with OTP + reason
- [x] `modules/secure/RulesPolicy.tsx` — rules & policies editor
- [x] `modules/secure/SecretsHealth.tsx` — secrets health check
- [x] `modules/secure/RateLimits.tsx` — rate limits monitor

## P8: Money Suite ✅
- [x] `modules/money/CostAuditor.tsx` — cost auditor report
- [x] `modules/money/UsageBilling.tsx` — usage & billing
  - [x] Daily spend chart (30 days)
  - [x] Forecast card
  - [x] Budget caps editor (OTP)
- [x] `modules/money/ROISavings.tsx` — ROI savings strip
  - [x] Semantic cache hits
  - [x] Estimated USD saved
  - [x] API cost reduction ratio

## P9: System + Polish ✅
- [x] `modules/system/ConfigEditor.tsx` — config editor (masked, OTP save)
- [x] `modules/system/FeatureFlags.tsx` — feature flags manager
  - [x] Toggle + rollout % slider
  - [x] Environment selector
- [x] `modules/system/Workspaces.tsx` — workspace admin CRUD
- [x] `modules/system/Backups.tsx` — backup center
  - [x] Backup list (timestamp, size, type, status)
  - [x] Create backup (progress toast)
  - [x] Restore (OTP, dual confirm)
- [x] `modules/system/DeployGate.tsx` — deploy gate control
  - [x] Lock/unlock with OTP + reason
  - [x] Status card
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

## Backend (Python) ✅
- [x] `backend/api/routes/commandcenter/` — aggregate endpoints
  - [x] `overview.py` — P3 Command Deck aggregation
  - [x] `operate.py` — agents, swarm, tasks, sessions, tenants
  - [x] `build.py` — router, providers, skills, memory
  - [x] `observe.py` — metrics, logs, events, CI/CD, health, traffic
  - [x] `secure.py` — threats, audit, approvals, rules, secrets, rate limits
  - [x] `money.py` — cost, usage, billing, ROI
  - [x] `system.py` — config, flags, workspaces, backups, deploy gate
- [x] `backend/ws/command_center.py` — extended dashboard manager
  - [x] Channel registry
  - [x] Event broadcasting
  - [x] JIT OTP verification endpoint
