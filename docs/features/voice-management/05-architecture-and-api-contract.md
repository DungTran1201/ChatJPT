# Architecture & API Contract: Voice Management

## 1. Architectural Component (ADR-015, COMP-005)
Hệ thống VoiceVox TTS Service được thiết kế theo mô hình Micro-Bridge & In-Process Embedded Engine tích hợp:
- **Client (Frontend)**: Tương tác qua React hooks, quản lý trình phát âm thanh và kiểm soát cache blob.
- **Backend Service (`VoicevoxService`)**:
  - **Embedded VoiceVox Core Engine (Primary)**: Tích hợp trực tiếp thư viện `voicevox_core` (v0.17.1) chạy in-process trong tiến trình Python kết hợp với DirectML/CPU ONNX Runtime DLL, từ điển OpenJTalk và 16 tệp mô hình nơ-ron VVM (`0.vvm` .. `15.vvm`). Không yêu cầu bật daemon ngoại vi cổng 50021, đảm bảo giọng nói nhân vật chuẩn xác 100% từ GitHub official.
  - **External VoiceVox HTTP Daemon (Secondary)**: Tự động kiểm tra và kết nối daemon VoiceVox trên cổng `50021` nếu có.
  - **Acoustic Fallback Synthesis (`BR-042`)**: Bộ sinh âm học multi-tone chuẩn PCM WAV bằng thư viện chuẩn Python khi cả hai động cơ trên không sẵn sàng.
  - **LRU In-Memory Cache**: Quản lý bộ nhớ đệm nhị phân WAV trong RAM với thuật toán LRU Cache để giảm tải tính toán CPU/GPU.
  - **Acoustic Modulation Guard (`SEC-015`, `BR-040`)**: Chuẩn hóa và giới hạn các dải tham số `speed_scale`, `pitch_scale`, `intonation_scale`, `volume_scale`.

---

## 2. API Specifications

### `GET /api/v1/voices` (OP-047)
- **Mục đích**: Lấy danh sách giọng đọc của các nhân vật kèm bộ lọc.
- **Query Parameters**:
  - `gender` (optional): `female` | `male` | `other`
  - `status` (optional): `ACTIVE` | `INACTIVE`
  - `search` (optional): Chuỗi tìm kiếm theo tên hoặc tên nhân vật.
- **Phản hồi (200 OK)**:
```json
{
  "total": 14,
  "items": [
    {
      "id": "voice_kasukabe_tsumugi",
      "name": "Kasukabe Tsumugi (Normal)",
      "character_name": "春日部つむぎ",
      "speaker_id": 8,
      "style_name": "Normal",
      "gender": "female",
      "description": "Giọng nữ tươi vui, trong sáng, phù hợp giao tiếp đời thường N5-N4.",
      "speed_scale": 1.0,
      "pitch_scale": 0.0,
      "intonation_scale": 1.0,
      "volume_scale": 1.0,
      "sample_text": "こんにちは！一緒に日本語を勉強しましょう！",
      "avatar_url": "/avatars/voices/tsumugi.png",
      "status": "ACTIVE",
      "is_system_preset": true
    }
  ]
}
```

### `GET /api/v1/voices/status` (OP-049)
- **Mục đích**: Kiểm tra tình trạng kết nối tới VoiceVox engine cục bộ (nhúng sẵn hoặc daemon).
- **Phản hồi (200 OK)**:
```json
{
  "engine_available": true,
  "engine_mode": "embedded_core",
  "engine_url": "embedded://voicevox_core",
  "version": "0.17.1 (voicevox_core)",
  "latency_ms": 0.5,
  "cached_audio_count": 14,
  "loaded_models_count": 16,
  "supported_speakers_count": 30,
  "error": null
}
```

### `POST /api/v1/voices/synthesize` (OP-053)
- **Mục đích**: Tổng hợp giọng nói trực tiếp từ văn bản tiếng Nhật và mã `speaker_id`.
- **Request Body**:
```json
{
  "text": "こんにちは、元気ですか？",
  "speaker_id": 8,
  "speed_scale": 1.0,
  "pitch_scale": 0.0,
  "intonation_scale": 1.0,
  "volume_scale": 1.0
}
```
- **Phản hồi (200 OK)**: Dòng luồng nhị phân âm thanh `audio/wav`.

### `POST /api/v1/voices/{id}/synthesize` (OP-054)
- **Mục đích**: Tổng hợp giọng nói sử dụng cấu hình âm học đã lưu của hồ sơ voice.
- **Phản hồi (200 OK)**: Dòng luồng nhị phân âm thanh `audio/wav`.
