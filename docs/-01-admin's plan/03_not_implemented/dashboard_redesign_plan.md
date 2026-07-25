# Dashboard Redesign Plan

## Overview
UI/UX redesign plan for the React/Vite Studio Client dashboard with focus on modern design patterns and Bangla language support.

## Original Plan
- CSS design tokens unification
- Glassmorphism design system
- Admin God-Mode Panel
- Agent Console
- Flutter theme sync

---

## 🔍 Codebase Audit (2026-07-26)

### Status: 🟡 Partially Implemented

The React studio-client dashboard already exists with glassmorphism, dark/light mode, and 28+ components. The redesign plan should focus on refinement rather than building from scratch.

### What Already Exists

| Component | Code Location | Why It's Better |
|-----------|--------------|-----------------|
| **Glassmorphism Design** | `apps/studio-client/src/components/admin/` | Already implemented with `glass-card` CSS class, Framer Motion animations, Space Grotesk font |
| **Dark/Light Mode** | `apps/studio-client/src/` | `useTheme` context already active |
| **Admin God-Mode Panel** | `apps/studio-client/src/components/admin/VisualRulesBuilder.tsx`, `RulesEnginePanel.tsx` | Already exists with constitutional rules integration |
| **Agent Console** | `apps/studio-client/src/components/admin/CommandCenter.tsx` (28,532 chars) | Full ReactFlow-based agent network visualization |
| **Design Tokens** | Standalone (`admin/dashboard/`) vs Studio-Client | Need unification — standalone uses `#3b82f6` (blue), studio uses `#00f3ff` (cyan) |

### What Still Needs Work

| Missing Piece | Effort |
|--------------|--------|
| Unify design tokens across standalone + studio-client | 2 days |
| Flutter theme sync (match web design tokens) | 2 days |
| Bangla UI activation via i18next | 3 days |

### Recommendation
The redesign is mostly about refinement: unify design tokens, activate Bangla UI, and sync the Flutter theme. The core design system (glassmorphism, animations, dark/light mode) is already in place and well-implemented.
