"""Canonical configuration metadata for SupremeAI.

This module is intentionally metadata-only: it contains variable names, aliases,
classification and source policy, never secret values.

The goal is to give runtime configuration, CI drift checks and future admin tooling
one stable vocabulary.  Secret values remain in Infisical/deployment environments.
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


# Canonical contract from specs/001-dynamic-production-configuration.
# Keep this registry deliberately small and authoritative for names that affect
# deployment topology, security boundaries, or secret provenance. Feature-specific
# providers can be added here without changing the validator architecture.
CONFIG_SPECS: tuple[ConfigSpec, ...] = (
    ConfigSpec("SUPREMEAI_USER_BACKEND_URL", frozenset({ConfigClass.REQUIRED}), frozenset({ConfigSource.ENV, ConfigSource.DEPLOY}), frozenset({"backend", "deploy"}), description="Canonical user backend location."),
    ConfigSpec("SUPREMEAI_ADMIN_BACKEND_URL", frozenset({ConfigClass.REQUIRED}), frozenset({ConfigSource.ENV, ConfigSource.DEPLOY}), frozenset({"backend", "deploy"}), description="Canonical admin backend location."),
    ConfigSpec("SCRAPER_URL", frozenset({ConfigClass.OPTIONAL}), frozenset({ConfigSource.ENV}), frozenset({"backend"}), description="Optional scraper service."),
    ConfigSpec("ADMIN_URL", frozenset({ConfigClass.OPTIONAL, ConfigClass.CONDITIONAL}), frozenset({ConfigSource.ENV}), frozenset({"backend"}), required_when="admin aggregation enabled"),
    ConfigSpec("CHECKOUT_BASE_URL", frozenset({ConfigClass.CONDITIONAL}), frozenset({ConfigSource.ENV}), frozenset({"backend"}), required_when="billing enabled"),
    ConfigSpec("RENDER_SERVICE_NAME", frozenset({ConfigClass.CONDITIONAL}), frozenset({ConfigSource.ENV, ConfigSource.GENERATED}), frozenset({"backend", "deploy"})),
    ConfigSpec("CORS_ORIGINS", frozenset({ConfigClass.REQUIRED}), frozenset({ConfigSource.ENV}), frozenset({"backend"}), aliases=("USER_CORS_ORIGINS",)),
    ConfigSpec("ADMIN_CORS_ORIGINS", frozenset({ConfigClass.REQUIRED}), frozenset({ConfigSource.ENV}), frozenset({"backend"})),
    ConfigSpec("ALLOWED_ORIGINS", frozenset({ConfigClass.REQUIRED}), frozenset({ConfigSource.ENV}), frozenset({"backend"}), aliases=("CORS_ORIGINS", "USER_CORS_ORIGINS"), description="Legacy compatibility input; canonical resolver owns interpretation."),
    ConfigSpec("ALLOWED_HOSTS", frozenset({ConfigClass.REQUIRED}), frozenset({ConfigSource.ENV}), frozenset({"backend"})),
    ConfigSpec("VITE_USER_BACKEND", frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"}), aliases=("VITE_API_URL",)),
    ConfigSpec("VITE_ADMIN_BACKEND", frozenset({ConfigClass.CONDITIONAL, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"}), required_when="VITE_PORTAL_TYPE=admin"),
    ConfigSpec("VITE_SCRAPER_BACKEND", frozenset({ConfigClass.OPTIONAL, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_PORTAL_TYPE", frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_USE_RELATIVE_PATH", frozenset({ConfigClass.OPTIONAL, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_WS_BASE_URL", frozenset({ConfigClass.OPTIONAL, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_FIREBASE_API_KEY", frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_FIREBASE_AUTH_DOMAIN", frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_FIREBASE_PROJECT_ID", frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_FIREBASE_STORAGE_BUCKET", frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_FIREBASE_MESSAGING_SENDER_ID", frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_FIREBASE_APP_ID", frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_SUPABASE_URL", frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("VITE_SUPABASE_ANON_KEY", frozenset({ConfigClass.REQUIRED, ConfigClass.PUBLIC}), frozenset({ConfigSource.BUILD}), frozenset({"frontend"})),
    ConfigSpec("SUPABASE_DATABASE_URL_POOLER", frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}), frozenset({ConfigSource.VAULT, ConfigSource.ENV}), frozenset({"backend"})),
    ConfigSpec("SUPABASE_DB_CA_CERT", frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}), frozenset({ConfigSource.VAULT, ConfigSource.ENV}), frozenset({"backend"}), required_when="explicit PostgreSQL CA verification is enabled"),
    ConfigSpec("SUPABASE_URL", frozenset({ConfigClass.REQUIRED}), frozenset({ConfigSource.VAULT, ConfigSource.ENV}), frozenset({"backend"})),
    ConfigSpec("SUPABASE_KEY", frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}), frozenset({ConfigSource.VAULT, ConfigSource.ENV}), frozenset({"backend"})),
    ConfigSpec("SUPABASE_SERVICE_ROLE_KEY", frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}), frozenset({ConfigSource.VAULT, ConfigSource.ENV}), frozenset({"backend"}), required_when="backend service-client paths enabled"),
    ConfigSpec("REDIS_URL", frozenset({ConfigClass.SECRET, ConfigClass.OPTIONAL}), frozenset({ConfigSource.VAULT, ConfigSource.ENV}), frozenset({"backend"})),
    ConfigSpec("OLLAMA_URL", frozenset({ConfigClass.OPTIONAL}), frozenset({ConfigSource.ENV}), frozenset({"user-local"})),
    ConfigSpec("SUPREMEAI_JWT_SECRET", frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}), frozenset({ConfigSource.VAULT, ConfigSource.ENV}), frozenset({"backend"})),
    ConfigSpec("ENCRYPTION_KEY", frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}), frozenset({ConfigSource.VAULT, ConfigSource.ENV}), frozenset({"backend"})),
    ConfigSpec("SUPREMEAI_ADMIN_PASSWORD_HASH", frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}), frozenset({ConfigSource.VAULT, ConfigSource.ENV}), frozenset({"backend"})),
    ConfigSpec("SUPREMEAI_API_KEY", frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}), frozenset({ConfigSource.VAULT, ConfigSource.ENV}), frozenset({"backend"})),
    ConfigSpec("INFISICAL_CLIENT_ID", frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}), frozenset({ConfigSource.ENV, ConfigSource.VAULT}), frozenset({"ci"})),
    ConfigSpec("INFISICAL_CLIENT_SECRET", frozenset({ConfigClass.SECRET, ConfigClass.REQUIRED}), frozenset({ConfigSource.ENV, ConfigSource.VAULT}), frozenset({"ci"})),
    ConfigSpec("INFISICAL_PROJECT_ID", frozenset({ConfigClass.REQUIRED}), frozenset({ConfigSource.ENV, ConfigSource.VAULT}), frozenset({"ci"})),
    ConfigSpec("RENDER_API_KEY", frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}), frozenset({ConfigSource.ENV, ConfigSource.VAULT}), frozenset({"ci"}), required_when="automated Render deployment enabled"),
    ConfigSpec("RENDER_PRIMARY_SVC_ID", frozenset({ConfigClass.CONDITIONAL}), frozenset({ConfigSource.ENV, ConfigSource.VAULT}), frozenset({"ci"}), required_when="primary Render service automation enabled"),
    ConfigSpec("CLOUDFLARE_API_TOKEN", frozenset({ConfigClass.SECRET, ConfigClass.CONDITIONAL}), frozenset({ConfigSource.ENV, ConfigSource.VAULT}), frozenset({"ci"}), required_when="Cloudflare deployment enabled"),
    ConfigSpec("CLOUDFLARE_ACCOUNT_ID", frozenset({ConfigClass.CONDITIONAL}), frozenset({ConfigSource.ENV, ConfigSource.VAULT}), frozenset({"ci"}), required_when="Cloudflare Workers deployment enabled"),
)


BY_NAME: dict[str, ConfigSpec] = {spec.name: spec for spec in CONFIG_SPECS}
ALIAS_TO_CANONICAL: dict[str, str] = {
    alias: spec.name for spec in CONFIG_SPECS for alias in spec.aliases
}


def get_config_spec(name: str) -> ConfigSpec | None:
    """Return canonical metadata, resolving a legacy alias when necessary."""
    canonical = ALIAS_TO_CANONICAL.get(name, name)
    return BY_NAME.get(canonical)


def canonical_name(name: str) -> str:
    return ALIAS_TO_CANONICAL.get(name, name)


def all_config_names() -> set[str]:
    return set(BY_NAME) | set(ALIAS_TO_CANONICAL)
