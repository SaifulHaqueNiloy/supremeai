"""Shared secret-strength policy for boot-time and runtime validators.

Issue #542 (BE-10): the JWT secret minimum length previously disagreed
across validators — ``core/config_secrets.py`` required >= 64 bytes when
the secret is first accessed, ``core/config_validator.py`` enforced only a
32-char floor at boot, and ``core/env_validator.py`` had no length check
at all. Boot-time fail-fast therefore used the weakest 32-char floor, so a
40-char secret passed startup validation but raised ``RuntimeError``
mid-request (500s on every authenticated endpoint).

This module is the single source of truth for that floor; every validator
imports the same constant.
"""

JWT_SECRET_MIN_LENGTH = 64
