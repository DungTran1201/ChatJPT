# Architecture & API Contract: Exam Management

## 1. Thành Phần Kiến Trúc (`COMP-001`, `COMP-002`)
- **Frontend Layer (`ai-frontend`)**:
  - Giao diện người dùng tại `/exams` với 2 tabs độc lập: "Kho Đề Thi" và "Tài Liệu Tham Khảo".
  - `examService.ts`: Client HTTP service tương tác với REST endpoints.
- **Backend Service Layer (`ai-backend`)**:
  - `exams.py` router: Xử lý các nghiệp vụ truy vấn danh mục, lọc theo cấp độ, chấm bài thi tự động, và quản lý liên kết tài liệu.
  - Tích hợp SQLite CSDL `exams`, `exam_questions`, `reference_materials`.

---

## 2. API Specifications

### `GET /api/v1/exams` (`OP-055`)
- **Query Params**: `level` (optional), `category` (optional), `search` (optional).
- **Phản hồi (200 OK)**:
```json
{
  "total": 6,
  "items": [
    {
      "id": "exam_seed_n5_full",
      "title": "Bộ Đề Thi Thử JLPT N5 Chuẩn Khảo Thí (Có Đáp Án & Giải Thích)",
      "description": "Đề thi thử toàn diện cấp độ N5 bao gồm Từ vựng, Ngữ pháp, Đọc hiểu và Nghe hiểu.",
      "level": "N5",
      "category": "JLPT_FULL",
      "year": 2024,
      "duration_minutes": 60,
      "total_questions": 10,
      "passing_score": 90,
      "max_score": 180,
      "drive_folder_url": "https://drive.google.com/drive/folders/14cvGKUh4Gu7ojd2JE6FzWL5hCTSFwhaz?usp=sharing",
      "status": "ACTIVE",
      "is_system_preset": true
    }
  ]
}
```

### `GET /api/v1/exams/{id}` (`OP-056`)
- **Mục đích**: Lấy thông tin chi tiết đề thi và danh sách câu hỏi đi kèm.
- **Phản hồi (200 OK)**: Chứa thông tin đề thi và mảng `questions`.

### `POST /api/v1/exams` (`OP-057`)
- **Mục đích**: Tạo đề thi mới do người dùng tùy chỉnh.

### `PUT /api/v1/exams/{id}` (`OP-058`)
- **Mục đích**: Cập nhật thông tin đề thi.

### `DELETE /api/v1/exams/{id}` (`OP-059`)
- **Mục đích**: Xóa đề thi (chặn xóa đề thi hệ thống `BR-044`).

### `POST /api/v1/exams/{id}/submit` (`OP-060`)
- **Mục đích**: Chấm điểm bài thi thử trực tuyến.
- **Request Body**:
```json
{
  "answers": {
    "q_n5_01": 2,
    "q_n5_02": 1
  }
}
```
- **Phản hồi (200 OK)**:
```json
{
  "exam_id": "exam_seed_n5_full",
  "total_questions": 10,
  "answered_count": 2,
  "correct_count": 2,
  "score": 36,
  "max_score": 180,
  "passed": false,
  "results": [
    {
      "question_id": "q_n5_01",
      "user_answer": 2,
      "correct_answer": 2,
      "is_correct": true,
      "explanation": "Câu trả lời chính xác! わたし (私) nghĩa là 'Tôi'."
    }
  ]
}
```

### `GET /api/v1/exams/materials` (`OP-061`)
- **Query Params**: `category` (optional), `level` (optional), `search` (optional).
- **Phản hồi (200 OK)**: Danh sách tài liệu tham khảo (N5..N1 Google Drive, Kaiwa Drive, Tae Kim Guide, Từ điển).

### `POST /api/v1/exams/materials` (`OP-062`)
- **Mục đích**: Tạo mới liên kết tài liệu tham khảo.

### `GET /api/v1/exams/materials/view/{material_id}` (`OP-063`)
- **Mục đích**: Stream trực tiếp tệp PDF giáo trình cục bộ (`LOCAL_FILE`) cho trình duyệt xem inline.
- **Path Param**: `material_id` (string).
- **Phản hồi**: File response với `Content-Type: application/pdf` và `Content-Disposition: inline; filename="..."`.

### `GET /api/v1/exams/materials/download/{material_id}` (`OP-064`)
- **Mục đích**: Tải tệp tài liệu cục bộ về máy người dùng dưới dạng đính kèm (Attachment).
- **Path Param**: `material_id` (string).
- **Phản hồi**: File response với `Content-Disposition: attachment; filename="..."`.

### `GET /api/v1/exams/rag/search` (`OP-065`)
- **Mục đích**: Tìm kiếm ngữ liệu sư phạm RAG (ngữ pháp, từ vựng, mẫu câu giao tiếp) đã lập chỉ mục từ kho tài liệu.
- **Query Params**: `q` (string, required), `level` (optional), `limit` (default: 5).
- **Phản hồi (200 OK)**:
```json
{
  "query": "te form",
  "level": "N5",
  "total": 1,
  "results": [
    {
      "id": "rag_n5_001",
      "level": "N5",
      "category": "GRAMMAR",
      "topic": "Động từ thể Te (~てください / ~ています)",
      "content": "Thể て (Te-form) là nền tảng quan trọng nhất trong sơ cấp...",
      "source": "Tae Kim's Guide & Minna no Nihongo I"
    }
  ]
}
```

