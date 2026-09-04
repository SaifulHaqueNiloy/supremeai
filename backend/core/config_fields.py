"""Pydantic field declarations for SupremeAI settings."""

from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import NoDecode


class SettingsFieldsMixin:
    PROJECT_NAME: str = "SupremeAI 2.0"
    API_V1_STR: str = "/api/v1"
    app_name: str = "SupremeAI 2.0"

    # ── LLM Gateway & Streaming Configuration ────────────────────────────────
    LLM_CONNECT_TIMEOUT: float = Field(default=5.0, validation_alias="LLM_CONNECT_TIMEOUT")
    LLM_READ_TIMEOUT: float = Field(default=30.0, validation_alias="LLM_READ_TIMEOUT")
    LLM_WRITE_TIMEOUT: float = Field(default=5.0, validation_alias="LLM_WRITE_TIMEOUT")
    LLM_POOL_TIMEOUT: float = Field(default=5.0, validation_alias="LLM_POOL_TIMEOUT")
    LLM_MAX_CONNECTIONS: int = Field(default=100, validation_alias="LLM_MAX_CONNECTIONS")
    LLM_MAX_KEEPALIVE: int = Field(default=20, validation_alias="LLM_MAX_KEEPALIVE")

    LATENCY_WINDOW_SIZE: int = Field(default=20, validation_alias="LATENCY_WINDOW_SIZE")
    LATENCY_NORMALIZATION_MS: float = Field(
        default=1000.0, validation_alias="LATENCY_NORMALIZATION_MS"
    )
    MIN_PROVIDER_WEIGHT: float = Field(default=0.01, validation_alias="MIN_PROVIDER_WEIGHT")
    CIRCUIT_FAILURE_THRESHOLD: int = Field(default=5, validation_alias="CIRCUIT_FAILURE_THRESHOLD")
    CIRCUIT_SUCCESS_RATE_FLOOR: float = Field(
        default=0.5, validation_alias="CIRCUIT_SUCCESS_RATE_FLOOR"
    )
    CIRCUIT_COOLDOWN_SECONDS: float = Field(
        default=30.0, validation_alias="CIRCUIT_COOLDOWN_SECONDS"
    )
    MAX_ROUTING_ATTEMPTS: int = Field(default=3, validation_alias="MAX_ROUTING_ATTEMPTS")
    docs_auth_enabled: bool = True
    docs_username: str = Field(default="admin", validation_alias="SUPREMEAI_DOCS_USERNAME")
    docs_password: SecretStr = Field(
        default=SecretStr("dev_password_only"),
        validation_alias="SUPREMEAI_DOCS_PASSWORD",
    )

    # ── নেটওয়ার্ক কনফিগ — সব env-driven, কোনো hardcode নেই ────────────────
    port: int = Field(
        default=8080, validation_alias="PORT"
    )  # বাংলা: Dockerfile CMD-এর ${PORT:-8080} default-এর সাথে consistent
    host: str = Field(default="0.0.0.0", validation_alias="HOST")

    # ── Canonical Portal Endpoints ──────────────────────────────────────────
    frontend_url: str = Field(default="", validation_alias="FRONTEND_URL")
    admin_url: str = Field(default="", validation_alias="ADMIN_URL")
    backend_url: str = Field(default="", validation_alias="BACKEND_URL")
    app_base_url: str = Field(default="", validation_alias="APP_BASE_URL")

    @property
    def frontend_base_url(self) -> str:
        """Compatibility property for routes using frontend_base_url."""
        return self.frontend_url or "http://localhost:3000"

    # CORS origins is implemented as a dynamic @property on SettingsSecretsMixin
    # (see config_secrets.py). It must NOT be redeclared as a static Field here —
    # a static Field on this mixin would shadow the property in the MRO and
    # silently disable env-driven CORS validation (incl. STRICT_CORS_TEST bypass).

    user_cors_origins: str | list[str] = Field(
        default=[],  # 🔧 CHANGED: No hardcoded domains! Set USER_CORS_ORIGINS in env.
        validation_alias="USER_CORS_ORIGINS",
    )
    admin_cors_origins: str | list[str] = Field(
        default=[],  # 🔧 CHANGED: No hardcoded domains! Set ADMIN_CORS_ORIGINS in env.
        validation_alias="ADMIN_CORS_ORIGINS",
    )
    enforce_anti_hacking: bool = Field(
        default=False,
        validation_alias="ENFORCE_ANTI_HACKING",
    )

    # বাংলা মন্তব্য: main.py-এর app_user/app_admin bootstrap-এর সাথে সামঞ্জস্যপূর্ণ একই SERVICE_ROLE flag।
    # DB pool sizing (database/session.py) এই মানের উপর ভিত্তি করে User vs Admin instance-এ আলাদা limit প্রয়োগ করে।
    service_role: str = Field(default="user", validation_alias="SERVICE_ROLE")

    # ── Open-Source Integrations Flags (backend/integrations/) ─────────────────
    # প্রতিটি upstream (mem0, Graphiti, browser-use, E2B) optional dependency;
    # flag false বা dependency absent থাকলে সিস্টেম zero-cost fallback দিয়ে চলে।
    mem0_enabled: bool = Field(default=False, validation_alias="SUPREMEAI_MEM0_ENABLED")
    graphiti_enabled: bool = Field(default=False, validation_alias="SUPREMEAI_GRAPHITI_ENABLED")
    browser_use_enabled: bool = Field(
        default=False, validation_alias="SUPREMEAI_BROWSER_USE_ENABLED"
    )
    e2b_enabled: bool = Field(default=False, validation_alias="SUPREMEAI_E2B_ENABLED")
    openhands_enabled: bool = Field(default=False, validation_alias="SUPREMEAI_OPENHANDS_ENABLED")
    openhands_server_url: str = Field(default="", validation_alias="OPENHANDS_SERVER_URL")

    # বাংলা মন্তব্য: JIT OTP over-saturation protection — প্রতি admin প্রতি এই সেকেন্ডে সর্বোচ্চ ১টি OTP।
    otp_cooldown_seconds: int = Field(default=60, validation_alias="OTP_COOLDOWN_SECONDS")

    # বাংলা মন্তব্য: Admin email list সম্পূর্ণ env-driven
    # (Moved to Security & Auth Config section to avoid duplication)

    # বাংলা মন্তব্য: Zero-Trust Host Validation — empty = crash
    # 🔧 DYNAMIC: Empty default — must be explicitly configured
    allowed_hosts: str | list[str] = Field(
        default=[],  # 🔧 CHANGED: No hardcoded hosts! Set ALLOWED_HOSTS in env.
        validation_alias="ALLOWED_HOSTS",
    )

    # ── Stripe, JWT & Encryption credentials — moved to Infisical-backed lazy properties ──

    # ── LLM rate limit thresholds — সব env-driven, hardcode নেই ─────────────
    # 🔧 NOTE: These defaults are provider-specific limits that may change.
    # Always check: https://ai.google.dev/gemini-api/docs/rate-limits
    # Override these via environment variables when providers update their limits.
    gemini_rpm_limit: int = Field(default=9, validation_alias="GEMINI_RPM_LIMIT")
    gemini_tpm_limit: int = Field(default=240_000, validation_alias="GEMINI_TPM_LIMIT")
    gemini_rpd_limit: int = Field(default=475, validation_alias="GEMINI_RPD_LIMIT")
    groq_rpm_limit: int = Field(default=28, validation_alias="GROQ_RPM_LIMIT")
    groq_tpm_limit: int = Field(default=28_500, validation_alias="GROQ_TPM_LIMIT")
    groq_rpd_limit: int = Field(default=13_680, validation_alias="GROQ_RPD_LIMIT")
    openrouter_rpm_limit: int = Field(default=19, validation_alias="OPENROUTER_RPM_LIMIT")
    openrouter_rpd_limit: int = Field(default=45, validation_alias="OPENROUTER_RPD_LIMIT")
    cloudflare_rpd_limit: int = Field(default=9_000, validation_alias="CLOUDFLARE_RPD_LIMIT")
    nvidia_rpm_limit: int = Field(default=38, validation_alias="NVIDIA_RPM_LIMIT")
    nvidia_tpm_limit: int = Field(default=38_000, validation_alias="NVIDIA_TPM_LIMIT")
    huggingface_rpm_limit: int = Field(default=18, validation_alias="HUGGINGFACE_RPM_LIMIT")
    huggingface_rpd_limit: int = Field(default=950, validation_alias="HUGGINGFACE_RPD_LIMIT")

    max_prompt_tokens: int = Field(default=4_000, validation_alias="MAX_PROMPT_TOKENS")
    max_response_tokens: int = Field(default=1_500, validation_alias="MAX_RESPONSE_TOKENS")
    max_cost_per_task: float = Field(default=0.01, validation_alias="MAX_COST_PER_TASK")
    enable_token_compression: bool = True

    # ── Security & Auth Config ──────────────────────────────────────────────
    security_context_ttl: int = Field(default=86400, validation_alias="SECURITY_CONTEXT_TTL")
    security_caution_log_ttl: int = Field(
        default=86400, validation_alias="SECURITY_CAUTION_LOG_TTL"
    )
    admin_emails: str | list[str] = Field(default_factory=list, validation_alias="ADMIN_EMAILS")

    supremeai_public_paths: str | list[str] = Field(
        default=[
            "/",
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/token",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            # Audit fix (this session): /auth/refresh authenticates via the
            # refresh-token JWT carried in the JSON body (type=refresh enforced,
            # fail-closed inside the endpoint). It must NOT be gated by the
            # access-token middleware — otherwise token refresh is unreachable
            # (always 401) and clients can never renew sessions.
            "/api/v1/auth/refresh",
            "/actuator",
            "/api/admin/firebase-auth",
            "/api/admin/firebase-login",
            "/api/admin/firebase-totp-setup",
            "/api/admin/firebase-totp-verify",
            "/api/v1/health",
            "/api/v1/health/",
            "/api/v1/live",
            "/api/v1/ready",
            "/api/voice/stream_audio",
            "/api/billing/webhook/stripe",
            "/api/billing/webhook/sslcommerz",
            # AUD-2.1: "/api/v1/markdown" removed from public paths — the markdown
            # export/search surface now requires authentication (router-level guard).
            "/api/config/public",
            # বাংলা মন্তব্য (ROOT-CAUSE FIX): "/api/task/stream" ও
            # "/api/preferences/default/stream" আগে এখানে (public paths) ছিল,
            # অথচ দুটো রুটই router/route-level dependencies=[Depends(get_current_user_token)]
            # দিয়ে auth বাধ্যতামূলক করে। AuthMiddleware public path হলে JWT decode করে
            # request.state.user সেট করে না — ফলে get_current_user_token সবসময় "Missing or
            # invalid authentication token" ধরে 401 দিত, ভ্যালিড Bearer token পাঠানো সত্ত্বেও।
            # এটাই ছিল TOTP verify সফল হওয়ার পরপরই dashboard-এ SSE স্ট্রিম ও থিম sync
            # 401 দিয়ে fail হওয়ার আসল কারণ। এখন middleware এই দুটো পাথেও টোকেন decode করে
            # request.state.user সেট করবে, তাই ডাউনস্ট্রিম dependency ঠিকভাবে token পাবে।
        ],
        validation_alias="SUPREMEAI_PUBLIC_PATHS",
    )

    prompt_blocked_patterns: str | list[str] = Field(
        default=["system prompt", "ignore all previous", "you are an administrative"],
        validation_alias="PROMPT_BLOCKED_PATTERNS",
    )
    rbac_role_definitions: Annotated[dict[str, list[str]], NoDecode] = Field(
        default_factory=lambda: {
            "admin": ["*"],
            "user": ["read", "write"],
            "guest": ["read"],
        },
        validation_alias="RBAC_ROLE_DEFINITIONS",
    )

    # ── Circuit Breaker Config ───────────────────────────────────────────────
    circuit_breaker_failure_threshold: int = Field(
        default=3, validation_alias="CIRCUIT_BREAKER_FAILURE_THRESHOLD"
    )
    circuit_breaker_cooldown_period: int = Field(
        default=60, validation_alias="CIRCUIT_BREAKER_COOLDOWN_PERIOD"
    )

    # ── Idempotency Config ───────────────────────────────────────────────
    # বাংলা মন্তব্য: idempotency_critical_paths সম্পূর্ণ env-driven।
    # IDEMPOTENCY_CRITICAL_PATHS="/api/orchestrate/generate,/api/billing/charge" (comma-separated)
    idempotency_critical_paths: str | list[str] = Field(
        default_factory=list,
        validation_alias="IDEMPOTENCY_CRITICAL_PATHS",
    )

    # ── Provider API Base URLs (Optional Proxies) ─────────────────────────
    openai_base_url: str = Field(default="", validation_alias="OPENAI_BASE_URL")
    deepseek_base_url: str = Field(default="", validation_alias="DEEPSEEK_BASE_URL")
    groq_base_url: str = Field(default="", validation_alias="GROQ_BASE_URL")
    anthropic_base_url: str = Field(default="", validation_alias="ANTHROPIC_BASE_URL")

    # ── Legacy / specific models ──────────────────────────────────────────────
    claude_openrouter_model: str = Field(
        default="anthropic/claude-3.5-haiku:free",
        validation_alias="CLAUDE_OPENROUTER_MODEL",
    )

    # বাংলা মন্তব্য: জেমিনি মডেল নাম সেন্ট্রালাইজড করা হলো যাতে কোনো ইউটিলিটি স্ক্রিপ্টে হার্ডকোড না থাকে।
    gemini_model_name: str = Field(
        default="gemini/gemini-2.0-flash",
        validation_alias="GEMINI_MODEL_NAME",
    )

    sentry_dsn: str = Field(default="", validation_alias="SENTRY_DSN")

    # বাংলা মন্তব্য: OLLAMA_URL — fail-fast, কোনো localhost fallback নেই
    ollama_url: str = Field(default="", validation_alias="OLLAMA_URL")

    gcp_project_id: str = Field(default="", validation_alias="GCP_PROJECT_ID")
    gcp_region: str = Field(default="us-central1", validation_alias="GCP_REGION")

    # বাংলা মন্তব্য: Filesystem paths
    admin_rules_db: str = Field(default="", validation_alias="ADMIN_RULES_DB_PATH")
    memory_db_dir: str = Field(default="", validation_alias="MEMORY_DB_DIR")
    skill_registry_path: str = Field(default="", validation_alias="SKILL_REGISTRY_PATH")
    # বাংলা মন্তব্য: ChromaDB ভেক্টর ডাটাবেসের জন্য কনফিগারেবল পাথ যোগ করা হলো।
    chromadb_path: str = Field(default="supremeai_knowledge_base", validation_alias="CHROMADB_PATH")

    # ── Sandbox config — env-driven ──────────────────────────────────────────
    workspace_base_dir: str = Field(
        default="/tmp/supremeai_workspace",
        validation_alias="WORKSPACE_BASE_DIR",
        description="Base directory for user workspace files (api/routes/files.py)",
    )
    sandbox_root: str = Field(default="/tmp/sandboxes", validation_alias="SANDBOX_ROOT")  # nosec B108
    firecracker_path: str = Field(
        default="/usr/bin/firecracker", validation_alias="FIRECRACKER_PATH"
    )
    gvisor_path: str = Field(default="/usr/bin/runsc", validation_alias="GVISOR_PATH")
    allow_sandbox_fallback: bool = Field(default=False, validation_alias="ALLOW_SANDBOX_FALLBACK")
    # বাংলা মন্তব্য: local_code_executor ও docker_sandbox-এর লোকাল ফলব্যাকের জন্য settings ভেরিয়েবল যোগ করা হলো।
    allow_local_sandbox_fallback: str = Field(
        default="false", validation_alias="ALLOW_LOCAL_SANDBOX_FALLBACK"
    )

    # ── Agent Execution Config — env-driven ─────────────────────────────────
    # বাংলা মন্তব্য: আগে agent_orchestrator.py সরাসরি os.getenv() করত।
    # এখন এই দুটো settings-এর Single Source of Truth থেকে আসে।
    max_agent_tokens: int = Field(default=5000, validation_alias="MAX_AGENT_TOKENS")
    max_agent_iterations: int = Field(default=5, validation_alias="MAX_AGENT_ITERATIONS")
    agent_admin_permissions_required: bool = Field(
        default=True, validation_alias="AGENT_ADMIN_PERMISSIONS_REQUIRED"
    )

    # ── LLM Cost Config — env-driven ────────────────────────────────────────
    # বাংলা মন্তব্য: আগে llm_gateway.py-এ `estimated_cost = tokens * 0.00001` hardcoded ছিল।
    # এখন এই factor settings থেকে নিয়ন্ত্রিত হয় যা runtime-এ override করা যাবে।
    llm_cost_per_token: float = Field(default=0.00001, validation_alias="LLM_COST_PER_TOKEN")

    # ── Task Queue Config — env-driven ──────────────────────────────────────
    # বাংলা মন্তব্য: task_queue_enhanced.py-এ TTL এবং backend priority এখন config-driven।
    task_result_ttl_seconds: int = Field(default=3600, validation_alias="TASK_RESULT_TTL_SECONDS")
    queue_backend_priority: str = Field(
        default="asyncio,redis,celery,pubsub", validation_alias="QUEUE_BACKEND_PRIORITY"
    )

    # ── Health Check Config — env-driven ────────────────────────────────────
    # বাংলা মন্তব্য: health_monitor.py-এ hardcoded interval এখন config-driven।
    health_check_interval_seconds: int = Field(
        default=60, validation_alias="HEALTH_CHECK_INTERVAL_SECONDS"
    )
    skill_timeout_seconds: int = Field(default=30, validation_alias="SKILL_TIMEOUT_SECONDS")
    redis_required_for_production: bool = Field(
        default=False, validation_alias="REDIS_REQUIRED_FOR_PRODUCTION"
    )

    # ── Self-Healing Config — env-driven ────────────────────────────────────
    self_heal_approval_webhook: str = Field(
        default="", validation_alias="SELF_HEAL_APPROVAL_WEBHOOK"
    )
    self_heal_approval_timeout_hours: int = Field(
        default=24, validation_alias="SELF_HEAL_APPROVAL_TIMEOUT_HOURS"
    )
    auto_remediation_dry_run: bool = Field(
        default=True, validation_alias="AUTO_REMEDIATION_DRY_RUN"
    )

    # ── Migrated Runtime Environment Fields ──────────────────────────────────
    db_slow_query_threshold: float = Field(default=0.2, validation_alias="DB_SLOW_QUERY_THRESHOLD")
    token_juice_enabled: bool = Field(default=True, validation_alias="TOKEN_JUICE_ENABLED")
    enable_evolution_learning: bool = Field(
        default=False, validation_alias="ENABLE_EVOLUTION_LEARNING"
    )
    voice_didi_confidence: float = Field(default=0.6, validation_alias="VOICE_DIDI_CONFIDENCE")
    voice_didi_max_duration: int = Field(default=30, validation_alias="VOICE_DIDI_MAX_DURATION")
    voice_didi_intents: str = Field(
        default="search,order,help,price,location,cancel,repeat",
        validation_alias="VOICE_DIDI_INTENTS",
    )
    bhasha_cache_ttl_hours: int = Field(default=24, validation_alias="BHASHA_CACHE_TTL_HOURS")
    bhasha_min_quality: float = Field(default=0.7, validation_alias="BHASHA_MIN_QUALITY")
    bhasha_max_cache: int = Field(default=10000, validation_alias="BHASHA_MAX_CACHE")
    bhasha_batch_concurrency: int = Field(default=5, validation_alias="BHASHA_BATCH_CONCURRENCY")

    # ── Microservices Config — env-driven ─────────────────────────────────────
    # বাংলা মন্তব্য: Scraper microservic-এর লিভ সেনেন, Cloudflare Worker থেকে proxy করে।
    scraper_service_url: str = Field(default="", validation_alias="SCRAPER_SERVICE_URL")
    # Media microservic-এর URL (Cloud Run)
    media_service_url: str = Field(default="", validation_alias="MEDIA_SERVICE_URL")

    # ── Core App Endpoints (Frontend/Backend Canonical Routing) ───────────────
    user_backend_url: str = Field(default="", validation_alias="USER_BACKEND_URL")
    admin_backend_url: str = Field(default="", validation_alias="ADMIN_BACKEND_URL")
    websocket_url: str = Field(default="", validation_alias="WEBSOCKET_URL")

    # ── Telegram Bot & Alerts Config ──────────────────────────────────────────
    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    admin_telegram_chat_id: str = Field(default="", validation_alias="ADMIN_TELEGRAM_CHAT_ID")

    # ── Automation & Vendor Independence Config ───────────────────────────────
    automation_enabled: bool = Field(default=True, validation_alias="AUTOMATION_ENABLED")
    storage_provider: str = Field(default="postgres", validation_alias="STORAGE_PROVIDER")
    messaging_provider: str = Field(default="existing", validation_alias="MESSAGING_PROVIDER")

    # n8n
    n8n_enabled: bool = Field(default=False, validation_alias="N8N_ENABLED")
    n8n_base_url: str = Field(default="", validation_alias="N8N_BASE_URL")
    n8n_timeout_seconds: int = Field(default=15, validation_alias="N8N_TIMEOUT_SECONDS")
    n8n_max_retries: int = Field(default=3, validation_alias="N8N_MAX_RETRIES")
    n8n_verify_tls: bool = Field(default=True, validation_alias="N8N_VERIFY_TLS")
    n8n_event_delivery_enabled: bool = Field(
        default=False, validation_alias="N8N_EVENT_DELIVERY_ENABLED"
    )

    # Appwrite
    appwrite_enabled: bool = Field(default=False, validation_alias="APPWRITE_ENABLED")
    appwrite_endpoint: str = Field(default="", validation_alias="APPWRITE_ENDPOINT")
    appwrite_project_id: str = Field(default="", validation_alias="APPWRITE_PROJECT_ID")
    appwrite_timeout_seconds: int = Field(default=10, validation_alias="APPWRITE_TIMEOUT_SECONDS")

    # ── Missing Config Variables from env check ───────────────────────────────
    resend_from_email: str = Field(
        default="noreply@supremeai.dev", validation_alias="RESEND_FROM_EMAIL"
    )
    retry_budget_max_tokens: int = Field(default=20, validation_alias="RETRY_BUDGET_MAX_TOKENS")
    retry_budget_refill_rate: float = Field(
        default=1.0, validation_alias="RETRY_BUDGET_REFILL_RATE"
    )
    runpod_api_url: str = Field(default="", validation_alias="RUNPOD_API_URL")
    sandbox_payload: str = Field(default="", validation_alias="SANDBOX_PAYLOAD")
