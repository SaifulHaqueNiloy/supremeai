import type { StateCreator } from 'zustand';
import type { WebContainer } from '@webcontainer/api';
import { getApiBaseUrl } from '../../utils/api';
import type { SupremeStore } from '../useSupremeStore';

export interface IdeFile {
  path: string;
  name: string;
  content: string;
  language: string;
  isModified: boolean;
}

export interface IdeSlice {
  webContainer: WebContainer | null;
  setWebContainer: (instance: WebContainer) => void;

  files: Record<string, IdeFile>;
  openFiles: string[];
  activeFile: string | null;
  editorContent: Record<string, string>;

  setActiveFile: (path: string) => void;
  openFile: (file: IdeFile) => void;
  closeFile: (path: string) => void;
  updateFileContent: (path: string, content: string) => void;
  markFileSaved: (path: string) => void;

  addOpenFile: (filePath: string) => void;
  removeOpenFile: (filePath: string) => void;
  updateEditorContent: (filePath: string, content: string) => void;
  saveFile: (filePath: string) => Promise<void>;
}

export const createIdeSlice: StateCreator<SupremeStore, [], [], IdeSlice> = (set, get) => ({
  webContainer: null,
  setWebContainer: (instance) => set({ webContainer: instance }),

  files: {},
  openFiles: [],
  activeFile: null,
  editorContent: {},

  setActiveFile: (path) => set({ activeFile: path }),

  openFile: (file) =>
    set((state) => {
      const updatedFiles = { ...state.files, [file.path]: file };
      const updatedOpenFiles = state.openFiles.includes(file.path)
        ? state.openFiles
        : [...state.openFiles, file.path];

      return {
        files: updatedFiles,
        openFiles: updatedOpenFiles,
        activeFile: file.path,
      };
    }),

  closeFile: (path) =>
    set((state) => {
      const newOpenFiles = state.openFiles.filter((p) => p !== path);
      return {
        openFiles: newOpenFiles,
        activeFile:
          state.activeFile === path
            ? newOpenFiles.length > 0
              ? newOpenFiles[newOpenFiles.length - 1]
              : null
            : state.activeFile,
      };
    }),

  updateFileContent: (path, content) =>
    set((state) => {
      const file = state.files[path];
      if (!file) return state;
      return {
        files: {
          ...state.files,
          [path]: { ...file, content, isModified: true },
        },
        editorContent: {
          ...state.editorContent,
          [path]: content,
        },
      };
    }),

  markFileSaved: (path) =>
    set((state) => {
      const file = state.files[path];
      if (!file) return state;
      return {
        files: {
          ...state.files,
          [path]: { ...file, isModified: false },
        },
      };
    }),

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
        state.activeFile === filePath
          ? state.openFiles.find((file) => file !== filePath) || null
          : state.activeFile,
    })),

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
