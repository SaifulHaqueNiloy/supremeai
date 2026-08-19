# backend/tests/mcp/test_supabase_mcp.py
# বাংলা মন্তব্য: Supabase MCP টেস্ট
# --- test_mcp_servers_integration.py থেকে স্প্লিট করা হয়েছে ---

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError



class TestSupabaseMCP:
    """supabase_mcp.py এর জন্য টেস্ট ক্লাস।"""

    def test_execute_query_input_validation(self):
        """ExecuteQueryInput মডেলের ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_supabase import ExecuteQueryInput, ResponseFormat

        valid_input = ExecuteQueryInput(
            query="SELECT * FROM users LIMIT 10",
            params=None,
            response_format=ResponseFormat.JSON,
        )
        assert valid_input.query == "SELECT * FROM users LIMIT 10"

    def test_execute_query_input_with_params(self):
        """ExecuteQueryInput প্যারামিটার সহ ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_supabase import ExecuteQueryInput, ResponseFormat

        valid_input = ExecuteQueryInput(
            query="SELECT * FROM users WHERE id = %s",
            params=[1],
            response_format=ResponseFormat.MARKDOWN,
        )
        assert valid_input.params == [1]

    def test_create_table_input_validation(self):
        """CreateTableInput মডেলের ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_supabase import CreateTableInput

        valid_input = CreateTableInput(
            table_name="users",
            columns="id SERIAL PRIMARY KEY, name VARCHAR(100)",
            if_not_exists=True,
        )
        assert valid_input.if_not_exists is True


class TestSupabaseMCPExtended:
    """supabase_mcp.py এর জন্য অতিরিক্ত টেস্ট।"""

    @pytest.mark.asyncio
    async def test_execute_sql_missing_db_url(self, monkeypatch):
        """Execute SQL এ ডাটাবেস URL না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setattr("tools.mcp.mcp_supabase._get_supabase_db_url", lambda: "")
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        params = ExecuteQueryInput(query="SELECT 1", response_format=ResponseFormat.JSON)
        result = await supabase_execute_sql(params)
        data = json.loads(result)
        assert data["error"] == "SUPABASE_DATABASE_URL not configured"

    @pytest.mark.asyncio
    async def test_execute_sql_destructive_without_admin(self, monkeypatch):
        """ডেস্ট্রাকটিভ কুয়েরি অথেন্টিকেশন না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "false")
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        params = ExecuteQueryInput(query="DROP TABLE users", response_format=ResponseFormat.JSON)
        result = await supabase_execute_sql(params)
        data = json.loads(result)
        assert "Admin authorization required" in data["error"]

    @pytest.mark.asyncio
    async def test_execute_sql_destructive_with_admin(self, monkeypatch):
        """ডেস্ট্রাকটিভ কুয়েরি অথেন্টিকেশন সহ সফল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.description = []
            mock_cursor.rowcount = 1
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, commit=MagicMock(), close=MagicMock())

            params = ExecuteQueryInput(query="DROP TABLE users", response_format=ResponseFormat.JSON)
            result = await supabase_execute_sql(params)
            data = json.loads(result)
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_execute_sql_select_json_format(self, monkeypatch):
        """SELECT কুয়েরি JSON ফরম্যাটে রিটার্ন হয়।"""
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [(1, "test"), (2, "test2")]
            mock_cursor.description = [("id",), ("name",)]
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, close=MagicMock())

            params = ExecuteQueryInput(query="SELECT * FROM users", response_format=ResponseFormat.JSON)
            result = await supabase_execute_sql(params)
            data = json.loads(result)
            assert data["row_count"] == 2

    @pytest.mark.asyncio
    async def test_create_table_missing_admin(self, monkeypatch):
        """Create Table এ অথেন্টিকেশন না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "false")
        from tools.mcp.mcp_supabase import CreateTableInput, supabase_create_table

        params = CreateTableInput(table_name="users", columns="id SERIAL PRIMARY KEY", if_not_exists=True)
        result = await supabase_create_table(params)
        data = json.loads(result)
        assert data["error"] == "Admin authorization required for table creation"

    @pytest.mark.asyncio
    async def test_create_table_success(self, monkeypatch):
        """Create Table সফল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_supabase import CreateTableInput, supabase_create_table

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_conn.return_value = MagicMock(cursor=MagicMock(), commit=MagicMock(), close=MagicMock())

            params = CreateTableInput(table_name="users", columns="id SERIAL PRIMARY KEY", if_not_exists=True)
            result = await supabase_create_table(params)
            data = json.loads(result)
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_run_migration_missing_db_url(self, monkeypatch):
        """Run Migration এ ডাটাবেস URL না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setattr("tools.mcp.mcp_supabase._get_supabase_db_url", lambda: "")
        from tools.mcp.mcp_supabase import MigrationInput, supabase_run_migration

        params = MigrationInput(
            migration_name="test",
            up_sql="CREATE TABLE test (id INT)",
            down_sql="DROP TABLE test",
        )
        result = await supabase_run_migration(params)
        data = json.loads(result)
        assert data["error"] == "SUPABASE_DATABASE_URL not configured"

    @pytest.mark.asyncio
    async def test_run_migration_already_applied(self, monkeypatch):
        """মাইগ্রেশন ইতিমধ্যে আপ্লাই করা হয়েছে।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_supabase import MigrationInput, supabase_run_migration

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = [1]
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, commit=MagicMock(), close=MagicMock())

            params = MigrationInput(
                migration_name="test",
                up_sql="CREATE TABLE test (id INT)",
                down_sql="DROP TABLE test",
            )
            result = await supabase_run_migration(params)
            data = json.loads(result)
            assert "already applied" in data["message"]

    @pytest.mark.asyncio
    async def test_run_migration_missing_admin(self, monkeypatch):
        """Run Migration এ অথেন্টিকেশন না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "false")
        from tools.mcp.mcp_supabase import MigrationInput, supabase_run_migration

        params = MigrationInput(
            migration_name="test",
            up_sql="CREATE TABLE test (id INT)",
            down_sql="DROP TABLE test",
        )
        result = await supabase_run_migration(params)
        data = json.loads(result)
        assert data["error"] == "Admin authorization required for migrations"

    @pytest.mark.asyncio
    async def test_list_tables_missing_db_url(self, monkeypatch):
        """List Tables এ ডাটাবেস URL না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setattr("tools.mcp.mcp_supabase._get_supabase_db_url", lambda: "")
        from tools.mcp.mcp_supabase import supabase_list_tables

        result = await supabase_list_tables()
        data = json.loads(result)
        assert data["error"] == "SUPABASE_DATABASE_URL not configured"

    @pytest.mark.asyncio
    async def test_list_tables_success(self, monkeypatch):
        """List Tables সফল হয়।"""
        from tools.mcp.mcp_supabase import supabase_list_tables

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                ("users", "BASE TABLE"),
                ("posts", "BASE TABLE"),
            ]
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, close=MagicMock())

            result = await supabase_list_tables()
            data = json.loads(result)
            assert data["count"] == 2


    def test_create_table_input_if_not_exists_default(self):
        """CreateTableInput এ if_not_exists এর ডিফল্ট মান।"""
        from tools.mcp.mcp_supabase import CreateTableInput

        params = CreateTableInput(table_name="users", columns="id INT")
        assert params.if_not_exists is True


    def test_migration_input_validation(self):
        """MigrationInput এর ইনপুট ভ্যালিডেশন।"""
        from tools.mcp.mcp_supabase import MigrationInput

        with pytest.raises(ValidationError):
            MigrationInput(
                migration_name="",
                up_sql="CREATE TABLE test (id INT)",
                down_sql="DROP TABLE test",
            )

        with pytest.raises(ValidationError):
            MigrationInput(migration_name="test", up_sql="", down_sql="DROP TABLE test")

        with pytest.raises(ValidationError):
            MigrationInput(migration_name="test", up_sql="CREATE TABLE test (id INT)", down_sql="")


    def test_execute_query_input_params_default(self):
        """ExecuteQueryInput এ params ডিফল্ট মান।"""
        from tools.mcp.mcp_supabase import ExecuteQueryInput

        params = ExecuteQueryInput(query="SELECT 1")
        assert params.params == []


    def test_create_table_input_columns_validation(self):
        """CreateTableInput এ columns ভ্যালিডেশন।"""
        from tools.mcp.mcp_supabase import CreateTableInput

        with pytest.raises(ValidationError):
            CreateTableInput(table_name="users", columns="")


    @pytest.mark.asyncio
    async def test_supabase_execute_sql_select_json(self, monkeypatch):
        """SELECT কুয়েরি JSON ফরম্যাটে রিটার্ন।"""
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
            mock_cursor.description = [("id",), ("name",)]
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, close=MagicMock())

            params = ExecuteQueryInput(query="SELECT * FROM users", response_format=ResponseFormat.JSON)
            result = await supabase_execute_sql(params)
            data = json.loads(result)
            assert data["row_count"] == 2
            assert data["columns"] == ["id", "name"]


    @pytest.mark.asyncio
    async def test_supabase_execute_sql_select_markdown(self, monkeypatch):
        """SELECT কুয়েরি Markdown ফরম্যাটে রিটার্ন।"""
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.description = []
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, close=MagicMock())

            params = ExecuteQueryInput(
                query="SELECT * FROM users WHERE id = 1",
                response_format=ResponseFormat.MARKDOWN,
            )
            result = await supabase_execute_sql(params)
            assert "# Query Results" in result


    @pytest.mark.asyncio
    async def test_supabase_execute_sql_insert(self, monkeypatch):
        """INSERT কুয়েরি সফল হয়।"""
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 1
            mock_cursor.description = None
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, commit=MagicMock(), close=MagicMock())

            params = ExecuteQueryInput(
                query="INSERT INTO users (name) VALUES ('Alice')",
                response_format=ResponseFormat.JSON,
            )
            result = await supabase_execute_sql(params)
            data = json.loads(result)
            assert data["success"] is True


    @pytest.mark.asyncio
    async def test_supabase_execute_sql_with_params(self, monkeypatch):
        """Parameterized কুয়েরি সফল হয়।"""
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [(1,)]
            mock_cursor.description = [("id",)]
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, close=MagicMock())

            params = ExecuteQueryInput(
                query="SELECT * FROM users WHERE id = %s",
                params=[1],
                response_format=ResponseFormat.JSON,
            )
            result = await supabase_execute_sql(params)
            data = json.loads(result)
            assert data["row_count"] == 1


    @pytest.mark.asyncio
    async def test_supabase_execute_sql_connection_error(self, monkeypatch):
        """ডাটাবেস কানেকশন ব্যর্থ।"""
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_conn.return_value = None

            params = ExecuteQueryInput(query="SELECT 1", response_format=ResponseFormat.JSON)
            result = await supabase_execute_sql(params)
            data = json.loads(result)
            assert data["error"] == "Failed to connect to database"


    @pytest.mark.asyncio
    async def test_supabase_execute_sql_sql_error(self, monkeypatch):
        """SQL এরর হ্যান্ডল হয়।"""
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = Exception("syntax error at line 1")
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, close=MagicMock())

            params = ExecuteQueryInput(query="SELECT * FROM invalid", response_format=ResponseFormat.JSON)
            result = await supabase_execute_sql(params)
            assert "SQL syntax error" in result


    @pytest.mark.asyncio
    async def test_execute_sql_connection_error(self, monkeypatch):
        """Execute SQL এ কানেকশন এরর।"""
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_conn.return_value = None

            params = ExecuteQueryInput(query="SELECT 1", response_format=ResponseFormat.JSON)
            result = await supabase_execute_sql(params)
            data = json.loads(result)
            assert data["error"] == "Failed to connect to database"


    @pytest.mark.asyncio
    async def test_supabase_execute_sql_no_rows(self, monkeypatch):
        """SELECT কুয়েরি কোন রো রিটার্ন করে না।"""
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.description = []
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, close=MagicMock())

            params = ExecuteQueryInput(
                query="SELECT * FROM empty_table",
                response_format=ResponseFormat.MARKDOWN,
            )
            result = await supabase_execute_sql(params)
            assert "No rows returned" in result


    @pytest.mark.asyncio
    async def test_supabase_execute_sql_rows_limited(self, monkeypatch):
        """SELECT কুয়েরি ১০০ রো-এর বেশি রিটার্ন করে।"""
        from tools.mcp.mcp_supabase import (
            ExecuteQueryInput,
            ResponseFormat,
            supabase_execute_sql,
        )

        rows = [(i, f"name{i}") for i in range(150)]

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = rows
            mock_cursor.description = [("id",), ("name",)]
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, close=MagicMock())

            params = ExecuteQueryInput(
                query="SELECT * FROM large_table",
                response_format=ResponseFormat.MARKDOWN,
            )
            result = await supabase_execute_sql(params)
            assert "Showing 100 of 150 rows" in result


    @pytest.mark.asyncio
    async def test_supabase_create_table_without_if_not_exists(self, monkeypatch):
        """IF NOT EXISTS ছাড়া টেবিল তৈরি।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_supabase import CreateTableInput, supabase_create_table

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_conn.return_value = MagicMock(cursor=MagicMock(), commit=MagicMock(), close=MagicMock())

            params = CreateTableInput(table_name="logs", columns="id SERIAL PRIMARY KEY", if_not_exists=False)
            result = await supabase_create_table(params)
            data = json.loads(result)
            assert data["success"] is True

        """মাইগ্রেশন ইতিমধ্যে আপ্লাই করা হয়েছে (ডিটেইলড)।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_supabase import MigrationInput, supabase_run_migration

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = [1]
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, commit=MagicMock(), close=MagicMock())

            params = MigrationInput(
                migration_name="existing_migration",
                up_sql="CREATE TABLE test (id INT)",
                down_sql="DROP TABLE test",
            )
            result = await supabase_run_migration(params)
            data = json.loads(result)
            assert "already applied" in data["message"]

        """মাইগ্রেশন সফল হলে DOWN SQL এক্সিকিউট হয় না।"""
        from tools.mcp.mcp_supabase import MigrationInput, supabase_run_migration

        with patch("tools.mcp.mcp_supabase._get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.return_value = MagicMock(cursor=lambda: mock_cursor, commit=MagicMock(), close=MagicMock())

            params = MigrationInput(
                migration_name="test",
                up_sql="CREATE TABLE test (id INT)",
                down_sql="DROP TABLE test",
            )
            result = await supabase_run_migration(params)
            data = json.loads(result)
            assert data["success"] is True
