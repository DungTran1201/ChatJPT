# Kế Hoạch Xác Minh & Kiểm Thử Chất Lượng (Verification Plan)
## Tính Năng: Multilingual Voice Input & Speech-to-Text (STT)

## 1. Mục Tiêu Kiểm Thử
Đảm bảo tính năng Thu âm Giọng nói Đa ngữ và Chuyển đổi STT hoạt động chính xác, bảo mật, có độ trễ chấp nhận được và hiển thị trực quan cả tệp âm thanh lẫn văn bản tương ứng trên giao diện chat.

## 2. Ma Trận Ca Kiểm Thử (Test Cases Matrix)

| ID | Tên Ca Kiểm Thử | Mục Đích | Kết Quả Mong Đợi | Trạng Thái |
| :--- | :--- | :--- | :--- | :--- |
| `TC-060` | Kiểm tra thu âm & STT tiếng Việt | Thu giọng nói tiếng Việt có dấu, ngữ điệu tự nhiên | Transcript chính xác >= 95%, Audio player phát lại rõ ràng | Ready |
| `TC-061` | Kiểm tra thu âm & STT tiếng Nhật | Thu câu giao tiếp Kaiwa tiếng Nhật có Kanji/Kana | Transcript hiển thị đúng Kanji và trợ từ, AI Sensei hiểu | Ready |
| `TC-062` | Kiểm tra thu âm & STT tiếng Anh | Thu câu tiếng Anh chuẩn và đan xen từ vựng | Transcript nhận diện chính xác từ ngữ | Ready |
| `TC-063` | Hiển thị đồng bộ Audio Player & Text | Kiểm tra tin nhắn người dùng sau khi gửi voice | Tin nhắn hiển thị Audio waveform bar + đoạn text vừa nói | Ready |
| `TC-064` | Từ chối cấp quyền Microphone | Người dùng nhấn Block quyền truy cập mic trên trình duyệt | UI hiển thị thông báo hướng dẫn mở quyền mic, không crash | Ready |
| `TC-065` | Giới hạn thời lượng thu âm tối đa | Thu âm liên tục vượt quá 120 giây | Hệ thống tự động dừng thu âm ở 120s và chuẩn bị gửi | Ready |
| `TC-066` | Giới hạn dung lượng tệp âm thanh | Thử upload tệp âm thanh > 10MB | API từ chối với lỗi `FILE_TOO_LARGE` (HTTP 413) | Ready |
| `TC-067` | Kiểm tra tính liên tục khi rớt mạng | Ngắt kết nối mạng trong quá trình upload audio | Bản ghi âm được giữ trên bộ nhớ tạm của client, cho phép retry | Ready |
| `TC-068` | Xác thực MIME Type tệp âm thanh | Gửi file mã độc giả mạo đuôi audio | Hệ thống phát hiện Magic Bytes không hợp lệ, chặn ngay | Ready |

## 3. Tiêu Chí Nghiệm Thu Deterministic Validators
- Chạy toàn bộ bộ kiểm tra tự động `tools/validators/run_all.py`.
- 100% các ID (`FR-079..FR-082`, `BR-047..BR-050`, `NFR-021..NFR-023`, `SEC-021..SEC-022`) được truy vết xuyên suốt tài liệu và mô hình chuẩn.

