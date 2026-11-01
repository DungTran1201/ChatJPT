# NGỮ CẢNH HỆ THỐNG & RANH GIỚI HOẠT ĐỘNG (SYSTEM CONTEXT & BOUNDARY)
## Hệ Thống ChatJPT — Hệ Sinh Thái Hỗ Trợ Học Tiếng Nhật Thông Minh

---

| Thông Tin Tài Liệu | Chi Tiết |
| :--- | :--- |
| **Dự án** | ChatJPT — Hệ Sinh Thái Hỗ Trợ Học Tiếng Nhật (`ChatJPT`) |
| **Mã tài liệu** | `SYS-CTX-001` |
| **Trạng thái Baseline** | **BASELINED** |
| **Mục đích** | Định vị ranh giới hệ thống, các đối tượng tác nhân học tập và các giao thức kết nối ngoại vi cho nền tảng học tiếng Nhật tích hợp AI Chatbot và Gia sư ảo 3D VRM |

---

## 1. Sơ Đồ Ngữ Cảnh Hệ Thống (System Context Diagram)

```mermaid
flowchart TD
    subgraph ExternalUsers ["TÁC NHÂN HỌC TẬP & VẬN HÀNH (HUMAN ACTORS)"]
        Guest["Khách Vãng Lai / Học Viên Thử Nghiệm<br/>(ACT-01: Guest / Trial Learner)"]
        Learner["Học Viên Tiếng Nhật (JLPT & Kaiwa)<br/>(ACT-02: Japanese Learner)"]
        Teacher["Giáo Viên / Người Hướng Dẫn<br/>(ACT-03: Japanese Educator / Sensei Creator)"]
        Admin["Quản Trị Viên Hệ Thống<br/>(ACT-04: System Admin)"]
    end

    subgraph SystemScope ["HỆ SINH THÁI HỌC TIẾNG NHẬT CHATJPT (IN-SCOPE)"]
        ChatJPT_System["Hệ Thống ChatJPT Platform<br/>- Giao diện Web Học Tập & 3D VRM Sensei Companion<br/>- API Gateway, Telemetry Middleware & Rate Limiter<br/>- Dịch vụ Xác Thực & Lưu Trữ Lịch Sử Học Tập Cá Nhân<br/>- Bộ Điều Phối AI Sư Phạm (Multi-Provider Orchestrator)<br/>- Thư Viện Quy Tắc Ngữ Pháp & Chỉ Dẫn Sensei Prompts<br/>- Quản Lý Tệp Đính Kèm Học Liệu & Khóa BYOK API Keys<br/>- Cơ Sở Dữ Liệu Học Liệu & Tiến Độ Học Tập"]
    end

    subgraph ExternalSystems ["DỊCH VỤ NGOẠI VI (EXTERNAL SERVICES)"]
        GeminiAPI["Google Gemini API<br/>(Primary LLM: Phân tích ngữ pháp, Kanji, dịch thuật, streaming tốc độ cao)"]
        OpenAIAPI["OpenAI API<br/>(Secondary/Failover LLM: Đánh giá ngữ pháp nâng cao, sinh đề thi JLPT)"]
        ClaudeAPI["Anthropic Claude API<br/>(Contextual LLM: Đàm thoại Kaiwa tự nhiên, Kính ngữ Keigo, văn hóa Nhật)"]
        OllamaLocal["Ollama Local Model<br/>(Mô hình ngôn ngữ tiếng Nhật cục bộ / offline)"]
    end

    %% Inbound Connections
    Guest -->|1. Trải nghiệm thử thách tiếng Nhật, đăng ký tài khoản (HTTPS)| ChatJPT_System
    Learner -->|2. Luyện thi JLPT, tra cứu Kanji, Kaiwa với 3D VRM Sensei (HTTPS / SSE)| ChatJPT_System
    Teacher -->|3. Tùy chỉnh quy tắc ngữ pháp, prompt Sensei chuyên đề (HTTPS)| ChatJPT_System
    Admin -->|4. Quản lý mô hình, quota và vận hành hệ thống (HTTPS)| ChatJPT_System

    %% Outbound Connections
    ChatJPT_System -->|5. Streaming Inference & Grammar Doctor (HTTPS)| GeminiAPI
    ChatJPT_System -.->|6. Failover / Advanced Evaluation (HTTPS)| OpenAIAPI
    ChatJPT_System -.->|7. Nuanced Kaiwa Dialogue (HTTPS)| ClaudeAPI
    ChatJPT_System -.->|8. Local Inference (HTTP)| OllamaLocal

    style SystemScope fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style ExternalUsers fill:#eff6ff,stroke:#2563eb
    style ExternalSystems fill:#fefce8,stroke:#ca8a04
```

---

## 2. Phân Định Ranh Giới Hệ Thống (System Boundary Definition)

### 2.1 Thành Phần Nằm Trong Ranh Giới (Inside System Boundary)
- **Tầng Trình Diễn Học Tập (Presentation & 3D VRM Stage)**:
  - Cung cấp giao diện web responsive tối ưu cho học tập ngôn ngữ (hỗ trợ hiển thị Furigana, Romaji, Kanji, định dạng Markdown giải thích ngữ pháp).
  - Trình diện Gia sư ảo 3D VRM (AI-Chan Sensei) tương tác biểu cảm, chuyển động tự nhiên (thở, chớp mắt, cử chỉ khuyến khích khi học viên phản xạ đúng).
  - Không gian Luyện Kaiwa trực quan, hiển thị các gợi ý đàm thoại và phân tích câu thoại theo thời gian thực.
- **Tầng Kiểm Soát Tải, An Ninh & Quota (Security & Quota Guard)**:
  - Kiểm soát tần suất 2 tầng (`BP-SEC-001`), xác thực JWT Cookie bảo vệ phiên học.
  - Quản lý định mức token học tập hàng ngày (`quota_manager`), ngăn ngừa lạm dụng chi phí AI.
  - Mã hóa an toàn khóa API cá nhân của học viên qua chuẩn AES-256-GCM (`SEC-015`).
- **Tầng Xử Lý Nghiệp Vụ Sư Phạm (Application & Pedagogy Services)**:
  - Quản lý hồ sơ học viên, lộ trình ôn tập JLPT (từ N5 đến N1), lịch sử hội thoại và ngữ cảnh bài học.
  - Quản lý thư viện Quy tắc ngữ pháp (Grammar Rules) và Chỉ dẫn sư phạm (System Prompts).
- **Tầng Điều Phối AI Ngôn Ngữ (Japanese AI Orchestration)**:
  - Tích hợp Prompt Engineering chuyên sâu về tiếng Nhật: Sửa lỗi câu (Grammar Doctor), Phân tích Hán tự (Kanji Breakdown), Phản xạ giao tiếp (Kaiwa Roleplay), Kính ngữ thương mại (Business Keigo).
  - Cơ chế tự động Failover giữa Gemini, OpenAI và Claude đảm bảo việc học không bao giờ bị gián đoạn.
- **Tầng Lưu Trữ Học Liệu & Tiến Độ (Persistence)**:
  - Quản lý người dùng, lịch sử chat, system prompts, rules ngữ pháp, tệp đính kèm học liệu và định mức sử dụng trong SQLite.

### 2.2 Thành Phần Nằm Ngoài Ranh Giới (Outside System Boundary)
- **Trình duyệt học viên (Client Web Browser)**: Môi trường phía người dùng (Chrome, Edge, Firefox, Safari) hỗ trợ WebGL và Audio/Fetch Streams.
- **Google Gemini API**: Đám mây trí tuệ nhân tạo của Google, phục vụ phân tích ngữ pháp nhanh và stream dữ liệu.
- **OpenAI API**: Đám mây trí tuệ nhân tạo của OpenAI, phục vụ dự phòng và sinh đề thi kiểm tra nâng cao.
- **Anthropic Claude API**: Đám mây AI phục vụ đàm thoại tiếng Nhật tự nhiên, tinh tế và chuẩn ngữ cảnh văn hóa.
- **Ollama Local**: Dịch vụ suy luận mô hình ngôn ngữ tiếng Nhật chạy offline cục bộ trên máy trạm của người dùng.

---

## 3. Giao Diện Tương Tác Ngoại Vi (External Interfaces)

| Giao Diện Ngoại Vi | Hướng Truyền | Giao Thức / Định Dạng | Mô Tả & Vai Trò | Ràng Buộc / SLA |
| :--- | :--- | :--- | :--- | :--- |
| **Web Learning Interface** | Inbound | HTTPS / JSON & Server-Sent Events (SSE) | Nhận yêu cầu học tập, câu hỏi luyện tập và trả về dữ liệu token stream kèm cấu trúc ngữ pháp thời gian thực. | Rate Limit 10 r/s (Ingress), 60 r/min (API). Độ trễ phản hồi ban đầu TTFT < 2s (`NFR-003`). |
| **Google Gemini API** | Outbound | HTTPS / Streaming REST (Google GenAI) | Gửi prompt kèm ngữ cảnh bài học tiếng Nhật, nhận luồng phân tích ngữ pháp và dịch thuật song ngữ. | Timeout 30s (`NFR-008`). Chuyển vùng khi gặp lỗi 429 hoặc 5xx. |
| **OpenAI API** | Outbound | HTTPS / Streaming REST (OpenAI SDK) | Tiếp nhận yêu cầu dự phòng khi Gemini gặp sự cố (`BR-005`), hoặc xử lý các bài kiểm tra logic ngữ pháp phức tạp. | Kích hoạt tự động, trong suốt với học viên. |
| **Anthropic Claude API** | Outbound | HTTPS / Streaming REST | Xử lý các bài đàm thoại Kaiwa tình huống đòi hỏi ngữ điệu lịch sự, sắc thái kính ngữ và bối cảnh văn hóa Nhật Bản. | Kích hoạt theo lựa chọn mô hình của học viên. |
| **Ollama Local API** | Outbound | HTTP / REST Streaming | Thực thi mô hình cục bộ khi học viên chọn chế độ ngoại tuyến không tốn chi phí token đám mây. | Tùy thuộc vào phần cứng cục bộ. |
