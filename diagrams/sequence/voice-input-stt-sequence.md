# Biểu Đồ Tuần Tự: Thu Âm Giọng Nói Đa Ngữ, Chuyển Đổi STT & Phản Hồi AI Thời Gian Thực
## Mã Kịch Bản: `SEQ-018` | Tính Năng: `FR-079`, `FR-080`, `FR-081`, `FR-082`

Biểu đồ mô tả chi tiết dòng tương tác đầu cuối từ khi Người học (`ACT-02`) kích hoạt nút thu âm giọng nói trên giao diện Next.js, chuyển đổi qua dịch vụ STT, hiển thị đồng thời sóng âm và văn bản chuyển đổi trên Chat, cho đến khi mô hình LLM tiếp nhận và phản hồi luồng SSE.

```mermaid
sequenceDiagram
    autonumber
    actor Learner as "ACT-02: Học viên (User)"
    participant Composer as "Next.js: MessageComposer"
    participant AudioRec as "Frontend: AudioRecorder (MediaRecorder)"
    participant ChatView as "Next.js: ChatWorkspace (AudioBubble)"
    participant BackendAPI as "FastAPI: /api/v1/chat/stt & stream"
    participant STTService as "Core: STT Service (Whisper/Gemini)"
    participant Database as "SQLite: attachments & messages"
    participant LLM as "LangGraph: LLM Multi-Provider"

    Note over Learner, Composer: 1. Khởi tạo & Thu âm Giọng nói (FR-079, BR-047)
    Learner->>Composer: Nhấn biểu tượng Microphone & chọn ngôn ngữ (vi / en / ja / auto)
    Composer->>AudioRec: Yêu cầu quyền truy cập mic (navigator.mediaDevices.getUserMedia)
    AudioRec-->>Composer: Quyền mic được chấp thuận (Permission Granted)
    AudioRec->>AudioRec: Bắt đầu ghi luồng âm thanh Opus/WebM & đếm thời gian (max 120s - BR-048)
    Composer-->>Learner: Hiển thị thanh Waveform trực quan & nút Stop / Pause / Discard

    Note over Learner, AudioRec: 2. Kết thúc thu âm & Xử lý STT (FR-080, BR-049)
    Learner->>Composer: Nhấn nút Dừng thu âm (Stop / Send)
    AudioRec->>Composer: Đóng gói Audio Blob (MIME: audio/webm, dung lượng < 10MB - SEC-021)
    Composer->>BackendAPI: POST /api/v1/chat/stt (FormData: audio_file, language_hint)
    BackendAPI->>BackendAPI: Kiểm tra Magic Bytes & giới hạn dung lượng (SEC-021)
    BackendAPI->>STTService: Chuyển đổi giọng nói thành văn bản (Transcribe vi/en/ja)
    STTService-->>BackendAPI: Trả về transcript_text, detected_language, confidence
    BackendAPI->>Database: Lưu tệp âm thanh vào bảng attachments (status = 'READY')
    BackendAPI-->>Composer: Trả về JSON {attachment_id, audio_url, transcript, language}

    Note over Composer, ChatView: 3. Hiển thị kép trên Giao diện Chat (FR-081, BR-050)
    Composer->>ChatView: Thêm User Message Bubble hiển thị đồng bộ:<br/>1. Audio Player (Play/Pause, scrub thanh tua, thời lượng)<br/>2. Đoạn văn bản vừa nói (Transcript)
    ChatView-->>Learner: Người dùng nghe lại giọng nói và kiểm tra văn bản vừa nói

    Note over ChatView, LLM: 4. Chuyển vào Luồng Xử lý AI & Trả lời Sensei (FR-082, OP-009)
    Composer->>BackendAPI: POST /api/v1/conversations/{id}/messages/stream<br/>(content = transcript, attachments = [attachment_id])
    BackendAPI->>Database: Lưu tin nhắn User vào bảng messages (content, audio_attachment_id)
    BackendAPI->>LLM: Gửi prompt văn bản + ngữ cảnh hội thoại vào LangGraph Engine
    LLM-->>BackendAPI: Stream từng token phản hồi (SSE chunk events)
    BackendAPI-->>ChatView: event: chunk (Token, status: streaming)
    ChatView-->>Learner: Hiển thị văn bản Sensei trả lời liên dòng (Interlinear / Furigana)
    BackendAPI->>Database: Cập nhật tin nhắn Assistant hoàn chỉnh (status = 'COMPLETED')
    BackendAPI-->>ChatView: event: done (tokens, latency_ms)
```

## Nguồn Tham Chiếu
- Yêu cầu chức năng: `FR-079`, `FR-080`, `FR-081`, `FR-082`
- Quy tắc nghiệp vụ: `BR-047`, `BR-048`, `BR-049`, `BR-050`
- Kiểm soát an ninh: `SEC-021`, `SEC-022`
- Hợp đồng API: `OP-066`, `OP-067`

