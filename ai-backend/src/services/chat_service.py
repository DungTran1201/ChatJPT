"""Chat Application Service (Facade).

Coordinates daily token quota checks, Anti-IDOR ownership validation, attachment binding,
sliding-window history, Sensei pedagogical prompt construction, SSE streaming via
ChatAgentOrchestrator, Semantic Cache learning, telemetry logging, and STT voice upload.
"""

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

from src.core.exceptions import (
    BadRequestError,
    NotFoundError,
    PayloadTooLargeError,
    QuotaExceededError,
    ValidationDomainError,
)
from src.core.storage import LocalAttachmentStorage, default_storage
from src.core.telemetry import metric_logger, quota_manager
from src.repositories.attachment_repo import AttachmentRepository
from src.repositories.conversation_repo import ConversationRepository
from src.repositories.model_repo import ModelRepository
from src.repositories.prompt_repo import PromptRepository
from src.repositories.rule_repo import RuleRepository
from src.schemas.v1.chat import MessageStreamRequest
from src.services.prompt_builder import PedagogicalPromptBuilder
from src.services.provider_registry import redact_secrets_from_text
from src.services.stt_service import STTService

MAX_STT_AUDIO_BYTES = 10 * 1024 * 1024  # 10MB (BR-048, SEC-021)


@dataclass
class PreparedChatStream:
    conversation_id: str
    user_id: str
    prompt_text: str
    selected_model: str
    context_messages: List[Dict[str, Any]]
    attachment_records: List[Dict[str, Any]]
    system_instruction: str
    sensei_id: Optional[str]
    sensei_voice_id: Optional[str]


class ChatService:
    """Facade orchestrating chat SSE streaming and voice STT ingestion."""

    def __init__(
        self,
        *,
        conv_repo: ConversationRepository,
        att_repo: AttachmentRepository,
        model_repo: ModelRepository,
        prompt_repo: PromptRepository,
        rule_repo: RuleRepository,
        prompt_builder: Optional[PedagogicalPromptBuilder] = None,
        stt_service: Optional[STTService] = None,
        storage: Optional[LocalAttachmentStorage] = None,
    ):
        self._convs = conv_repo
        self._atts = att_repo
        self._models = model_repo
        self._prompts = prompt_repo
        self._rules = rule_repo
        self._prompt_builder = prompt_builder or PedagogicalPromptBuilder()
        self._stt = stt_service or STTService()
        self._storage = storage or default_storage

    def prepare_stream(
        self,
        *,
        conversation_id: str,
        req: MessageStreamRequest,
        current_user: Dict[str, Any],
    ) -> PreparedChatStream:
        user_id = current_user["id"]

        # 0. Daily token quota check (BR-020, CTRL-008)
        is_allowed, used_tokens, limit_tokens, _ = quota_manager.check_quota(user_id, estimated_tokens=100)
        if not is_allowed:
            metric_logger.log_metric(
                endpoint=f"/api/v1/conversations/{conversation_id}/messages/stream",
                method="POST",
                status_code=429,
                latency_ms=1.0,
                user_id=user_id,
                error_code="DAILY_QUOTA_EXCEEDED",
            )
            now_dt = datetime.now(timezone.utc)
            reset_dt = (now_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            retry_after_secs = int((reset_dt - now_dt).total_seconds())
            raise QuotaExceededError(
                f"Hạn ngạch token trong ngày đã hết ({used_tokens:,}/{limit_tokens:,} tokens). "
                "Yêu cầu bị chặn (HTTP 429). Hạn ngạch sẽ được làm mới lúc 00:00 UTC.",
                error_code="DAILY_QUOTA_EXCEEDED",
                extra={
                    "daily_tokens_used": used_tokens,
                    "daily_token_limit": limit_tokens,
                    "retry_after": retry_after_secs,
                },
                headers={"Retry-After": str(retry_after_secs)},
                structured=True,
            )

        # 1. Anti-IDOR conversation ownership check (BR-002)
        conv = self._convs.get_owned(conversation_id, user_id)
        if not conv:
            raise NotFoundError("Cuộc trò chuyện không tồn tại hoặc bạn không có quyền truy cập.")

        # 2. Validate prompt length / attachment presence (INV-02, BR-003)
        prompt_text = req.content.strip()
        if not prompt_text and not req.attachments:
            raise ValidationDomainError("Nội dung tin nhắn phải từ 1 đến 4000 ký tự hoặc có tệp đính kèm.")
        if not prompt_text and req.attachments:
            prompt_text = "Vui lòng phân tích tệp đính kèm."
        elif len(prompt_text) > 4000:
            raise ValidationDomainError("Nội dung tin nhắn không được vượt quá 4000 ký tự.")

        # 3. Validate all attachments BEFORE persisting the user message (strict owner check)
        attachment_records: List[Dict[str, Any]] = []
        audio_att_id = req.audio_attachment_id
        if req.attachments:
            for att_id in req.attachments:
                att = self._atts.get_owned(att_id, user_id)
                if not att:
                    raise NotFoundError(
                        f"Tệp đính kèm '{att_id}' không tồn tại hoặc bạn không có quyền truy cập.",
                        error_code="ATTACHMENT_NOT_FOUND",
                        structured=True,
                    )
                if att.get("status") not in ("READY", "ATTACHED"):
                    raise BadRequestError(
                        f"Tệp đính kèm '{att.get('filename')}' chưa ở trạng thái sẵn sàng (READY).",
                        error_code="ATTACHMENT_NOT_READY",
                        structured=True,
                    )
                attachment_records.append(att)
                if not audio_att_id and (
                    att.get("category") == "audio" or (att.get("mime_type") or "").startswith("audio/")
                ):
                    audio_att_id = att_id

        if audio_att_id and not any(a["id"] == audio_att_id for a in attachment_records):
            audio_row = self._atts.get_owned(audio_att_id, user_id)
            if not audio_row:
                raise NotFoundError(
                    f"Tệp âm thanh '{audio_att_id}' không tồn tại hoặc bạn không có quyền truy cập.",
                    error_code="ATTACHMENT_NOT_FOUND",
                    structured=True,
                )

        # 4. Persist user message and bind attachments
        user_msg_id = str(uuid.uuid4())
        self._convs.insert_user_message(
            message_id=user_msg_id,
            conversation_id=conversation_id,
            content=prompt_text,
            audio_attachment_id=audio_att_id,
            audio_duration_ms=req.audio_duration_ms or 0,
            stt_language=req.stt_language or req.language or "auto",
        )
        if audio_att_id:
            self._atts.bind_to_message(audio_att_id, user_msg_id, conversation_id)
        for att in attachment_records:
            self._atts.bind_to_message(att["id"], user_msg_id, conversation_id)

        # 5. Auto-title first message (INV-03, BR-004)
        if conv["title"] == "Cuộc trò chuyện mới":
            auto_title = prompt_text[:30].strip() + ("..." if len(prompt_text) > 30 else "")
            self._convs.rename(conversation_id, user_id, auto_title)
        else:
            self._convs.touch(conversation_id)

        # 6. Sliding window context (max 20 recent messages, INV-04)
        context_messages = self._convs.get_recent_context(conversation_id, limit=20)

        # 7. Resolve model, Sensei persona, active always-on rules, and build system prompt
        selected_model = req.model or self._models.get_default_active_id() or "gemini-3.8-flash"
        sensei_row = self._prompts.get_visible(req.sensei_id, user_id) if req.sensei_id else None
        sensei_voice_id = sensei_row.get("voice_id") if sensei_row else None
        active_rules = self._rules.list_active_always_on(user_id)

        system_instruction = self._prompt_builder.build(
            user=current_user,
            requested_language=req.language,
            sensei_row=sensei_row,
            active_rules=active_rules,
        )

        return PreparedChatStream(
            conversation_id=conversation_id,
            user_id=user_id,
            prompt_text=prompt_text,
            selected_model=selected_model,
            context_messages=context_messages,
            attachment_records=attachment_records,
            system_instruction=system_instruction,
            sensei_id=req.sensei_id,
            sensei_voice_id=sensei_voice_id,
        )

    async def stream_events(self, ctx: PreparedChatStream) -> AsyncGenerator[str, None]:
        """Yields formatted SSE chunks and persists final response, cache learning, and telemetry."""
        from llm.agent import chat_agent

        assistant_msg_id = str(uuid.uuid4())
        accumulated: List[str] = []
        final_model_used = ctx.selected_model
        start_time = time.perf_counter()
        ttft_ms: Optional[float] = None
        is_simulated = False

        try:
            async for event in chat_agent.astream_agent(
                prompt=ctx.prompt_text,
                history=ctx.context_messages,
                system_instruction=ctx.system_instruction,
                model_override=ctx.selected_model,
                attachments=ctx.attachment_records or None,
                user_id=ctx.user_id,
                conversation_id=ctx.conversation_id,
            ):
                ev_status = event.get("status")
                if ev_status == "streaming":
                    token_str = event.get("token", "")
                    accumulated.append(token_str)
                    if ttft_ms is None:
                        ttft_ms = (time.perf_counter() - start_time) * 1000
                    payload = json.dumps({"token": token_str, "status": "streaming"}, ensure_ascii=False)
                    yield f"event: chunk\ndata: {payload}\n\n"
                elif ev_status == "failover":
                    final_model_used = event.get("to_model", final_model_used)
                    payload = json.dumps(event, ensure_ascii=False)
                    yield f"event: failover\ndata: {payload}\n\n"
                elif ev_status == "done":
                    final_model_used = event.get("model", final_model_used)
                    is_simulated = bool(event.get("simulated"))
                elif ev_status == "error":
                    err_msg = redact_secrets_from_text(str(event.get("message", "Lỗi sinh phản hồi")))
                    payload = json.dumps({"status": "error", "message": err_msg}, ensure_ascii=False)
                    yield f"event: error\ndata: {payload}\n\n"

            final_text = "".join(accumulated).strip()
            self._convs.insert_assistant_message(
                message_id=assistant_msg_id,
                conversation_id=ctx.conversation_id,
                content=final_text,
                model_used=final_model_used,
                sensei_id=ctx.sensei_id,
                voice_id=ctx.sensei_voice_id,
            )

            # Auto-learn into Semantic Cache (skip simulator/empty responses)
            if final_text and ctx.prompt_text and not is_simulated:
                try:
                    from src.services.semantic_cache_service import SemanticCacheService

                    SemanticCacheService.learn_interaction(
                        prompt_raw=ctx.prompt_text,
                        response_text=final_text,
                        category="learned_chat",
                    )
                except Exception:
                    pass

            total_latency_ms = (time.perf_counter() - start_time) * 1000
            prompt_tokens_est = max(int(len(ctx.prompt_text.split()) * 1.3), 5)
            completion_tokens_est = max(int(len(final_text.split()) * 1.3), 5)
            total_tokens_est = prompt_tokens_est + completion_tokens_est

            quota_manager.consume_quota(ctx.user_id, total_tokens_est)
            provider = self._models.get_provider(final_model_used) or "google"

            metric_logger.log_metric(
                endpoint=f"/api/v1/conversations/{ctx.conversation_id}/messages/stream",
                method="POST",
                status_code=200,
                latency_ms=total_latency_ms,
                user_id=ctx.user_id,
                ttft_ms=ttft_ms,
                model_name=final_model_used,
                provider=provider,
                prompt_tokens=prompt_tokens_est,
                completion_tokens=completion_tokens_est,
                total_tokens=total_tokens_est,
            )

            done_payload = json.dumps(
                {
                    "status": "done",
                    "message_id": assistant_msg_id,
                    "model": final_model_used,
                    "tokens": total_tokens_est,
                    "latency_ms": round(total_latency_ms, 1),
                    "sensei_id": ctx.sensei_id,
                    "voice_id": ctx.sensei_voice_id,
                },
                ensure_ascii=False,
            )
            yield f"event: done\ndata: {done_payload}\n\n"
        except Exception as exc:
            total_latency_ms = (time.perf_counter() - start_time) * 1000
            metric_logger.log_metric(
                endpoint=f"/api/v1/conversations/{ctx.conversation_id}/messages/stream",
                method="POST",
                status_code=500,
                latency_ms=total_latency_ms,
                user_id=ctx.user_id,
                error_code="LLM_STREAM_ERROR",
            )
            safe_err = redact_secrets_from_text(str(exc))
            err_payload = json.dumps({"status": "error", "message": safe_err}, ensure_ascii=False)
            yield f"event: error\ndata: {err_payload}\n\n"

    async def transcribe_voice_upload(
        self,
        *,
        user_id: str,
        filename: str,
        content_bytes: bytes,
        language: Optional[str] = "auto",
        duration_ms: Optional[int] = 0,
    ) -> Dict[str, Any]:
        if len(content_bytes) > MAX_STT_AUDIO_BYTES:
            raise PayloadTooLargeError(
                "Tệp âm thanh vượt quá giới hạn 10MB cho phép.",
                error_code="FILE_TOO_LARGE",
                structured=True,
            )
        if len(content_bytes) == 0:
            raise BadRequestError(
                "Tệp âm thanh rỗng (0 bytes).",
                error_code="EMPTY_FILE",
                structured=True,
            )

        try:
            file_meta = self._storage.save(user_id, filename or "voice.webm", content_bytes)
        except ValueError as ve:
            raise BadRequestError(str(ve), error_code="INVALID_AUDIO_FORMAT", structured=True)

        file_meta["category"] = "audio"
        try:
            self._atts.create(user_id=user_id, file_meta=file_meta)
        except Exception:
            self._storage.delete(file_meta["storage_path"])
            raise

        att_id = file_meta["id"]
        stt_res = await self._stt.transcribe(
            audio_bytes=content_bytes,
            filename=file_meta["filename"],
            language_hint=language,
            user_id=user_id,
        )
        self._atts.update_extracted_text(att_id, stt_res.transcript)

        return {
            "status": "success",
            "data": {
                "attachment_id": att_id,
                "filename": file_meta["filename"],
                "audio_url": f"/api/v1/attachments/{att_id}/view",
                "duration_ms": duration_ms or 0,
                "transcript": stt_res.transcript,
                "detected_language": stt_res.detected_language,
                "confidence": stt_res.confidence,
                "engine_used": stt_res.engine_used,
                "latency_ms": stt_res.latency_ms,
            },
        }
