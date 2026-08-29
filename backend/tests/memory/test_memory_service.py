import json
import os
import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from services.memory_service import CascadeMemoryService

pytestmark = pytest.mark.memory


class TestCascadeMemoryService:
    @pytest.mark.unit
    def test_cascade_memory_service_sqlite_fallback(self, tmp_path):
        db_file = tmp_path / "memory.db"
        service = CascadeMemoryService(db_path=str(db_file))
        assert not service._use_pg

        service.store_memory(
            file_path="test.py", content="def test(): pass", summary="test summary", structure="{}"
        )

        # Verify it was inserted in sqlite
        with sqlite3.connect(service.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT summary, content FROM file_memories WHERE file_path = 'test.py'")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "test summary"
            assert row[1] == "def test(): pass"

    @pytest.mark.unit
    @patch("services.memory_service.pooled_pg")
    def test_cascade_memory_service_pgvector(self, mock_pooled_pg):
        mock_pooled_pg.is_available.return_value = True

        service = CascadeMemoryService()
        assert service._use_pg

        # Verify schema execution for ai_memory
        assert mock_pooled_pg.execute.called
        call_args = mock_pooled_pg.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS ai_memory" in call_args
        assert "embedding TEXT" in call_args
        assert "metadata JSONB" in call_args

    @pytest.mark.unit
    @patch("services.memory_service.pooled_pg")
    def test_store_memory_pg_insert(self, mock_pooled_pg):
        mock_pooled_pg.is_available.return_value = True

        service = CascadeMemoryService()

        service.store_memory(
            file_path="test.py", content="def test(): pass", summary="test summary", structure="{}"
        )

        # Check if execute was called to insert
        execute_calls = mock_pooled_pg.execute.call_args_list
        insert_called = False
        for call in execute_calls:
            query = call[0][0]
            if "INSERT INTO ai_memory" in query or "UPDATE ai_memory" in query:
                insert_called = True

        assert insert_called, "Should execute an INSERT/UPDATE on ai_memory"
