"""Secret loading and lazy-secret behavior for SupremeAI settings."""

import asyncio
import json
import os
import secrets
import sys
from typing import Any

from pydantic import PrivateAttr, SecretStr, model_serializer

from core.logging_config import logger

from .security.secret_vault import get_secret_vault


class SettingsSecretsMixin:
    def _is_test_environment(self) -> bool:
        if os.getenv("ENV", "").lower() in {"production", "staging"}:
            return False
        return (
            "pytest" in sys.modules
            or os.getenv("CI") == "true"
            or os.getenv("GITHUB_ACTIONS") == "true"
        )

    # বাংলা মন্তব্য: Pydantic v2-এ Mixin-এর ভেতরে PrivateAttr ব্যবহার করলে
    # instance-level private attr initialize নাও হতে পারে (ModelPrivateAttr iterable error)।
    # তাই নিরাপদ সমাধান হিসেবে __dict__-এ আলাদা namespace ব্যবহার করা হচ্ছে।
    _cached_secrets: dict[str, str] = PrivateAttr(default_factory=dict)
    _secrets_batch_loaded: bool = PrivateAttr(default=False)

    def _get_private_state(self) -> dict:
        """Mixin-এ নিরাপদ private state access।"""
        if "_cached_secrets" not in self.__dict__:
            self.__dict__["_cached_secrets"] = {}
        if "_secrets_batch_loaded" not in self.__dict__:
            self.__dict__["_secrets_batch_loaded"] = False
        return self.__dict__

    # বাংলা মন্তব্য: ব্যাচ লোডিংয়ের জন্য প্রয়োজনীয় কোর সিক্রেট কীগুলোর তালিকা।
    # startup-এ একবারে শুধু কোর সিক্রেট লোড করা হবে, যাতে মেমরি এবং স্টার্টআপ টাইম কম লাগে।
    # অপশনাল ইন্টিগ্রেশনগুলো (যেমন AI providers, Kaggle) দরকার হলে lazily লোড হবে।
    _CORE_SECRET_KEYS: list[str] = [
        "SUPABASE_DATABASE_URL_POOLER",
        "SUPABASE_DB_CA_CERT",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "REDIS_URL",
        "SUPREMEAI_JWT_SECRET",
        "ENCRYPTION_KEY",
        "SUPREMEAI_ADMIN_PASSWORD_HASH",
        "CI_WEBHOOK_SECRET",
        "SUPREMEAI_API_KEY",
    ]

    def _ensure_secrets_loaded(self) -> None:
        """Batch-load all secrets at once into memory cache.

        বাংলা: startup-এ **একটাই** `listSecrets()` HTTP call দিয়ে সব secrets
        লোড করে। আগের sequential per-secret loop (~30s) থেকে ~1s-এ নামিয়ে আনে।

        V4.2: Bulk-first via `fetch_all_secrets()` → per-key individual fallback।
        """
        state = self._get_private_state()
        if state["_secrets_batch_loaded"]:
            return
        cached = state["_cached_secrets"]

        import time

        _t0 = time.perf_counter()

        # ── STEP 1: Bulk fetch — এক HTTP call-এ সব secrets ─────────────────
        bulk = get_secret_vault().fetch_all_secrets()

        if bulk:
            # সরাসরি bulk dict থেকে map করো — কোনো HTTP call নেই
            for secret_key in self._BATCH_SECRET_KEYS:
                if secret_key in bulk and bulk[secret_key]:
                    cached[secret_key] = bulk[secret_key]

            # JSON blob secrets — bulk result-এ থাকলে parse করো
            _json_blobs = {
                "LLM_PROVIDER_KEYS": {
                    "openai": "OPENAI_API_KEY",
                    "gemini": "GEMINI_API_KEY",
                    "groq": "GROQ_API_KEY",
                    "deepseek": "DEEPSEEK_API_KEY",
                    "nvidia": "NVIDIA_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                    "huggingface": "HF_API_KEY",
                },
                "DATABASE_CONFIG": {
                    "pooler_url": "SUPABASE_DATABASE_URL_POOLER",
                    "supabase_url": "SUPABASE_URL",
                    "supabase_key": "SUPABASE_KEY",
                },
                "AUTH_KEYS": {
                    "jwt_secret": "SUPREMEAI_JWT_SECRET",
                    "encryption_key": "ENCRYPTION_KEY",
                    "supremeai_api_key": "SUPREMEAI_API_KEY",
                    "admin_password_hash": "SUPREMEAI_ADMIN_PASSWORD_HASH",
                },
            }
            import json as _json

            for blob_key, field_map in _json_blobs.items():
                raw = bulk.get(blob_key, "")
                if not raw:
                    continue
                try:
                    blob = _json.loads(raw)
                    for json_field, cache_key in field_map.items():
                        val = blob.get(json_field, "")
                        if val and not cached.get(cache_key):
                            cached[cache_key] = val
                except Exception as _je:
                    logger.debug(f"JSON blob '{blob_key}' parse failed: {_je}")

            elapsed = time.perf_counter() - _t0
            loaded = sum(1 for k in self._CORE_SECRET_KEYS if cached.get(k))
            logger.info(
                f"✅ Secrets bulk-loaded: {loaded}/{len(self._CORE_SECRET_KEYS)} core keys "
                f"in {elapsed:.3f}s (1 HTTP call)"
            )
        else:
            # ── STEP 2: Fallback — bulk fetch ব্যর্থ হলে পুরানো method ────
            logger.warning(
                "⚠️ Bulk secret fetch unavailable — falling back to individual fetches. "
                "This will be slower (~0.7s × secret count)."
            )

            # Legacy JSON blob fetch (3 HTTP calls)
            try:
                llm_keys = get_secret_vault().fetch_json_secret("LLM_PROVIDER_KEYS", default={})
                if llm_keys:
                    cached["OPENAI_API_KEY"] = llm_keys.get("openai", "")
                    cached["GEMINI_API_KEY"] = llm_keys.get("gemini", "")
                    cached["GROQ_API_KEY"] = llm_keys.get("groq", "")
                    cached["DEEPSEEK_API_KEY"] = llm_keys.get("deepseek", "")
                    cached["NVIDIA_API_KEY"] = llm_keys.get("nvidia", "")
                    cached["OPENROUTER_API_KEY"] = llm_keys.get("openrouter", "")
                    cached["HF_API_KEY"] = llm_keys.get("huggingface", "")

                db_config = get_secret_vault().fetch_json_secret("DATABASE_CONFIG", default={})
                if db_config:
                    cached["SUPABASE_DATABASE_URL_POOLER"] = db_config.get("pooler_url", "")
                    cached["SUPABASE_URL"] = db_config.get("supabase_url", "")
                    cached["SUPABASE_KEY"] = db_config.get("supabase_key", "")

                auth_keys = get_secret_vault().fetch_json_secret("AUTH_KEYS", default={})
                if auth_keys:
                    cached["SUPREMEAI_JWT_SECRET"] = auth_keys.get("jwt_secret", "")
                    cached["ENCRYPTION_KEY"] = auth_keys.get("encryption_key", "")
                    cached["SUPREMEAI_API_KEY"] = auth_keys.get("supremeai_api_key", "")
                    cached["SUPREMEAI_ADMIN_PASSWORD_HASH"] = auth_keys.get(
                        "admin_password_hash", ""
                    )

            except Exception as e:
                logger.debug(f"JSON blob fetch failed, falling back to individual: {e}")

            # Individual per-secret fetch for remaining missing keys
            for secret_key in self._CORE_SECRET_KEYS:
                if cached.get(secret_key):
                    continue  # already loaded

                try:
                    val = get_secret_vault().fetch_secret(secret_key, default="")
                    if val:
                        cached[secret_key] = val
                except Exception as _secret_err:
                    logger.debug(
                        f"Secret {secret_key} not available during batch load: {_secret_err}"
                    )

        # ── STEP 3: Individual fetch — bulk miss-এর safety net ───────────────
        # bulk সফল হলেও কিছু key missing থাকতে পারে (নতুন secrets, path mismatch)
        if bulk:
            missing = [k for k in self._CORE_SECRET_KEYS if not cached.get(k)]
            if missing:
                logger.debug(
                    f"Fetching {len(missing)} secrets individually (not in bulk result): {missing}"
                )
                for secret_key in missing:
                    try:
                        val = get_secret_vault().fetch_secret(secret_key, default="")
                        if val:
                            cached[secret_key] = val
                    except Exception as _secret_err:
                        logger.debug(
                            f"Secret {secret_key} not available individually: {_secret_err}"
                        )

        state["_secrets_batch_loaded"] = True

    def _get_cached_secret(self, key: str) -> str:
        """Get cached secret with explicit empty vs not-found handling.

        English: Returns the cached secret value. Logs a warning if the requested
        secret key was never loaded into cache (not found in vault or env).
        Returns empty string as fallback to avoid crashes, but the caller should
        check for empty strings where critical.

        বাংলা মন্তব্য: ব্যাচ লোড করা ক্যাশ থেকে সিক্রেট রিটার্ন করে।
        প্রথম কলেই সব সিক্রেট লোড করা হয়, এরপর শুধু মেমোরি থেকে রিটার্ন।
        """
        self._ensure_secrets_loaded()
        cached = self._get_private_state()["_cached_secrets"]

        if key not in cached:
            # Lazy load for optional keys
            if not self._is_test_environment():
                logger.info(f"Lazy loading optional secret: {key}")
                try:
                    val = get_secret_vault().fetch_secret(key, default="")
                    cached[key] = val
                except Exception as e:
                    logger.warning(f"Failed to lazy load optional secret '{key}': {e}")
                    cached[key] = ""
            else:
                logger.debug(
                    f"Secret '{key}' not found in cache after batch load - returning empty string"
                )
                cached[key] = ""
        return cached.get(key, "")

    # ── Cloud-fetched secrets — GCP Secret Manager বা env fallback ───────────
    # বাংলা মন্তব্য: স্টার্টআপ টাইম কমাতে এবং Infisical ভল্ট থেকে একের পর এক সিক্রেট ফেচ করা এড়াতে
    # `@computed_field` এর জায়গায় অলস (lazy) `@property` ব্যবহার করা হলো। এর ফলে শুধুমাত্র
    # অন-ডিমান্ড অ্যাক্সেস করলেই সিক্রেট ফেচ হবে এবং গ্লোবাল ক্যাশে জমা থাকবে।
    @property
    def supabase_database_url(self) -> str:
        return self._get_cached_secret("SUPABASE_DATABASE_URL_POOLER")

    @property
    def supabase_db_ca_cert(self) -> str:
        return self._get_cached_secret("SUPABASE_DB_CA_CERT")

    # বাংলা মন্তব্য: Anti-Hacking এবং OTP রাউটার সিক্রেটসমূহ (ঐচ্ছিক — মিসিং থাকলে সার্ভার ক্র্যাশ করবে না)
    @property
    def discord_otp_webhook_url(self) -> SecretStr | None:
        try:
            url = self._get_cached_secret("DISCORD_OTP_WEBHOOK_URL")
        except Exception:
            url = ""
        return SecretStr(url) if url else None

    @property
    def resend_api_key(self) -> SecretStr | None:
        key = self._get_cached_secret("RESEND_API_KEY")
        return SecretStr(key) if key else None

    @property
    def admin_notification_email(self) -> str | None:
        return self._get_cached_secret("ADMIN_NOTIFICATION_EMAIL")

    @property
    def redis_url(self) -> str:
        url = self._get_cached_secret("REDIS_URL")
        if not url:
            return url
        # বাংলা মন্তব্য (BUG FIX): Upstash কনসোলে দুই ধরনের URL দেওয়া থাকে —
        # একটি REST API URL (https://...) এবং একটি TLS/native URL (rediss://...)।
        # আমাদের কোড redis.asyncio.ConnectionPool.from_url() ব্যবহার করে (Upstash-এর
        # REST client নয়), তাই ভুলে REST URL (https://...) সেট করলে আগে এটিকে
        # "redis://https://..." বানিয়ে ফেলত — সম্পূর্ণ অকার্যকর এবং সাইলেন্টলি
        # in-memory rate-limiter fallback-এ চলে যেত। এখন এই ভুল কনফিগারেশন স্পষ্টভাবে
        # ধরা হচ্ছে এবং লগে সতর্ক করা হচ্ছে, যাতে ডিবাগ করা সহজ হয়।
        if url.startswith(("http://", "https://")):
            logger.error(
                "⚠️ REDIS_URL একটি Upstash REST API URL (http/https) — এটি ভুল। "
                "Upstash কনসোল থেকে 'rediss://...' ফরম্যাটের TLS URL ব্যবহার করুন "
                "(REST API URL নয়), নাহলে Redis কানেক্ট হবে না এবং rate limiter "
                "in-memory fallback-এ চলে যাবে।"
            )
            return ""
        if not url.startswith(("redis://", "rediss://", "unix://")):
            return f"redis://{url}"
        return url

    def _set_cached_secret(self, key: str, value: Any) -> None:
        self._ensure_secrets_loaded()
        self._get_private_state()["_cached_secrets"][key] = str(value) if value is not None else ""

    @property
    def openrouter_api_key(self) -> str:
        return self._get_cached_secret("OPENROUTER_API_KEY")

    @openrouter_api_key.setter
    def openrouter_api_key(self, value: str) -> None:
        self._set_cached_secret("OPENROUTER_API_KEY", value)

    @property
    def hf_api_key(self) -> str:
        return self._get_cached_secret("HF_API_KEY")

    @hf_api_key.setter
    def hf_api_key(self, value: str) -> None:
        self._set_cached_secret("HF_API_KEY", value)

    @property
    def hf_api_keys(self) -> list[str]:
        """বাংলা মন্তব্য: কমা-দ্বারা আলাদা করা HF API কীসমূহ লিস্ট আকারে রিটার্ন করা হয়।"""
        raw = self.hf_api_key
        if not raw:
            return []
        return [key.strip() for key in raw.split(",") if key.strip()]

    # Swarm Model Registry for 7 Hugging Face models
    MODEL_SWARM: dict[str, str] = {
        "coding": "njelit1/supreme-coder-3b",
        "reasoning": "njelitltd/supreme-reasoner-3b",
        "general": "ziaulhaq1/supreme-general-3b",
        "creative": "njelitltd2/supreme-creative-3b",
        "master": "njelitltd3/supreme-master-3b",
        "vision": "njelltd5/supreme-vision-3b",
        "draft": "njelltd4/supreme-draft-0.5b",
    }

    @property
    def gemini_api_key(self) -> str:
        return self._get_cached_secret("GEMINI_API_KEY")

    @gemini_api_key.setter
    def gemini_api_key(self, value: str) -> None:
        self._set_cached_secret("GEMINI_API_KEY", value)

    @property
    def openai_api_key(self) -> str:
        return self._get_cached_secret("OPENAI_API_KEY")

    @openai_api_key.setter
    def openai_api_key(self, value: str) -> None:
        self._set_cached_secret("OPENAI_API_KEY", value)

    @property
    def deepseek_api_key(self) -> str:
        return self._get_cached_secret("DEEPSEEK_API_KEY")

    @deepseek_api_key.setter
    def deepseek_api_key(self, value: str) -> None:
        self._set_cached_secret("DEEPSEEK_API_KEY", value)

    @property
    def groq_api_key(self) -> str:
        return self._get_cached_secret("GROQ_API_KEY")

    @groq_api_key.setter
    def groq_api_key(self, value: str) -> None:
        self._set_cached_secret("GROQ_API_KEY", value)

    @property
    def nvidia_api_key(self) -> str:
        return self._get_cached_secret("NVIDIA_API_KEY")

    @nvidia_api_key.setter
    def nvidia_api_key(self, value: str) -> None:
        self._set_cached_secret("NVIDIA_API_KEY", value)

    @property
    def firecrawl_api_key(self) -> str:
        return self._get_cached_secret("FIRECRAWL_API_KEY")

    @property
    def langfuse_public_key(self) -> str:
        return self._get_cached_secret("LANGFUSE_PUBLIC_KEY")

    @property
    def langfuse_secret_key(self) -> str:
        return self._get_cached_secret("LANGFUSE_SECRET_KEY")

    @property
    def kaggle_api_keys(self) -> list[str]:
        """Fetch all Kaggle API keys (base + 1 to 6) into a list."""
        keys = []
        for key_name in [
            "KAGGLE_API_TOKEN",
            "KAGGLE_API_TOKEN_1",
            "KAGGLE_API_TOKEN_2",
            "KAGGLE_API_TOKEN_3",
            "KAGGLE_API_TOKEN_4",
            "KAGGLE_API_TOKEN_5",
            "KAGGLE_API_TOKEN_6",
        ]:
            val = self._get_cached_secret(key_name)
            if val:
                keys.append(val)
        return keys

    @property
    def discord_bot_token(self) -> str:
        try:
            return self._get_cached_secret("DISCORD_BOT_TOKEN")
        except Exception:
            return ""

    @property
    def github_client_id(self) -> str:
        return self._get_cached_secret("GITHUB_CLIENT_ID")

    @property
    def github_client_secret(self) -> str:
        return self._get_cached_secret("GITHUB_CLIENT_SECRET")

    @property
    def ci_webhook_secret(self) -> str:
        return self._get_cached_secret("CI_WEBHOOK_SECRET")

    # ── Supabase credentials — settings-এ মাইগ্রেট করা হলো ──────────────────
    # বাংলা মন্তব্য: আগে database/supabase_client.py সরাসরি os.environ.get() করত।
    # এখন এই দুটো computed field settings-এর Single Source of Truth।
    # supabase_client.py শুধু settings.supabase_url এবং settings.supabase_key ব্যবহার করবে।
    @property
    def supabase_url(self) -> str:
        return self._get_cached_secret("SUPABASE_URL")

    @property
    def supabase_key(self) -> str:
        return self._get_cached_secret("SUPABASE_KEY")

    # বাংলা মন্তব্য: backend-only/audit টেবিল (যেমন evolution_logs) RLS bypass করে
    # লিখতে হলে service_role key দরকার। SUPABASE_SERVICE_ROLE_KEY সেট না থাকলে
    # SUPABASE_KEY-তেই fallback করবে (আগের বিহেভিয়ার অক্ষুণ্ণ রাখতে), তবে production-এ
    # এই env var আলাদাভাবে সেট করাটাই সঠিক নিরাপত্তা প্র্যাকটিস।
    @property
    def supabase_service_key(self) -> str:
        key = self._get_cached_secret("SUPABASE_SERVICE_ROLE_KEY")
        if self.env == "production" and not key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required in production environment.")
        return key or self._get_cached_secret("SUPABASE_KEY")

    @property
    def firebase_service_account_json(self) -> str:
        return self._get_cached_secret("FIREBASE_SERVICE_ACCOUNT_JSON")

    # ── System API Token — settings-এ মাইগ্রেট করা হলো ──────────────────────
    # বাংলা মন্তব্য: আগে auth_middleware.py সরাসরি os.getenv("SUPREMEAI_API_KEY") করত।
    # এখন এই computed field settings-এর Single Source of Truth।
    @property
    def supremeai_api_token(self) -> str:
        return self._get_cached_secret("SUPREMEAI_API_KEY")

    @property
    def neo4j_uri(self) -> str:
        return self._get_cached_secret("NEO4J_URI") or "bolt://localhost:7687"  # is_local()

    @property
    def neo4j_user(self) -> str:
        return self._get_cached_secret("NEO4J_USER") or "neo4j"

    @property
    def neo4j_password(self) -> str:
        return self._get_cached_secret("NEO4J_PASSWORD") or ""

    # ── Admin Password Hash — Infisical-backed lazy property ────────────────
    # বাংলা মন্তব্য: Pydantic Field(validation_alias=...) সরাসরি OS env var থেকে পড়ে, যা Infisical
    # ভল্টে থাকা সিক্রেট পড়তে পারে না এবং Render ডিপ্লয়মেন্টে Validation Error ঘটিয়ে প্রসেস করায়।
    # তাই এটি lazy @property এবং _get_cached_secret() এ রূপান্তর করা হলো যাতে অন-ডিমান্ড ভল্ট বা env থেকে ফেচ হয়।
    @property
    def supremeai_admin_password_hash(self) -> str | None:
        val = (
            self._get_cached_secret("SUPREMEAI_ADMIN_PASSWORD_HASH")
            or os.getenv("SUPREMEAI_ADMIN_PASSWORD_HASH")
            or os.getenv("supremeai_admin_password_hash")
        )
        if not val and "pytest" not in sys.modules and os.getenv("CI") != "true":
            raise ValueError("supremeai_admin_password_hash must be explicitly set.")
        return val

    # ── JWT & Encryption Credentials — Infisical-backed ─────────────────────
    # বাংলা মন্তব্য: JWT সিক্রেট এবং এনক্রিপশন কী ক্লাউড ভল্ট (Infisical/GCP) থেকে ডায়নামিকালি
    # লোড করার জন্য lazy property প্যাটার্ন প্রয়োগ করা হয়েছে।
    @property
    def jwt_secret(self) -> str:
        """Get JWT secret with environment-specific handling.

        বাংলা মন্তব্য: প্রোডাকশনে SUPREMEAI_JWT_SECRET অবশ্যই নির্দিষ্ট করতে হবে এবং ৬৪ বাইটের বেশি হতে হবে।
        Non-production এ generated secret কে _jwt_secret_cache-তে cache করা হয় যাতে
        create_access_token() ও verify_token() একই secret পায় — নাহলে JWSSignatureError হয়।
        """
        # Production: Must be explicitly set
        if self.env == "production":
            secret = (
                os.getenv("SUPREMEAI_JWT_SECRET")
                or os.getenv("JWT_SECRET")
                or self._get_cached_secret("SUPREMEAI_JWT_SECRET")
            )
            if not secret or len(secret) < 64:
                raise RuntimeError("Production JWT secret must be set and >= 64 bytes")
            self._jwt_secret_cache = secret
            return secret

        # Return cached value if available (critical for token create/verify consistency)
        if hasattr(self, "_jwt_secret_cache") and self._jwt_secret_cache:
            return self._jwt_secret_cache

        # Development: Try file first, then generate
        secret_file = "/etc/secrets/jwt_secret"
        local_file = ".secrets/jwt_secret.key"  # Windows compatibility

        for path in [secret_file, local_file]:
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        secret = f.read().strip()
                        if len(secret) >= 32:  # Minimum acceptable length
                            self._jwt_secret_cache = secret
                            return secret
                except OSError:
                    continue

        # Generate new secret if none found — cache it for consistency
        new_secret = secrets.token_hex(64)
        self._jwt_secret_cache = new_secret
        try:
            # Try to write to local file first (more permissive)
            os.makedirs(".secrets", exist_ok=True)
            with open(local_file, "w") as f:
                f.write(new_secret)
            return new_secret
        except OSError:
            logger.warning("Could not persist JWT secret - using in-memory only")
            return new_secret

    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins with environment-specific defaults and validation.

        বাংলা মন্তব্য: প্রোডাকশনে শুধুমাত্র অনুমোদিত ডোমেইনসমূহ অ্যাক্সেস করতে পারবে।
        টেস্টিং বা CI এনভায়রনমেন্টে (pytest, GITHUB_ACTIONS, CI, বা ALLOW_TEST_ORIGIN_BYPASS=true)
        ভ্যালিডেশন বাইপাস করে টেস্ট অরিজিন বা ডিফল্ট অরিজিন ফেরত দেওয়া হয়।
        """
        env_origins = os.getenv("CORS_ORIGINS")
        if env_origins:
            env_origins = env_origins.strip()
            try:
                parsed = json.loads(env_origins)
                origins = (
                    [str(o).strip() for o in parsed if str(o).strip()]
                    if isinstance(parsed, list)
                    else []
                )
            except json.JSONDecodeError:
                origins = [o.strip() for o in env_origins.split(",") if o.strip()]
        else:
            origins = [
                "http://localhost:3000",  # is_local()
                "http://localhost:5173",  # is_local()
                "http://localhost:8000",  # is_local()
            ]

        # বাংলা মন্তব্য: টেস্ট ও CI এনভায়রনমেন্ট সনাক্তকরণ
        force_strict = os.getenv("STRICT_CORS_TEST", "").lower() in ("true", "1")
        is_test_or_ci = not force_strict and (
            "pytest" in sys.modules
            or os.getenv("CI", "").lower() in ("true", "1")
            or os.getenv("GITHUB_ACTIONS", "").lower() in ("true", "1")
            or os.getenv("ALLOW_TEST_ORIGIN_BYPASS", "").lower() in ("true", "1")
            or self.is_origin_bypass_allowed
            or self.env in ("test", "testing", "local")
        )

        if self.env in ("production", "staging"):
            # বাংলা মন্তব্য: পুরনো hardcoded domain allowlist সরানো হয়েছে।
            # render.yaml-এ operator যেসব domain সেট করেন (onrender.com, vercel.app, web.app)
            # সেগুলো আগের stale list-এর সাথে না মেলায় সব origin reject হতো → RuntimeError → crash।
            # এখন শুধু scheme (https://) validate করা হয় — operator-configured যেকোনো domain গ্রহণযোগ্য।
            validated_origins = []
            for origin in origins:
                if (
                    origin.startswith("https://")
                    or "localhost" in origin
                    or "127.0.0.1" in origin  # is_local()
                    or is_test_or_ci
                ):
                    validated_origins.append(origin)
                else:
                    logger.warning(f"Rejecting non-HTTPS CORS origin in production: {origin}")

            if not validated_origins:
                if is_test_or_ci:
                    return (
                        origins
                        if origins
                        else [
                            "http://localhost:3000",  # is_local()
                            "http://localhost:5173",  # is_local()
                            "http://localhost:8000",  # is_local()
                        ]
                    )
                raise RuntimeError(
                    "No valid CORS origins provided. "
                    "Ensure CORS_ORIGINS env var contains https:// origins."
                )

            return validated_origins

        return origins

    @property
    def encryption_key(self) -> SecretStr:
        val = self._get_cached_secret("ENCRYPTION_KEY")
        if val:
            return SecretStr(val)

        # Fallback for development/local environment
        if self.env == "production":
            raise ValueError("ENCRYPTION_KEY must be explicitly set in production!")

        import base64
        import os

        local_file = ".secrets/encryption.key"
        if os.path.exists(local_file):
            try:
                with open(local_file) as f:
                    secret = f.read().strip()
                    if len(secret) >= 43:  # Fernet keys are 44 characters (base64 of 32 bytes)
                        return SecretStr(secret)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                import logging

                logging.getLogger(__name__).exception(f"Silenced error: {e}")

        # Generate a new Fernet key (URL-safe base64-encoded 32-byte key)
        new_key = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
        try:
            os.makedirs(".secrets", exist_ok=True)
            with open(local_file, "w") as f:
                f.write(new_key)
        except OSError:
            logger.warning("Could not persist ENCRYPTION_KEY - using in-memory only")

        return SecretStr(new_key)

    # ── Stripe Credentials — Infisical-backed ────────────────────────────────
    # বাংলা মন্তব্য: Stripe এপিআই এবং ওয়েবহুক সিক্রেটসমূহের জন্য Infisical lazy fetching নিশ্চিত করা হলো,
    # যাতে প্রোডাকশন পেমেন্ট ক্রেডেনশিয়াল ভল্ট থেকে সরাসরি ইন-মেমোরিতে ফেচ হয়।
    @property
    def stripe_api_key(self) -> SecretStr:
        val = self._get_cached_secret("STRIPE_API_KEY")
        return SecretStr(val) if val else SecretStr("")

    @property
    def stripe_webhook_secret(self) -> SecretStr:
        val = self._get_cached_secret("STRIPE_WEBHOOK_SECRET")
        return SecretStr(val) if val else SecretStr("")

    @property
    def telegram_bot_token(self) -> str:
        return self._get_cached_secret("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "")

    @property
    def admin_telegram_chat_id(self) -> str:
        return self._get_cached_secret("ADMIN_TELEGRAM_CHAT_ID") or os.getenv(
            "ADMIN_TELEGRAM_CHAT_ID", ""
        )

    # ── Automation Credentials — Infisical-backed ────────────────────────────
    @property
    def n8n_webhook_secret(self) -> SecretStr:
        val = self._get_cached_secret("N8N_WEBHOOK_SECRET")
        return SecretStr(val) if val else SecretStr("")

    @property
    def appwrite_api_key(self) -> SecretStr:
        val = self._get_cached_secret("APPWRITE_API_KEY")
        return SecretStr(val) if val else SecretStr("")

    # ── Serializer ──────────────────────────────────────────────────────────
    # বাংলা মন্তব্য: @property-ভিত্তিক সিক্রেট Pydantic model_dump()-এ অন্তর্ভুক্ত হয় না।
    # এই serializer নিশ্চিত করে যে settings.model_dump() কল করলে সব ফিল্ড এবং প্রপার্টি দেখা যায়,
    # কিন্তু সিক্রেট ভ্যালুগুলি "***REDACTED***" হিসাবে দেখানো হয়।
    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Ensure properties are visible in serialization, with secrets redacted."""
        result: dict[str, Any] = {}
        for field_name in self.model_fields:
            result[field_name] = getattr(self, field_name)
        # Include critical lazy properties with redaction
        redacted = "***REDACTED***"
        result["jwt_secret"] = redacted
        result["redis_url"] = redacted
        result["supabase_database_url"] = redacted
        result["supremeai_admin_password_hash"] = redacted
        result["encryption_key"] = redacted
        result["supremeai_api_token"] = redacted
        result["stripe_api_key"] = redacted
        result["stripe_webhook_secret"] = redacted
        result["firebase_service_account_json"] = redacted
        # Include API keys (redacted)
        for key_field in [
            "openrouter_api_key",
            "gemini_api_key",
            "openai_api_key",
            "groq_api_key",
            "nvidia_api_key",
            "hf_api_key",
            "deepseek_api_key",
            "firecrawl_api_key",
            "discord_bot_token",
            "github_client_id",
            "github_client_secret",
            "ci_webhook_secret",
            "supabase_url",
            "supabase_key",
            "supabase_service_key",
            "langfuse_public_key",
            "langfuse_secret_key",
            "KAGGLE_API_TOKEN",
            "KAGGLE_API_TOKEN_1",
            "KAGGLE_API_TOKEN_2",
            "KAGGLE_API_TOKEN_3",
            "KAGGLE_API_TOKEN_4",
            "KAGGLE_API_TOKEN_5",
            "KAGGLE_API_TOKEN_6",
            "N8N_WEBHOOK_SECRET",
            "APPWRITE_API_KEY",
        ]:
            result[key_field] = redacted
        # Include non-secret properties
        result["neo4j_uri"] = self.neo4j_uri
        result["neo4j_user"] = self.neo4j_user
        result["admin_notification_email"] = self.admin_notification_email
        return result
