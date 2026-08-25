"""Compression utilities for LLM context optimization."""

# FIX: original used 'from backend.engine.compression.token_juice import ...'
# which only works when CWD is the project root, not when running from backend/.
# Use relative import so it works regardless of CWD.
from .token_juice import CompressionResult, TokenJuice

__all__ = ["TokenJuice", "CompressionResult"]
