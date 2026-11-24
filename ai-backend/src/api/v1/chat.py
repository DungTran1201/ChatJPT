"""Chat Streaming & Speech-to-Text (STT) API router — thin HTTP/SSE controller."""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import StreamingResponse

from src.core.exceptions import PayloadTooLargeError
from src.core.security import app_rate_limiter, get_current_user
from src.dependencies import get_chat_service
from src.schemas.v1.chat import MessageStreamRequest
from src.services.chat_service import MAX_STT_AUDIO_BYTES, ChatService

chat_router = APIRouter(tags=["Chat Streaming"])


async def _read_bounded_audio(file: UploadFile, max_bytes: int) -> bytes:
    chunks = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise PayloadTooLargeError(
                "Tệp âm thanh vượt quá giới hạn 10MB cho phép.",
                error_code="FILE_TOO_LARGE",
                structured=True,
            )
        chunks.append(chunk)
    return b"".join(chunks)


@chat_router.post("/conversations/{conversation_id}/messages/stream")
async def stream_message_endpoint(
    conversation_id: str,
    req: MessageStreamRequest,
    raw_request: Request,
    current_user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    client_ip = raw_request.client.host if raw_request.client else "127.0.0.1"
    app_rate_limiter.check(client_ip)

    ctx = service.prepare_stream(
        conversation_id=conversation_id,
        req=req,
        current_user=current_user,
    )
    return StreamingResponse(
        service.stream_events(ctx),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@chat_router.post("/chat/stt", summary="Chuyển đổi âm thanh giọng nói thành văn bản (STT) đa ngữ")
async def speech_to_text_endpoint(
    file: UploadFile = File(..., description="Tệp âm thanh WebM, WAV, OGG, MP4"),
    language: Optional[str] = Form("auto", description="Ngôn ngữ gợi ý: vi, en, ja, auto"),
    duration_ms: Optional[int] = Form(0, description="Thời lượng thu âm (ms)"),
    current_user: dict = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    content_bytes = await _read_bounded_audio(file, MAX_STT_AUDIO_BYTES)
    return await service.transcribe_voice_upload(
        user_id=current_user["id"],
        filename=file.filename or "voice.webm",
        content_bytes=content_bytes,
        language=language,
        duration_ms=duration_ms,
    )
