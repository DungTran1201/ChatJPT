# Use Cases & Acceptance Criteria: Exam Management

## 1. Use Case Model
- **`UC-045`**: Khám Phá & Quản Lý Kho Đề Thi (Explore & Manage Exam Bank)
- **`UC-046`**: Làm Bài Thi Thử Trực Tuyến & Xem Giải Thích Sư Phạm (Take Mock Exam & Review Explanations)
- **`UC-047`**: Tra Cứu & Khai Thác Tài Liệu Tham Khảo (Explore Reference Materials & Drive Links)

---

## 2. Chi Tiết Use Cases & Tiêu Chí Nghiệm Thu (Acceptance Criteria)

### `UC-045`: Khám Phá & Quản Lý Kho Đề Thi
- **Actor**: Người học (Learner), Quản trị viên (Admin).
- **Preconditions**: Người dùng đã đăng nhập hoặc sử dụng với tư cách khách.
- **Main Flow**:
  1. Người dùng chọn tab "Kho Đề Thi (Exam Bank)" trên menu `/exams`.
  2. Hệ thống tải danh mục đề thi kèm các thẻ thống kê tổng số đề thi và phân bổ theo cấp độ N5..N1.
  3. Người dùng chọn lọc theo cấp độ "N5" -> Hệ thống lọc tức thời hiển thị các đề thi thuộc trình độ N5.
  4. Người dùng bấm "Mở Thư Mục Drive" -> Hệ thống mở thư mục Google Drive chính thức trong tab mới.
- **Acceptance Criteria**:
  - `AC-045-1`: Danh sách hiển thị đúng các bộ đề thi hạt giống N5, N4, N3, N2, N1 và Kaiwa.
  - `AC-045-2`: Nhấn nút Google Drive mở đúng link Google Drive tương ứng đã thiết lập.

### `UC-046`: Làm Bài Thi Thử Trực Tuyến
- **Actor**: Người học (Learner).
- **Preconditions**: Bộ đề thi có câu hỏi trong bảng `exam_questions`.
- **Main Flow**:
  1. Người học nhấn nút "Làm Bài Thi Thử" trên thẻ đề thi.
  2. Modal bài thi hiển thị đồng hồ đếm ngược và danh sách câu hỏi trắc nghiệm 4 đáp án.
  3. Người học chọn đáp án cho từng câu và nhấn "Nộp Bài".
  4. Hệ thống chấm điểm, đối chiếu đáp án đúng và hiển thị lời giải thích ngữ pháp/từ vựng chi tiết.
- **Acceptance Criteria**:
  - `AC-046-1`: Hệ thống tính toán chính xác điểm số theo số câu trả lời đúng.
  - `AC-046-2`: Mỗi câu hỏi đều hiển thị rõ lý do tại sao phương án đó đúng bằng tiếng Việt.

### `UC-047`: Tra Cứu & Khai Thác Tài Liệu Tham Khảo
- **Actor**: Người học (Learner).
- **Main Flow**:
  1. Người học chuyển sang tab "Tài Liệu Tham Khảo (Reference Materials)".
  2. Hệ thống hiển thị 6 thư mục Google Drive (N5..N1, Kaiwa), tài liệu Tae Kim's Grammar Guide và Kho Từ Điển.
  3. Người học có thể nhấn Ghim (Pin) tài liệu hoặc nhấn Mở tài liệu.
- **Acceptance Criteria**:
  - `AC-047-1`: Toàn bộ 6 link Google Drive do người dùng cung cấp hiển thị chính xác và truy cập được 100%.
  - `AC-047-2`: Thẻ Tae Kim Guide hiển thị tóm lược ngữ pháp và link tra cứu chuyên sâu.

