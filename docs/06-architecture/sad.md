# TÀI LIỆU ĐẶC TẢ KIẾN TRÚC PHẦN MỀM (SOFTWARE ARCHITECTURE DOCUMENT - SAD)
## Hệ Thống Website Chatbot Trợ Lý Ảo (AI-Chan Assistant)

---

| Thông Tin Tài Liệu | Chi Tiết |
| :--- | :--- |
| **Dự án** | Hệ Sinh Thái Học Tiếng Nhật ChatJPT (`chatjpt`) |
| **Mã tài liệu** | `ARCH-SAD-001` |
| **Trạng thái Baseline** | **BASELINED (UPDATED — ADR-017)** |
| **Mục đích** | Mô tả kiến trúc tổng thể của hệ thống dựa trên mô hình C4 (Context, Container, Component), xác lập kiến trúc 4 tầng chuẩn SOLID/KISS và lựa chọn công nghệ thực tế |

---

## 1. Mục Tiêu Kiến Trúc & Nguyên Tắc Thiết Kế (Architectural Drivers)

1. **Hiệu Năng & Độ Trễ Thấp (Performance & Low Latency)**: Tối ưu hóa thời gian bắt đầu stream phản hồi dưới 2 giây (`NFR-003`) thông qua Server-Sent Events (SSE).
2. **Độ Sẵn Sàng & Tính Tự Phục Hồi (High Availability & Resilience)**: Không phụ thuộc vào một nhà cung cấp duy nhất; tự động chuyển vùng dự phòng (Failover) từ Google Gemini sang OpenAI (`BR-005`, `NFR-008`).
3. **Bảo Mật Phòng Thủ Theo Chiều Sâu (Defense in Depth)**: Kiểm soát tần suất 2 tầng (`BP-SEC-001`), băm mật khẩu bcrypt (`SEC-002`), bảo vệ phiên bằng HttpOnly Secure Cookie (`SEC-004`) và cách ly dữ liệu cá nhân triệt tiêu lỗ hổng IDOR (`BR-002`, `NFR-018`).
4. **Kiến Trúc Tối Giản & Dễ Vận Hành (Simplicity - Ponytail Senior Dev Mode)**: Cấu trúc 3 tầng (3-tier) containerized rõ ràng, không thêm thấu kính phức tạp khi chưa có yêu cầu; đóng gói hoàn chỉnh qua Docker Compose.

---

## 2. Mô Hình Kiến Trúc C4 — Cấp Độ 2: Container View

```mermaid
flowchart TD
    User["Người Học Tiếng Nhật<br/>[ACT-01 / ACT-02]"]

    subgraph ContainerBoundary ["HẠ TẦNG ỨNG DỤNG CHATJPT"]
        Nginx["Container 1: Ingress Gateway (ai-infra)<br/>Nginx Reverse Proxy<br/>- SSL Termination & Rate Limit Layer 1<br/>- Static & API/SSE Proxy Routing"]

        Frontend["Container 2: Web Client (ai-frontend)<br/>Next.js 16 App Router, React<br/>- Trải nghiệm học tiếng Nhật (Chat, Sensei, Exams, Voices)<br/>- SSE Streaming Reader & Real-Time Telemetry Dashboard"]

        Backend["Container 3: Application Server (ai-backend)<br/>FastAPI, Python, Uvicorn (4-Layer SOLID/KISS - ADR-017)<br/>- Thin Routers + Pure ASGI TelemetryMiddleware<br/>- Domain Services, ProviderRegistry, STT & VoiceVox Core<br/>- Modular LangGraph LLM Orchestrator & Scoped Circuit Breaker"]

        SQLiteDB[("Storage 1: SQLite WAL Database<br/>database/app.db (16 tables + FTS5 Semantic Cache)<br/>- DatabaseManager + UnitOfWork + PRAGMA foreign_keys=ON")]

        FileStorage[("Storage 2: Local Secure Storage<br/>- database/uploads/ (Attachments)<br/>- models/embedded/ & voicevox_core/ & data/reference_materials/")]
    end

    subgraph ExternalCloud ["DỊCH VỤ NGOÀI INTERNET"]
        CloudLLMs["Cloud LLM & STT Providers<br/>Google Gemini / Groq / OpenAI / Anthropic / Local Ollama"]
    end

    User -->|HTTPS / HTTP| Nginx
    Nginx -->|HTTP:3000| Frontend
    Nginx -->|HTTP:8000| Backend
    Frontend -.->|REST & SSE| Nginx

    Backend -->|WAL ACID Transactions| SQLiteDB
    Backend -->|Path-Safe I/O| FileStorage
    Backend -->|HTTPS Outbound + Failover| CloudLLMs

    style ContainerBoundary fill:#f8fafc,stroke:#334155,stroke-width:2px
    style Nginx fill:#eff6ff,stroke:#3b82f6
    style Frontend fill:#eff6ff,stroke:#3b82f6
    style Backend fill:#eff6ff,stroke:#3b82f6
    style SQLiteDB fill:#f0fdf4,stroke:#22c55e
    style FileStorage fill:#f0fdf4,stroke:#22c55e
    style ExternalCloud fill:#fef9c3,stroke:#ca8a04
```

---

## 3. Mô Hình Kiến Trúc C4 — Cấp Độ 3: Component View (ai-backend 4-Layer SOLID — ADR-017)

```mermaid
flowchart TD
    subgraph API_Layer ["1. TẦNG GIAO TIẾP & BẢO VỆ (THIN ROUTERS & PURE ASGI MIDDLEWARE)"]
        TelemetryMW["Pure ASGI TelemetryMiddleware<br/>Non-blocking metrics, SSE-safe (BR-019)"]
        SecurityCore["Core Security & Rate Limiter<br/>JWT + SEC-007 password_changed_at, ADMIN_EMAILS"]
        Routers["13 Thin Routers (src/api/v1/*)<br/>0 inline SQL, Pydantic DTOs in src/schemas/v1/*"]
        DI["Composition Root (src/dependencies.py)<br/>FastAPI Depends() wiring"]
    end

    subgraph Service_Layer ["2. TẦNG NGHIỆP VỤ & ĐIỀU PHỐI AI (SERVICES & LLM ENGINE)"]
        CoreServices["Domain Services (src/services/*)<br/>Auth, User, Conv, Attachment, Prompt, Rule, TextImport, Model, Exam"]
        ProviderReg["ProviderRegistry & CredentialService<br/>AES-256-GCM SecretVault, SSRF Guard, Atomic .env"]
        ChatFacade["ChatService + PedagogicalPromptBuilder<br/>Trilingual Sensei Spec + always_on Rules"]
        VoiceSTT["VoicevoxService & STTService<br/>Chain of Responsibility TTS/STT + Thread-Safe LRU"]
        LLMEngine["Modular LLM Engine (llm/*)<br/>ScopedModelQuotaTracker, MessageBuilder, Orchestrator"]
        OfflineEngine["EmbeddedModelService & SemanticCacheService<br/>Hardware Gate + FTS5 Cache + OfflineResponder"]
    end

    subgraph Data_Layer ["3. TẦNG TRUY XUẤT DỮ LIỆU (REPOSITORIES & UoW)"]
        Repos["10 Domain Repositories (src/repositories/*)<br/>User, Conv, ApiKey, Model, Att, Prompt, Rule, Embedded, Voice, Exam, Telemetry"]
        DBMgr["DatabaseManager & UnitOfWork (src/core/database.py)<br/>SQLite WAL, busy_timeout=5000, FK ON"]
    end

    TelemetryMW --> Routers
    Routers --> SecurityCore
    Routers --> DI
    DI --> CoreServices
    DI --> ProviderReg
    DI --> ChatFacade
    DI --> VoiceSTT
    DI --> OfflineEngine

    ChatFacade --> LLMEngine
    LLMEngine --> ProviderReg
    LLMEngine --> OfflineEngine
    CoreServices --> Repos
    ProviderReg --> Repos
    ChatFacade --> Repos
    VoiceSTT --> Repos
    OfflineEngine --> Repos
    Repos --> DBMgr
```

---

## 4. Công Nghệ Chủ Đạo & Cơ Sở Lựa Chọn (Technology Stack Rationale)

1. **Backend Core (FastAPI, Python, Uvicorn — `ADR-017`)**: Kiến trúc 4 tầng chuẩn SOLID/KISS (`Routers -> Services -> Repositories -> Core/SQLite`), tách biệt hoàn toàn Pydantic DTO (`src/schemas/v1/`), domain entity (`src/models/v1/`), và xử lý lỗi miền tập trung qua `DomainError`.
2. **Frontend UI (Next.js 16 App Router & React)**: Hỗ trợ trải nghiệm học tiếng Nhật tương tác (Furigana Ruby, tô màu ngữ pháp, trình phát giọng nói VoiceVox, thi thử JLPT và Dashboard Telemetry SSE).
3. **Database (SQLite WAL + FTS5)**: Tối ưu vận hành cục bộ gọn nhẹ (KISS), kích hoạt Write-Ahead Logging (`WAL`), `busy_timeout=5000`, `PRAGMA foreign_keys = ON`, quản trị giao dịch nguyên tử qua `UnitOfWork`, và chỉ mục toàn văn `FTS5` cho 10,000+ mục Semantic Cache.
4. **AI Agent Engine (`llm/` — `ADR-005`, `ADR-017`)**: Tách riêng `ScopedModelQuotaTracker` (circuit breaker cô lập theo `user_id`), `message_builder.py` (cửa sổ trượt 20 tin nhắn `INV-04` + trích xuất đính kèm đa phương thức), và `orchestrator.py` ủy quyền khởi tạo model cho `ProviderRegistry`.
5. **VoiceVox TTS & Multilingual STT (`ADR-015`, `ADR-008`, `ADR-017`)**: Áp dụng mẫu **Chain of Responsibility** (VoiceVox Embedded Core → Daemon → Acoustic Fallback không cache; Groq Whisper → OpenAI Whisper → Gemini Audio → Heuristic) cùng `asyncio.to_thread` tránh chặn event loop.



---

## 5. Kiến Trúc Mở Rộng: Module Nhập Liệu Giọng Nói & STT (FEAT-006, ADR-008)

### 5.1 Quyết Định Kiến Trúc ADR-008: Hybrid STT Pipeline
- **Bối cảnh**: Người học tiếng Nhật cần luyện tập phản xạ giao tiếp Kaiwa bằng giọng nói (tiếng Việt, tiếng Anh, tiếng Nhật) thay vì chỉ gõ phím.
- **Quyết định**: Áp dụng kiến trúc lai (Hybrid Dual-Mode STT Pipeline):
  1. *Client-Side Capture*: Sử dụng Web Audio API kết hợp MediaRecorder API nén chuẩn Opus/WebM (24-32kbps Mono 16kHz) trực tiếp trong trình duyệt để giảm tải băng thông mạng (NFR-022).
  2. *Server-Side STT Engine (COMP-007)*: Máy chủ FastAPI tiếp nhận tệp âm thanh qua endpoint POST /api/v1/chat/stt (OP-066), xác thực Magic Bytes (SEC-021), lưu trữ tệp vào bảng ttachments và điều phối sang OpenAI Whisper hoặc Google Gemini Multimodal Audio để nhận diện đa ngữ chính xác cao (FR-080, BR-047).
  3. *Dual-Display Message Bubble*: Tin nhắn của người dùng trong khung chat hiển thị song song cả trình phát âm thanh (Audio Player) và đoạn văn bản chuyển đổi (Transcript) để người học tự kiểm tra phát âm của bản thân (FR-081, BR-050, UX-016).
  4. *Direct LLM Ingestion*: Đoạn văn bản sau STT được đưa trực tiếp vào đồ thị LangGraph Agent để Sensei phân tích ngữ pháp liên dòng và phản hồi thời gian thực qua luồng Server-Sent Events (FR-082, OP-067).
