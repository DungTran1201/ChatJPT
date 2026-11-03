# Scope, Assumptions & Decisions: Exam & Reference Materials Management

## 1. Scope (Phạm Vi)
- **Kho Đề Thi (Exam Bank)**:
  - Quản lý danh mục đề thi phân loại theo cấp độ (`N5`, `N4`, `N3`, `N2`, `N1`, `KAIWA`, `GENERAL`).
  - Hỗ trợ các phân môn: `JLPT_FULL`, `CHOUKAI` (Nghe hiểu), `DOKKAI` (Đọc hiểu), `GOI_BUNPOU` (Từ vựng & Ngữ pháp), `KAIWA_SCENARIO` (Kịch bản đàm thoại).
  - Tích hợp tài liệu đính kèm (Link Google Drive chính thức, tệp PDF đề thi, tệp Audio nghe hiểu, đáp án).
  - Cho phép xem chi tiết đề, làm bài thi thử trắc nghiệm trực tuyến kèm chấm điểm và giải thích sư phạm tự động.
- **Kho Tài Liệu Tham Khảo (Reference Materials)**:
  - Tích hợp toàn diện 6 kho tài liệu Google Drive người học cung cấp:
    - Tài liệu N5: `https://drive.google.com/drive/folders/14cvGKUh4Gu7ojd2JE6FzWL5hCTSFwhaz?usp=sharing`
    - Tài liệu N4: `https://drive.google.com/drive/folders/1HytgiK1tJaSGW4wUmHYQRbniPYu3-NLh?usp=sharing`
    - Tài liệu N3: `https://drive.google.com/drive/folders/1lwUZCcGfAl2HwhrQVz-R4s-dXMEKpuZD?usp=sharing`
    - Tài liệu N2: `https://drive.google.com/drive/folders/1lCVccq1e-dCWKR8CzZX7EbmRkuLPah7F?usp=sharing`
    - Tài liệu N1: `https://drive.google.com/drive/folders/1451604QICFd_zpWxYXLz5jJj6z2Xh4RI?usp=sharing`
    - Tài liệu Kaiwa: `https://drive.google.com/drive/folders/17JFLZlqVgwxJFS0BkHAv1I_szVJz-aQB?usp=sharing`
  - Cẩm nang ngữ pháp Tae Kim Japanese Grammar Guide (`https://guidetojapanese.org/learn/`).
  - Hệ thống từ vựng từ điển tiếng Nhật chuẩn hóa.

## 2. Facts, Assumptions, Decisions

### FACTS:
- Người học cần một kho đề thi và tài liệu học tập tập trung, không phải lục tìm rời rạc trên nhiều nền tảng.
- Mỗi cấp độ JLPT đòi hỏi cấu trúc câu hỏi, thời gian và dạng bài khác nhau.

### ASSUMPTIONS:
- Người dùng có kết nối internet để truy cập tài liệu trên Google Drive và các đường dẫn học thuật bên ngoài.
- Dữ liệu câu hỏi trắc nghiệm của các đề thi mẫu lưu trữ trực tiếp trong CSDL nội bộ SQLite để phục vụ làm bài thi trực tuyến mượt mà.

### DECISIONS:
- **`DEC-EXAM-001`**: Tổ chức giao diện thành 2 tab trực quan tại route `/exams`: "Kho Đề Thi (Exam Bank)" và "Tài Liệu Tham Khảo (Reference Materials)".
- **`DEC-EXAM-002`**: Seed sẵn 6 thư mục Google Drive chính thức từ người dùng vào CSDL `reference_materials` với cờ `is_system_preset = 1`.
- **`DEC-EXAM-003`**: Cho phép thi thử online với bộ câu hỏi có chấm điểm tự động và lời giải thích chi tiết mang phong cách Sensei.
