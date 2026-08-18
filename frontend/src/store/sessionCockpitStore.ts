// apps/studio-client/src/store/sessionCockpitStore.ts
// 🛡️ M0.2 MIGRATION: This store is now a backward-compat shim.
// All session cockpit state has been merged into useSupremeStore via sessionCockpitSlice.
import { useSupremeStore } from './useSupremeStore';
import type {
  SessionCockpitSlice,
  SujonState,
  LogEntry,
  FileNode,
  ReasoningEntry,
} from './slices/sessionCockpitSlice';

export type { SujonState, LogEntry, FileNode, ReasoningEntry };
export const useSessionCockpitStore = useSupremeStore;
export type SessionCockpitState = SessionCockpitSlice;
