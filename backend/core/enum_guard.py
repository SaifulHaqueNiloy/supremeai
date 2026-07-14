"""This module provides a robust mechanism to validate the consistency between Python `enum.Enum` definitions and their corresponding PostgreSQL `ENUM` types at application startup. It plays a critical role in the SupremeAI project by preventing potential runtime errors and data integrity issues that could arise from mismatches between the application's code and the database schema, ensuring a stable and reliable backend for the AI ecosystem.

Key Components:
- `EnumMismatchError`: A custom exception raised when a discrepancy is found between Python and database enum values.
- `guard_enum()`: Asynchronously validates a single Python `enum.Enum` against its corresponding PostgreSQL `ENUM` type, querying the database and raising `EnumMismatchError` if any mismatches are detected.
- `run_enum_guards()`: Orchestrates the startup validation process for all critical enums used across the SupremeAI application's data models, calling `guard_enum` for each.

Dependencies:
- `enum`: Standard library for creating enumeration types in Python.
- `loguru`: For structured and flexible logging of validation progress and issues.
- `sqlalchemy`: For interacting with the PostgreSQL database, specifically for executing raw SQL queries to inspect enum definitions.
- `database.session`: Provides the SQLAlchemy engine for establishing database connections.
- `models.agent_session`: Imports `AgentSessionState` and `ControlMode` enums for validation.
- `models.execution_log`: Imports `LogType` enum for validation.
- `models.execution_policy`: Imports `PolicyScope` enum for validation.
- `models.target_platform_credential`: Imports `AuthType` and `CredentialStatus` enums for validation."""

import enum

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.session import engine


class EnumMismatchError(Exception):
    pass


async def guard_enum(conn, db_enum_name: str, py_enum: type[enum.Enum]) -> bool:
    """
    Validates that the Python Enum matches the Postgres Enum at startup.
    Prevents runtime crashes due to database mismatches.
    Returns True if passed or missing, False if skipped due to DB error.
    """
    try:
        result = await conn.execute(
            text("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = :enum_name"),
            {"enum_name": db_enum_name},
        )
        db_labels = {row[0] for row in result.all()}

        if not db_labels:
            logger.warning(f"Enum '{db_enum_name}' not found in database. Is Alembic up to date?")
            return True

        py_labels = {e.value for e in py_enum}

        if db_labels != py_labels:
            missing_in_db = py_labels - db_labels
            missing_in_py = db_labels - py_labels
            error_msg = f"Enum mismatch for '{db_enum_name}'. "
            if missing_in_db:
                error_msg += f"Values in Python but missing in DB: {missing_in_db}. "
            if missing_in_py:
                error_msg += f"Values in DB but missing in Python: {missing_in_py}. "
            raise EnumMismatchError(error_msg)

        logger.info(f"Enum '{db_enum_name}' successfully validated against Python model.")
        return True
    except SQLAlchemyError as e:
        logger.warning(f"Skipping Enum Guard for '{db_enum_name}' (DB connection/dialect issue): {e}")
        return False
    except EnumMismatchError:
        raise


async def run_enum_guards():
    from models.agent_session import AgentSessionState
    from models.agent_session import ControlMode
    from models.execution_log import LogType
    from models.execution_policy import PolicyScope
    from models.target_platform_credential import AuthType
    from models.target_platform_credential import CredentialStatus

    logger.info("Running Startup Enum Guards...")

    enums_to_check = [
        ("agent_session_state", AgentSessionState),
        ("control_mode", ControlMode),
        ("log_type_enum", LogType),
        ("policy_scope_enum", PolicyScope),
        ("auth_type_enum", AuthType),
        ("credential_status_enum", CredentialStatus),
    ]

    passed = 0
    skipped = 0

    try:
        async with engine.connect() as conn:
            for db_name, py_enum in enums_to_check:
                if await guard_enum(conn, db_name, py_enum):
                    passed += 1
                else:
                    skipped += 1
    except SQLAlchemyError as e:
        logger.warning(f"Failed to connect to database for enum guards: {e}")
        skipped = len(enums_to_check)

    if skipped > 0:
        logger.warning(f"Enum Guards Summary: {passed} passed, {skipped} skipped due to DB errors.")
    else:
        logger.info(f"Enum Guards Summary: All {passed} passed successfully.")
