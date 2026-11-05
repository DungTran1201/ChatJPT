# Kiến Trúc Thành Phần: Hệ Thống Thu Âm Giọng Nói & Xử Lý STT
## Kiến Trúc: `COMP-007` | Tham Chiếu: `FR-079`, `FR-080`, `FR-081`, `FR-082`

Biểu đồ mô tả cấu trúc chi tiết các thành phần phân rã ở phía Frontend (Next.js 16) và Backend (FastAPI Core) cùng dòng kết nối giữa các module.

```mermaid
flowchart TD
    subgraph Frontend_App ["TẦNG TRÌNH DUYỆT WEB (ai-frontend)"]
        subgraph Composer_Module ["MessageComposer Module"]
            MicButton["VoiceRecordButton<br/>(Kích hoạt thu âm & chọn ngôn ngữ)"]
            Waveform["WaveformVisualizer<br/>(Hiển thị sóng âm thời gian thực qua Web Audio API)"]
            AudioRecorder["AudioRecorder Hook / Service<br/>(Quản lý MediaRecorder, nén Opus/WebM, đếm giờ)"]
            LiveSpeechPreview["WebSpeechFallback<br/>(Hỗ trợ bản nháp trực tiếp khi đang nói)"]
        end

        subgraph Chat_Workspace ["ChatWorkspace Module"]
            UserAudioBubble["UserAudioMessageBubble<br/>[FR-081, BR-050]"]
            AudioPlayer["AudioPlayerBar<br/>(Play/Pause, scrub thanh tua, thời lượng)"]
            TranscriptDisplay["TranscriptSubtitleView<br/>(Hiển thị văn bản chuyển đổi)"]
            SenseiBubble["SenseiResponseBubble<br/>(Hiển thị Interlinear Markdown & Furigana)"]
        end
    end

    subgraph Backend_App ["TẦNG MÁY CHỦ DỊCH VỤ (ai-backend)"]
        subgraph API_Routers ["FastAPI API Routers"]
            STTRouter["STTRouter<br/>POST /api/v1/chat/stt<br/>[OP-066]"]
            ChatStreamRouter["ChatRouter<br/>POST /api/v1/conversations/{id}/messages/stream<br/>[OP-009, OP-067]"]
        end

        subgraph Core_Services ["Core Services Layer"]
            STTService["STT Transcription Service (COMP-007)<br/>- Audio Normalization (16kHz Mono)<br/>- Language Detection (vi / en / ja)<br/>- Fallback Engine Coordinator"]
            AttachmentStorage["AttachmentStorageService<br/>(Lưu file WebM/WAV an toàn vào đĩa)"]
            MimeValidator["Mime & MagicByte Validator<br/>(Chặn mã độc giả mạo đuôi audio - SEC-021)"]
        end

        subgraph AI_Engine ["LangGraph Orchestration"]
            PromptAssembler["Pedagogical Prompt Assembler<br/>(Kết hợp transcript + Rule sư phạm + Persona)"]
            LLMClient["LangGraph StateGraph Engine<br/>(Gemini 3.8 Flash / OpenAI GPT-4o-mini)"]
        end
    end

    subgraph Storage_Layer ["TẦNG CƠ SỞ DỮ LIỆU & FILE SYSTEM"]
        DB_Attachments[("Bảng attachments<br/>(Lưu metadata tệp âm thanh)")]
        DB_Messages[("Bảng messages<br/>(Lưu content, audio_attachment_id)")]
        LocalAudioDisk[("Local Storage:<br/>ai-backend/data/storage/attachments/")]
    end

    subgraph External_STT_Cloud ["DỊCH VỤ CHUYỂN ĐỔI GIỌNG NÓI NGOÀI"]
        WhisperCloud["OpenAI / Groq Whisper API<br/>(Nhận diện đa ngữ chuẩn xác cao)"]
        GeminiAudio["Google Gemini Multimodal Audio<br/>(Phân tích âm thanh ngữ cảnh trực tiếp)"]
    end

    %% Luồng kết nối Frontend
    MicButton --> AudioRecorder
    AudioRecorder --> Waveform
    AudioRecorder -.-> LiveSpeechPreview
    AudioRecorder -->|Audio Blob| STTRouter

    %% Luồng kết nối Backend
    STTRouter --> MimeValidator
    MimeValidator --> AttachmentStorage
    AttachmentStorage --> LocalAudioDisk
    AttachmentStorage --> DB_Attachments
    STTRouter --> STTService
    STTService --> WhisperCloud
    STTService -.-> GeminiAudio
    
    %% Phản hồi về Frontend
    STTRouter -- Trả về Transcript + audio_url --> Composer_Module
    Composer_Module --> UserAudioBubble
    UserAudioBubble --> AudioPlayer
    UserAudioBubble --> TranscriptDisplay
    AudioPlayer -->|Tải file âm thanh| LocalAudioDisk

    %% Gửi vào Chat Stream
    Composer_Module -->|Transcript + Attachment ID| ChatStreamRouter
    ChatStreamRouter --> DB_Messages
    ChatStreamRouter --> PromptAssembler
    PromptAssembler --> LLMClient
    LLMClient -- SSE Tokens --> SenseiBubble

    style Frontend_App fill:#f0f9ff,stroke:#0284c7,stroke-width:2px
    style Backend_App fill:#fdf4ff,stroke:#a855f7,stroke-width:2px
    style Storage_Layer fill:#f0fdf4,stroke:#16a34a,stroke-width:2px
    style External_STT_Cloud fill:#fefce8,stroke:#ca8a04,stroke-width:2px
```

## Nguồn Tham Chiếu
- Thành phần: `COMP-001` (Frontend), `COMP-002` (Backend), `COMP-003` (LLM), `COMP-007` (STT Transcription Service).
- Hợp đồng API: `OP-066` (`/chat/stt`), `OP-067` (`/messages/audio-stream`).

