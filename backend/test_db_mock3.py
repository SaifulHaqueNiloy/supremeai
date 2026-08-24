import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.core.health_check import ComprehensiveHealthChecker, HealthStatus


async def main():
    checker = ComprehensiveHealthChecker()
    mock_engine = MagicMock()
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = None
    mock_engine.connect.return_value = mock_conn

    with (
        patch("database.session.init_engine"),
        patch("database.session._engine_instance", mock_engine),
    ):
        result = await checker.check_database()
        print(f"Status: {result.status}")
        print(f"Message: {result.message}")


asyncio.run(main())
