# Open Questions & Implementation Readiness: Exam Management

## 1. Câu Hỏi Mở & Khuyến Nghị (Open Questions)
- **Câu hỏi 1**: Trong tương lai có nên cho phép Sensei tự động chấm bài làm tự luận hoặc bài nghe Choukai bằng giọng nói không?
  - *Khuyến nghị*: Hiện tại triển khai trắc nghiệm khách quan tự động chấm điểm và link file nghe trực tiếp. Giai đoạn sau sẽ tích hợp VoiceVox và Speech Recognition cho phần Kaiwa Exam.
- **Câu hỏi 2**: Người dùng có thể tự upload file PDF trực tiếp lên server thay vì chỉ dùng Google Drive không?
  - *Khuyến nghị*: Hệ thống đã có sẵn `AttachmentService` (`/attachments`), có thể gắn `attachment_id` vào bài thi khi cần lưu trữ trực tiếp trên máy chủ.

## 2. Tiêu Chí Sẵn Sàng (Readiness Checklist)
- [x] Đặc tả SRS, Use Cases và Traceability Matrix hoàn tất.
- [x] Thiết kế mô hình CSDL `exams`, `exam_questions`, `reference_materials` hoàn tất.
- [x] Thiết kế API contract và bảo mật chống gian lận đáp án hoàn tất.
- [x] Tích hợp đầy đủ 6 đường dẫn Google Drive chính thức từ người dùng.
- [x] Sẵn sàng chuyển sang giai đoạn Coding & DB Migration.
