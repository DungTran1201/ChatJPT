# Kế Hoạch Kiểm Thử & Bộ Ca Kiểm Thử (Test Cases)
## Phân Hệ: Voice Input & STT | Tính Năng: `FEAT-006`

## 1. Chiến Lược Kiểm Thử (Testing Strategy)
- **Kiểm thử đơn vị (Unit Tests)**: Kiểm tra module trích xuất Magic Bytes, nén âm thanh WebM và logic xác thực tham số ngôn ngữ.
- **Kiểm thử tích hợp (Integration Tests)**: Kiểm tra tương tác giữa `STTRouter` với `STTService` và cơ sở dữ liệu `attachments`/`messages`.
- **Kiểm thử đầu cuối (End-to-End E2E)**: Kiểm tra từ thao tác bấm mic, nói tiếng Việt, tiếng Anh, tiếng Nhật tới khi nhận diện hiển thị trên chat.

---

## 2. Chi Tiết Các Ca Kiểm Thử (Test Cases)

### `TC-060`: Kiểm thử thu âm & STT Tiếng Việt
- **Mức độ ưu tiên**: P0 | **Loại**: E2E
- **Điều kiện tiên quyết**: Đã đăng nhập tài khoản học viên, microphone hoạt động tốt.
- **Các bước thực hiện**:
  1. Mở cuộc hội thoại và bấm nút Microphone.
  2. Chọn ngôn ngữ: Tiếng Việt (`vi`).
  3. Nói rõ ràng câu: *"Chào Sensei, hôm nay chúng ta học ngữ pháp bài 15 nhé."*
  4. Bấm nút Gửi tin nhắn.
- **Kết quả mong đợi**: Tin nhắn người dùng xuất hiện với Audio Player phát lại đúng câu nói và dòng chữ tiếng Việt chính xác 100%.

### `TC-061`: Kiểm thử thu âm & STT Tiếng Nhật (Kaiwa)
- **Mức độ ưu tiên**: P0 | **Loại**: E2E
- **Điều kiện tiên quyết**: Tài khoản học viên đang ở chế độ hội thoại Kaiwa.
- **Các bước thực hiện**:
  1. Bấm nút Microphone và chọn tiếng Nhật (`ja`).
  2. Nói câu giao tiếp: *"明日の会議は何時から始まりますか"* (Cuộc họp ngày mai bắt đầu lúc mấy giờ?).
  3. Bấm Gửi.
- **Kết quả mong đợi**: Chữ Hán (Kanji) `明日` (ashita), `会議` (kaigi), `何時` (nanji), `始まりますか` được nhận dạng chính xác; Sensei trả lời tự nhiên.

### `TC-062`: Kiểm thử thu âm & STT Tiếng Anh
- **Mức độ ưu tiên**: P0 | **Loại**: E2E
- **Các bước thực hiện**:
  1. Bấm nút Microphone và chọn tiếng Anh (`en`).
  2. Nói câu: *"Could you explain the nuance between wa and ga particles?"*
  3. Bấm Gửi.
- **Kết quả mong đợi**: Văn bản tiếng Anh nhận diện chuẩn xác từng từ, AI Sensei giải thích rõ ràng sự khác biệt giữa trợ từ `wa` và `ga`.

### `TC-063`: Hiển thị đồng bộ Audio Player & Phụ đề trên Chat
- **Mức độ ưu tiên**: P0 | **Loại**: UI/UX
- **Các bước thực hiện**:
  1. Sau khi gửi tin nhắn thoại thành công, kiểm tra bong bóng tin nhắn.
  2. Bấm nút Play trên thanh Audio Player (`UX-016`).
  3. Kéo thanh trượt tiến trình đến mốc giữa câu.
- **Kết quả mong đợi**: Âm thanh phát mượt mà, thanh trượt tua đúng vị trí, dòng văn bản hiển thị cố định bên dưới để kiểm tra (`BR-050`).

### `TC-064`: Xử lý từ chối cấp quyền Microphone
- **Mức độ ưu tiên**: P1 | **Loại**: UI/UX
- **Các bước thực hiện**:
  1. Bấm nút Microphone.
  2. Khi trình duyệt hiện popup xin quyền, chọn "Block".
- **Kết quả mong đợi**: Giao diện không bị treo, xuất hiện banner thông báo thân thiện hướng dẫn người dùng mở lại quyền mic trong cài đặt.

### `TC-065`: Giới hạn thời lượng thu âm tối đa 120 giây
- **Mức độ ưu tiên**: P0 | **Loại**: Functional
- **Các bước thực hiện**:
  1. Bắt đầu thu âm và để thiết bị thu liên tục.
  2. Quan sát đồng hồ đếm thời gian.
- **Kết quả mong đợi**: Khi đồng hồ chạm mốc `02:00` (120 giây), hệ thống tự động ngắt thu âm (`BR-048`) và đóng gói dữ liệu sẵn sàng gửi.

### `TC-066`: Giới hạn dung lượng tệp âm thanh 10MB
- **Mức độ ưu tiên**: P0 | **Loại**: Security
- **Các bước thực hiện**:
  1. Gửi request POST tệp âm thanh giả lập kích thước 12MB lên `/api/v1/chat/stt`.
- **Kết quả mong đợi**: Server trả về HTTP 413 Payload Too Large với mã lỗi `FILE_TOO_LARGE` (`SEC-021`).

### `TC-067`: Khả năng chịu lỗi khi mất kết nối mạng
- **Mức độ ưu tiên**: P1 | **Loại**: Resilience
- **Các bước thực hiện**:
  1. Thu âm một đoạn âm thanh.
  2. Ngắt kết nối mạng trước khi bấm Gửi.
- **Kết quả mong đợi**: Tệp âm thanh không bị mất, giao diện hiển thị nút "Thử lại (Retry)" để người dùng gửi lại khi có mạng trở lại (`BR-049`).

### `TC-068`: Xác thực Magic Bytes chống mã độc
- **Mức độ ưu tiên**: P0 | **Loại**: Security
- **Các bước thực hiện**:
  1. Đổi tên một file nhị phân thực thi `.exe` thành `voice.webm`.
  2. Gửi file lên endpoint `/api/v1/chat/stt`.
- **Kết quả mong đợi**: Backend phát hiện header nhị phân không phải âm thanh, từ chối với HTTP 400 (`SEC-021`).

