import uuid
import json
import asyncio
import os
import time
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, AsyncGenerator, List, Dict, Any
from src.core.security import get_current_user, app_rate_limiter
from src.core.telemetry import quota_manager, metric_logger
from src.db import query_one, query_all, execute_commit

chat_router = APIRouter(tags=["Chat Streaming"])

class MessageStreamRequest(BaseModel):
    content: str = Field(default="", max_length=4000, description="Nội dung prompt câu hỏi (tối đa 4000 ký tự)")
    model: Optional[str] = "gemini-3.8-flash"
    sensei_id: Optional[str] = Field(default=None, description="ID của Sensei đồng hành (N5..N1)")
    language: Optional[str] = Field(default=None, description="Ngôn ngữ giao diện người dùng (vi, en, ja)")
    attachments: Optional[List[str]] = Field(default=None, description="Danh sách attachment_id đính kèm cho lượt chat này")

async def generate_mock_ai_stream(prompt: str, history: list) -> AsyncGenerator[str, None]:
    """Fallback high-quality AI streaming generator when external cloud keys are absent."""
    greeting = f"Chào bạn! Tôi là **AI-Chan Assistant**, trợ lý ảo thông minh của bạn.\n\n"
    
    # Custom contextual logic
    p_lower = prompt.lower()
    if "python" in p_lower:
        explanation = (
            f"Về câu hỏi liên quan đến Python: *\"{prompt}\"*:\n\n"
            f"Dưới đây là ví dụ minh họa tối ưu:\n\n"
            f"```python\n"
            f"def solution(items: list) -> dict:\n"
            f"    \"\"\"Giải pháp tối ưu thời gian O(n) và không gian O(n)\"\"\"\n"
            f"    return {{item: len(item) for item in items if item}}\n"
            f"\n"
            f"# Kiểm tra chạy thử:\n"
            f"sample_data = ['ai-chan', 'fastapi', 'nextjs', 'sqlite']\n"
            f"print(solution(sample_data))\n"
            f"```\n\n"
            f"Hệ thống đã tự động xử lý và lưu trữ dữ liệu vào cơ sở dữ liệu `app.db`."
        )
    elif "chào" in p_lower or "hello" in p_lower or "hi" in p_lower:
        explanation = (
            f"Rất vui được hỗ trợ bạn hôm nay! Tôi có thể giúp bạn:\n"
            f"1. **Giải đáp thắc mắc lập trình** (Python, TypeScript, SQL, Docker).\n"
            f"2. **Tư vấn kiến trúc hệ thống** và tối ưu hóa hiệu năng.\n"
            f"3. **Soạn thảo và tóm tắt văn bản** theo ngữ cảnh.\n\n"
            f"Bạn muốn bắt đầu với chủ đề nào?"
        )
    else:
        explanation = (
            f"Tôi đã tiếp nhận câu hỏi của bạn: *\"{prompt}\"*.\n\n"
            f"Dựa trên ngữ cảnh phiên làm việc ({len(history)} tin nhắn trước đó), dưới đây là phân tích chi tiết:\n\n"
            f"- **Phân tích yêu cầu**: Yêu cầu của bạn đã được kiểm tra tính hợp lệ và cách ly dữ liệu cá nhân an toàn (`BR-002`).\n"
            f"- **Phản hồi**: Hệ thống phản hồi qua cơ chế Server-Sent Events (SSE) theo thời gian thực (`ADR-004`).\n"
            f"- **Khả năng dự phòng**: Cổng AI hỗ trợ Multi-Provider Failover giữa Gemini và OpenAI (`ADR-003`).\n\n"
            f"Nếu bạn cần thêm chi tiết hoặc muốn tôi viết code mẫu, hãy cho tôi biết nhé!"
        )

    full_text = greeting + explanation
    # Tách thành các từ/token nhỏ để mô phỏng dòng chảy streaming thực tế
    words = full_text.split(" ")
    for idx, word in enumerate(words):
        chunk_word = word + (" " if idx < len(words) - 1 else "")
        chunk_data = json.dumps({"token": chunk_word, "status": "streaming"}, ensure_ascii=False)
        yield f"event: chunk\ndata: {chunk_data}\n\n"
        await asyncio.sleep(0.04)  # 40ms per token for natural typing speed

@chat_router.post("/conversations/{conversation_id}/messages/stream")
async def stream_message_endpoint(
    conversation_id: str,
    req: MessageStreamRequest,
    raw_request: Request,
    current_user: dict = Depends(get_current_user)
):
    client_ip = raw_request.client.host if raw_request.client else "127.0.0.1"
    app_rate_limiter.check(client_ip)

    user_id = current_user["id"]
    
    # 0. Kiểm tra Hạn ngạch Quota Token hàng ngày (BR-020, CTRL-008, TC-025)
    is_allowed, used_tokens, limit_tokens, is_warn_80 = quota_manager.check_quota(user_id, estimated_tokens=100)
    if not is_allowed:
        # Ghi nhận metric chặn quota 429
        metric_logger.log_metric(
            endpoint=f"/api/v1/conversations/{conversation_id}/messages/stream",
            method="POST",
            status_code=429,
            latency_ms=1.0,
            user_id=user_id,
            error_code="DAILY_QUOTA_EXCEEDED"
        )
        now_dt = datetime.now(timezone.utc)
        reset_dt = (now_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        retry_after_secs = int((reset_dt - now_dt).total_seconds())

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "DAILY_QUOTA_EXCEEDED",
                "message": f"Hạn ngạch token trong ngày đã hết ({used_tokens:,}/{limit_tokens:,} tokens). Yêu cầu bị chặn (HTTP 429). Hạn ngạch sẽ được làm mới lúc 00:00 UTC.",
                "daily_tokens_used": used_tokens,
                "daily_token_limit": limit_tokens,
                "retry_after": retry_after_secs
            },
            headers={"Retry-After": str(retry_after_secs)}
        )

    # 1. Kiểm tra quyền sở hữu cuộc trò chuyện (Anti-IDOR - BR-002, CTRL-002, TC-011)
    conv = query_one(
        "SELECT id, title FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id)
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuộc trò chuyện không tồn tại hoặc bạn không có quyền truy cập."
        )

    # 2. Kiểm tra độ dài prompt hoặc tệp đính kèm (INV-02, BR-003)
    prompt_text = req.content.strip()
    if not prompt_text and not req.attachments:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nội dung tin nhắn phải từ 1 đến 4000 ký tự hoặc có tệp đính kèm."
        )
    if not prompt_text and req.attachments:
        prompt_text = "Vui lòng phân tích tệp đính kèm."
    elif len(prompt_text) > 4000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nội dung tin nhắn không được vượt quá 4000 ký tự."
        )

    # 3. Ghi nhận tin nhắn người dùng vào CSDL (bảng messages)
    user_msg_id = str(uuid.uuid4())
    execute_commit(
        """
        INSERT INTO messages (id, conversation_id, role, content, model_used)
        VALUES (?, ?, 'user', ?, ?)
        """,
        (user_msg_id, conversation_id, prompt_text, "client")
    )

    # 3.5. Xử lý và xác thực danh sách attachment_ids (Anti-IDOR, BR-002, Attachment Lifecycle)
    attachment_records: List[Dict[str, Any]] = []
    if req.attachments:
        for att_id in req.attachments:
            att = query_one(
                "SELECT * FROM attachments WHERE id = ? AND (user_id = ? OR user_id = 'guest_user')",
                (att_id, user_id)
            )
            if not att:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error_code": "ATTACHMENT_NOT_FOUND",
                        "message": f"Tệp đính kèm '{att_id}' không tồn tại hoặc bạn không có quyền truy cập."
                    }
                )
            if att.get("status") not in ("READY", "ATTACHED"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "ATTACHMENT_NOT_READY",
                        "message": f"Tệp đính kèm '{att.get('filename')}' chưa ở trạng thái sẵn sàng (READY)."

                    }
                )
            # Ràng buộc attachment vào message và conversation
            execute_commit(
                """
                UPDATE attachments
                SET message_id = ?, conversation_id = ?, status = 'ATTACHED', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (user_msg_id, conversation_id, att_id)
            )
            attachment_records.append(att)

    # 4. Tự động đổi tên tiêu đề nếu là tin nhắn đầu tiên (INV-03, BR-004)
    if conv["title"] == "Cuộc trò chuyện mới":
        auto_title = prompt_text[:30].strip() + ("..." if len(prompt_text) > 30 else "")
        execute_commit(
            "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (auto_title, conversation_id)
        )
    else:
        execute_commit(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,)
        )

    # 5. Truy vấn tối đa 20 tin nhắn gần nhất làm ngữ cảnh trượt (INV-04)
    context_msgs = query_all(
        """
        SELECT role, content FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (conversation_id,)
    )
    context_msgs.reverse()

    # 6. Generator truyền luồng Server-Sent Events (SSE) qua LangChain & LangGraph Agent (ADR-005)
    async def sse_event_generator():
        assistant_msg_id = str(uuid.uuid4())
        accumulated_response = []
        # Tra cứu mô hình mặc định từ bảng models nếu không chỉ định cụ thể
        selected_model = req.model
        if not selected_model:
            def_model_row = query_one("SELECT id FROM models WHERE is_default = 1 AND status = 'ACTIVE' LIMIT 1")
            selected_model = def_model_row["id"] if def_model_row else "gemini-3.8-flash"
        final_model_used = selected_model

        start_time = time.perf_counter()
        ttft_recorded = False
        ttft_ms = None

        # Nạp chỉ thị persona của Sensei đồng hành nếu được chọn (FR-064, FR-065, FR-072)
        sensei_instruction = None
        sensei_voice_id = None
        if req.sensei_id:
            sensei_row = query_one(
                "SELECT name, content, teaching_style, catchphrase, japanese_level, voice_id FROM system_prompts WHERE id = ? AND (user_id = ? OR is_system_preset = 1)",
                (req.sensei_id, user_id)
            )
            if sensei_row:
                sensei_voice_id = sensei_row.get("voice_id")
                sensei_instruction = (
                    f"TÊN SENSEI: {sensei_row['name']} (Cấp độ {sensei_row.get('japanese_level', 'N5')})\n"
                    f"PHONG CÁCH SƯ PHẠM: {sensei_row.get('teaching_style', '')}\n"
                    f"CÂU CỬA MIỆNG: {sensei_row.get('catchphrase', '')}\n\n"
                    f"CHỈ THỊ PERSONA:\n{sensei_row['content']}"
                )

        # Định dạng cấu trúc câu trả lời sư phạm của Sensei theo cài đặt người dùng (FR-067, FR-068)
        formatting_rules = []
        user_lang = req.language or current_user.get("language_preference") or "vi"
        if user_lang not in ("vi", "ja", "en"):
            user_lang = "vi"

        if user_lang == "vi":
            lang_label = "tiếng Việt"
            formatting_rules.append(
                "QUY TẮC BẮT BUỘC VỀ NGÔN NGỮ (TUYỆT ĐỐI TUÂN THỦ):\n"
                "1. Người học đang sử dụng giao diện TIẾNG VIỆT.\n"
                "2. TUYỆT ĐỐI KHÔNG DÙNG TIẾNG ANH trong bất kỳ câu dịch hay phần giải thích nào.\n"
                "3. Toàn bộ bản dịch đặt dưới mỗi câu tiếng Nhật PHẢI 100% LÀ TIẾNG VIỆT.\n"
                "4. Toàn bộ phần phân tích ngữ pháp, từ vựng và sắc thái PHẢI 100% LÀ TIẾNG VIỆT (dùng thuật ngữ 'Khiêm nhường ngữ', 'Tôn kính ngữ', v.v. - TUYỆT ĐỐI KHÔNG dùng tiếng Anh)."
            )
        elif user_lang == "ja":
            lang_label = "日本語"
            formatting_rules.append(
                "言語規則: ユーザーの表示言語は日本語です。要約や解説はすべて自然な日本語で記述してください。"
            )
        else:
            lang_label = "English"
            formatting_rules.append(
                "LANGUAGE RULE: Provide all translations and grammar breakdown in English."
            )

        formatting_rules.append(
            "QUY TẮC CHỮ TIẾNG NHẬT TỰ NHIÊN (KHÔNG CHÈN DẤU CÁCH BỪA BÃI):\n"
            "- Viết câu tiếng Nhật tự nhiên, KHÔNG chèn khoảng trắng bừa bãi giữa các từ tiếng Nhật hoặc trước/sau dấu câu (、, 。, ！, ？).\n"
            "- Ví dụ: viết 「さあ、今日はどんな気分？」, TUYỆT ĐỐI KHÔNG viết 「さあ 、 今日 は どんな 気分 ？ 」."
        )

        if current_user.get("response_show_furigana", 1):
            formatting_rules.append(
                "- FURIGANA: BẮT BUỘC gắn Furigana cho chữ Kanji bằng định dạng Ruby Markdown duy nhất: `[漢字](かんじ)` (ví dụ: `[今日](きょう)`, `[元気](げんき)`, `[日本語](にほんご)`).\n"
                "  TUYỆT ĐỐI KHÔNG DÙNG `{漢字}[かんじ]` hoặc `（ 漢字 かんじ ） [ ]`."
            )
        if current_user.get("response_highlight_grammar", 1):
            formatting_rules.append(
                "- TÔ MÀU NGỮ PHÁP (MÀU XANH LÁ ĐỒNG NHẤT): Với trợ từ hoặc cấu trúc/ngữ pháp trọng tâm, bọc viền bằng `{từ}[g-green]` (đồng nhất màu xanh lá). TUYỆT ĐỐI chỉ dùng `[g-green]`, không dùng màu khác."
            )
        if current_user.get("response_show_translation", 1):
            formatting_rules.append(
                f"- BẢN DỊCH DƯỚI CÂU: Mỗi câu thoại tiếng Nhật BẮT BUỘC PHẢI CÓ dòng dịch nghĩa sang {lang_label} đặt ngay bên dưới trên một dòng riêng biệt, định dạng: `(Bản dịch: <nội dung dịch>)`. Bắt buộc 100% bằng {lang_label}."
            )
        if current_user.get("response_grammar_breakdown", 1):
            formatting_rules.append(
                f"- PHÂN TÍCH TỪ VỰNG & NGỮ PHÁP (ĐÓNG KHUNG CẤU TRÚC RÕ RÀNG):\n"
                f"Ở cuối câu trả lời, hãy tạo khối phân tích riêng biệt ngăn cách bởi một dòng kẻ `---` và tiêu đề `### 🔍 Phân tích Ngữ pháp & Từ vựng`.\n"
                f"Mỗi điểm ngữ pháp hoặc từ vựng trọng tâm BẮT BUỘC PHẢI ĐƯỢC ĐÁNH SỐ VÀ CÓ TIÊU ĐỀ RÕ RÀNG:\n"
                f"1. **【Cấu trúc/Từ vựng】** *(Phân loại / Cấp độ)*\n"
                f"- *Ý nghĩa:* Giải thích cụ thể bằng {lang_label}\n"
                f"- *Sắc thái:* Hướng dẫn cách dùng và bối cảnh giao tiếp tự nhiên bằng {lang_label}\n\n"
                f"2. **【Cấu trúc/Từ vựng tiếp theo】** *(Phân loại / Cấp độ)*\n"
                f"- *Ý nghĩa:* Giải thích cụ thể bằng {lang_label}\n"
                f"- *Sắc thái:* Hướng dẫn cách dùng và bối cảnh giao tiếp tự nhiên bằng {lang_label}"
            )

        # Add explicit FEW-SHOT template matching Settings preview
        formatting_rules.append(
            f"\n--- MẪU TRÌNH BÀY CHUẨN CỦA SENSEI (BẮT BUỘC TUÂN THỦ CHÍNH XÁC THEO MẪU NÀY) ---\n"
            f"{{はい}}[g-green]、[元気](げんき)ですよ！[一緒](いっしょ)に[日本語](にほんご)を[勉強](べんきょう)しましょうね！\n"
            f"(Bản dịch: Vâng, tôi rất khỏe! Chúng ta cùng nhau học tiếng Nhật nhé!)\n\n"
            f"[今日](きょう)は{{どんな}}[g-green][気分](きぶん)ですか？[何](なに)か{{面白い}}[g-green][出来事](できごと)はありましたか？\n"
            f"(Bản dịch: Hôm nay tâm trạng bạn thế nào? Có chuyện gì vui không?)\n\n"
            f"---\n"
            f"### 🔍 Phân tích Ngữ pháp & Từ vựng\n"
            f"1. **【〜ましょう】** *(Động từ thể rủ rê / Lịch sự)*\n"
            f"- *Ý nghĩa:* Diễn tả lời mời hoặc đề xuất cùng làm việc gì đó một cách thân thiện.\n"
            f"- *Sắc thái:* Tạo cảm giác gắn kết, ấm áp và khích lệ người học tham gia.\n\n"
            f"2. **【〜ですか】** *(Trợ từ nghi vấn)*\n"
            f"- *Ý nghĩa:* Dùng ở cuối câu để tạo câu hỏi lịch thiệp.\n"
            f"- *Sắc thái:* Bày tỏ sự quan tâm chân thành đến người đối thoại."
        )

        if formatting_rules:
            formatting_prompt = "\n".join(formatting_rules)
            if sensei_instruction:
                sensei_instruction += f"\n\nQUY CHUẨN ĐỊNH DẠNG CÂU TRẢ LỜI CỦA SENSEI (RESPONSES SPEC):\n{formatting_prompt}"
            else:
                sensei_instruction = f"QUY CHUẨN ĐỊNH DẠNG CÂU TRẢ LỜI CỦA SENSEI (RESPONSES SPEC):\n{formatting_prompt}"

        try:
            from llm.agent import chat_agent

            async for event in chat_agent.astream_agent(
                prompt=prompt_text,
                history=context_msgs,
                system_instruction=sensei_instruction,
                model_override=selected_model,
                attachments=attachment_records if attachment_records else None,
                user_id=current_user["id"],
                conversation_id=conversation_id
            ):

                if event.get("status") == "streaming":
                    token_str = event.get("token", "")
                    accumulated_response.append(token_str)

                    # Đo đạc TTFT ngay khi nhận chunk token đầu tiên (FR-029)
                    if not ttft_recorded:
                        ttft_ms = (time.perf_counter() - start_time) * 1000
                        ttft_recorded = True

                    data_payload = json.dumps({"token": token_str, "status": "streaming"}, ensure_ascii=False)
                    yield f"event: chunk\ndata: {data_payload}\n\n"
                elif event.get("status") == "failover":
                    final_model_used = event.get("to_model", final_model_used)
                    failover_payload = json.dumps(event, ensure_ascii=False)
                    yield f"event: failover\ndata: {failover_payload}\n\n"
                elif event.get("status") == "done":
                    final_model_used = event.get("model", final_model_used)
                elif event.get("status") == "error":
                    err_msg = event.get("message", "Lỗi sinh phản hồi")
                    err_payload = json.dumps({"status": "error", "message": err_msg}, ensure_ascii=False)
                    yield f"event: error\ndata: {err_payload}\n\n"

            # Lưu toàn bộ câu trả lời hoàn chỉnh vào CSDL kèm sensei_id và voice_id (FR-072, FR-073)
            final_text = "".join(accumulated_response).strip()
            execute_commit(
                """
                INSERT INTO messages (id, conversation_id, role, content, model_used, sensei_id, voice_id)
                VALUES (?, ?, 'assistant', ?, ?, ?, ?)
                """,
                (assistant_msg_id, conversation_id, final_text, final_model_used, req.sensei_id, sensei_voice_id)
            )

            # Tự động học vào Semantic Cache với cơ chế Deduplication (FR-063, BR-022)
            if final_text and prompt_text:
                try:
                    from src.services.semantic_cache_service import SemanticCacheService
                    SemanticCacheService.learn_interaction(
                        prompt_raw=prompt_text,
                        response_text=final_text,
                        category="learned_chat"
                    )
                except Exception:
                    pass

            # Tính toán telemetry hoàn tất: latency, token usage, trừ quota & ghi log (FR-029, FR-030, BR-019)
            total_latency_ms = (time.perf_counter() - start_time) * 1000
            prompt_tokens_est = max(int(len(prompt_text.split()) * 1.3), 5)
            completion_tokens_est = max(int(len(final_text.split()) * 1.3), 5)
            total_tokens_est = prompt_tokens_est + completion_tokens_est

            # Cập nhật Quota
            quota_manager.consume_quota(user_id, total_tokens_est)

            # Tìm provider của model
            model_info = query_one("SELECT provider FROM models WHERE id = ?", (final_model_used,))
            provider = model_info["provider"] if model_info else "google"

            # Ghi log telemetry và broadcast SSE lên Dashboard (FR-033, OP-019)
            metric_logger.log_metric(
                endpoint=f"/api/v1/conversations/{conversation_id}/messages/stream",
                method="POST",
                status_code=200,
                latency_ms=total_latency_ms,
                user_id=user_id,
                ttft_ms=ttft_ms,
                model_name=final_model_used,
                provider=provider,
                prompt_tokens=prompt_tokens_est,
                completion_tokens=completion_tokens_est,
                total_tokens=total_tokens_est
            )

            # Gửi sự kiện done hoàn tất kèm sensei_id và voice_id (SEQ-003, ADR-004, FR-072, FR-073)
            done_payload = json.dumps({
                "status": "done",
                "message_id": assistant_msg_id,
                "model": final_model_used,
                "tokens": total_tokens_est,
                "latency_ms": round(total_latency_ms, 1),
                "sensei_id": req.sensei_id,
                "voice_id": sensei_voice_id
            }, ensure_ascii=False)
            yield f"event: done\ndata: {done_payload}\n\n"

        except Exception as exc:
            total_latency_ms = (time.perf_counter() - start_time) * 1000
            metric_logger.log_metric(
                endpoint=f"/api/v1/conversations/{conversation_id}/messages/stream",
                method="POST",
                status_code=500,
                latency_ms=total_latency_ms,
                user_id=user_id,
                error_code="LLM_STREAM_ERROR"
            )
            err_payload = json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {err_payload}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
