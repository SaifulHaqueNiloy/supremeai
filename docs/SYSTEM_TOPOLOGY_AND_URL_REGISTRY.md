# SupremeAI System Topology & URL Registry
> **Single Source of Truth (SSOT)** for all system endpoints, backend gateways, and feature URL mappings.
> যেকোনো নতুন ফিচার, ক্লাউড মাইগ্রেশন বা অ্যান্ডপয়েন্ট পরিবর্তনের সময় এই ফাইলটি আপডেট ও রেফারেন্স হিসেবে ব্যবহার করতে হবে।

---

## 🗺️ ১. Master Gateway & Base URLs

| এনভায়রনমেন্ট / গেটওয়ে | ক্যানোনিকাল URL | প্রটোকল | সার্ভিস বর্ণনা |
| :--- | :--- | :--- | :--- |
| **Cloudflare Worker Gateway** | `https://supremeai-worker.paykaribazaronline.workers.dev` | HTTPS / WSS | আল্ট্রা-ফাস্ট এজ রাউটার, ব্যান্ডউইথ অপটিমাইজার ও মেইন এপিআই গেটওয়ে |
| **Render Docker Backend (Primary)** | `https://supremeai-backend-docker.onrender.com` | HTTPS / WSS | FastAPI কোর ব্যাকএন্ড, পাইপলাইন, ডাটাবেস হ্যান্ডলার ও এআই অরকেস্ট্রেটর |
| **Render Frontend Workspace** | `https://supremeai-frontend-6nwi.onrender.com/workspace` | HTTPS | লাইভ ক্লাউড ফ্রন্টএন্ড ওয়েব স্টুডিও ও ওয়ার্কস্পেস |
| **Admin Portal (Firebase)** | `https://supremeai-admin.web.app` / `https://supremeai-admin.firebaseapp.com` | HTTPS | সুপ্রিমএআই সুপার-অ্যাডমিন ড্যাশবোর্ড |
| **User Web App (Firebase / Vercel)** | `https://supremeai-a.web.app` / `https://supremeai-a.firebaseapp.com` | HTTPS | ইউজার ওয়েব ক্লায়েন্ট |
| **Offline Supporting Hand** | `http://localhost:11434` | HTTP REST | লোকাল Ollama (শুধুমাত্র অফলাইন ফলব্যাকের জন্য অনুমোদিত) |

---

## 🧩 ২. Feature to URL & Client Mapping Matrix

| ফিচার / মডিউল | ক্লায়েন্ট ফাইল লোকেশন | এনভায়রনমেন্ট ভ্যারিয়েবল / কনফিগ কী | রিয়েল প্রোডাকশন অ্যান্ডপয়েন্ট | প্রটোকল | ফলব্যাক স্ট্র্যাটেজি |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AI Chat & Streaming** | `frontend/src/utils/api.ts` | `VITE_API_BASE`, `VITE_API_URL` | `https://supremeai-backend-docker.onrender.com/api/v1/chat` | HTTPS (SSE / REST) | Render Retry Backoff |
| **Swarm & Trio 2.0 Pipeline** | `tools/vscode-extension/src/services/SwarmPipelineProvider.ts` | `supremeai.swarmBackendUrl`, `supremeai.backendUrl` | `https://supremeai-worker.paykaribazaronline.workers.dev/api/v1/ide-trio/execute` | HTTPS POST | Worker Failover |
| **Cross-AI Observer Engine** | `tools/vscode-extension/src/services/CrossAiObserverService.ts` | `supremeai.backendUrl` | `https://supremeai-worker.paykaribazaronline.workers.dev/api/evolution/learn` | HTTPS POST | In-memory Queue |
| **Dynamic Sidebar Skills** | `tools/vscode-extension/src/providers/SupremeWebviewProvider.ts` | `supremeai.backendUrl` | `https://supremeai-worker.paykaribazaronline.workers.dev/api/skills` | HTTPS GET | Cached Recipes |
| **Telemetry & Patch Tracker** | `tools/vscode-extension/src/services/TelemetryTracker.ts` | `supremeai.backendUrl` | `https://supremeai-worker.paykaribazaronline.workers.dev/api/v1/swarm/telemetry/patch-result` | HTTPS POST | Silent Drop on Offline |
| **Customer Usage Dashboard** | `tools/vscode-extension/src/providers/SupremeAICustomerDashboardProvider.ts` | `supremeai.backendUrl` | `https://supremeai-worker.paykaribazaronline.workers.dev` | HTTPS GET | Local Session Storage |
| **Real-Time Voice Matrix** | `frontend/src/utils/api.ts` | `VITE_WS_BASE_URL` | `wss://supremeai-backend-docker.onrender.com/api/voice/ws` | WebSocket (WSS) | REST fallback |
| **Live 3D Brain Visualizer** | `frontend/src/components/BrainVisualizer/LiveBrainVisualizer.tsx` | `VITE_WS_BASE_URL` | `wss://supremeai-backend-docker.onrender.com/api/brain-visualizer/ws` | WebSocket (WSS) | Polling Snapshot `/api/brain-visualizer/snapshot` |
| **Collaborative Editor Sync** | `backend/tools/collaborative_editor.py` | `REDIS_URL` | Upstash Redis TLS (`rediss://...`) | Redis Pub/Sub | Local Dev Redis (`redis://localhost:6379`) |
| **Self-Assembling Studio** | `frontend/src/utils/api.ts` | `VITE_API_BASE` | `https://supremeai-backend-docker.onrender.com/api/self-assemble` | HTTPS POST | Task Queue |
| **Auth & JIT OTP** | `frontend/src/utils/api.ts` | `VITE_API_BASE` | `https://supremeai-backend-docker.onrender.com/auth/login` | HTTPS POST | Rate-limited Retry |

---

## 🔒 ৩. Security & Isolation Rules
1. **No Third-Party AI Direct Exposure:** ফ্রন্টএন্ড বা এক্সটেনশন কখনোই সরাসরি OpenAI, Anthropic বা Gemini API-তে কথা বলবে না। সব রিকোয়েস্ট SupremeAI গেটওয়ে হয়ে যাবে।
2. **Dynamic Fallbacks:** ক্লায়েন্ট ফাইলে কোনো হার্ডকোডেড `localhost` রাখা যাবে না। সবসময় `import.meta.env` বা `vscode.workspace.getConfiguration` দিয়ে কনফিগুরেবেল রাখতে হবে।
3. **Automated Audit:** যেকোনো রিলিজের আগে `python scripts/audit_topology_urls.py` রান করে কনফিগ ভ্যালিডেট করতে হবে।
