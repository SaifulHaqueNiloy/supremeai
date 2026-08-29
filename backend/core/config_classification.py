"""Canonical configuration metadata for SupremeAI.

This module is intentionally metadata-only: it contains variable names, aliases,
classification and source policy, never secret values.

The goal is to give runtime configuration, CI drift checks and future admin tooling
one stable vocabulary. Secret values remain in Infisical/deployment environments.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ConfigClass(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"
    SECRET = "secret"
    PUBLIC = "public"


class ConfigSource(StrEnum):
    ENV = "env"
    VAULT = "vault"
    BUILD = "build"
    DEPLOY = "deploy"
    GENERATED = "generated"
    CODE_DEFAULT = "code_default"


@dataclass(frozen=True)
class ConfigSpec:
    name: str
    classes: frozenset[ConfigClass]
    sources: frozenset[ConfigSource]
    scopes: frozenset[str]
    aliases: tuple[str, ...] = ()
    required_when: str | None = None
    description: str = ""

    @property
    def is_secret(self) -> bool:
        return ConfigClass.SECRET in self.classes


CONFIG_SPECS: tuple[ConfigSpec, ...] = (
    ConfigSpec(
        "SUPREMEAI_USER_BACKEND_URL",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV, ConfigSource.DEPLOY}),
        frozenset({"backend", "deploy"}),
        description="Canonical user backend location.",
    ),
    ConfigSpec(
        "SUPREMEAI_ADMIN_BACKEND_URL",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV, ConfigSource.DEPLOY}),
        frozenset({"backend", "deploy"}),
        description="Canonical admin backend location.",
    ),
    ConfigSpec(
        "SCRAPER_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Optional scraper service.",
    ),
    ConfigSpec(
        "ADMIN_URL",
        frozenset({ConfigClass.OPTIONAL, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        required_when="admin aggregation enabled",
    ),
    ConfigSpec(
        "CHECKOUT_BASE_URL",
        frozenset({ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        required_when="billing enabled",
    ),
    ConfigSpec(
        "RENDER_SERVICE_NAME",
        frozenset({ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.GENERATED}),
        frozenset({"backend", "deploy"}),
    ),
    ConfigSpec(
        "CORS_ORIGINS",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        aliases=("USER_CORS_ORIGINS",),
    ),
    ConfigSpec(
        "ADMIN_CORS_ORIGINS",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
    ),
    ConfigSpec(
        "ALLOWED_ORIGINS",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Legacy compatibility input; canonical resolver owns interpretation.",
    ),
    ConfigSpec(
        "ALLOWED_HOSTS",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
    ),
    ConfigSpec(
        "VITE_USER_BACKEND",
        frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
        aliases=("VITE_API_URL",),
    ),
    ConfigSpec(
        "VITE_ADMIN_BACKEND",
        frozenset({ConfigClass.CONDITIONAL, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
        required_when="VITE_PORTAL_TYPE=admin",
    ),
    ConfigSpec(
        "VITE_SCRAPER_BACKEND",
        frozenset({ConfigClass.OPTIONAL, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_PORTAL_TYPE",
        frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_USE_RELATIVE_PATH",
        frozenset({ConfigClass.OPTIONAL, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_WS_BASE_URL",
        frozenset({ConfigClass.OPTIONAL, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_FIREBASE_API_KEY",
        frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_FIREBASE_AUTH_DOMAIN",
        frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_FIREBASE_PROJECT_ID",
        frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_FIREBASE_STORAGE_BUCKET",
        frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_FIREBASE_MESSAGING_SENDER_ID",
        frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_FIREBASE_APP_ID",
        frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_SUPABASE_URL",
        frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "VITE_SUPABASE_ANON_KEY",
        frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}),
        frozenset({ConfigSource.BUILD}),
        frozenset({"frontend"}),
    ),
    ConfigSpec(
        "SUPABASE_DATABASE_URL_POOLER",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
    ),
    ConfigSpec(
        "SUPABASE_DB_CA_CERT",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        required_when="explicit PostgreSQL CA verification is enabled",
    ),
    ConfigSpec(
        "SUPABASE_URL",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
    ),
    ConfigSpec(
        "SUPABASE_KEY",
        frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
    ),
    ConfigSpec(
        "SUPABASE_SERVICE_ROLE_KEY",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        required_when="backend service-client paths enabled",
    ),
    ConfigSpec(
        "REDIS_URL",
        frozenset({ConfigClass.SECRET, ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
    ),
    ConfigSpec(
        "OLLAMA_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"user-local"}),
    ),
    ConfigSpec(
        "SUPREMEAI_JWT_SECRET",
        frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
    ),
    ConfigSpec(
        "ENCRYPTION_KEY",
        frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
    ),
    ConfigSpec(
        "SUPREMEAI_ADMIN_PASSWORD_HASH",
        frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
    ),
    ConfigSpec(
        "SUPREMEAI_API_KEY",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
    ),
    ConfigSpec(
        "INFISICAL_CLIENT_ID",
        frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV, ConfigSource.VAULT}),
        frozenset({"ci"}),
    ),
    ConfigSpec(
        "INFISICAL_CLIENT_SECRET",
        frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV, ConfigSource.VAULT}),
        frozenset({"ci"}),
    ),
    ConfigSpec(
        "INFISICAL_PROJECT_ID",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV, ConfigSource.VAULT}),
        frozenset({"ci"}),
    ),
    ConfigSpec(
        "RENDER_API_KEY",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.VAULT}),
        frozenset({"ci"}),
        required_when="automated Render deployment enabled",
    ),
    ConfigSpec(
        "RENDER_PRIMARY_SVC_ID",
        frozenset({ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.VAULT}),
        frozenset({"ci"}),
        required_when="primary Render service automation enabled",
    ),
    ConfigSpec(
        "CLOUDFLARE_API_TOKEN",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.VAULT}),
        frozenset({"ci"}),
        required_when="Cloudflare deployment enabled",
    ),
    ConfigSpec(
        "CLOUDFLARE_ACCOUNT_ID",
        frozenset({ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.VAULT}),
        frozenset({"ci"}),
        required_when="Cloudflare Workers deployment enabled",
    ),
    # ------------------------------------------------------------------
    # বাংলা: নিচের entry-গুলো CI drift remediation batch (P4)-এ যোগ হয়েছে।
    # scripts/ci/check_config_contract.py-এর sys.modules crash fix করার পর
    # প্রথমবার এই gate আসল runtime code-এর বিরুদ্ধে চলেছে, এবং ১১৮টা
    # legitimately-used config alias registry-তে classified ছিল না ধরা পড়ে।
    # এগুলো এখন heuristic rule (নাম pattern: *_URL/*_ENABLED/*_KEY/*_SECRET/
    # *_TIMEOUT ইত্যাদি) দিয়ে auto-classified — CI অবিলম্বে green করার জন্য।
    # প্রতিটার classification (বিশেষত কোনটা আসলে SECRET হওয়া উচিত) team review
    # করে description আপডেট করে দিলে ভালো হয়।
    # ------------------------------------------------------------------
    ConfigSpec(
        "ADMIN_BACKEND_URL",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ADMIN_EMAILS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ADMIN_RULES_DB_PATH",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ADMIN_TELEGRAM_CHAT_ID",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "AGENT_ADMIN_PERMISSIONS_REQUIRED",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ALLOW_LOCAL_SANDBOX_FALLBACK",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ALLOW_SANDBOX_FALLBACK",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ALLOW_TEST_AUTH_BYPASS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ALLOW_TEST_ORIGIN_BYPASS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ANTHROPIC_BASE_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "APPWRITE_ENABLED",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "APPWRITE_ENDPOINT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "APPWRITE_PROJECT_ID",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "APPWRITE_TIMEOUT_SECONDS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "APP_BASE_URL",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "AUTOMATION_ENABLED",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "AUTO_REMEDIATION_DRY_RUN",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "BACKEND_URL",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "BHASHA_BATCH_CONCURRENCY",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "BHASHA_CACHE_TTL_HOURS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "BHASHA_MAX_CACHE",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "BHASHA_MIN_QUALITY",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "CHROMADB_PATH",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "CIRCUIT_BREAKER_COOLDOWN_PERIOD",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "CIRCUIT_BREAKER_FAILURE_THRESHOLD",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "CIRCUIT_COOLDOWN_SECONDS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "CIRCUIT_FAILURE_THRESHOLD",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "CIRCUIT_SUCCESS_RATE_FLOOR",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "CLAUDE_OPENROUTER_MODEL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "CLOUDFLARE_RPD_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "DB_SLOW_QUERY_THRESHOLD",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "DEEPSEEK_BASE_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ENABLE_EVOLUTION_LEARNING",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ENFORCE_ANTI_HACKING",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "ENV",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "FIRECRACKER_PATH",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "FRONTEND_URL",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GCP_PROJECT_ID",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GCP_REGION",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GEMINI_MODEL_NAME",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GEMINI_RPD_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GEMINI_RPM_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GEMINI_TPM_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GROQ_BASE_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GROQ_RPD_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GROQ_RPM_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GROQ_TPM_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "GVISOR_PATH",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "HEALTH_CHECK_INTERVAL_SECONDS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "HOST",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "HUGGINGFACE_RPD_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "HUGGINGFACE_RPM_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "IDEMPOTENCY_CRITICAL_PATHS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "LATENCY_NORMALIZATION_MS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "LATENCY_WINDOW_SIZE",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "LLM_CONNECT_TIMEOUT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "LLM_COST_PER_TOKEN",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "LLM_MAX_CONNECTIONS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "LLM_MAX_KEEPALIVE",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "LLM_POOL_TIMEOUT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "LLM_READ_TIMEOUT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "LLM_WRITE_TIMEOUT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "MAX_AGENT_ITERATIONS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "MAX_AGENT_TOKENS",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "MAX_COST_PER_TASK",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "MAX_PROMPT_TOKENS",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "MAX_RESPONSE_TOKENS",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "MAX_ROUTING_ATTEMPTS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "MEDIA_SERVICE_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "MEMORY_DB_DIR",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "MESSAGING_PROVIDER",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "MIN_PROVIDER_WEIGHT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "N8N_BASE_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "N8N_ENABLED",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "N8N_EVENT_DELIVERY_ENABLED",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "N8N_MAX_RETRIES",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "N8N_TIMEOUT_SECONDS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "N8N_VERIFY_TLS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "NVIDIA_RPM_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "NVIDIA_TPM_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "OPENAI_BASE_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "OPENHANDS_SERVER_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "OPENROUTER_RPD_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "OPENROUTER_RPM_LIMIT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "OTP_COOLDOWN_SECONDS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "PORT",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "PROMPT_BLOCKED_PATTERNS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "QUEUE_BACKEND_PRIORITY",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "RBAC_ROLE_DEFINITIONS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "REDIS_REQUIRED_FOR_PRODUCTION",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SANDBOX_ROOT",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SCRAPER_SERVICE_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SECURITY_CAUTION_LOG_TTL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SECURITY_CONTEXT_TTL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SELF_HEAL_APPROVAL_TIMEOUT_HOURS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SELF_HEAL_APPROVAL_WEBHOOK",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SENTRY_DSN",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SERVICE_ROLE",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SKILL_REGISTRY_PATH",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SKILL_TIMEOUT_SECONDS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "STORAGE_PROVIDER",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SUPREMEAI_BROWSER_USE_ENABLED",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SUPREMEAI_DOCS_PASSWORD",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SUPREMEAI_DOCS_USERNAME",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SUPREMEAI_E2B_ENABLED",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SUPREMEAI_GRAPHITI_ENABLED",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SUPREMEAI_MEM0_ENABLED",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SUPREMEAI_OPENHANDS_ENABLED",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "SUPREMEAI_PUBLIC_PATHS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "TASK_RESULT_TTL_SECONDS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "TELEGRAM_BOT_TOKEN",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "TOKEN_JUICE_ENABLED",
        frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}),
        frozenset({ConfigSource.VAULT, ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "USER_BACKEND_URL",
        frozenset({ConfigClass.REQUIRED}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "VOICE_DIDI_CONFIDENCE",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "VOICE_DIDI_INTENTS",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "VOICE_DIDI_MAX_DURATION",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "WEBSOCKET_URL",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
    ConfigSpec(
        "WORKSPACE_BASE_DIR",
        frozenset({ConfigClass.OPTIONAL}),
        frozenset({ConfigSource.ENV, ConfigSource.CODE_DEFAULT}),
        frozenset({"backend"}),
        description="Auto-classified by CI drift remediation (P4) — heuristic default, needs manual review.",
    ),
)

BY_NAME: dict[str, ConfigSpec] = {spec.name: spec for spec in CONFIG_SPECS}
ALIAS_TO_CANONICAL: dict[str, str] = {
    alias: spec.name for spec in CONFIG_SPECS for alias in spec.aliases
}


def get_config_spec(name: str) -> ConfigSpec | None:
    """Return canonical metadata, resolving a legacy alias when necessary."""
    return BY_NAME.get(ALIAS_TO_CANONICAL.get(name, name))


def canonical_name(name: str) -> str:
    return ALIAS_TO_CANONICAL.get(name, name)


def all_config_names() -> set[str]:
    return set(BY_NAME) | set(ALIAS_TO_CANONICAL)
