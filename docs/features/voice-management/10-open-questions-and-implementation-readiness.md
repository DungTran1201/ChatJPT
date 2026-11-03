# Open Questions & Implementation Readiness: Voice Management

## 1. Open Questions Register
- Hiện không có câu hỏi mở nào tồn đọng. Toàn bộ kiến trúc và mô hình dữ liệu đã được xác nhận với đầy đủ cơ chế hoạt động offline.

## 2. Implementation Readiness Checklist
- [x] Canonical Requirements & State Machine cập nhật đầy đủ (`FR-069`..`FR-073`, `BR-040`..`BR-042`, `SEC-015`, `STATE-VOICE-01`).
- [x] Cơ sở dữ liệu: Bảng `voices` và cột `voice_id` trong `system_prompts` đã sẵn sàng.
- [x] Backend service: `VoicevoxService` hỗ trợ kết nối engine, LRU caching và Fallback WAV.
- [x] Frontend UI: Trang `/voices`, Modal tùy chỉnh âm học, cập nhật bộ chọn giọng Sensei và nút loa phát âm Chat.
- [x] Bộ kiểm thử tự động `test_voices.py` sẵn sàng chạy xác minh toàn diện.
