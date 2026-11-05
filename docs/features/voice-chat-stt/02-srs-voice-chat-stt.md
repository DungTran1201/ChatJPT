# Đặc Tả Yêu Cầu Phần Mềm: Voice Input & Speech-to-Text (STT)
## Chuẩn Đặc Tả: ISO/IEC/IEEE 29148 Standard | Tính Năng: `FEAT-006`

## 1. Giới Thiệu (Introduction)
Tài liệu đặc tả các yêu cầu phần mềm cho phân hệ Nhập liệu Giọng nói Đa ngữ (Tiếng Việt, Tiếng Anh, Tiếng Nhật) và Chuyển đổi Giọng nói thành Văn bản (STT) tích hợp trong ứng dụng học tiếng Nhật ChatJPT.

## 2. Đặc Tả Chi Tiết Yêu Cầu Chức Năng

### 2.1. `FR-079`: Thu âm giọng nói đa ngữ (vi, en, ja)
- **Mô tả**: Giao diện người dùng cho phép khởi động, tạm dừng, tiếp tục và hủy quá trình thu âm âm thanh qua microphone.
- **Tiền điều kiện**: Trình duyệt có kết nối thiết bị microphone và được người dùng cấp quyền.
- **Xử lý**:
  - Ghi nhận tín hiệu âm thanh qua Web Audio API với tần số lấy mẫu từ 16kHz đến 48kHz.
  - Cho phép chọn ngôn ngữ gợi ý (Language Hint): `vi` (Tiếng Việt), `en` (Tiếng Anh), `ja` (Tiếng Nhật), hoặc `auto` (Tự động phát hiện) (`BR-047`).
  - Hiển thị sóng âm động (`UX-015`) và thời gian ghi âm liên tục.
- **Hậu điều kiện**: Tạo ra khối dữ liệu âm thanh (Audio Blob) định dạng WebM/Opus hoặc WAV.

### 2.2. `FR-080`: Chuyển đổi giọng nói thành văn bản (STT Pipeline)
- **Mô tả**: Hệ thống xử lý khối dữ liệu âm thanh và trích xuất thành chuỗi văn bản tương ứng.
- **Xử lý**:
  - Chuyển tiếp Audio Blob lên máy chủ qua endpoint `POST /api/v1/chat/stt` (`OP-066`).
  - Kiểm tra tính hợp lệ của tệp âm thanh (dung lượng <= 10MB, thời lượng <= 120s, magic bytes chuẩn) (`BR-048`, `SEC-021`).
  - Đưa vào bộ chuyển đổi Whisper hoặc Gemini Multimodal Audio để nhận dạng văn bản tiếng Việt có dấu, tiếng Anh và tiếng Nhật kèm Kanji/Kana.
  - Trả về kết quả gồm: đoạn văn bản nhận dạng (`transcript`), ngôn ngữ phát hiện (`detected_language`), độ tin cậy (`confidence`) và đường dẫn tệp âm thanh đã lưu.

### 2.3. `FR-081`: Hiển thị đồng bộ Audio Player & Phụ đề văn bản trên Chat
- **Mô tả**: Tin nhắn người dùng sau khi nói phải được hiển thị trực quan và lưu trữ đầy đủ trong lịch sử trò chuyện.
- **Xử lý**:
  - Khung bong bóng tin nhắn của người dùng hiển thị thanh phát âm thanh nhỏ gọn (`UX-016`) có nút Play/Pause, thanh kéo tua (scrub bar) và thời lượng.
  - Hiển thị văn bản chuyển đổi ngay bên dưới trình phát âm thanh để người dùng kiểm tra câu nói (`BR-050`).
  - Người dùng có thể nhấn nghe lại âm thanh bất kỳ lúc nào để tự kiểm tra phát âm của bản thân.

### 2.4. `FR-082`: Điều phối Audio và Transcript vào mô hình AI
- **Mô tả**: Tiếp nhận văn bản sau khi chuyển đổi từ giọng nói làm đầu vào trực tiếp cho trợ lý ảo Sensei.
- **Xử lý**:
  - Gửi nội dung văn bản tới `POST /api/v1/conversations/{id}/messages/stream` (`OP-009`).
  - Kết hợp với quy tắc sư phạm, tính cách Sensei và trình độ JLPT đang chọn.
  - Mô hình AI sinh câu trả lời giảng giải ngữ pháp, phản hồi hội thoại Kaiwa và phát giọng đọc qua luồng SSE.

## 3. Đặc Tả Yêu Cầu Phi Chức Năng
- **`NFR-021` (Độ trễ STT)**: Thời gian từ khi bấm dừng nói đến khi văn bản xuất hiện trên màn hình không quá 1.5 giây.
- **`NFR-022` (Tối ưu băng thông)**: Âm thanh nén Opus đạt tỷ lệ nén cao, không gây nghẽn băng thông mạng di động.
- **`NFR-023` (Bảo mật & Riêng tư)**: Dữ liệu âm thanh của học viên được lưu trong thư mục an toàn, chỉ người sở hữu phiên mới có quyền nghe lại (`SEC-022`).

