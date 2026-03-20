"""
File upload validation utilities.

Validates file type, size, and content before storage.
"""

import magic
from typing import BinaryIO
from fastapi import UploadFile, HTTPException, status

from app.config import get_settings


class FileValidationError(Exception):
    """Raised when file validation fails."""

    def __init__(self, message: str, code: str = "invalid_file"):
        self.message = message
        self.code = code
        super().__init__(message)


async def validate_upload_file(
    file: UploadFile,
    allowed_types: list[str] | None = None,
    max_size_mb: int | None = None,
) -> bytes:
    """
    Validate an uploaded file's type and size.

    Args:
        file: The uploaded file from FastAPI
        allowed_types: List of allowed MIME types (uses config default if None)
        max_size_mb: Maximum file size in MB (uses config default if None)

    Returns:
        The file content as bytes

    Raises:
        HTTPException: If validation fails
    """
    settings = get_settings()

    if allowed_types is None:
        allowed_types = settings.allowed_file_types
    if max_size_mb is None:
        max_size_mb = settings.max_upload_size_mb

    # Read file content
    content = await file.read()
    await file.seek(0)  # Reset for potential re-read

    # Validate file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size_mb}MB.",
        )

    # Validate MIME type using python-magic (checks actual file content)
    detected_mime = magic.from_buffer(content, mime=True)

    if detected_mime not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{detected_mime}' is not allowed. Allowed types: {', '.join(allowed_types)}",
        )

    # Also verify the declared content type matches
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Declared content type '{file.content_type}' is not allowed.",
        )

    return content


def validate_file_extension(filename: str, allowed_extensions: list[str] | None = None) -> bool:
    """
    Validate file extension against allowed list.

    Args:
        filename: The filename to check
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.docx'])

    Returns:
        True if extension is allowed
    """
    if allowed_extensions is None:
        # Default allowed extensions based on common file types
        allowed_extensions = [
            ".jpg", ".jpeg", ".png", ".gif", ".webp",  # Images
            ".pdf",  # Documents
            ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",  # Office
            ".txt", ".csv", ".json",  # Text
        ]

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed_extensions


# MIME type to extension mapping
MIME_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "application/json": ".json",
}


def get_extension_for_mime(mime_type: str) -> str:
    """Get file extension for a MIME type."""
    return MIME_TO_EXTENSION.get(mime_type, "")
