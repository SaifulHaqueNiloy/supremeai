# Complete Browser-Based IDE Implementation

This plan outlines the architecture for upgrading the current chat-based interface into a fully-fledged Browser-Based IDE (Step 2 - P1 enhancement).

## 🎯 Goal
Transform `AgentWorkspace.tsx` from a simple chat + single-file editor into a multi-pane IDE that includes a File Explorer, multiple tabs, an AI Chat assistant, and an interactive Terminal powered by WebContainers.

## ⚠️ User Review Required
> [!IMPORTANT]
> To achieve smooth panel resizing (like VS Code), I propose adding `react-resizable-panels`. Please approve this new dependency. 
> Command: `pnpm add react-resizable-panels` inside `apps/studio-client`.

## ❓ Open Questions
> [!WARNING]
> Do you want to keep the IDE within `AgentWorkspace.tsx` (replacing the current layout) or should I create a new dedicated page like `IdeWorkspace.tsx` so users can switch between the basic chat and the full IDE?

## 🛠 Proposed Changes

### apps/studio-client/package.json
- Add `react-resizable-panels` for drag-to-resize split panes.

### apps/studio-client/src/components/editor/
#### [NEW] [FileExplorer.tsx](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/components/editor/FileExplorer.tsx)
A new component that uses `WebContainer.fs.readdir` to recursively list files and folders. It will allow users to click and open files in the editor.

#### [NEW] [EditorTabs.tsx](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/components/editor/EditorTabs.tsx)
A tab strip at the top of the Monaco Editor to manage multiple open files.

### apps/studio-client/src/pages/
#### [MODIFY] [AgentWorkspace.tsx](file:///c:/Users/n/supremeai/supremeai_2.0/apps/studio-client/src/pages/AgentWorkspace.tsx)
- Integrate `react-resizable-panels` to create three main resizable areas:
  1. Left: AI Chat
  2. Middle: File Explorer
  3. Right: Monaco Editor + Terminal (split vertically)
- Add state management for `activeFile`, `openFiles`, and file contents.
- Sync file saves from the Monaco Editor back to the WebContainer file system (`WebContainer.fs.writeFile`).

## ✅ Verification Plan

### Manual Verification
1. Run `pnpm dev` in `apps/studio-client`.
2. Open the IDE page in the browser.
3. Use the AI Chat to ask it to "create a simple node server".
4. Verify that the AI creates files, which then appear in the new File Explorer.
5. Verify that clicking on a file opens it in a new tab in the Monaco editor.
6. Verify that running `node server.js` in the Terminal works as expected.
