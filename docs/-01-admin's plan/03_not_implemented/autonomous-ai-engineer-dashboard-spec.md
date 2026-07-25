# Autonomous AI Engineer Dashboard — "Sujon Core" Specification

## Overview
Production architecture specification for a cross-platform web automation cockpit dashboard with live execution shell, sandbox viewport, agent state machine, and human-in-the-loop protocols.

---

## 🔍 Codebase Audit (2026-07-26)

### Status: 🔴 Truly Not Implemented

This is a new feature that does not exist in the codebase yet. No cockpit-style dashboard or Sujon Core implementation found.

### What Already Exists (Related Infrastructure)

| Component | Code Location | How It Helps |
|-----------|--------------|--------------|
| **HeadlessTerminalAgent** | `backend/agents/headless_terminal_agent.py` | Can serve as the execution engine for the cockpit's shell pane |
| **SwarmPubSub (Redis)** | `backend/core/swarm_pubsub.py` | Can stream execution logs to the frontend in real-time |
| **NATS Messaging** | `backend/core/messaging/nats_messaging.py` | Can be used for agent state machine event distribution |
| **Admin Dashboard (28+ components)** | `apps/studio-client/src/components/admin/` | Existing dashboard framework can be extended with cockpit panels |
| **LLM Router** | `backend/core/llm_router.py` | Can power the agent reasoning log pane |
| **Session Takeover** | `backend/api/routes/session_takeover.py` | Existing session management can be extended for HITL protocol |

### Recommendation
This is genuinely new work, but has significant existing infrastructure to build upon. The HeadlessTerminalAgent provides the execution engine, SwarmPubSub provides real-time streaming, and the existing admin dashboard provides the UI framework. Build the cockpit as new panels within the existing admin dashboard rather than a standalone app.
