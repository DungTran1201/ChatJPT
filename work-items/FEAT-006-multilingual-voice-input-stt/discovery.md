# Báo Cáo Khảo Sát & Đánh Giá Hiện Trạng (Discovery Analysis)
## Tính Năng: Multilingual Voice Input & Speech-to-Text (STT)

## 1. Hiện Trạng Hệ Thống (As-Is State)
- **Đầu vào hiện tại**: Giao diện [`MessageComposer.tsx`](file:///c:/Users/sv/Project/ChatJPT/ai-frontend/src/components/chat/MessageComposer.tsx) hiện chỉ nhận dữ liệu văn bản gõ tay qua `textarea` và tệp văn bản đính kèm qua [`AttachmentUploader.tsx`](file:///c:/Users/sv/Project/ChatJPT/ai-frontend/src/components/ui/AttachmentUploader.tsx).
- **Hạ tầng âm thanh hiện có**: Đã có hệ thống VOICEVOX Text-to-Speech (TTS) tại [`ai-backend/src/api/v1/voices.py`](file:///c:/Users/sv/Project/ChatJPT/ai-backend/src/api/v1/voices.py) phục vụ phát âm câu trả lời của Sensei (`FR-069` đến `FR-073`), nhưng **chưa có chiều ngược lại** (Speech-to-Text từ người dùng).
- **Lưu trữ tệp đính kèm**: Bảng `attachments` trong SQLite/PostgreSQL đã hỗ trợ lưu trữ tệp tin với đường dẫn cục bộ và MIME type (`audio/webm`, `audio/wav`, `audio/mp4`).

## 2. Khoảng Trống & Thách Thức (Gap Analysis)
| Hạng mục | Hiện trạng (As-Is) | Mục tiêu (To-Be) |
| :--- | :--- | :--- |
| **Microphone Capture** | Chưa hỗ trợ trên giao diện chat | Tích hợp Web Audio API + MediaStream Recording với WebM/Opus |
| **Speech Recognition** | Không có module STT | Tích hợp Dual-Engine: OpenAI Whisper / Faster-Whisper + Fallback Web Speech API |
| **Đa ngôn ngữ** | Chỉ cấu hình TTS tiếng Nhật | Hỗ trợ chuẩn xác 3 ngôn ngữ: `vi`, `en`, `ja` |
| **UI Message Bubble** | Tin nhắn User chỉ hiển thị raw text | Tin nhắn User hiển thị Audio Waveform Player + STT Transcribed Text |
| **LLM Ingestion** | Luồng `POST .../messages/stream` chỉ nhận string | Endpoint hỗ trợ trực tiếp STT transcription flow |

## 3. Đánh Giá Giải Pháp Công Nghệ STT
1. **Phương án 1 (OpenAI Whisper / Groq Whisper / Faster-Whisper Backend)**:
   - *Ưu điểm*: Chất lượng nhận diện vượt trội, chuẩn ngữ điệu cả tiếng Nhật, tiếng Việt và tiếng Anh; không phụ thuộc vào trình duyệt của người dùng.
   - *Độ trễ*: 400ms - 1.2s đối với đoạn âm thanh ngắn (< 15 giây).
2. **Phương án 2 (Web Speech API Client-side `webkitSpeechRecognition`)**:
   - *Ưu điểm*: 0 latency chuyển đổi, không tốn tài nguyên server backend, hoàn toàn miễn phí.
   - *Nhược điểm*: Phụ thuộc vào trình duyệt (Chrome/Edge hỗ trợ tốt, Firefox/Safari hạn chế), không tự động lưu file audio wav/webm chất lượng cao.
3. **Quyết định kiến trúc (Hybrid Dual-Mode)**:
   - Cho phép thu âm WebM/Opus chất lượng cao gửi về Backend xử lý STT chuẩn xác qua Whisper/Gemini Multimodal, đồng thời kích hoạt Web Speech API preview trực tiếp trên giao diện để người dùng thấy chữ chạy ngay khi đang nói.

