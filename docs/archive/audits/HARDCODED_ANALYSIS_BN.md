# 🔍 SupremeAI Hardcoded Data Analysis Report
## বাংলা: হার্ডকোডেড ডাটা বিশ্লেষণ এবং Dynamic Configuration রিকমেন্ডেশন

---

## 📋 সারসংক্ষেপ (Executive Summary)

আমি আপনার **SupremeAI** GitHub repository গভীরভাবে অ্যানালাইস করেছি। নিচে **সব hardcoded values** এবং সেগুলোকে **dynamic/env-driven** করার উপায় বাংলায় ব্যাখ্যা করা হলো।

---

## 🚨 CRITICAL: 3rd Party URLs - যেগুলো পরিবর্তনে কোড পরিবর্তন লাগবে

### 1. **Render Backend URL (সবচেয়ে গুরুত্বপূর্ণ)**

| ফাইল | Hardcoded Value | সমস্যা |
|------|-----------------|---------|
| `frontend/vite.config.ts` | `https://supremeai-backend-docker.onrender.com` | Render deploy URL পরিবর্তনে কোড edit লাগবে |
| `frontend/src/utils/api.ts` | `https://supremeai-backend-docker.onrender.com` | Same issue |
| `render.yaml` | `https://supremeai-backend-docker.onrender.com` | Environment variable থাকা সত্ত্বেও hardcoded |

#### 🛠️ সমাধান (Fix):

```typescript
// ❌ বর্তমান (frontend/vite.config.ts)
const ADMIN_BACKEND = process.env.VITE_ADMIN_BACKEND || 'https://supremeai-backend-docker.onrender.com'
const USER_BACKEND = process.env.VITE_USER_BACKEND || process.env.VITE_API_URL || 'https://supremeai-backend-docker.onrender.com'

// ✅ সঠিক (Fully Dynamic)
const ADMIN_BACKEND = process.env.VITE_ADMIN_BACKEND || process.env.RENDER_SERVICE_URL || ''
const USER_BACKEND = process.env.VITE_USER_BACKEND || process.env.VITE_API_URL || process.env.RENDER_SERVICE_URL || ''

// ⚠️ Production-এ missing env = build error (Fail-Fast)
if (!ADMIN_BACKEND && process.env.NODE_ENV === 'production') {
  throw new Error('❌ VITE_ADMIN_BACKEND environment variable is required in production!')
}
```

```yaml
# ❌ বর্তমান (render.yaml)
envVars:
  - key: VITE_ADMIN_BACKEND
    value: "https://supremeai-backend-docker.onrender.com"  # HARDCODED!

# ✅ সঠিক - Render Auto URL Injection
envVars:
  - key: VITE_ADMIN_BACKEND
    value: "https://${RENDER_SERVICE_NAME}.onrender.com"
  # অথবা Render-এর built-in variable use করো:
  # value: https://$RENDER_EXTERNAL_HOSTNAME
```

---

### 2. **Firebase Hosting Rewrites (firebase.json)**

```json
// ❌ বর্তমান - Backend URL hardcoded
{
  "source": "/admin-api/**",
  "destination": "https://supremeai-backend-docker.onrender.com/admin-api/**"
}

// ✅ সঠিক - Firebase Runtime Config ব্যবহার
// firebase.json rewrites support করে না dynamically,
// তাই **build time replace** করতে হবে:
{
  "source": "/admin-api/**",
  "destination": "{{BACKEND_URL}}/admin-api/**"
}
// scripts/render_build_frontend.sh এ sed command দিয়ে replace:
// sed -i "s|{{BACKEND_URL}}|$VITE_ADMIN_BACKEND|g" dist-admin/firebase.json
```

---

### 3. **CORS Origins Default Values**

| ফাইল | Hardcoded Origins |
|------|-------------------|
| `backend/core/config_fields.py` | `https://supremeai-lac.vercel.app`, `https://supremeai-a.web.app`, etc. |
| `.env.example` | Full list of deployment URLs |

#### 🛠️ সমাধান:

```python
# ❌ বর্তমান (config_fields.py)
user_cors_origins: str | list[str] = Field(
    default=["https://supremeai-lac.vercel.app", "https://supremeai-a.firebaseapp.com", ...],
    validation_alias="USER_CORS_ORIGINS",
)

# ✅ সঠিক - Empty default + Fail-Fast validation
user_cors_origins: str | list[str] = Field(
    default=[],  # No default - must be explicitly set!
    validation_alias="USER_CORS_ORIGINS",
)

# config_validation.py-এ add করো:
@model_validator(mode="after")
def validate_cors_origins(self):
    if self.env == "production" and not self.user_cors_origins:
        raise ValueError("USER_CORS_ORIGINS is REQUIRED in production. Set it in Render dashboard.")
    return self
```

---

## ⚠️ HIGH: Port Numbers & Service Configuration

### 4. **Scraper Port Mismatch**

| ফাইল | Value | Issue |
|------|-------|-------|
| `backend/services/scraper/main.py` | `8081` (default) | Dockerfile EXPOSE 8080 |
| `render.yaml` | `8081` | Should match Dockerfile |

#### 🛠️ সমাধান:

```python
# ❌ বর্তমান (scraper/main.py)
port = int(os.getenv("PORT", "8081"))  # Wrong default!

# ✅ সঠিক - Dockerfile EXPOSE 8080 এর সাথে match
port = int(os.getenv("PORT", "8080"))
```

```yaml
# render.yaml-ও update করো:
envVars:
  - key: PORT
    value: "8080"  # 8081 → 8080 fix
```

---

### 5. **Browser Viewport & Timeout Constants**

| ফাইল | Hardcoded Value | উদ্দেশ্য |
|------|-----------------|-----------|
| `browser_agent.py` | `viewport: {"width": 1280, "height": 1080}` | Browser size |
| `web_scraper.py` | `timeout=15.0` | HTTP timeout |
| `browser_agent.py` | `timeout=30000` | Playwright timeout |
| `browser_agent.py` | `timeout=10000` | Selector wait |

#### 🛠️ সমাধান:

```python
# ✅ browser_agent.py - Environment-driven config
class BrowserAgent:
    def __init__(self, headless: bool = True):
        self._semaphore = asyncio.Semaphore(_max)
        self.viewport_width = int(os.getenv("BROWSER_VIEWPORT_WIDTH", "1280"))
        self.viewport_height = int(os.getenv("BROWSER_VIEWPORT_HEIGHT", "1080"))
        self.page_timeout = int(os.getenv("BROWSER_PAGE_TIMEOUT_MS", "30000"))
        self.selector_timeout = int(os.getenv("BROWSER_SELECTOR_TIMEOUT_MS", "10000"))

# Context creation:
context = await browser.new_context(
    viewport={"width": self.viewport_width, "height": self.viewport_height},
    user_agent=os.getenv("BROWSER_USER_AGENT", "Mozilla/5.0 ..."),
)
```

---

## 📊 MEDIUM: LLM Provider Rate Limits

### 6. **Rate Limit Thresholds (config_fields.py)**

```python
# ❌ বর্তমান - All hardcoded limits
gemini_rpm_limit: int = Field(default=9, ...)        # Google might change this!
groq_rpm_limit: int = Field(default=28, ...)
openrouter_rpm_limit: int = Field(default=19, ...)
nvidia_rpm_limit: int = Field(default=38, ...)
huggingface_rpm_limit: int = Field(default=18, ...)
```

#### 🛠️ সমাধান:

```python
# ✅ Option A: Fetch from provider API at startup (Recommended for enterprise)
class LLMRateLimitFetcher:
    """Fetches current rate limits from LLM provider APIs."""
    
    GEMINI_DOCS_URL = "https://ai.google.dev/gemini-api/docs/rate-limits"
    
    @staticmethod
    async def fetch_gemini_limits(api_key: str) -> dict:
        # Parse from API response or cache
        pass
    
# ✅ Option B: Environment override with documentation
gemini_rpm_limit: int = Field(
    default=9,
    validation_alias="GEMINI_RPM_LIMIT",
    description="See: https://ai.google.dev/gemini-api/docs/rate-limits"
)
```

---

## 🔒 SECURITY: Headers & Security Settings

### 7. **COOP/COEP Headers (Cross-Origin Policies)**

| ফাইল | Current Value | Risk |
|------|---------------|------|
| `frontend/vite.config.ts` | `require-corp` / `same-origin` | Blocks cross-origin resources |
| `firebase.json` | `require-corp` / `same-origin` | Same issue |
| `render.yaml` | `require-corp` / `same-origin` | Same issue |

#### 🛠️ সমাধান:

```typescript
// ✅ vite.config.ts - Env-driven headers
const coopHeader = process.env.COOP_HEADER || 'cross-origin'  // Less restrictive
const coepHeader = process.env.COEP_HEADER || 'unsafe-none'   // Allow embedding

server: {
  headers: {
    'Cross-Origin-Embedder-Policy': coopHeader,
    'Cross-Origin-Opener-Policy': coepHeader,
  },
}
```

---

### 8. **User-Agent Strings**

```python
# ❌ বর্তমান - Multiple places hardcoded
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
# web_scraper.py
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
# browser_agent.py

# ✅ সঠিক - Single source of truth
DEFAULT_USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
```

---

## 🌐 LOW: Domain/URL Patterns

### 9. **Firebase Hosting Detection (api.ts)**

```typescript
// ❌ Hardcoded domain check
if (hostname.includes('vercel.app')) {
  return '';
}

// ✅ Dynamic detection via env
const RELATIVE_PATH_HOSTS = (import.meta.env.RELATIVE_PATH_HOSTS || 'vercel.app,localhost').split(',')
if (RELATIVE_PATH_HOSTS.some(h => hostname.includes(h))) {
  return '';
}
```

---

### 10. **Allowed Hosts Default (config_fields.py)**

```python
# ❌ বর্তমান
allowed_hosts: str | list[str] = Field(
    default=["onrender.com", "web.app", "firebaseapp.com", "vercel.app", ...],
)

# ✅ সঠিক
allowed_hosts: str | list[str] = Field(
    default=[],  # Must be explicit in production
)
```

---

## 📝 Complete Fix Summary Table

| Priority | Location | Hardcoded Item | Dynamic Solution |
|----------|----------|----------------|------------------|
| 🚨 CRITICAL | `vite.config.ts` | Render backend URL | `VITE_ADMIN_BACKEND` env required |
| 🚨 CRITICAL | `api.ts` | Render backend URL | Same as above |
| 🚨 CRITICAL | `firebase.json` | Backend rewrite URL | Build-time sed replace |
| 🚨 CRITICAL | `render.yaml` | VITE_* backend URLs | Use `${RENDER_*}` vars |
| ⚠️ HIGH | `scraper/main.py` | Port 8081 | Change to 8080 |
| ⚠️ HIGH | `browser_agent.py` | Viewport 1280x1080 | Env vars |
| ⚠️ HIGH | `web_scraper.py` | Timeout 15s | Env var |
| ⚠️ HIGH | `config_fields.py` | CORS defaults | Empty + validate |
| 📊 MEDIUM | `config_fields.py` | LLM rate limits | Document + env override |
| 🔒 SECURITY | `vite.config.ts` | COOP/COEP headers | Env-driven |
| 🔒 SECURITY | Multiple files | User-Agent string | Single env var |
| 🌐 LOW | `api.ts` | vercel.app check | Env-driven list |

---

## 🚀 Implementation Action Plan

### Phase 1: Immediate Fixes (Critical)
1. **Create `env_config.ts`** - Frontend central config loader
2. **Update `render.yaml`** - Remove all hardcoded URLs
3. **Fix `scraper/main.py`** - Port 8081 → 8080
4. **Add build script** - Replace `{{PLACEHOLDERS}}` in firebase.json

### Phase 2: Security Improvements
5. **COOP/COEP headers** - Make configurable per environment
6. **CORS origins** - Empty defaults + production validation
7. **User-Agent** - Single source of truth

### Phase 3: Operational Flexibility
8. **Browser timeouts** - All env-driven
9. **LLM rate limits** - Documentation + env file example
10. **Allowed hosts** - Explicit configuration required

---

## 💡 Key Insight (মূল উপদেশ)

> **"যেকোনো 3rd Party URL, Port, Domain, API Key, Rate Limit - সবকিছু Environment Variable হওয়া উচিত। 
> Code-এ শুধু `os.getenv()` বা `process.env.*` থাকবে - কোনো fallback default value থাকবে না (Production-এ)."**

এটি করলে:
- ✅ Render/Vercel/Firebase পরিবর্তন করলে কোড change লাগবে না
- ✅ New environment add করা সহজ হবে
- ✅ Multi-region deployment সম্ভব হবে
- ✅ Security audit সহজ হবে

---

*Report Generated: $(date)*  
*Analyzer: SupremeAI Code Review Agent*
