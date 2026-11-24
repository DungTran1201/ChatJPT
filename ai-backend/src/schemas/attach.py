"""Backward-compatibility re-export shim for src.schemas.v1.attachments."""

from src.schemas.v1.attachments import (
    AttachmentResponse,
    AttachmentListResponse,
    ModelCapability,
    CapabilityResponse,
)

__all__ = [
    "AttachmentResponse",
    "AttachmentListResponse",
    "ModelCapability",
    "CapabilityResponse",
]
