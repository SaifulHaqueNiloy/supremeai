"""Unit tests for UnifiedDBManager in SupremeAI 2.0."""

import pytest
from unittest.mock import AsyncMock

from memory.unified_db_manager import UnifiedDBManager


@pytest.fixture
def mock_stores():
    sqlite_mock = AsyncMock()
    sqlite_mock.save = AsyncMock(return_value=True)
    sqlite_mock.get = AsyncMock(return_value={"id": "rec-1", "value": "test_data"})
    sqlite_mock.delete = AsyncMock(return_value=True)

    supabase_mock = AsyncMock()
    supabase_mock.insert = AsyncMock(return_value=True)
    supabase_mock.fetch_by_id = AsyncMock(return_value={"id": "rec-1", "value": "cloud_data"})
    supabase_mock._provider = "sqlite"

    chroma_mock = AsyncMock()
    chroma_mock.add_document = AsyncMock(return_value=True)

    postgres_mock = AsyncMock()
    postgres_mock.execute_query = AsyncMock(return_value=True)

    return {
        "sqlite": sqlite_mock,
        "supabase": supabase_mock,
        "chroma": chroma_mock,
        "postgres": postgres_mock,
    }


@pytest.mark.asyncio
async def test_unified_db_save_record_all_success(mock_stores):
    manager = UnifiedDBManager(
        sqlite_store=mock_stores["sqlite"],
        supabase_store=mock_stores["supabase"],
        chroma_store=mock_stores["chroma"],
        postgres_store=mock_stores["postgres"],
    )

    results = await manager.save_record(
        collection="users",
        record_id="usr-123",
        data={"name": "Alice", "role": "admin"},
        text_content="User Alice administrator profile",
    )

    assert results["sqlite"] is True
    assert results["supabase"] is True
    assert results["postgres"] is True
    assert results["chroma"] is True
    mock_stores["sqlite"].save.assert_called_once_with("users", "usr-123", {"name": "Alice", "role": "admin"})


@pytest.mark.asyncio
async def test_unified_db_save_record_invalid_collection_name(mock_stores):
    manager = UnifiedDBManager(
        sqlite_store=mock_stores["sqlite"],
        supabase_store=mock_stores["supabase"],
        chroma_store=mock_stores["chroma"],
        postgres_store=mock_stores["postgres"],
    )

    with pytest.raises(ValueError, match="Invalid collection name"):
        await manager.save_record(
            collection="users; DROP TABLE users;",
            record_id="usr-123",
            data={"name": "Attacker"},
        )


@pytest.mark.asyncio
async def test_unified_db_get_record_sqlite_hit(mock_stores):
    manager = UnifiedDBManager(
        sqlite_store=mock_stores["sqlite"],
        supabase_store=mock_stores["supabase"],
        chroma_store=mock_stores["chroma"],
        postgres_store=mock_stores["postgres"],
    )

    record = await manager.get_record("users", "rec-1")
    assert record == {"id": "rec-1", "value": "test_data"}
    mock_stores["sqlite"].get.assert_called_once_with("users", "rec-1")
    mock_stores["supabase"].fetch_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_unified_db_get_record_sqlite_miss_supabase_hit(mock_stores):
    mock_stores["sqlite"].get.return_value = None
    manager = UnifiedDBManager(
        sqlite_store=mock_stores["sqlite"],
        supabase_store=mock_stores["supabase"],
        chroma_store=mock_stores["chroma"],
        postgres_store=mock_stores["postgres"],
    )

    record = await manager.get_record("users", "rec-1")
    assert record == {"id": "rec-1", "value": "cloud_data"}
    mock_stores["sqlite"].get.assert_called_once_with("users", "rec-1")
    mock_stores["supabase"].fetch_by_id.assert_called_once_with("users", "rec-1")


@pytest.mark.asyncio
async def test_unified_db_delete_record(mock_stores):
    manager = UnifiedDBManager(
        sqlite_store=mock_stores["sqlite"],
        supabase_store=mock_stores["supabase"],
        chroma_store=mock_stores["chroma"],
        postgres_store=mock_stores["postgres"],
    )

    results = await manager.delete_record("users", "rec-1")
    assert results["sqlite"] is True
    assert results["postgres"] is True


@pytest.mark.asyncio
async def test_unified_db_health_check(mock_stores):
    manager = UnifiedDBManager(
        sqlite_store=mock_stores["sqlite"],
        supabase_store=mock_stores["supabase"],
        chroma_store=mock_stores["chroma"],
        postgres_store=mock_stores["postgres"],
    )

    health = await manager.health_check()
    assert health["status"] == "healthy"
    assert health["sqlite"] is True
