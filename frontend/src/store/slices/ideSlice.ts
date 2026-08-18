import type { StateCreator } from 'zustand';
import { getApiBaseUrl } from '../../utils/api';
import type { SupremeStore } from '../useSupremeStore';

export interface IdeSlice {
  activeFile: string | null;
  openFiles: string[];
  editorContent: Record<string, string>;
  addOpenFile: (filePath: string) => void;
  removeOpenFile: (filePath: string) => void;
  setActiveFile: (filePath: string) => void;
  updateEditorContent: (filePath: string, content: string) => void;
  saveFile: (filePath: string) => Promise<void>;
}

export const createIdeSlice: StateCreator<SupremeStore, [], [], IdeSlice> = (set, get) => ({
  activeFile: null,
  openFiles: [],
  editorContent: {},
  addOpenFile: (filePath) =>
    set((state) => {
      if (!state.openFiles.includes(filePath)) {
        return { openFiles: [...state.openFiles, filePath] };
      }
      return state;
    }),
  removeOpenFile: (filePath) =>
    set((state) => ({
      openFiles: state.openFiles.filter((file) => file !== filePath),
      activeFile:
        state.activeFile === filePath ? state.openFiles.find((file) => file !== filePath) || null : state.activeFile,
    })),
  setActiveFile: (filePath) => set({ activeFile: filePath }),
  updateEditorContent: (filePath, content) =>
    set((state) => ({ editorContent: { ...state.editorContent, [filePath]: content } })),
  saveFile: async (filePath) => {
    set({ loading: true, error: null });
    try {
      await fetch(`${getApiBaseUrl()}/api/files/${encodeURIComponent(filePath)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: get().editorContent[filePath] }),
      });
    } catch {
      set({ error: 'Failed to save file' });
    } finally {
      set({ loading: false });
    }
  },
});
