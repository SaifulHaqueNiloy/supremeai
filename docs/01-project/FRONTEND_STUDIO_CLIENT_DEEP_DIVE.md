# SupremeAI 2.0 — Frontend & Studio Client Deep-Dive Specification
**Document ID:** `DOC-FRONTEND-2026-001`  
**Category:** Frontend Architecture, UI Security & State Management  
**Target:** `apps/studio-client/` (~243 files) & Admin Portals  
**Status:** Live Technical Specification  
**Author:** SupremeAI Frontend & Security Engineering Team  

---

## 📌 1. Executive Summary & Core Scope

The frontend of SupremeAI 2.0 (`apps/studio-client`) is built on React 18, TypeScript, TailwindCSS, Zustand for state management, and Vite/Next.js tooling. It serves as the primary interface for customer interactions, multi-agent chat, live prompt execution, and tenant admin controls.

This document details:
1. **Frontend Architecture & Directory Structure** (`apps/studio-client/src/`)
2. **Security Hardening & Remediation** (ChatPanel XSS Sanitization & JWT Storage Security)
3. **State Management & Real-Time Hydration** (Zustand Stores & Event Bus)
4. **Admin Portals Breakdown** (Full Admin Dashboard vs Light Admin Portal)

---

## 🏗️ 2. Frontend Directory Structure

```
apps/studio-client/src/
├── components/
│   ├── customer/
│   │   ├── ChatPanel.tsx       <-- Main Multi-Agent Chat (XSS Sanitized)
│   │   ├── PromptInput.tsx     <-- User Input & File Attachment Handler
│   │   └── ResponseViewer.tsx  <-- Code & Markdown Renderer
│   ├── admin/
│   │   ├── QuotaMonitor.tsx    <-- Real-time Tenant Quota & Billing Metrics
│   │   └── AgentSupervisorUI.tsx<-- Live Background Agent Monitor
│   └── shared/
│       ├── UIComponents.tsx
│       └── Header.tsx
├── store/
│   ├── useChatStore.ts         <-- Chat Messages & Active Session State
│   ├── useAuthStore.ts         <-- User Session, JWT & RBAC Permissions
│   └── useAgentStore.ts        <-- Swarm Agent Execution Telemetry
├── services/
│   ├── api.ts                  <-- Axios / Fetch wrapper with Bearer Token
│   └── websocket.ts            <-- Real-time Collaborative WS Client
└── utils/
    └── sanitize.ts             <-- HTML & Script Escaping Helper
```

---

## 🛡️ 3. Security Hardening & Remediation

### 3.1 ChatPanel XSS Remediation (`ChatPanel.tsx`)
- **Vulnerability:** Raw HTML rendering without escaping allowed arbitrary `<script>` injection and potential session hijacking.
- **Remediation Implemented:**
  1. All incoming prompt and LLM stream text is passed through `sanitizeHtml()` before regex parsing or markdown rendering.
  2. Strict Content Security Policy (CSP) headers added to frontend server delivery.

### 3.2 Authentication & JWT Token Storage
- **Current State:** JWT stored in `localStorage` / Zustand persisted state for fast SPA rehydration.
- **Production Migration Target:** Transitioning to `HttpOnly`, `SameSite=Strict`, `Secure` cookies for production enterprise deployments to eliminate token theft risk via DOM access.

---

## 📊 4. Admin Portals Comparison

| Feature | Full Admin Portal (`apps/studio-client/src/components/admin`) | Admin Dashboard Light (`admin/dashboard_light.html`) |
|---|---|---|
| **Target Audience** | Enterprise System Administrators | On-call DevOps & Zero-Cost Free Tier Monitors |
| **Dependencies** | React 18, Recharts, Zustand, Tailwind | Single standalone HTML/JS file (No Node runtime) |
| **Real-time Metrics** | WebSocket telemetry + SSE streaming | REST Polling (10s interval) |
| **Resource Usage** | Heavy SPA client | Zero-footprint static server |

---

## 🎯 5. Conclusion & Integration
With XSS escaping active in `ChatPanel.tsx` and Zustand state hydration verified, `apps/studio-client` provides a secure, reactive, and responsive interface for SupremeAI 2.0 users across web and desktop integrations.
