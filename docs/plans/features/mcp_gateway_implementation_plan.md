# Architectural Analysis & Implementation Plan: Personal MCP Gateway & Multi-Tenant MCP Hub

This document provides an in-depth architectural evaluation of the proposed **Personal MCP Gateway** design, reconciles it with SupremeAI's existing codebase and `MASTER_PLAN_BANGLA.md` (Battleground B6 & Phases 2–6), and presents a phased, production-grade implementation roadmap.

---

## 1. Architectural Analysis of the User's Proposal

### 1.1 The Core Proposition & Axiom

> **"Public endpoint, private identity, explicit authorization."**
> 
> *The MCP URL is the discovery and routing layer. It is NOT the authorization layer.*

The user's revised proposal corrects a dangerous misconception common in distributed systems: confusing **routing addressing** with **security credentials**. Making the endpoint public (e.g., `https://niloy.mcp.supremeai.ai`) is structurally sound **provided that** every invocation is intercepted by a strict, authenticated token validation and tenant isolation boundary.

### 1.2 Evaluation Scorecard & Nuance Breakdown

| Architectural Pillar | User Rating | Analysis & Codebase Alignment | Verdict |
| :--- | :---: | :--- | :---: |
| **Vanity / Slug Routing** (`*.mcp.supremeai.ai`) | **9.5/10** | Excellent UX for AI clients (Cursor, Claude Desktop, Claude Web). Translates high-entropy UUIDs into memorable endpoints. | **Approved** |
| **Decoupled Identity** (`slug` $\to$ `tenant_id`) | **10/10** | Essential for security. Prevents enumeration, allows username renames without orphaned clients, shields PII. | **Approved** |
| **Single Shared Gateway Engine** | **10/10** | Running a Node.js process per user is an anti-pattern on constrained cloud resources (Render free tier / Cloud Run). One stateless multi-tenant gateway process dynamically scoped via request context is the only scalable path. | **Approved** |
| **Per-Client Token & Scopes** | **9.5/10** | Already partially modeled in [client-registry.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/policy/client-registry.ts). Gives Cursor, Claude, and Gemini distinct access profiles. | **Approved** |
| **Postgres Persistence** (vs in-memory Map) | **10/10** | Eliminates split-brain across horizontal replicas and survives Render cold restarts. | **Approved** |
| **Principal Hierarchy** (Personal $\to$ Team $\to$ Workspace) | **9.0/10** | Future-proofs B2B and agency accounts without rewriting routing tables later. | **Approved** |

### 1.3 Key Findings in Current Codebase

1. **Foundations Already Present:**
   - [tenant.model.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/tenancy/tenant.model.ts) and [tenant.registry.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/tenancy/tenant.registry.ts) already enforce multi-tenancy limits, customer/admin isolation, and admin token verification.
   - [client-registry.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/policy/client-registry.ts) implements `StoredClient` with SHA-256 hashed bearer tokens, tenant-scoping (`tenantId`), role-based scopes (`viewer`, `agent`, `admin`), and lifecycle states (`pending`, `active`, `revoked`, `expired`).
   - [index.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/index.ts) lines 320–355 and 706–744 already use `RequestContextStore` with async storage to pass `role`, `scopes`, and `tenantId` down to tool execution.
2. **Current Limitations & Gaps to Close:**
   - **Host Subdomain Extraction:** [index.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/index.ts) currently binds all traffic to a flat `/mcp` path on the single host without inspecting the subdomain.
   - **Persistence Layer:** Both `tenant.registry.ts` and `client-registry.ts` rely on atomic local file writes (`registry.json`) or in-memory `Map` instances. In production, Render containers have ephemeral disks unless mounted to persistent disks or migrated to Supabase/Postgres.
   - **Edge Routing:** [cloudflare_worker.js](file:///f:/supremeai/infrastructure/cloudflare_worker.js) balances traffic by weight across services, but lacks wildcard subdomain matching (`*.mcp.supremeai.ai`) to route MCP traffic directly to the MCP Control Tower.
   - **Frontend Disconnect:** [IntegrationsManager.tsx](file:///f:/supremeai/frontend/src/pages/user/IntegrationsManager.tsx) has a read-only [MCPConnector.tsx](file:///f:/supremeai/frontend/src/components/plugins/MCPConnector.tsx) viewer, but no "Personal MCP Gateway Hub" where a user can claim their slug, generate tokens, view connected AIs, or adjust client roles.

---

## 2. Target System Architecture

```text
                           Wildcard DNS (*.mcp.supremeai.ai)
                                          │
                                          ▼
                      Cloudflare Edge Worker (Edge Router)
                      - Matches Host: <slug>.mcp.supremeai.ai
                      - Enforces Edge DDOS & IP Rate Limiting
                      - Injects CF-Tenant-Slug header
                                          │
                                          ▼
               SupremeAI MCP Gateway (infrastructure/mcp-control-plane)
                                          │
    ┌─────────────────────────────────────┴─────────────────────────────────────┐
    ▼                                                                           ▼
1. Slug Resolver Middleware                                         2. Authenticator Middleware
   Extracts `slug` from Host header                                     Extracts `Authorization: Bearer mcp_...`
   Looks up `mcp_slugs` in Postgres / Redis                             Hashes token with SHA-256
   Resolves canonical `tenant_id`                                       Finds client in `mcp_clients`
    └─────────────────────────────────────┬─────────────────────────────────────┘
                                          │
                                          ▼
                           3. Cross-Verification Gate
                 Assert: client.tenant_id === resolved.tenant_id
               (Prevents Client Token Spoofing across Subdomains)
                                          │
                                          ▼
                             4. Policy & Scopes Engine
                   Sets RequestContext: role, scopes, tenant_id
                 Evaluates tool execution rules & HITL permissions
                                          │
                                          ▼
                      Universal MCP Dispatcher & Transports
                         - Streamable HTTP (/mcp)
                         - SSE (/sse + /messages)
                         - Tools & Resources Registry
```

---

## 3. Database Schema Design (Postgres / Supabase)

To enable horizontal scalability across instances and persistent multi-tenancy, three relational tables will be introduced via Alembic migration:

```sql
-- 1. MCP Slugs Registry (Vanity & Alias mapping)
CREATE TABLE mcp_slugs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(63) NOT NULL UNIQUE,
    tenant_id VARCHAR(64) NOT NULL,
    target_type VARCHAR(20) NOT NULL DEFAULT 'user', -- 'user' | 'workspace' | 'organization'
    is_primary BOOLEAN NOT NULL DEFAULT true,
    status VARCHAR(20) NOT NULL DEFAULT 'active',    -- 'active' | 'reserved' | 'deprecated'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_slug_format CHECK (slug ~* '^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$')
);

CREATE INDEX idx_mcp_slugs_lookup ON mcp_slugs(slug) WHERE status = 'active';
CREATE INDEX idx_mcp_slugs_tenant ON mcp_slugs(tenant_id);

-- 2. MCP Tenants (Extended metadata and limits)
CREATE TABLE mcp_tenants (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_email VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'customer',     -- 'admin' | 'customer'
    status VARCHAR(20) NOT NULL DEFAULT 'active',     -- 'active' | 'suspended' | 'deleted'
    plan VARCHAR(20) NOT NULL DEFAULT 'free',         -- 'free' | 'pro' | 'enterprise'
    admin_token_hash VARCHAR(64) NOT NULL,
    max_clients INT NOT NULL DEFAULT 10,
    max_tools_per_min INT NOT NULL DEFAULT 120,
    max_token_days INT NOT NULL DEFAULT 90,
    allowed_categories JSONB NOT NULL DEFAULT '["github", "ai", "docs", "notify", "knowledge"]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. MCP Clients (Per-AI-client credentials)
CREATE TABLE mcp_clients (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES mcp_tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,                       -- e.g. "Claude Desktop", "Cursor Mac"
    provider VARCHAR(50) NOT NULL DEFAULT 'generic',  -- 'claude', 'cursor', 'gemini', 'vscode', 'custom'
    protocol VARCHAR(30) NOT NULL DEFAULT 'streamable-http',
    role VARCHAR(20) NOT NULL DEFAULT 'agent',        -- 'viewer' | 'agent' | 'admin'
    scopes JSONB NOT NULL DEFAULT '["health:read", "system:read", "tools:execute"]'::jsonb,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    token_prefix VARCHAR(12) NOT NULL,                -- e.g. "mcp_a8f9..." for UI identification
    status VARCHAR(20) NOT NULL DEFAULT 'active',     -- 'pending' | 'active' | 'revoked' | 'expired'
    expires_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mcp_clients_token_hash ON mcp_clients(token_hash) WHERE status = 'active';
CREATE INDEX idx_mcp_clients_tenant ON mcp_clients(tenant_id);
```

---

## 4. Phased Implementation Plan

This implementation plan aligns directly with SupremeAI's `MASTER_PLAN_BANGLA.md` (Battleground B6 & Phases 2 through 6).

### Phase A: Core DB Migration & MCP Control Tower Registry Adapters
*Primary Goal: Replace local JSON file persistence with database-backed storage with local caching.*

1. **Alembic Migration:**
   - Create `backend/alembic_migrations/versions/2026_09_14_010000_create_mcp_gateway_tables.py` to establish `mcp_slugs`, `mcp_tenants`, and `mcp_clients`.
2. **Database Adapter in Node.js Control Tower:**
   - Create [infrastructure/mcp-control-plane/src/tenancy/db.adapter.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/tenancy/db.adapter.ts) using `pg` / Postgres connection pool or Supabase REST/Postgres.
   - Implement read-through LRU cache with 60s TTL for slug and token resolutions to avoid DB bottlenecks on high-frequency MCP calls.
3. **Refactor Tenant & Client Registries:**
   - Upgrade [tenant.registry.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/tenancy/tenant.registry.ts) and [client-registry.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/policy/client-registry.ts) to query the DB adapter when `DATABASE_URL` / `SUPABASE_URL` is configured, with seamless fallback to existing JSON file in local test environments.

### Phase B: Gateway Routing & Subdomain Slug Resolution
*Primary Goal: Allow vanity URL requests to resolve to the correct tenant context.*

1. **Host Extraction Middleware in Control Tower:**
   - In [index.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/index.ts):
     ```typescript
     function extractSlugFromHost(hostHeader?: string): string | null {
       if (!hostHeader) return null;
       const host = hostHeader.split(":")[0].toLowerCase();
       // e.g. "niloy.mcp.supremeai.ai" or "niloy.localhost"
       const parts = host.split(".");
       if (parts.length >= 3 && parts[1] === "mcp") return parts[0];
       if (host.endsWith(".localhost") && parts.length === 2) return parts[0];
       return null;
     }
     ```
   - Resolve `slug` $\to$ `tenant_id`.
   - If caller's client token has a `tenantId` that does NOT match the resolved `tenant_id`, return `403 Forbidden: Token not valid for this MCP subdomain`.
2. **Cloudflare Worker Edge Update:**
   - Update [infrastructure/cloudflare_worker.js](file:///f:/supremeai/infrastructure/cloudflare_worker.js) and [infrastructure/wrangler.toml](file:///f:/supremeai/infrastructure/wrangler.toml):
     - Add route rule: `*.mcp.supremeai.ai/*` $\to$ route directly to `MCP_URL` (`https://supremeai-mcp-tower.onrender.com`).
     - Pass down `Host` and custom header `X-MCP-Slug` to the origin.

### Phase C: Backend Management API for Slugs & Clients
*Primary Goal: Expose REST endpoints in FastAPI for claiming slugs and managing AI clients.*

1. **FastAPI Routes (`backend/api/routes/mcp_hub.py`):**
   - `GET /api/v1/mcp/gateway`: Returns user's assigned slug, gateway URL, and tenant stats.
   - `POST /api/v1/mcp/slug/claim`: Validates and claims a vanity slug (checks reserved words: `admin`, `api`, `app`, `core`, `system`, `hub`, `auth`).
   - `GET /api/v1/mcp/clients`: Lists all registered AI clients for the authenticated user's tenant.
   - `POST /api/v1/mcp/clients`: Registers a new AI client (returns client ID + secret token once).
   - `PATCH /api/v1/mcp/clients/{client_id}`: Updates client role (`viewer`, `agent`, `admin`) or provider.
   - `POST /api/v1/mcp/clients/{client_id}/rotate`: Rotates client token.
   - `DELETE /api/v1/mcp/clients/{client_id}`: Revokes client access.

### Phase D: Frontend MCP Hub Interface
*Primary Goal: Replace the simple viewer with a comprehensive Personal MCP Hub.*

1. **New UI Component:**
   - Create `frontend/src/pages/user/MCPHub.tsx` and integrate it into `IntegrationsManager.tsx` or as a top-level `/hub/mcp` route.
   - **Hero Section:**
     - Displays: `https://<slug>.mcp.supremeai.ai` with a 1-click copy button.
     - "Claim / Change Subdomain" modal.
   - **Connected AI Clients Table:**
     - Cards/Rows for Claude, Cursor, Gemini, VS Code, Custom.
     - Status badges: `Active`, `Pending Approval`, `Revoked`.
     - Dropdown for Role selection: `Viewer` (Read-only), `Agent` (Standard Tools), `Admin` (Full Control).
     - Token preview with "Copy Setup Config" button (generates ready-to-paste `claude_desktop_config.json` and `.cursor/mcp.json`).
   - **Real-time Activity Log:**
     - Last seen timestamp and tool invocation count per client.

### Phase E: Policy Engine & Multi-Client Isolation
*Primary Goal: Fine-grained governance per client type.*

1. **Default vs Advanced Client Governance:**
   - **Default Mode:** All clients of a tenant inherit the tenant's base policy.
   - **Advanced Mode:** Specific tools can be restricted per client (e.g., Cursor gets `tools:execute` for code refactoring; Claude Web gets read-only `docs:read` + `knowledge:search`).
2. **Audit Logging Integration:**
   - Every MCP call logs `client_id`, `provider`, `tenant_id`, `slug`, and `action` to the append-only audit trail.

---

## 5. Proposed File Modifications & Additions

### Backend & Database
- `[NEW]` [backend/alembic_migrations/versions/2026_09_14_010000_create_mcp_gateway_tables.py](file:///f:/supremeai/backend/alembic_migrations/versions/2026_09_14_010000_create_mcp_gateway_tables.py)
- `[NEW]` [backend/models/mcp_gateway.py](file:///f:/supremeai/backend/models/mcp_gateway.py)
- `[NEW]` [backend/api/routes/mcp_hub.py](file:///f:/supremeai/backend/api/routes/mcp_hub.py)
- `[MODIFY]` [backend/main.py](file:///f:/supremeai/backend/main.py) — Register `mcp_hub.router`

### MCP Control Tower (Node.js)
- `[NEW]` [infrastructure/mcp-control-plane/src/tenancy/db.adapter.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/tenancy/db.adapter.ts)
- `[NEW]` [infrastructure/mcp-control-plane/src/tenancy/slug.resolver.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/tenancy/slug.resolver.ts)
- `[MODIFY]` [infrastructure/mcp-control-plane/src/tenancy/tenant.registry.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/tenancy/tenant.registry.ts)
- `[MODIFY]` [infrastructure/mcp-control-plane/src/policy/client-registry.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/policy/client-registry.ts)
- `[MODIFY]` [infrastructure/mcp-control-plane/src/index.ts](file:///f:/supremeai/infrastructure/mcp-control-plane/src/index.ts) — Add subdomain extraction and cross-tenant validation

### Edge Routing (Cloudflare)
- `[MODIFY]` [infrastructure/wrangler.toml](file:///f:/supremeai/infrastructure/wrangler.toml) — Add wildcard route
- `[MODIFY]` [infrastructure/cloudflare_worker.js](file:///f:/supremeai/infrastructure/cloudflare_worker.js) — Subdomain inspection and pass-through

### Frontend
- `[NEW]` [frontend/src/pages/user/MCPHub.tsx](file:///f:/supremeai/frontend/src/pages/user/MCPHub.tsx)
- `[NEW]` [frontend/src/services/mcpHubService.ts](file:///f:/supremeai/frontend/src/services/mcpHubService.ts)
- `[MODIFY]` [frontend/src/pages/user/IntegrationsManager.tsx](file:///f:/supremeai/frontend/src/pages/user/IntegrationsManager.tsx) — Embed the new MCP Hub

---

## 6. Verification & Testing Plan

### 6.1 Automated Tests
1. **Database & API Suite:**
   - Run `pytest backend/tests/api/routes/test_mcp_hub.py` to verify slug claiming, collision rejection, and client token generation.
2. **Control Tower Unit & Integration Tests:**
   - Add `test_slug_resolution.ts` in `infrastructure/mcp-control-plane/`:
     - Test slug extraction from `Host: alice.mcp.supremeai.ai`.
     - Test token belonging to `tenant_bob` attempting to access `alice.mcp.supremeai.ai` (must yield `403`).
     - Test valid token for `tenant_alice` on `alice.mcp.supremeai.ai` (yields `200` with proper role/scopes).
3. **CI Pipeline Validation:**
   - Verify that `build-mcp` and `backend-test` pass cleanly in GitHub Actions.

### 6.2 Manual & Edge Verification
1. **Localhost Subdomain Simulation:**
   - Test using `curl -H "Host: testuser.localhost" http://localhost:8080/mcp` with valid and invalid Bearer tokens.
2. **Client Config Verification:**
   - Generate config for Claude Desktop (`claude_desktop_config.json`) and test connection against the local or staging MCP Gateway.
