# ADR-017: Tái Cấu Trúc Backend Theo Kiến Trúc 4 Tầng Chuẩn SOLID, KISS & Design Patterns

| Thuộc Tính | Giá Trị |
| :--- | :--- |
| **Mã Quyết Định** | `ADR-017` |
| **Trạng Thái** | `APPROVED` (Implemented) |
| **Ngày Phê Duyệt** | `2026-11-24` |
| **Liên Kết Mô Hình** | `models/architecture/architecture.yaml` (`ARCH-001`, `COMP-002..COMP-007`), `models/domain/domain.yaml`, `models/api/api.yaml`, `models/testing/testing.yaml` |
| **Truy Vết Yêu Cầu** | `SEC-007`, `BR-002`, `BR-013`, `BR-019`, `BR-020`, `BR-023`, `BR-040`, `BR-042`, `BR-044`, `FR-071`, `FR-076`, `NFR-020` |

---

## 1. Bối Cảnh (Context)

Qua khảo sát mã nguồn hiện trạng của `ai-backend/`, hệ thống bộc lộ 5 nhóm nợ kỹ thuật và rủi ro an ninh nghiêm trọng:

1. **Vi phạm SRP & DIP trong tầng Router**: Các tệp trong `src/api/v1/` trộn lẫn Pydantic DTOs, domain constants, business rules, raw SQL (`query_one`, `execute_commit`), và prompt formatting dài hàng trăm dòng (ví dụ `chat.py` 607 dòng, `exams.py` 464 dòng, `prompts.py` 520 dòng).
2. **Độ lệch Schema & N+1 / Toàn vẹn giao dịch**: `database/schema.sql` thiếu cột trên 5 bảng (`messages`, `models`, `api_metric_logs`, `attachments`, `user_api_keys`); nhiều thao tác ghi liên quan không nằm trong transaction nguyên tử (đổi default model, xóa hội thoại kèm tệp, OCC update trên `rules`, `get_or_create_quota`).
3. **Lỗi bảo mật & độ tin cậy thực thi**:
   - Thiếu kiểm tra `password_changed_at` (`SEC-007`), kiểm tra admin bằng substring `"admin" in email`, SSRF trên Ollama URL, newline injection khi ghi `.env`, path traversal trên `model_id` của embedded model, IDOR trên `RuleService.clone_rule` và `attachments`, lộ đáp án bài thi khi gọi `include_answers=true` (`CTRL-EXAM-03`).
   - Lỗi runtime nghiêm trọng tại `llm/agent.py` khi gọi `extract_text_from_file(storage_path, m_type)` (2 tham số thay vì 4 tham số với bytes); `BaseHTTPMiddleware` đệm luồng SSE; `VoicevoxService` lưu nhầm fallback beep vào LRU cache; route `DELETE /models/embedded` bị che khuất bởi `DELETE /models/{model_id}`.
4. **Hiệu năng & Blocking Event Loop**: `MetricLogger.get_metrics_summary` tải toàn bộ log 30 ngày vào RAM; `TelemetryMiddleware` ghi SQLite đồng bộ trên luồng sự kiện chính; `VoicevoxService` và `GeminiAudioSTTProvider` chạy I/O đồng bộ ngay trong `async def`.
5. **Trùng lặp khởi tạo LLM Provider**: Cả `CredentialService`, `models.py` và `llm/agent.py` đều tự duy trì cấu hình provider tách biệt.

---

## 2. Quyết Định Kiến Trúc (Decision)

Tái cấu trúc toàn bộ `ai-backend/` sang **kiến trúc 4 tầng phân lớp nghiêm ngặt** (giữ nguyên SQLite nâng cấp WAL mode và bảo toàn **100% tương thích API** với `ai-frontend/`):

```text
Thin Routers (src/api/v1/*)              --> HTTP/SSE parsing, Rate Limit, Depends(...)
        │ (Schemas: src/schemas/v1/*)
        ▼
Application Services (src/services/*)    --> Business Rules, Facades, Strategies, Builders
        │ (Entities: src/models/v1/*)        + Modular LLM Engine (llm/*)
        ▼
Repositories (src/repositories/*)        --> 10 Domain Repositories (100% isolated SQL)
        │
        ▼
Core Infrastructure (src/core/*)         --> DatabaseManager + UnitOfWork (SQLite WAL),
                                             DomainError, Security (SEC-007), SecretVault,
                                             Storage, Pure ASGI TelemetryMiddleware
```

### Danh Mục Design Patterns Áp Dụng Chuẩn KISS

| Pattern | Áp Dụng Cụ Thể | Lợi Ích |
| :--- | :--- | :--- |
| **Repository + Unit of Work** | `src/core/database.py`, `src/repositories/{user,conversation,api_key,model,attachment,prompt,rule,embedded,voice,exam,telemetry}_repo.py` | Tách biệt 100% SQL khỏi router/service; hỗ trợ transaction nguyên tử, WAL mode, `PRAGMA foreign_keys = ON`. |
| **Composition Root (DI)** | `src/dependencies.py` | Nối tập trung toàn bộ repository và service cho FastAPI `Depends(...)`, dễ thay thế mock trong unit test. |
| **Registry + Strategy + Factory** | `src/services/provider_registry.py` (`ProviderRegistry`, `ProviderSpec`) | Nguồn chân lý duy nhất cho 7 nhà cung cấp (Google, OpenAI, Anthropic, Groq, Ollama, Brave, SerpAPI), SSRF guard và khởi tạo LangChain model. |
| **Chain of Responsibility + Strategy** | `src/services/stt_service.py` (Groq Whisper → OpenAI Whisper → Gemini Audio → Heuristic) & `src/services/voicevox_service.py` (Embedded Core → Daemon → Acoustic Fallback) | Khả năng mở rộng Open-Closed, tự động dự phòng an toàn, không cache fallback beep. |
| **Builder / Template Strategy** | `src/services/prompt_builder.py` (`PedagogicalPromptBuilder`) | Thay thế 160 dòng nối chuỗi tam ngữ (`vi`/`ja`/`en`) trong `chat.py`; tự động tiêm các quy tắc `always_on` đang kích hoạt vào ngữ cảnh Sensei. |
| **Facade** | `src/services/chat_service.py`, `llm/agent.py`, `src/db.py` | Đóng gói luồng nghiệp vụ phức tạp (Quota → Anti-IDOR → Context → Stream → Learn Cache → Telemetry) và giữ tương thích ngược với caller cũ. |
| **Pure ASGI Middleware** | `src/core/telemetry_middleware.py` | Đo đạc latency/status/5xx non-blocking qua `asyncio.to_thread` mà không đệm luồng SSE. |
| **Scoped Circuit Breaker** | `llm/circuit_breaker.py` (`ScopedModelQuotaTracker`) | Cô lập thời gian cooldown 429 theo `(user_id, model_name)` để BYOK của một người dùng không khóa người dùng khác. |

---

## 3. Hệ Quả & Ràng Buộc (Consequences)

- **Tích cực**: 0 dòng SQL và 0 schema định nghĩa trực tiếp trong `src/api/v1/*`; sửa triệt để toàn bộ lỗi bảo mật và lỗi logic đã phát hiện; 3 bộ Unit Test độc lập (`tests/unit/*`) + 6 đường ống Integration Test (`tests/integration/test_pipelines.py`) kiểm chứng toàn bộ hành vi.
- **Tương thích**: `ai-frontend/` hoạt động không cần sửa đổi; các hàm facade (`src/db.py`, `llm/agent.py`, classmethods trên `CredentialService`, `RuleService`, `SemanticCacheService`, `EmbeddedModelService`, `HardwareInspectionService`) được bảo toàn cho 13 bộ test hồi quy sẵn có.
- **Giới hạn đã biết (`ponytail:`)**:
  - `InMemoryRateLimiter` dùng bộ đếm trong tiến trình (nâng cấp sang Redis khi triển khai đa worker).
  - `GeminiAudioSTTProvider` dùng khóa mutex quanh `google.generativeai.configure` cho đến khi chuyển sang SDK `google-genai` hỗ trợ client độc lập.
