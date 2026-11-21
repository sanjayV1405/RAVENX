import os
import hashlib
from typing import Tuple
from app.core.config import settings
from app.core.exceptions import UnsupportedFileTypeError, FileSizeLimitExceededError

# Valid MIME types map
MIME_TYPE_MAP = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def validate_file_metadata(filename: str, file_size: int) -> Tuple[str, str]:
    """
    Validates file extension and size against configured boundaries.
    Returns (clean_extension, resolved_mime_type).
    """
    if not filename or "." not in filename:
        raise UnsupportedFileTypeError(
            extension="unknown",
            allowed=settings.ALLOWED_FILE_EXTENSIONS
        )

    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        raise UnsupportedFileTypeError(
            extension=ext,
            allowed=settings.ALLOWED_FILE_EXTENSIONS
        )

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        max_mb = settings.MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise FileSizeLimitExceededError(max_size_mb=max_mb)

    mime_type = MIME_TYPE_MAP.get(ext, "application/octet-stream")
    return ext, mime_type


def calculate_sha256(data: bytes) -> str:
    """Calculates SHA-256 hash for document integrity validation."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()

