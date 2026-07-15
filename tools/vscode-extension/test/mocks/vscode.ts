import { vi } from 'vitest';

export const window = {
  showInformationMessage: vi.fn(),
  showErrorMessage: vi.fn(),
  showWarningMessage: vi.fn(),
  createOutputChannel: vi.fn().mockReturnValue({ appendLine: vi.fn(), show: vi.fn() }),
};

export const commands = {
  executeCommand: vi.fn().mockResolvedValue(undefined),
  registerCommand: vi.fn().mockReturnValue({ dispose: vi.fn() }),
};

// এখানে workspace মকটি প্রপারলি চেইন করুন
export const workspace = {
  isTrusted: true,
  getConfiguration: vi.fn().mockReturnValue({
    get: vi.fn(),
    update: vi.fn().mockResolvedValue(undefined), // এই লাইনটি Missing ছিল
  }),
  workspaceFolders: [],
  onDidSaveTextDocument: vi.fn().mockReturnValue({ dispose: vi.fn() }),
};

export const authentication = {
  getSession: vi.fn().mockResolvedValue(undefined),
};

export const EventEmitter = vi.fn().mockImplementation(() => ({
  event: vi.fn(),
  fire: vi.fn(),
  dispose: vi.fn(),
}));
