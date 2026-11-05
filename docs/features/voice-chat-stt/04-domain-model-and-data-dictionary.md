# Mô Hình Miền & Từ Điển Dữ Liệu: Voice Input & STT
## Phân Hệ: Voice Input & STT | Tính Năng: `FEAT-006`

## 1. Mô Hình Thực Thể Miền (Domain Entities)

### 1.1. Thực thể `Message` (Mở rộng cho Audio & STT)
Bổ sung các trường lưu trữ liên quan đến âm thanh đầu vào của người dùng:
- **`id`** (`VARCHAR(36)`): Khóa chính UUID.
- **`conversation_id`** (`VARCHAR(36)`): Khóa ngoại tham chiếu `conversations(id)`.
- **`role`** (`VARCHAR(20)`): `'user'` hoặc `'assistant'`.
- **`content`** (`TEXT`): Đoạn văn bản (được trích xuất từ STT đối với tin nhắn giọng nói).
- **`audio_attachment_id`** (`VARCHAR(36)`, nullable): Khóa ngoại liên kết tới bảng `attachments(id)`.
- **`audio_duration_ms`** (`INTEGER`, default 0): Thời lượng tệp âm thanh ghi âm tính bằng mili-giây.
- **`stt_language`** (`VARCHAR(10)`, default `'auto'`): Ngôn ngữ nhận dạng (`'vi'`, `'en'`, `'ja'`).
- **`stt_confidence`** (`REAL`, default 1.0): Điểm tin cậy của thuật toán STT (thang điểm 0.0 đến 1.0).

### 1.2. Thực thể `Attachment` (Đã có sẵn trong hệ thống)
Lưu trữ tệp âm thanh nhị phân trên đĩa và quản lý quyền sở hữu:
- **`id`** (`VARCHAR(36)`): Khóa chính UUID của tệp đính kèm.
- **`user_id`** (`VARCHAR(36)`): Định danh người tải lên (ngăn chặn IDOR).
- **`filename`** (`VARCHAR(255)`): Tên tệp lưu trữ (ví dụ: `voice_20261105_103000.webm`).
- **`stored_path`** (`VARCHAR(500)`): Đường dẫn vật lý trên server (trong `data/storage/attachments/`).
- **`file_size`** (`INTEGER`): Kích thước file tính bằng byte (tối đa 10MB theo `BR-048`).
- **`mime_type`** (`VARCHAR(100)`): Định dạng MIME chuẩn (`audio/webm`, `audio/wav`, `audio/ogg`, `audio/mp4`).
- **`status`** (`VARCHAR(20)`): `'READY'`, `'ATTACHED'`, `'DELETED'`.

---

## 2. Từ Điển Dữ Liệu (Data Dictionary)

| Tên Trường | Kiểu Dữ Liệu | Ràng Buộc | Mô Tả Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `audio_file` | Binary File | Bắt buộc (POST /stt) | File âm thanh gửi từ client (WebM/WAV) |
| `language_hint` | String (2-4 ký tự) | Tùy chọn (`vi`, `en`, `ja`, `auto`) | Gợi ý ngôn ngữ người học đang nói để tăng tốc độ và độ chuẩn xác STT (`BR-047`) |
| `duration_ms` | Integer | >= 0 và <= 120,000 | Thời lượng đoạn ghi âm của học viên (`BR-048`) |
| `transcript` | String | UTF-8, tối đa 4000 ký tự | Văn bản hoàn chỉnh được STT chuyển đổi từ giọng nói |
| `detected_language`| String | `vi`, `en`, `ja` | Ngôn ngữ hệ thống tự động phát hiện được từ âm thanh |
| `confidence` | Float | 0.00 đến 1.00 | Mức độ tin cậy của câu nhận diện |

