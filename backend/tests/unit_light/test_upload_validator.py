"""Tests for core.upload_validator — pure file-upload validation (FastAPI HTTPException)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from core.upload_validator import MAX_UPLOAD_BYTES, UploadValidationError, validate_upload


def _make_file(filename, content_type, body):
    f = MagicMock()
    f.filename = filename
    f.content_type = content_type
    f.read = AsyncMock(return_value=body)
    f.seek = AsyncMock()
    return f


@pytest.mark.asyncio
async def test_valid_upload():
    f = _make_file("script.py", "text/x-python", b"print('hi')")
    await validate_upload(f)
    f.seek.assert_awaited_with(0)


@pytest.mark.asyncio
async def test_missing_extension_rejected():
    f = _make_file("noextension", "text/plain", b"x")
    with pytest.raises(UploadValidationError):
        await validate_upload(f)


@pytest.mark.asyncio
async def test_disallowed_extension_rejected():
    f = _make_file("evil.exe", "application/octet-stream", b"x")
    with pytest.raises(UploadValidationError):
        await validate_upload(f)


@pytest.mark.asyncio
async def test_content_type_mismatch_rejected():
    f = _make_file("script.py", "image/png", b"x")
    with pytest.raises(UploadValidationError):
        await validate_upload(f)


@pytest.mark.asyncio
async def test_too_large_rejected():
    f = _make_file("big.py", "text/x-python", b"x" * (MAX_UPLOAD_BYTES + 1))
    with pytest.raises(HTTPException) as exc:
        await validate_upload(f)
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_empty_content_type_allowed_when_in_list():
    # content_type empty -> skip mismatch check, only size is validated.
    f = _make_file("ok.py", "", b"small")
    await validate_upload(f)
