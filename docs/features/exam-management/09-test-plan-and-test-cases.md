# Test Plan & Test Cases: Exam Management

## 1. Test Matrix
| Mã Test Case | Mục Tiêu Kiểm Thử | Yêu Cầu Liên Quan | Loại Kiểm Thử |
| :--- | :--- | :--- | :--- |
| `TC-EXAM-001` | Lấy danh mục đề thi và lọc theo cấp độ (`N5`..`N1`, `KAIWA`) | `FR-074` | Backend API / Unit |
| `TC-EXAM-002` | Xác thực ràng buộc dữ liệu đề thi và thời lượng làm bài (`BR-043`, `BR-045`) | `FR-075`, `BR-043` | Validation / Unit |
| `TC-EXAM-003` | Chặn xóa hoặc can thiệp đề thi chuẩn hệ thống (`BR-044`) | `FR-075`, `BR-044` | Security / Integration |
| `TC-EXAM-004` | Nộp bài thi trực tuyến và tự động chấm điểm (`FR-076`) | `FR-076` | API Integration |
| `TC-EXAM-005` | Truy vấn danh mục tài liệu tham khảo và kiểm tra link Google Drive | `FR-077`, `BR-046` | API Integration |
| `TC-EXAM-006` | Khử khuẩn input dữ liệu và chống injection (`SEC-016`) | `SEC-016` | Security |

---

## 2. Chi Tiết Kịch Bản Kiểm Thử

### `TC-EXAM-001`: Lọc đề thi theo cấp độ
- **Input**: Gửi `GET /api/v1/exams?level=N5`.
- **Expected Result**: Trả về HTTP 200, danh sách chứa bộ đề thi N5, `total >= 1`.

### `TC-EXAM-003`: Bảo vệ đề thi hệ thống
- **Input**: Gửi `DELETE /api/v1/exams/exam_seed_n5_full`.
- **Expected Result**: Trả về HTTP 403 Forbidden hoặc 400 Bad Request kèm thông báo không được xóa đề thi mẫu hệ thống.

### `TC-EXAM-004`: Nộp bài thi và nhận kết quả
- **Input**: Gửi `POST /api/v1/exams/exam_seed_n5_full/submit` kèm payload đáp án.
- **Expected Result**: HTTP 200, trả về tổng số câu hỏi, số câu đúng, điểm số và chi tiết giải thích cho từng câu.
