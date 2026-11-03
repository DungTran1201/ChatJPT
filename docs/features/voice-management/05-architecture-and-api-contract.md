# Architecture & API Contract: Voice Management

## 1. Architectural Component (ADR-015, COMP-005)
Hệ thống VoiceVox TTS Service được thiết kế theo mô hình Micro-Bridge tích hợp:
- **Client (Frontend)**: Tương tác qua React hooks, quản lý trình phát âm thanh và kiểm soát cache blob.
- **Backend Service (`VoicevoxService`)**:
  - Giao tiếp HTTP với VoiceVox Engine daemon trên cổng `50021`.
  - Quản lý bộ nhớ đệm nhị phân WAV trong RAM với thuật toán LRU Cache để giảm tải tính toán cho GPU/CPU.
  - Xử lý bộ lọc tham số âm học an toàn (`SEC-015`).
  - Cung cấp cơ chế Fallback âm học khi engine ngoại tuyến (`BR-042`).

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
- **Mục đích**: Kiểm tra tình trạng kết nối tới VoiceVox engine cục bộ.
- **Phản hồi (200 OK)**:
```json
{
  "engine_available": true,
  "engine_url": "http://127.0.0.1:50021",
  "version": "0.14.4",
  "latency_ms": 12.5,
  "cached_audio_count": 42
}
```

### `POST /api/v1/voices/{id}/synthesize` (OP-054)
- **Mục đích**: Tổng hợp văn bản tiếng Nhật thành file âm thanh WAV theo giọng đọc của nhân vật cụ thể.
- **Request Body**:
```json
{
  "text": "はじめまして、よろしくおねがいします！",
  "speed_scale": 1.05,
  "pitch_scale": 0.0,
  "intonation_scale": 1.1
}
```
- **Phản hồi**: Trực tiếp luồng nhị phân `Content-Type: audio/wav`.
