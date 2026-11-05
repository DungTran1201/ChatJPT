# Phân Tích Tác Động Hệ Thống (Impact Analysis)
## Tính Năng: Multilingual Voice Input & Speech-to-Text (STT)

## 1. Bản Đồ Tác Động (Impact Matrix)

```
┌────────────────────────────────────────────────────────┐
│                   HỌC VIÊN NÓI VÀO MIC                 │
└───────────────────────────┬────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│ Client-side Audio Rec │       │ Client-side Live STT  │
│ MediaRecorder (Opus)  │       │ Web Speech API (opt)  │
└───────────┬───────────┘       └───────────┬───────────┘
            │                               │
            └───────────────┬───────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ UI: Preview Audio Waveform + Edit Transcript           │
└───────────────────────────┬────────────────────────────┘
                            │ Gửi tin nhắn giọng nói
                            ▼
┌────────────────────────────────────────────────────────┐
│ Backend API: POST /api/v1/chat/stt                     │
│ & POST /conversations/{id}/messages/audio-stream       │
└───────────────────────────┬────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│ Lưu Audio Attachment  │       │ Whisper/Gemini STT    │
│ CSDL: attachments     │       │ Transcribe Vi/En/Ja   │
└───────────┬───────────┘       └───────────┬───────────┘
            │                               │
            └───────────────┬───────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│ CSDL: Bảng messages (lưu transcript + audio_att_id)   │
│ AI LLM Core: Phân tích ngữ cảnh & sinh lời giải Sensei │
└────────────────────────────────────────────────────────┘
```

## 2. Chi Tiết Tác Động Các Lớp Hệ Thống

### 2.1. Tầng Giao Diện Người Dùng (Frontend UI/UX)
- [`ai-frontend/src/components/chat/MessageComposer.tsx`](file:///c:/Users/sv/Project/ChatJPT/ai-frontend/src/components/chat/MessageComposer.tsx): Bổ sung nút Microphone (`VoiceRecordButton`), thanh hiển thị trực quan âm lượng/sóng âm khi ghi âm (`WaveformVisualizer`), bộ chọn ngôn ngữ gợi ý (`vi`, `en`, `ja`, `auto`).
- [`ai-frontend/src/components/chat/ChatWorkspace.tsx`](file:///c:/Users/sv/Project/ChatJPT/ai-frontend/src/components/chat/ChatWorkspace.tsx): Cập nhật bong bóng tin nhắn người dùng (`UserMessageBubble`) để hiển thị trình phát âm thanh thu nhỏ (`AudioPlayerBar`) cùng dòng phụ đề văn bản chuyển đổi.
- [`ai-frontend/src/types/index.ts`](file:///c:/Users/sv/Project/ChatJPT/ai-frontend/src/types/index.ts): Bổ sung các trường `audio_url`, `audio_duration_ms`, `stt_language`, `stt_transcript` vào interface `Message`.

### 2.2. Tầng Máy Chủ Ứng Dụng (FastAPI Backend)
- [`ai-backend/src/api/v1/chat.py`](file:///c:/Users/sv/Project/ChatJPT/ai-backend/src/api/v1/chat.py): Bổ sung endpoint `POST /api/v1/chat/stt` nhận file âm thanh upload đa phần (multipart/form-data) và endpoint gửi tin nhắn âm thanh kèm SSE streaming.
- `ai-backend/src/services/stt_service.py`: Xây dựng dịch vụ STT chuyển đổi giọng nói độc lập hỗ trợ Whisper API / local whisper với tham số `language` linh hoạt (`vi`, `en`, `ja`).

### 2.3. Tầng Cơ Sở Dữ Liệu (Database Schema)
- Bảng `messages`: Bổ sung các cột:
  - `audio_attachment_id VARCHAR(36) REFERENCES attachments(id)`
  - `audio_duration_ms INTEGER DEFAULT 0`
  - `stt_language VARCHAR(10) DEFAULT 'auto'`
  - `stt_confidence REAL DEFAULT 1.0`

### 2.4. Tầng Bảo Mật & Rủi Ro (Security & Risk)
- **Kiểm soát dung lượng**: Giới hạn file âm thanh tối đa 10MB và thời lượng thu âm tối đa 120 giây (`BR-048`).
- **Xác thực MIME type**: Chặn mã độc giả mạo tệp âm thanh; chỉ chấp nhận `audio/webm`, `audio/ogg`, `audio/wav`, `audio/mp4` (`SEC-021`).
- **Quyền riêng tư (Privacy)**: Tệp ghi âm giọng nói của người dùng được phân quyền cô lập chống IDOR tương tự tin nhắn (`SEC-022`).

