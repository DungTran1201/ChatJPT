# Software Requirements Specification (SRS): Voice Management (VoiceVox)

## 1. Functional Requirements

### FR-069: VoiceVox Character Voice Catalog & Filtering
- Hệ thống phải hiển thị danh mục trực quan tất cả các nhân vật VoiceVox có sẵn.
- Cho phép tìm kiếm theo tên nhân vật (Character Name: e.g. つむぎ, めたん, ずんだもん) hoặc tên hiển thị (Display Name).
- Cung cấp bộ lọc theo giới tính (`female`, `male`, `other`), phong cách phát âm (`Normal`, `Sweet`, `Whisper`, `Joy`, `Angry`, `Cool`) và trạng thái (`ACTIVE`, `INACTIVE`).
- Hiển thị đầy đủ thông tin: Ảnh đại diện nhân vật (Avatar), Speaker ID VoiceVox, mô tả tính cách giọng đọc và các tham số âm học hiện hành.

### FR-070: Voice Customization & Acoustic Parameter Tuning
- Cho phép người dùng tùy chỉnh các tham số âm học của giọng đọc nhân vật:
  - **Tốc độ đọc (Speed Scale)**: dải giá trị từ `0.5` đến `2.0` (mặc định: `1.0`).
  - **Cao độ âm thanh (Pitch Scale)**: dải giá trị từ `-0.15` đến `0.15` (mặc định: `0.0`).
  - **Ngữ điệu / Nhấn nhá (Intonation Scale)**: dải giá trị từ `0.0` đến `2.0` (mặc định: `1.0`).
  - **Âm lượng (Volume Scale)**: dải giá trị từ `0.0` đến `2.0` (mặc định: `1.0`).
- Cho phép cập nhật câu thoại mẫu phát âm thử nghiệm (`sample_text`).
- Cho phép thêm mới hồ sơ giọng tùy chỉnh hoặc điều chỉnh các hồ sơ giọng hiện hữu (đáp ứng `BR-040`).

### FR-071: Voice Audio Preview & TTS Synthesis Pipeline
- Cung cấp nút nghe thử (Test Audio Playback) ngay trên danh thiếp giọng đọc và trong modal tùy chỉnh.
- Khi người dùng bấm nghe thử, client gửi yêu cầu đến `POST /api/v1/voices/{id}/synthesize` hoặc `POST /api/v1/voices/synthesize`.
- Backend kiểm tra kết nối VoiceVox local engine (`http://127.0.0.1:50021`). Nếu engine khả dụng:
  - Gọi `/audio_query` với văn bản tiếng Nhật và speaker ID.
  - Cập nhật các trường `speedScale`, `pitchScale`, `intonationScale`, `volumeScale` trong truy vấn.
  - Gọi `/synthesis` nhận luồng byte WAV nhị phân và phản hồi `audio/wav`.
- Nếu engine ngoại tuyến (Offline), backend kích hoạt cơ chế `BR-042` trả về âm thanh tổng hợp fallback hoặc tín hiệu để frontend kích hoạt Web Speech API.

### FR-072: Sensei Persona Voice Binding & Selection
- Trong giao diện quản lý Sensei Guidance (`/prompts`), mỗi Sensei phải có một trường cấu hình `voice_id` liên kết với danh mục `voices`.
- Giao diện form tạo/chỉnh sửa Sensei cung cấp bộ chọn giọng (Voice Selector Dropdown) hiển thị rõ: Ảnh đại diện nhân vật, Tên nhân vật, Phong cách và nút nghe thử nhanh âm thanh của giọng đó.
- Khi lưu Sensei, giá trị `voice_id` được kiểm tra tính hợp lệ và toàn vẹn tham chiếu (`BR-041`).

### FR-073: Interactive Japanese Kaiwa Voice Playback via Assigned Sensei Voice
- Trong cửa sổ hội thoại luyện tập tiếng Nhật (Kaiwa Chat), mỗi lượt trả lời của Sensei có nút loa phát âm 🔊.
- Khi người dùng nhấn nút loa, hệ thống sẽ tự động sử dụng chính xác `voice_id` đã được gán cho Sensei hiện tại để phát âm thanh câu trả lời bằng tiếng Nhật.
- Trải nghiệm phát âm mượt mà, hỗ trợ thanh trạng thái phát (Playing / Idle) và tự động dừng âm thanh trước đó khi phát câu mới.

---

## 2. Non-Functional Requirements & Guardrails
- **NFR-VOICE-01 (Latency)**: Phản hồi âm thanh tổng hợp từ LRU cache phải dưới 20ms; tổng hợp thời gian thực từ local VoiceVox engine không quá 800ms cho câu dưới 100 ký tự.
- **NFR-VOICE-02 (Offline Resilience)**: Khi VoiceVox engine không chạy trên máy chủ cục bộ, toàn bộ ứng dụng web và các tính năng khác (Chat, Sensei Guidance, Grammar) vẫn hoạt động 100% bình thường không gặp lỗi 500.
- **NFR-VOICE-03 (Format Compatibility)**: Định dạng âm thanh chuẩn hóa `audio/wav`, phát trực tiếp trên mọi trình duyệt web (Chrome, Edge, Firefox, Safari).
