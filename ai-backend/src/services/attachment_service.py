"""Attachment application service (SRP, DIP, rollback-on-DB-failure, strict Anti-IDOR)."""

from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote

from src.core.config import settings
from src.core.exceptions import NotFoundError, ValidationDomainError
from src.core.storage import LocalAttachmentStorage, default_storage
from src.models.v1.attachment import (
    ALLOWED_ATTACHMENT_CATEGORIES,
    SUPPORTED_ATTACHMENT_MIME_TYPES,
    AttachmentEntity,
)
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.conversation_repo import ConversationRepository
from src.repositories.prompt_repo import PromptRepository
from src.schemas.v1.attachments import (
    AttachmentListResponse,
    AttachmentResponse,
    CapabilityResponse,
    ModelCapability,
)


def _classify_storage_error_code(err_str: str) -> str:
    if "thực thi" in err_str or "script" in err_str or "Binary Executable" in err_str:
        return "EXECUTABLE_FILE_BLOCKED"
    if "rỗng" in err_str:
        return "EMPTY_FILE"
    if "vượt quá" in err_str:
        return "FILE_TOO_LARGE"
    if "MIME" in err_str or "định dạng" in err_str:
        return "UNSUPPORTED_MEDIA_TYPE"
    return "FILE_PROCESSING_FAILED"


def build_content_disposition(disposition: str, filename: str) -> str:
    """RFC 5987 safe header avoiding Starlette Latin-1 encoding crashes on UTF-8 filenames."""
    ascii_fallback = filename.encode("ascii", "ignore").decode("ascii").replace('"', "_") or "file"
    utf8_encoded = quote(filename, safe="")
    return f'{disposition}; filename="{ascii_fallback}"; filename*=UTF-8\'\'{utf8_encoded}'


class AttachmentService:
    """Orchestrates file validation, disk storage, DB persistence, and secure download/view."""

    def __init__(
        self,
        att_repo: AttachmentRepository,
        conv_repo: ConversationRepository,
        prompt_repo: PromptRepository,
        storage: Optional[LocalAttachmentStorage] = None,
    ):
        self._atts = att_repo
        self._convs = conv_repo
        self._prompts = prompt_repo
        self._storage = storage or default_storage

    def get_capabilities(self) -> CapabilityResponse:
        return CapabilityResponse(
            default_provider=settings.DEFAULT_LLM_PROVIDER or "gemini",
            max_file_size_mb=settings.MAX_FILE_SIZE_MB,
            max_files_per_request=settings.MAX_FILES_PER_REQUEST,
            allowed_categories=ALLOWED_ATTACHMENT_CATEGORIES,
            supported_mime_types=SUPPORTED_ATTACHMENT_MIME_TYPES,
            models=[
                ModelCapability(
                    model_id="gemini-3.8-flash",
                    provider="google",
                    supports_images=True,
                    supports_pdf_native=True,
                    supports_text_documents=True,
                    max_file_size_mb=settings.MAX_FILE_SIZE_MB,
                ),
                ModelCapability(
                    model_id="gemini-3.5-flash-lite",
                    provider="google",
                    supports_images=True,
                    supports_pdf_native=True,
                    supports_text_documents=True,
                    max_file_size_mb=settings.MAX_FILE_SIZE_MB,
                ),
                ModelCapability(
                    model_id="gpt-4o-mini",
                    provider="openai",
                    supports_images=True,
                    supports_pdf_native=False,
                    supports_text_documents=True,
                    max_file_size_mb=settings.MAX_FILE_SIZE_MB,
                ),
            ],
        )

    def upload(
        self,
        *,
        user_id: str,
        filename: str,
        content_bytes: bytes,
        context_type: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> AttachmentResponse:
        conversation_id = None
        prompt_id = None

        if context_type == "chat" and context_id:
            if not self._convs.get_owned(context_id, user_id):
                raise NotFoundError("Cuộc trò chuyện không tồn tại hoặc bạn không có quyền.")
            conversation_id = context_id
        elif context_type in ("system_prompt", "prompt") and context_id:
            if not self._prompts.get_owned(context_id, user_id):
                raise NotFoundError("System Prompt không tồn tại hoặc bạn không có quyền.")
            prompt_id = context_id

        try:
            file_meta = self._storage.save(user_id, filename or "file", content_bytes)
        except ValueError as val_err:
            err_str = str(val_err)
            raise ValidationDomainError(
                err_str,
                error_code=_classify_storage_error_code(err_str),
                structured=True,
            )

        try:
            created_row = self._atts.create(
                user_id=user_id,
                file_meta=file_meta,
                conversation_id=conversation_id,
                prompt_id=prompt_id,
            )
        except Exception:
            self._storage.delete(file_meta["storage_path"])
            raise

        return AttachmentResponse.from_entity(AttachmentEntity.from_attachment_row(created_row))

    def list_attachments(
        self,
        *,
        user_id: str,
        conversation_id: Optional[str] = None,
        prompt_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> AttachmentListResponse:
        rows = self._atts.list_filtered(
            user_id=user_id,
            conversation_id=conversation_id,
            prompt_id=prompt_id,
            status_filter=status_filter,
        )
        items = [AttachmentResponse.from_entity(AttachmentEntity.from_attachment_row(r)) for r in rows]
        return AttachmentListResponse(items=items, total=len(items))

    def get_detail(self, attachment_id: str, user_id: str) -> AttachmentResponse:
        row = self._atts.get_owned(attachment_id, user_id)
        if not row:
            raise NotFoundError("Tệp không tồn tại hoặc bạn không có quyền truy cập.")
        return AttachmentResponse.from_entity(AttachmentEntity.from_attachment_row(row))

    def load_binary(self, attachment_id: str, user_id: str, *, inline: bool = False) -> Tuple[bytes, str, str]:
        row = self._atts.get_owned(attachment_id, user_id)
        if not row:
            raise NotFoundError("Tệp không tồn tại hoặc bạn không có quyền truy cập.")
        storage_path = row.get("storage_path") or row.get("stored_path") or ""
        try:
            raw_bytes = self._storage.read_bytes(storage_path)
        except Exception as exc:
            raise NotFoundError(f"Không thể đọc nội dung tệp lưu trữ: {exc}")

        mime = row["mime_type"]
        if inline and mime in ("text/html", "image/svg+xml", "application/xhtml+xml"):
            mime = "text/plain"
        return raw_bytes, mime, row["filename"]

    def delete(self, attachment_id: str, user_id: str) -> Dict[str, Any]:
        row = self._atts.get_owned(attachment_id, user_id, include_deleted=True)
        if not row:
            raise NotFoundError("Tệp không tồn tại hoặc bạn không có quyền xóa.")

        storage_path = row.get("storage_path") or row.get("stored_path")
        if storage_path:
            self._storage.delete(storage_path)
        self._atts.delete(attachment_id, user_id)
        return {
            "id": attachment_id,
            "deleted": True,
            "message": "Đã xóa tệp đính kèm thành công.",
        }
