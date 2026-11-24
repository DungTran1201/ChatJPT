"""Thin HTTP router for File Attachments & Assets (/api/v1/attachments)."""

import io
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from src.core.config import settings
from src.core.security import app_rate_limiter, get_optional_current_user
from src.dependencies import get_attachment_service
from src.schemas.v1.attachments import (
    AttachmentListResponse,
    AttachmentResponse,
    CapabilityResponse,
)
from src.services.attachment_service import AttachmentService, build_content_disposition

attachments_router = APIRouter(prefix="/attachments", tags=["File Attachments & Assets"])


async def _read_upload_with_limit(file: UploadFile, max_bytes: int) -> bytes:
    chunks = []
    total = 0
    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "FILE_TOO_LARGE",
                    "message": f"Dung lượng tệp vượt quá giới hạn tối đa cho phép ({settings.MAX_FILE_SIZE_MB} MB).",
                },
            )
        chunks.append(chunk)
    return b"".join(chunks)


@attachments_router.get("/capabilities", response_model=CapabilityResponse, summary="Truy vấn khả năng xử lý tệp & mô hình hỗ trợ")
async def get_attachment_capabilities(
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    att_service: AttachmentService = Depends(get_attachment_service),
):
    return att_service.get_capabilities()


@attachments_router.post("/upload", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED, summary="Tải lên tệp đính kèm hoặc tài nguyên thư viện")
async def upload_attachment(
    request: Request,
    file: UploadFile = File(...),
    context_type: Optional[str] = Form(None),
    context_id: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    att_service: AttachmentService = Depends(get_attachment_service),
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    app_rate_limiter.check(client_ip)

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    content_bytes = await _read_upload_with_limit(file, max_bytes)
    return att_service.upload(
        user_id=current_user["id"],
        filename=file.filename or "file",
        content_bytes=content_bytes,
        context_type=context_type,
        context_id=context_id,
    )


@attachments_router.get("/", response_model=AttachmentListResponse, summary="Danh sách tệp đính kèm theo bộ lọc")
@attachments_router.get("", response_model=AttachmentListResponse, include_in_schema=False)
async def list_attachments(
    conversation_id: Optional[str] = Query(None),
    prompt_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    att_service: AttachmentService = Depends(get_attachment_service),
):
    return att_service.list_attachments(
        user_id=current_user["id"],
        conversation_id=conversation_id,
        prompt_id=prompt_id,
        status_filter=status_filter,
    )


@attachments_router.get("/{attachment_id}", response_model=AttachmentResponse, summary="Lấy thông tin chi tiết tệp đính kèm")
async def get_attachment_detail(
    attachment_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    att_service: AttachmentService = Depends(get_attachment_service),
):
    return att_service.get_detail(attachment_id, current_user["id"])


@attachments_router.get("/{attachment_id}/download", summary="Tải xuống tệp nhị phân gốc an toàn")
async def download_attachment(
    attachment_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    att_service: AttachmentService = Depends(get_attachment_service),
):
    raw_bytes, mime, filename = att_service.load_binary(attachment_id, current_user["id"], inline=False)
    return StreamingResponse(
        io.BytesIO(raw_bytes),
        media_type=mime,
        headers={
            "Content-Disposition": build_content_disposition("attachment", filename),
            "Content-Length": str(len(raw_bytes)),
            "X-Content-Type-Options": "nosniff",
        },
    )


@attachments_router.get("/{attachment_id}/view", summary="Xem nội dung tệp trực tiếp trong trình duyệt (Preview inline)")
async def view_attachment(
    attachment_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    att_service: AttachmentService = Depends(get_attachment_service),
):
    raw_bytes, mime, filename = att_service.load_binary(attachment_id, current_user["id"], inline=True)
    return StreamingResponse(
        io.BytesIO(raw_bytes),
        media_type=mime,
        headers={
            "Content-Disposition": build_content_disposition("inline", filename),
            "Content-Length": str(len(raw_bytes)),
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline';",
        },
    )


@attachments_router.delete("/{attachment_id}", summary="Xóa tệp đính kèm")
async def delete_attachment(
    attachment_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_current_user),
    att_service: AttachmentService = Depends(get_attachment_service),
):
    return att_service.delete(attachment_id, current_user["id"])
