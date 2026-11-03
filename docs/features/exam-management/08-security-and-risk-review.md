# Security & Risk Review: Exam Management

## 1. Phân Tích Mối Đe Dọa (Threat Modeling & Controls)

| Nguy Cơ / Đe Dọa | Mức Độ | Biện Pháp Kiểm Soát Kỹ Thuật (`CTRL-###`) |
| :--- | :--- | :--- |
| **Xóa nhầm bộ đề mẫu hệ thống** | Cao | `CTRL-EXAM-01`: Cờ `is_system_preset` trong CSDL; backend chặn mọi yêu cầu `DELETE`/`PUT` đối với đề thi hệ thống (`BR-044`). |
| **Chèn mã độc / XSS qua URL Drive** | Trung bình | `CTRL-EXAM-02`: Bộ kiểm tra URL chỉ chấp nhận giao thức `https://` và tên miền hợp lệ (`drive.google.com`, `guidetojapanese.org`) (`BR-046`). |
| **Gian lận đáp án khi làm bài thi** | Thấp | `CTRL-EXAM-03`: Endpoint `GET /api/v1/exams/{id}` chỉ trả về câu hỏi và 4 lựa chọn, **không trả về trường `correct_option`** hay `explanation` trước khi nộp bài. |
| **SQL Injection qua bộ lọc tìm kiếm** | Cao | `CTRL-EXAM-04`: Sử dụng hoàn toàn Parameterized Query với DB driver của SQLite / SQLAlchemy. |
| **Độ dài câu hỏi và giới hạn số điểm** | Thấp | `CTRL-EXAM-05`: Pydantic Model xác thực độ dài câu hỏi tối đa 2000 ký tự, thời lượng 1 - 360 phút (`BR-045`). |

