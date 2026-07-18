# backend/api/v1/__init__.py
# 🏗️ Enterprise Execution Plan - Part 3: Telemetry Module Initialization

from .telemetry import router as telemetry_router

__all__ = ["telemetry_router"]
