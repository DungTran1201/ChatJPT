# Software Requirements Specification (SRS): Exam & Materials Management

## 1. Giới Thiệu
Tài liệu đặc tả yêu cầu phần mềm cho phân hệ Quản Lý Kho Đề Thi & Tài Liệu Tham Khảo (Exam Management) thuộc nền tảng ChatJPT.

## 2. Yêu Cầu Chức Năng (Functional Requirements)

### `FR-074`: Danh Mục Kho Đề Thi & Bộ Lọc Đa Cấp Độ
- Hệ thống phải hiển thị danh sách các bộ đề thi với thông tin đầy đủ: Tiêu đề, Cấp độ (`N5`..`N1`, `KAIWA`), Thể loại (`JLPT Full`, `Choukai`, `Dokkai`, `Goi & Bunpou`), Thời lượng, Số lượng câu hỏi, Điểm đạt/Điểm tối đa.
- Cung cấp bộ lọc theo: Cấp độ (Tất cả, N5, N4, N3, N2, N1, Kaiwa), Thể loại, và ô tìm kiếm theo từ khóa.

### `FR-075`: Quản Lý Đề Thi & Liên Kết Thư Mục Google Drive
- Cho phép người dùng tạo mới bộ đề thi cá nhân hoặc cấu hình thông tin đề thi.
- Hỗ trợ gắn liên kết thư mục Google Drive chứa tài nguyên đề thi (PDF, Audio, Đáp án).
- Bộ đề mẫu hệ thống (`is_system_preset = 1`) được bảo vệ khỏi hành vi xóa bỏ (`BR-044`).

### `FR-076`: Thi Thử Trực Tuyến & Chấm Điểm Kèm Lời Giải Sensei
- Cung cấp giao diện làm bài thi thử trực quan với danh sách câu hỏi trắc nghiệm chia theo từng phân môn (`GOI`, `BUNPOU`, `DOKKAI`, `CHOUKAI`, `KAIWA`).
- Tự động đếm ngược thời gian làm bài theo `duration_minutes`.
- Khi nộp bài, hệ thống tự động chấm điểm, hiển thị số câu đúng/sai, tỷ lệ phần trăm và chi tiết lời giải thích sư phạm tiếng Việt cho từng câu.

### `FR-077`: Kho Tài Liệu Tham Khảo (JLPT Drive, Tae Kim Guide, Từ Điển)
- Hệ thống tích hợp sẵn các nguồn tài liệu học tập chính thức:
  1. Thư mục Google Drive N5 đến N1 và Kaiwa.
  2. Cẩm nang ngữ pháp tiếng Nhật Tae Kim's Japanese Grammar Guide.
  3. Kho tra cứu từ vựng và từ điển tiếng Nhật.
- Hiển thị danh mục dạng thẻ (Card) trực quan kèm nhãn tags, tác giả, và nút mở tài liệu 1-chạm (`Open External Drive`).

### `FR-078`: Đánh Dấu Ghim Tài Liệu Yêu Thích
- Người học có thể ghim các tài liệu quan trọng lên đầu để truy cập nhanh chóng mỗi khi đăng nhập.

## 3. Yêu Cầu Phi Chức Năng (Non-Functional Requirements)
- **`NFR-EXAM-01` (Latency)**: API trả về danh mục đề thi và tài liệu < 100ms.
- **`NFR-EXAM-02` (Usability)**: Giao diện chuyển đổi 2 tabs mượt mà, hỗ trợ Dark/Light theme đồng bộ theo cài đặt hệ thống.
- **`NFR-EXAM-03` (Responsiveness)**: Tương thích hoàn hảo trên cả máy tính bàn (Desktop) và thiết bị di động.
