# Biểu Đồ Phân Làn Swimlane: Quy Trình Thu Âm, Nhận Diện Giọng Nói & Phản Hồi AI
## Phân Làn Trách Nhiệm: `SWIM-VOICE-CHAT` | Tham Chiếu: `FR-079`, `FR-080`, `FR-081`, `FR-082`

Biểu đồ Swimlane phân định rõ ranh giới trách nhiệm giữa Học viên, Trình duyệt Web Client, Máy chủ FastAPI Backend, Dịch vụ Nhận diện STT và Mô hình AI Ngôn ngữ.

```mermaid
sequenceDiagram
    autonumber
    box rgb(240, 249, 255) TÁC NHÂN NGƯỜI DÙNG & TRÌNH DUYỆT (Next.js Client)
        actor User as "Học viên (ACT-02)"
        participant UI as "Next.js UI (MessageComposer & ChatWorkspace)"
        participant WebAudio as "Web Audio & MediaRecorder Engine"
    end
    box rgb(253, 244, 255) TẦNG DỊCH VỤ MÁY CHỦ (FastAPI Core)
        participant API as "FastAPI Gateway (/api/v1/*)"
        participant Storage as "Attachment & Database Service"
    end
    box rgb(254, 252, 232) TẦNG ĐIỀU PHỐI AI & STT NGOÀI
        participant STTEngine as "Whisper / Gemini STT Service"
        participant LLMEngine as "LangGraph AI Orchestrator"
    end

    %% Giai đoạn 1: Thu âm
    User->>UI: Nhấn giữ / Nhấn nút Mic & Chọn tiếng Nhật (ja) [FR-079]
    UI->>WebAudio: Khởi tạo MediaStream & AudioContext
    WebAudio-->>UI: Cung cấp mảng tần số âm thanh (Frequency Data)
    UI-->>User: Hiển thị thanh sóng âm động & đếm thời lượng ghi âm [UX-015]
    User->>UI: Nhấn Dừng thu âm (Stop)
    UI->>WebAudio: Kết thúc ghi luồng & đóng gói file WebM/Opus (< 10MB)

    %% Giai đoạn 2: Xử lý STT
    UI->>API: Gửi file âm thanh qua POST /api/v1/chat/stt [OP-066]
    API->>API: Xác thực Magic Bytes & giới hạn an ninh (SEC-021)
    API->>Storage: Ghi tệp âm thanh vào thư mục data/storage/attachments/
    API->>STTEngine: Chuyển tiếp audio buffer kèm language_hint="ja" [FR-080]
    STTEngine-->>API: Trả về kết quả: {transcript, detected_language, confidence}
    API-->>UI: Phản hồi JSON chứa URL âm thanh & đoạn văn bản STT

    %% Giai đoạn 3: Hiển thị kép và Gửi vào LLM
    UI->>UI: Render tin nhắn User với 2 phần tử đồng bộ:<br/>1. Trình phát âm thanh (Audio Waveform Player)<br/>2. Đoạn văn bản vừa nói (Transcript) [FR-081, BR-050]
    UI->>API: POST /conversations/{id}/messages/stream (content=transcript) [FR-082]
    API->>Storage: Ghi tin nhắn User vào CSDL kèm audio_attachment_id
    API->>LLMEngine: Khởi chạy đồ thị LangGraph với câu hỏi người dùng
    LLMEngine-->>API: Stream từng token phản hồi qua SSE (chunk events)
    API-->>UI: Đẩy dòng SSE token về trình duyệt
    UI-->>User: Hiển thị câu trả lời sư phạm của Sensei theo thời gian thực
```

## Nguồn Tham Chiếu
- Vai trò & Làn phân công: `User`, `UI`, `WebAudio`, `API`, `Storage`, `STTEngine`, `LLMEngine`.
- Yêu cầu liên kết: `FR-079`, `FR-080`, `FR-081`, `FR-082`, `BR-047`, `BR-050`.

