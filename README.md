# ChatJPT — AI-Powered Japanese Learning Ecosystem
> Hệ sinh thái hỗ trợ học tiếng Nhật toàn diện tích hợp Trợ lý ảo AI 3D (Virtual Sensei), Luyện Kaiwa phản xạ, Chấm chữa ngữ pháp (Grammar Doctor), và Phân tích Hán tự chuyên sâu.

---

## 🌸 Giới thiệu dự án (Project Overview)

**ChatJPT** là một nền tảng hỗ trợ học tiếng Nhật thông minh được phát triển trên kiến trúc Fullstack hiện đại kết hợp Trợ lý ảo AI 3D tương tác theo thời gian thực. Hệ thống chuyển đổi việc học tiếng Nhật truyền thống thành một trải nghiệm cá nhân hóa, trực quan và sinh động:

- **Virtual Sensei (Trợ lý ảo 3D VRM)**: Tương tác qua giọng nói và văn bản cùng nhân vật 3D biểu cảm tự nhiên (Three.js + `@pixiv/three-vrm`), hỗ trợ khẩu hình (viseme) và chuyển động cảm xúc.
- **Kaiwa Roleplay Studio**: Luyện giao tiếp phản xạ theo các tình huống thực tế (phỏng vấn baito, mua sắm konbini, giao tiếp công sở Keigo) phân loại theo chuẩn JLPT từ N5 đến N1.
- **AI Grammar Doctor**: Phân tích lỗi ngữ pháp, giải thích sắc thái từ vựng (nuance), và đề xuất cách diễn đạt tự nhiên chuẩn người bản xứ.
- **Kanji & Vocabulary Breakdown**: Hiển thị Furigana, Onyomi, Kunyomi, số nét và từ vựng liên quan trực tiếp trong giao diện chat.
- **Đa kênh học tập (Multi-channel Ecosystem)**: Học tập đồng bộ trên Web App và Discord Bot cộng đồng.

---

## 🏛️ Kiến trúc công nghệ (Technical Architecture)

Dự án được xây dựng dựa trên kiến trúc phân lớp hướng đối tượng với độ chịu lỗi và tính sẵn sàng cao:

```
┌────────────────────────────────────────────────────────┐
│             ChatJPT Web App (Next.js 16)               │
│  - Three.js + @pixiv/three-vrm 3D Avatar (AI-Chan)    │
│  - React 19 + Tailwind CSS + Lucide Icons             │
│  - Live SSE Markdown Stream + Furigana/Ruby Display   │
└───────────────────────────▲────────────────────────────┘
                            │ REST / SSE Stream
┌───────────────────────────▼────────────────────────────┐
│          FastAPI Core Backend (Python 3.10+)           │
│  - ProjectChatTurnManager (Detached Background Turns)  │
│  - LangGraph Multi-Provider Failover (Gemini/OpenAI)   │
│  - AES-256 Encrypted Credential Vault                  │
│  - Japanese Pedagogy Tool Registry (32 Tools)          │
│  - SQLite (WAL Mode) / PostgreSQL Database             │
└───────────────────────────▲────────────────────────────┘
                            │ Shared Project Graphs
┌───────────────────────────▼────────────────────────────┐
│            Discord Community Bot (Dororo)              │
│  - Discord.py Multi-Bot Gateway                        │
│  - Real-time Q&A, Daily Kanji / Vocabulary Flashcard   │
└────────────────────────────────────────────────────────┘
```

---

## 📂 Cấu trúc thư mục (Key Directories)

- `docs/` — Toàn bộ tài liệu kỹ thuật BA, PM, Kiến trúc (SRS, PDP, SAD, Test Cases, Security).
  - `docs/01-planning/` — Kế hoạch tổng thể phát triển dự án (`project-development-plan.md`).
  - `docs/02-requirements/` — Đặc tả yêu cầu phần mềm chuẩn ISO/IEC/IEEE 29148 (`SRS.md`).
  - `docs/05-system-analysis/` — Phân tích ngữ cảnh hệ thống (`system-context.md`).
- `models/` — Canonical structured models (YAML): `system-context.yaml`, `requirements.yaml`, `architecture.yaml`, `api.yaml`.
- `ai-backend/` — FastAPI backend service với LangGraph engine và credential management.
- `ai-frontend/` — Next.js 16 App Router UI với 3D VRM Canvas và Conversation Workspace.
- `discord-bot/` — Daemon bot Discord kết nối cộng đồng.
- `tools/validators/` — Bộ công cụ deterministic validation bảo đảm tính toàn vẹn tài liệu và mã nguồn.
- `.agents/` — Quy tắc, kỹ năng, và subagents của Antigravity AI Engineering.

---

## 🚀 Khởi chạy nhanh (Quick Start)

Để khởi động toàn bộ hệ thống ChatJPT (Backend API, Frontend Web, và Discord Bot) chỉ bằng một lệnh:

```cmd
run-demo.bat
```

Mỗi dịch vụ sẽ được khởi chạy trong cửa sổ **Command Prompt (`cmd.exe`)** riêng biệt với live log streaming:
- **Backend API**: `http://127.0.0.1:8000` (Swagger docs: `/docs`)
- **Frontend App**: `http://localhost:3000`
- **Discord Bot**: `Dororo Gateway` (nếu đã cấu hình token)

### Lệnh tiện ích quản lý
- **Kiểm tra trạng thái hệ thống**: `run-demo.bat --check`
- **Dừng toàn bộ dịch vụ an toàn**: `run-demo.bat --stop`
- **Chạy chế độ gom một cửa sổ (Single console)**: `run-demo.bat --single-console`
- **Không tự động mở trình duyệt**: `run-demo.bat --no-browser`
- **Bỏ qua Discord Bot**: `run-demo.bat --no-discord`

---

## 🔍 Tiêu chuẩn kỹ thuật & Đảm bảo chất lượng

Dự án tuân thủ nghiêm ngặt quy trình kỹ nghệ phần mềm Antigravity BA:
1. **Kiểm tra tính nhất quán (Validation)**:
   ```cmd
   python tools/validators/run_all.py
   ```
2. **Nguyên tắc định danh duy nhất**: Toàn bộ yêu cầu (`FR-###`), quy tắc nghiệp vụ (`BR-###`), bảo mật (`SEC-###`), và kiến trúc (`ARCH-###`) được duy trì bất biến xuyên suốt các lớp tài liệu và mã nguồn.
3. **Bảo mật**: Tuyệt đối không lưu trữ khóa API hoặc thông tin nhạy cảm trong mã nguồn; sử dụng AES-256 mã hóa cấu hình trong database.
