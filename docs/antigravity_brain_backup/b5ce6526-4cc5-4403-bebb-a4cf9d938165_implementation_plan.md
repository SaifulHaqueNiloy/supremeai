# Redesign Customer Dashboard (User Workspace) with Aethel Core Theme

We will restore path-based routing in the client app and redesign the default landing customer view to match the "User Workspace" plan: Central AI Core (Personal Hub), connected floating skill nodes, glassmorphic chat panel on the right, and bottom voice waveform bar.

## User Review Required

None.

## Proposed Changes

### Frontend User Workspace Redesign

---

#### [MODIFY] [App.tsx](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/App.tsx)
- Re-introduce `isAdminMode()` helper.
- Update default landing page render block:
  - Header: Aethel Central Workspace HUD.
  - Left/Center area: React Flow graph with a pulsing circular `Central AI Core` and connected skill nodes (`Code Arch`, `Data Analyzer`, `Web Research`, `Custom Node`).
  - Right area: Glassmorphic chat console panel with prompt input.
  - Bottom area: Floating voice command bar with active waveform animation.

---

## Verification Plan

### Manual Verification
- Verify compilation passes with no TypeScript or lint warnings.
- Run dev server and inspect both user dashboard (`/`) and admin dashboard (`/admin`).
