# Đánh Giá An Ninh & Rủi Ro: Voice Input & STT
## Phân Hệ: Voice Input & STT | Tính Năng: `FEAT-006`

## 1. Mô Hình Đe Dọa (Threat Modeling)

| Mã Rủi Ro | Loại Đe Dọa | Mô Tả Nguy Cơ | Biện Pháp Kiểm Soát |
| :--- | :--- | :--- | :--- |
| `THR-006` | Giả mạo tệp độc hại | Kẻ tấn công gửi tệp thực thi (exe, sh, php) đổi tên thành `.webm` hoặc `.wav` để khai thác lỗ hổng máy chủ. | `CTRL-006`, `SEC-021`: Đọc và kiểm tra Magic Bytes (Header nhị phân) của tệp bằng thư viện `filetype` / `python-magic`. Từ chối ngay nếu không phải định dạng âm thanh chuẩn. |
| `THR-004` | Tấn công cạn kiệt tài nguyên (DoS) | Tải lên các file âm thanh dung lượng cực lớn (hàng trăm MB) hoặc gửi liên tục để chiếm dụng dung lượng đĩa và quota STT. | `CTRL-004`, `BR-048`: Giới hạn dung lượng tối đa 10MB và thời lượng tối đa 120s; áp dụng Rate Limiting 30 req/min/IP tại tầng Ingress Gateway. |
| `THR-001` | Lộ lọt dữ liệu giọng nói (IDOR) | Người dùng B cố ý truy cập đường dẫn tệp âm thanh của người dùng A (`/attachments/{id}`). | `SEC-022`: Kiểm tra quyền sở hữu `user_id` trong bảng `attachments` trước khi cho phép tải hoặc phát lại tệp âm thanh. |

---

## 2. Chính Sách Bảo Mật Dữ Liệu Âm Thanh (Audio Data Governance)
1. **Lưu trữ bảo mật**: Tệp âm thanh thu âm được lưu trữ trong thư mục nội bộ `ai-backend/data/storage/attachments/` với định danh UUID ngẫu nhiên không thể đoán trước (`UUIDv4`).
2. **Quyền riêng tư (Privacy)**: Tuyệt đối không dùng dữ liệu giọng nói của học viên để huấn luyện lại các mô hình bên thứ ba nếu chưa có sự đồng thuận rõ ràng.
3. **Mã hóa truyền tải**: Toàn bộ luồng âm thanh tải lên và tải về bắt buộc phải đi qua giao thức bảo mật mã hóa HTTPS/TLS 1.3 (`NFR-023`).

