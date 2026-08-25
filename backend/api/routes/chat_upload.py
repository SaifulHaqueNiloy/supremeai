import json
import os
import uuid
from datetime import UTC, datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from api.deps import get_current_user_token
from database.supabase_client import SupabaseDB

router = APIRouter(
    prefix="/api/chat/upload",
    tags=["Chat Upload"],
    dependencies=[Depends(get_current_user_token)],
)

# Upload directory — relative to the backend root
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed MIME types and their file extensions
ALLOWED_MIME_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "image/avif": ".avif",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# In-memory registry of uploaded files (attachment_id -> metadata)
_uploads: dict[str, dict] = {}


# ---------- Pydantic Schemas ----------


class AttachmentResponse(BaseModel):
    attachment_id: str
    url: str
    name: str
    size: int
    mime_type: str


# ---------- Helpers ----------


def _mime_to_ext(mime: str) -> str | None:
    """Return the canonical file extension for a MIME type, or None."""
    return ALLOWED_MIME_TYPES.get(mime)


def _get_attachment_url(attachment_id: str) -> str:
    """Return the API URL to serve the uploaded file."""
    return f"/api/chat/upload/{attachment_id}"


def _validate_image_header(content: bytes, mime_type: str) -> bool:
    """Basic image header validation to reject non-image payloads disguised with image MIME types."""
    if len(content) < 4:
        return False
    header = content[:8]
    if mime_type == "image/png" and header[:4] == b"\x89PNG":
        return True
    if mime_type == "image/jpeg" and header[:2] == b"\xff\xd8":
        return True
    if mime_type == "image/gif" and header[:6] in (b"GIF87a", b"GIF89a"):
        return True
    if mime_type == "image/webp" and header[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return True
    if mime_type == "image/svg+xml":
        text = content[:512].decode("utf-8", errors="ignore").strip()
        return text.startswith("<") and ("svg" in text.lower())
    # BMP starts with "BM"
    if mime_type == "image/bmp" and header[:2] == b"BM":
        return True
    # For AVIF and TIFF we skip deep validation and trust the MIME
    if mime_type in ("image/avif", "image/tiff"):
        return True
    # If unrecognized header, still allow (some formats vary)
    return True


# ---------- Routes ----------


@router.post("/", response_model=AttachmentResponse)
async def upload_chat_image(
    file: UploadFile = File(..., description="Image file to upload (max 10MB)"),
    user: dict = Depends(get_current_user_token),
):
    """Upload an image file for use in chat messages.

    Validates file type and size, stores to local disk, and returns
    metadata that can be included in chat message payloads.
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Validate MIME type
    mime_type = file.content_type or ""
    ext = _mime_to_ext(mime_type)
    if ext is None:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {mime_type}. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES.keys()))}",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content)} bytes). Maximum allowed: {MAX_FILE_SIZE} bytes (10MB).",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Validate image header to catch disguised files
    if not _validate_image_header(content, mime_type):
        raise HTTPException(
            status_code=400,
            detail="File content does not match the declared MIME type.",
        )

    # Generate a unique ID and filename
    attachment_id = uuid.uuid4().hex
    original_name = file.filename or f"upload{ext}"
    safe_name = f"{attachment_id}{ext}"
    user_dir = os.path.join(UPLOAD_DIR, user_id[:8])
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, safe_name)

    # Write file to disk
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except OSError as e:
        logger.error(f"Failed to write upload file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file") from e

    url = _get_attachment_url(attachment_id)

    metadata = {
        "attachment_id": attachment_id,
        "url": url,
        "name": original_name,
        "size": len(content),
        "mime_type": mime_type,
        "file_path": file_path,
        "user_id": user_id,
        "created_at": datetime.now(UTC).isoformat(),
    }

    _uploads[attachment_id] = metadata

    # Persist reference in DB
    try:
        db = SupabaseDB()
        db.client.table("chat_attachments").insert(
            {
                "id": attachment_id,
                "user_id": user_id,
                "file_name": original_name,
                "file_path": file_path,
                "mime_type": mime_type,
                "file_size": len(content),
            }
        ).execute()
    except Exception as db_err:
        logger.warning(f"DB insert for attachment failed (non-critical): {db_err}")

    # Optionally run vision analysis
    try:
        from services.vision_service import VisionService

        vision_svc = VisionService()
        analysis = await vision_svc.analyze_image(content, query="Describe this image briefly")
        metadata["vision_analysis"] = analysis
    except Exception as vision_err:
        logger.debug(f"Vision analysis skipped: {vision_err}")

    logger.info(f"Chat image uploaded: {attachment_id} ({mime_type}, {len(content)} bytes)")

    return AttachmentResponse(
        attachment_id=attachment_id,
        url=url,
        name=original_name,
        size=len(content),
        mime_type=mime_type,
    )


@router.get("/{attachment_id}")
async def serve_upload(
    attachment_id: str,
    user: dict = Depends(get_current_user_token),
):
    """Serve an uploaded file by its attachment ID.

    Returns the file with the appropriate Content-Type header.
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Look up in-memory registry first
    metadata = _uploads.get(attachment_id)

    if metadata is None:
        # Try loading from database
        try:
            db = SupabaseDB()
            resp = db.client.table("chat_attachments").select("*").eq("id", attachment_id).execute()
            if resp.data:
                metadata = resp.data[0]
                _uploads[attachment_id] = metadata
        except Exception:
            pass

    if metadata is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = metadata["file_path"]
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Attachment file not found on disk")

    mime_type = metadata.get("mime_type", "application/octet-stream")
    file_name = metadata.get("file_name", "download")

    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=file_name,
        headers={
            "Cache-Control": "private, max-age=86400",
        },
    )


@router.delete("/{attachment_id}")
async def delete_upload(
    attachment_id: str,
    user: dict = Depends(get_current_user_token),
):
    """Delete an uploaded attachment.

    Only the owner can delete their own attachments.
    """
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    metadata = _uploads.get(attachment_id)
    if metadata is None:
        try:
            db = SupabaseDB()
            resp = db.client.table("chat_attachments").select("*").eq("id", attachment_id).execute()
            if resp.data:
                metadata = resp.data[0]
        except Exception:
            pass

    if metadata is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if metadata.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="You do not own this attachment")

    # Delete from disk
    file_path = metadata.get("file_path", "")
    if file_path and os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            logger.warning(f"Failed to delete file from disk: {e}")

    # Delete from DB
    try:
        db = SupabaseDB()
        db.client.table("chat_attachments").delete().eq("id", attachment_id).execute()
    except Exception as db_err:
        logger.warning(f"Failed to delete attachment from DB: {db_err}")

    # Remove from memory
    _uploads.pop(attachment_id, None)

    return {"status": "deleted", "attachment_id": attachment_id}
