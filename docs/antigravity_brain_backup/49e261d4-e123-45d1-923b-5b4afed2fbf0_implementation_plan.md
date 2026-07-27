# Goal Description

The goal is to resolve the **Layout Fragmentation** and memory overlap issue in the Admin Dashboard. Currently, heavy layouts (`CommandCenter` or `RedesignedDashboardMockup`) remain mounted in the background while other modules render on top of them as overlays. This causes multiple complex layouts to exist simultaneously, leading to performance degradation and possible race conditions.

We will refactor this into a **"Layout-as-a-Component"** mapping pattern, ensuring that only one layout or module is mounted in the DOM at any given time.

## User Review Required

> [!WARNING]
> By removing the "background overlay" approach, the aesthetic will change slightly: modules will now render as full-page components replacing the canvas, rather than floating on top of a dimmed background. Please confirm this aligns with your vision.

> [!TIP]
> I will maintain a unified wrapper to preserve the "MODULE: [NAME]" header and the "Close" button for navigation back to the main canvas, ensuring no UX is lost.

## Proposed Changes

### Dashboard Component
#### [MODIFY] src/components/admin/AdminSubTabContent.tsx
- Create a `MODULE_MAP` object mapping `AdminSubTab` strings to their respective React components.
- Remove the `isOverlayOpen` CSS-based hiding logic (`opacity-40`, `pointer-events-none`).
- Replace the multiple conditional rendering blocks with a single dynamic component lookup: `const SelectedModule = MODULE_MAP[adminSubTab] || RedesignedDashboardMockup;`
- Render only the `SelectedModule`, wrapping it in the header/close-button UI if it is not the main dashboard or command center. This guarantees previous layouts are fully unmounted.

## Verification Plan

### Automated Tests
- Run `pnpm run build` to verify TypeScript typings for the dynamic component map.

### Manual Verification
- In the local dev server (`pnpm dev`), navigate between the "AI Core" (Command Center) and other sidebar modules.
- Inspect the React Component Tree to verify that `RedesignedDashboardMockup` is fully unmounted when `ModelRouter` is active.
