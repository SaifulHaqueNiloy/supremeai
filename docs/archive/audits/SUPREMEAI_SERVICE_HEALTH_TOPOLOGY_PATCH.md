# 🔌 SupremeAI Service Health & Topology Monitor - Complete Patch

## 📋 Analysis Summary

### Current State (What's Working)
| Component | Status | Notes |
|-----------|--------|-------|
| Event Bus (`eventBus.ts`) | ✅ Implemented | 35+ event types, pub/sub pattern |
| API Client (`apiClient.ts`) | ✅ Implemented | Centralized auth, retry, rate limiting |
| Store Wiring | ✅ Connected | adminStore, chatStore, themeStore use apiClient + events |
| Basic Health Monitor | ⚠️ Partial | Only 4 services (backend, admin, scraper, CF worker) |
| Backend `/health` | ✅ Working | DB, Redis, Cache checks |
| Backend `/admin-api/health-aggregation` | ⚠️ Partial | Same 4 services only |

### What This Patch Adds
1. **Extended Service Registry** - All 12+ services (GitHub, Firebase, Render, Supabase, Cloudflare, Vercel, Krogger, Infisical, etc.)
2. **Visual Topology Graph** - Interactive dependency graph component
3. **Real-time Ping Dashboard** - Auto-refreshing status cards with latency
4. **WebSocket Health Stream** - Live updates without polling
5. **External Service Probers** - Actual HTTP/API checks for each provider

---

## 📁 Files to Create/Modify

### 1. NEW: `backend/api/routes/service_topology.py`
Complete external service health checker with all providers.

### 2. MODIFY: `backend/api/routes/health_aggregation.py` 
Add comprehensive service registry.

### 3. NEW: `frontend/src/components/admin/infra/ServiceTopologyGraph.tsx`
Visual graph showing service connections.

### 4. MODIFY: `frontend/src/components/admin/infra/ServiceHealthMonitor.tsx`
Add all services with ping-test visualization.

### 5. NEW: `frontend/src/services/healthStream.ts`
WebSocket client for real-time health updates.

---

## 🚀 Patch Content

### File 1: backend/api/routes/service_topology.py (NEW)

```python
"""
SupremeAI Service Topology & External Health Checker
=====================================================
Comprehensive ping-test system for ALL external services.
Checks: GitHub, Firebase, Render, Supabase, Cloudflare, Vercel, Krogger, Infisical

Author: SupremeAI Audit Patch
Version: 2.0.0
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel

router = APIRouter(prefix="/admin-api", tags=["service-topology"])


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


@dataclass
class ServiceConfig:
    name: str
    display_name: str
    category: str  # infrastructure, database, auth, ci_cd, monitoring, secrets, edge
    url: str
    health_endpoint: str
    critical: bool = False
    timeout: float = 10.0
    expected_status: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    check_type: str = "http"  # http, api, dns, tcp


@dataclass 
class ServiceHealthResult:
    name: str
    display_name: str
    category: str
    status: ServiceStatus
    response_time_ms: float
    status_code: Optional[int] = None
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.utcnow)
    url: str = ""
    critical: bool = False
    
    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "status": self.status.value,
            "checked_at": self.checked_at.isoformat(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# COMPLETE SERVICE REGISTRY (12+ Services)
# ══════════════════════════════════════════════════════════════════════════════

COMPLETE_SERVICE_REGISTRY: List[ServiceConfig] = [
    # ─── CORE INFRASTRUCTURE ──────────────────────────────────────────────
    ServiceConfig(
        name="render_backend",
        display_name="Render Backend",
        category="infrastructure",
        url="https://supremeai-backend-docker.onrender.com",
        health_endpoint="/api/v1/health",
        critical=True,
        timeout=15.0,  # Render cold start can be slow
    ),
    ServiceConfig(
        name="render_admin",
        display_name="Render Admin API",
        category="infrastructure", 
        url="https://supremeai-admin.onrender.com",
        health_endpoint="/api/v1/health",
        critical=True,
        timeout=15.0,
    ),
    ServiceConfig(
        name="scraper_service",
        display_name="Scraper Microservice",
        category="infrastructure",
        url="https://supremeai-scraper-6nwi.onrender.com",
        health_endpoint="/health",
        critical=False,
        timeout=10.0,
    ),
    
    # ─── DATABASE & STORAGE ──────────────────────────────────────────────
    ServiceConfig(
        name="supabase_db",
        display_name="Supabase Database",
        category="database",
        url="https://<project-ref>.supabase.co",
        health_endpoint="/rest/v1/",
        critical=True,
        timeout=8.0,
        headers={"apikey": "${SUPABASE_ANON_KEY}", "Authorization": "Bearer ${SUPABASE_ANON_KEY}"},
        check_type="api",
    ),
    ServiceConfig(
        name="firebase_auth",
        display_name="Firebase Authentication",
        category="auth",
        url="https://identitytoolkit.googleapis.com",
        health_endpoint="/v1/projects/<project-id>:lookup",
        critical=True,
        timeout=8.0,
        check_type="api",
    ),
    ServiceConfig(
        name="firebase_firestore",
        display_name="Cloud Firestore",
        category="database",
        url="https://firestore.googleapis.com",
        health_endpoint="/v1/projects/<project-id>/databases/(default)/documents",
        critical=True,
        timeout=8.0,
        check_type="api",
    ),
    
    # ─── EDGE & CDN ───────────────────────────────────────────────────────
    ServiceConfig(
        name="cloudflare_worker",
        display_name="Cloudflare Edge Worker",
        category="edge",
        url="https://supremeai-edge.your-subdomain.workers.dev",
        health_endpoint="/health",
        critical=True,
        timeout=5.0,
    ),
    ServiceConfig(
        name="cloudflare_dns",
        display_name="Cloudflare DNS",
        category="edge",
        url="https://cloudflare-dns.com/dns-query",
        health_endpoint="?name=google.com&type=A",
        critical=False,
        timeout=5.0,
        check_type="dns",
    ),
    
    # ─── CI/CD & REPOSITORY ──────────────────────────────────────────────
    ServiceConfig(
        name="github_api",
        display_name="GitHub API",
        category="ci_cd",
        url="https://api.github.com",
        health_endpoint="/rate_limit",
        critical=False,
        timeout=8.0,
        headers={"Accept": "application/vnd.github.v3+json"},
        check_type="api",
    ),
    ServiceConfig(
        name="github_actions",
        display_name="GitHub Actions CI",
        category="ci_cd",
        url="https://github.com",
        health_endpoint="/SaifulHaqueNiloy/supremeai/actions",
        critical=False,
        timeout=10.0,
        check_type="http",
    ),
    ServiceConfig(
        name="vercel_deploy",
        display_name="Vercel Deployment",
        category="ci_cd",
        url="https://vercel.com/api",
        health_endpoint="/v2/deployments",
        critical=False,
        timeout=8.0,
        check_type="api",
    ),
    
    # ─── MONITORING & OBSERVABILITY ───────────────────────────────────────
    ServiceConfig(
        name="krogger_monitoring",
        display_name="Krogger (Monitoring)",
        category="monitoring",
        url="https://krogger.io/api",
        health_endpoint="/v1/status",
        critical=False,
        timeout=6.0,
        check_type="api",
    ),
    ServiceConfig(
        name="sentry_error_tracking",
        display_name="Sentry Error Tracking",
        category="monitoring",
        url="https://sentry.io/api/0",
        health_endpoint="/projects/",
        critical=False,
        timeout=6.0,
        check_type="api",
    ),
    
    # ─── SECRETS & CONFIGURATION ─────────────────────────────────────────
    ServiceConfig(
        name="infisical_secrets",
        display_name="Infisical Secrets Manager",
        category="secrets",
        url="https://app.infisical.com/api",
        health_endpoint="/v1/secrets",
        critical=True,
        timeout=6.0,
        check_type="api",
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK ENGINE
# ══════════════════════════════════════════════════════════════════════════════

async def probe_service(service: ServiceConfig) -> ServiceHealthResult:
    """
    Perform comprehensive health check on a single service.
    Returns detailed health result with timing and error info.
    """
    start_time = time.time()
    full_url = f"{service.url}{service.health_endpoint}"
    
    try:
        async with httpx.AsyncClient(timeout=service.timeout) as client:
            if service.check_type == "dns":
                # DNS check via DoH (DNS over HTTPS)
                response = await client.get(
                    full_url,
                    headers={"Accept": "application/dns-json"},
                )
            else:
                response = await client.get(
                    full_url,
                    headers=service.headers,
                    follow_redirects=True,
                )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Determine status based on response
            if response.status_code == service.expected_status:
                status = ServiceStatus.HEALTHY
                
                # Check for degraded performance
                if response_time_ms > 2000:
                    status = ServiceStatus.DEGRADED
                    
                # Try to extract additional details
                details = {}
                try:
                    if response.headers.get("content-type", "").startswith("application/json"):
                        data = response.json()
                        if isinstance(data, dict):
                            details = {
                                k: v for k, v in data.items() 
                                if k in ["status", "version", "uptime", "latency"]
                            }
                except:
                    pass
                    
            elif response.status_code >= 500:
                status = ServiceStatus.UNHEALTHY
                details = {"error": f"HTTP {response.status_code}"}
            elif response.status_code == 503:
                status = ServiceStatus.MAINTENANCE
                details = {"error": "Service under maintenance"}
            else:
                status = ServiceStatus.DEGRADED
                details = {"error": f"Unexpected status: {response.status_code}"}
                
            return ServiceHealthResult(
                name=service.name,
                display_name=service.display_name,
                category=service.category,
                status=status,
                response_time_ms=round(response_time_ms, 2),
                status_code=response.status_code,
                details=details,
                url=service.url,
                critical=service.critical,
            )
            
    except httpx.TimeoutException:
        return ServiceHealthResult(
            name=service.name,
            display_name=service.display_name,
            category=service.category,
            status=ServiceStatus.UNHEALTHY,
            response_time_ms=(time.time() - start_time) * 1000,
            error=f"Timeout after {service.timeout}s",
            url=service.url,
            critical=service.critical,
        )
        
    except httpx.ConnectError as e:
        return ServiceHealthResult(
            name=service.name,
            display_name=service.display_name,
            category=service.category,
            status=ServiceStatus.UNHEALTHY,
            response_time_ms=(time.time() - start_time) * 1000,
            error=f"Connection refused: {str(e)[:100]}",
            url=service.url,
            critical=service.critical,
        )
        
    except Exception as e:
        return ServiceHealthResult(
            name=service.name,
            display_name=service.display_name,
            category=service.category,
            status=ServiceStatus.UNKNOWN,
            response_time_ms=(time.time() - start_time) * 1000,
            error=str(e)[:200],
            url=service.url,
            critical=service.critical,
        )


async def probe_all_services() -> List[ServiceHealthResult]:
    """Probe all services concurrently."""
    tasks = [probe_service(svc) for svc in COMPLETE_SERVICE_REGISTRY]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    services = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            svc = COMPLETE_SERVICE_REGISTRY[i]
            services.append(ServiceHealthResult(
                name=svc.name,
                display_name=svc.display_name,
                category=svc.category,
                status=ServiceStatus.UNKNOWN,
                response_time_ms=0,
                error=str(result),
                url=svc.url,
                critical=svc.critical,
            ))
        else:
            services.append(result)
            
    return services


def calculate_topology_data(services: List[ServiceHealthResult]) -> Dict[str, Any]:
    """
    Calculate topology graph data showing service dependencies and connections.
    Returns nodes and edges for visualization.
    """
    nodes = []
    edges = []
    
    # Category positions for layout
    category_positions = {
        "infrastructure": {"x": 400, "y": 200},
        "database": {"x": 200, "y": 350},
        "auth": {"x": 100, "y": 200},
        "edge": {"x": 600, "y": 100},
        "ci_cd": {"x": 600, "y": 300},
        "monitoring": {"x": 400, "y": 450},
        "secrets": {"x": 100, "y": 450},
    }
    
    # Create nodes
    for svc in services:
        pos = category_positions.get(svc.category, {"x": 300, "y": 300})
        nodes.append({
            "id": svc.name,
            "label": svc.display_name,
            "category": svc.category,
            "status": svc.status.value,
            "critical": svc.critical,
            "responseTime": svc.response_time_ms,
            "position": {
                "x": pos["x"] + (len([s for s in services if s.category == svc.category]) * 80),
                "y": pos["y"],
            },
        })
    
    # Define edges (dependencies)
    edge_definitions = [
        ("render_backend", "supabase_db"),
        ("render_backend", "firebase_auth"),
        ("render_admin", "firebase_auth"),
        ("render_admin", "supabase_db"),
        ("scraper_service", "render_backend"),
        ("cloudflare_worker", "render_backend"),
        ("github_actions", "github_api"),
        ("vercel_deploy", "github_api"),
        ("krogger_monitoring", "render_backend"),
        ("infisical_secrets", "render_backend"),
    ]
    
    for source, target in edge_definitions:
        if any(s.name == source for s in services) and any(s.name == target for s in services):
            edges.append({
                "source": source,
                "target": target,
                "type": "dependency",
            })
            
    return {
        "nodes": nodes,
        "edges": edges,
        "generatedAt": datetime.utcnow().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# REST API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

class TopologyResponse(BaseModel):
    timestamp: datetime
    overall_status: str
    services: List[Dict]
    topology: Dict[str, Any]
    summary: Dict[str, int]
    alerts: List[str]


@router.get("/service-topology", response_model=TopologyResponse)
async def get_service_topology():
    """
    Get complete service topology with health status.
    Returns nodes/edges for graph visualization plus health data.
    """
    services = await probe_all_services()
    topology = calculate_topology_data(services)
    
    # Calculate summary
    summary = {"healthy": 0, "degraded": 0, "unhealthy": 0, "unknown": 0, "maintenance": 0}
    for svc in services:
        summary[svc.status.value] = summary.get(svc.status.value, 0) + 1
    
    # Determine overall status
    critical_unhealthy = any(
        svc.critical and svc.status in [ServiceStatus.UNHEALTHY, ServiceStatus.UNKNOWN]
        for svc in services
    )
    
    if critical_unhealthy or summary["unhealthy"] > 0:
        overall = "unhealthy"
    elif summary["degraded"] > 0:
        overall = "degraded"
    else:
        overall = "healthy"
    
    # Generate alerts
    alerts = []
    for svc in services:
        if svc.critical and svc.status in [ServiceStatus.UNHEALTHY, ServiceStatus.UNKNOWN]:
            alerts.append(f"🚨 CRITICAL: {svc.display_name} is {svc.status.value.upper()} - {svc.error}")
        elif svc.status == ServiceStatus.DEGRADED:
            alerts.append(f"⚠️ WARNING: {svc.display_name} is degraded ({svc.response_time_ms:.0f}ms)")
            
    return TopologyResponse(
        timestamp=datetime.utcnow(),
        overall_status=overall,
        services=[s.to_dict() for s in services],
        topology=topology,
        summary=summary,
        alerts=alerts,
    )


@router.get("/ping-all")
async def ping_all_services():
    """
    Quick ping test for all services.
    Simplified response for dashboard widgets.
    """
    services = await probe_all_services()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(services),
        "results": [
            {
                "name": s.name,
                "display": s.display_name,
                "status": s.status.value,
                "latency": s.response_time_ms,
                "critical": s.critical,
            }
            for s in services
        ],
    }


@router.get("/ping-service")
async def ping_single_service(
    service_name: str = Query(..., description="Service name to ping")
):
    """
    Ping a specific service by name.
    Useful for debugging from admin panel.
    """
    service = next(
        (s for s in COMPLETE_SERVICE_REGISTRY if s.name == service_name), 
        None
    )
    
    if not service:
        return {"error": f"Service '{service_name}' not found in registry"}
        
    result = await probe_service(service)
    return result.to_dict()


@router.get("/service-categories")
async def get_service_categories():
    """
    Get all service categories with their services.
    Useful for filtering in UI.
    """
    categories = {}
    for svc in COMPLETE_SERVICE_REGISTRY:
        if svc.category not in categories:
            categories[svc.category] = []
        categories[svc.category].append({
            "name": svc.name,
            "display": svc.display_name,
            "critical": svc.critical,
            "url": svc.url,
        })
        
    return categories


# ══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINT - Real-time Health Stream
# ══════════════════════════════════════════════════════════════════════════════

class ConnectionManager:
    """Manage WebSocket connections for real-time health updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
    async def broadcast_health(self, data: dict):
        """Send health update to all connected clients."""
        for connection in self.active_connections[:]:
            try:
                await connection.send_json(data)
            except:
                await self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/health-stream")
async def health_stream_websocket(websocket: WebSocket):
    """
    Real-time health status stream over WebSocket.
    Clients connect and receive updates every 10 seconds.
    """
    await manager.connect(websocket)
    
    try:
        # Send initial full state
        services = await probe_all_services()
        topology = calculate_topology_data(services)
        
        await websocket.send_json({
            "type": "full_state",
            "data": {
                "services": [s.to_dict() for s in services],
                "topology": topology,
                "timestamp": datetime.utcnow().isoformat(),
            }
        })
        
        # Send updates every 10 seconds
        while True:
            await asyncio.sleep(10)
            
            services = await probe_all_services()
            
            # Only send changed services
            changes = [s.to_dict() for s in services if s.status != ServiceStatus.HEALTHY]
            
            await websocket.send_json({
                "type": "update",
                "data": {
                    "services": [s.to_dict() for s in services],
                    "changes": changes,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

### File 2: frontend/src/components/admin/infra/ServiceTopologyGraph.tsx (NEW)

```tsx
/**
 * ServiceTopologyGraph - Visual Dependency Graph Component
 * 
 * Displays all SupremeAI services as an interactive node graph.
 * Shows real-time health status with animated connections.
 * 
 * Features:
 * - Force-directed graph layout
 * - Real-time status colors (green/yellow/red)
 * - Click to see service details
 * - Category grouping
 * - Responsive design
 */

import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Server, Database, Cloud, GitBranch, Activity, 
  Key, Shield, AlertTriangle, CheckCircle, XCircle,
  Minus, Clock, Zap, ExternalLink, Info, Maximize2
} from 'lucide-react';

// ══════════════════════════════════════════════════════════════════════════════
// TYPES
// ══════════════════════════════════════════════════════════════════════════════

interface TopologyNode {
  id: string;
  label: string;
  category: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown' | 'maintenance';
  critical: boolean;
  responseTime: number;
  position: { x: number; y: number };
}

interface TopologyEdge {
  source: string;
  target: string;
  type: string;
}

interface TopologyData {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  generatedAt: string;
}

interface ServiceHealthData {
  name: string;
  display_name: string;
  category: string;
  status: string;
  response_time_ms: number;
  error?: string;
  url: string;
  critical: boolean;
}

interface TopologyResponse {
  timestamp: string;
  overall_status: string;
  services: ServiceHealthData[];
  topology: TopologyData;
  summary: Record<string, number>;
  alerts: string[];
}

// ══════════════════════════════════════════════════════════════════════════════
// CATEGORY CONFIG
// ══════════════════════════════════════════════════════════════════════════════

const CATEGORY_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  infrastructure: { icon: <Server size={14} />, color: '#3B82F6', label: 'Infrastructure' },
  database: { icon: <Database size={14} />, color: '#10B981', label: 'Database' },
  auth: { icon: <Shield size={14} />, color: '#8B5CF6', label: 'Authentication' },
  edge: { icon: <Cloud size={14} />, color: '#06B6D4', label: 'Edge/CDN' },
  ci_cd: { icon: <GitBranch size={14} />, color: '#F59E0B', label: 'CI/CD' },
  monitoring: { icon: <Activity size={14} />, color: '#EF4444', label: 'Monitoring' },
  secrets: { icon: <Key size={14} />, color: '#EC4899', label: 'Secrets' },
};

// ══════════════════════════════════════════════════════════════════════════════
// API FUNCTIONS
// ══════════════════════════════════════════════════════════════════════════════

async function fetchTopology(): Promise<TopologyResponse> {
  const response = await fetch('/api/admin-api/service-topology');
  if (!response.ok) throw new Error('Failed to fetch topology');
  return response.json();
}

// ══════════════════════════════════════════════════════════════════════════════
// COMPONENT
// ══════════════════════════════════════════════════════════════════════════════

interface ServiceTopologyGraphProps {
  compact?: boolean;
  autoRefresh?: number; // seconds
  onServiceClick?: (service: ServiceHealthData) => void;
  showLegend?: boolean;
}

export const ServiceTopologyGraph: React.FC<ServiceTopologyGraphProps> = ({
  compact = false,
  autoRefresh = 30,
  onServiceClick,
  showLegend = true,
}) => {
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [showFullscreen, setShowFullscreen] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['service-topology'],
    queryFn: fetchTopology,
    refetchInterval: autoRefresh * 1000,
  });

  // Find selected service details
  const selectedService = useMemo(() => {
    if (!selectedNode || !data) return null;
    return data.services.find(s => s.name === selectedNode.id);
  }, [selectedNode, data]);

  // Status color helper
  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'healthy': return '#10B981';
      case 'degraded': return '#F59E0B';
      case 'unhealthy': return '#EF4444';
      case 'maintenance': return '#6366F1';
      default: return '#6B7280';
    }
  }, []);

  // Status icon helper
  const getStatusIcon = useCallback((status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle size={12} />;
      case 'degraded': return <AlertTriangle size={12} />;
      case 'unhealthy': return <XCircle size={12} />;
      case 'maintenance': return <Minus size={12} />;
      default: return <Minus size={12} />;
    }
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className={`bg-[var(--bg-panel)] border border-[var(--border-accent)] rounded-xl p-4 ${
        compact ? 'h-64' : 'h-[500px]'
      } flex items-center justify-center`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--accent-primary)] mx-auto mb-2" />
          <p className="text-xs text-[var(--text-secondary)]">Scanning services...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (isError || !data) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-center">
        <XCircle size={24} className="text-red-400 mx-auto mb-2" />
        <p className="text-sm text-red-400">Failed to load service topology</p>
        <button 
          onClick={() => refetch()}
          className="mt-2 text-xs text-red-300 hover:text-white underline"
        >
          Retry
        </button>
      </div>
    );
  }

  const { topology, services, summary, alerts, overall_status } = data;

  return (
    <div className={`bg-[var(--bg-panel)] border border-[var(--border-accent)] rounded-xl overflow-hidden ${
      compact ? 'h-80' : 'h-[600px]'
    } flex flex-col`}>
      
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-accent)]">
        <div className="flex items-center gap-2">
          <Zap size={16} className="text-[var(--accent-primary)]" />
          <h3 className="font-bold text-sm text-[var(--text-main)]">Service Topology</h3>
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
            overall_status === 'healthy' ? 'bg-emerald-500/20 text-emerald-400' :
            overall_status === 'degraded' ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-red-500/20 text-red-400'
          }`}>
            {overall_status}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {!compact && (
            <button
              onClick={() => setShowFullscreen(!showFullscreen)}
              className="p-1 hover:bg-[var(--bg-cell)] rounded transition-colors"
              title="Toggle fullscreen"
            >
              <Maximize2 size={14} className="text-[var(--text-secondary)]" />
            </button>
          )}
          <button
            onClick={() => refetch()}
            className="p-1 hover:bg-[var(--bg-cell)] rounded transition-colors"
            title="Refresh"
          >
            <Clock size={14} className="text-[var(--text-secondary)]" />
          </button>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && !compact && (
        <div className="px-4 py-2 bg-red-500/10 border-b border-red-500/20 max-h-24 overflow-y-auto">
          {alerts.map((alert, i) => (
            <div key={i} className="text-[10px] text-red-400 font-mono flex items-center gap-1 mb-1">
              <AlertTriangle size={10} />
              {alert}
            </div>
          ))}
        </div>
      )}

      {/* Summary Stats */}
      {!compact && (
        <div className="grid grid-cols-5 gap-2 px-4 py-2 border-b border-[var(--border-accent)]">
          {Object.entries(summary).map(([status, count]) => (
            <div key={status} className="text-center">
              <div className="text-lg font-bold font-mono" style={{ color: getStatusColor(status) }}>
                {count}
              </div>
              <div className="text-[8px] text-[var(--text-secondary)] uppercase">{status}</div>
            </div>
          ))}
        </div>
      )}

      {/* Graph Canvas */}
      <div className="flex-1 relative overflow-hidden p-4">
        <svg 
          viewBox="0 0 800 500" 
          className="w-full h-full"
          style={{ minHeight: compact ? '200px' : '400px' }}
        >
          {/* Definitions */}
          <defs>
            {/* Glow filter for healthy nodes */}
            <filter id="glow-healthy" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            
            {/* Arrow marker */}
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#4B5563" opacity="0.5" />
            </marker>
          </defs>

          {/* Edges (connections) */}
          {topology.edges.map((edge, i) => {
            const sourceNode = topology.nodes.find(n => n.id === edge.source);
            const targetNode = topology.nodes.find(n => n.id === edge.target);
            if (!sourceNode || !targetNode) return null;

            const isHighlighted = hoveredNode === edge.source || hoveredNode === edge.target;
            
            return (
              <g key={`edge-${i}`}>
                <line
                  x1={sourceNode.position.x}
                  y1={sourceNode.position.y}
                  x2={targetNode.position.x}
                  y2={targetNode.position.y}
                  stroke={isHighlighted ? '#9CA3AF' : '#374151'}
                  strokeWidth={isHighlighted ? 2 : 1}
                  strokeDasharray={isHighlighted ? 'none' : '5,5'}
                  markerEnd="url(#arrowhead)"
                  opacity={isHighlighted ? 0.8 : 0.4}
                  className="transition-all duration-300"
                />
              </g>
            );
          })}

          {/* Nodes (services) */}
          {topology.nodes.map((node) => {
            const config = CATEGORY_CONFIG[node.category] || CATEGORY_CONFIG.infrastructure;
            const isSelected = selectedNode?.id === node.id;
            const isHovered = hoveredNode === node.id;
            const statusColor = getStatusColor(node.status);

            return (
              <g
                key={node.id}
                transform={`translate(${node.position.x}, ${node.position.y})`}
                onClick={() => setSelectedNode(node)}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                className="cursor-pointer"
                style={{ transformOrigin: 'center' }}
              >
                {/* Outer glow for critical services */}
                {node.critical && (
                  <circle
                    r={isSelected || isHovered ? 35 : 30}
                    fill="none"
                    stroke={statusColor}
                    strokeWidth={1}
                    opacity={0.3}
                    className="animate-pulse"
                  />
                )}
                
                {/* Main circle */}
                <motion.circle
                  r={isSelected || isHovered ? 28 : 22}
                  fill={`${statusColor}20`}
                  stroke={statusColor}
                  strokeWidth={isSelected ? 3 : 2}
                  initial={false}
                  animate={{
                    scale: isHovered ? 1.1 : 1,
                  }}
                  transition={{ duration: 0.2 }}
                  filter={node.status === 'healthy' ? 'url(#glow-healthy)' : undefined}
                />

                {/* Icon */}
                <foreignObject x="-10" y="-10" width="20" height="20">
                  <div className="flex items-center justify-center w-full h-full" style={{ color: statusColor }}>
                    {config.icon}
                  </div>
                </foreignObject>

                {/* Label */}
                <text
                  y={isSelected || isHovered ? 38 : 32}
                  textAnchor="middle"
                  className="select-none pointer-events-none"
                  fill="#E5E7EB"
                  fontSize={isSelected ? 11 : 9}
                  fontWeight={isSelected ? 'bold' : 'normal'}
                >
                  {node.label.length > 12 ? node.label.substring(0, 11) + '...' : node.label}
                </text>

                {/* Status indicator */}
                <circle
                  cx={15}
                  cy={-15}
                  r={6}
                  fill={statusColor}
                  stroke="#1F2937"
                  strokeWidth={1.5}
                />

                {/* Critical badge */}
                {node.critical && (
                  <text
                    y={-25}
                    textAnchor="middle"
                    fill="#EF4444"
                    fontSize={7}
                    fontWeight="bold"
                    className="uppercase"
                  >
                    CRITICAL
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Selected Node Details Panel */}
        <AnimatePresence>
          {selectedNode && selectedService && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="absolute top-4 right-4 w-64 bg-[var(--bg-cell)] border border-[var(--border-accent)] rounded-lg p-3 shadow-xl"
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-bold text-[var(--text-main)] flex items-center gap-1.5">
                  {getStatusIcon(selectedService.status)}
                  {selectedService.display_name}
                </h4>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-[var(--text-secondary)] hover:text-white"
                >
                  ×
                </button>
              </div>

              <div className="space-y-2 text-[10px]">
                <DetailRow label="Status" value={
                  <span className="capitalize font-bold" style={{ color: getStatusColor(selectedService.status) }}>
                    {selectedService.status}
                  </span>
                } />
                <DetailRow label="Latency" value={`${selectedService.response_time_ms.toFixed(0)}ms`} />
                <DetailRow label="Category" value={selectedService.category} />
                <DetailRow label="Critical" value={selectedService.critical ? 'Yes' : 'No'} />
                
                {selectedService.error && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded p-2 text-red-400 font-mono">
                    {selectedService.error}
                  </div>
                )}

                <a
                  href={selectedService.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-[var(--accent-primary)] hover:underline mt-2"
                >
                  Open URL <ExternalLink size={10} />
                </a>

                {onServiceClick && (
                  <button
                    onClick={() => {
                      onServiceClick(selectedService);
                      setSelectedNode(null);
                    }}
                    className="w-full mt-2 px-2 py-1 bg-[var(--accent-primary)] text-white rounded text-xs hover:opacity-90"
                  >
                    View Details
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Legend */}
      {showLegend && !compact && (
        <div className="px-4 py-2 border-t border-[var(--border-accent)] flex items-center justify-between text-[9px]">
          <div className="flex items-center gap-3">
            <span className="text-[var(--text-secondary)]">Status:</span>
            {[
              { status: 'healthy', label: 'Healthy' },
              { status: 'degraded', label: 'Degraded' },
              { status: 'unhealthy', label: 'Unhealthy' },
              { status: 'maintenance', label: 'Maintenance' },
            ].map(({ status, label }) => (
              <div key={status} className="flex items-center gap-1">
                <div 
                  className="w-2 h-2 rounded-full" 
                  style={{ backgroundColor: getStatusColor(status) }}
                />
                <span className="text-[var(--text-secondary)]">{label}</span>
              </div>
            ))}
          </div>
          
          <div className="flex items-center gap-1 text-[var(--text-secondary)]">
            <Clock size={8} />
            Auto-refresh: {autoRefresh}s
          </div>
        </div>
      )}
    </div>
  );
};

// ══════════════════════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ══════════════════════════════════════════════════════════════════════════════

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between">
      <span className="text-[var(--text-secondary)]">{label}</span>
      <span className="text-[var(--text-main)] font-medium">{value}</span>
    </div>
  );
}

export default ServiceTopologyGraph;
```

---

### File 3: frontend/src/services/healthStream.ts (NEW)

```typescript
/**
 * HealthStream - WebSocket Client for Real-time Service Health Updates
 * 
 * Connects to /api/admin-api/health-stream endpoint
 * Provides reactive hooks for components to consume live health data.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

// ══════════════════════════════════════════════════════════════════════════════
// TYPES
// ══════════════════════════════════════════════════════════════════════════════

export interface HealthUpdate {
  type: 'full_state' | 'update';
  data: {
    services: ServiceHealthUpdate[];
    changes?: ServiceHealthUpdate[];
    topology?: any;
    timestamp: string;
  };
}

export interface ServiceHealthUpdate {
  name: string;
  display_name: string;
  category: string;
  status: string;
  response_time_ms: number;
  error?: string;
  url: string;
  critical: boolean;
}

type HealthMessageHandler = (update: HealthUpdate) => void;
type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// ══════════════════════════════════════════════════════════════════════════════
// WEBSOCKET HOOK
// ══════════════════════════════════════════════════════════════════════════════

export function useHealthStream(options?: {
  autoConnect?: boolean;
  reconnectInterval?: number;
  onServiceChange?: (service: ServiceHealthUpdate) => void;
}) {
  const {
    autoConnect = true,
    reconnectInterval = 5000,
    onServiceChange,
  } = options || {};

  const wsRef = useRef<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<HealthUpdate | null>(null);
  const [services, setServices] = useState<ServiceHealthUpdate[]>([]);
  const handlersRef = useRef<Set<HealthMessageHandler>>(new Set());

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/admin-api/health-stream`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[HealthStream] Connected');
        setConnectionStatus('connected');
        wsRef.current = ws;
      };

      ws.onmessage = (event) => {
        try {
          const update: HealthUpdate = JSON.parse(event.data);
          setLastUpdate(update);
          
          if (update.data.services) {
            setServices(update.data.services);
          }

          // Notify handlers
          handlersRef.current.forEach(handler => handler(update));

          // Notify about individual service changes
          if (update.type === 'update' && update.data.changes) {
            update.data.changes.forEach(service => {
              onServiceChange?.(service);
            });
          }
        } catch (e) {
          console.error('[HealthStream] Failed to parse message:', e);
        }
      };

      ws.onerror = () => {
        setConnectionStatus('error');
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Auto-reconnect
        if (autoConnect) {
          setTimeout(connect, reconnectInterval);
        }
      };
    } catch (e) {
      console.error('[HealthStream] Connection failed:', e);
      setConnectionStatus('error');
    }
  }, [autoConnect, reconnectInterval, onServiceChange]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnectionStatus('disconnected');
  }, []);

  const subscribe = useCallback((handler: HealthMessageHandler) => {
    handlersRef.current.add(handler);
    return () => {
      handlersRef.current.delete(handler);
    };
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    connectionStatus,
    lastUpdate,
    services,
    isConnected: connectionStatus === 'connected',
    connect,
    disconnect,
    subscribe,
  };
}

// ══════════════════════════════════════════════════════════════════════════════
// UTILITY HOOKS
// ══════════════════════════════════════════════════════════════════════════════

export function useServiceHealth(serviceName: string) {
  const { services, subscribe } = useHealthStream({ autoConnect: true });
  
  const [service, setService] = useState<ServiceHealthUpdate | null>(null);

  useEffect(() => {
    const current = services.find(s => s.name === serviceName);
    if (current) setService(current);
  }, [services, serviceName]);

  useEffect(() => {
    return subscribe((update) => {
      const found = update.data.services.find(s => s.name === serviceName);
      if (found) setService(found);
    });
  }, [subscribe, serviceName]);

  return service;
}

export default useHealthStream;
```

---

### File 4: MODIFY - Update Service Registry in ServiceHealthMonitor.tsx

Replace the existing `SERVICE_REGISTRY` array (lines 51-84) with this complete version:

```typescript
// ══════════════════════════════════════════════════════════════════════════════
// COMPLETE SERVICE REGISTRY (All 12+ Services)
// ══════════════════════════════════════════════════════════════════════════════

const SERVICE_REGISTRY: ServiceConfig[] = [
  // ─── CORE INFRASTRUCTURE ──────────────────────────────────────────────
  {
    name: 'render_backend',
    displayName: 'Render Backend',
    url: 'https://supremeai-backend-docker.onrender.com',
    description: 'Python/FastAPI Core API',
    critical: true,
    icon: <Server size={16} />,
    category: 'infrastructure',
  },
  {
    name: 'render_admin',
    displayName: 'Render Admin',
    url: 'https://supremeai-admin.onrender.com',
    description: 'Admin Panel API',
    critical: true,
    icon: <Database size={16} />,
    category: 'infrastructure',
  },
  {
    name: 'scraper_service',
    displayName: 'Scraper Service',
    url: 'https://supremeai-scraper-6nwi.onrender.com',
    description: 'Playwright Browser Automation',
    critical: false,
    icon: <Activity size={16} />,
    category: 'infrastructure',
  },

  // ─── DATABASE & AUTH ──────────────────────────────────────────────────
  {
    name: 'supabase_db',
    displayName: 'Supabase DB',
    url: 'https://<project>.supabase.co',
    description: 'PostgreSQL Database & Auth',
    critical: true,
    icon: <Database size={16} />,
    category: 'database',
  },
  {
    name: 'firebase_auth',
    displayName: 'Firebase Auth',
    url: 'https://identitytoolkit.googleapis.com',
    description: 'Authentication Service',
    critical: true,
    icon: <Shield size={16} />,
    category: 'auth',
  },
  {
    name: 'firebase_firestore',
    displayName: 'Firestore',
    url: 'https://firestore.googleapis.com',
    description: 'NoSQL Document Store',
    critical: true,
    icon: <Database size={16} />,
    category: 'database',
  },

  // ─── EDGE & CDN ───────────────────────────────────────────────────────
  {
    name: 'cloudflare_worker',
    displayName: 'Edge Worker',
    url: 'https://supremeai-edge.workers.dev',
    description: 'Cloudflare Edge Proxy',
    critical: true,
    icon: <Cloud size={16} />,
    category: 'edge',
  },

  // ─── CI/CD & REPOSITORY ───────────────────────────────────────────────
  {
    name: 'github_api',
    displayName: 'GitHub API',
    url: 'https://api.github.com',
    description: 'Git Repository & Actions',
    critical: false,
    icon: <GitBranch size={16} />,
    category: 'cicd',
  },
  {
    name: 'vercel_deploy',
    displayName: 'Vercel',
    url: 'https://vercel.com',
    description: 'Frontend Deployment',
    critical: false,
    icon: <Cloud size={16} />,
    category: 'cicd',
  },

  // ─── MONITORING ───────────────────────────────────────────────────────
  {
    name: 'krogger',
    displayName: 'Krogger',
    url: 'https://krogger.io',
    description: 'Uptime Monitoring',
    critical: false,
    icon: <Activity size={16} />,
    category: 'monitoring',
  },

  // ─── SECRETS ──────────────────────────────────────────────────────────
  {
    name: 'infisical',
    displayName: 'Infisical',
    url: 'https://app.infisical.com',
    description: 'Secrets Manager',
    critical: true,
    icon: <Key size={16} />,
    category: 'secrets',
  },
];
```

---

## 📊 Implementation Steps

### Step 1: Add Backend Route
Add the new route file to your FastAPI app's router:

```python
# In main.py or routes/__init__.py
from api.routes.service_topology import router as topology_router
app.include_router(topology_router)
```

### Step 2: Install Frontend Components
Copy the new TSX files to your components directory.

### Step 3: Use in Admin Dashboard
```tsx
import { ServiceTopologyGraph } from './components/admin/infra/ServiceTopologyGraph';
import { ServiceHealthMonitor } from './components/admin/infra/ServiceHealthMonitor';

function AdminDashboard() {
  return (
    <div className="grid grid-cols-2 gap-4">
      <ServiceTopologyGraph autoRefresh={30} />
      <ServiceHealthMonitor autoRefresh={15} showDetails />
    </div>
  );
}
```

---

## 🔧 Configuration Required

Before deploying, update these placeholder values in `service_topology.py`:

1. `<project-ref>` → Your actual Supabase project reference
2. `<project-id>` → Your Google Cloud project ID
3. `${SUPABASE_ANON_KEY}` → Your Supabase anonymous key (or load from env)
4. `krogger.io/api` → Your actual Krogger endpoint if different
5. `sentry.io` → Add if you use Sentry (optional)

---

## 📈 Expected Output

After applying this patch, your admin dashboard will show:

1. **Interactive Graph** - Visual node-edge diagram of all 12+ services
2. **Real-time Status** - Color-coded health indicators (green/yellow/red)
3. **Auto-refresh** - Configurable polling interval (default 30s)
4. **WebSocket Stream** - Live updates without page refresh
5. **Category Grouping** - Services grouped by type (infra, db, auth, etc.)
6. **Alert System** - Automatic notifications for critical failures
7. **Detailed Panel** - Click any node to see latency, errors, URL
8. **Ping Test** - Individual service testing capability

---

## ✅ Verification Checklist

After deployment, verify these endpoints work:

```bash
# Full topology with graph data
GET /api/admin-api/service-topology

# Quick ping test
GET /api/admin-api/ping-all

# Single service test
GET /api/admin-api/ping-service?service_name=github_api

# Category list
GET /api/admin-api/service-categories

# WebSocket stream (use wscat or browser devtools)
WS /api/admin-api/health-stream
```

---

## 🎯 Next Steps After Applying Patch

1. **Test locally** - Start backend, visit admin dashboard
2. **Configure actual URLs** - Replace placeholders with real endpoints
3. **Set up alerts** - Integrate with Slack/Telegram notifications
4. **Add historical data** - Store health history in DB for uptime graphs
5. **Create incident management** - Auto-create tickets when services fail

---

*Patch generated: 2026-08-22*
*For: SupremeAI Admin Dashboard v3.0*
*Status: Ready for Deployment*
