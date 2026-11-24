"""Attachments & File Capability API schemas."""

from typing import List, Optional
from pydantic import BaseModel
from src.models.v1.attachment import AttachmentEntity


class AttachmentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    mime_type: str
    category: str
    status: str
    checksum_sha256: Optional[str] = None
    extracted_text: Optional[str] = None
    created_at: str
    download_url: str
    view_url: str
    extracted_text_preview: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    prompt_id: Optional[str] = None

    @classmethod
    def from_entity(cls, entity: AttachmentEntity) -> "AttachmentResponse":
        return cls(
            id=entity.id,
            filename=entity.filename,
            file_size=entity.file_size,
            mime_type=entity.mime_type,
            category=entity.category,
            status=entity.status,
            checksum_sha256=entity.checksum_sha256,
            extracted_text=entity.extracted_text,
            created_at=entity.created_at,
            download_url=entity.download_url,
            view_url=entity.view_url,
            extracted_text_preview=entity.extracted_text_preview,
            image_width=entity.image_width,
            image_height=entity.image_height,
            conversation_id=entity.conversation_id,
            message_id=entity.message_id,
            prompt_id=entity.prompt_id,
        )


class AttachmentListResponse(BaseModel):
    items: List[AttachmentResponse]
    total: int


class ModelCapability(BaseModel):
    model_id: str
    provider: str
    supports_images: bool
    supports_pdf_native: bool
    supports_text_documents: bool
    max_file_size_mb: int


class CapabilityResponse(BaseModel):
    default_provider: str
    max_file_size_mb: int
    max_files_per_request: int
    allowed_categories: List[str]
    supported_mime_types: List[str]
    models: List[ModelCapability]
