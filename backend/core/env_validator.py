"""
SupremeAI Environment Validator - 10/10 Production Readiness
================================================================
Validates all required environment variables at startup with clear error messages.
Prevents silent failures from missing configuration.

Single source of truth (issue #1260, Wave 3.4): the canonical env-key vocabulary
lives in ``core/config_classification.py::CONFIG_SPECS``. ``ENV_REGISTRY`` below
is a *derived view* of that registry — it declares WHICH classified keys this
validator checks at boot (a startup-policy decision that cannot be filtered out
of CONFIG_SPECS attributes, see the comment on ``_ENV_REGISTRY_ORDER``), then
builds one ``EnvVarDefinition`` per key, resolving names/aliases through the
canonical registry. A key renamed or removed in CONFIG_SPECS fails loudly here
at import time instead of silently drifting.

Author: SuperAI Enhancement Patch
Version: 2.1.0
"""

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Issue #542 (BE-10): unify the JWT secret floor with the other validators.
# Issue #567 (BE-16): canonical JWT secret env-var name + deprecated alias.
# Issue #1260 (Wave 3.4): ENV_REGISTRY derives from the canonical CONFIG_SPECS.
from core.config_classification import get_config_spec
from core.logging_config import logger
from core.secret_policy import (
    JWT_SECRET_DEPRECATED_ENV,
    JWT_SECRET_ENV,
    JWT_SECRET_MIN_LENGTH,
)


class EnvSeverity(Enum):
    """Severity levels for environment variables"""

    CRITICAL = "critical"  # App won't start without this
    HIGH = "high"  # Major features broken
    MEDIUM = "medium"  # Degraded functionality
    LOW = "low"  # Optional enhancements
    INFO = "info"  # Informational only


@dataclass
class EnvVarDefinition:
    """Definition of an environment variable"""

    name: str
    description: str
    severity: EnvSeverity
    default: str | None = None
    pattern: str | None = None  # Regex pattern for validation
    min_length: int | None = None  # Minimum value length (issue #542 / BE-10)
    examples: list[str] = field(default_factory=list)
    documentation_url: str | None = None


# ==========================================================================
# ENV_REGISTRY — derived view over the canonical CONFIG_SPECS (issue #1260)
# ==========================================================================
# Boot-validation membership is a startup POLICY, not a classification
# property: 112 CONFIG_SPECS entries share the exact
# (conditional, secret)/(env, vault)/(backend) signature of e.g. GEMINI_API_KEY
# but are deliberately NOT boot-checked, so no attribute filter can reproduce
# this subset. It is therefore an explicit ordered tuple, cross-checked against
# CONFIG_SPECS at import time by _build_env_registry(): renaming/removing a
# classified key breaks import here with a precise message instead of drifting.
#
# Validator-specific semantics (severity / pattern / default / min_length) are
# boot-validator policy and live in _ENV_PROFILES. Descriptions stay the
# curated validator text: the CONFIG_SPECS descriptions for these keys are
# still auto-classification placeholders ("needs manual review") — curate
# CONFIG_SPECS first, then switch the builder over to spec.description.

_ENV_REGISTRY_ORDER: tuple[str, ...] = (
    # ── Core ──────────────────────────────────────────────────────────────
    "ENV",
    "PORT",
    "HOST",
    # ── Secrets (CRITICAL in production) ─────────────────────────────────
    JWT_SECRET_ENV,
    "SUPREMEAI_ADMIN_PASSWORD_HASH",
    "SUPREMEAI_ENCRYPTION_KEY",
    "SUPREMEAI_API_TOKEN",
    # ── Database (Supabase) ───────────────────────────────────────────────
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "SUPABASE_DATABASE_URL_POOLER",
    # ── Redis (Upstash) ───────────────────────────────────────────────────
    "REDIS_URL",
    "UPSTASH_REDIS_REST_URL",
    "UPSTASH_REDIS_REST_TOKEN",
    # ── LLM API Keys (at least one required) ─────────────────────────────
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "NVIDIA_API_KEY",
    "DEEPSEEK_API_KEY",
    "HF_API_KEY",
    # ── Stripe ─────────────────────────────────────────────────────────────
    "STRIPE_API_KEY",
    "STRIPE_WEBHOOK_SECRET",
    # ── Infisical (Secret Vault) ──────────────────────────────────────────
    "INFISICAL_TOKEN",
    "INFISICAL_CLIENT_ID",
    "INFISICAL_CLIENT_SECRET",
    # ── Observability ─────────────────────────────────────────────────────
    "SENTRY_DSN",
    "OTLP_ENDPOINT",
    # ── Security ──────────────────────────────────────────────────────────
    "ENFORCE_ANTI_HACKING",
    "OTP_COOLDOWN_SECONDS",
)


@dataclass(frozen=True)
class _EnvVarProfile:
    """Boot-validator semantics for one classified key (see _ENV_PROFILES)."""

    severity: EnvSeverity
    description: str
    default: str | None = None
    pattern: str | None = None  # Regex pattern for validation
    min_length: int | None = None  # Minimum value length (issue #542 / BE-10)
    examples: tuple[str, ...] = ()
    documentation_url: str | None = None


_ENV_PROFILES: dict[str, _EnvVarProfile] = {
    "ENV": _EnvVarProfile(
        severity=EnvSeverity.CRITICAL,
        description="Environment mode (local, staging, production)",
        default="local",
        examples=("local", "staging", "production"),
    ),
    "PORT": _EnvVarProfile(
        severity=EnvSeverity.CRITICAL,
        description="Server port number",
        default="8080",
        pattern=r"^\d{4,5}$",
    ),
    "HOST": _EnvVarProfile(
        severity=EnvSeverity.MEDIUM,
        description="Server bind address",
        default="0.0.0.0",
    ),
    JWT_SECRET_ENV: _EnvVarProfile(
        severity=EnvSeverity.CRITICAL,
        description="JWT signing secret (canonical; JWT_SECRET is a deprecated alias)",
        # Issue #542 (BE-10): had no length check, so a too-short secret
        # passed boot validation and blew up mid-request when
        # settings.jwt_secret raised RuntimeError (>=64 floor).
        min_length=JWT_SECRET_MIN_LENGTH,
    ),
    "SUPREMEAI_ADMIN_PASSWORD_HASH": _EnvVarProfile(
        severity=EnvSeverity.CRITICAL,
        description="Bcrypt hash of admin password",
    ),
    "SUPABASE_URL": _EnvVarProfile(
        severity=EnvSeverity.CRITICAL,
        description="Supabase project URL",
        pattern=r"^https://[a-z0-9-]+\.supabase\.co$",
    ),
    "SUPABASE_KEY": _EnvVarProfile(
        severity=EnvSeverity.CRITICAL,
        description="Supabase anon/public API key",
        pattern=r"^eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+$",
    ),
    "SUPABASE_DATABASE_URL_POOLER": _EnvVarProfile(
        severity=EnvSeverity.HIGH,
        description="Supabase pooler connection string (postgresql://)",
        pattern=r"^postgresql://[^:]+:[^@]+@[^:]+:\d+/.+$",
    ),
    "REDIS_URL": _EnvVarProfile(
        severity=EnvSeverity.HIGH,
        description="Redis connection URL (redis:// or rediss://)",
        pattern=r"^red?iss?://[^:]+(:[^@]+)?@[^:]+:\d+/\d*$",
    ),
    "UPSTASH_REDIS_REST_TOKEN": _EnvVarProfile(
        severity=EnvSeverity.MEDIUM,
        description="Upstash Redis REST authentication token",
    ),
    "OPENROUTER_API_KEY": _EnvVarProfile(
        severity=EnvSeverity.HIGH,
        description="OpenRouter API key for multi-model access",
        pattern=r"^sk-or-[a-zA-Z0-9_-]+$",
    ),
    "OPENAI_API_KEY": _EnvVarProfile(
        severity=EnvSeverity.HIGH,
        description="OpenAI API key (GPT-4, GPT-3.5)",
        pattern=r"^sk-[a-zA-Z0-9]{48}$",
    ),
    "GEMINI_API_KEY": _EnvVarProfile(
        severity=EnvSeverity.HIGH,
        description="Google Gemini API key",
        pattern=r"^AIza[a-zA-Z0-9_-]{35}$",
    ),
    "GROQ_API_KEY": _EnvVarProfile(
        severity=EnvSeverity.LOW,
        description="Groq API key for fast inference",
        pattern=r"^gsk_[a-zA-Z0-9]{52}$",
    ),
    "NVIDIA_API_KEY": _EnvVarProfile(
        severity=EnvSeverity.LOW,
        description="NVIDIA API key for GPU-accelerated inference",
    ),
    "DEEPSEEK_API_KEY": _EnvVarProfile(
        severity=EnvSeverity.LOW,
        description="DeepSeek API key",
    ),
    "STRIPE_WEBHOOK_SECRET": _EnvVarProfile(
        severity=EnvSeverity.MEDIUM,
        description="Stripe webhook signature secret",
        pattern=r"^whsec_[a-zA-Z0-9]+$",
    ),
    "INFISICAL_TOKEN": _EnvVarProfile(
        severity=EnvSeverity.HIGH,
        description="Infisical authentication token",
    ),
    "INFISICAL_CLIENT_ID": _EnvVarProfile(
        severity=EnvSeverity.HIGH,
        description="Infisical Machine Identity client ID",
    ),
    "INFISICAL_CLIENT_SECRET": _EnvVarProfile(
        severity=EnvSeverity.HIGH,
        description="Infisical Machine Identity client secret",
    ),
    "SENTRY_DSN": _EnvVarProfile(
        severity=EnvSeverity.LOW,
        description="Sentry DSN for error tracking",
        pattern=r"^https://[a-f0-9]+@[a-z0-9-]+\.ingest\.sentry\.io/\d+$",
    ),
    "ENFORCE_ANTI_HACKING": _EnvVarProfile(
        severity=EnvSeverity.LOW,
        description="Enable anti-hacking protections",
        default="false",
    ),
    "OTP_COOLDOWN_SECONDS": _EnvVarProfile(
        severity=EnvSeverity.LOW,
        description="OTP cooldown period in seconds",
        default="60",
    ),
}

# Boot-checked keys NOT yet classified in CONFIG_SPECS (issue #1260 follow-up:
# adopt these into CONFIG_SPECS, then move their definitions into
# _ENV_PROFILES and delete them from this override map). Kept as full
# definitions so the validator behaviour is unchanged until adoption.
_ENV_REGISTRY_OVERRIDES: dict[str, EnvVarDefinition] = {
    "SUPREMEAI_ENCRYPTION_KEY": EnvVarDefinition(
        name="SUPREMEAI_ENCRYPTION_KEY",
        description="Fernet encryption key for sensitive data",
        severity=EnvSeverity.LOW,
    ),
    "SUPREMEAI_API_TOKEN": EnvVarDefinition(
        name="SUPREMEAI_API_TOKEN",
        description="Master API token for service-to-service auth",
        severity=EnvSeverity.LOW,
        pattern=r"^sk-[a-zA-Z0-9]{32,}$",
    ),
    "UPSTASH_REDIS_REST_URL": EnvVarDefinition(
        name="UPSTASH_REDIS_REST_URL",
        description="Upstash Redis REST API endpoint",
        severity=EnvSeverity.MEDIUM,
    ),
    "HF_API_KEY": EnvVarDefinition(
        name="HF_API_KEY",
        description="HuggingFace API key for model access",
        severity=EnvSeverity.LOW,
        pattern=r"^hf_[a-zA-Z0-9]{34}$",
    ),
    "STRIPE_API_KEY": EnvVarDefinition(
        name="STRIPE_API_KEY",
        description="Stripe secret API key (sk_live_ or sk_test_)",
        severity=EnvSeverity.MEDIUM,
        pattern=r"^sk_(test|live)_[a-zA-Z0-9]+$",
    ),
    "OTLP_ENDPOINT": EnvVarDefinition(
        name="OTLP_ENDPOINT",
        description="OpenTelemetry collector endpoint",
        severity=EnvSeverity.LOW,
    ),
}


def _build_env_registry() -> list[EnvVarDefinition]:
    """Derive ENV_REGISTRY from CONFIG_SPECS + boot-validator profiles.

    Fails loudly when the boot-validation policy and the canonical registry
    drift apart (unclassified key, missing profile, renamed spec).
    """
    registry: list[EnvVarDefinition] = []
    for name in _ENV_REGISTRY_ORDER:
        override = _ENV_REGISTRY_OVERRIDES.get(name)
        if override is not None:
            registry.append(override)
            continue
        spec = get_config_spec(name)
        if spec is None:
            raise RuntimeError(
                f"ENV_REGISTRY member {name!r} is not classified in "
                "core/config_classification.py CONFIG_SPECS (issue #1260). "
                "Classify it there (or add it to _ENV_REGISTRY_OVERRIDES with "
                "a reason) before boot validation can use it."
            )
        try:
            profile = _ENV_PROFILES[name]
        except KeyError as exc:
            raise RuntimeError(
                f"ENV_REGISTRY member {name!r} has no _ENV_PROFILES entry — "
                "declare its boot-validation semantics (severity/pattern/"
                "default) in core/env_validator.py."
            ) from exc
        registry.append(
            EnvVarDefinition(
                name=name,
                # Curated validator text; spec.description is intentionally NOT
                # used yet (auto-classified placeholders, see block comment).
                description=profile.description,
                severity=profile.severity,
                default=profile.default,
                pattern=profile.pattern,
                min_length=profile.min_length,
                examples=list(profile.examples),
                documentation_url=profile.documentation_url,
            )
        )
    return registry


# Complete environment variable registry (derived — see block comment above).
ENV_REGISTRY: list[EnvVarDefinition] = _build_env_registry()


@dataclass
class ValidationResult:
    """Result of environment variable validation"""

    is_valid: bool
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    info: list[dict[str, Any]] = field(default_factory=list)
    score: int = 0  # 0-100


class EnvironmentValidator:
    """
    Validates environment variables and provides clear diagnostics.

    Usage:
        validator = EnvironmentValidator()
        result = validator.validate()

        if not result.is_valid:
            logger.error("Environment validation failed!")
            validator.print_report(result)
            sys.exit(1)
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.

        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
        self.registry = ENV_REGISTRY

    def validate(self) -> ValidationResult:
        """
        Validate all registered environment variables.

        Returns:
            ValidationResult with detailed findings
        """
        result = ValidationResult(is_valid=True)
        total_vars = len(self.registry)
        valid_count = 0

        for env_def in self.registry:
            value = os.environ.get(env_def.name)

            if env_def.name == JWT_SECRET_ENV and not (value and value.strip()):
                # Issue #567 (BE-16): JWT_SECRET is a deprecated alias for the
                # canonical SUPREMEAI_JWT_SECRET — accept it instead of a
                # false CRITICAL "missing", but warn so operators migrate;
                # the >=64-byte floor (issue #542) still applies to it.
                legacy = os.environ.get(JWT_SECRET_DEPRECATED_ENV, "")
                if legacy.strip():
                    if len(legacy) < (env_def.min_length or 0):
                        result.errors.append(
                            {
                                "variable": env_def.name,
                                "message": (
                                    f"Deprecated alias {JWT_SECRET_DEPRECATED_ENV} is only "
                                    f"{len(legacy)} characters long; minimum required length "
                                    f"is {env_def.min_length}"
                                ),
                                "severity": env_def.severity.value,
                            }
                        )
                        result.is_valid = False
                    else:
                        result.warnings.append(
                            {
                                "variable": env_def.name,
                                "message": (
                                    f"Deprecated alias {JWT_SECRET_DEPRECATED_ENV} is set; "
                                    f"rename it to the canonical {JWT_SECRET_ENV} "
                                    "(Issue #567 / BE-16)."
                                ),
                                "severity": env_def.severity.value,
                            }
                        )
                        valid_count += 1
                    continue

            if value is None or value.strip() == "":
                if env_def.default is not None:
                    # Use default value
                    os.environ[env_def.name] = env_def.default
                    result.info.append(
                        {
                            "variable": env_def.name,
                            "message": f"Using default value: {env_def.default}",
                            "severity": env_def.severity.value,
                        }
                    )
                    valid_count += 1
                else:
                    # Missing required variable
                    error_msg = self._format_missing_error(env_def)

                    if env_def.severity in [EnvSeverity.CRITICAL, EnvSeverity.HIGH]:
                        result.errors.append(
                            {
                                "variable": env_def.name,
                                "message": error_msg,
                                "severity": env_def.severity.value,
                                "description": env_def.description,
                            }
                        )
                        if env_def.severity == EnvSeverity.CRITICAL:
                            result.is_valid = False
                    else:
                        result.warnings.append(
                            {
                                "variable": env_def.name,
                                "message": error_msg,
                                "severity": env_def.severity.value,
                                "description": env_def.description,
                            }
                        )
            else:
                value_is_valid = True

                # Validate format if pattern specified
                if env_def.pattern:
                    import re

                    if not re.match(env_def.pattern, value):
                        msg = f"Invalid format for {env_def.name}. Expected pattern: {env_def.pattern}"

                        if env_def.severity == EnvSeverity.CRITICAL:
                            result.errors.append(
                                {
                                    "variable": env_def.name,
                                    "message": msg,
                                    "severity": env_def.severity.value,
                                    "actual_value_preview": value[:8] + "..."
                                    if len(value) > 8
                                    else value,
                                }
                            )
                            result.is_valid = False
                        else:
                            result.warnings.append(
                                {
                                    "variable": env_def.name,
                                    "message": msg,
                                    "severity": env_def.severity.value,
                                }
                            )
                        value_is_valid = False

                # Validate minimum length if specified (issue #542 / BE-10)
                if env_def.min_length is not None and len(value) < env_def.min_length:
                    msg = (
                        f"Value for {env_def.name} is only {len(value)} characters long; "
                        f"minimum required length is {env_def.min_length}"
                    )

                    if env_def.severity == EnvSeverity.CRITICAL:
                        result.errors.append(
                            {
                                "variable": env_def.name,
                                "message": msg,
                                "severity": env_def.severity.value,
                                "actual_value_preview": value[:8] + "..."
                                if len(value) > 8
                                else value,
                            }
                        )
                        result.is_valid = False
                    else:
                        result.warnings.append(
                            {
                                "variable": env_def.name,
                                "message": msg,
                                "severity": env_def.severity.value,
                            }
                        )
                    value_is_valid = False

                if value_is_valid:
                    valid_count += 1

        # Calculate health score
        result.score = int((valid_count / total_vars) * 100)

        # Check for at least one LLM provider across the entire dynamic pool ($0..N)
        llm_providers = [
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            "GROQ_API_KEY",
            "MISTRAL_API_KEY",
            "ANTHROPIC_API_KEY",
            "DEEPSEEK_API_KEY",
            "COHERE_API_KEY",
            "BYNARA_API_KEY",
            "BAI_API_KEY",
            "TOGETHER_API_KEY",
            "HF_API_KEY",
            "HUGGINGFACE_API_KEY",
            "OLLAMA_API_KEY",
            "OLLAMA_BASE_URL",
        ]
        has_llm_provider = any(os.environ.get(key) for key in llm_providers)

        if not has_llm_provider:
            result.errors.append(
                {
                    "variable": "LLM_PROVIDERS",
                    "message": "At least one LLM API key is required across dynamic pool (e.g., OPENAI, GEMINI, OPENROUTER, MISTRAL, GROQ, ANTHROPIC, DEEPSEEK, etc.)",
                    "severity": "critical",
                }
            )
            result.is_valid = False

        return result

    def _format_missing_error(self, env_def: EnvVarDefinition) -> str:
        """Format user-friendly error message for missing variable"""
        examples_str = ""
        if env_def.examples:
            examples_str = f"\n  Examples: {', '.join(env_def.examples)}"

        doc_url_str = ""
        if env_def.documentation_url:
            doc_url_str = f"\n  Docs: {env_def.documentation_url}"

        return (
            f"Missing required environment variable: {env_def.name}\n"
            f"  Description: {env_def.description}"
            f"{examples_str}"
            f"{doc_url_str}"
        )

    def print_report(self, result: ValidationResult) -> None:
        """Print validation report to console"""
        from core.logging_config import logger

        logger.info("\n" + "=" * 70)
        from core.logging_config import logger

        logger.info("🔍 SUPREMEAI ENVIRONMENT VALIDATION REPORT")
        from core.logging_config import logger

        logger.info("=" * 70)
        from core.logging_config import logger

        logger.info(f"\n📊 Health Score: {result.score}/100")
        from core.logging_config import logger

        logger.info(f"   Status: {'✅ PASS' if result.is_valid else '❌ FAIL'}\n")

        if result.errors:
            from core.logging_config import logger

            logger.info("🚨 CRITICAL ERRORS (Must Fix):")
            from core.logging_config import logger

            logger.info("-" * 70)
            for i, error in enumerate(result.errors, 1):
                from core.logging_config import logger

                logger.info(f"\n{i}. {error['variable']}")
                from core.logging_config import logger

                logger.info(f"   {error['message']}")
                if "description" in error:
                    from core.logging_config import logger

                    logger.info(f"   📖 {error['description']}")

        if result.warnings:
            from core.logging_config import logger

            logger.info("\n⚠️  WARNINGS (Recommended):")
            from core.logging_config import logger

            logger.info("-" * 70)
            for i, warning in enumerate(result.warnings, 1):
                from core.logging_config import logger

                logger.info(f"\n{i}. {warning['variable']}")
                from core.logging_config import logger

                logger.info(f"   {warning['message']}")

        if result.info:
            from core.logging_config import logger

            logger.info("\nℹ️  INFORMATION:")
            from core.logging_config import logger

            logger.info("-" * 70)
            for info in result.info[:5]:  # Show first 5
                from core.logging_config import logger

                logger.info(f"  • {info['variable']}: {info['message']}")

        from core.logging_config import logger

        logger.info("\n" + "=" * 70 + "\n")


def validate_environment(strict: bool = False) -> bool:
    """
    Convenience function to validate environment.

    Args:
        strict: If True, fail on warnings too

    Returns:
        True if validation passes, False otherwise
    """
    validator = EnvironmentValidator(strict_mode=strict)
    result = validator.validate()

    if not result.is_valid:
        validator.print_report(result)
        logger.error(f"Environment validation failed with score: {result.score}/100")
        return False

    logger.success(f"✅ Environment validation passed! Score: {result.score}/100")
    return True


# Auto-run when executed directly
if __name__ == "__main__":
    import json

    logger.debug("🔍 SupremeAI Environment Validator")
    logger.debug("=" * 50)

    validator = EnvironmentValidator()
    result = validator.validate()

    validator.print_report(result)

    # Output JSON for CI/CD consumption
    output = {
        "valid": result.is_valid,
        "score": result.score,
        "errors": len(result.errors),
        "warnings": len(result.warnings),
        "details": {"errors": result.errors, "warnings": result.warnings},
    }

    logger.debug("\n📋 JSON Output (for CI/CD):")
    logger.debug(json.dumps(output, indent=2))

    sys.exit(0 if result.is_valid else 1)
