# Mermaid Diagrams: Voice Management Architecture & Flows

## 1. State Diagram: Vòng Đời Giọng Nói & Trạng Thái Engine (`STATE-VOICE-01`)

```mermaid
stateDiagram-v2
    [*] --> ACTIVE: Khởi tạo hồ sơ giọng VoiceVox
    
    ACTIVE --> TUNING: Người dùng mở Voice Tuning Modal
    TUNING --> ACTIVE: Lưu tham số thành công (BR-040)
    TUNING --> ACTIVE: Người dùng hủy bỏ chỉnh sửa
    
    ACTIVE --> INACTIVE: Tắt trạng thái kích hoạt
    INACTIVE --> ACTIVE: Bật trạng thái kích hoạt
    
    ACTIVE --> DEGRADED: VoiceVox Engine cổng 50021 ngoại tuyến
    DEGRADED --> ACTIVE: Engine phục hồi kết nối thành công
    
    INACTIVE --> ARCHIVED: Xóa hồ sơ tùy chỉnh (Không phải System Preset)
    ARCHIVED --> [*]
```

---

## 2. Sequence Diagram: Luồng Tổng Hợp & Phát Âm Thanh (`SEQ-VOICE-01`)

```mermaid
sequenceDiagram
    autonumber
    actor User as Người Học
    participant UI as Kaiwa Chat / Voices Page
    participant API as Backend Voices API
    participant Cache as LRU Binary Audio Cache
    participant Engine as VoiceVox Engine (Port 50021)
    
    User->>UI: Nhấn nút Loa 🔊 phát âm câu trả lời
    UI->>API: POST /api/v1/voices/{id}/synthesize {text, speed, pitch}
    API->>Cache: Kiểm tra cache MD5(text, speaker_id, speed, pitch)
    
    alt Đã tồn tại trong Cache
        Cache-->>API: Trả về Binary WAV Buffer (<5ms)
        API-->>UI: 200 OK (Content-Type: audio/wav)
        UI->>User: Phát âm thanh tức thì qua HTML5 Audio
    else Chưa có trong Cache
        API->>Engine: GET /version (Health Check)
        alt Engine Đang Hoạt Động (Online)
            API->>Engine: POST /audio_query?text={text}&speaker={id}
            Engine-->>API: Audio Query JSON
            API->>API: Áp dụng tham số (speedScale, pitchScale, intonationScale)
            API->>Engine: POST /synthesis?speaker={id} (Query JSON Body)
            Engine-->>API: Audio/WAV Binary Data
            API->>Cache: Lưu kết quả vào LRU Cache
            API-->>UI: 200 OK (Content-Type: audio/wav)
            UI->>User: Phát âm thanh giọng nhân vật VoiceVox
        else Engine Ngoại Tuyến (Offline / BR-042)
            API->>API: Sinh Fallback WAV hoặc trả cờ Fallback
            API-->>UI: 200 OK (Fallback WAV / Web Speech Trigger)
            UI->>User: Phát âm giọng đọc dự phòng không gây gián đoạn
        end
    end
```

---

## 3. Component Diagram: Cấu Trúc Thành Phần Hệ Thống (`COMP-005`)

```mermaid
graph TD
    subgraph Frontend["Frontend Layer (ai-frontend)"]
        VP["Voices Page (/voices)"]
        SP["Sensei Guidance (/prompts)"]
        CW["Kaiwa Chat Workspace"]
        VS["voiceService.ts"]
        AP["Web Audio / HTML5 Audio Player"]
    end

    subgraph Backend["Backend Layer (ai-backend)"]
        VR["voices_router (/api/v1/voices)"]
        SPR["system_prompts_router (/api/v1/system-prompts)"]
        VVS["VoicevoxService"]
        AC["LRU Audio Cache (RAM)"]
        FW["Fallback WAV Generator"]
    end

    subgraph Storage["Database & Engine"]
        DB[("SQLite app.db (voices, system_prompts)")]
        VVE["VoiceVox Local Engine Daemon (:50021)"]
    end

    VP --> VS
    SP --> VS
    CW --> VS
    VS --> VR
    SP --> SPR

    VR --> VVS
    SPR --> DB
    VR --> DB
    VVS --> AC
    VVS --> VVE
    VVS --> FW
```


---

## 4. Sequence Diagram: Luồng Phân Giải & Phát Giọng Sensei Trong Hội Thoại (SEQ-VOICE-02)

`mermaid
sequenceDiagram
    autonumber
    actor Learner as Người Học (Learner)
    participant UI as ChatWorkspace (/chat)
    participant ChatAPI as Chat Stream API (/chat.py)
    participant DB as SQLite app.db (messages, system_prompts)
    participant VoiceAPI as Voices API (/voices.py)
    participant Engine as VoiceVox Engine Core / Daemon

    Learner->>UI: Chọn Sensei (e.g. Yuki Sensei N1 - voice_shikoku_metan)
    UI->>UI: Lưu activeSenseiVoiceId & localStorage('ai_chan_selected_sensei_voice')
    Learner->>UI: Gửi câu hỏi Kaiwa
    UI->>ChatAPI: POST /conversations/{id}/messages/stream {sensei_id, model, ...}
    ChatAPI->>DB: Truy vấn system_prompts lấy voice_id
    DB-->>ChatAPI: voice_id: 'voice_shikoku_metan'
    ChatAPI->>DB: Lưu Assistant Message với (sensei_id, voice_id)
    ChatAPI-->>UI: SSE event: done {message_id, sensei_id, voice_id}
    UI->>UI: Cập nhật message state kèm sensei_id & voice_id
    
    Learner->>UI: Nhấn biểu tượng Loa 🔊 trên câu trả lời
    UI->>VoiceAPI: POST /api/v1/voices/voice_shikoku_metan/synthesize {text}
    Note over VoiceAPI: Nếu gọi bằng sensei_id, backend tự động tra cứu voice_id từ system_prompts
    VoiceAPI->>Engine: Tổng hợp âm thanh theo speaker_id của Shikoku Metan (ID 0)
    Engine-->>VoiceAPI: Binary WAV Stream
    VoiceAPI-->>UI: 200 OK (Content-Type: audio/wav)
    UI->>Learner: Phát âm giọng đọc đặc trưng của Yuki Sensei
`
