# 🔍 Codebase Hardcoded Value Analysis

I have scanned the entire SupremeAI codebase for hardcoded `URLs`, `ports`, `timeouts`, and `API limits`. Here is what I found. There are several critical areas where hardcoded values exist and should be moved to our new **System Dynamic Config Module** or `.env` variables.

## 🚨 Critical Hardcoded Areas Found

### 1. Hardcoded WebApp URLs in Telegram Bot
In `backend/tools/social/telegram_bot.py`, the Mini App and Admin Dashboard URLs are fully hardcoded. If you change your frontend hosting (e.g., Vercel to Cloudflare), the Telegram bot will break and point to dead links.
*   `https://supremeai-lac.vercel.app` (Hardcoded 5+ times)
*   `https://supremeai-admin.web.app`
*   `https://supremeai-backend-docker.onrender.com/docs`

**Solution:** Inject these via `SystemDynamicConfig.get("FRONTEND_URL")` and `SystemDynamicConfig.get("ADMIN_URL")`.

### 2. Timeouts in External HTTP Requests
I found over **250 instances** of hardcoded timeouts in `httpx.AsyncClient(timeout=X)` across various tools and workers (e.g., `telegram_bot.py`, `mcp_cloud_deploy.py`, `marketplace_agent.py`, `vpn_switcher.py`).
*   Example: `httpx.AsyncClient(timeout=10)`
*   Example: `page.wait_for_selector(..., timeout=2000)` (Playwright)

**Solution:** These should fetch from the dynamic config `SystemDynamicConfig.get("DEFAULT_HTTP_TIMEOUT_MS")`. If an API suddenly becomes slow, we can increase the timeout from the Admin Dashboard without deploying code.

### 3. LLM Provider API URLs
In `backend/services/llm/providers.py` and `llm_router.py`, the base URLs for many providers are hardcoded:
*   `https://api.moonshot.cn/v1`
*   `https://api.deepseek.com/v1`
*   `https://api.together.xyz/v1`

**Solution:** While API URLs rarely change, hardcoding them prevents using a proxy (e.g., LiteLLM proxy or Cloudflare AI Gateway). We should use `.env` fallbacks for these `BASE_URL`s.

### 4. Enterprise SSO & SAML Configurations
In `backend/tools/sso_integrator.py`, metadata URLs and Microsoft/Google OAuth endpoints are partially hardcoded.
*   `https://supremeai.com/metadata`
*   `https://supremeai.com/acs`

**Solution:** These must be fully dynamic per-tenant or via the global dynamic config store.

### 5. Email & Marketing Deep Links
In `email_service.py` and `viral_referral_engine.py`:
*   `https://api.resend.com/emails`
*   `https://supremeai.com` (Base URL for sharing)

---

## 🎯 Next Steps

I have added these areas to our **Implementation Plan**. When we build the `SystemDynamicConfig` module (Supabase `app_configurations`), we will replace all these hardcoded URLs and timeouts with dynamic getters.

This ensures that if you ever switch domains, change hosting providers, or experience slow APIs, you can update everything globally from the Admin Dashboard in real-time.
