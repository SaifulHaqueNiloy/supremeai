"""Shared fixtures for misc tests."""

import pytest
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_supabase_execute_sql(monkeypatch):
    """Mock Supabase database connections for unit tests to prevent CI relation errors."""
    
    # Mock supabase_execute_sql (used by SkillManager)
    async def mock_execute_sql(*args, **kwargs):
        return '{"rows": []}'
    
    try:
        monkeypatch.setattr("core.skill_manager.supabase_execute_sql", mock_execute_sql)
    except Exception:
        pass
        
    # Mock _get_connection (used by UniversalRulesEngine)
    def mock_get_connection():
        # Returns a mock connection that returns no rows for any query
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cur
        return mock_conn

    try:
        monkeypatch.setattr("core.universal_rules._get_connection", mock_get_connection)
    except Exception:
        pass
