# Kiến Trúc Kỹ Thuật & Hợp Đồng API: Voice Input & STT
## Phân Hệ: Voice Input & STT | Tính Năng: `FEAT-006`

## 1. Thiết Kế Kiến Trúc Module
Hệ thống Voice Input & STT tuân thủ nguyên tắc Clean Architecture và kiến trúc hướng dịch vụ (Service-Oriented Architecture):

```
┌────────────────────────────────────────────────────────┐
│               Trình Duyệt Client (Next.js)             │
│  - MediaRecorder + AudioContext (Thu âm 16-48kHz)      │
│  - WebM/Opus Chunker & Base64 / Binary Packager        │
│  - Audio Player Bar + Waveform Visualizer Component    │
└───────────────────────────▲────────────────────────────┘
                            │ REST / Multipart Upload
┌───────────────────────────▼────────────────────────────┐
│              FastAPI Gateway & STT Controller          │
│  - POST /api/v1/chat/stt                               │
│  - POST /api/v1/conversations/{id}/messages/stream     │
└───────────────────────────▲────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│ Dịch vụ STT Cốt Lõi   │       │ Quản lý Tệp Đính Kèm  │
│ (STT Service Engine)  │       │ (Attachment Service)  │
│ - Whisper / Gemini    │       │ - Magic Byte Check    │
│ - Multi-Language STT  │       │ - Anti-IDOR Isolation │
└───────────────────────┘       └───────────────────────┘
```

---

## 2. Đặc Tả Hợp Đồng Giao Diện API (API Contract)

### 2.1. Endpoint Chuyển Đổi Giọng Nói Thành Văn Bản (`OP-066`)
- **Đường dẫn**: `POST /api/v1/chat/stt`
- **Content-Type**: `multipart/form-data`
- **Xác thực**: Bắt buộc Session Cookie hoặc Bearer Token (`SEC-004`).
- **Tham số Form-Data**:
  - `file` (bắt buộc): Tệp âm thanh nhị phân (`audio/webm`, `audio/wav`, `audio/ogg`, `audio/mp4`). Dung lượng tối đa 10MB (`SEC-021`).
  - `language` (tùy chọn): Ngôn ngữ gợi ý (`vi`, `en`, `ja`, `auto`). Mặc định: `auto` (`BR-047`).
  - `duration_ms` (tùy chọn): Thời lượng đoạn ghi âm từ client tính bằng mili-giây.
- **Mã phản hồi thành công (HTTP 200 OK)**:
```json
{
  "status": "success",
  "data": {
    "attachment_id": "att_9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4",
    "filename": "voice_record_20261105_103000.webm",
    "audio_url": "/api/v1/attachments/att_9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4/download",
    "duration_ms": 4200,
    "transcript": "すみません、この電車は新宿に行きますか",
    "detected_language": "ja",
    "confidence": 0.985
  }
}
```

- **Mã phản hồi lỗi thường gặp**:
  - `HTTP 400 Bad Request`: `{"error_code": "INVALID_AUDIO_FORMAT", "message": "Định dạng tệp âm thanh không được hỗ trợ hoặc bị hỏng."}`
  - `HTTP 413 Payload Too Large`: `{"error_code": "FILE_TOO_LARGE", "message": "Tệp âm thanh vượt quá giới hạn 10MB cho phép."}`
  - `HTTP 429 Too Many Requests`: `{"error_code": "RATE_LIMIT_EXCEEDED", "message": "Tần suất gửi âm thanh vượt ngưỡng 30 req/min."}`

---

### 2.2. Endpoint Gửi Tin Nhắn Giọng Nói & Kích Hoạt Luồng AI (`OP-067`)
- **Đường dẫn**: `POST /api/v1/conversations/{conversation_id}/messages/stream`
- **Content-Type**: `application/json`
- **Body Request**:
```json
{
  "content": "すみません、この電車は新宿に行きますか",
  "attachments": ["att_9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4"],
  "model": "gemini-3.8-flash",
  "sensei_id": "sensei_sakura_n5",
  "language": "vi"
}
```
- **Xử lý phía Backend**:
  - Gắn `attachment_id` vào cột `audio_attachment_id` của bảng `messages`.
  - Khởi tạo luồng suy luận của AI Sensei và stream từng token phản hồi qua Server-Sent Events (SSE).

