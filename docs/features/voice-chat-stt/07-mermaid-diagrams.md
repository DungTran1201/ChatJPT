# Tổng Hợp Biểu Đồ Trực Quan Mermaid: Voice Input & STT
## Phân Hệ: Voice Input & STT | Tính Năng: `FEAT-006`

Tài liệu này tổng hợp toàn bộ các biểu đồ kỹ thuật phục vụ việc phát triển, kiểm thử và bảo trì tính năng Thu âm Giọng nói Đa ngữ & STT.

---

## 1. Biểu Đồ Tuần Tự (Sequence Diagram - `SEQ-018`)

```mermaid
sequenceDiagram
    actor Learner as "Học viên (ACT-02)"
    participant UI as "Next.js UI (MessageComposer)"
    participant AudioAPI as "Browser Web Audio API"
    participant API as "FastAPI Backend (/api/v1/chat/stt)"
    participant STT as "Whisper / Gemini STT Engine"
    participant LLM as "LangGraph AI Agent"

    Learner->>UI: Bấm nút Microphone & Chọn tiếng Nhật
    UI->>AudioAPI: Khởi động MediaRecorder (WebM/Opus)
    AudioAPI-->>UI: Cung cấp sóng âm trực tiếp
    Learner->>UI: Bấm nút Gửi tin nhắn
    UI->>AudioAPI: Thu thập Blob âm thanh hoàn chỉnh
    UI->>API: POST /api/v1/chat/stt (audio_file)
    API->>STT: Chuyển đổi âm thanh thành văn bản
    STT-->>API: Trả về {transcript, language, confidence}
    API-->>UI: Phản hồi JSON chứa audio_url & transcript
    UI->>UI: Render bong bóng tin nhắn: Audio Player + Transcript
    UI->>API: POST /conversations/{id}/messages/stream
    API->>LLM: Gửi prompt văn bản vào mô hình AI
    LLM-->>UI: Stream câu trả lời của Sensei qua SSE
```

---

## 2. Biểu Đồ Luồng Nghiệp Vụ (BPMN - `PROC-VOICE-CHAT`)

```mermaid
flowchart TD
    StartEvent(("Bắt đầu nói")) --> SelectLang["Chọn tiếng Việt / Anh / Nhật"]
    SelectLang --> StartRecord["Bắt đầu thu âm"]
    StartRecord --> CheckTime{"Thời lượng >= 120s?"}
    CheckTime -- Có --> AutoStop["Tự động dừng thu âm"]
    CheckTime -- Không --> ManualStop["Bấm Dừng thủ công"]
    AutoStop --> Upload["Gửi âm thanh lên Backend"]
    ManualStop --> Upload
    Upload --> STTProcess["Xử lý STT đa ngữ"]
    STTProcess --> DisplayDual["Hiển thị Audio Player & Văn bản"]
    DisplayDual --> StreamAI["AI phản hồi câu trả lời sư phạm"]
    StreamAI --> EndEvent(("Kết thúc"))
```

---

## 3. Biểu Đồ Vòng Đời Trạng Thái (State Diagram - `STATE-VOICE-INPUT`)

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> RECORDING : Nhấn nút Mic
    RECORDING --> PAUSED : Nhấn Tạm dừng
    PAUSED --> RECORDING : Nhấn Tiếp tục
    RECORDING --> TRANSCRIBING : Nhấn Dừng/Gửi hoặc 120s
    RECORDING --> IDLE : Nhấn Hủy (Trash)
    TRANSCRIBING --> READY_IN_CHAT : STT thành công
    READY_IN_CHAT --> PLAYING_AUDIO : Nhấn nút Play
    PLAYING_AUDIO --> READY_IN_CHAT : Hết audio hoặc bấm Pause
    READY_IN_CHAT --> IDLE : Thu âm lượt tiếp theo
```

