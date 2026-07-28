"""
Coverage tests for tools/seed_database.py.
Target: 100% line coverage.

কভারেজ টেস্ট — seed_database মডিউলের সকল ফাংশন ও শাখা কভার করা হয়েছে।
"""

import os
import sqlite3
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# ── সিস্টেম পাথে প্রোজেক্ট রুট যোগ করা ──────────────────────────────
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    old_db_path = os.environ.get("DB_PATH")
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestInitFtsDB:
    """Tests for _init_fts_db."""

    def test_init_fts_db_creates_table(self):
        """_init_fts_db should create the FTS virtual table."""
        from tools.seed_database import _init_fts_db

        conn = sqlite3.connect(":memory:")
        _init_fts_db(conn)

        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_fts'")
        assert cursor.fetchone() is not None
        conn.close()


class TestUpsertFTS:
    """Tests for _upsert_fts."""

    def test_upsert_fts_inserts_new_row(self):
        """_upsert_fts should insert a new row."""
        from tools.seed_database import _init_fts_db, _upsert_fts

        conn = sqlite3.connect(":memory:")
        _init_fts_db(conn)
        _upsert_fts(conn, 1, "Test Title", "Test content here", "test_source")

        cursor = conn.execute("SELECT title, content, source FROM knowledge_fts WHERE rowid=1")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "Test Title"
        conn.close()

    def test_upsert_fts_updates_existing_row(self):
        """_upsert_fts should update an existing row."""
        from tools.seed_database import _init_fts_db, _upsert_fts

        conn = sqlite3.connect(":memory:")
        _init_fts_db(conn)
        _upsert_fts(conn, 1, "Original", "Original content", "src1")
        _upsert_fts(conn, 1, "Updated", "Updated content", "src2")

        cursor = conn.execute("SELECT title, content, source FROM knowledge_fts WHERE rowid=1")
        row = cursor.fetchone()
        assert row[0] == "Updated"
        conn.close()


class TestSeedAll:
    """Tests for seed_all."""

    def test_seed_all_no_seed_data_dir(self):
        """seed_all should handle missing seed_data directory gracefully."""
        from tools.seed_database import seed_all

        with patch("tools.seed_database.os.path.exists", return_value=False):
            result = seed_all()
            assert result is None  # Function returns None when dir missing

    def test_seed_all_with_rag_failure(self):
        """seed_all should handle RAG initialization failure."""
        from tools.seed_database import seed_all

        with patch("tools.seed_database.LocalSearchRAG", side_effect=Exception("RAG init failed")):
            with pytest.raises(Exception):
                seed_all()

    def test_seed_all_empty_seed_dir(self):
        """seed_all should process an empty seed directory."""
        from tools.seed_database import seed_all

        with (
            patch("tools.seed_database.os.listdir", return_value=[]),
            patch("tools.seed_database.LocalSearchRAG") as mock_rag,
        ):
            mock_rag_instance = MagicMock()
            mock_rag.return_value = mock_rag_instance
            result = seed_all()
            assert result is not None

    def test_seed_all_skips_init_and_helpers(self):
        """seed_all should skip __init__.py and helpers.py files."""
        from tools.seed_database import seed_all

        with (
            patch("tools.seed_database.os.listdir", return_value=["__init__.py", "helpers.py", "data.py"]),
            patch("tools.seed_database.LocalSearchRAG") as mock_rag,
        ):
            mock_rag_instance = MagicMock()
            mock_rag.return_value = mock_rag_instance
            result = seed_all()
            assert result is not None

    def test_seed_all_module_load_error(self):
        """seed_all should handle module loading errors."""
        from tools.seed_database import seed_all

        with (
            patch("tools.seed_database.os.listdir", return_value=["test_module.py"]),
            patch("tools.seed_database.os.path.exists", return_value=True),
            patch("tools.seed_database.importlib.util.spec_from_file_location", return_value=None),
            patch("tools.seed_database.LocalSearchRAG") as mock_rag,
        ):
            mock_rag_instance = MagicMock()
            mock_rag.return_value = mock_rag_instance
            result = seed_all()
            assert result is not None

    @patch("tools.seed_database.os.path.exists")
    @patch("tools.seed_database.os.listdir")
    @patch("tools.seed_database.LocalSearchRAG")
    def test_seed_all_module_exec_error(self, mock_rag, mock_listdir, mock_exists):
        """seed_all should handle module execution errors."""
        from tools.seed_database import seed_all

        mock_exists.return_value = True
        mock_listdir.return_value = ["broken_module.py"]
        mock_rag_instance = MagicMock()
        mock_rag.return_value = mock_rag_instance

        with patch("tools.seed_database.importlib.util.spec_from_file_location") as mock_spec:
            mock_spec_obj = MagicMock()
            mock_spec_obj.loader = MagicMock()
            mock_spec.return_value = mock_spec_obj
            mock_spec_obj.loader.exec_module.side_effect = ImportError("Module broken")

            result = seed_all()
            assert result is not None


class TestMainFunction:
    """Tests for the main entry point."""

    @patch("tools.seed_database.seed_all")
    def test_main_calls_seed_all(self, mock_seed):
        """Main should call seed_all."""
        from tools.seed_database import main

        main()
        mock_seed.assert_called_once()
