# Sơ Đồ Thành Phần Kiến Trúc (Component Architecture Diagram)
## Dự Án: Website Hỗ Trợ Học Tiếng Nhật & AI Virtual Sensei (ChatJPT)

---

| Thông Tin Sơ Đồ | Chi Tiết |
| :--- | :--- |
| **Mã Sơ Đồ** | `DIAG-COMP-001` |
| **Loại Sơ Đồ** | **C4 Component Diagram (Level 3 — ai-backend 4-Layer SOLID/KISS — `ADR-017`)** |
| **Nguồn Sự Thật Thượng Nguồn** | [docs/06-architecture/sad.md](../../docs/06-architecture/sad.md) (`ARCH-SAD-001`), [ADR-017](../../docs/06-architecture/ADR/ADR-017-backend-solid-kiss-refactoring.md), [models/architecture/architecture.yaml](../../models/architecture/architecture.yaml) |
| **Mục Đích** | Trực quan hóa kiến trúc 4 tầng thực tế bên trong `ai-backend/` (Thin Routers → Services & LLM Engine → 10 Repositories → SQLite WAL & Storage) |

---

## 1. Biểu Đồ Thành Phần Chi Tiết (C4 Component View)

```mermaid
flowchart TD
    Client["Trình Duyệt Người Học<br/>(ai-frontend — Next.js 16 App Router)"]

    subgraph IngressLayer ["TẦNG INGRESS (ai-infra)"]
        NginxGateway["Nginx Reverse Proxy<br/>- SSL Termination & Rate Limit Layer 1<br/>- REST & SSE Proxy Routing"]
    end

    subgraph BackendApp ["ỨNG DỤNG LÕI BACKEND (ai-backend — FastAPI / ADR-017)"]
        subgraph APILayer ["1. Tầng HTTP/SSE & Bảo Vệ (Thin Routers + Pure ASGI)"]
            TelemetryMW["Pure ASGI TelemetryMiddleware<br/>Non-buffering SSE, async metric logging (BR-019)"]
            SecurityGuard["Core Security & Rate Limiter<br/>JWT + SEC-007 password_changed_at, ADMIN_EMAILS"]
            RouterGroup["13 Thin Routers (src/api/v1/*)<br/>Auth, Users, Conv, Chat/STT, Embedded, Models,<br/>API Keys, Prompts, Rules, Attachments, Voices, Exams, Resources"]
            SchemasV1["Pydantic v2 DTOs (src/schemas/v1/*)<br/>& Global DomainError Handler"]
            CompositionRoot["Composition Root (src/dependencies.py)<br/>FastAPI Depends() Wiring"]
        end

        subgraph ServiceLayer ["2. Tầng Nghiệp Vụ & Điều Phối AI (Services + llm/)"]
            CoreServices["Domain Services (src/services/*)<br/>Auth, User, Conv, Attachment, Prompt, Rule, TextImport, Model, Exam"]
            ProviderReg["ProviderRegistry + CredentialService<br/>AES-256-GCM SecretVault, Ollama SSRF Guard, Atomic .env"]
            ChatFacade["ChatService + PedagogicalPromptBuilder<br/>Trilingual Sensei Spec + always_on Rules Injection"]
            LLMEngine["Modular LLM Engine (llm/*)<br/>ScopedModelQuotaTracker, MessageBuilder (INV-04), Orchestrator"]
            VoiceSTT["VoicevoxService & STTService<br/>Chain of Responsibility TTS/STT + Thread-Safe LRU"]
            EmbeddedCache["EmbeddedModelService & SemanticCacheService<br/>Hardware Gate + OfflineSenseiResponder + FTS5 Cache"]
        end

        subgraph RepositoryLayer ["3. Tầng Truy Xuất Dữ Liệu (Repositories & UoW)"]
            DomainRepos["10 Domain Repositories (src/repositories/*)<br/>User, Conv, ApiKey, Model, Att, Prompt, Rule, Embedded, Voice, Exam, Telemetry"]
            DBMgr["DatabaseManager & UnitOfWork<br/>(src/core/database.py — SQLite WAL, busy_timeout=5000, FK ON)"]
            LocalStore["LocalAttachmentStorage<br/>(src/core/storage.py — Magic Bytes, Atomic Writes)"]
        end
    end

    subgraph PersistenceLayer ["HẠ TẦNG LƯU TRỮ CỤC BỘ"]
        SQLiteDB[("SQLite WAL Database<br/>database/app.db (16 bảng + FTS5)")]
        DiskAssets[("Tệp Lưu Trữ Cục Bộ<br/>uploads/, voicevox_core/, models/embedded/, reference_materials/")]
    end

    subgraph ExternalServices ["DỊCH VỤ NGOÀI & DAEMON CỤC BỘ"]
        CloudLLMs["Cloud LLM & STT APIs<br/>Google Gemini / Groq / OpenAI / Anthropic / Ollama"]
        VoiceVoxDaemon["VoiceVox Engine<br/>In-Process ONNX Core / Local Daemon (:50021)"]
    end

    Client -->|"REST & SSE"| NginxGateway
    NginxGateway -->|"HTTP:8000"| TelemetryMW
    TelemetryMW --> RouterGroup
    RouterGroup --> SecurityGuard
    RouterGroup --> SchemasV1
    RouterGroup --> CompositionRoot

    CompositionRoot --> CoreServices
    CompositionRoot --> ProviderReg
    CompositionRoot --> ChatFacade
    CompositionRoot --> VoiceSTT
    CompositionRoot --> EmbeddedCache

    ChatFacade --> LLMEngine
    LLMEngine --> ProviderReg
    LLMEngine --> EmbeddedCache

    CoreServices --> DomainRepos
    CoreServices --> LocalStore
    ProviderReg --> DomainRepos
    ChatFacade --> DomainRepos
    VoiceSTT --> DomainRepos
    EmbeddedCache --> DomainRepos

    DomainRepos --> DBMgr
    DBMgr -->|"ACID WAL"| SQLiteDB
    LocalStore -->|"Path-Safe I/O"| DiskAssets
    EmbeddedCache -->|"Safe Model ID"| DiskAssets
    VoiceSTT -->|"In-Process / HTTP"| VoiceVoxDaemon
    LLMEngine -->|"HTTPS Failover"| CloudLLMs
    ProviderReg -->|"Async Health Probe"| CloudLLMs

    style IngressLayer fill:#eff6ff,stroke:#3b82f6
    style BackendApp fill:#f8fafc,stroke:#334155,stroke-width:2px
    style APILayer fill:#f1f5f9,stroke:#64748b
    style ServiceLayer fill:#ecfdf5,stroke:#10b981
    style RepositoryLayer fill:#fffbeb,stroke:#f59e0b
    style PersistenceLayer fill:#f0fdf4,stroke:#22c55e
    style ExternalServices fill:#fefce8,stroke:#ca8a04
```
