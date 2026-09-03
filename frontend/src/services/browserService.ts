import { apiClient } from './apiClient';

export interface BrowserSession {
  session_id: string;
  status: string;
  url: string;
}

export interface BrowserActionResult {
  success: boolean;
  action: string;
  url: string;
  content?: string;
  screenshot?: string;
}

export type BrowserAction =
  | { action: 'navigate'; url: string }
  | { action: 'click'; selector: string }
  | { action: 'fill' | 'type'; selector: string; value: string }
  | { action: 'screenshot'; full_page?: boolean }
  | { action: 'content' | 'extract' };

export const browserService = {
  createSession: () => apiClient.post<BrowserSession>('/api/browser/automation/sessions', {}),
  listSessions: () => apiClient.get<{ sessions: BrowserSession[] }>('/api/browser/automation/sessions'),
  closeSession: (sessionId: string) =>
    apiClient.delete<{ success: boolean }>(`/api/browser/automation/sessions/${encodeURIComponent(sessionId)}`),
  execute: (sessionId: string, action: BrowserAction) =>
    apiClient.post<BrowserActionResult>('/api/browser/automation/actions', {
      session_id: sessionId,
      ...action,
    }),
};

export default browserService;
