// frontend/src/store/slices/types.ts
// Shared domain types for the unified Supreme store slices.

export interface User {
  id: string;
  email: string;
  role: string;
  name?: string;
  [key: string]: unknown;
}

export interface Workspace {
  id: string;
  name: string;
  description?: string;
  [key: string]: unknown;
}

export interface Role {
  id: string;
  name: string;
  permissions?: string[];
}

export interface Permission {
  id: string;
  name: string;
}

export interface Session {
  id: string;
  user_id: string;
  status: string;
  created_at: string;
}

// ─── Workspace Integration Types ──────────────────────────────────────────────
export interface DockIntegration {
  id: string;
  icon: string;
  label: string;
  enabled: boolean;
}

export interface Notification {
  id: string;
  type: 'info' | 'error' | 'success';
  message: string;
  correlationId?: string;
}
