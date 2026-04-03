"""
utils/file_upload.py
─────────────────────
Local file-upload helper.  Validates MIME type, file size,
saves to UPLOAD_DIR, and returns the relative URL path.
Swap this module's internals for Cloudinary / S3 when needed.
"""

import os
import uuid
from pathlib import Path
from typing import List

import aiofiles
from fastapi import HTTPException, UploadFile

from app.config.settings import settings

# Allowed image MIME types
ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # convert MB → bytes


async def save_upload_file(file: UploadFile, sub_dir: str = "general") -> str:
    """
    Validate and persist an uploaded file.

    Args:
        file:    FastAPI UploadFile object.
        sub_dir: Subdirectory inside UPLOAD_DIR (e.g. 'avatars', 'portfolios').

    Returns:
        Relative URL path like '/uploads/avatars/uuid.jpg'

    Raises:
        HTTPException 400 – invalid type or oversized file.
    """
    # ── Validate content type ──────────────────────────────────────────────
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: {ALLOWED_IMAGE_TYPES}",
        )

    # ── Read content & check size ──────────────────────────────────────────
    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed: {settings.MAX_FILE_SIZE_MB} MB",
        )

    # ── Build destination path ─────────────────────────────────────────────
    ext = Path(file.filename or "upload.jpg").suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest_dir = Path(settings.UPLOAD_DIR) / sub_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    # ── Write to disk ──────────────────────────────────────────────────────
    async with aiofiles.open(dest_path, "wb") as f:
        await f.write(contents)

    return f"/uploads/{sub_dir}/{filename}"


def delete_upload_file(url_path: str) -> None:
    """Remove a previously uploaded file given its URL path."""
    if not url_path:
        return
    # Strip leading slash and join with CWD
    file_path = Path(url_path.lstrip("/"))
    if file_path.exists():
        os.remove(file_path)
