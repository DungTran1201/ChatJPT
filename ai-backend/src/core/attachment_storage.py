"""Backward-compatibility facade delegating to src.core.storage."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.core.storage import (
    BLOCKED_EXTENSIONS,
    CODE_EXTENSIONS,
    DOC_EXTENSIONS,
    IMAGE_EXTENSIONS,
    FileSecurityValidator,
    LocalAttachmentStorage,
    TextExtractor,
    default_storage,
)


def get_upload_base_dir() -> Path:
    return default_storage.get_base_dir()


def sanitize_filename(filename: str) -> str:
    return FileSecurityValidator.sanitize_filename(filename)


def classify_file(content_bytes: bytes, filename: str) -> Tuple[str, str]:
    return FileSecurityValidator.classify(content_bytes, filename)


def extract_text_from_file(
    content_bytes: bytes,
    category: str,
    mime_type: str,
    filename: str,
) -> Optional[str]:
    return TextExtractor.extract(content_bytes, category, mime_type, filename)


def save_attachment_file(
    user_id: str,
    raw_filename: str,
    content_bytes: bytes,
) -> Dict[str, Any]:
    return default_storage.save(user_id, raw_filename, content_bytes)


def get_attachment_absolute_path(storage_path: str) -> Path:
    return default_storage.resolve_safe_path(storage_path)


def read_attachment_bytes(storage_path: str) -> bytes:
    return default_storage.read_bytes(storage_path)


def delete_attachment_file(storage_path: str) -> bool:
    return default_storage.delete(storage_path)


__all__ = [
    "BLOCKED_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "CODE_EXTENSIONS",
    "DOC_EXTENSIONS",
    "FileSecurityValidator",
    "TextExtractor",
    "LocalAttachmentStorage",
    "default_storage",
    "get_upload_base_dir",
    "sanitize_filename",
    "classify_file",
    "extract_text_from_file",
    "save_attachment_file",
    "get_attachment_absolute_path",
    "read_attachment_bytes",
    "delete_attachment_file",
]
