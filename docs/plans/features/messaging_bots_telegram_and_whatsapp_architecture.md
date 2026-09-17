---
target_scope: supremeai_internal
---

# Plan: The 3 Faces of SupremeAI — Unified Omnichannel Interaction Gateway (Web Dashboard, Telegram Bot & WhatsApp Bot)
**Document:** `docs/plans/features/messaging_bots_telegram_and_whatsapp_architecture.md`  
**Status:** 🔄 **ACTIVE / IN PROGRESS** (Web & Telegram Live, WhatsApp Planned)  
**Priority:** HIGH (P1)  
**Domain Circle:** Circle C3 (DevOps & Messaging) + Circle C4 (Frontend UI) + Circle C5 (Agent Orchestration)  
**Governing Rule:** *AGENTS.md Clause 1 & Clause 7: "Frontend = Face, Not the Private Brain" & Unified Tri-Interface Abstraction*

---

## 🎯 1. Executive Summary & Vision: "One Living Brain, Three Interaction Faces"

SupremeAI-এর মূল দর্শন হলো: **একটাই সেন্ট্রাল ইন্টেলিজেন্স ও অর্কেস্ট্রেশন ব্রেন, কিন্তু ব্যবহারকারী ও অ্যাডমিনের সাথে যোগাযোগের ৩টি সমান শক্তিশালী মুখ (3 Faces of SupremeAI):**

1. **Face 1: Web Dashboard (The Visual Face):** ব্রাউজার ও ডেস্কটপ ইন্টারফেস (`frontend/src/`) — যেখানে রিচ ডেটা ভিজুয়ালাইজেশন, ডায়নামিক প্লাগইন সেটিংস, ৩ডি টেলিমেট্রি এবং ফুল-স্ক্রিন কোডিং স্টুডিও পরিচালিত হয়।
2. **Face 2: Telegram Bot (The Agile Mobile Command Face):** দ্রুত কমান্ড, নোটিফিকেশন, মোবাইল অন-দ্য-গো ম্যানেজমেন্ট এবং TelDrive জিরো-কস্ট ব্যাকআপ স্টোরেজ (`backend/tools/social/telegram_bot/`)।
3. **Face 3: WhatsApp Bot (The Universal Ubiquitous Face):** পৃথিবীর সর্বাধিক ব্যবহৃত মেসেজিং নেটওয়ার্কের মাধ্যমে অ্যাডমিন কন্ট্রোল, টিম কোলাবরেশন এবং প্রো-অ্যাক্টিভ ইন্সিডেন্ট ম্যানেজমেন্ট (`backend/tools/social/whatsapp_bot/`)।

> 💡 **গোল্ডেন রুল:** ব্যবহারকারী ড্যাশবোর্ড থেকে কমান্ড দিক, টেলিগ্রাম চ্যাট থেকে দিক, বা হোয়াটসঅ্যাপ মেসেজ থেকে দিক — ভেতরের **অ্যাকশন, সিকিউরিটি পলিসি, মেমোরি কনটেক্সট এবং এআই রেসপন্স ১০০% একই থাকবে।** ৩টি মুখ একই ব্যাকএন্ড প্রোটোকলের সাথে সরাসরি সংযুক্ত।

---

## 🏛️ 2. The Tri-Interface Gateway Topology

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             THE 3 FACES OF SUPREMEAI                             │
│                                                                                  │
│   ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐   │
│   │   FACE 1: WEB UI     │  │  FACE 2: TELEGRAM    │  │  FACE 3: WHATSAPP    │   │
│   │   - React 19 Studio  │  │  - Bot API / Webhook │  │  - Cloud API / Hooks │   │
│   │   - Mission Control  │  │  - Inline Keyboards  │  │  - Interactive Lists │   │
│   │   - 3D Telemetry     │  │  - Mobile Alerts     │  │  - Instant Ping      │   │
│   └──────────┬───────────┘  └──────────┬───────────┘  └──────────┬───────────┘   │
└──────────────┼─────────────────────────┼─────────────────────────┼───────────────┘
               │                         │                         │
               ▼                         ▼                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      UNIFIED INBOUND GATEWAY & SECURITY LAYER                     │
│  - Identity & Tenant Mapping (Web Token / Telegram ID / WhatsApp Phone Number)   │
│  - Unified Security Guard (RBAC Roles, Session Nonce, TOTP 2FA Verification)     │
│  - Normalized Event Schema (Command, Prompt, Callback, File Attachment)          │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      CENTRAL BRAIN & CONTROL PLANE CORE                          │
│  - FastMCP Control Tower (10 Domain Circles Orchestration)                      │
│  - SupremeOrchestrator (Multi-Agent Swarm: Gemini, Groq, Claude, Ollama)         │
│  - Tri-Layer Polyglot Memory (Supabase Postgres + Redis Cache + Qdrant Vector)   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📱 3. Face-by-Face Capability Alignment

| Capability / Action | Face 1: Web Dashboard | Face 2: Telegram Bot | Face 3: WhatsApp Bot |
|---|:---:|:---:|:---:|
| **Authentication Mode** | Supabase JWT & Cookie Session | Telegram `initData` + TOTP 2FA | Phone ID Match + WhatsApp TOTP 2FA |
| **System Health Sweep** | Real-time SVG / Charts | `/status` Inline Keyboard | `status` Interactive Button Menu |
| **Customer Experience** | Clean conversation & prompt runner | Natural Language Assistant & project status | Ubiquitous chat assistant & task notifications |
| **Admin Experience** | Full Mission Control & 3D Telemetry | `/admin` commands, quick approval & TelDrive | Emergency commands, 2FA kill-switch & alerts |
| **Task / Prompt Execution**| Studio Terminal / Chat Tab | Direct Message NLP Dispatch | Direct Message NLP Dispatch |
| **Destructive HITL Approval**| Modal Dialog Confirm Button | Inline 2FA Callback Button | WhatsApp Quick Reply 2FA Button |
| **Telemetry & Metrics** | 3D Graph + WebSockets | Live Markdown Metric Snap | Compact Text / Card Summary |
| **Database & Config Backups**| One-Click Export in UI | TelDrive Encrypted Channel | Encrypted Media Attachment |
| **Emergency Kill-Switch** | Admin Red Button | `/kill` + 2FA PIN | `kill` + 2FA PIN |

---

## 🛠️ 4. Shared Backend Abstraction & Security

### 4.1 Universal Security Guard (`messaging_security_guard.py`)
টেলিগ্রাম ও হোয়াটসঅ্যাপের আলাদা আলাদা সিকিউরিটি ফাইল না রেখে একটি সেন্ট্রাল গার্ড থাকবে:
- **Tenant & Identity Resolver:** টেলিগ্রাম চ্যাট আইডি বা হোয়াটসঅ্যাপ ফোন নম্বরকে ইন্টারনাল `tenant_id` এবং `user_role` (SuperAdmin, WorkspaceAdmin, User) এ ম্যাপ করে।
- **Shared TOTP 2FA Engine:** স্পর্শকাতর কোনো কমান্ড (যেমন: সার্ভার রিস্টার্ট, ক্যাশ ফ্ল্যাশ, বিলিং চেঞ্জ) যেকোনো মুখ থেকেই আসুক না কেন, সিস্টেম ৬ ডিজিটের Google Authenticator TOTP চাইবে।

### 4.2 Unified Message Dispatcher
```python
class NormalizedMessage(BaseModel):
    source_face: Literal["web", "telegram", "whatsapp"]
    sender_id: str
    tenant_id: str
    role: UserRole
    text: str
    attachments: list[dict] = []
    session_id: str
```
সব ৩টি মুখ থেকে আসা ইনপুট এই একক অবজেক্টে কনভার্ট হয়ে সরাসরি সেন্ট্রাল `SupremeOrchestrator` এ প্রবেশ করবে।

---

## 🚀 5. WhatsApp Integration Roadmap (Reaching Parity with Telegram)

1. **Backend Package Creation (`backend/tools/social/whatsapp_bot/`):**
   - `router.py`: FastAPI Webhook রুট (`/api/v1/whatsapp/webhook`) — Meta Handshake এবং ইনবাউন্ড মেসেজ রিসিভার।
   - `handler.py`: `WhatsAppBotHandler` — টেক্সট, ইন্টারঅ্যাক্টিভ বাটন এবং লিস্ট মেসেজ সেন্ডার।
   - `keyboards.py`: টেলিগ্রাম ইনলাইন কিবোর্ডের সমতুল্য হোয়াটসঅ্যাপ ইন্টারঅ্যাক্টিভ কম্পোনেন্ট বিল্ডার।
2. **Meta Cloud API Setup:**
   - WhatsApp Business Platform API কনফিগারেশন (মাসে প্রথম ১,০০০ সার্ভিস মেসেজ সম্পূর্ণ ফ্রি)।
   - অফলাইন/লোকাল টেস্টের জন্য Baileys বা Twilio স্যান্ডবক্স ফলব্যাক।
3. **Control Tower Tool Integration:**
   - `supremeai-control-tower` এ নতুন টুল এক্সপোজ করা: `notify_send_whatsapp` (যাতে এআই নিজে অ্যাডমিনকে হোয়াটসঅ্যাপে জরুরি অ্যালার্ট পাঠাতে পারে)।