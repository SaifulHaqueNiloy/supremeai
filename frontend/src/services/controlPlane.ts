import { fetchWithRetry, getApiBaseUrl } from '../utils/api'

export type ServiceStatus = 'healthy' | 'degraded' | 'unconfigured' | 'timeout' | 'unreachable' | 'unhealthy'

export interface ServiceDefinition {
  id: string
  display_name: string
  role: string
  capabilities: string[]
  critical: boolean
  configured: boolean
  health_path: string
}

export interface CapabilityDefinition {
  id: string
  service_id: string
  available: boolean
}

export interface ControlPlaneRegistry {
  version: string
  timestamp: string
  services: ServiceDefinition[]
  capabilities: CapabilityDefinition[]
}

export interface ServiceHealth extends ServiceDefinition {
  status: ServiceStatus
  status_code?: number
  error?: string
  latency_ms?: number
  checked_at: string
}

export interface ControlPlaneHealth {
  version: string
  timestamp: string
  overall_status: 'healthy' | 'degraded'
  services: ServiceHealth[]
}

export interface McpHealthDashboard {
  snapshots: Record<string, Record<string, unknown>>
  dependencies: Record<string, string[]>
  timestamp: string
}

export interface McpHealthSummary {
  status: 'healthy' | 'degraded' | 'unknown'
  serviceCount: number
  unhealthyCount: number
  services: Array<{ provider: string; status: string; checkedAt: string; latencyMs?: number }>
  timestamp: string
}

import { getAuthHeaders } from './apiClient'

async function getJson<T>(path: string): Promise<T> {
  const correlationId = globalThis.crypto?.randomUUID?.() ?? `cp-${Date.now()}`
  const authHeaders = await getAuthHeaders().catch(() => ({}))
  const response = await fetchWithRetry(path.startsWith('http') ? path : `${getApiBaseUrl(path)}${path}`, {
    headers: { Accept: 'application/json', 'X-Correlation-ID': correlationId, ...authHeaders },
    signal: AbortSignal.timeout(10000),
  })
  if (!response.ok) throw new Error(`Control plane request failed: ${response.status}`)
  return response.json() as Promise<T>
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const correlationId = globalThis.crypto?.randomUUID?.() ?? `cp-${Date.now()}`
  const authHeaders = await getAuthHeaders().catch(() => ({}))
  const response = await fetchWithRetry(path.startsWith('http') ? path : `${getApiBaseUrl(path)}${path}`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'X-Correlation-ID': correlationId, ...authHeaders },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(10000),
  })
  if (!response.ok) throw new Error(`Control plane request failed: ${response.status}`)
  return response.json() as Promise<T>
}

  export interface TaskSubmission {
  goal: string
  metadata?: Record<string, unknown>
  }

  export interface TaskHandle {
  task_id: string
  status: string
  }

  const workerUrl = (path: string) => `${import.meta.env.VITE_WORKER_URL ?? getApiBaseUrl(path)}${path}`

  export const controlPlane = {
  registry: () => getJson<ControlPlaneRegistry>('/api/v1/control-plane/registry'),
  health: () => getJson<ControlPlaneHealth>('/api/v1/control-plane/health'),
  mcpSummary: () => getJson<McpHealthSummary>(`${import.meta.env.VITE_MCP_CONTROL_PLANE_URL ?? ''}/health/summary`),
  mcpDashboard: () => getJson<McpHealthDashboard>(`${import.meta.env.VITE_MCP_CONTROL_PLANE_URL ?? ''}/health/dashboard`),
  mcpSweep: () => postJson<Record<string, unknown>>(`${import.meta.env.VITE_MCP_CONTROL_PLANE_URL ?? ''}/health/sweep`, {}),
  submitTask: (payload: TaskSubmission) => postJson<TaskHandle>(workerUrl('/tasks'), payload),
  taskStatus: (taskId: string) => getJson<TaskHandle>(workerUrl(`/tasks/${encodeURIComponent(taskId)}`)),
  cancelTask: (taskId: string) => postJson<TaskHandle>(workerUrl(`/tasks/${encodeURIComponent(taskId)}/cancel`), {}),
  }

export function capabilityAvailable(registry: ControlPlaneRegistry | undefined, capability: string): boolean {
  return registry?.capabilities.some((item) => item.id === capability && item.available) ?? false
}
