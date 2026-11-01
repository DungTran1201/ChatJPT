# ChatJPT — AI-Powered Japanese Learning Ecosystem
> Hệ sinh thái hỗ trợ học tiếng Nhật toàn diện tích hợp Trợ lý ảo AI 3D (Virtual Sensei), Luyện Kaiwa phản xạ, Chấm chữa ngữ pháp (Grammar Doctor), và Phân tích Hán tự chuyên sâu.

---

## 🌸 Giới thiệu dự án (Project Overview)

**ChatJPT** là một nền tảng hỗ trợ học tiếng Nhật thông minh được phát triển trên kiến trúc Fullstack hiện đại kết hợp Trợ lý ảo AI 3D tương tác theo thời gian thực. Hệ thống chuyển đổi việc học tiếng Nhật truyền thống thành một trải nghiệm cá nhân hóa, trực quan và sinh động:

- **Virtual Sensei (Trợ lý ảo 3D VRM)**: Tương tác qua văn bản và biểu cảm cùng nhân vật 3D tự nhiên (Three.js + `@pixiv/three-vrm`), hỗ trợ xoay 360 độ, cử chỉ động viên và chuyển động cảm xúc.
- **Kaiwa Roleplay Studio**: Luyện giao tiếp phản xạ theo các tình huống thực tế (phỏng vấn baito, mua sắm konbini, giao tiếp công sở Keigo) phân loại theo chuẩn JLPT từ N5 đến N1.
- **AI Grammar Doctor**: Phân tích lỗi ngữ pháp, giải thích sắc thái từ vựng (nuance), và đề xuất cách diễn đạt tự nhiên chuẩn người bản xứ.
- **Kanji & Vocabulary Breakdown**: Hiển thị Furigana, Onyomi, Kunyomi, số nét và từ vựng liên quan trực tiếp trong giao diện chat.
- **Quản lý Quy tắc & Prompts Sư phạm (Rules & Prompts)**: Tùy biến linh hoạt System Prompts và Rules theo trình độ JLPT (N5 - N1) với cơ chế kích hoạt tự động (`always_on`, `model_decision`, `glob`, `manual`).
- **Tùy biến Khóa API cá nhân (BYOK)**: Cho phép học viên kết nối API Key riêng (Google Gemini, OpenAI, Claude, OpenRouter, DeepSeek, Groq) với cơ chế mã hóa AES-256 an toàn.

---

## 🏛️ Kiến trúc công nghệ (Technical Architecture)

Dự án được xây dựng dựa trên kiến trúc phân lớp hướng đối tượng với độ chịu lỗi và tính sẵn sàng cao:

```
┌────────────────────────────────────────────────────────┐
│             ChatJPT Web App (Next.js 16)               │
│  - Three.js + @pixiv/three-vrm 3D Avatar (AI-Chan)    │
│  - React 19 + Tailwind CSS + Lucide Icons             │
│  - Live SSE Markdown Stream + Furigana/Ruby Display   │
│  - Rules & Prompts Sư phạm Management UI               │
└───────────────────────────▲────────────────────────────┘
                            │ REST / SSE Stream
┌───────────────────────────▼────────────────────────────┐
│          FastAPI Core Backend (Python 3.10+)           │
│  - LangGraph Multi-Provider Failover (Gemini/OpenAI)   │
│  - AES-256 Encrypted Credential Vault (BYOK Keys)      │
│  - Pedagogy Rules & System Prompts Execution Engine    │
│  - Attachment & Document Ingestion Service             │
│  - SQLite (WAL Mode) / PostgreSQL Database             │
└────────────────────────────────────────────────────────┘
```

---

## 📂 Cấu trúc thư mục (Key Directories)

- `docs/` — Toàn bộ tài liệu kỹ thuật BA, PM, Kiến trúc (SRS, PDP, SAD, Test Cases, Security).
  - `docs/01-planning/` — Kế hoạch tổng thể phát triển dự án (`project-development-plan.md`).
  - `docs/02-requirements/` — Đặc tả yêu cầu phần mềm chuẩn ISO/IEC/IEEE 29148 (`SRS.md`).
  - `docs/05-system-analysis/` — Phân tích ngữ cảnh hệ thống (`system-context.md`).
- `models/` — Canonical structured models (YAML): `system-context.yaml`, `requirements.yaml`, `domain.yaml`, `api.yaml`, `architecture.yaml`, `deployment.yaml`.
- `ai-backend/` — FastAPI backend service với LangGraph engine, Rules & Prompts, và credential vault.
- `ai-frontend/` — Next.js 16 App Router UI với 3D VRM Canvas, Conversation Workspace, và Rules/Prompts manager.
- `tools/validators/` — Bộ công cụ deterministic validation bảo đảm tính toàn vẹn tài liệu và mã nguồn.
- `.agents/` — Quy tắc, kỹ năng, và subagents của Antigravity AI Engineering.

---

## 🚀 Khởi chạy nhanh (Quick Start)

Để khởi động toàn bộ hệ thống ChatJPT (Backend API và Frontend Web) chỉ bằng một lệnh:

```cmd
run-demo.bat
```

Mỗi dịch vụ sẽ được khởi chạy trong cửa sổ **Command Prompt (`cmd.exe`)** riêng biệt với live log streaming:
- **Backend API**: `http://127.0.0.1:8000` (Swagger docs: `/docs`)
- **Frontend App**: `http://localhost:3000`
- **Rules & Prompts**: `http://localhost:3000/rules`

### Lệnh tiện ích quản lý
- **Kiểm tra trạng thái hệ thống**: `run-demo.bat --check`
- **Dừng toàn bộ dịch vụ an toàn**: `run-demo.bat --stop`
- **Chạy chế độ gom một cửa sổ (Single console)**: `run-demo.bat --single-console`
- **Không tự động mở trình duyệt**: `run-demo.bat --no-browser`

---

## 🔍 Tiêu chuẩn kỹ thuật & Đảm bảo chất lượng

Dự án tuân thủ nghiêm ngặt quy trình kỹ nghệ phần mềm Antigravity BA:
1. **Kiểm tra tính nhất quán (Validation)**:
   ```cmd
   ai-backend\.venv\Scripts\python.exe tools/validators/run_all.py
   ```
2. **Nguyên tắc định danh duy nhất**: Toàn bộ yêu cầu (`FR-###`), quy tắc nghiệp vụ (`BR-###`), bảo mật (`SEC-###`), và kiến trúc (`ARCH-###`) được duy trì bất biến xuyên suốt các lớp tài liệu và mã nguồn.
3. **Bảo mật**: Tuyệt đối không lưu trữ khóa API hoặc thông tin nhạy cảm trong mã nguồn; sử dụng AES-256 mã hóa cấu hình trong database.
