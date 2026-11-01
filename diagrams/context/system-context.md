# Sơ Đồ Ngữ Cảnh Hệ Thống (System Context Diagram)
## Dự Án: Website Hỗ Trợ Học Tiếng Nhật & AI Virtual Sensei (ChatJPT)

---

| Thông Tin Sơ Đồ | Chi Tiết |
| :--- | :--- |
| **Mã Sơ Đồ** | `DIAG-CTX-001` |
| **Loại Sơ Đồ** | **System Context Diagram (C4 Context Level 1)** |
| **Nguồn Sự Thật Thượng Nguồn** | [docs/05-system-analysis/system-context.md](file:///c:/Users/PC/Project/ChatJPT/docs/05-system-analysis/system-context.md), [docs/06-architecture/sad.md](file:///c:/Users/PC/Project/ChatJPT/docs/06-architecture/sad.md) |
| **Mục Đích** | Mô tả biên giới hệ thống ChatJPT, các tác nhân con người tương tác và các dịch vụ đám mây ngoại vi |

---

## 1. Biểu Đồ Ngữ Cảnh Mermaid

```mermaid
flowchart TD
    subgraph HumanActors ["TÁC NHÂN CON NGƯỜI (HUMAN ACTORS)"]
        Guest["Khách Vãng Lai<br/>[ACT-01: Guest]<br/>Truy cập trang công khai (/login, /register)"]
        User["Người Dùng Đã Xác Thực<br/>[ACT-02: Japanese Learner / Registered User]<br/>Trò chuyện, học tiếng Nhật, luyện Kaiwa, quản lý Rules & Prompts"]
    end

    subgraph SystemBoundary ["BIÊN GIỚI HỆ THỐNG TRỢ LÝ HỌC TIẾNG NHẬT CHATJPT (IN-SCOPE)"]
        AI_System["Hệ Thống Web Chatbot ChatJPT<br/>[ChatJPT Platform]<br/>- Giao diện người dùng Web (Next.js 16 + 3D VRM Sensei)<br/>- Cổng Ingress & Rate Limiter (Nginx)<br/>- Dịch vụ xác thực & Quản lý đàm thoại sư phạm (FastAPI)<br/>- Điều phối mô hình LLM & Failover<br/>- Cơ sở dữ liệu quan hệ (SQLite/PostgreSQL) & Cache (Redis)"]
    end

    subgraph ExternalCloud ["DỊCH VỤ NGOÀI INTERNET (EXTERNAL CLOUD SERVICES)"]
        Gemini["Google Gemini API<br/>[EXT-01: Primary LLM Provider]<br/>gemini-2.5-flash / pro<br/>Streaming Inference (HTTPS)"]
        OpenAI["OpenAI API<br/>[EXT-02: Fallback LLM Provider]<br/>gpt-4o-mini / gpt-4o<br/>Dự phòng khi Gemini sự cố (HTTPS)"]
        Claude["Anthropic Claude API<br/>[EXT-03: Secondary Fallback Provider]<br/>claude-3-5-sonnet (HTTPS)"]
    end

    %% Inbound Interactions
    Guest -->|"1. Đăng ký tài khoản & Đăng nhập<br/>[HTTPS:443 / JSON]"| AI_System
    User -->|"2. Luyện Kaiwa, gửi câu hỏi ngữ pháp & quản lý Rules<br/>[HTTPS:443 / JSON]"| AI_System
    AI_System -->|"3. Truyền luồng phản hồi token kèm Furigana & 3D Avatar Sync<br/>[Server-Sent Events (SSE)]"| User

    %% Outbound Cloud Integrations
    AI_System -->|"4. Yêu cầu sinh văn bản chính (Primary Request)<br/>[Outbound HTTPS / REST Stream]"| Gemini
    AI_System -.->|"5. Tự động chuyển vùng dự phòng khi lỗi 429/5xx/timeout<br/>[Outbound HTTPS Failover]"| OpenAI
    AI_System -.->|"6. Dự phòng cấp 2 (Secondary Failover)<br/>[Outbound HTTPS Failover]"| Claude

    style HumanActors fill:#eff6ff,stroke:#2563eb,stroke-width:1px
    style SystemBoundary fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style ExternalCloud fill:#fefce8,stroke:#ca8a04,stroke-width:1px
```

---

## 2. Thuyết Minh Ranh Giới Kỹ Thuật

1. **Bên trong ranh giới (In-Scope)**:
   - Toàn bộ giao diện Web Chat học tiếng Nhật (`ai-frontend` với 3D VRM Canvas), API Gateway & Rate Limiter (`nginx-gateway`), Server nghiệp vụ sư phạm (`ai-backend`), Database quan hệ (`postgres` / `sqlite`) và Cache phiên (`redis`).
2. **Bên ngoài ranh giới (External)**:
   - Thiết bị và trình duyệt của người dùng (Edge Browser hỗ trợ WebGL 2.0).
   - Nền tảng Google Gemini API, OpenAI API, Anthropic Claude API (Cloud PaaS/SaaS).
