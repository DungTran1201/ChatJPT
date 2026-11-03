# Scope, Assumptions, Decisions & Fact Register: Voice Management (VoiceVox)

## 1. Executive Summary & Problem Statement
Trong ứng dụng học tiếng Nhật **AI-Chan Kaiwa**, trải nghiệm luyện hội thoại tự nhiên yêu cầu phát âm chuẩn bản xứ của các nhân vật (Sensei personas) với ngữ điệu sinh động và phong cách riêng biệt. Hệ thống cần tích hợp công nghệ **VoiceVox** - công cụ mã nguồn mở hàng đầu trong lĩnh vực chuyển đổi văn bản sang âm thanh tiếng Nhật (Japanese Neural Text-To-Speech) với khả năng tùy biến đa nhân vật (Kasukabe Tsumugi, Shikoku Metan, Zundamon, Kuronotake, Aoyama Ryusei, Hau, v.v.).

Chức năng **Quản Lý Voice (Voice Management)** cung cấp:
1. Danh mục quản lý tập trung các Voice của nhân vật với các thông số âm học (Speed, Pitch, Intonation, Volume).
2. Trình nghe thử mẫu giọng (Live Audio Preview) tức thì qua API tổng hợp âm thanh VoiceVox.
3. Cho phép mỗi Sensei trong danh sách Sensei Guidance (`system_prompts`) tùy ý lựa chọn và gán một giọng nhân vật từ danh mục voice.
4. Trình phát âm thanh hội thoại tự nhiên trong giao diện chat khi người học nhấn nút loa phát âm.

---

## 2. Fact Register (Sự Thật Đã Xác Thực)
- **FACT-VOICE-01**: Bảng `voices` đã được khởi tạo trong cơ sở dữ liệu `app.db` với 14 nhân vật VoiceVox chuẩn (Kasukabe Tsumugi, Shikoku Metan, Zundamon, Kuronotake, Aoyama Ryusei, Hau, Goki, Kyushu Sora, v.v.) kèm speaker ID và thông số âm học chuẩn.
- **FACT-VOICE-02**: Bảng `system_prompts` đã có cột ngoại khóa `voice_id` tham chiếu đến `voices(id)` và 5 Sensei chuẩn N5-N1 đã được gán mặc định các giọng phù hợp.
- **FACT-VOICE-03**: Engine VoiceVox chuẩn giao tiếp qua HTTP REST API (mặc định cổng `50021`), với 2 bước tổng hợp cốt lõi: `POST /audio_query?text=...&speaker=...` và `POST /synthesis?speaker=...`.
- **FACT-VOICE-04**: Trong môi trường cục bộ chưa cài đặt hoặc chưa khởi chạy VoiceVox daemon, cổng 50021 sẽ không phản hồi. Hệ thống phải đảm bảo cơ chế suy giảm chất lượng linh hoạt (Graceful Degradation) tạo âm thanh mẫu hoặc điều hướng sang Web Speech API trên trình duyệt.

---

## 3. Assumptions Register (Giả Định Kỹ Thuật)
- **ASSUMPTION-VOICE-01**: Tốc độ tổng hợp âm thanh cục bộ VoiceVox dao động từ 150ms đến 600ms tùy độ dài câu. Bộ nhớ đệm âm thanh (LRU Cache) với khóa MD5 `(text, speaker_id, speed, pitch, intonation)` sẽ giảm độ trễ về dưới 5ms cho các câu lặp lại.
- **ASSUMPTION-VOICE-02**: Định dạng âm thanh trả về từ VoiceVox là PCM WAV (16-bit, 24kHz/44.1kHz), tương thích hoàn toàn với thẻ `<audio>` và Web Audio API của trình duyệt hiện đại.

---

## 4. Decisions Register (Quyết Định Kiến Trúc)
- **DECISION-VOICE-01**: Kiến trúc 2 tầng (Two-Tier TTS Pipeline):
  - Tầng 1: Backend VoiceVox Proxy Service (`VoicevoxService`) kiểm tra engine status, thực thi audio query + synthesis, lưu LRU cache trong bộ nhớ.
  - Tầng 2: Client Web Audio Fallback: nếu Backend thông báo engine Offline hoặc gặp lỗi socket, giao diện Chat tự động chuyển tiếp sang Web Speech API trình duyệt để người dùng không bị gián đoạn trải nghiệm học tập.
- **DECISION-VOICE-02**: Quản lý độc lập Voice Catalog tại trang `/voices`, đồng thời nhúng bộ chọn giọng `VoiceSelector` vào form cấu hình Sensei (`/prompts`) và bảng điều khiển Kaiwa Chat.

---

## 5. Requirements Traceability Baseline
- `FR-069`: VoiceVox Character Voice Catalog & Filtering
- `FR-070`: Voice Customization & Acoustic Parameter Tuning
- `FR-071`: Voice Audio Preview & TTS Synthesis Pipeline
- `FR-072`: Sensei Persona Voice Binding & Selection
- `FR-073`: Interactive Japanese Kaiwa Voice Playback via Assigned Sensei Voice
- `BR-040`: Voice Parameter Bounds Sanity (Speed: 0.5-2.0, Pitch: -0.15-0.15, Intonation: 0.0-2.0, Volume: 0.0-2.0)
- `BR-041`: Sensei Voice Assignment Invariant
- `BR-042`: Graceful Voice Engine Degradation & Acoustic Fallback
- `SEC-015`: Audio Ingress & Voice Parameter Injection Sanitization
