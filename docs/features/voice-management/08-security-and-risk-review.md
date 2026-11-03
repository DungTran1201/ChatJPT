# Security & Risk Review: Voice Management (SEC-015)

## 1. Security Threat Analysis & Mitigations
- **Mối Đe Dọa 1: Lạm Dụng Tài Nguyên Tổng Hợp Âm Thanh (Resource Exhaustion / DoS)**:
  - *Nguy cơ*: Giọng đọc tổng hợp bằng mạng nơ-ron tiêu tốn năng lực tính toán CPU/GPU. Nếu kẻ tấn công gửi hàng nghìn yêu cầu văn bản dài liên tục, hệ thống có thể bị treo.
  - *Kiểm soát (`SEC-015`)*:
    1. Giới hạn độ dài văn bản tối đa gửi vào API tổng hợp âm thanh không quá 500 ký tự.
    2. Áp dụng giới hạn tần suất yêu cầu (Rate Limiting) trên các endpoint tổng hợp âm thanh.
    3. Tận dụng tối đa bộ nhớ đệm LRU Cache: các câu thoại trùng lặp sẽ được phục vụ trực tiếp từ RAM mà không cần gọi lại VoiceVox Engine.
- **Mối Đe Dọa 2: Tham Số Âm Học Bất Thường (Parameter Injection / Buffer Distortion)**:
  - *Nguy cơ*: Truyền các giá trị cực đoan (âm thanh âm cực đại, tốc độ vô hạn) có thể làm vỡ âm lượng hoặc gây lỗi tràn bộ đệm VoiceVox.
  - *Kiểm soát (`BR-040`)*: Pydantic Validator ở Backend cưỡng chế nghiêm ngặt các dải giá trị:
    - `0.5 <= speed_scale <= 2.0`
    - `-0.15 <= pitch_scale <= 0.15`
    - `0.0 <= intonation_scale <= 2.0`
    - `0.0 <= volume_scale <= 2.0`
- **Mối Đe Dọa 3: Xóa Nhầm Giọng Chuẩn Hệ Thống (Preset Tampering)**:
  - *Nguy cơ*: Người dùng vô tình hoặc cố ý xóa các giọng nhân vật chuẩn đi kèm hệ thống (`is_system_preset = 1`).
  - *Kiểm soát*: Chặn thao tác `DELETE` đối với các bản ghi có cờ `is_system_preset = true`.
