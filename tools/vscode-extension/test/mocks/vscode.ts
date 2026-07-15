import { vi } from 'vitest';

export const window = {
  showInformationMessage: vi.fn().mockResolvedValue(undefined),
  showErrorMessage: vi.fn().mockResolvedValue(undefined),
  showWarningMessage: vi.fn().mockResolvedValue(undefined),
  createOutputChannel: vi.fn().mockReturnValue({ appendLine: vi.fn(), show: vi.fn() }),
};

export const commands = {
  executeCommand: vi.fn().mockResolvedValue(undefined),
  registerCommand: vi.fn().mockReturnValue({ dispose: vi.fn() }),
};

export const workspace = {
  isTrusted: true,
  getConfiguration: vi.fn().mockReturnValue({ 
    get: vi.fn(),
    update: vi.fn().mockResolvedValue(undefined) 
  }),
  workspaceFolders: [],
  onDidSaveTextDocument: vi.fn().mockReturnValue({ dispose: vi.fn() }),
};

export const authentication = {
  getSession: vi.fn().mockResolvedValue(undefined),
};

export const Uri = {
  parse: vi.fn(),
  file: vi.fn(),
};

export const EventEmitter = vi.fn().mockImplementation(() => ({
  event: vi.fn(),
  fire: vi.fn(),
  dispose: vi.fn(),
}));
