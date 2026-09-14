# Plan: Messaging Bot Architecture — Telegram & WhatsApp Omnichannel Gateway
**Document:** `docs/plans/features/messaging_bots_telegram_and_whatsapp_architecture.md`  
**Status:** 🔄 **ACTIVE / IN PROGRESS** (Telegram Live, WhatsApp Planned)  
**Priority:** HIGH (P1)  
**Domain Circle:** Circle C3 (DevOps & Messaging) + Circle C5 (Agent Orchestration)  
**Governing Rule:** *AGENTS.md Clause 1 & Clause 5: Unified Omnichannel Messaging Abstraction with Zero Cross-Wiring*

---

## 🎯 1. Executive Summary & Vision

SupremeAI is designed as an accessible, multi-surface autonomous AI operating system. Users and administrators should be able to interact with SupremeAI's core intelligence, query system telemetry, trigger autonomous workflows, and receive proactive incident alerts directly from their daily messaging platforms.

- **Current State:** A comprehensive, production-hardened **Telegram Bot** is fully implemented (`backend/tools/social/telegram_bot/`), featuring webhook/polling modes, TOTP 2FA admin authentication, TelDrive zero-cost encrypted storage, and direct routing to SupremeOrchestrator.
- **Target Evolution:** Extend this messaging architecture into a **Unified Omnichannel Gateway** that mirrors all conversational, administrative, and notification capabilities into **WhatsApp** (via Meta Cloud API / Baileys / Twilio WhatsApp API) using identical shared cognitive routers, security layers, and intent dispatchers.

---

## 🏛️ 2. Core Architectural Philosophy: Provider-Neutral Gateway

Never hardcode single-platform implementations. The architecture separates the **Messaging Provider Adapter** from the **SupremeAI Cognitive Brain**:

```text
┌──────────────────────┐          ┌──────────────────────┐
│  Telegram Client     │          │  WhatsApp Client     │
│  (Bot API / Webhook) │          │  (Cloud API/Webhook) │
└──────────┬───────────┘          └──────────┬───────────┘
           │                                 │
           ▼                                 ▼
┌──────────────────────┐          ┌──────────────────────┐
│ Telegram Adapter     │          │ WhatsApp Adapter     │
│ (updates.py)         │          │ (whatsapp_handler.py)│
└──────────┬───────────┘          └──────────┬───────────┘
           │                                 │
           └────────────────┬────────────────┘
                            ▼
           ┌─────────────────────────────────┐
           │   Unified Messaging Interface   │
           │   - Inbound Message Normalizer  │
           │   - Security & TOTP 2FA Guard   │
           │   - Session & Thread Context    │
           └────────────────┬────────────────┘
                            │
                            ▼
           ┌─────────────────────────────────┐
           │ Central MCP Control Tower /     │
           │ SupremeOrchestrator Brain       │
           │ (Multi-Agent Routing & Memory)  │
           └─────────────────────────────────┘
```

---

## 📱 3. Existing Telegram Bot Architecture (Live & Verified)

### 3.1 Location & Modular Split
`backend/tools/social/telegram_bot/`:
- `handler.py` — Core `TelegramBotHandler` lifecycle, configuration bootstrap, Bot API HTTP requests.
- `keyboards.py` — Inline interactive keyboard layouts (Admin Command Center, User Studio, Quick Action triggers).
- `updates.py` — Update dispatcher for webhook/polling; enforces **AutonoGuard** injection protection and session states.
- `conversations.py` — Multi-turn conversation flows, MCP client discovery, telemetry reporting, and knowledge base search.
- `admin_handlers.py` — High-privilege controls (Health sweep, TelDrive encrypted database backups, devops controls, rules inspector).
- `user_handlers.py` — User-facing panels (Desktop client downloads, VSIX extension, skill catalogue).
- `ai_engine.py` — Fallback cognitive response pipeline (Gemini $\to$ Groq $\to$ SupremeOrchestrator).
- `router.py` — FastAPI webhook route definition (`/telegram/webhook`).

### 3.2 Security & 2FA Layer
- Located at `backend/tools/social/telegram_security.py`.
- **TelegramSecurityGuard**: Verifies Telegram `initData` HMAC-SHA256 signatures, manages user role whitelists (Admin vs User), and mandates **TOTP 2FA** tokens before executing destructive actions (e.g. system reboots, database operations, cache purges).

---

## 💬 4. WhatsApp Bot Architecture Plan (Identical Capabilities)

To deliver parity on WhatsApp, SupremeAI will implement a symmetrical package: `backend/tools/social/whatsapp_bot/`.

### 4.1 Integration Options
1. **Meta WhatsApp Cloud API (Primary Enterprise Path):**
   - Official, webhook-based, highly reliable for production.
   - Hosted directly on Meta's infrastructure with zero local browser/session overhead.
   - Free tier: First 1,000 service conversations per month are completely free.
2. **Baileys / Node.js Bridge (Zero-Cost Free Alternative):**
   - Headless WebSocket connection to WhatsApp Web.
   - Can run as an internal sidecar or micro-worker.
3. **Twilio WhatsApp API (Fallback Provider):**
   - Zero configuration sandbox for rapid testing and verified SMS/WhatsApp alerting.

### 4.2 Module Layout for WhatsApp Bot (`backend/tools/social/whatsapp_bot/`)
- `__init__.py` — Package exports and configuration bootstrap (`WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`).
- `handler.py` — `WhatsAppBotHandler` responsible for sending text, interactive list messages, and template notifications.
- `updates.py` — Inbound webhook validator handling Meta verification challenge (`hub.challenge`) and decrypting incoming messages.
- `keyboards.py` — Converts SupremeAI UI actions into WhatsApp **Interactive Buttons** (up to 3 buttons) and **Interactive Section Lists** (up to 10 options).
- `router.py` — FastAPI webhook endpoint:
  - `GET /api/v1/whatsapp/webhook` — Meta Webhook verification handshake.
  - `POST /api/v1/whatsapp/webhook` — Inbound message and status updates payload.
- `security.py` — Shared integration with `TelegramSecurityGuard` for TOTP verification over WhatsApp messages.

---

## 🔄 5. Feature Parity Matrix

| Feature | Telegram Bot (Live) | WhatsApp Bot (Target) |
|---|:---:|:---:|
| **Webhook Delivery** | ✅ Yes (`/telegram/webhook`) | 🎯 Yes (`/api/v1/whatsapp/webhook`) |
| **Local Polling Mode** | ✅ Yes (Long-polling fallback) | ⚠️ N/A (Webhooks only) |
| **Interactive Buttons / Menus** | ✅ Inline Keyboards | 🎯 WhatsApp Interactive Buttons & Lists |
| **2FA / TOTP High-Risk Guard** | ✅ Enforced via `telegram_security.py` | 🎯 Enforced via shared TOTP engine |
| **System Health & Telemetry** | ✅ `/status`, `/health` | 🎯 `status`, `health` commands & quick reply |
| **Autonomous AI Chat** | ✅ Gemini $\to$ Groq $\to$ Orchestrator | 🎯 Same cognitive pipeline |
| **Database & Config Backups** | ✅ TelDrive encrypted channel | 🎯 Media attachment delivery |
| **Proactive Incident Alerts** | ✅ Notification engine | 🎯 WhatsApp Template Notification |

---

## 🛠️ 6. Implementation Roadmap

### Phase 1: Shared Core Abstraction
- Refactor `telegram_security.py` into a generic `messaging_security_guard.py` so TOTP sessions and user permissions apply equally to Telegram and WhatsApp sender IDs.
- Create unified message schemas (`IncomingMessage`, `OutgoingMessage`, `InteractiveMenu`).

### Phase 2: WhatsApp Webhook & Handler Implementation
- Implement `backend/tools/social/whatsapp_bot/` with Meta Cloud API webhook verification.
- Connect inbound messages to `SupremeOrchestrator` agent loop.

### Phase 3: Interactive Command Parity
- Implement WhatsApp List Messages for Admin Command Center (Health, Deployments, AI Provider Status, Memory Search).
- Implement interactive confirmation for consequential HITL approvals via WhatsApp buttons.

### Phase 4: Control Tower & Notification Integration
- Register WhatsApp tools in `supremeai-control-tower` (`notify_send_whatsapp`).
- Update notification dispatchers to route critical alerts simultaneously to Telegram and WhatsApp channels.
