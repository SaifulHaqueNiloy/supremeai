import { fetchWithRetry, getApiBaseUrl } from '@/utils/api'

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

async function getJson<T>(path: string): Promise<T> {
  const correlationId = globalThis.crypto?.randomUUID?.() ?? `cp-${Date.now()}`
  const response = await fetchWithRetry(`${getApiBaseUrl(path)}${path}`, {
    headers: { Accept: 'application/json', 'X-Correlation-ID': correlationId },
    signal: AbortSignal.timeout(10000),
  })
  if (!response.ok) throw new Error(`Control plane request failed: ${response.status}`)
  return response.json() as Promise<T>
}

export const controlPlane = {
  registry: () => getJson<ControlPlaneRegistry>('/api/v1/control-plane/registry'),
  health: () => getJson<ControlPlaneHealth>('/api/v1/control-plane/health'),
}

export function capabilityAvailable(registry: ControlPlaneRegistry | undefined, capability: string): boolean {
  return registry?.capabilities.some((item) => item.id === capability && item.available) ?? false
}
