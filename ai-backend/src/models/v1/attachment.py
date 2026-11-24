"""Attachment domain entity (attachments table)."""

from enum import Enum
from typing import Any, Mapping, Optional
from src.models.v1.base import DomainModel

ALLOWED_ATTACHMENT_CATEGORIES = [
    "image",
    "document",
    "code",
    "archive",
    "audio",
    "video",
    "other",
]

SUPPORTED_ATTACHMENT_MIME_TYPES = [
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
    "text/x-python",
    "text/javascript",
    "text/typescript",
    "text/html",
    "text/css",
]


class AttachmentStatus(str, Enum):
    READY = "READY"
    ATTACHED = "ATTACHED"
    DELETED = "DELETED"


class AttachmentEntity(DomainModel):
    """Domain entity mirroring the attachments table."""

    id: str
    user_id: Optional[str] = None
    filename: str
    file_size: int
    mime_type: str
    category: str
    status: str = AttachmentStatus.READY.value
    storage_path: Optional[str] = None
    checksum_sha256: Optional[str] = None
    extracted_text: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    prompt_id: Optional[str] = None
    created_at: str = ""
    updated_at: Optional[str] = None

    @property
    def download_url(self) -> str:
        return f"/api/v1/attachments/{self.id}/download"

    @property
    def view_url(self) -> str:
        return f"/api/v1/attachments/{self.id}/view"

    @property
    def extracted_text_preview(self) -> Optional[str]:
        extracted = self.extracted_text or ""
        if len(extracted) > 200:
            return extracted[:200] + "..."
        return extracted or None

    @classmethod
    def from_attachment_row(cls, row: Mapping[str, Any]) -> "AttachmentEntity":
        return cls(
            id=row["id"],
            user_id=row.get("user_id"),
            filename=row["filename"],
            file_size=row.get("file_size") or 0,
            mime_type=row.get("mime_type") or "application/octet-stream",
            category=row.get("category") or "other",
            status=row.get("status") or AttachmentStatus.READY.value,
            storage_path=row.get("storage_path") or row.get("stored_path"),
            checksum_sha256=row.get("checksum_sha256"),
            extracted_text=row.get("extracted_text"),
            image_width=row.get("image_width"),
            image_height=row.get("image_height"),
            conversation_id=row.get("conversation_id"),
            message_id=row.get("message_id"),
            prompt_id=row.get("prompt_id"),
            created_at=str(row.get("created_at") or ""),
            updated_at=str(row["updated_at"]) if row.get("updated_at") is not None else None,
        )
