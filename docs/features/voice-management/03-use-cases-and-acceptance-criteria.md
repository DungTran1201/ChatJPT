# Use Cases & Acceptance Criteria: Voice Management

## 1. Use Case UC-042: Manage VoiceVox Character Catalog & Acoustic Tuning
- **Primary Actor**: Registered User / System Admin
- **Preconditions**: Người dùng đăng nhập vào hệ thống, truy cập trang `/voices`.
- **Main Flow**:
  1. Người dùng duyệt danh sách nhân vật giọng đọc VoiceVox được hiển thị dưới dạng card trực quan.
  2. Người dùng sử dụng ô tìm kiếm hoặc bộ lọc theo giới tính/phong cách để tìm nhân vật mong muốn.
  3. Người dùng nhấn nút "Tùy Chỉnh Âm Học" (Tune Voice) trên thẻ nhân vật.
  4. Hệ thống mở modal tùy chỉnh với các thanh trượt: Tốc độ (Speed), Cao độ (Pitch), Ngữ điệu (Intonation), Âm lượng (Volume).
  5. Người dùng kéo thanh trượt điều chỉnh và bấm "Nghe Thử Mẫu" để kiểm tra âm thanh tức thì.
  6. Người dùng bấm "Lưu Thiết Lập", hệ thống gọi API `PUT /api/v1/voices/{id}` và cập nhật thông số vào database.

### Acceptance Criteria (Gherkin):
```gherkin
Scenario: Cập nhật thành công tham số âm học của giọng đọc
  Given Người dùng mở modal tùy chỉnh cho giọng "Kasukabe Tsumugi (Normal)"
  When Người dùng thiết lập speed_scale = 1.15 và pitch_scale = 0.05
  And Người dùng nhấn nút "Lưu Thiết Lập"
  Then Hệ thống gửi yêu cầu PUT /api/v1/voices/{id} với các tham số mới
  And Phản hồi trả về mã trạng thái 200 OK
  And Danh mục hiển thị thông số đã được cập nhật thành công

Scenario: Từ chối lưu tham số âm học vượt ngưỡng cho phép (BR-040)
  Given Người dùng cố tình nhập speed_scale = 3.5 (vượt ngưỡng 2.0)
  When Người dùng nhấn "Lưu Thiết Lập"
  Then Hệ thống chặn yêu cầu tại client và hiển thị thông báo lỗi kiểm định giá trị hợp lệ
```

---

## 2. Use Case UC-043: Voice Preview & Audio Synthesis Pipeline
- **Primary Actor**: Registered User / Guest
- **Preconditions**: Người dùng đang ở trang `/voices`, form Sensei hoặc khung chat.
- **Main Flow**:
  1. Người dùng nhấn nút phát âm thanh mẫu trên thẻ giọng đọc hoặc nút loa trong chat.
  2. Frontend gửi văn bản tiếng Nhật và ID giọng đọc tới endpoint tổng hợp âm thanh.
  3. Backend kiểm tra cache: nếu đã có bản ghi âm thanh khớp, trả về trực tiếp từ bộ nhớ đệm.
  4. Nếu chưa có trong cache, backend gọi VoiceVox engine qua cổng 50021 để sinh audio query và synthesis.
  5. Backend lưu audio vào cache và truyền luồng WAV nhị phân về trình duyệt.
  6. Frontend nhận âm thanh và tự động phát qua HTML5 Audio element.

### Acceptance Criteria (Gherkin):
```gherkin
Scenario: Nghe thử giọng đọc thành công với VoiceVox Engine
  Given VoiceVox Engine đang chạy tại cổng 50021
  When Người dùng nhấn nút "Nghe Thử" trên giọng "Zundamon (Normal)"
  Then Hệ thống gửi yêu cầu POST /api/v1/voices/{id}/synthesize
  And Nhận về luồng âm thanh audio/wav với mã HTTP 200
  And Trình duyệt phát âm thanh câu chào bằng giọng Zundamon

Scenario: Xử lý linh hoạt khi VoiceVox Engine ngoại tuyến (BR-042)
  Given VoiceVox Engine chưa khởi chạy trên cổng 50021
  When Người dùng nhấn nút "Nghe Thử"
  Then Backend phát hiện timeout hoặc connection refused
  And Kích hoạt cơ chế Fallback tổng hợp âm thanh mẫu an toàn
  And Giao diện hiển thị cảnh báo Engine Offline kèm hướng dẫn khởi chạy VoiceVox
```

---

## 3. Use Case UC-044: Assign Character Voice to Sensei Persona & Playback in Chat
- **Primary Actor**: Registered User
- **Preconditions**: Người dùng quản lý danh sách Sensei Guidance tại `/prompts`.
- **Main Flow**:
  1. Người dùng mở modal chỉnh sửa thông tin Sensei (ví dụ: Sakura Sensei N5).
  2. Trong trường "Giọng Nói Nhân Vật" (Character Voice), người dùng mở danh sách chọn và lựa chọn một nhân vật (ví dụ: Kasukabe Tsumugi).
  3. Người dùng bấm nghe thử giọng ngay bên cạnh dropdown để xác nhận độ phù hợp với phong cách sư phạm của Sensei.
  4. Người dùng bấm "Lưu Sensei", hệ thống cập nhật trường `voice_id` trong cơ sở dữ liệu (`BR-041`).
  5. Trong màn hình Kaiwa Chat, khi trò chuyện với Sakura Sensei, bấm nút loa phát âm sẽ kích hoạt giọng đọc Kasukabe Tsumugi tương ứng.
