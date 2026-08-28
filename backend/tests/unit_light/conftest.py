"""Isolated unit-test conftest.

These tests cover small, dependency-light modules (deprecated shims, pure
helpers, rate-limiter logic that is fully mocked). They do NOT require a live
Postgres/Redis, so we override the autouse DB fixtures from the root
``tests/conftest.py`` with no-op stand-ins. This lets the suite run anywhere
without external infrastructure while leaving the rest of the suite untouched.
"""

from unittest.mock import MagicMock

import pytest
import pytest_asyncio


@pytest_asyncio.fixture(scope="session", autouse=True)
async def db_engine():
    yield MagicMock()


@pytest_asyncio.fixture(autouse=True)
async def db_session(db_engine):
    yield MagicMock()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_database(db_session):
    yield
